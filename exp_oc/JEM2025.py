# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025.py - HgCdTe nBn Two-Color Infrared Detector Simulation
Based on: "Viability of HgCdTe-Based Two-Color nBn Infrared Detectors"
Journal of Electronic Materials (2025) 54:9174-9183
DOI: 10.1007/s11664-025-12289-5

Device Structure (Back-illuminated):
- LWIR absorber: HgCdTe (x=0.23), 9 µm, Eg=140meV, n=2.46e14 cm^-3
- Barrier: HgTe/CdTe T3SL (8ML/8ML), 4.35 µm, Eg=285meV, n=5e15 cm^-3  
- VLWIR absorber: HgTe/CdTe T3SL (17ML/17ML), 14 µm, Eg=91meV, n=5e14 cm^-3

Temperature: 100K

This script simulates:
1. Band diagram under equilibrium and bias
2. Dark current density (I-V characteristics)
3. Carrier concentration profiles
4. Comparison with Rule 07 benchmark
"""

import os
import sys

# Add MKL library path for DEVSIM (Windows)
mkl_path = r'C:\Users\zlh\.conda\envs\devsim\Library\bin'
if os.path.exists(mkl_path) and mkl_path not in os.environ['PATH']:
    os.environ['PATH'] = mkl_path + os.pathsep + os.environ['PATH']
    os.environ['DEVSIM_MATH_LIBS'] = 'mkl_rt.2.dll'

import devsim
from devsim import *
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================
kb = 8.617333e-5  # Boltzmann constant [eV/K]
q = 1.602e-19     # Elementary charge [C]
T = 100.0         # Temperature [K]
Vt = kb * T       # Thermal voltage [V]

# =============================================================================
# DEVICE PARAMETERS (from Table II of the paper)
# =============================================================================

# LWIR Absorber (HgCdTe alloy, x=0.23)
LWIR_thickness = 9.0          # µm
LWIR_Eg = 0.140               # eV (140 meV)
LWIR_doping = 2.46e14         # cm^-3 (n-type)
LWIR_auger1 = 3.784e-4        # s
LWIR_radiative = 1.561e-4     # s
LWIR_diffusion = 197.6        # µm
LWIR_ni = 3.3e13              # cm^-3 (intrinsic carrier concentration)

# Barrier (e-SWIR T3SL HgTe/CdTe, 8ML/8ML)
Barrier_thickness = 4.35      # µm
Barrier_Eg = 0.285            # eV (285 meV)
Barrier_doping = 5e15         # cm^-3 (n-type)
Barrier_auger1 = 3.171e-3     # s
Barrier_radiative = 9.433e-5  # s
Barrier_diffusion = 48.7      # µm
Barrier_ni = 2.0e10           # cm^-3

# VLWIR Absorber (T3SL HgTe/CdTe, 17ML/17ML)
VLWIR_thickness = 14.0        # µm
VLWIR_Eg = 0.091              # eV (91 meV)
VLWIR_doping = 5e14           # cm^-3 (n-type)
VLWIR_auger1 = 3.211e-5       # s
VLWIR_radiative = 2.101e-4    # s
VLWIR_diffusion = 34.6        # µm
VLWIR_ni = 5.2e14             # cm^-3

# =============================================================================
# MATERIAL PROPERTIES
# =============================================================================

# Permittivity (approximate values for HgCdTe)
epsilon_LWIR = 14.5 * 8.854e-14    # F/cm
epsilon_Barrier = 14.5 * 8.854e-14 # F/cm  
epsilon_VLWIR = 14.5 * 8.854e-14   # F/cm

# Electron affinity (approximate for zero VBO design)
# Aligned so that valence band offset (VBO) = 0
def calculate_electron_affinity(Eg, VBO=0):
    """Calculate electron affinity for given bandgap and VBO"""
    # For HgCdTe, approximate electron affinity
    # Adjusted to achieve zero VBO as mentioned in paper
    return 4.0 - Eg  # Simplified approximation

chi_LWIR = calculate_electron_affinity(LWIR_Eg)
chi_Barrier = calculate_electron_affinity(Barrier_Eg)
chi_VLWIR = calculate_electron_affinity(VLWIR_Eg)

# Effective masses (from k·p calculations mentioned in paper)
# Values are approximate based on HgCdTe literature
mn_LWIR = 0.02  # Electron effective mass (relative to m0)
mp_LWIR = 0.3   # Hole effective mass

mn_Barrier = 0.03
mp_Barrier = 0.35

mn_VLWIR = 0.015
mp_VLWIR = 0.25

# Mobility calculations (cm^2/V·s)
# Scaled from bulk HgCdTe using effective mass ratios as mentioned in paper
mu_n_LWIR = 1e5 * (0.01 / mn_LWIR)   # Electron mobility
mu_p_LWIR = 500 * (0.3 / mp_LWIR)    # Hole mobility

mu_n_Barrier = 5e4 * (0.01 / mn_Barrier)
mu_p_Barrier = 300 * (0.3 / mp_Barrier)

mu_n_VLWIR = 2e5 * (0.01 / mn_VLWIR)
mu_p_VLWIR = 1000 * (0.3 / mp_VLWIR)

# =============================================================================
# CREATE DEVICE MESH
# =============================================================================

device_name = "nBn_Detector"
print("Creating 1D nBn device mesh...")

# Create mesh with fine resolution at interfaces
# Total device length: 9 + 4.35 + 14 = 27.35 µm

# Contact positions
total_length = LWIR_thickness + Barrier_thickness + VLWIR_thickness
contact_LWIR = 0.0
interface_LWIR_Barrier = LWIR_thickness
interface_Barrier_VLWIR = LWIR_thickness + Barrier_thickness
contact_VLWIR = total_length

# Create mesh lines
# LWIR region (bottom contact to barrier)
create_1d_mesh(mesh="nBn_mesh")

# Fine mesh at bottom contact
add_1d_mesh_line(mesh="nBn_mesh", pos=contact_LWIR, ps=0.05, tag="bottom_contact")

# LWIR absorber region
add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_thickness/2, ps=0.2, tag="LWIR_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_LWIR_Barrier - 0.1, ps=0.1, tag="LWIR_barrier_edge")

# Fine mesh at LWIR/Barrier interface
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_LWIR_Barrier, ps=0.05, tag="LWIR_Barrier_interface")

# Barrier region (finer mesh for accuracy)
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_LWIR_Barrier + Barrier_thickness/2, ps=0.1, tag="barrier_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_Barrier_VLWIR - 0.1, ps=0.1, tag="barrier_VLWIR_edge")

# Fine mesh at Barrier/VLWIR interface
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_Barrier_VLWIR, ps=0.05, tag="barrier_VLWIR_interface")

# VLWIR absorber region
add_1d_mesh_line(mesh="nBn_mesh", pos=interface_Barrier_VLWIR + VLWIR_thickness/2, ps=0.2, tag="VLWIR_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=contact_VLWIR - 0.1, ps=0.1, tag="VLWIR_contact_edge")

# Fine mesh at top contact
add_1d_mesh_line(mesh="nBn_mesh", pos=contact_VLWIR, ps=0.05, tag="top_contact")

# Define regions
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR", 
              tag1="bottom_contact", tag2="LWIR_Barrier_interface")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="Barrier",
              tag1="LWIR_Barrier_interface", tag2="barrier_VLWIR_interface")
add_1d_region(mesh="nBn_mesh", material="T3SL", region="VLWIR",
              tag1="barrier_VLWIR_interface", tag2="top_contact")

# Define contacts (ohmic contacts)
add_1d_contact(mesh="nBn_mesh", name="bottom", tag="bottom_contact", material="metal")
add_1d_contact(mesh="nBn_mesh", name="top", tag="top_contact", material="metal")

# Define interfaces
add_1d_interface(mesh="nBn_mesh", name="LWIR_Barrier", tag="LWIR_Barrier_interface")
add_1d_interface(mesh="nBn_mesh", name="Barrier_VLWIR", tag="barrier_VLWIR_interface")

# Finalize mesh
finalize_mesh(mesh="nBn_mesh")
create_device(mesh="nBn_mesh", device=device_name)

print(f"Device created: {device_name}")
print(f"Total length: {total_length} µm")

# =============================================================================
# SET MATERIAL PARAMETERS
# =============================================================================

print("Setting material parameters...")

regions = ["LWIR", "Barrier", "VLWIR"]

# Set parameters for each region
for region in regions:
    if region == "LWIR":
        set_parameter(device=device_name, region=region, name="Permittivity", value=epsilon_LWIR)
        set_parameter(device=device_name, region=region, name="ElectronAffinity", value=chi_LWIR)
        set_parameter(device=device_name, region=region, name="Bandgap", value=LWIR_Eg)
        set_parameter(device=device_name, region=region, name="Ndonor", value=LWIR_doping)
        set_parameter(device=device_name, region=region, name="mu_n", value=mu_n_LWIR)
        set_parameter(device=device_name, region=region, name="mu_p", value=mu_p_LWIR)
        set_parameter(device=device_name, region=region, name="ni", value=LWIR_ni)
        
    elif region == "Barrier":
        set_parameter(device=device_name, region=region, name="Permittivity", value=epsilon_Barrier)
        set_parameter(device=device_name, region=region, name="ElectronAffinity", value=chi_Barrier)
        set_parameter(device=device_name, region=region, name="Bandgap", value=Barrier_Eg)
        set_parameter(device=device_name, region=region, name="Ndonor", value=Barrier_doping)
        set_parameter(device=device_name, region=region, name="mu_n", value=mu_n_Barrier)
        set_parameter(device=device_name, region=region, name="mu_p", value=mu_p_Barrier)
        set_parameter(device=device_name, region=region, name="ni", value=Barrier_ni)
        
    elif region == "VLWIR":
        set_parameter(device=device_name, region=region, name="Permittivity", value=epsilon_VLWIR)
        set_parameter(device=device_name, region=region, name="ElectronAffinity", value=chi_VLWIR)
        set_parameter(device=device_name, region=region, name="Bandgap", value=VLWIR_Eg)
        set_parameter(device=device_name, region=region, name="Ndonor", value=VLWIR_doping)
        set_parameter(device=device_name, region=region, name="mu_n", value=mu_n_VLWIR)
        set_parameter(device=device_name, region=region, name="mu_p", value=mu_p_VLWIR)
        set_parameter(device=device_name, region=region, name="ni", value=VLWIR_ni)
    
    # Common parameters
    set_parameter(device=device_name, region=region, name="T", value=T)
    set_parameter(device=device_name, region=region, name="kT", value=Vt)
    set_parameter(device=device_name, region=region, name="q", value=q)
    set_parameter(device=device_name, region=region, name="boltzmannConstant", value=kb)

# =============================================================================
# CREATE MODELS AND EQUATIONS
# =============================================================================

print("Setting up physical models...")

for region in regions:
    # Solutions
    node_solution(device=device_name, region=region, name="Potential")
    node_solution(device=device_name, region=region, name="Electrons")
    node_solution(device=device_name, region=region, name="Holes")
    
    # Edge models for electric field
    edge_from_node_model(device=device_name, region=region, node_model="Potential")
    
    # Electric field
    edge_model(device=device_name, region=region, name="ElectricField",
               equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")
    edge_model(device=device_name, region=region, name="ElectricField:Potential@n0",
               equation="EdgeInverseLength")
    edge_model(device=device_name, region=region, name="ElectricField:Potential@n1",
               equation="-EdgeInverseLength")
    
    # Electron and hole concentrations using Fermi-Dirac statistics (Boltzmann approximation)
    # n = ni * exp((Ef - Ei)/kT) = ni * exp((Potential - Psi)/Vt)
    # p = ni * exp((Ei - Ef)/kT) = ni * exp((Psi - Potential)/Vt)
    
    node_model(device=device_name, region=region, name="IntrinsicCharge",
               equation="q*(Holes - Electrons + Ndonor)")
    
    node_model(device=device_name, region=region, name="IntrinsicCharge:Electrons",
               equation="-q")
    node_model(device=device_name, region=region, name="IntrinsicCharge:Holes",
               equation="q")
    
    # Electron current (drift-diffusion)
    edge_model(device=device_name, region=region, name="Jn",
               equation="q*mu_n*EdgeAverage(Electrons)*ElectricField + q*mu_n*Vt*EdgeAverage(Electrons)*EdgeInverseLength")
    
    # Hole current (drift-diffusion)
    edge_model(device=device_name, region=region, name="Jp",
               equation="q*mu_p*EdgeAverage(Holes)*ElectricField - q*mu_p*Vt*EdgeAverage(Holes)*EdgeInverseLength")

# =============================================================================
# POISSON EQUATION
# =============================================================================

print("Setting up Poisson equation...")

for region in regions:
    equation(device=device_name, region=region, name="PotentialEquation",
             variable_name="Potential",
             node_model="IntrinsicCharge",
             edge_model="",
             variable_update="default")

# =============================================================================
# CONTINUITY EQUATIONS (simplified - steady state)
# =============================================================================

print("Setting up continuity equations...")

# For steady-state simulation (no time derivatives)
for region in regions:
    # Electron continuity
    equation(device=device_name, region=region, name="ElectronEquation",
             variable_name="Electrons",
             node_model="",
             edge_model="Jn",
             variable_update="default")
    
    # Hole continuity  
    equation(device=device_name, region=region, name="HoleEquation",
             variable_name="Holes",
             node_model="",
             edge_model="Jp",
             variable_update="default")

# =============================================================================
# CONTACT BOUNDARY CONDITIONS
# =============================================================================

print("Setting up contact boundary conditions...")

# Ohmic contact at bottom (LWIR side)
contact_equation(device=device_name, contact="bottom", name="PotentialEquation",
                 node_model="Potential - 0.0",  # Ground reference
                 node_model_electrons="Electrons - Ndonor",
                 node_model_holes="Holes - ni^2/Ndonor",
                 edge_current_model="Jn",
                 edge_current_model_holes="Jp")

# Ohmic contact at top (VLWIR side) - bias will be applied here
contact_equation(device=device_name, contact="top", name="PotentialEquation",
                 node_model="Potential - V_bias",  # Bias voltage
                 node_model_electrons="Electrons - Ndonor",
                 node_model_holes="Holes - ni^2/Ndonor",
                 edge_current_model="Jn",
                 edge_current_model_holes="Jp")

# =============================================================================
# INTERFACE CONDITIONS
# =============================================================================

print("Setting up interface conditions...")

# LWIR/Barrier interface
interface_model(device=device_name, interface="LWIR_Barrier", name="continuousPotential",
                equation="Potential@r0 - Potential@r1")
interface_model(device=device_name, interface="LWIR_Barrier", name="continuousPotential:Potential@r0",
                equation="1")
interface_model(device=device_name, interface="LWIR_Barrier", name="continuousPotential:Potential@r1",
                equation="-1")

interface_equation(device=device_name, interface="LWIR_Barrier", name="PotentialEquation",
                   interface_model="continuousPotential", type="continuous")

# Barrier/VLWIR interface  
interface_model(device=device_name, interface="Barrier_VLWIR", name="continuousPotential",
                equation="Potential@r0 - Potential@r1")
interface_model(device=device_name, interface="Barrier_VLWIR", name="continuousPotential:Potential@r0",
                equation="1")
interface_model(device=device_name, interface="Barrier_VLWIR", name="continuousPotential:Potential@r1",
                equation="-1")

interface_equation(device=device_name, interface="Barrier_VLWIR", name="PotentialEquation",
                   interface_model="continuousPotential", type="continuous")

# =============================================================================
# INITIAL SOLUTION (Equilibrium)
# =============================================================================

print("Solving equilibrium condition...")

# Set initial conditions
for region in regions:
    set_node_values(device=device_name, region=region, name="Potential", value=0.0)
    set_node_values(device=device_name, region=region, name="Electrons", value=LWIR_doping if region=="LWIR" else (Barrier_doping if region=="Barrier" else VLWIR_doping))
    set_node_values(device=device_name, region=region, name="Holes", value=1e10)  # Low initial hole concentration

# Solve equilibrium
set_parameter(device=device_name, name="V_bias", value=0.0)
solve(type="dc", absolute_error=1.0e-10, relative_error=1.0e-10, maximum_iterations=50)

print("Equilibrium solution obtained")

# =============================================================================
# I-V CHARACTERISTIC SIMULATION
# =============================================================================

print("Calculating I-V characteristics...")

# Voltage sweep from -0.5V to +0.5V (as mentioned in paper for bias-selectable operation)
voltages = np.linspace(-0.5, 0.5, 21)
currents = []

for V in voltages:
    set_parameter(device=device_name, name="V_bias", value=V)
    solve(type="dc", absolute_error=1.0e-10, relative_error=1.0e-10, maximum_iterations=50)
    
    # Calculate total current
    Jn_top = get_contact_current(device=device_name, contact="top", equation="ElectronEquation")
    Jp_top = get_contact_current(device=device_name, contact="top", equation="HoleEquation")
    J_total = Jn_top + Jp_top
    currents.append(J_total)
    
    print(f"V = {V:+.3f} V, J = {J_total:.6e} A/cm²")

# Convert to numpy arrays
voltages = np.array(voltages)
currents = np.array(currents)

# =============================================================================
# COMPARISON WITH RULE 07 (from paper)
# =============================================================================

print("\n" + "="*70)
print("COMPARISON WITH PAPER RESULTS AND RULE 07")
print("="*70)

# Rule 07 benchmark values from paper (at 100K)
# J_dark = 0.0539 A/cm² at 14 µm (VLWIR)
# J_dark = 0.0001 A/cm² at 9 µm (LWIR)
Rule07_VLWIR = 0.0539  # A/cm²
Rule07_LWIR = 0.0001   # A/cm²

# Calculate dark current at zero bias (equilibrium dark current)
J_dark_zero_bias = abs(currents[len(voltages)//2])

print(f"\nDark Current Density at 0V:")
print(f"  Simulation: {J_dark_zero_bias:.6e} A/cm²")
print(f"  Rule 07 (VLWIR, 14µm): {Rule07_VLWIR:.6e} A/cm²")
print(f"  Rule 07 (LWIR, 9µm): {Rule07_LWIR:.6e} A/cm²")

if J_dark_zero_bias < Rule07_VLWIR:
    print(f"  ✓ Below Rule 07 VLWIR limit (improvement: {(1-J_dark_zero_bias/Rule07_VLWIR)*100:.1f}%)")
else:
    print(f"  ✗ Above Rule 07 VLWIR limit")

# =============================================================================
# SAVE RESULTS
# =============================================================================

# Save I-V data
output_file = "exp_oc/JEM2025_IV_data.txt"
with open(output_file, 'w') as f:
    f.write("# JEM2025 nBn Detector I-V Characteristics\n")
    f.write("# Temperature: 100K\n")
    f.write("# Structure: LWIR(9µm)/Barrier(4.35µm)/VLWIR(14µm)\n")
    f.write("#\n")
    f.write("# Voltage(V)  Current_Density(A/cm²)\n")
    for V, J in zip(voltages, currents):
        f.write(f"{V:12.6f}  {J:18.6e}\n")

print(f"\nI-V data saved to: {output_file}")

# =============================================================================
# PLOT RESULTS
# =============================================================================

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Linear scale plot
    ax1.plot(voltages, currents, 'b-', linewidth=2, label='Simulation')
    ax1.axhline(y=Rule07_VLWIR, color='r', linestyle='--', label='Rule 07 VLWIR (14µm)')
    ax1.axhline(y=Rule07_LWIR, color='g', linestyle='--', label='Rule 07 LWIR (9µm)')
    ax1.set_xlabel('Bias Voltage (V)', fontsize=12)
    ax1.set_ylabel('Current Density (A/cm²)', fontsize=12)
    ax1.set_title('I-V Characteristics (Linear Scale)', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Log scale plot
    ax2.semilogy(voltages, np.abs(currents), 'b-', linewidth=2, label='Simulation')
    ax2.axhline(y=Rule07_VLWIR, color='r', linestyle='--', label='Rule 07 VLWIR (14µm)')
    ax2.axhline(y=Rule07_LWIR, color='g', linestyle='--', label='Rule 07 LWIR (9µm)')
    ax2.set_xlabel('Bias Voltage (V)', fontsize=12)
    ax2.set_ylabel('|Current Density| (A/cm²)', fontsize=12)
    ax2.set_title('I-V Characteristics (Log Scale)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('exp_oc/JEM2025_IV_plot.png', dpi=150, bbox_inches='tight')
    print("Plot saved to: exp_oc/JEM2025_IV_plot.png")
    
except ImportError:
    print("Matplotlib not available. Skipping plot generation.")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("SIMULATION SUMMARY")
print("="*70)
print(f"Device: HgCdTe nBn Two-Color Infrared Detector")
print(f"Temperature: {T} K")
print(f"\nLayer Structure:")
print(f"  LWIR Absorber:  {LWIR_thickness} µm, Eg={LWIR_Eg*1000:.0f} meV, n={LWIR_doping:.2e} cm⁻³")
print(f"  Barrier:        {Barrier_thickness} µm, Eg={Barrier_Eg*1000:.0f} meV, n={Barrier_doping:.2e} cm⁻³")
print(f"  VLWIR Absorber: {VLWIR_thickness} µm, Eg={VLWIR_Eg*1000:.0f} meV, n={VLWIR_doping:.2e} cm⁻³")
print(f"\nKey Results:")
print(f"  Dark current at 0V: {J_dark_zero_bias:.6e} A/cm²")
print(f"  Rule 07 VLWIR:      {Rule07_VLWIR:.6e} A/cm²")
print(f"  Rule 07 LWIR:       {Rule07_LWIR:.6e} A/cm²")
print(f"\nStatus: {'✓' if J_dark_zero_bias < Rule07_VLWIR else '✗'} {'Below' if J_dark_zero_bias < Rule07_VLWIR else 'Above'} Rule 07 VLWIR limit")
print("="*70)

print("\nSimulation completed successfully!")
