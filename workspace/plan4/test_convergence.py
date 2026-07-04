#!/usr/bin/env python3
"""
收敛性测试 - 使用小步长验证电场修复
测试L=6.0μm，电压步进0.25V，-0.5V到-5V
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
    CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact,
    CreateContinuousInterfaceModel
)
from devsim import interface_equation

def create_field_plate_mesh(device_name, L_fp, L_device=50.0, H_n=20.0, H_pplus=2.0, 
                            L_pplus=5.0, t_ox=0.2, t_fp=0.5):
    scale = 1e-4
    devsim.create_2d_mesh(mesh=device_name)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=-1e-8, ps=1e-8)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=0.0, ps=0.5*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_pplus*scale, ps=0.05*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=(L_pplus+L_fp)*scale, ps=0.1*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_device*scale, ps=0.5*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_device*scale+1e-8, ps=1e-8)
    devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=0.0, ps=0.5*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=H_pplus*scale, ps=0.05*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=H_n*scale, ps=0.1*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=(H_n+t_ox)*scale, ps=0.05*scale)
    devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=(H_n+t_ox+t_fp)*scale, ps=0.05*scale)
    devsim.add_2d_region(mesh=device_name, material="Si", region="pplus",
                         xl=0.0, xh=L_pplus*scale, yl=0.0, yh=H_pplus*scale)
    devsim.add_2d_region(mesh=device_name, material="Si", region="ndrift",
                         xl=L_pplus*scale, xh=L_device*scale, yl=0.0, yh=H_n*scale)
    devsim.add_2d_region(mesh=device_name, material="metal", region="fieldplate",
                         xl=0.0, xh=(L_pplus+L_fp)*scale, 
                         yl=(H_n+t_ox)*scale - 1e-9, yh=(H_n+t_ox+t_fp)*scale)
    devsim.add_2d_region(mesh=device_name, material="metal", region="air_left",
                         xl=-1e-8, xh=0.0, yl=0.0, yh=H_n*scale)
    devsim.add_2d_region(mesh=device_name, material="metal", region="air_right",
                         xl=L_device*scale, xh=L_device*scale+1e-8, yl=0.0, yh=H_n*scale)
    devsim.add_2d_interface(mesh=device_name, name="pplus_ndrift", 
                            region0="pplus", region1="ndrift",
                            xl=L_pplus*scale, xh=L_pplus*scale,
                            yl=0.0, yh=H_pplus*scale, bloat=1e-10)
    devsim.add_2d_contact(mesh=device_name, name="anode", material="metal", region="pplus",
                          yl=0.0, yh=0.0, xl=0.0, xh=L_pplus*scale, bloat=1e-10)
    devsim.add_2d_contact(mesh=device_name, name="cathode", material="metal", region="ndrift",
                          xl=L_device*scale, xh=L_device*scale, 
                          yl=0.0, yh=H_n*scale, bloat=1e-10)
    fp_y = (H_n + t_ox) * scale
    devsim.add_2d_contact(mesh=device_name, name="field_plate", material="metal", region="fieldplate",
                          yl=fp_y, yh=fp_y + 1e-10, 
                          xl=0.0, xh=(L_pplus+L_fp)*scale, bloat=1e-10)
    devsim.finalize_mesh(mesh=device_name)
    devsim.create_device(mesh=device_name, device=device_name)

print("="*70)
print("收敛性测试 - L=6.0μm，小步长0.25V")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode")
except:
    pass

create_field_plate_mesh("diode", 6.0)
print("✓ 网格创建完成")

SetSiliconParameters("diode", "pplus", 300)
SetSiliconParameters("diode", "ndrift", 300)
devsim.node_model(device="diode", region="pplus", name="Acceptors", equation="1e19")
devsim.node_model(device="diode", region="pplus", name="NetDoping", equation="Acceptors")
devsim.node_model(device="diode", region="ndrift", name="NetDoping", equation="1e14")
print("✓ 掺杂设置完成")

for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Potential")
    CreateSiliconPotentialOnly("diode", region)
devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)
CreateSiliconPotentialOnlyContact("diode", "ndrift", "cathode")
CreateSiliconPotentialOnlyContact("diode", "pplus", "anode")
interface_model_name = CreateContinuousInterfaceModel("diode", "pplus_ndrift", "Potential")
interface_equation(device="diode", interface="pplus_ndrift", name="PotentialEquation", 
                   interface_model=interface_model_name, type="continuous")
devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=100)
print("✓ 势求解收敛")

for region in ["pplus", "ndrift"]:
    CreateSolution("diode", region, "Electrons")
    CreateSolution("diode", region, "Holes")
    devsim.set_node_values(device="diode", region=region, name="Electrons", init_from="IntrinsicElectrons")
    devsim.set_node_values(device="diode", region=region, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion("diode", region)
CreateSiliconDriftDiffusionAtContact("diode", "pplus", "anode")
CreateSiliconDriftDiffusionAtContact("diode", "ndrift", "cathode")
devsim.solve(type="dc", absolute_error=1e15, relative_error=1e-4, maximum_iterations=200)
devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-6, maximum_iterations=200)
print("✓ 漂移扩散初始解收敛")

for region in ["pplus", "ndrift"]:
    devsim.edge_from_node_model(device="diode", region=region, node_model="Potential")
    devsim.edge_model(
        device="diode", region=region, name="ElectricField",
        equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
    )
print("✓ 电场模型创建完成")

# 小步长测试：0.25V步进，-0.5V到-5V
target_voltages = [-0.25*i for i in range(2, 21)]  # -0.5, -0.75, -1.0, ..., -5.0
print(f"\n开始电压扫描（{len(target_voltages)}个点，步长0.25V）...")
print("-"*70)

results = []
current_v = 0.0
converged_count = 0
failed_voltages = []

for target_v in target_voltages:
    print(f"\n电压: {target_v:.2f}V ", end='', flush=True)
    
    devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=target_v)
    devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)
    devsim.set_parameter(device="diode", name=GetContactBiasName("field_plate"), value=target_v)
    
    try:
        devsim.solve(type="dc", absolute_error=1e12, relative_error=1e-5, maximum_iterations=150)
        
        # 更新电场模型
        for region in ["pplus", "ndrift"]:
            devsim.edge_from_node_model(device="diode", region=region, node_model="Potential")
            try:
                devsim.delete_edge_model(device="diode", region=region, name="ElectricField")
            except:
                pass
            devsim.edge_model(
                device="diode", region=region, name="ElectricField",
                equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
            )
        
        current_v = target_v
        converged_count += 1
        
        # 提取数据
        try:
            e_current = devsim.get_contact_current(device="diode", contact="anode", 
                                                  equation="ElectronContinuityEquation")
            h_current = devsim.get_contact_current(device="diode", contact="anode", 
                                                  equation="HoleContinuityEquation")
            current = e_current + h_current
        except:
            current = 0
        
        E_field = devsim.get_edge_model_values(device="diode", region="ndrift", name="ElectricField")
        max_E = max(abs(x) for x in E_field) if E_field else 0
        
        results.append({"V": target_v, "I": current, "E": max_E})
        print(f"✓ Emax={max_E:.2e} V/cm, I={current:.2e}A")
        
    except Exception as e:
        print(f"✗ 收敛失败: {str(e)[:50]}")
        failed_voltages.append(target_v)
        break

print("\n" + "="*70)
print("测试总结:")
print(f"  成功收敛: {converged_count}/{len(target_voltages)} 个点")
print(f"  最高电压: {current_v}V")
if failed_voltages:
    print(f"  失败电压: {failed_voltages}")
print("\n电场变化趋势:")
for r in results[:5]:
    print(f"  V={r['V']:5.2f}V: E={r['E']:.2e} V/cm")
print("="*70)

# 保存结果
os.makedirs("data/test", exist_ok=True)
with open("data/test/convergence_test_L6.json", 'w') as f:
    json.dump({
        "L_fp": 6.0,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "converged_count": converged_count,
        "failed_voltages": failed_voltages
    }, f, indent=2)
print("\n结果已保存: data/test/convergence_test_L6.json")
