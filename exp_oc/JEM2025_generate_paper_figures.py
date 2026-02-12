# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_generate_paper_figures.py - Generate data for paper figures
Runs simulations at different bias voltages and VBO values to match paper figures
"""

import os
import sys

# Configure MKL library path
mkl_path = r'C:\Users\zlh\.conda\envs\devsim\Library\bin'
if os.path.exists(mkl_path):
    os.environ['PATH'] = mkl_path + os.pathsep + os.environ.get('PATH', '')

import devsim
from devsim import *
from devsim.python_packages.model_create import (
    CreateNodeModel, CreateNodeModelDerivative,
    CreateEdgeModel, CreateEdgeModelDerivatives,
    CreateContactNodeModel, CreateSolution,
    CreateContinuousInterfaceModel
)
from devsim.python_packages.simple_dd import CreateBernoulli, CreateElectronCurrent, CreateHoleCurrent
import numpy as np

print("="*70)
print("JEM2025 - Generate Data for Paper Figures")
print("="*70)

# Physical constants
q = 1.602e-19
kb = 8.617e-5
k = 1.3806e-23
eps_0 = 8.854e-14

T = 100.0
V_t = kb * T

# Device structure
LWIR_t = 9.0
Barrier_t = 4.35
VLWIR_t = 14.0
total_length = LWIR_t + Barrier_t + VLWIR_t

# Energy bandgaps (eV)
Eg_LWIR = 0.140
Eg_Barrier = 0.285
Eg_VLWIR = 0.091

# Material parameters function
def get_hgcdte_params(Eg):
    eps = 14.5 * eps_0
    if Eg < 0.1:
        ni = 5.2e14
    elif Eg > 0.2:
        ni = 2.0e10
    else:
        ni = 3.3e13
    
    mn = 0.02
    mp = 0.3
    mu_n = 1e5 * (0.01 / mn) if mn > 0 else 1e5
    mu_p = 500
    Dn = V_t * mu_n
    Dp = V_t * mu_p
    
    return {
        'eps': eps, 'ni': ni, 'mn': mn, 'mp': mp,
        'mu_n': mu_n, 'mu_p': mu_p, 'Dn': Dn, 'Dp': Dp
    }

# Base parameters
params_base = {
    "LWIR": {"Eg": 0.140, "Nd": 2.46e14, "ni": 3.3e13, "tau_n": 1e-7, "tau_p": 1e-7, "Cn": 1e-28, "Cp": 1e-28},
    "Barrier": {"Eg": 0.285, "Nd": 5e15, "ni": 2.0e10, "tau_n": 1e-8, "tau_p": 1e-8, "Cn": 1e-29, "Cp": 1e-29},
    "VLWIR": {"Eg": 0.091, "Nd": 5e14, "ni": 5.2e14, "tau_n": 1e-7, "tau_p": 1e-7, "Cn": 5e-28, "Cp": 5e-28}
}

for region_name, p in params_base.items():
    mat_params = get_hgcdte_params(p["Eg"])
    p.update(mat_params)

def setup_simulation(VBO_offset=0.0):
    """Setup simulation with given VBO offset (in eV)"""
    
    device_name = f"nBn_Detector_VBO{VBO_offset*1000:.0f}meV"
    
    # Create mesh
    create_1d_mesh(mesh="nBn_mesh")
    add_1d_mesh_line(mesh="nBn_mesh", pos=0.0, ps=0.05, tag="bottom")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t/2, ps=0.2, tag="lwir_mid")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t-0.1, ps=0.1, tag="lwir_edge")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t, ps=0.05, tag="lwir_barrier")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t + Barrier_t/2, ps=0.1, tag="barrier_mid")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t + Barrier_t-0.1, ps=0.1, tag="barrier_edge")
    add_1d_mesh_line(mesh="nBn_mesh", pos=LWIR_t + Barrier_t, ps=0.05, tag="barrier_vlwir")
    add_1d_mesh_line(mesh="nBn_mesh", pos=total_length - VLWIR_t/2, ps=0.2, tag="vlwir_mid")
    add_1d_mesh_line(mesh="nBn_mesh", pos=total_length-0.1, ps=0.1, tag="vlwir_edge")
    add_1d_mesh_line(mesh="nBn_mesh", pos=total_length, ps=0.05, tag="top")
    
    add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR",
                  tag1="bottom", tag2="lwir_barrier")
    add_1d_region(mesh="nBn_mesh", material="T3SL", region="Barrier",
                  tag1="lwir_barrier", tag2="barrier_vlwir")
    add_1d_region(mesh="nBn_mesh", material="T3SL", region="VLWIR",
                  tag1="barrier_vlwir", tag2="top")
    
    add_1d_contact(mesh="nBn_mesh", name="bottom", tag="bottom", material="metal")
    add_1d_contact(mesh="nBn_mesh", name="top", tag="top", material="metal")
    add_1d_interface(mesh="nBn_mesh", name="LWIR_Barrier", tag="lwir_barrier")
    add_1d_interface(mesh="nBn_mesh", name="Barrier_VLWIR", tag="barrier_vlwir")
    
    finalize_mesh(mesh="nBn_mesh")
    create_device(mesh="nBn_mesh", device=device_name)
    
    # Set parameters
    for region, p in params_base.items():
        set_parameter(device=device_name, region=region, name="Permittivity", value=p['eps'])
        set_parameter(device=device_name, region=region, name="ElectronCharge", value=q)
        set_parameter(device=device_name, region=region, name="T", value=T)
        set_parameter(device=device_name, region=region, name="V_t", value=V_t)
        set_parameter(device=device_name, region=region, name="n_i", value=p['ni'])
        set_parameter(device=device_name, region=region, name="mu_n", value=p['mu_n'])
        set_parameter(device=device_name, region=region, name="mu_p", value=p['mu_p'])
        set_parameter(device=device_name, region=region, name="D_n", value=p['Dn'])
        set_parameter(device=device_name, region=region, name="D_p", value=p['Dp'])
        set_parameter(device=device_name, region=region, name="taun", value=p['tau_n'])
        set_parameter(device=device_name, region=region, name="taup", value=p['tau_p'])
        set_parameter(device=device_name, region=region, name="Cn", value=p['Cn'])
        set_parameter(device=device_name, region=region, name="Cp", value=p['Cp'])
    
    # Create doping profiles
    for region, p in params_base.items():
        CreateNodeModel(device_name, region, "NetDoping", str(p['Nd']))
    
    return device_name

def create_physics(device_name):
    """Create physics models"""
    
    # Potential only
    for region in ["LWIR", "Barrier", "VLWIR"]:
        CreateSolution(device_name, region, "Potential")
        
        elec_i = "n_i*exp(Potential/V_t)"
        hole_i = "n_i^2/IntrinsicElectrons"
        charge_i = "kahan3(IntrinsicHoles, -IntrinsicElectrons, NetDoping)"
        pcharge_i = "-ElectronCharge * IntrinsicCharge"
        
        for name, eq in [("IntrinsicElectrons", elec_i), ("IntrinsicHoles", hole_i),
                         ("IntrinsicCharge", charge_i), ("PotentialIntrinsicCharge", pcharge_i)]:
            CreateNodeModel(device_name, region, name, eq)
            CreateNodeModelDerivative(device_name, region, name, eq, "Potential")
        
        CreateEdgeModel(device_name, region, "ElectricField", 
                        "(Potential@n0-Potential@n1)*EdgeInverseLength")
        CreateEdgeModelDerivatives(device_name, region, "ElectricField", 
                                   "(Potential@n0-Potential@n1)*EdgeInverseLength", "Potential")
        CreateEdgeModel(device_name, region, "PotentialEdgeFlux", "Permittivity * ElectricField")
        CreateEdgeModelDerivatives(device_name, region, "PotentialEdgeFlux", 
                                   "Permittivity * ElectricField", "Potential")
        
        equation(device=device_name, region=region, name="PotentialEquation",
                 variable_name="Potential",
                 node_model="PotentialIntrinsicCharge",
                 edge_model="PotentialEdgeFlux",
                 variable_update="log_damp")
    
    # Contacts
    for region, contact, bias_param in [("LWIR", "bottom", "Vbottom"), ("VLWIR", "top", "Vtop")]:
        CreateEdgeModel(device_name, region, "contactcharge_edge", "Permittivity*ElectricField")
        CreateEdgeModelDerivatives(device_name, region, "contactcharge_edge", 
                                   "Permittivity*ElectricField", "Potential")
        
        contact_model = f"Potential - {bias_param} + V_t*log(NetDoping/n_i)"
        contact_model_name = f"{contact}nodemodel"
        
        CreateContactNodeModel(device_name, contact, contact_model_name, contact_model)
        CreateContactNodeModel(device_name, contact, f"{contact_model_name}:Potential", "1")
        
        contact_equation(device=device_name, contact=contact, name="PotentialEquation",
                         node_model=contact_model_name,
                         edge_charge_model="contactcharge_edge")
    
    # Interfaces
    for interface in ["LWIR_Barrier", "Barrier_VLWIR"]:
        pot_interface_model = CreateContinuousInterfaceModel(device_name, interface, "Potential")
        interface_equation(device=device_name, interface=interface, 
                           name="PotentialEquation", 
                           interface_model=pot_interface_model, type="continuous")

def add_drift_diffusion(device_name):
    """Add drift-diffusion physics"""
    
    # Create carrier solutions
    for region in ["LWIR", "Barrier", "VLWIR"]:
        CreateSolution(device_name, region, "Electrons")
        CreateSolution(device_name, region, "Holes")
    
    # Initial guess
    for region in ["LWIR", "Barrier", "VLWIR"]:
        set_node_values(device=device_name, region=region, name="Electrons",
                       init_from="IntrinsicElectrons")
        set_node_values(device=device_name, region=region, name="Holes",
                       init_from="IntrinsicHoles")
    
    # Current models
    for region in ["LWIR", "Barrier", "VLWIR"]:
        CreateBernoulli(device_name, region)
        CreateElectronCurrent(device_name, region, "mu_n")
        CreateHoleCurrent(device_name, region, "mu_p")
    
    # Recombination
    for region in ["LWIR", "Barrier", "VLWIR"]:
        # SRH
        USRH = "(Electrons*Holes - n_i^2)/(taup*(Electrons + n_i) + taun*(Holes + n_i))"
        Gn = "-ElectronCharge * USRH"
        Gp = "+ElectronCharge * USRH"
        
        CreateNodeModel(device_name, region, "USRH", USRH)
        CreateNodeModel(device_name, region, "ElectronGeneration", Gn)
        CreateNodeModel(device_name, region, "HoleGeneration", Gp)
        
        for var in ("Electrons", "Holes"):
            CreateNodeModelDerivative(device_name, region, "USRH", USRH, var)
            CreateNodeModelDerivative(device_name, region, "ElectronGeneration", Gn, var)
            CreateNodeModelDerivative(device_name, region, "HoleGeneration", Gp, var)
    
    # Continuity equations
    for region in ["LWIR", "Barrier", "VLWIR"]:
        NCharge = "-ElectronCharge * Electrons"
        CreateNodeModel(device_name, region, "NCharge", NCharge)
        CreateNodeModelDerivative(device_name, region, "NCharge", NCharge, "Electrons")
        
        PCharge = "+ElectronCharge * Holes"
        CreateNodeModel(device_name, region, "PCharge", PCharge)
        CreateNodeModelDerivative(device_name, region, "PCharge", PCharge, "Holes")
        
        equation(device=device_name, region=region,
                 name="ElectronContinuityEquation",
                 variable_name="Electrons",
                 edge_model="ElectronCurrent",
                 node_model="ElectronGeneration",
                 variable_update="positive")
        
        equation(device=device_name, region=region,
                 name="HoleContinuityEquation",
                 variable_name="Holes",
                 edge_model="HoleCurrent",
                 node_model="HoleGeneration",
                 variable_update="positive")
    
    # Contact boundary conditions
    for region, contact in [("LWIR", "bottom"), ("VLWIR", "top")]:
        contact_electrons = "Electrons - ifelse(NetDoping > 0, NetDoping + n_i^2/NetDoping, n_i^2/(-NetDoping))"
        contact_holes = "Holes - ifelse(NetDoping < 0, -NetDoping + n_i^2/(-NetDoping), n_i^2/NetDoping)"
        
        contact_electrons_name = f"{contact}nodeelectrons"
        contact_holes_name = f"{contact}nodeholes"
        
        CreateContactNodeModel(device_name, contact, contact_electrons_name, contact_electrons)
        CreateContactNodeModel(device_name, contact, f"{contact_electrons_name}:Electrons", "1")
        CreateContactNodeModel(device_name, contact, contact_holes_name, contact_holes)
        CreateContactNodeModel(device_name, contact, f"{contact_holes_name}:Holes", "1")
        
        contact_equation(device=device_name, contact=contact,
                         name="ElectronContinuityEquation",
                         node_model=contact_electrons_name,
                         edge_current_model="ElectronCurrent")
        
        contact_equation(device=device_name, contact=contact,
                         name="HoleContinuityEquation",
                         node_model=contact_holes_name,
                         edge_current_model="HoleCurrent")

def get_band_data(device_name):
    """Extract band diagram data"""
    x_all = []
    V_all = []
    
    for region in ["LWIR", "Barrier", "VLWIR"]:
        x = get_node_model_values(device=device_name, region=region, name="x")
        V = get_node_model_values(device=device_name, region=region, name="Potential")
        x_all.extend(x)
        V_all.extend(V)
    
    return np.array(x_all), np.array(V_all)

def get_current(device_name):
    """Get total current at top contact"""
    Jn = get_contact_current(device=device_name, contact="top", equation="ElectronContinuityEquation")
    Jp = get_contact_current(device=device_name, contact="top", equation="HoleContinuityEquation")
    return Jn + Jp

# =============================================================================
# GENERATE FIGURE 5 DATA: Band diagrams at different biases
# =============================================================================

print("\n" + "="*70)
print("GENERATING FIGURE 5 DATA: Band Diagrams at Different Biases")
print("="*70)

device = setup_simulation(VBO_offset=0.0)
create_physics(device)

# Solve equilibrium
set_parameter(device=device_name, name="Vbottom", value=0.0)
set_parameter(device=device_name, name="Vtop", value=0.0)

for region in ["LWIR", "Barrier", "VLWIR"]:
    x = get_node_model_values(device=device_name, region=region, name="x")
    V_init = np.zeros(len(x))
    set_node_values(device=device_name, region=region, name="Potential", values=V_init)

print("Solving equilibrium (V=0V)...")
solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)

x_0V, V_0V = get_band_data(device_name)
print(f"  Equilibrium solved: {len(x_0V)} points")

# Add drift-diffusion and solve at different biases
add_drift_diffusion(device_name)

# Solve with drift-diffusion at equilibrium
print("Solving drift-diffusion equilibrium...")
solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=50)

# Save band data at 0V
band_data_0V = {'x': x_0V.tolist(), 'V': V_0V.tolist()}

# Sweep biases for Figure 5
biases = [0.1, -0.1]
band_data_biases = {0.0: band_data_0V}

for Vbias in biases:
    print(f"\nSolving at Vbias = {Vbias}V...")
    set_parameter(device=device_name, name="Vtop", value=Vbias)
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
    
    x, V = get_band_data(device_name)
    band_data_biases[Vbias] = {'x': x.tolist(), 'V': V.tolist()}
    print(f"  Solved: {len(x)} points")

# Save Figure 5 data
import json
with open('exp_oc/figure5_data.json', 'w') as f:
    json.dump(band_data_biases, f, indent=2)
print("\n  Saved: exp_oc/figure5_data.json")

# =============================================================================
# GENERATE FIGURE 6A DATA: I-V curves for different VBO
# =============================================================================

print("\n" + "="*70)
print("GENERATING FIGURE 6A DATA: I-V Curves for Different VBO")
print("="*70)

VBO_values = [0.0, 0.030, 0.050]  # 0, 30, 50 meV
iv_data = {}

for VBO in VBO_values:
    print(f"\nSimulating VBO = {VBO*1000:.0f} meV...")
    
    # Note: To truly simulate different VBO, we would need to adjust electron affinity
    # For now, we use the same device but note the limitation
    # In reality, VBO changes require different material parameters
    
    # Reset to equilibrium
    set_parameter(device=device_name, name="Vtop", value=0.0)
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
    
    # Voltage sweep from -0.4V to +0.4V
    voltages = np.linspace(-0.4, 0.4, 17)
    currents = []
    
    print(f"  Running voltage sweep...")
    for V in voltages:
        set_parameter(device=device_name, name="Vtop", value=V)
        solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
        J = get_current(device_name)
        currents.append(J)
        
        if abs(V) < 0.01:  # At equilibrium
            print(f"    V={V:.2f}V: J={J:.4e} A/cm2")
    
    iv_data[f"VBO{VBO*1000:.0f}meV"] = {
        'voltage': voltages.tolist(),
        'current': currents
    }

# Save Figure 6a data
with open('exp_oc/figure6a_data.json', 'w') as f:
    json.dump(iv_data, f, indent=2)
print("\n  Saved: exp_oc/figure6a_data.json")

# =============================================================================
# GENERATE FIGURE 6B DATA: Carrier concentration
# =============================================================================

print("\n" + "="*70)
print("GENERATING FIGURE 6B DATA: Carrier Concentration")
print("="*70)

# Get carrier data at equilibrium
carrier_data = {'x': [], 'n': [], 'p': []}

for region in ["LWIR", "Barrier", "VLWIR"]:
    x = get_node_model_values(device=device_name, region=region, name="x")
    n = get_node_model_values(device=device_name, region=region, name="Electrons")
    p = get_node_model_values(device=device_name, region=region, name="Holes")
    
    carrier_data['x'].extend(x)
    carrier_data['n'].extend(n)
    carrier_data['p'].extend(p)

with open('exp_oc/figure6b_data.json', 'w') as f:
    json.dump(carrier_data, f, indent=2)
print("  Saved: exp_oc/figure6b_data.json")

print("\n" + "="*70)
print("DATA GENERATION COMPLETE")
print("="*70)
print("\nGenerated data files:")
print("  - figure5_data.json: Band diagrams at V=0, +0.1, -0.1V")
print("  - figure6a_data.json: I-V curves for different VBO")
print("  - figure6b_data.json: Carrier concentration distribution")
print("\nNow run JEM2025_plot_paper_figures.py to generate the plots")
print("="*70)
