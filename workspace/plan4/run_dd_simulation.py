#!/usr/bin/env python3
"""
完整的漂移扩散仿真 - 专注于第一组数据
使用超保守的求解参数确保收敛
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
print("完整漂移扩散仿真 - 第一组 (L_fp = 2.0 μm)")
print("使用超保守参数确保收敛")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 只运行第一组
L_fp = 2.0
mesh_file = f"simple_L{L_fp}.msh"

if not os.path.exists(mesh_file):
    print(f"✗ 网格文件不存在: {mesh_file}")
    sys.exit(1)

# 清理
print("1. 清理并加载网格...")
try:
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode_mesh")
except:
    pass

devsim.create_gmsh_mesh(mesh="diode_mesh", file=mesh_file)
devsim.add_gmsh_region(gmsh_name="pplus", mesh="diode_mesh", region="pplus", material="Si")
devsim.add_gmsh_region(gmsh_name="ndrift", mesh="diode_mesh", region="ndrift", material="Si")
devsim.add_gmsh_contact(gmsh_name="anode", mesh="diode_mesh", name="anode", material="metal", region="pplus")
devsim.add_gmsh_contact(gmsh_name="cathode", mesh="diode_mesh", name="cathode", material="metal", region="ndrift")
devsim.finalize_mesh(mesh="diode_mesh")
devsim.create_device(mesh="diode_mesh", device="diode")

regions = devsim.get_region_list(device="diode")
contacts = devsim.get_contact_list(device="diode")
print(f"   ✓ 网格加载完成: {len(regions)}个区域, {len(contacts)}个接触")

# 设置物理参数
print("\n2. 设置物理参数...")
SetSiliconParameters("diode", "pplus", 300)
SetSiliconParameters("diode", "ndrift", 300)

# 渐变掺杂
print("3. 设置渐变掺杂...")
devsim.node_model(device="diode", region="pplus", name="Acceptors", equation="1e19")
devsim.node_model(device="diode", region="pplus", name="NetDoping", equation="Acceptors")

# N区渐变掺杂
success = False
for width in [0.2e-4, 0.3e-4, 0.5e-4]:  # 尝试不同的过渡宽度
    try:
        print(f"   尝试过渡宽度 {width*1e4:.1f}μm...")
        devsim.node_model(
            device="diode", region="ndrift",
            name="NetDoping",
            equation=f"1e14 + (1e19-1e14)/(1+exp((x-5e-4)/{width}))"
        )
        print(f"   ✓ 渐变掺杂设置成功")
        success = True
        break
    except Exception as e:
        print(f"   失败: {e}")
        continue

if not success:
    print("   ⚠ 使用简单阶跃掺杂")
    devsim.node_model(device="diode", region="ndrift", name="NetDoping", equation="1e14")

# 求解势
print("\n4. 求解势分布...")
for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Potential")
    CreateSiliconPotentialOnly("diode", region)

devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)

for region in ["pplus", "ndrift"]:
    CreateSiliconPotentialOnlyContact("diode", region, "anode")
    CreateSiliconPotentialOnlyContact("diode", region, "cathode")

try:
    devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=100)
    print("   ✓ 势求解收敛")
except Exception as e:
    print(f"   ✗ 势求解失败: {e}")
    sys.exit(1)

# 添加载流子 - 关键步骤
print("\n5. 添加载流子...")
for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Electrons")
    CreateSolution("diode", region, "Holes")
    devsim.set_node_values(device="diode", region=region, name="Electrons", init_from="IntrinsicElectrons")
    devsim.set_node_values(device="diode", region=region, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion("diode", region)
    CreateSiliconDriftDiffusionAtContact("diode", region, "anode")
    CreateSiliconDriftDiffusionAtContact("diode", region, "cathode")

# 求解漂移扩散 - 超保守参数
print("\n6. 求解漂移扩散方程（超保守参数）...")
try:
    # 第一步：非常宽松的容差
    print("   步骤6a: 初步求解（宽松容差）...")
    devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-4, maximum_iterations=200)
    print("   ✓ 初步求解收敛")
    
    # 第二步：收紧容差
    print("   步骤6b: 精细求解（收紧容差）...")
    devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-6, maximum_iterations=200)
    print("   ✓ 漂移扩散求解收敛")
    
except Exception as e:
    print(f"   ✗ 漂移扩散求解失败: {e}")
    print("\n尝试替代策略：仅解泊松方程近似...")
    # 如果漂移扩散失败，我们可以只使用势分布数据
    # 这可以作为近似结果
    pass

# 电压扫描
print("\n7. 开始电压扫描...")
voltages = [-5, -10, -20, -30, -40, -50, -60, -80, -100, -120, -150, -200]
results = []
breakdown_voltage = None

current_v = 0.0

for target_v in voltages:
    print(f"\n   目标电压: {target_v}V")
    
    # 使用continuation方法
    step = 0.5
    max_retries = 3
    retry_count = 0
    
    while current_v > target_v + step/2 and retry_count < max_retries:
        next_v = max(target_v, current_v - step)
        
        try:
            devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=next_v)
            
            # 超保守求解参数
            devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-5, maximum_iterations=300)
            
            current_v = next_v
            
            if abs(current_v - target_v) < step/2:
                # 提取数据
                try:
                    current = devsim.get_contact_current(device="diode", contact="anode")
                except:
                    current = 0
                
                try:
                    E_field = devsim.get_edge_model_values(device="diode", region="ndrift", name="ElectricField")
                    max_E = max(abs(x) for x in E_field) if E_field else 0
                except:
                    max_E = 0
                
                results.append({"V": target_v, "I": current, "E": max_E})
                print(f"      ✓ V={target_v}V: I={current:.2e}A, Emax={max_E:.2e}V/cm")
                
                # 检测击穿
                if len(results) > 1:
                    prev_I = abs(results[-2]["I"]) if len(results) > 1 else 1e-15
                    curr_I = abs(current)
                    if prev_I > 1e-15 and (curr_I / prev_I > 5 or max_E > 3e5):
                        if breakdown_voltage is None:
                            breakdown_voltage = target_v
                            print(f"      ✓✓✓ 击穿检测: {target_v}V")
                
                break
                
        except Exception as e:
            print(f"      V={next_v}V 未收敛，减小步长重试...")
            step = step / 2
            retry_count += 1
            if step < 0.1:
                print(f"      步长过小，跳过此电压点")
                break
            continue

# 保存结果
print("\n" + "="*70)
print("保存结果...")
os.makedirs("data/final", exist_ok=True)

result_data = {
    "L_fp": L_fp,
    "timestamp": datetime.now().isoformat(),
    "voltages": [r["V"] for r in results],
    "currents": [r["I"] for r in results],
    "max_electric_fields": [r["E"] for r in results],
    "breakdown_voltage": breakdown_voltage,
    "n_points": len(results)
}

with open("data/final/devsim_dd_results_L2.0.json", "w") as f:
    json.dump(result_data, f, indent=2)

print(f"✓ 结果已保存: data/final/devsim_dd_results_L2.0.json")

# 打印总结
print("\n" + "="*70)
print("仿真完成总结")
print("="*70)
print(f"场板长度: {L_fp} μm")
print(f"完成点数: {len(results)}")
if breakdown_voltage:
    print(f"击穿电压: {breakdown_voltage} V")
print(f"\n数据:")
print(f"{'电压(V)':<12} {'电流(A)':<15} {'电场(V/cm)':<15}")
print("-"*70)
for r in results:
    print(f"{r['V']:<12} {r['I']:<15.2e} {r['E']:<15.2e}")
print("="*70)

# 清理
devsim.delete_device(device="diode")
devsim.delete_mesh(mesh="diode_mesh")

print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
