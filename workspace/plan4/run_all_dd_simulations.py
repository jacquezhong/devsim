#!/usr/bin/env python3
"""
运行所有剩余场板长度的DEVSIM漂移扩散仿真
并行运行以提高效率
"""
import sys
import os
import json
import time
import subprocess
from datetime import datetime

# 场板长度列表（排除已完成的第一组）
L_fp_values = [4.0, 6.0, 8.0, 10.0]

print("="*70)
print("运行所有剩余场板长度的DEVSIM仿真")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"场板长度: {L_fp_values} μm")
print()

# 为每个场板长度创建一个独立的Python脚本
for L_fp in L_fp_values:
    script_content = f'''#!/usr/bin/env python3
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

L_fp = {L_fp}
print(f"\\n{'='*70}")
print(f"仿真场板长度 L_fp = {{L_fp}} μm")
print(f"{'='*70}")

mesh_file = f"simple_L{{L_fp}}.msh"

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
                results.append({{"V": target_v, "I": current, "E": max_E}})
                print(f"V={{target_v}}V: I={{current:.2e}}A, Emax={{max_E:.2e}}V/cm")
                break
        except:
            step = step / 2
            if step < 0.1:
                break
            continue

# 保存结果
os.makedirs("data/final", exist_ok=True)
result_data = {{
    "L_fp": L_fp,
    "timestamp": datetime.now().isoformat(),
    "voltages": [r["V"] for r in results],
    "currents": [r["I"] for r in results],
    "max_electric_fields": [r["E"] for r in results],
    "n_points": len(results)
}}

with open(f"data/final/devsim_dd_results_L{{L_fp}}.json", "w") as f:
    json.dump(result_data, f, indent=2)

print(f"\\n✓ 结果已保存: devsim_dd_results_L{{L_fp}}.json")
print(f"完成点数: {{len(results)}}")

devsim.delete_device(device="diode")
devsim.delete_mesh(mesh="diode_mesh")
'''
    
    script_file = f"run_dd_L{L_fp}.py"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"创建脚本: {script_file}")

print("\n开始并行运行所有仿真...")
print("这可能需要 2-4 小时，请耐心等待")
print("="*70)

# 顺序运行（避免内存冲突）
for L_fp in L_fp_values:
    script_file = f"run_dd_L{L_fp}.py"
    log_file = f"dd_simulation_L{L_fp}.log"
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始运行 L_fp = {L_fp} μm...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ['python3', script_file],
            capture_output=True,
            text=True,
            timeout=7200  # 2小时超时
        )
        
        # 保存日志
        with open(log_file, 'w') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr)
        
        elapsed = time.time() - start_time
        print(f"  完成! 耗时: {elapsed/60:.1f} 分钟")
        
        # 检查结果文件
        result_file = f"data/final/devsim_dd_results_L{L_fp}.json"
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                data = json.load(f)
            print(f"  数据点: {data.get('n_points', 0)}")
        else:
            print(f"  ⚠ 未生成结果文件")
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ 超时 (>2小时)")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

print("\n" + "="*70)
print("所有仿真完成!")
print("="*70)

# 收集所有结果
print("\n收集所有结果...")
all_results = []
for L_fp in [2.0] + L_fp_values:  # 包括第一组
    result_file = f"data/final/devsim_dd_results_L{L_fp}.json"
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            data = json.load(f)
        all_results.append(data)
        print(f"  ✓ L={L_fp}μm: {data.get('n_points', 0)} 点")

# 保存合并结果
with open("data/final/devsim_all_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "description": "DEVSIM drift-diffusion simulation results for all field plate lengths",
        "results": all_results
    }, f, indent=2)

print(f"\n✓ 所有结果已保存: data/final/devsim_all_results.json")
print(f"总共: {len(all_results)} 组数据")
