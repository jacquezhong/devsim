# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_corrected_thickness_v2.py - 修正厚度参数版本2
使用图4中的正确厚度：VLWIR=5μm, Barrier=0.2μm, LWIR=5μm
"""

import os
import sys
import json
import numpy as np

# MKL路径
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

print("="*70)
print("JEM2025 - Corrected Thickness v2 (From Figure 4)")
print("="*70)

# 物理常数
q = 1.602e-19
kb = 8.617e-5
k = 1.3806e-23
eps_0 = 8.854e-14

T = 100.0
V_t = kb * T

# =============================================================================
# 正确的设备结构 (根据图4)
# =============================================================================

# 修正后的厚度（主要三层）
VLWIR_t = 5.0      # μm
Barrier_t = 0.2    # μm  
LWIR_t = 5.0       # μm

# 总长度
total_length = VLWIR_t + Barrier_t + LWIR_t

print(f"\nDevice Structure (from Figure 4):")
print(f"  VLWIR absorber: {VLWIR_t} μm (top)")
print(f"  Barrier: {Barrier_t} μm")
print(f"  LWIR absorber: {LWIR_t} μm (bottom)")
print(f"  Total: {total_length} μm")
print(f"  Temperature: {T} K")

# =============================================================================
# 材料参数 (Table II)
# =============================================================================

params = {
    "VLWIR": {
        "Eg": 0.091, "Nd": 5e14, "ni": 5.2e14,
        "tau_n": 3.211e-5, "tau_p": 2.101e-4,
        "Cn": 1e-28, "Cp": 1e-28,
        "me": 0.008, "mh": 0.4, "eps_r": 14.5
    },
    "Barrier": {
        "Eg": 0.285, "Nd": 5e15, "ni": 2.0e10,
        "tau_n": 3.171e-3, "tau_p": 9.433e-5,
        "Cn": 1e-30, "Cp": 1e-30,
        "me": 0.01, "mh": 0.3, "eps_r": 14.5
    },
    "LWIR": {
        "Eg": 0.140, "Nd": 2.46e14, "ni": 3.3e13,
        "tau_n": 3.784e-4, "tau_p": 1.561e-4,
        "Cn": 1e-28, "Cp": 1e-28,
        "me": 0.02, "mh": 0.35, "eps_r": 14.5
    }
}

# 计算输运参数
for region, p in params.items():
    mn = p['me']
    eps = p['eps_r'] * eps_0
    mu_n = 1e5 * (0.01 / mn) if mn > 0 else 1e5
    mu_p = 500
    Dn = V_t * mu_n / kb
    Dp = V_t * mu_p / kb
    p.update({'eps': eps, 'mu_n': mu_n, 'mu_p': mu_p, 'Dn': Dn, 'Dp': Dp})

# =============================================================================
# 创建网格 (简化版本)
# =============================================================================

device_name = "nBn_Corrected"
print("\n[1/6] Creating device...")

create_1d_mesh(mesh="nBn_mesh")

# 简化的网格创建 - 使用明确的坐标
# VLWIR: 0 - 5 μm
add_1d_mesh_line(mesh="nBn_mesh", pos=0.0, ps=0.05, tag="top")
add_1d_mesh_line(mesh="nBn_mesh", pos=1.0, ps=0.1, tag="vlwir_1")
add_1d_mesh_line(mesh="nBn_mesh", pos=2.0, ps=0.1, tag="vlwir_2")
add_1d_mesh_line(mesh="nBn_mesh", pos=3.0, ps=0.1, tag="vlwir_3")
add_1d_mesh_line(mesh="nBn_mesh", pos=4.0, ps=0.1, tag="vlwir_4")
add_1d_mesh_line(mesh="nBn_mesh", pos=4.9, ps=0.05, tag="vlwir_end")

# Barrier: 5.0 - 5.2 μm (极细网格)
add_1d_mesh_line(mesh="nBn_mesh", pos=5.0, ps=0.02, tag="barrier_start")
add_1d_mesh_line(mesh="nBn_mesh", pos=5.1, ps=0.01, tag="barrier_mid")
add_1d_mesh_line(mesh="nBn_mesh", pos=5.2, ps=0.02, tag="barrier_end")

# LWIR: 5.2 - 10.2 μm
add_1d_mesh_line(mesh="nBn_mesh", pos=6.0, ps=0.1, tag="lwir_1")
add_1d_mesh_line(mesh="nBn_mesh", pos=7.0, ps=0.1, tag="lwir_2")
add_1d_mesh_line(mesh="nBn_mesh", pos=8.0, ps=0.1, tag="lwir_3")
add_1d_mesh_line(mesh="nBn_mesh", pos=9.0, ps=0.1, tag="lwir_4")
add_1d_mesh_line(mesh="nBn_mesh", pos=10.0, ps=0.1, tag="lwir_5")
add_1d_mesh_line(mesh="nBn_mesh", pos=10.2, ps=0.05, tag="bottom")

# 创建区域
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="VLWIR",
              tag1="top", tag2="barrier_start")
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="Barrier",
              tag1="barrier_start", tag2="barrier_end")
add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR",
              tag1="barrier_end", tag2="bottom")

# 接触
add_1d_contact(mesh="nBn_mesh", name="top", tag="top", material="metal")
add_1d_contact(mesh="nBn_mesh", name="bottom", tag="bottom", material="metal")

# 界面
add_1d_interface(mesh="nBn_mesh", name="VLWIR_Barrier", tag="barrier_start")
add_1d_interface(mesh="nBn_mesh", name="Barrier_LWIR", tag="barrier_end")

finalize_mesh(mesh="nBn_mesh")
create_device(mesh="nBn_mesh", device=device_name)

node_count = sum(len(get_node_model_values(device=device_name, region=r, name="x")) 
                 for r in ["VLWIR", "Barrier", "LWIR"])
print(f"  Device created: {node_count} nodes")

# =============================================================================
# 设置参数
# =============================================================================

print("\n[2/6] Setting parameters...")

for region, p in params.items():
    for name, value in [
        ("Permittivity", p['eps']), ("ElectronCharge", q), ("T", T), ("V_t", V_t),
        ("n_i", p['ni']), ("mu_n", p['mu_n']), ("mu_p", p['mu_p']),
        ("D_n", p['Dn']), ("D_p", p['Dp']),
        ("taun", p['tau_n']), ("taup", p['tau_p']),
        ("Cn", p['Cn']), ("Cp", p['Cp']), ("Eg", p['Eg'])
    ]:
        set_parameter(device=device_name, region=region, name=name, value=value)
    CreateNodeModel(device_name, region, "NetDoping", str(p['Nd']))

print("  Parameters set")

# =============================================================================
# Poisson方程
# =============================================================================

print("\n[3/6] Creating potential physics...")

for region in ["VLWIR", "Barrier", "LWIR"]:
    CreateSolution(device_name, region, "Potential")
    
    fd = "1.5" if params[region]['Eg'] < 0.1 else "1.2" if params[region]['Eg'] < 0.15 else "1.0"
    ni = params[region]['ni']
    
    elec_i = f"{ni}*{fd}*exp(Potential/V_t)"
    hole_i = f"({ni}*{fd})^2/IntrinsicElectrons"
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

# 接触
for region, contact, bias in [("LWIR", "bottom", "Vbottom"), ("VLWIR", "top", "Vtop")]:
    CreateEdgeModel(device_name, region, "contactcharge_edge", "Permittivity*ElectricField")
    CreateEdgeModelDerivatives(device_name, region, "contactcharge_edge", 
                               "Permittivity*ElectricField", "Potential")
    
    contact_model = f"Potential - {bias} + V_t*log(abs(NetDoping)/n_i)"
    CreateContactNodeModel(device_name, contact, f"{contact}nodemodel", contact_model)
    CreateContactNodeModel(device_name, contact, f"{contact}nodemodel:Potential", "1")
    
    contact_equation(device=device_name, contact=contact, name="PotentialEquation",
                     node_model=f"{contact}nodemodel",
                     edge_charge_model="contactcharge_edge")

# 界面
for interface in ["VLWIR_Barrier", "Barrier_LWIR"]:
    pot_model = CreateContinuousInterfaceModel(device_name, interface, "Potential")
    interface_equation(device=device_name, interface=interface, 
                       name="PotentialEquation", 
                       interface_model=pot_model, type="continuous")

print("  Potential physics created")

# =============================================================================
# 求解Poisson
# =============================================================================

print("\n[4/6] Solving Poisson equation...")

set_parameter(device=device_name, name="Vbottom", value=0.0)
set_parameter(device=device_name, name="Vtop", value=0.0)

for region in ["VLWIR", "Barrier", "LWIR"]:
    x = get_node_model_values(device=device_name, region=region, name="x")
    set_node_values(device=device_name, region=region, name="Potential", values=np.zeros(len(x)))

solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)
print("  Poisson solved")

# =============================================================================
# 漂移-扩散
# =============================================================================

print("\n[5/6] Adding drift-diffusion...")

for region in ["VLWIR", "Barrier", "LWIR"]:
    CreateSolution(device_name, region, "Electrons")
    CreateSolution(device_name, region, "Holes")
    
    set_node_values(device=device_name, region=region, name="Electrons",
                    init_from="IntrinsicElectrons")
    set_node_values(device=device_name, region=region, name="Holes",
                    init_from="IntrinsicHoles")

for region in ["VLWIR", "Barrier", "LWIR"]:
    CreateBernoulli(device_name, region)
    CreateElectronCurrent(device_name, region, "mu_n")
    CreateHoleCurrent(device_name, region, "mu_p")

for region in ["VLWIR", "Barrier", "LWIR"]:
    srh = "(Electrons*Holes - n_i^2)/(taup*(Electrons + n_i) + taun*(Holes + n_i))"
    auger = "(Cn*Electrons + Cp*Holes)*(Electrons*Holes - n_i^2)" if region == "VLWIR" else \
            "0.5*(Cn*Electrons + Cp*Holes)*(Electrons*Holes - n_i^2)" if region == "LWIR" else "0"
    rad = "(Electrons*Holes - n_i^2)/taup"
    
    USRH = f"({srh} + {auger} + {rad})"
    CreateNodeModel(device_name, region, "USRH", USRH)
    CreateNodeModel(device_name, region, "ElectronGeneration", f"-ElectronCharge * USRH")
    CreateNodeModel(device_name, region, "HoleGeneration", f"+ElectronCharge * USRH")
    
    for var in ("Electrons", "Holes"):
        for model in ("USRH", "ElectronGeneration", "HoleGeneration"):
            CreateNodeModelDerivative(device_name, region, model, 
                                       f"{'-' if 'Electron' in model else '+'}ElectronCharge * USRH" if 'Generation' in model else USRH, 
                                       var)

for region in ["VLWIR", "Barrier", "LWIR"]:
    for name, var, current, gen in [
        ("ElectronContinuityEquation", "Electrons", "ElectronCurrent", "ElectronGeneration"),
        ("HoleContinuityEquation", "Holes", "HoleCurrent", "HoleGeneration")
    ]:
        CreateNodeModel(device_name, region, f"{var}Charge", f"{'-' if var=='Electrons' else '+'}ElectronCharge * {var}")
        CreateNodeModelDerivative(device_name, region, f"{var}Charge", 
                                   f"{'-' if var=='Electrons' else '+'}ElectronCharge * {var}", var)
        
        equation(device=device_name, region=region, name=name, variable_name=var,
                 edge_model=current, node_model=gen, variable_update="positive")

for region, contact in [("LWIR", "bottom"), ("VLWIR", "top")]:
    nelec = "0.5*(pow(NetDoping,2) + 4*pow(n_i,2))^0.5 + 0.5*NetDoping"
    nhole = "0.5*(pow(NetDoping,2) + 4*pow(n_i,2))^0.5 - 0.5*NetDoping"
    
    # 电子接触条件
    CreateContactNodeModel(device_name, contact, f"{contact}nodeelectrons", f"Electrons - {nelec}")
    CreateContactNodeModel(device_name, contact, f"{contact}nodeelectrons:Electrons", "1")
    contact_equation(device=device_name, contact=contact, name="ElectronContinuityEquation",
                     node_model=f"{contact}nodeelectrons", edge_current_model="ElectronCurrent")
    
    # 空穴接触条件
    CreateContactNodeModel(device_name, contact, f"{contact}nodeholes", f"Holes - {nhole}")
    CreateContactNodeModel(device_name, contact, f"{contact}nodeholes:Holes", "1")
    contact_equation(device=device_name, contact=contact, name="HoleContinuityEquation",
                     node_model=f"{contact}nodeholes", edge_current_model="HoleCurrent")

print("  Drift-diffusion added")

# =============================================================================
# 求解
# =============================================================================

print("\n[6/6] Solving drift-diffusion...")

solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=50)
print("  Drift-diffusion solved")

# 保存数据
print("\n  Extracting data...")
x_all, V_all, n_all, p_all = [], [], [], []

for region in ["VLWIR", "Barrier", "LWIR"]:
    x = get_node_model_values(device=device_name, region=region, name="x")
    V = get_node_model_values(device=device_name, region=region, name="Potential")
    n = get_node_model_values(device=device_name, region=region, name="Electrons")
    p = get_node_model_values(device=device_name, region=region, name="Holes")
    x_all.extend(x)
    V_all.extend(V)
    n_all.extend(n)
    p_all.extend(p)

eq_data = {
    'x': x_all, 'V': V_all, 'n': n_all, 'p': p_all,
    'region_boundaries': [0, VLWIR_t, VLWIR_t + Barrier_t, total_length]
}

with open('exp_oc/JEM2025_corrected_equilibrium.json', 'w') as f:
    json.dump(eq_data, f, indent=2)

print("  Saved: JEM2025_corrected_equilibrium.json")

# IV扫描
print("\nRunning IV sweep (-0.4V to +0.4V)...")

voltages = np.linspace(-0.4, 0.4, 17)
currents = []

for i, V in enumerate(voltages):
    set_parameter(device=device_name, name="Vtop", value=V)
    
    try:
        solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
        
        Jn = get_contact_current(device=device_name, contact="top", equation="ElectronContinuityEquation")
        Jp = get_contact_current(device=device_name, contact="top", equation="HoleContinuityEquation")
        J = Jn + Jp
        currents.append(J)
        
        if i % 4 == 0:
            print(f"  V={V:+.2f}V: J={J:.4e} A/cm2")
    except Exception as e:
        print(f"  V={V:+.2f}V: Failed - {e}")
        currents.append(None)

iv_data = {
    'voltage': voltages.tolist(),
    'current': currents,
    'temperature': T,
    'device': 'nBn_HgCdTe_corrected'
}

with open('exp_oc/JEM2025_corrected_iv.json', 'w') as f:
    json.dump(iv_data, f, indent=2)

print("\n  Saved: JEM2025_corrected_iv.json")

print("\n" + "="*70)
print("Simulation Complete!")
print("="*70)
print(f"\nCorrected thickness:")
print(f"  VLWIR: {VLWIR_t} μm")
print(f"  Barrier: {Barrier_t} μm")
print(f"  LWIR: {LWIR_t} μm")
print("="*70)
