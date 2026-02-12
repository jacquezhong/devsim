# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_simple.py - Simplified HgCdTe nBn Detector Simulation
Based on JEM2025 paper parameters
"""

import os
import sys

# Add MKL library path for DEVSIM
mkl_path = r'C:\Users\zlh\.conda\envs\devsim\Library\bin'
if os.path.exists(mkl_path) and mkl_path not in os.environ.get('PATH', ''):
    os.environ['PATH'] = mkl_path + os.pathsep + os.environ.get('PATH', '')

# Import DEVSIM
try:
    import devsim
    from devsim import *
    print("DEVSIM imported successfully")
except Exception as e:
    print(f"Error importing DEVSIM: {e}")
    print("Trying alternative import...")
    # Try setting environment variable
    os.environ['DEVSIM_MATH_LIBS'] = 'mkl_rt.2.dll'
    import devsim
    from devsim import *

import numpy as np

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

T = 100.0  # Temperature [K]
kb = 8.617e-5  # Boltzmann constant [eV/K]
Vt = kb * T    # Thermal voltage [V]
q = 1.602e-19  # Elementary charge [C]

print(f"\nTemperature: {T} K")
print(f"Thermal voltage (kT/q): {Vt:.6f} V")

# =============================================================================
# DEVICE GEOMETRY (1D)
# =============================================================================

# Layer thicknesses (in µm)
LWIR_thickness = 9.0
Barrier_thickness = 4.35
VLWIR_thickness = 14.0
total_length = LWIR_thickness + Barrier_thickness + VLWIR_thickness

print(f"\nDevice structure:")
print(f"  LWIR:    {LWIR_thickness} µm")
print(f"  Barrier: {Barrier_thickness} µm")
print(f"  VLWIR:   {VLWIR_thickness} µm")
print(f"  Total:   {total_length} µm")

# =============================================================================
# CREATE MESH
# =============================================================================

device_name = "nBn_Detector"

print("\nCreating mesh...")

# Simple mesh with uniform spacing
create_1d_mesh(mesh="nBn_mesh")

# Bottom contact at x=0
add_1d_mesh_line(mesh="nBn_mesh", pos=0.0, ps=0.1, tag="bottom")

# LWIR region
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_thickness/2, ps=0.2, tag="lwir_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_thickness, ps=0.1, tag="lwir_barrier")

# Barrier region
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_thickness + Barrier_thickness/2, ps=0.1, tag="barrier_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_thickness + Barrier_thickness, ps=0.1, tag="barrier_vlwir")

# VLWIR region
add_1d_mesh_line(mesh="nBn_mesh", pos=total_length - VLWIR_thickness/2, ps=0.2, tag="vlwir_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=total_length, ps=0.1, tag="top")

# Define regions
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR",
              tag1="bottom", tag2="lwir_barrier")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="Barrier",
              tag1="lwir_barrier", tag2="barrier_vlwir")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="VLWIR",
              tag1="barrier_vlwir", tag2="top")

# Define contacts
add_1d_contact(mesh="nBn_mesh", name="bottom", tag="bottom", material="metal")
add_1d_contact(mesh="nBn_mesh", name="top", tag="top", material="metal")

# Define interfaces
add_1d_interface(mesh="nBn_mesh", name="LWIR_Barrier", tag="lwir_barrier")
add_1d_interface(mesh="nBn_mesh", name="Barrier_VLWIR", tag="barrier_vlwir")

# Finalize
finalize_mesh(mesh="nBn_mesh")
create_device(mesh="nBn_mesh", device=device_name)

print(f"Device '{device_name}' created successfully")

# =============================================================================
# SET PARAMETERS (simplified capacitor model first)
# =============================================================================

print("\nSetting parameters...")

# Permittivity (F/cm) - approximate for HgCdTe
epsilon = 14.5 * 8.854e-14

# Doping concentrations (cm^-3) from Table II
LWIR_doping = 2.46e14
Barrier_doping = 5e15
VLWIR_doping = 5e14

for region, doping in [("LWIR", LWIR_doping), ("Barrier", Barrier_doping), ("VLWIR", VLWIR_doping)]:
    set_parameter(device=device_name, region=region, name="Permittivity", value=epsilon)
    set_parameter(device=device_name, region=region, name="Ndonor", value=doping)
    set_parameter(device=device_name, region=region, name="T", value=T)
    print(f"  {region}: Nd = {doping:.2e} cm^-3")

# =============================================================================
# SET UP EQUATIONS (Poisson only for initial test)
# =============================================================================

print("\nSetting up Poisson equation...")

for region in ["LWIR", "Barrier", "VLWIR"]:
    # Potential solution
    node_solution(device=device_name, region=region, name="Potential")
    
    # Electric field
    edge_from_node_model(device=device_name, region=region, node_model="Potential")
    
    edge_model(device=device_name, region=region, name="ElectricField",
               equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")
    
    edge_model(device=device_name, region=region, name="ElectricField:Potential@n0",
               equation="EdgeInverseLength")
    edge_model(device=device_name, region=region, name="ElectricField:Potential@n1",
               equation="-EdgeInverseLength")
    
    # Displacement field D = epsilon * E
    edge_model(device=device_name, region=region, name="Dfield",
               equation="Permittivity*ElectricField")
    edge_model(device=device_name, region=region, name="Dfield:Potential@n0",
               equation="diff(Permittivity*ElectricField, Potential@n0)")
    edge_model(device=device_name, region=region, name="Dfield:Potential@n1",
               equation="-Dfield:Potential@n0")
    
    # Charge density (donors only for now)
    node_model(device=device_name, region=region, name="ChargeDensity",
               equation="q*Ndonor")

# Poisson equation: div(D) = rho
for region in ["LWIR", "Barrier", "VLWIR"]:
    equation(device=device_name, region=region, name="PoissonEquation",
             variable_name="Potential",
             node_model="ChargeDensity",
             edge_model="Dfield",
             variable_update="default")

# =============================================================================
# CONTACT BOUNDARY CONDITIONS
# =============================================================================

print("Setting up boundary conditions...")

# Ground at bottom
contact_equation(device=device_name, contact="bottom", name="PoissonEquation",
                 node_model="Potential",
                 edge_model="")

# Bias at top (will vary for I-V)
set_parameter(device=device_name, name="Vbias", value=0.0)
contact_equation(device=device_name, contact="top", name="PoissonEquation",
                 node_model="Potential - Vbias",
                 edge_model="")

# =============================================================================
# INTERFACE CONDITIONS (continuous potential)
# =============================================================================

for interface in ["LWIR_Barrier", "Barrier_VLWIR"]:
    interface_model(device=device_name, interface=interface, name="continuousPotential",
                    equation="Potential@r0 - Potential@r1")
    interface_model(device=device_name, interface=interface, name="continuousPotential:Potential@r0",
                    equation="1")
    interface_model(device=device_name, interface=interface, name="continuousPotential:Potential@r1",
                    equation="-1")
    interface_equation(device=device_name, interface=interface, name="PoissonEquation",
                       interface_model="continuousPotential", type="continuous")

# =============================================================================
# SOLVE EQUILIBRIUM
# =============================================================================

print("\nSolving equilibrium...")

# Initial guess
for region in ["LWIR", "Barrier", "VLWIR"]:
    set_node_values(device=device_name, region=region, name="Potential", value=0.0)

# Solve at 0V
set_parameter(device=device_name, name="Vbias", value=0.0)
solve(type="dc", absolute_error=1e-10, relative_error=1e-10, maximum_iterations=30)

print("✓ Equilibrium solution obtained")

# =============================================================================
# I-V SIMULATION
# =============================================================================

print("\nRunning I-V sweep...")

# Voltage sweep (V)
voltages = np.linspace(-0.5, 0.5, 11)
currents = []

for V in voltages:
    set_parameter(device=device_name, name="Vbias", value=V)
    solve(type="dc", absolute_error=1e-10, relative_error=1e-10, maximum_iterations=30)
    
    # Get displacement current (simplified)
    # For a real device, you'd calculate electron/hole currents
    D_field = get_edge_model_values(device=device_name, region="VLWIR", name="Dfield")
    if D_field:
        current = abs(D_field[-1])  # Last edge value
        currents.append(current)
        print(f"  V = {V:+.2f} V, D = {current:.4e}")
    else:
        currents.append(0.0)

currents = np.array(currents)

# =============================================================================
# COMPARISON WITH RULE 07
# =============================================================================

print("\n" + "="*60)
print("COMPARISON WITH PAPER RESULTS")
print("="*60)

# Rule 07 values from paper (at 100K)
Rule07_VLWIR = 0.0539  # A/cm^2
Rule07_LWIR = 0.0001   # A/cm^2

# Note: This simplified model doesn't calculate actual dark current
# A full drift-diffusion model would be needed for accurate comparison

print(f"\nRule 07 Benchmark (from paper):")
print(f"  VLWIR (14 µm): {Rule07_VLWIR:.4e} A/cm²")
print(f"  LWIR (9 µm):   {Rule07_LWIR:.4e} A/cm²")

print(f"\nNote: This simplified Poisson solver doesn't calculate")
print(f"dark current directly. A full drift-diffusion model")
print(f"would be needed for accurate I-V characteristics.")

# =============================================================================
# SAVE RESULTS
# =============================================================================

output_file = "exp_oc/JEM2025_simple_results.txt"
with open(output_file, 'w') as f:
    f.write("# JEM2025 nBn Detector - Simplified Simulation\n")
    f.write(f"# Temperature: {T} K\n")
    f.write("#\n")
    f.write("# Voltage(V)  Current(A/cm2)\n")
    for V, J in zip(voltages, currents):
        f.write(f"{V:12.6f}  {J:18.6e}\n")

print(f"\nResults saved to: {output_file}")

# =============================================================================
# PLOT
# =============================================================================

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 6))
    plt.plot(voltages, currents, 'b-o', linewidth=2, markersize=6)
    plt.xlabel('Bias Voltage (V)', fontsize=12)
    plt.ylabel('Displacement Field (a.u.)', fontsize=12)
    plt.title('JEM2025 nBn Detector - Simplified I-V Characteristics', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('exp_oc/JEM2025_simple_plot.png', dpi=150, bbox_inches='tight')
    print("Plot saved to: exp_oc/JEM2025_simple_plot.png")
except Exception as e:
    print(f"Could not create plot: {e}")

print("\n" + "="*60)
print("SIMULATION COMPLETED")
print("="*60)
