#!/usr/bin/env python3
"""
Generate figures for the open reverse-recovery benchmark.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

PLAN_DIR = Path(__file__).resolve().parents[1]

plt.rcParams["font.sans-serif"] = ["Hiragino Sans GB", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["mathtext.default"] = "regular"
plt.rcParams["font.size"] = 9
plt.rcParams["axes.labelsize"] = 9
plt.rcParams["legend.fontsize"] = 8
plt.rcParams["xtick.labelsize"] = 8
plt.rcParams["ytick.labelsize"] = 8
plt.rcParams["lines.linewidth"] = 1.6
plt.rcParams["lines.markersize"] = 4.5

SCI = FuncFormatter(lambda value, _pos: f"{value:.0e}")
PLAIN = FuncFormatter(lambda value, _pos: f"{value:g}")


def save_figure(fig: plt.Figure, stem: str) -> None:
    out_dir = PLAN_DIR / "figures/benchmark"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{stem}.png", dpi=300)
    fig.savefig(out_dir / f"{stem}.pdf")
    plt.close(fig)


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def load_waveform(data: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    waveform = data["waveform"]
    if waveform.get("format") == "npz":
        npz_path = PLAN_DIR / waveform["file"]
        with np.load(npz_path) as arrays:
            return arrays["time_s"], arrays["voltage_V"], arrays["current_A"]
    return (
        np.asarray(waveform["time_s"], dtype=float),
        np.asarray(waveform["voltage_V"], dtype=float),
        np.asarray(waveform["current_A"], dtype=float),
    )


def default_case(data: dict) -> bool:
    params = data.get("parameters", {})
    return (
        np.isclose(params.get("time_step_s", np.nan), 2e-9, rtol=1e-12, atol=0.0)
        and np.isclose(params.get("mesh_density_cm", np.nan), 2e-7, rtol=1e-12, atol=0.0)
    )


def plot_dc() -> None:
    dc_files = sorted((PLAN_DIR / "data/benchmark/raw").glob("dc_tau_*.json"))
    if not dc_files:
        return
    fig, ax = plt.subplots(figsize=(7, 5))
    for path in dc_files:
        data = load_json(path)
        voltage = [p["voltage_V"] for p in data["points"]]
        current = [p["current_A"] for p in data["points"]]
        ax.semilogy(voltage, np.clip(current, 1e-40, None), marker="o", label=data["case_id"])
    ax.set_xlabel("Forward voltage (V)")
    ax.set_ylabel("Contact current (A)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = PLAN_DIR / "figures/benchmark/fig_dc_iv.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)
    plt.close(fig)


def plot_publication_dc() -> None:
    path = PLAN_DIR / "data/benchmark/raw/dc_tau_1e-06.json"
    if not path.exists():
        return
    data = load_json(path)
    voltage = np.asarray([p["voltage_V"] for p in data["points"]], dtype=float)
    current = np.asarray([p["current_A"] for p in data["points"]], dtype=float)
    mask = current > 0.0
    voltage = voltage[mask]
    current = current[mask]

    fig, ax = plt.subplots(figsize=(3.35, 2.55))
    ax.semilogy(voltage, current, marker="o", color="tab:blue")
    target = data["metrics"]["target_current_A"]
    vf = data["metrics"]["Vf_at_target_A"]
    ax.axhline(target, color="0.35", linestyle="--", linewidth=1.0)
    if vf is not None:
        ax.axvline(vf, color="0.35", linestyle=":", linewidth=1.0)
        ax.text(
            0.08,
            2e2,
            f"$V_F$={vf:.3f} V\n$I_F$={target:.0e} A",
            fontsize=7.5,
            va="center",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "0.75",
                "linewidth": 0.5,
                "alpha": 0.9,
            },
        )
    ax.set_xlabel("Forward voltage (V)")
    ax.set_ylabel("Contact current (A)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(1e-8, max(current) * 2.0)
    ax.yaxis.set_major_formatter(SCI)
    ax.grid(True, which="both", color="0.86", linewidth=0.6)
    fig.tight_layout()
    save_figure(fig, "fig_pub_dc_iv")


def plot_recovery_waveforms() -> None:
    raw_dir = PLAN_DIR / "data/benchmark/raw"
    files = sorted(raw_dir.glob("recovery_vfixed*.json"))
    files += sorted(raw_dir.glob("recovery_ifixed*.json"))
    if not files:
        files = sorted(raw_dir.glob("recovery*.json"))
    if not files:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    for path in files:
        data = load_json(path)
        time_s, _, current = load_waveform(data)
        time_ns = time_s * 1e9
        tau = data["parameters"]["taun_s"]
        initial_condition = data["parameters"].get("initial_condition", "legacy")
        ax.plot(time_ns, current, label=f"{initial_condition}, tau={tau:.0e}s")
    ax.set_xlabel("Time after reverse step (ns)")
    ax.set_ylabel("Contact current (A)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = PLAN_DIR / "figures/benchmark/fig_recovery_waveforms.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)
    plt.close(fig)


def load_default_waveforms(initial_condition: str) -> list[tuple[float, np.ndarray, np.ndarray]]:
    raw_dir = PLAN_DIR / "data/benchmark/raw"
    prefix = "recovery_ifixed" if initial_condition == "target_current" else "recovery_vfixed"
    waveforms = []
    for path in sorted(raw_dir.glob(f"{prefix}_tau_*.json")):
        data = load_json(path)
        if not default_case(data):
            continue
        time_s, _, current = load_waveform(data)
        tau = float(data["parameters"]["taun_s"])
        waveforms.append((tau, time_s, current))
    return sorted(waveforms, key=lambda row: row[0])


def plot_publication_recovery_waveforms() -> None:
    fixed_voltage = load_default_waveforms("fixed_voltage")
    target_current = load_default_waveforms("target_current")
    if not fixed_voltage and not target_current:
        return

    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.7), sharex=True)
    specs = [
        (axes[0], fixed_voltage, "Fixed-voltage initialization"),
        (axes[1], target_current, "Target-current initialization"),
    ]
    for ax, rows, title in specs:
        for tau, time_s, current in rows:
            time_ns = time_s * 1e9
            reverse_current = np.clip(-current, 1e-12, None)
            ax.semilogy(time_ns, reverse_current, marker="o", label=f"{tau:.0e} s")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Time after reverse step (ns)")
        ax.set_xlim(0.0, 10.0)
        ax.yaxis.set_major_formatter(SCI)
        ax.grid(True, which="both", color="0.86", linewidth=0.6)
        ax.legend(
            title="Lifetime",
            title_fontsize=8,
            frameon=False,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0.0,
        )
    axes[0].set_ylabel("Reverse current magnitude (A)")
    fig.tight_layout(w_pad=4.2)
    save_figure(fig, "fig_pub_recovery_waveforms")


def plot_lifetime_metrics() -> None:
    paths = [
        PLAN_DIR / "data/benchmark/metrics/metrics_lifetime_sweep.json",
        PLAN_DIR / "data/benchmark/metrics/metrics_lifetime_sweep_target_current.json",
    ]
    paths = [path for path in paths if path.exists()]
    if not paths:
        return

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for path in paths:
        metrics = load_json(path)
        label = "target current" if "target_current" in path.stem else "fixed voltage"
        tau = np.asarray([m["tau_s"] for m in metrics])
        qrr = np.asarray([m["Q_rr_C"] for m in metrics])
        irrm = np.asarray([m["I_rrm_A"] for m in metrics])
        trr = np.asarray([m["t_rr_s"] for m in metrics])
        for ax, y, ylabel in [
            (axes[0], qrr, "Qrr (C)"),
            (axes[1], irrm, "Irrm (A)"),
            (axes[2], trr, "trr (s)"),
        ]:
            ax.loglog(tau, np.clip(y, 1e-40, None), marker="o", label=label)
            ax.set_xlabel("Lifetime (s)")
            ax.set_ylabel(ylabel)
            ax.grid(True, which="both", alpha=0.3)
    for ax in axes:
        ax.legend(fontsize=8)
    fig.tight_layout()
    out = PLAN_DIR / "figures/benchmark/fig_lifetime_metrics.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)
    plt.close(fig)


def plot_publication_lifetime_summary() -> None:
    specs = [
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_lifetime_sweep.json",
            "Fixed voltage",
            "tab:blue",
        ),
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_lifetime_sweep_target_current.json",
            "Target current",
            "tab:orange",
        ),
    ]
    loaded = []
    for path, label, color in specs:
        if path.exists():
            loaded.append((load_json(path), label, color))
    if not loaded:
        return

    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.75))
    for metrics, label, color in loaded:
        tau = np.asarray([m["tau_s"] for m in metrics], dtype=float)
        qrr = np.asarray([m["Q_rr_C"] for m in metrics], dtype=float)
        stored = np.asarray([m["stored_mobile_charge_C"] for m in metrics], dtype=float)
        axes[0].loglog(tau, qrr, marker="o", color=color, label=label)
        axes[1].loglog(tau, stored, marker="o", color=color, label=label)

    axes[0].set_ylabel("$Q_{rr}$ (C)")
    axes[1].set_ylabel("Stored mobile charge (C)")
    for ax in axes:
        ax.set_xlabel("Carrier lifetime (s)")
        ax.xaxis.set_major_formatter(SCI)
        ax.yaxis.set_major_formatter(SCI)
        ax.grid(True, which="both", color="0.86", linewidth=0.6)
        ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    save_figure(fig, "fig_pub_lifetime_summary")


def plot_convergence() -> None:
    specs = [
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_time_step_sweep.json",
            "time_step_s",
            "Time step (s)",
            "fig_time_step_convergence.png",
        ),
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_mesh_sweep.json",
            "mesh_density_cm",
            "Junction mesh density (cm)",
            "fig_mesh_convergence.png",
        ),
    ]
    for path, key, xlabel, filename in specs:
        if not path.exists():
            continue
        data = load_json(path)
        x = np.asarray([row[key] for row in data], dtype=float)
        qrr = np.asarray([row["Q_rr_C"] for row in data], dtype=float)
        irrm = np.asarray([row["I_rrm_A"] for row in data], dtype=float)
        order = np.argsort(x)
        x = x[order]
        qrr = qrr[order]
        irrm = irrm[order]

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].loglog(x, np.clip(qrr, 1e-40, None), marker="o")
        axes[0].set_xlabel(xlabel)
        axes[0].set_ylabel("Qrr (C)")
        axes[0].grid(True, which="both", alpha=0.3)

        axes[1].loglog(x, np.clip(irrm, 1e-40, None), marker="o", color="tab:red")
        axes[1].set_xlabel(xlabel)
        axes[1].set_ylabel("Irrm (A)")
        axes[1].grid(True, which="both", alpha=0.3)

        fig.tight_layout()
        out = PLAN_DIR / "figures/benchmark" / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=300)
        plt.close(fig)


def plot_publication_convergence() -> None:
    specs = [
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_time_step_sweep.json",
            "time_step_s",
            "Time step (s)",
            "fig_pub_time_step_convergence",
        ),
        (
            PLAN_DIR / "data/benchmark/metrics/metrics_mesh_sweep.json",
            "mesh_density_cm",
            "Mesh density near transitions (cm)",
            "fig_pub_mesh_convergence",
        ),
    ]
    for path, key, xlabel, stem in specs:
        if not path.exists():
            continue
        data = load_json(path)
        x_values = np.asarray([row[key] for row in data], dtype=float)
        qrr = np.asarray([row["Q_rr_C"] for row in data], dtype=float)
        irrm = np.asarray([row["I_rrm_A"] for row in data], dtype=float)
        order = np.argsort(x_values)
        x_values = x_values[order]
        qrr = qrr[order]
        irrm = irrm[order]
        ref_idx = 0
        qrr_rel = 100.0 * np.abs(qrr / qrr[ref_idx] - 1.0)
        irrm_rel = 100.0 * np.abs(irrm / irrm[ref_idx] - 1.0)
        x = np.arange(len(x_values), dtype=float)
        xlabels = [f"{value:.0e}" for value in x_values]

        fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.65), sharex=True)
        axes[0].plot(x, qrr_rel, marker="o", color="tab:blue")
        axes[1].plot(x, irrm_rel, marker="o", color="tab:red")
        axes[0].set_ylabel("$Q_{rr}$ relative change (%)")
        axes[1].set_ylabel("$I_{rrm}$ relative change (%)")
        for ax in axes:
            ax.set_xlabel(xlabel)
            ax.set_xticks(x)
            ax.set_xticklabels(xlabels)
            ax.yaxis.set_major_formatter(PLAIN)
            ax.grid(True, which="both", color="0.86", linewidth=0.6)
        fig.tight_layout()
        save_figure(fig, stem)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-diagnostic",
        action="store_true",
        help="also regenerate the older diagnostic figures",
    )
    args = parser.parse_args()

    if args.include_diagnostic:
        plot_dc()
        plot_recovery_waveforms()
        plot_lifetime_metrics()
        plot_convergence()
    plot_publication_dc()
    plot_publication_recovery_waveforms()
    plot_publication_lifetime_summary()
    plot_publication_convergence()
    print("Publication benchmark figures generated in figures/benchmark")


if __name__ == "__main__":
    main()
