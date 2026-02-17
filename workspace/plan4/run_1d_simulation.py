#!/usr/bin/env python3
"""
简化版DEVSIM仿真 - 快速验证
使用简化的结构和稳健的求解
"""
import sys
import os
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

import devsim
from devsim.python_packages.simple_physics import SetSiliconParameters
from datetime import datetime

print("="*70)
print("DEVSIM场板二极管快速验证")
print("="*70)

# 创建简单的1D网格（从2D截面取中心线）
mesh_name = "diode_1d"
device_name = "diode"

# 使用DEVSIM内置的1D网格创建
devsim.create_1d_mesh(mesh=mesh_name)
devsim.add_1d_mesh_line(mesh=mesh_name, pos=0, ps=0.05e-4, tag="anode")
devsim.add_1d_mesh_line(mesh=mesh_name, pos=5e-4, ps=0.05e-4, tag="junction")
devsim.add_1d_mesh_line(mesh=mesh_name, pos=50e-4, ps=0.2e-4, tag="cathode")

devsim.add_1d_region(mesh=mesh_name, material="Si", region="pplus", tag1="anode", tag2="junction")
devsim.add_1d_region(mesh=mesh_name, material="Si", region="ndrift", tag1="junction", tag2="cathode")

devsim.add_1d_contact(mesh=mesh_name, name="anode", material="metal", tag="anode")
devsim.add_1d_contact(mesh=mesh_name, name="cathode", material="metal", tag="cathode")

devsim.finalize_mesh(mesh=mesh_name)
devsim.create_device(mesh=mesh_name, device=device_name)

print("✓ 1D网格创建完成")

# 设置参数
SetSiliconParameters(device_name, "pplus", 300)
SetSiliconParameters(device_name, "ndrift", 300)

# 设置掺杂
devsim.node_model(device=device_name, region="pplus", name="Acceptors", equation="1e19")
devsim.node_model(device=device_name, region="pplus", name="Donors", equation="0")
devsim.node_model(device=device_name, region="pplus", name="NetDoping", equation="Acceptors-Donors")

devsim.node_model(device=device_name, region="ndrift", name="Acceptors", equation="0")
devsim.node_model(device=device_name, region="ndrift", name="Donors", equation="1e14")
devsim.node_model(device=device_name, region="ndrift", name="NetDoping", equation="Donors-Acceptors")

print("✓ 物理模型设置完成")

# 求解初始解
from devsim.python_packages.model_create import CreateSolution
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly, CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact,
    GetContactBiasName
)

for region in ["pplus", "ndrift"]:
    CreateSolution(device_name, region, "Potential")
    CreateSiliconPotentialOnly(device_name, region)

devsim.set_parameter(device=device_name, name=GetContactBiasName("anode"), value=0.0)
devsim.set_parameter(device=device_name, name=GetContactBiasName("cathode"), value=0.0)

for region in ["pplus", "ndrift"]:
    CreateSiliconPotentialOnlyContact(device_name, region, "anode")
    CreateSiliconPotentialOnlyContact(device_name, region, "cathode")

devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=30)

print("✓ 势求解完成")

# 添加载流子
for region in ["pplus", "ndrift"]:
    CreateSolution(device_name, region, "Electrons")
    CreateSolution(device_name, region, "Holes")
    devsim.set_node_values(device=device_name, region=region, 
                          name="Electrons", init_from="IntrinsicElectrons")
    devsim.set_node_values(device=device_name, region=region, 
                          name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(device_name, region)
    CreateSiliconDriftDiffusionAtContact(device_name, region, "anode")
    CreateSiliconDriftDiffusionAtContact(device_name, region, "cathode")

devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)

print("✓ 漂移扩散求解完成")

# 扫描偏压
print("\n开始偏压扫描...")
voltages = [-5, -10, -15, -20, -30, -40, -50, -60, -80, -100, -120, -150, -200]
results = []

for v in voltages:
    try:
        print(f"  V = {v}V...", end=' ')
        devsim.set_parameter(device=device_name, name=GetContactBiasName("anode"), value=v)
        
        solve_info = devsim.solve(type="dc", absolute_error=1e12, 
                                 relative_error=1e-8, maximum_iterations=50)
        
        # 提取电流
        current = devsim.get_contact_current(device=device_name, contact="anode")
        
        # 提取电场
        try:
            E_field = devsim.get_edge_model_values(device=device_name, 
                                                   region="ndrift", name="ElectricField")
            max_E = max(abs(x) for x in E_field) if E_field else 0
        except:
            max_E = 0
        
        results.append({"V": v, "I": current, "E": max_E})
        print(f"I={current:.2e}A, Emax={max_E:.2e}V/cm")
        
    except Exception as e:
        print(f"失败: {e}")
        break

# 保存结果
import json
os.makedirs("data/final", exist_ok=True)
with open("data/final/devsim_1d_results.json", "w") as f:
    json.dump({
        "device": "1D_diode",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }, f, indent=2)

print("\n" + "="*70)
print("结果汇总:")
print(f"{'电压(V)':<12} {'电流(A)':<15} {'电场(V/cm)':<15}")
print("-"*70)
for r in results:
    print(f"{r['V']:<12} {r['I']:<15.2e} {r['E']:<15.2e}")
print("="*70)
print(f"\n结果已保存: data/final/devsim_1d_results.json")
