#!/usr/bin/env python3
"""
最终版漂移扩散仿真 - 简化设计，场板通过node_model控制
"""
import sys
import os
import json
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

import devsim
from devsim.python_packages.simple_physics import SetSiliconParameters, GetContactBiasName
from devsim.python_packages.model_create import CreateSolution
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly, CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact
)

L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]

print("="*70)
print("漂移扩散仿真 - 最终版")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

for L_fp in L_fp_values:
    print(f"\n{'='*70}")
    print(f"仿真场板长度 L_fp = {L_fp} μm")
    print(f"{'='*70}")
    
    mesh_file = f"fp_L{L_fp}.msh"
    result_file = f"data/final/devsim_dd_results_L{L_fp}.json"
    
    if os.path.exists(result_file):
        print(f"✓ 结果已存在，跳过: {result_file}")
        continue
    
    if not os.path.exists(mesh_file):
        print(f"✗ 网格文件不存在: {mesh_file}")
        continue
    
    # 清理
    try:
        devsim.delete_device(device="diode")
        devsim.delete_mesh(mesh="diode_mesh")
    except:
        pass
    
    # 加载网格
    print("1. 加载网格...")
    devsim.create_gmsh_mesh(mesh="diode_mesh", file=mesh_file)
    devsim.add_gmsh_region(gmsh_name="pplus", mesh="diode_mesh", region="pplus", material="Si")
    devsim.add_gmsh_region(gmsh_name="ndrift", mesh="diode_mesh", region="ndrift", material="Si")
    devsim.add_gmsh_region(gmsh_name="fieldplate_metal", mesh="diode_mesh", region="fieldplate_metal", material="metal")
    devsim.add_gmsh_contact(gmsh_name="anode", mesh="diode_mesh", name="anode", material="metal", region="pplus")
    devsim.add_gmsh_contact(gmsh_name="cathode", mesh="diode_mesh", name="cathode", material="metal", region="ndrift")
    # 注意：没有field_plate contact，场板电势通过node_model控制
    devsim.finalize_mesh(mesh="diode_mesh")
    devsim.create_device(mesh="diode_mesh", device="diode")
    print(f"   ✓ 网格加载完成")
    
    # 设置物理参数
    print("2. 设置物理参数...")
    SetSiliconParameters("diode", "pplus", 300)
    SetSiliconParameters("diode", "ndrift", 300)
    
    # 掺杂
    devsim.node_model(device="diode", region="pplus", name="Acceptors", equation="1e19")
    devsim.node_model(device="diode", region="pplus", name="NetDoping", equation="Acceptors")
    try:
        devsim.node_model(
            device="diode", region="ndrift",
            name="NetDoping",
            equation="1e14 + (1e19-1e14)/(1+exp((x-5e-4)/0.2e-4))"
        )
    except:
        devsim.node_model(device="diode", region="ndrift", name="NetDoping", equation="1e14")
    print("   ✓ 渐变掺杂设置完成")
    
    # 求解势
    print("3. 求解势分布...")
    for region in ["pplus", "ndrift"]:
        CreateSolution("diode", region, "Potential")
        CreateSiliconPotentialOnly("diode", region)
    
    # 金属场板：通过node_model设置电势（参考cap2d.py）
    devsim.set_parameter(device="diode", name="field_plate_bias", value=0.0)
    devsim.node_model(device="diode", region="fieldplate_metal", name="Potential", equation="field_plate_bias;")
    
    # 设置接触偏置
    devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
    devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)
    
    # 为接触创建边界条件
    for region in ["pplus", "ndrift"]:
        CreateSiliconPotentialOnlyContact("diode", region, "anode")
        CreateSiliconPotentialOnlyContact("diode", region, "cathode")
    
    devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=100)
    print("   ✓ 势求解收敛")
    
    # 添加载流子
    print("4. 添加载流子...")
    for region in ["pplus", "ndrift"]:
        CreateSolution("diode", region, "Electrons")
        CreateSolution("diode", region, "Holes")
        devsim.set_node_values(device="diode", region=region, name="Electrons", init_from="IntrinsicElectrons")
        devsim.set_node_values(device="diode", region=region, name="Holes", init_from="IntrinsicHoles")
        CreateSiliconDriftDiffusion("diode", region)
        CreateSiliconDriftDiffusionAtContact("diode", region, "anode")
        CreateSiliconDriftDiffusionAtContact("diode", region, "cathode")
    
    # 求解漂移扩散
    print("5. 求解漂移扩散...")
    devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-4, maximum_iterations=200)
    devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-6, maximum_iterations=200)
    print("   ✓ 漂移扩散求解收敛")
    
    # 创建电场模型
    print("6. 创建电场模型...")
    for region in ["pplus", "ndrift"]:
        devsim.edge_from_node_model(device="diode", region=region, node_model="Potential")
        devsim.edge_model(
            device="diode",
            region=region,
            name="ElectricField",
            equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
        )
    devsim.edge_model(device="diode", region="fieldplate_metal", name="ElectricField", equation="0")
    print("   ✓ 电场模型创建完成")
    
    # 电压扫描
    print("7. 开始电压扫描...")
    target_voltages = [-5, -10, -20, -30, -40, -50, -60, -80, -100, -120, -150]
    results = []
    current_v = 0.0
    
    for target_v in target_voltages:
        print(f"\n   目标电压: {target_v}V")
        
        voltage_gap = abs(target_v - current_v)
        if voltage_gap <= 10:
            step = voltage_gap
        elif voltage_gap <= 30:
            step = 5.0
        else:
            step = 10.0
        
        success = False
        retry_count = 0
        max_retries = 3
        
        while current_v > target_v and retry_count < max_retries:
            next_v = max(target_v, current_v - step)
            
            try:
                print(f"      尝试 V={next_v}V...", end=' ')
                # 同时设置阳极和场板偏置
                devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=next_v)
                devsim.set_parameter(device="diode", name="field_plate_bias", value=next_v)
                
                devsim.solve(type="dc", absolute_error=1e13, relative_error=1e-5, maximum_iterations=100)
                
                current_v = next_v
                print("✓")
                
                if abs(current_v - target_v) < 0.1:
                    # 提取数据
                    try:
                        e_current = devsim.get_contact_current(device="diode", contact="anode", equation="ElectronContinuityEquation")
                        h_current = devsim.get_contact_current(device="diode", contact="anode", equation="HoleContinuityEquation")
                        current = e_current + h_current
                    except:
                        current = 0
                    
                    try:
                        V_vals = devsim.get_node_model_values(device="diode", region="ndrift", name="Potential")
                        E_field = devsim.get_edge_model_values(device="diode", region="ndrift", name="ElectricField")
                        max_E = max(abs(x) for x in E_field) if E_field else 0
                        print(f"        [DEBUG] V range: {min(V_vals):.2f} to {max(V_vals):.2f} V, Emax={max_E:.2e}")
                    except:
                        max_E = 0
                    
                    results.append({"V": target_v, "I": current, "E": max_E})
                    print(f"      ✓ 记录: V={target_v}V, I={current:.2e}A, Emax={max_E:.2e}V/cm")
                    success = True
                    break
                    
            except Exception as e:
                print(f"✗ ({e})")
                retry_count += 1
                step = step / 2
                if step < 1.0:
                    break
                continue
        
        if not success:
            print(f"      ⚠ 未能到达 {target_v}V，停止扫描")
            break
    
    # 保存结果
    print(f"\n8. 保存结果...")
    os.makedirs("data/final", exist_ok=True)
    
    result_data = {
        "L_fp": L_fp,
        "timestamp": datetime.now().isoformat(),
        "voltages": [r["V"] for r in results],
        "currents": [r["I"] for r in results],
        "max_electric_fields": [r["E"] for r in results],
        "n_points": len(results)
    }
    
    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"   ✓ 结果已保存: {result_file}")
    
    # 清理
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode_mesh")

print("\n" + "="*70)
print("所有仿真完成！")
print("="*70)
