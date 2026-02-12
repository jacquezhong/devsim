# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_simulation.py - HgCdTe nBn Two-Color Infrared Detector
Based on: "Viability of HgCdTe-Based Two-Color nBn Infrared Detectors"
Journal of Electronic Materials (2025) 54:9174-9183
DOI: 10.1007/s11664-025-12289-5
"""

import os
import sys

# Configure MKL library path
mkl_path = r'C:\Users\zlh\.conda\envs\devsim\Library\bin'
if os.path.exists(mkl_path):
    os.environ['PATH'] = mkl_path + os.pathsep + os.environ.get('PATH', '')

# Import DEVSIM
import devsim
from devsim import *

# Physical constants
T = 100.0  # Temperature [K]
kb = 8.617e-5  # Boltzmann constant [eV/K]
Vt = kb * T    # Thermal voltage [V]
q = 1.602e-19  # Elementary charge [C]

print("="*70)
print("JEM2025 nBn Two-Color Infrared Detector Simulation")
print("="*70)
print(f"\nTemperature: {T} K")
print(f"Thermal voltage: {Vt:.6f} V")

# =============================================================================
# DEVICE GEOMETRY
# =============================================================================

# Layer thicknesses (um)
LWIR_t = 9.0
Barrier_t = 4.35
VLWIR_t = 14.0
total = LWIR_t + Barrier_t + VLWIR_t

print(f"\nDevice Geometry:")
print(f"  LWIR:    {LWIR_t} um")
print(f"  Barrier: {Barrier_t} um")
print(f"  VLWIR:   {VLWIR_t} um")
print(f"  Total:   {total} um")

# =============================================================================
# CREATE MESH
# =============================================================================

device_name = "nBn_Detector"
print("\nCreating mesh...")

create_1d_mesh(mesh="nBn_mesh")

# Mesh lines with varying resolution
add_1d_mesh_line(mesh="nBn_mesh", pos=0.0, ps=0.1, tag="bottom")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t/2, ps=0.2, tag="lwir_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t, ps=0.1, tag="lwir_barrier")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t + Barrier_t/2, ps=0.1, tag="barrier_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t + Barrier_t, ps=0.1, tag="barrier_vlwir")
add_1d_mesh_line(mesh="nBn_mesh", pos=total - VLWIR_t/2, ps=0.2, tag="vlwir_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=total, ps=0.1, tag="top")

# Regions
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR",
              tag1="bottom", tag2="lwir_barrier")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="Barrier",
              tag1="lwir_barrier", tag2="barrier_vlwir")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="VLWIR",
              tag1="barrier_vlwir", tag2="top")

# Contacts
add_1d_contact(mesh="nBn_mesh", name="bottom", tag="bottom", material="metal")
add_1d_contact(mesh="nBn_mesh", name="top", tag="top", material="metal")

# Interfaces
add_1d_interface(mesh="nBn_mesh", name="LWIR_Barrier", tag="lwir_barrier")
add_1d_interface(mesh="nBn_mesh", name="Barrier_VLWIR", tag="barrier_vlwir")

finalize_mesh(mesh="nBn_mesh")
create_device(mesh="nBn_mesh", device=device_name)

print(f"Device '{device_name}' created")

# =============================================================================
# MATERIAL PARAMETERS (from Table II)
# =============================================================================

print("\nSetting material parameters...")

# Permittivity (F/cm) - HgCdTe
epsilon = 14.5 * 8.854e-14

# Parameters from paper Table II
params = {
    "LWIR": {
        "Eg": 0.140,  # eV
        "Nd": 2.46e14,  # cm^-3
        "ni": 3.3e13,   # cm^-3
        "auger1": 3.784e-4,  # s
        "radiative": 1.561e-4,  # s
        "Ldiff": 197.6,  # um
        "R0A": 3.094,  # Ohm*cm^2
    },
    "Barrier": {
        "Eg": 0.285,  # eV
        "Nd": 5e15,   # cm^-3
        "ni": 2.0e10, # cm^-3
        "auger1": 3.171e-3,     # s
        "radiative": 9.433e-5,  # s
        "Ldiff": 48.7,   # um
        "R0A": None,
    },
    "VLWIR": {
        "Eg": 0.091,  # eV
        "Nd": 5e14,   # cm^-3
        "ni": 5.2e14, # cm^-3
        "auger1": 3.211e-5,     # s
        "radiative": 2.101e-4,  # s
        "Ldiff": 34.6,   # um
        "R0A": 0.307,  # Ohm*cm^2
    }
}

for region, p in params.items():
    set_parameter(device=device_name, region=region, name="Permittivity", value=epsilon)
    set_parameter(device=device_name, region=region, name="q", value=q)
    set_parameter(device=device_name, region=region, name="Eg", value=p["Eg"])
    set_parameter(device=device_name, region=region, name="Ndonor", value=p["Nd"])
    set_parameter(device=device_name, region=region, name="ni", value=p["ni"])
    set_parameter(device=device_name, region=region, name="T", value=T)
    print(f"  {region}: Eg={p['Eg']*1000:.0f} meV, Nd={p['Nd']:.2e} cm^-3")

# =============================================================================
# SET UP EQUATIONS (Poisson Equation)
# =============================================================================

print("\nSetting up equations...")

for region in ["LWIR", "Barrier", "VLWIR"]:
    # Potential solution
    node_solution(device=device_name, region=region, name="Potential")
    
    # Electric field
    edge_from_node_model(device=device_name, region=region, node_model="Potential")
    
    edge_model(device=device_name, region=region, name="Efield",
               equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")
    
    edge_model(device=device_name, region=region, name="Efield:Potential@n0",
               equation="EdgeInverseLength")
    edge_model(device=device_name, region=region, name="Efield:Potential@n1",
               equation="-EdgeInverseLength")
    
    # Displacement field
    edge_model(device=device_name, region=region, name="Dfield",
               equation="Permittivity*Efield")
    edge_model(device=device_name, region=region, name="Dfield:Potential@n0",
               equation="diff(Permittivity*Efield, Potential@n0)")
    edge_model(device=device_name, region=region, name="Dfield:Potential@n1",
               equation="-Dfield:Potential@n0")
    
    # Charge from ionized donors
    node_model(device=device_name, region=region, name="Charge",
               equation="q*Ndonor")

# Poisson equation
for region in ["LWIR", "Barrier", "VLWIR"]:
    equation(device=device_name, region=region, name="PoissonEq",
             variable_name="Potential",
             node_model="Charge",
             edge_model="Dfield",
             variable_update="default")

# =============================================================================
# BOUNDARY CONDITIONS
# =============================================================================

print("Setting boundary conditions...")

# Define bias parameter
set_parameter(device=device_name, name="Vbias", value=0.0)

# Bottom contact (ground, 0V)
# Define node model for bottom contact in LWIR region
node_model(device=device_name, region="LWIR", name="bottom_contact_model",
           equation="Potential - 0.0")
node_model(device=device_name, region="LWIR", name="bottom_contact_model:Potential",
           equation="1")

contact_equation(device=device_name, contact="bottom", name="PoissonEq",
                 node_model="bottom_contact_model",
                 edge_model="",
                 node_charge_model="",
                 edge_charge_model="Dfield",
                 node_current_model="",
                 edge_current_model="")

# Top contact (bias voltage)
# Define node model for top contact in VLWIR region
node_model(device=device_name, region="VLWIR", name="top_contact_model",
           equation="Potential - Vbias")
node_model(device=device_name, region="VLWIR", name="top_contact_model:Potential",
           equation="1")

contact_equation(device=device_name, contact="top", name="PoissonEq",
                 node_model="top_contact_model",
                 edge_model="",
                 node_charge_model="",
                 edge_charge_model="Dfield",
                 node_current_model="",
                 edge_current_model="")

# Interface conditions
for interface in ["LWIR_Barrier", "Barrier_VLWIR"]:
    interface_model(device=device_name, interface=interface, name="contPot",
                    equation="Potential@r0 - Potential@r1")
    interface_model(device=device_name, interface=interface, name="contPot:Potential@r0",
                    equation="1")
    interface_model(device=device_name, interface=interface, name="contPot:Potential@r1",
                    equation="-1")
    interface_equation(device=device_name, interface=interface, name="PoissonEq",
                       interface_model="contPot", type="continuous")

# =============================================================================
# SOLVE EQUILIBRIUM
# =============================================================================

print("\nSolving equilibrium...")

# Initial guess - set constant potential
for region in ["LWIR", "Barrier", "VLWIR"]:
    # Get node count for this region
    x_vals = get_node_model_values(device=device_name, region=region, name="x")
    if x_vals:
        n_nodes = len(x_vals)
        # Set all nodes to 0.0
        import numpy as np
        zero_values = np.zeros(n_nodes)
        set_node_values(device=device_name, region=region, name="Potential", values=zero_values)

# Solve
set_parameter(device=device_name, name="Vbias", value=0.0)
solve(type="dc", absolute_error=1e-10, relative_error=1e-10, maximum_iterations=30)

print("Equilibrium solution obtained")

# Get node positions and potential
x_LWIR = get_node_model_values(device=device_name, region="LWIR", name="x")
x_Barrier = get_node_model_values(device=device_name, region="Barrier", name="x")
x_VLWIR = get_node_model_values(device=device_name, region="VLWIR", name="x")

V_LWIR = get_node_model_values(device=device_name, region="LWIR", name="Potential")
V_Barrier = get_node_model_values(device=device_name, region="Barrier", name="Potential")
V_VLWIR = get_node_model_values(device=device_name, region="VLWIR", name="Potential")

print(f"\nEquilibrium potential range:")
print(f"  LWIR:    {min(V_LWIR):.6f} to {max(V_LWIR):.6f} V")
print(f"  Barrier: {min(V_Barrier):.6f} to {max(V_Barrier):.6f} V")
print(f"  VLWIR:   {min(V_VLWIR):.6f} to {max(V_VLWIR):.6f} V")

# =============================================================================
# I-V SIMULATION
# =============================================================================

print("\nRunning I-V sweep...")

import numpy as np

voltages = np.linspace(-0.5, 0.5, 11)
displacement_currents = []

for V in voltages:
    set_parameter(device=device_name, name="Vbias", value=V)
    solve(type="dc", absolute_error=1e-10, relative_error=1e-10, maximum_iterations=30)
    
    # Get displacement field at top contact
    D_vals = get_edge_model_values(device=device_name, region="VLWIR", name="Dfield")
    if D_vals and len(D_vals) > 0:
        J_disp = abs(D_vals[-1])  # Last edge
        displacement_currents.append(J_disp)
    else:
        displacement_currents.append(0.0)
    
    print(f"  V = {V:+.2f} V, D = {displacement_currents[-1]:.6e}")

displacement_currents = np.array(displacement_currents)

# =============================================================================
# COMPARISON WITH RULE 07
# =============================================================================

print("\n" + "="*70)
print("COMPARISON WITH PAPER RESULTS")
print("="*70)

# Rule 07 values from paper (at 100K)
Rule07_VLWIR = 0.0539  # A/cm^2
Rule07_LWIR = 0.0001   # A/cm^2

print(f"\nRule 07 Benchmark (at 100K):")
print(f"  VLWIR (14 um): {Rule07_VLWIR:.4e} A/cm^2")
print(f"  LWIR (9 um):   {Rule07_LWIR:.4e} A/cm^2")

print(f"\nNote:")
print("  This simplified Poisson solver calculates electrostatic potential")
print("  and displacement field. For accurate dark current prediction,")
print("  a full drift-diffusion model with carrier continuity equations")
print("  and recombination models (Auger, SRH, radiative) is required.")

print(f"\nKey findings from paper:")
print(f"  - Zero VBO between absorber and barrier")
print(f"  - Dark current below Rule 07 limits")
print(f"  - Bias-selectable dual-band operation")

# =============================================================================
# SAVE RESULTS
# =============================================================================

print("\nSaving results...")

# I-V data
with open("exp_oc/JEM2025_IV_data.txt", 'w') as f:
    f.write("# JEM2025 nBn Detector Simulation\n")
    f.write("# Simplified Poisson solver results\n")
    f.write(f"# Temperature: {T} K\n")
    f.write("# Voltage(V)  Displacement_Field\n")
    for V, D in zip(voltages, displacement_currents):
        f.write(f"{V:12.6f}  {D:18.6e}\n")

# Band diagram data
with open("exp_oc/JEM2025_band_diagram.txt", 'w') as f:
    f.write("# Band diagram at equilibrium (V=0)\n")
    f.write("# Position(um)  Potential(V)\n")
    f.write("# LWIR region\n")
    for x, V in zip(x_LWIR, V_LWIR):
        f.write(f"{x:12.6f}  {V:18.6e}\n")
    f.write("# Barrier region\n")
    for x, V in zip(x_Barrier, V_Barrier):
        f.write(f"{x:12.6f}  {V:18.6e}\n")
    f.write("# VLWIR region\n")
    for x, V in zip(x_VLWIR, V_VLWIR):
        f.write(f"{x:12.6f}  {V:18.6e}\n")

print("  Saved: exp_oc/JEM2025_IV_data.txt")
print("  Saved: exp_oc/JEM2025_band_diagram.txt")

# =============================================================================
# PLOT RESULTS
# =============================================================================

print("\nGenerating plots...")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # I-V plot
    ax1.plot(voltages, displacement_currents, 'b-o', linewidth=2, markersize=6, label='Simulation')
    ax1.set_xlabel('Bias Voltage (V)', fontsize=12)
    ax1.set_ylabel('Displacement Field (a.u.)', fontsize=12)
    ax1.set_title('I-V Characteristics', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Band diagram
    x_all = list(x_LWIR) + list(x_Barrier) + list(x_VLWIR)
    V_all = list(V_LWIR) + list(V_Barrier) + list(V_VLWIR)
    ax2.plot(x_all, V_all, 'g-', linewidth=2)
    ax2.axvline(x=LWIR_t, color='r', linestyle='--', alpha=0.5, label='LWIR/Barrier')
    ax2.axvline(x=LWIR_t+Barrier_t, color='r', linestyle='--', alpha=0.5, label='Barrier/VLWIR')
    ax2.set_xlabel('Position (um)', fontsize=12)
    ax2.set_ylabel('Potential (V)', fontsize=12)
    ax2.set_title('Band Diagram at Equilibrium', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('exp_oc/JEM2025_results.png', dpi=150, bbox_inches='tight')
    print("  Saved: exp_oc/JEM2025_results.png")
    
except Exception as e:
    print(f"  Could not create plots: {e}")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("SIMULATION SUMMARY")
print("="*70)

print(f"\nDevice: HgCdTe nBn Two-Color Infrared Detector")
print(f"Temperature: {T} K")

print(f"\nLayer Structure:")
print(f"  LWIR:    {LWIR_t} um, Eg={params['LWIR']['Eg']*1000:.0f} meV, Nd={params['LWIR']['Nd']:.2e} cm^-3")
print(f"  Barrier: {Barrier_t} um, Eg={params['Barrier']['Eg']*1000:.0f} meV, Nd={params['Barrier']['Nd']:.2e} cm^-3")
print(f"  VLWIR:   {VLWIR_t} um, Eg={params['VLWIR']['Eg']*1000:.0f} meV, Nd={params['VLWIR']['Nd']:.2e} cm^-3")

print(f"\nSimulation Results:")
print(f"  Equilibrium solved successfully")
print(f"  I-V sweep: {len(voltages)} points from -0.5V to +0.5V")

print(f"\nPaper Reference Values (Rule 07 at 100K):")
print(f"  VLWIR (14 um): {Rule07_VLWIR:.4e} A/cm^2")
print(f"  LWIR (9 um):   {Rule07_LWIR:.4e} A/cm^2")

print(f"\nFiles Generated:")
print(f"  - exp_oc/JEM2025_simulation.py (this script)")
print(f"  - exp_oc/JEM2025_IV_data.txt")
print(f"  - exp_oc/JEM2025_band_diagram.txt")
print(f"  - exp_oc/JEM2025_results.png")

print("\n" + "="*70)
print("SIMULATION COMPLETED SUCCESSFULLY")
print("="*70)
