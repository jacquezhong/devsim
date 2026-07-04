#!/usr/bin/env python3
"""
Metric extraction for the open diode reverse-recovery benchmark.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def _as_array(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=float)


def extract_recovery_metrics(
    time_s: list[float],
    current_a: list[float],
    reverse_start_s: float = 0.0,
    threshold_fraction: float = 0.1,
) -> dict[str, Any]:
    """Extract I_rrm, Q_rr, and t_rr from a reverse-recovery waveform.

    Current convention: forward current is positive and reverse recovery is
    negative. If the waveform has no negative current, the returned metrics are
    flagged as having no recovery event.
    """
    time = _as_array(time_s)
    current = _as_array(current_a)

    if time.size == 0 or current.size == 0 or time.size != current.size:
        raise ValueError("time_s and current_a must be non-empty arrays of equal length")

    mask = time >= reverse_start_s
    if not np.any(mask):
        raise ValueError("reverse_start_s is outside the waveform time range")

    t = time[mask]
    i = current[mask]

    peak_idx = int(np.argmin(i))
    peak_current = float(i[peak_idx])
    i_rrm = float(abs(min(peak_current, 0.0)))

    if i_rrm == 0.0:
        return {
            "I_rrm_A": 0.0,
            "Q_rr_C": 0.0,
            "t_rr_s": 0.0,
            "t_peak_s": float(t[peak_idx]),
            "t_end_s": float(t[0]),
            "threshold_fraction": threshold_fraction,
            "recovery_incomplete": False,
            "has_reverse_recovery": False,
        }

    threshold = -threshold_fraction * i_rrm
    end_idx = len(i) - 1
    recovery_incomplete = True
    for idx in range(peak_idx, len(i)):
        if i[idx] >= threshold:
            end_idx = idx
            recovery_incomplete = False
            break

    t_int = t[: end_idx + 1]
    i_int = i[: end_idx + 1]
    reverse_current = np.clip(-i_int, 0.0, None)
    q_rr = float(np.trapezoid(reverse_current, t_int))

    return {
        "I_rrm_A": i_rrm,
        "Q_rr_C": q_rr,
        "t_rr_s": float(t[end_idx] - t[0]),
        "t_peak_s": float(t[peak_idx]),
        "t_end_s": float(t[end_idx]),
        "threshold_fraction": threshold_fraction,
        "recovery_incomplete": recovery_incomplete,
        "has_reverse_recovery": True,
    }


def extract_dc_metrics(
    voltage_v: list[float],
    current_a: list[float],
    target_current_a: float,
) -> dict[str, Any]:
    """Extract target forward voltage and a local differential resistance."""
    voltage = _as_array(voltage_v)
    current = _as_array(current_a)

    order = np.argsort(voltage)
    voltage = voltage[order]
    current = current[order]

    target_not_reached = target_current_a > float(np.max(current))
    vf = None
    if not target_not_reached:
        vf = float(np.interp(target_current_a, current, voltage))

    r_diff = None
    if len(voltage) >= 3:
        gradients = np.gradient(voltage, current, edge_order=1)
        finite = gradients[np.isfinite(gradients)]
        if finite.size:
            r_diff = float(np.median(finite))

    return {
        "target_current_A": target_current_a,
        "Vf_at_target_A": vf,
        "target_not_reached": target_not_reached,
        "R_diff_ohm": r_diff,
        "max_current_A": float(np.max(current)),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("waveform_json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--threshold", type=float, default=0.1)
    args = parser.parse_args()

    with args.waveform_json.open() as f:
        data = json.load(f)

    metrics = extract_recovery_metrics(
        data["waveform"]["time_s"],
        data["waveform"]["current_A"],
        threshold_fraction=args.threshold,
    )
    data["metrics"] = metrics

    output = args.output or args.waveform_json
    with output.open("w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
