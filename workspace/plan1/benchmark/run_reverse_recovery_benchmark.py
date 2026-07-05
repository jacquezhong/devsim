#!/usr/bin/env python3
"""
Run reverse-recovery transient benchmark cases.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from benchmark_common import (
    chdir_plan,
    carrier_profile,
    contact_current,
    device_parameters,
    ensure_dirs,
    initialize_transient,
    load_config,
    set_top_bias,
    setup_device,
    solve_dc,
    solve_transient,
    stored_mobile_charge_c,
    write_json,
    write_npz,
)
from extract_metrics import extract_recovery_metrics


def find_forward_voltage_for_current(config: dict, target_current_a: float) -> dict:
    dc = config["dc"]
    voltages = np.arange(
        dc["start_voltage_V"],
        dc["stop_voltage_V"] + 0.5 * dc["step_voltage_V"],
        dc["step_voltage_V"],
    )
    points = []
    reached = False
    bracket_low = None
    bracket_high = None
    for voltage in voltages:
        set_top_bias(config, float(voltage))
        ok = solve_dc()
        current = contact_current(config)
        point = {"voltage_V": float(voltage), "current_A": current, "converged": ok}
        points.append(point)
        if current >= target_current_a:
            reached = True
            bracket_high = point
            bracket_low = points[-2] if len(points) >= 2 else point
            break

    refine_points = []
    if reached and bracket_low is not None and bracket_high is not None:
        low_v = float(bracket_low["voltage_V"])
        high_v = float(bracket_high["voltage_V"])
        forward_voltage = high_v
        for _ in range(16):
            mid_v = 0.5 * (low_v + high_v)
            set_top_bias(config, mid_v)
            ok = solve_dc()
            current = contact_current(config)
            refine_points.append(
                {"voltage_V": mid_v, "current_A": current, "converged": ok}
            )
            forward_voltage = mid_v
            if abs(current - target_current_a) <= max(1e-12, 1e-3 * target_current_a):
                break
            if current < target_current_a:
                low_v = mid_v
            else:
                high_v = mid_v
    else:
        forward_voltage = float(points[-1]["voltage_V"])

    set_top_bias(config, forward_voltage)
    solve_dc()
    resolved_current = contact_current(config)
    return {
        "target_current_A": float(target_current_a),
        "resolved_forward_voltage_V": forward_voltage,
        "resolved_forward_current_A": resolved_current,
        "target_reached": reached,
        "dc_probe_points": points,
        "dc_refine_points": refine_points,
    }


def waveform_payload(case_id: str, times: list[float], voltages: list[float], currents: list[float]) -> dict:
    path = Path("data/benchmark/waveforms") / f"{case_id}.npz"
    time = np.asarray(times, dtype=float)
    voltage = np.asarray(voltages, dtype=float)
    current = np.asarray(currents, dtype=float)
    write_npz(path, time_s=time, voltage_V=voltage, current_A=current)
    return {
        "format": "npz",
        "file": str(path),
        "points": int(time.size),
        "time_start_s": float(time[0]) if time.size else None,
        "time_end_s": float(time[-1]) if time.size else None,
        "current_min_A": float(np.min(current)) if current.size else None,
        "current_max_A": float(np.max(current)) if current.size else None,
    }


def normalized_quantities(
    config: dict,
    metrics: dict,
    stored_charge: dict,
    forward_current_a: float,
    target_current_a: float | None = None,
) -> dict:
    area = float(config["device"].get("reference_area_cm2", 1.0))
    return {
        "reference_area_cm2": area,
        "forward_current_density_A_cm2": float(forward_current_a) / area,
        "target_current_density_A_cm2": float(target_current_a) / area
        if target_current_a is not None
        else None,
        "I_rrm_density_A_cm2": float(metrics["I_rrm_A"]) / area,
        "Q_rr_density_C_cm2": float(metrics["Q_rr_C"]) / area,
        "stored_mobile_charge_density_C_cm2": float(
            stored_charge["stored_mobile_charge_C"]
        )
        / area,
    }


def run_recovery(
    tau_s: float,
    time_step_s: float | None = None,
    mesh_density_cm: float | None = None,
    initial_condition: str = "fixed_voltage",
    target_current_a: float | None = None,
    output: Path | None = None,
) -> dict:
    chdir_plan()
    ensure_dirs()
    config = load_config()
    transient = dict(config["transient"])
    if time_step_s is not None:
        transient["time_step_s"] = time_step_s
    if mesh_density_cm is not None:
        config["device"]["mesh_density_cm"] = mesh_density_cm

    setup_device(config, tau_s=tau_s)
    equilibrium_profile = carrier_profile(config)

    started = time.perf_counter()

    target_info = None
    if initial_condition == "target_current":
        target = target_current_a or config["dc"]["target_current_A"]
        target_info = find_forward_voltage_for_current(config, float(target))
        forward_voltage = target_info["resolved_forward_voltage_V"]
    else:
        forward_voltage = transient["forward_voltage_V"]
        set_top_bias(config, forward_voltage)
        solve_dc()

    initialize_transient()

    # Let the forward-biased state settle in transient mode so that stored
    # charge is represented by the previous time state.
    for _ in range(int(transient["forward_settle_steps"])):
        ok = solve_transient(transient["time_step_s"])
        if not ok:
            break

    forward_current = contact_current(config)
    forward_profile = carrier_profile(config)
    stored_charge = stored_mobile_charge_c(config, equilibrium_profile, forward_profile)

    set_top_bias(config, transient["reverse_voltage_V"])
    n_steps = int(np.ceil(transient["reverse_time_s"] / transient["time_step_s"]))
    times = []
    voltages = []
    currents = []
    converged = True
    failed_at = None

    current_time = 0.0
    for step in range(n_steps + 1):
        ok = solve_transient(transient["time_step_s"])
        current_time = (step + 1) * transient["time_step_s"]
        times.append(float(current_time))
        voltages.append(float(transient["reverse_voltage_V"]))
        currents.append(contact_current(config))
        if not ok:
            converged = False
            failed_at = float(current_time)
            break

    elapsed = time.perf_counter() - started
    metrics = extract_recovery_metrics(
        times,
        currents,
        reverse_start_s=0.0,
        threshold_fraction=transient["recovery_threshold_fraction"],
    )

    init_label = "ifixed" if initial_condition == "target_current" else "vfixed"
    target_label = ""
    default_target = float(config["dc"]["target_current_A"])
    if (
        initial_condition == "target_current"
        and target_current_a is not None
        and not np.isclose(float(target_current_a), default_target)
    ):
        target_label = f"_I_{float(target_current_a):.0e}"
    case_id = (
        f"recovery_{init_label}{target_label}_tau_{tau_s:.0e}_dt_"
        f"{transient['time_step_s']:.0e}_mesh_"
        f"{config['device']['mesh_density_cm']:.0e}"
    )
    waveform = waveform_payload(case_id, times, voltages, currents)
    normalized = normalized_quantities(
        config,
        metrics,
        stored_charge,
        forward_current,
        target_current_a
        if initial_condition == "target_current"
        else None,
    )
    result = {
        "case_id": case_id,
        "parameters": {
            **device_parameters(config, tau_s),
            "initial_condition": initial_condition,
            "v_forward_V": forward_voltage,
            "forward_current_A": forward_current,
            "target_current": target_info,
            "v_reverse_V": transient["reverse_voltage_V"],
            "forward_settle_steps": transient["forward_settle_steps"],
            "time_step_s": transient["time_step_s"],
            "reverse_time_s": transient["reverse_time_s"],
        },
        "waveform": waveform,
        "metrics": metrics,
        "normalized": normalized,
        "stored_charge": stored_charge,
        "solver": {
            "converged": converged,
            "failed_at_s": failed_at,
            "elapsed_s": elapsed,
        },
        "current_sign_convention": "positive_forward_negative_reverse",
    }

    output_path = output or Path("data/benchmark/raw") / f"{case_id}.json"
    write_json(output_path, result)
    return result


def run_lifetime_sweep() -> list[dict]:
    config = load_config()
    results = []
    for tau in config["sweeps"]["lifetimes_s"]:
        result = run_recovery(float(tau))
        results.append(
            {
                "case_id": result["case_id"],
                "tau_s": float(tau),
                **result["metrics"],
                **result["normalized"],
                **result["stored_charge"],
                "converged": result["solver"]["converged"],
                "elapsed_s": result["solver"]["elapsed_s"],
            }
        )
        print(
            f"{result['case_id']}: Qrr={result['metrics']['Q_rr_C']:.3e} C, "
            f"Irrm={result['metrics']['I_rrm_A']:.3e} A, "
            f"elapsed={result['solver']['elapsed_s']:.2f}s"
        )
    write_json(Path("data/benchmark/metrics/metrics_lifetime_sweep.json"), results)
    return results


def run_lifetime_sweep_target_current(target_current_a: float | None = None) -> list[dict]:
    config = load_config()
    target = target_current_a or config["dc"]["target_current_A"]
    results = []
    for tau in config["sweeps"]["lifetimes_s"]:
        result = run_recovery(
            float(tau),
            initial_condition="target_current",
            target_current_a=float(target),
        )
        results.append(
            {
                "case_id": result["case_id"],
                "tau_s": float(tau),
                "target_current_A": float(target),
                "v_forward_V": result["parameters"]["v_forward_V"],
                "forward_current_A": result["parameters"]["forward_current_A"],
                **result["metrics"],
                **result["normalized"],
                **result["stored_charge"],
                "converged": result["solver"]["converged"],
                "elapsed_s": result["solver"]["elapsed_s"],
            }
        )
        print(
            f"{result['case_id']}: Vf={result['parameters']['v_forward_V']:.3e} V, "
            f"If={result['parameters']['forward_current_A']:.3e} A, "
            f"Qrr={result['metrics']['Q_rr_C']:.3e} C, "
            f"Qstored={result['stored_charge']['stored_mobile_charge_C']:.3e} C, "
            f"elapsed={result['solver']['elapsed_s']:.2f}s"
        )
    write_json(
        Path("data/benchmark/metrics/metrics_lifetime_sweep_target_current.json"),
        results,
    )
    return results


def run_time_step_sweep(
    tau_s: float,
    initial_condition: str = "fixed_voltage",
    target_current_a: float | None = None,
) -> list[dict]:
    config = load_config()
    target = target_current_a or config["dc"]["target_current_A"]
    results = []
    for dt in config["sweeps"]["time_steps_s"]:
        result = run_recovery(
            float(tau_s),
            time_step_s=float(dt),
            initial_condition=initial_condition,
            target_current_a=float(target),
        )
        results.append(
            {
                "case_id": result["case_id"],
                "tau_s": float(tau_s),
                "time_step_s": float(dt),
                "initial_condition": initial_condition,
                "target_current_A": float(target)
                if initial_condition == "target_current"
                else None,
                "v_forward_V": result["parameters"]["v_forward_V"],
                "forward_current_A": result["parameters"]["forward_current_A"],
                **result["metrics"],
                **result["normalized"],
                **result["stored_charge"],
                "converged": result["solver"]["converged"],
                "elapsed_s": result["solver"]["elapsed_s"],
            }
        )
        print(
            f"{result['case_id']}: Qrr={result['metrics']['Q_rr_C']:.3e} C, "
            f"Irrm={result['metrics']['I_rrm_A']:.3e} A, "
            f"Qstored={result['stored_charge']['stored_mobile_charge_C']:.3e} C, "
            f"elapsed={result['solver']['elapsed_s']:.2f}s"
        )
    suffix = "_target_current" if initial_condition == "target_current" else ""
    write_json(
        Path(f"data/benchmark/metrics/metrics_time_step_sweep{suffix}.json"),
        results,
    )
    return results


def run_forward_current_sweep(tau_s: float) -> list[dict]:
    config = load_config()
    results = []
    for target in config["sweeps"]["target_currents_A"]:
        result = run_recovery(
            float(tau_s),
            initial_condition="target_current",
            target_current_a=float(target),
        )
        results.append(
            {
                "case_id": result["case_id"],
                "tau_s": float(tau_s),
                "target_current_A": float(target),
                "v_forward_V": result["parameters"]["v_forward_V"],
                "forward_current_A": result["parameters"]["forward_current_A"],
                **result["metrics"],
                **result["normalized"],
                **result["stored_charge"],
                "converged": result["solver"]["converged"],
                "elapsed_s": result["solver"]["elapsed_s"],
            }
        )
        print(
            f"{result['case_id']}: If={result['parameters']['forward_current_A']:.3e} A, "
            f"Qrr/A={result['normalized']['Q_rr_density_C_cm2']:.3e} C/cm^2, "
            f"Irrm/A={result['normalized']['I_rrm_density_A_cm2']:.3e} A/cm^2, "
            f"elapsed={result['solver']['elapsed_s']:.2f}s"
        )
    write_json(
        Path("data/benchmark/metrics/metrics_forward_current_sweep.json"),
        results,
    )
    return results


def run_mesh_sweep(tau_s: float) -> list[dict]:
    config = load_config()
    results = []
    for mesh in config["sweeps"]["mesh_densities_cm"]:
        result = run_recovery(float(tau_s), mesh_density_cm=float(mesh))
        results.append(
            {
                "case_id": result["case_id"],
                "tau_s": float(tau_s),
                "mesh_density_cm": float(mesh),
                **result["metrics"],
                **result["normalized"],
                "converged": result["solver"]["converged"],
                "elapsed_s": result["solver"]["elapsed_s"],
            }
        )
        print(
            f"{result['case_id']}: Qrr={result['metrics']['Q_rr_C']:.3e} C, "
            f"Irrm={result['metrics']['I_rrm_A']:.3e} A, "
            f"elapsed={result['solver']['elapsed_s']:.2f}s"
        )
    write_json(Path("data/benchmark/metrics/metrics_mesh_sweep.json"), results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tau", type=float, default=1e-6)
    parser.add_argument("--dt", type=float)
    parser.add_argument("--mesh", type=float)
    parser.add_argument(
        "--sweep",
        choices=[
            "single",
            "lifetime",
            "lifetime-target-current",
            "time",
            "time-target-current",
            "forward-current",
            "mesh",
        ],
        default="single",
    )
    parser.add_argument(
        "--initial-condition",
        choices=["fixed_voltage", "target_current"],
        default="fixed_voltage",
    )
    parser.add_argument("--target-current", type=float)
    args = parser.parse_args()

    if args.sweep == "lifetime":
        run_lifetime_sweep()
        return
    if args.sweep == "lifetime-target-current":
        run_lifetime_sweep_target_current(args.target_current)
        return
    if args.sweep == "time":
        run_time_step_sweep(args.tau)
        return
    if args.sweep == "time-target-current":
        run_time_step_sweep(
            args.tau,
            initial_condition="target_current",
            target_current_a=args.target_current,
        )
        return
    if args.sweep == "forward-current":
        run_forward_current_sweep(args.tau)
        return
    if args.sweep == "mesh":
        run_mesh_sweep(args.tau)
        return

    result = run_recovery(
        args.tau,
        args.dt,
        args.mesh,
        initial_condition=args.initial_condition,
        target_current_a=args.target_current,
    )
    print(
        f"{result['case_id']}: {result['waveform']['points']} points, "
        f"Qrr={result['metrics']['Q_rr_C']:.3e} C, "
        f"Irrm={result['metrics']['I_rrm_A']:.3e} A, "
        f"Qstored={result['stored_charge']['stored_mobile_charge_C']:.3e} C, "
        f"converged={result['solver']['converged']}, "
        f"elapsed={result['solver']['elapsed_s']:.2f}s"
    )


if __name__ == "__main__":
    main()
