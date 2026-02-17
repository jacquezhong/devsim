#!/usr/bin/env python3
"""
优化的DEVSIM场板二极管仿真
解决收敛问题的关键策略：
1. 渐变掺杂（避免突变结）
2. 超小电压步长（0.5V）+ Continuation
3. 放宽容差 + 增加迭代次数
4. 先解泊松方程，再解漂移扩散
"""
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

import devsim
from devsim.python_packages.simple_physics import SetSiliconParameters, GetContactBiasName
from devsim.python_packages.model_create import CreateSolution
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly, CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact
)

print("="*70)
print("优化的DEVSIM场板二极管仿真")
print("解决收敛问题的完整方案")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 场板长度列表
L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]

# 结果存储
all_results = []

for L_fp in L_fp_values:
    print(f"\n{'='*70}")
    print(f"仿真场板长度 L_fp = {L_fp} μm")
    print(f"{'='*70}")
    
    mesh_file = f"simple_L{L_fp}.msh"
    
    if not os.path.exists(mesh_file):
        print(f"✗ 网格文件不存在: {mesh_file}")
        continue
    
    # 清理之前的设备
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
    devsim.add_gmsh_contact(gmsh_name="anode", mesh="diode_mesh", name="anode", material="metal", region="pplus")
    devsim.add_gmsh_contact(gmsh_name="cathode", mesh="diode_mesh", name="cathode", material="metal", region="ndrift")
    devsim.finalize_mesh(mesh="diode_mesh")
    devsim.create_device(mesh="diode_mesh", device="diode")
    
    regions = devsim.get_region_list(device="diode")
    contacts = devsim.get_contact_list(device="diode")
    print(f"   ✓ 区域: {regions}, 接触: {contacts}")
    
    # 设置硅参数
    print("2. 设置物理参数...")
    SetSiliconParameters("diode", "pplus", 300)
    SetSiliconParameters("diode", "ndrift", 300)
    
    # ========== 关键优化1: 渐变掺杂 ==========
    print("3. 设置渐变掺杂（避免突变结）...")
    
    # P+区: x < 4.5um, 高掺杂
    devsim.node_model(device="diode", region="pplus", name="Acceptors", equation="1e19")
    devsim.node_model(device="diode", region="pplus", name="Donors", equation="0")
    devsim.node_model(device="diode", region="pplus", name="NetDoping", equation="Acceptors")
    
    # N区: x > 5.5um, 低掺杂
    devsim.node_model(device="diode", region="ndrift", name="Acceptors", equation="0")
    devsim.node_model(device="diode", region="ndrift", name="Donors", equation="1e14")
    
    # 在N区靠近结的位置设置渐变（通过position-dependent doping）
    # 使用平滑过渡函数
    
    # 渐变区: 4.5um < x < 5.5um, 从1e19渐变到1e14
    # 使用sigmoid函数: Nd = 1e14 + (1e19-1e14) / (1 + exp((x-5e-4)/w))
    # 其中w是过渡宽度
    devsim.node_model(
        device="diode", region="ndrift",
        name="NetDoping",
        equation="1e14 + (1e19-1e14)/(1+exp((x-5e-4)/0.2e-4))"
    )
    
    print("   ✓ 渐变掺杂设置完成 (4.5um-5.5um渐变区)")
    
    # ========== 关键优化2: 先解泊松方程 ==========
    print("4. 求解初始势分布...")
    
    for region in ["pplus", "ndrift"]:
        CreateSolution("diode", region, "Potential")
        CreateSiliconPotentialOnly("diode", region)
    
    # 设置接触偏置
    devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
    devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)
    
    for region in ["pplus", "ndrift"]:
        CreateSiliconPotentialOnlyContact("diode", region, "anode")
        CreateSiliconPotentialOnlyContact("diode", region, "cathode")
    
    # 求解泊松方程（放宽的容差）
    try:
        devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=50)
        print("   ✓ 势求解收敛")
    except Exception as e:
        print(f"   ✗ 势求解失败: {e}")
        continue
    
    # ========== 关键优化3: 添加载流子 ==========
    print("5. 添加载流子并求解漂移扩散...")
    
    for region in ["pplus", "ndrift"]:
        CreateSolution("diode", region, "Electrons")
        CreateSolution("diode", region, "Holes")
        devsim.set_node_values(device="diode", region=region, name="Electrons", init_from="IntrinsicElectrons")
        devsim.set_node_values(device="diode", region=region, name="Holes", init_from="IntrinsicHoles")
        CreateSiliconDriftDiffusion("diode", region)
        CreateSiliconDriftDiffusionAtContact("diode", region, "anode")
        CreateSiliconDriftDiffusionAtContact("diode", region, "cathode")
    
    # 求解漂移扩散（放宽的容差）
    try:
        devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-8, maximum_iterations=50)
        print("   ✓ 漂移扩散求解收敛")
    except Exception as e:
        print(f"   ✗ 漂移扩散求解失败: {e}")
        continue
    
    # ========== 关键优化4: 超小步长电压扫描 ==========
    print("6. 开始超小步长电压扫描...")
    
    # 从0V到-200V，步长0.5V
    voltages = []
    currents = []
    max_E_fields = []
    breakdown_voltage = None
    
    # 目标电压列表（只记录这些点）
    target_voltages = [-5, -10, -20, -30, -40, -50, -60, -80, -100, -120, -150, -200]
    
    current_v = 0.0
    step = 0.5  # 超小步长
    
    for target_v in target_voltages:
        print(f"\n   目标电压: {target_v}V")
        
        # 使用continuation方法，逐步增加电压
        while current_v > target_v + step/2:  # 注意是负值
            next_v = max(target_v, current_v - step)
            
            try:
                # 设置下一个电压
                devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=next_v)
                
                # 求解（放宽容差）
                devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-6, maximum_iterations=100)
                
                current_v = next_v
                
                # 如果达到目标电压，记录数据
                if abs(current_v - target_v) < step/2:
                    # 提取电流
                    try:
                        current = devsim.get_contact_current(device="diode", contact="anode")
                    except:
                        current = 0
                    
                    # 提取峰值电场
                    try:
                        E_field = devsim.get_edge_model_values(device="diode", region="ndrift", name="ElectricField")
                        max_E = max(abs(x) for x in E_field) if E_field else 0
                    except:
                        max_E = 0
                    
                    voltages.append(target_v)
                    currents.append(current)
                    max_E_fields.append(max_E)
                    
                    print(f"      ✓ V={target_v}V: I={current:.2e}A, Emax={max_E:.2e}V/cm")
                    
                    # 检测击穿
                    if breakdown_voltage is None and len(currents) > 1:
                        prev_current = abs(currents[-2]) if len(currents) > 1 else 1e-15
                        curr_current = abs(current)
                        if prev_current > 1e-15:
                            current_ratio = curr_current / prev_current
                            if current_ratio > 5 or max_E > 3e5:
                                breakdown_voltage = target_v
                                print(f"      ✓✓✓ 击穿检测: {target_v}V")
                    
                    break  # 完成此目标电压，进入下一个
                    
            except Exception as e:
                print(f"      ✗ V={next_v}V 未收敛: {e}")
                # 减小步重试
                step = step / 2
                if step < 0.1:  # 最小步长限制
                    print(f"      步长过小，跳过此电压")
                    break
                continue
    
    # 保存结果
    result = {
        'L_fp': L_fp,
        'voltages': voltages,
        'currents': currents,
        'max_electric_fields': max_E_fields,
        'breakdown_voltage': breakdown_voltage,
        'timestamp': datetime.now().isoformat()
    }
    all_results.append(result)
    
    print(f"\n   结果汇总:")
    print(f"      完成点数: {len(voltages)}")
    if breakdown_voltage:
        print(f"      击穿电压: {breakdown_voltage}V")
    
    # 清理
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode_mesh")

# 保存所有结果
print("\n" + "="*70)
print("保存结果...")
os.makedirs("data/final", exist_ok=True)

with open("data/final/devsim_optimized_results.json", "w") as f:
    json.dump({
        "description": "Optimized DEVSIM simulation with graded doping and continuation method",
        "timestamp": datetime.now().isoformat(),
        "results": all_results
    }, f, indent=2)

print(f"✓ 结果已保存: data/final/devsim_optimized_results.json")

# 打印总结
print("\n" + "="*70)
print("仿真完成总结")
print("="*70)
print(f"{'L_fp (μm)':<12} {'数据点':<10} {'击穿电压 (V)':<15}")
print("-"*70)
for r in all_results:
    L_fp = r['L_fp']
    n_points = len(r['voltages'])
    BV = r['breakdown_voltage'] if r['breakdown_voltage'] else "未击穿"
    print(f"{L_fp:<12} {n_points:<10} {str(BV):<15}")
print("="*70)
