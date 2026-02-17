#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

import devsim
from devsim.python_packages.simple_physics import SetSiliconParameters, GetContactBiasName
from devsim.python_packages.model_create import CreateSolution
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly, CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact
)
import json
from datetime import datetime
import os

L_fp = 6.0
print(f"\n======================================================================")
print(f"仿真场板长度 L_fp = {L_fp} μm")
print(f"======================================================================")

mesh_file = f"simple_L{L_fp}.msh"

# 清理
try:
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode_mesh")
except:
    pass

# 加载网格
devsim.create_gmsh_mesh(mesh="diode_mesh", file=mesh_file)
devsim.add_gmsh_region(gmsh_name="pplus", mesh="diode_mesh", region="pplus", material="Si")
devsim.add_gmsh_region(gmsh_name="ndrift", mesh="diode_mesh", region="ndrift", material="Si")
devsim.add_gmsh_contact(gmsh_name="anode", mesh="diode_mesh", name="anode", material="metal", region="pplus")
devsim.add_gmsh_contact(gmsh_name="cathode", mesh="diode_mesh", name="cathode", material="metal", region="ndrift")
devsim.finalize_mesh(mesh="diode_mesh")
devsim.create_device(mesh="diode_mesh", device="diode")

# 设置物理参数
SetSiliconParameters("diode", "pplus", 300)
SetSiliconParameters("diode", "ndrift", 300)

# 掺杂
devsim.node_model(device="diode", region="pplus", name="Acceptors", equation="1e19")
devsim.node_model(device="diode", region="pplus", name="NetDoping", equation="Acceptors")

# 渐变掺杂
try:
    devsim.node_model(
        device="diode", region="ndrift",
        name="NetDoping",
        equation="1e14 + (1e19-1e14)/(1+exp((x-5e-4)/0.2e-4))"
    )
except:
    devsim.node_model(device="diode", region="ndrift", name="NetDoping", equation="1e14")

# 求解势
for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Potential")
    CreateSiliconPotentialOnly("diode", region)

devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)

for region in ["pplus", "ndrift"]:
    CreateSiliconPotentialOnlyContact("diode", region, "anode")
    CreateSiliconPotentialOnlyContact("diode", region, "cathode")

devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=100)

# 添加载流子
for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Electrons")
    CreateSolution("diode", region, "Holes")
    devsim.set_node_values(device="diode", region=region, name="Electrons", init_from="IntrinsicElectrons")
    devsim.set_node_values(device="diode", region=region, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion("diode", region)
    CreateSiliconDriftDiffusionAtContact("diode", region, "anode")
    CreateSiliconDriftDiffusionAtContact("diode", region, "cathode")

# 求解漂移扩散
devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-4, maximum_iterations=200)
devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-6, maximum_iterations=200)

# 电压扫描（去掉-200V，避免收敛问题）
voltages = [-5, -10, -20, -30, -40, -50, -60, -80, -100, -120, -150]
results = []
current_v = 0.0
step = 0.5

for target_v in voltages:
    while current_v > target_v + step/2:
        next_v = max(target_v, current_v - step)
        try:
            devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=next_v)
            devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-5, maximum_iterations=300)
            current_v = next_v
            
            if abs(current_v - target_v) < step/2:
                current = devsim.get_contact_current(device="diode", contact="anode")
                E_field = devsim.get_edge_model_values(device="diode", region="ndrift", name="ElectricField")
                max_E = max(abs(x) for x in E_field) if E_field else 0
                results.append({"V": target_v, "I": current, "E": max_E})
                print(f"V={target_v}V: I={current:.2e}A, Emax={max_E:.2e}V/cm")
                break
        except:
            step = step / 2
            if step < 0.1:
                break
            continue

# 保存结果
os.makedirs("data/final", exist_ok=True)
result_data = {
    "L_fp": L_fp,
    "timestamp": datetime.now().isoformat(),
    "voltages": [r["V"] for r in results],
    "currents": [r["I"] for r in results],
    "max_electric_fields": [r["E"] for r in results],
    "n_points": len(results)
}

with open(f"data/final/devsim_dd_results_L{L_fp}.json", "w") as f:
    json.dump(result_data, f, indent=2)

print(f"\n✓ 结果已保存: devsim_dd_results_L{L_fp}.json")
print(f"完成点数: {len(results)}")

devsim.delete_device(device="diode")
devsim.delete_mesh(mesh="diode_mesh")
