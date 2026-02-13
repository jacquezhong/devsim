# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_reproduce_figures.py - 复现论文图5和图6
支持两组厚度参数:
- Figure 5: VLWIR=5μm, Barrier=0.2μm, LWIR=5μm (优化设计)
- Figure 6: VLWIR=14μm, Barrier=0.2μm, LWIR=9μm (对比用)

用法:
  python JEM2025_reproduce_figures.py --figure 5  # 生成图5数据
  python JEM2025_reproduce_figures.py --figure 6  # 生成图6数据
"""

import os
import sys
import json
import numpy as np
import argparse

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


def run_simulation(figure_num, output_prefix):
    """
    运行指定图号的仿真
    
    Args:
        figure_num: 5 或 6
        output_prefix: 输出文件前缀
    """
    
    # 物理常数
    q = 1.602e-19
    kb = 8.617e-5
    k = 1.3806e-14
    eps_0 = 8.854e-14
    
    T = 100.0
    V_t = kb * T
    
    # =============================================================================
    # 根据图号选择厚度参数
    # =============================================================================
    
    if figure_num == 5:
        # Figure 5: 优化设计结构 (来自图4)
        VLWIR_t = 5.0      # μm
        Barrier_t = 0.2    # μm  
        LWIR_t = 5.0       # μm
        config_name = "Figure 5 (Optimized Design)"
    elif figure_num == 6:
        # Figure 6: 对比用结构 (用于与Man的工作对比)
        VLWIR_t = 14.0     # μm
        Barrier_t = 0.2    # μm
        LWIR_t = 9.0       # μm
        config_name = "Figure 6 (Comparison with Man's Work)"
    else:
        raise ValueError(f"Invalid figure number: {figure_num}. Must be 5 or 6.")
    
    total_length = VLWIR_t + Barrier_t + LWIR_t
    
    print("="*70)
    print(f"JEM2025 - Reproducing {config_name}")
    print("="*70)
    print(f"\nDevice Structure:")
    print(f"  VLWIR absorber: {VLWIR_t} μm")
    print(f"  Barrier: {Barrier_t} μm")
    print(f"  LWIR absorber: {LWIR_t} μm")
    print(f"  Total: {total_length} μm")
    print(f"  Temperature: {T} K")
    
    # =============================================================================
    # 材料参数 (Table II - 与厚度无关)
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
    # 创建网格 (根据厚度动态生成)
    # =============================================================================
    
    device_name = f"nBn_F{figure_num}"
    print(f"\n[1/6] Creating device {device_name}...")
    
    create_1d_mesh(mesh="nBn_mesh")
    
    # 根据厚度动态生成网格线
    # VLWIR区域: 0 - VLWIR_t μm
    barrier_start = VLWIR_t
    barrier_end = VLWIR_t + Barrier_t
    
    # VLWIR网格 (使用适当的网格密度)
    vlwir_ps = min(0.1, VLWIR_t / 20)  # 根据厚度调整网格密度
    for i in range(0, int(VLWIR_t) + 1, max(1, int(VLWIR_t / 10))):
        ps = 0.05 if i < 1 or i > VLWIR_t - 1 else vlwir_ps
        add_1d_mesh_line(mesh="nBn_mesh", pos=float(i), ps=ps, tag=f"vlwir_{i}")
    
    # 确保终点有网格线
    add_1d_mesh_line(mesh="nBn_mesh", pos=barrier_start - 0.1, ps=0.05, tag="vlwir_end")
    
    # Barrier区域: VLWIR_t - (VLWIR_t + Barrier_t) μm (极细网格)
    add_1d_mesh_line(mesh="nBn_mesh", pos=barrier_start, ps=0.02, tag="barrier_start")
    add_1d_mesh_line(mesh="nBn_mesh", pos=barrier_start + Barrier_t/2, ps=0.01, tag="barrier_mid")
    add_1d_mesh_line(mesh="nBn_mesh", pos=barrier_end, ps=0.02, tag="barrier_end")
    
    # LWIR网格
    lwir_ps = min(0.1, LWIR_t / 20)
    for i in range(int(barrier_end) + 1, int(total_length), max(1, int(LWIR_t / 10))):
        add_1d_mesh_line(mesh="nBn_mesh", pos=float(i), ps=lwir_ps, tag=f"lwir_{i}")
    
    # 确保终点有网格线
    add_1d_mesh_line(mesh="nBn_mesh", pos=total_length, ps=0.05, tag="bottom")
    
    # 创建区域
    add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="VLWIR",
                  tag1="vlwir_0" if VLWIR_t >= 1 else "vlwir_end", tag2="barrier_start")
    add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="Barrier",
                  tag1="barrier_start", tag2="barrier_end")
    add_1d_region(mesh="nBn_mesh", material="HgCdTe", region="LWIR",
                  tag1="barrier_end", tag2="bottom")
    
    # 接触
    add_1d_contact(mesh="nBn_mesh", name="top", tag="vlwir_0" if VLWIR_t >= 1 else "vlwir_end", material="metal")
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
        'region_boundaries': [0, VLWIR_t, VLWIR_t + Barrier_t, total_length],
        'thickness': {'VLWIR': VLWIR_t, 'Barrier': Barrier_t, 'LWIR': LWIR_t},
        'figure': figure_num
    }
    
    eq_file = f'exp_oc/{output_prefix}_equilibrium.json'
    with open(eq_file, 'w') as f:
        json.dump(eq_data, f, indent=2)
    
    print(f"  Saved: {eq_file}")
    
    # IV扫描
    print(f"\nRunning IV sweep (-0.4V to +0.4V) for Figure {figure_num}...")
    
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
        'device': f'nBn_HgCdTe_Figure{figure_num}',
        'figure': figure_num
    }
    
    iv_file = f'exp_oc/{output_prefix}_iv.json'
    with open(iv_file, 'w') as f:
        json.dump(iv_data, f, indent=2)
    
    print(f"\n  Saved: {iv_file}")
    
    print("\n" + "="*70)
    print(f"Figure {figure_num} Simulation Complete!")
    print("="*70)
    print(f"\nThickness used:")
    print(f"  VLWIR: {VLWIR_t} μm")
    print(f"  Barrier: {Barrier_t} μm")
    print(f"  LWIR: {LWIR_t} μm")
    print("="*70)
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Run JEM2025 simulations for Figure 5 or 6')
    parser.add_argument('--figure', type=int, choices=[5, 6], required=True,
                       help='Which figure to simulate (5 or 6)')
    parser.add_argument('--both', action='store_true',
                       help='Run both Figure 5 and Figure 6 simulations')
    
    args = parser.parse_args()
    
    if args.both:
        # 运行两组仿真
        print("\n" + "="*70)
        print("Running both Figure 5 and Figure 6 simulations")
        print("="*70 + "\n")
        
        success5 = run_simulation(5, "JEM2025_Figure5")
        print("\n" + "="*70 + "\n")
        success6 = run_simulation(6, "JEM2025_Figure6")
        
        if success5 and success6:
            print("\n" + "="*70)
            print("Both simulations completed successfully!")
            print("="*70)
        else:
            print("\nSome simulations failed.")
    else:
        # 运行单个仿真
        output_prefix = f"JEM2025_Figure{args.figure}"
        run_simulation(args.figure, output_prefix)


if __name__ == "__main__":
    main()
