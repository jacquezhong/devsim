#!/usr/bin/env python3
"""
Shared DEVSIM setup for the plan1 reverse-recovery benchmark.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PLAN_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".opencode" / "skills" / "devsim-examples"))

import devsim  # noqa: E402
from devsim.python_packages.model_create import CreateNodeModel  # noqa: E402
from devsim.python_packages.simple_physics import (  # noqa: E402
    CreateSiliconDriftDiffusion,
    CreateSiliconDriftDiffusionAtContact,
    CreateSiliconPotentialOnly,
    CreateSiliconPotentialOnlyContact,
    GetContactBiasName,
    SetSiliconParameters,
)
from devsim.python_packages.simple_physics import ece_name, hce_name  # noqa: E402
from devsim.python_packages.model_create import CreateSolution  # noqa: E402


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or PLAN_DIR / "benchmark" / "config.json"
    with config_path.open() as f:
        return json.load(f)


def ensure_dirs() -> None:
    for rel in [
        "data/benchmark/raw",
        "data/benchmark/waveforms",
        "data/benchmark/metrics",
        "data/benchmark/reference",
        "figures/benchmark",
    ]:
        (PLAN_DIR / rel).mkdir(parents=True, exist_ok=True)


def cleanup(mesh_name: str, device_name: str) -> None:
    for action, kwargs in [
        (devsim.delete_device, {"device": device_name}),
        (devsim.delete_mesh, {"mesh": mesh_name}),
    ]:
        try:
            action(**kwargs)
        except Exception:
            pass


def create_mesh(device: dict[str, Any]) -> None:
    mesh = device["mesh_name"]
    devsim.create_1d_mesh(mesh=mesh)
    devsim.add_1d_mesh_line(mesh=mesh, pos=0.0, ps=1e-7, tag="top")
    if device.get("profile", "pn") == "pin":
        p_end = device["p_width_cm"]
        n_start = device["device_length_cm"] - device["n_width_cm"]
        devsim.add_1d_mesh_line(mesh=mesh, pos=p_end, ps=device["mesh_density_cm"], tag="p_i")
        devsim.add_1d_mesh_line(mesh=mesh, pos=n_start, ps=device["mesh_density_cm"], tag="i_n")
    else:
        devsim.add_1d_mesh_line(
            mesh=mesh,
            pos=device["junction_position_cm"],
            ps=device["mesh_density_cm"],
            tag="mid",
        )
    devsim.add_1d_mesh_line(
        mesh=mesh,
        pos=device["device_length_cm"],
        ps=1e-7,
        tag="bot",
    )
    devsim.add_1d_contact(mesh=mesh, name="top", tag="top", material="metal")
    devsim.add_1d_contact(mesh=mesh, name="bot", tag="bot", material="metal")
    devsim.add_1d_region(
        mesh=mesh,
        material="Si",
        region=device["region_name"],
        tag1="top",
        tag2="bot",
    )
    devsim.finalize_mesh(mesh=mesh)
    devsim.create_device(mesh=mesh, device=device["device_name"])


def set_doping(config: dict[str, Any]) -> None:
    device = config["device"]
    device_name = device["device_name"]
    region = device["region_name"]
    p_doping = device["p_doping_cm3"]
    n_doping = device["n_doping_cm3"]
    if device.get("profile", "pn") == "pin":
        p_end = device["p_width_cm"]
        n_start = device["device_length_cm"] - device["n_width_cm"]
        i_doping = device.get("i_doping_cm3", 0.0)
        CreateNodeModel(device_name, region, "Acceptors", f"{p_doping}*step({p_end}-x)")
        CreateNodeModel(device_name, region, "Donors", f"{n_doping}*step(x-{n_start}) + {i_doping}*step(x-{p_end})*step({n_start}-x)")
    else:
        junction = device["junction_position_cm"]
        CreateNodeModel(device_name, region, "Acceptors", f"{p_doping}*step({junction}-x)")
        CreateNodeModel(device_name, region, "Donors", f"{n_doping}*step(x-{junction})")
    CreateNodeModel(device_name, region, "NetDoping", "Donors-Acceptors")


def setup_device(config: dict[str, Any], tau_s: float | None = None) -> None:
    device = config["device"]
    device_name = device["device_name"]
    region = device["region_name"]
    cleanup(device["mesh_name"], device_name)
    create_mesh(device)
    SetSiliconParameters(device_name, region, device["temperature_K"])
    if tau_s is not None:
        devsim.set_parameter(device=device_name, region=region, name="taun", value=tau_s)
        devsim.set_parameter(device=device_name, region=region, name="taup", value=tau_s)

    set_doping(config)

    CreateSolution(device_name, region, "Potential")
    CreateSiliconPotentialOnly(device_name, region)
    for contact in ("top", "bot"):
        devsim.set_parameter(device=device_name, name=GetContactBiasName(contact), value=0.0)
        CreateSiliconPotentialOnlyContact(device_name, region, contact)
    devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=50)

    for solution in ("Electrons", "Holes"):
        CreateSolution(device_name, region, solution)
    devsim.set_node_values(device=device_name, region=region, name="Electrons", init_from="IntrinsicElectrons")
    devsim.set_node_values(device=device_name, region=region, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(device_name, region)
    for contact in ("top", "bot"):
        CreateSiliconDriftDiffusionAtContact(device_name, region, contact)
    devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=50)


def set_top_bias(config: dict[str, Any], voltage: float) -> None:
    devsim.set_parameter(
        device=config["device"]["device_name"],
        name=GetContactBiasName("top"),
        value=voltage,
    )


def solve_dc(max_iterations: int = 50) -> bool:
    info = devsim.solve(
        type="dc",
        absolute_error=1e10,
        relative_error=1e-10,
        maximum_iterations=max_iterations,
    )
    return True if info is None else bool(info.get("converged", True))


def solve_transient(tdelta: float, max_iterations: int = 50) -> bool:
    info = devsim.solve(
        type="transient_bdf1",
        absolute_error=1e10,
        relative_error=1e-10,
        maximum_iterations=max_iterations,
        tdelta=tdelta,
        charge_error=1,
    )
    return True if info is None else bool(info.get("converged", True))


def initialize_transient() -> bool:
    info = devsim.solve(
        type="transient_dc",
        absolute_error=1e10,
        relative_error=1e-10,
        maximum_iterations=50,
    )
    return True if info is None else bool(info.get("converged", True))


def contact_current(config: dict[str, Any], contact: str = "top") -> float:
    device_name = config["device"]["device_name"]
    electron = devsim.get_contact_current(device=device_name, contact=contact, equation=ece_name)
    hole = devsim.get_contact_current(device=device_name, contact=contact, equation=hce_name)
    # Benchmark convention: positive current is the forward current measured at
    # the top contact for the default PN orientation.
    return float(electron + hole)


def get_node_array(config: dict[str, Any], name: str) -> np.ndarray:
    device = config["device"]
    values = devsim.get_node_model_values(
        device=device["device_name"],
        region=device["region_name"],
        name=name,
    )
    return np.asarray(values, dtype=float)


def carrier_profile(config: dict[str, Any]) -> dict[str, np.ndarray]:
    return {
        "x_cm": get_node_array(config, "x"),
        "node_volume_cm3": get_node_array(config, "NodeVolume"),
        "electrons_cm3": get_node_array(config, "Electrons"),
        "holes_cm3": get_node_array(config, "Holes"),
    }


def stored_mobile_charge_c(
    config: dict[str, Any],
    reference: dict[str, np.ndarray],
    profile: dict[str, np.ndarray] | None = None,
) -> dict[str, float]:
    """Integrate excess mobile charge relative to a reference state.

    The benchmark reports q * integral(max(n-n0, 0) + max(p-p0, 0)) dV.
    This is a diagnostic for stored plasma, not a replacement for terminal
    charge accounting in a calibrated power-diode model.
    """
    current = profile or carrier_profile(config)
    q = float(
        devsim.get_parameter(
            device=config["device"]["device_name"],
            region=config["device"]["region_name"],
            name="ElectronCharge",
        )
    )
    volume = current["node_volume_cm3"]
    excess_electrons = np.clip(
        current["electrons_cm3"] - reference["electrons_cm3"], 0.0, None
    )
    excess_holes = np.clip(current["holes_cm3"] - reference["holes_cm3"], 0.0, None)
    electron_charge = q * float(np.sum(excess_electrons * volume))
    hole_charge = q * float(np.sum(excess_holes * volume))
    return {
        "stored_electron_charge_C": electron_charge,
        "stored_hole_charge_C": hole_charge,
        "stored_mobile_charge_C": electron_charge + hole_charge,
        "node_count": int(volume.size),
    }


def device_parameters(config: dict[str, Any], tau_s: float | None = None) -> dict[str, Any]:
    device = dict(config["device"])
    if tau_s is not None:
        device["taun_s"] = tau_s
        device["taup_s"] = tau_s
    return device


def write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def write_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def chdir_plan() -> None:
    os.chdir(PLAN_DIR)
