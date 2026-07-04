#!/usr/bin/env python3
"""
Run the Level 0 DC I-V benchmark and save actual contact currents.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from benchmark_common import (
    chdir_plan,
    contact_current,
    device_parameters,
    ensure_dirs,
    load_config,
    set_top_bias,
    setup_device,
    solve_dc,
    write_json,
)
from extract_metrics import extract_dc_metrics


def run_dc(tau_s: float, output: Path | None = None) -> dict:
    chdir_plan()
    ensure_dirs()
    config = load_config()
    dc = config["dc"]
    setup_device(config, tau_s=tau_s)

    voltages = np.arange(
        dc["start_voltage_V"],
        dc["stop_voltage_V"] + 0.5 * dc["step_voltage_V"],
        dc["step_voltage_V"],
    )

    started = time.perf_counter()
    points = []
    converged = True
    failed_at = None
    for voltage in voltages:
        set_top_bias(config, float(voltage))
        ok = solve_dc()
        current = contact_current(config)
        points.append(
            {
                "voltage_V": float(voltage),
                "current_A": current,
                "converged": ok,
            }
        )
        if not ok:
            converged = False
            failed_at = float(voltage)
            break

    elapsed = time.perf_counter() - started
    metrics = extract_dc_metrics(
        [p["voltage_V"] for p in points],
        [p["current_A"] for p in points],
        dc["target_current_A"],
    )

    result = {
        "case_id": f"dc_tau_{tau_s:.0e}",
        "parameters": device_parameters(config, tau_s),
        "dc": dc,
        "points": points,
        "metrics": metrics,
        "solver": {
            "converged": converged,
            "failed_at_voltage_V": failed_at,
            "elapsed_s": elapsed,
        },
    }
    output_path = output or Path("data/benchmark/raw") / f"dc_tau_{tau_s:.0e}.json"
    write_json(output_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tau", type=float, default=1e-6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_dc(args.tau, args.output)
    print(
        f"{result['case_id']}: {len(result['points'])} points, "
        f"converged={result['solver']['converged']}, "
        f"elapsed={result['solver']['elapsed_s']:.2f}s"
    )


if __name__ == "__main__":
    main()
