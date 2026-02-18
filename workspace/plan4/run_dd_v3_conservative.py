#!/usr/bin/env python3
"""
漂移扩散仿真 V3 - 保守收敛策略
针对高电压反向偏置的渐进式扫描方法
"""
import sys
import os
import json
from datetime import datetime

# 切换到脚本所在目录（确保能找到网格文件）
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

def solve_with_fallback(device, absolute_error, relative_error, max_iterations, 
                       min_step_factor=0.5, description=""):
    """
    尝试求解，如果失败则使用更宽松的容差重试
    
    参数:
        device: 器件名称
        absolute_error: 绝对误差
        relative_error: 相对误差
        max_iterations: 最大迭代次数
        min_step_factor: 失败后容差放宽倍数
        description: 求解描述（用于日志）
    
    返回:
        (success, solve_info): 是否成功，求解信息
    """
    # 第一次尝试：使用指定容差
    try:
        solve_info = devsim.solve(type="dc", absolute_error=absolute_error, 
                                 relative_error=relative_error, 
                                 maximum_iterations=max_iterations)
        converged = True if solve_info is None else solve_info.get("converged", True)
        if converged:
            return True, solve_info
    except Exception as e:
        pass
    
    # 第二次尝试：放宽容差
    print(f"      放宽容差重试...", end=' ')
    try:
        solve_info = devsim.solve(type="dc", 
                                 absolute_error=absolute_error*10, 
                                 relative_error=relative_error*10, 
                                 maximum_iterations=max_iterations)
        converged = True if solve_info is None else solve_info.get("converged", True)
        if converged:
            return True, solve_info
    except Exception as e:
        pass
    
    # 第三次尝试：更宽松的容差
    print(f"再次放宽容差...", end=' ')
    try:
        solve_info = devsim.solve(type="dc", 
                                 absolute_error=absolute_error*100, 
                                 relative_error=relative_error*100, 
                                 maximum_iterations=max_iterations*2)
        converged = True if solve_info is None else solve_info.get("converged", True)
        if converged:
            return True, solve_info
    except Exception as e:
        return False, None

def run_voltage_step(device, voltage, prev_voltage, step_count, max_retries=3):
    """
    运行单个电压步，包含失败重试机制
    
    参数:
        device: 器件名称
        voltage: 目标电压
        prev_voltage: 前一步电压（用于计算步长）
        step_count: 当前步数（用于日志）
        max_retries: 最大重试次数
    
    返回:
        (success, actual_voltage): 是否成功，实际达到的电压
    """
    voltage_gap = abs(voltage - prev_voltage)
    
    # 设置偏置
    devsim.set_parameter(device=device, name=GetContactBiasName("anode"), value=voltage)
    devsim.set_parameter(device=device, name=GetContactBiasName("cathode"), value=0.0)
    devsim.set_parameter(device=device, name=GetContactBiasName("field_plate"), value=voltage)
    
    print(f"    Step {step_count}: V={voltage}V (gap={voltage_gap}V)", end=' ')
    
    # 尝试求解
    success, solve_info = solve_with_fallback(
        device, 
        absolute_error=1e12, 
        relative_error=1e-6, 
        max_iterations=100,
        description=f"V={voltage}V"
    )
    
    if success:
        print("✓")
        # 重新创建边缘模型以更新电场
        for region in ["pplus", "ndrift"]:
            devsim.edge_from_node_model(device=device, region=region, node_model="Potential")
        return True, voltage
    else:
        print("✗")
        return False, prev_voltage

def extract_data(device, voltage):
    """
    提取当前电压点的数据
    
    参数:
        device: 器件名称
        voltage: 当前电压
    
    返回:
        dict: 包含电压、电流、电场的数据字典
    """
    try:
        # 获取电流
        e_current = devsim.get_contact_current(device=device, contact="anode", 
                                              equation="ElectronContinuityEquation")
        h_current = devsim.get_contact_current(device=device, contact="anode", 
                                              equation="HoleContinuityEquation")
        current = e_current + h_current
    except Exception as e:
        current = 0
    
    try:
        # 获取电场
        E_field = devsim.get_edge_model_values(device=device, region="ndrift", 
                                              name="ElectricField")
        max_E = max(abs(x) for x in E_field) if E_field else 0
    except Exception as e:
        max_E = 0
    
    return {
        "V": voltage,
        "I": current,
        "E": max_E
    }

# 场板长度列表
L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]

print("="*70)
print("漂移扩散仿真 V3 - 保守收敛策略")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

for L_fp in L_fp_values:
    print(f"\n{'='*70}")
    print(f"仿真场板长度 L_fp = {L_fp} μm")
    print(f"{'='*70}")
    
    mesh_file = f"fp_L{L_fp}.msh"
    result_file = f"data/final/devsim_dd_v3_results_L{L_fp}.json"
    
    # 检查是否已有结果
    if os.path.exists(result_file):
        print(f"✓ 结果已存在，跳过: {result_file}")
        with open(result_file, 'r') as f:
            data = json.load(f)
        print(f"  数据点: {data.get('n_points', 0)}")
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
    devsim.add_gmsh_contact(gmsh_name="field_plate", mesh="diode_mesh", name="field_plate", material="metal", region="ndrift")
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
    
    # 设置接触偏置
    devsim.set_parameter(device="diode", name=GetContactBiasName("anode"), value=0.0)
    devsim.set_parameter(device="diode", name=GetContactBiasName("cathode"), value=0.0)
    devsim.set_parameter(device="diode", name=GetContactBiasName("field_plate"), value=0.0)
    
    # 创建接触（注意顺序：必须先cathode，后anode）
    CreateSiliconPotentialOnlyContact("diode", "ndrift", "cathode")
    CreateSiliconPotentialOnlyContact("diode", "pplus", "anode")
    CreateSiliconPotentialOnlyContact("diode", "ndrift", "field_plate")
    
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
    
    # 创建漂移扩散边界
    for region in ["pplus", "ndrift"]:
        CreateSiliconDriftDiffusionAtContact("diode", region, "anode")
        CreateSiliconDriftDiffusionAtContact("diode", region, "cathode")
    
    # 求解漂移扩散（初始解）
    print("5. 求解漂移扩散初始解...")
    success, _ = solve_with_fallback("diode", 1e15, 1e-4, 200)
    if success:
        success, _ = solve_with_fallback("diode", 1e12, 1e-6, 200)
    if not success:
        print("   ✗ 初始解求解失败，跳过此场板长度")
        continue
    print("   ✓ 漂移扩散初始解收敛")
    
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
    
    # 渐进式电压扫描 - 保守策略
    print("7. 开始渐进式电压扫描...")
    print("   策略：从-0.5V开始，小步长逐步增加到-150V")
    
    # 目标电压点（渐进式）
    target_voltages = [
        -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0, -4.5, -5.0,  # 小步长启动
        -6.0, -7.0, -8.0, -9.0, -10.0,  # 1V步长
        -12.0, -14.0, -16.0, -18.0, -20.0,  # 2V步长
        -23.0, -26.0, -29.0, -32.0, -35.0,  # 3V步长
        -40.0, -45.0, -50.0, -55.0, -60.0,  # 5V步长
        -70.0, -80.0, -90.0, -100.0, -115.0, -130.0, -150.0  # 更大步长
    ]
    
    results = []
    current_v = 0.0
    step_count = 0
    
    for target_v in target_voltages:
        step_count += 1
        
        # 尝试达到目标电压
        success, reached_v = run_voltage_step("diode", target_v, current_v, step_count)
        
        if success:
            current_v = reached_v
            # 提取并记录数据
            data = extract_data("diode", current_v)
            results.append(data)
            print(f"      ✓ 记录: V={current_v}V, I={data['I']:.2e}A, Emax={data['E']:.2e}V/cm")
        else:
            # 失败：尝试中间电压
            mid_v = (current_v + target_v) / 2
            if abs(mid_v - current_v) > 0.1:  # 只有当差距足够大时才尝试
                print(f"    尝试中间电压 V={mid_v}V...", end=' ')
                success, reached_v = run_voltage_step("diode", mid_v, current_v, f"{step_count}a")
                if success:
                    current_v = reached_v
                    data = extract_data("diode", current_v)
                    results.append(data)
                    print(f"✓")
                    print(f"      ✓ 记录: V={current_v}V, I={data['I']:.2e}A, Emax={data['E']:.2e}V/cm")
                    
                    # 再次尝试原目标
                    success2, reached_v2 = run_voltage_step("diode", target_v, current_v, f"{step_count}b")
                    if success2:
                        current_v = reached_v2
                        data = extract_data("diode", current_v)
                        results.append(data)
                        print(f"      ✓ 记录: V={current_v}V, I={data['I']:.2e}A, Emax={data['E']:.2e}V/cm")
                else:
                    print("✗")
                    print(f"      ⚠ 无法收敛，停止扫描。最高电压: {current_v}V")
                    break
            else:
                print(f"      ⚠ 步长过小，停止扫描。最高电压: {current_v}V")
                break
    
    # 保存结果
    print(f"\n8. 保存结果...")
    os.makedirs("data/final", exist_ok=True)
    
    result_data = {
        "L_fp": L_fp,
        "timestamp": datetime.now().isoformat(),
        "method": "conservative_step_v3",
        "voltages": [r["V"] for r in results],
        "currents": [r["I"] for r in results],
        "max_electric_fields": [r["E"] for r in results],
        "n_points": len(results),
        "max_voltage": current_v
    }
    
    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"   ✓ 结果已保存: {result_file}")
    print(f"   完成点数: {len(results)}/{len(target_voltages)}")
    print(f"   最高电压: {current_v}V")
    
    # 清理
    devsim.delete_device(device="diode")
    devsim.delete_mesh(mesh="diode_mesh")

# 合并所有结果
print("\n" + "="*70)
print("收集所有结果...")
all_results = []
for L_fp in L_fp_values:
    result_file = f"data/final/devsim_dd_v3_results_L{L_fp}.json"
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            data = json.load(f)
        all_results.append(data)
        print(f"  ✓ L={L_fp}μm: {data.get('n_points', 0)} 点, 最高 {data.get('max_voltage', 0)}V")

with open("data/final/devsim_all_v3_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "description": "DEVSIM DD simulation with conservative step strategy",
        "results": all_results
    }, f, indent=2)

print(f"\n✓ 所有结果已保存: data/final/devsim_all_v3_results.json")
print("="*70)
