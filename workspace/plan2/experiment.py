#!/usr/bin/env python3
"""
Plan2: 亚微米级互连线寄生电容仿真
多导线（三线）结构电容提取实验
使用电容矩阵方法：C_ij = ∂Qi/∂Vj
"""

import sys
import os
import json
import numpy as np

sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

from devsim import (
    add_2d_contact, add_2d_mesh_line, add_2d_region,
    contact_equation, contact_node_model, create_2d_mesh, create_device,
    delete_device, delete_mesh, edge_from_node_model, edge_model,
    element_from_edge_model, equation, finalize_mesh, get_contact_charge,
    node_model, node_solution, set_parameter, solve, write_devices,
)


def create_three_wire_mesh(device_name, spacing, wire_width=0.2, wire_height=0.5,
                           domain_width=10.0, domain_height=5.0):
    """创建三线结构网格"""
    scale = 1e-4  # um to cm
    
    # 计算导线位置
    w1_x1 = domain_width/2 - spacing - wire_width - spacing/2
    w1_x2 = w1_x1 + wire_width
    w2_x1 = domain_width/2 - wire_width/2
    w2_x2 = w2_x1 + wire_width
    w3_x1 = domain_width/2 + spacing/2
    w3_x2 = w3_x1 + wire_width
    w_y1 = domain_height/2 - wire_height/2
    w_y2 = w_y1 + wire_height
    
    create_2d_mesh(mesh=device_name)
    
    # Y方向网格线
    add_2d_mesh_line(mesh=device_name, dir="y", pos=0.0, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=w_y1*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=w_y2*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=domain_height*scale, ps=0.5*scale)
    
    # X方向网格线
    add_2d_mesh_line(mesh=device_name, dir="x", pos=0.0, ps=0.5*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w1_x1*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w1_x2*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w2_x1*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w2_x2*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w3_x1*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=w3_x2*scale, ps=0.02*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=domain_width*scale, ps=0.5*scale)
    
    # 定义区域
    add_2d_region(mesh=device_name, material="gas", region="air",
                  yl=0.0, yh=domain_height*scale, xl=0.0, xh=domain_width*scale)
    
    for region_name, x1, x2 in [("wire_left", w1_x1, w1_x2),
                                 ("wire_center", w2_x1, w2_x2),
                                 ("wire_right", w3_x1, w3_x2)]:
        add_2d_region(mesh=device_name, material="metal", region=region_name,
                      yl=w_y1*scale, yh=w_y2*scale, xl=x1*scale, xh=x2*scale)
    
    # 定义接触
    for contact_name, x1, x2 in [("left", w1_x1, w1_x2),
                                   ("center", w2_x1, w2_x2),
                                   ("right", w3_x1, w3_x2)]:
        add_2d_contact(mesh=device_name, name=contact_name, region="air",
                       yl=w_y1*scale, yh=w_y2*scale, xl=x1*scale, xh=x2*scale,
                       material="metal")
    
    finalize_mesh(mesh=device_name)
    create_device(mesh=device_name, device=device_name)


def setup_and_solve(device_name, permittivity, biases):
    """设置参数并求解"""
    # 设置介电常数
    set_parameter(device=device_name, region="air", name="Permittivity", value=permittivity)
    
    # 创建电势变量和模型
    node_solution(device=device_name, region="air", name="Potential")
    edge_from_node_model(device=device_name, region="air", node_model="Potential")
    
    # 电场模型
    edge_model(device=device_name, region="air", name="ElectricField",
               equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")
    edge_model(device=device_name, region="air", name="ElectricField:Potential@n0",
               equation="EdgeInverseLength")
    edge_model(device=device_name, region="air", name="ElectricField:Potential@n1",
               equation="-EdgeInverseLength")
    
    # 电位移场
    edge_model(device=device_name, region="air", name="DField",
               equation="Permittivity*ElectricField")
    edge_model(device=device_name, region="air", name="DField:Potential@n0",
               equation="diff(Permittivity*ElectricField, Potential@n0)")
    edge_model(device=device_name, region="air", name="DField:Potential@n1",
               equation="-DField:Potential@n0")
    
    # 泊松方程
    equation(device=device_name, region="air", name="PotentialEquation",
             variable_name="Potential", edge_model="DField", variable_update="default")
    
    # 接触边界条件
    contacts = ["left", "center", "right"]
    for i, (c, bias) in enumerate(zip(contacts, biases)):
        contact_node_model(device=device_name, contact=c, name=f"{c}_bc",
                           equation=f"Potential - {bias}")
        contact_node_model(device=device_name, contact=c, name=f"{c}_bc:Potential", equation="1")
        contact_equation(device=device_name, contact=c, name="PotentialEquation",
                         node_model=f"{c}_bc", edge_charge_model="DField")
        set_parameter(device=device_name, name=f"{c}_bias", value=bias)
    
    # 固定金属区域电势
    for region, bias in [("wire_left", biases[0]), ("wire_center", biases[1]), ("wire_right", biases[2])]:
        node_model(device=device_name, region=region, name="Potential", equation=f"{bias};")
    
    # 求解
    solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30, solver_type="direct")
    
    # 提取电荷
    charges = []
    for c in contacts:
        q = get_contact_charge(device=device_name, contact=c, equation="PotentialEquation")
        charges.append(q)
    
    return charges


def extract_capacitance_matrix(device_name, permittivity):
    """
    使用有限差分法提取电容矩阵
    C_ij = ∂Qi/∂Vj ≈ ΔQi/ΔVj
    """
    contacts = ["left", "center", "right"]
    n = len(contacts)
    C_matrix = np.zeros((n, n))
    
    delta_V = 1.0  # 1V的电压变化
    
    # 对每个接触施加单位电压，其他接地
    for j in range(n):
        biases = [0.0, 0.0, 0.0]
        biases[j] = delta_V
        
        # 求解
        charges = setup_and_solve(device_name, permittivity, biases)
        
        # C_ij = Qi / Vj (当Vk=0, k≠j)
        for i in range(n):
            C_matrix[i, j] = charges[i] / delta_V
    
    return C_matrix


def run_three_wire_capacitance(spacing, permittivity):
    """运行三线电容仿真并提取电容矩阵"""
    device_name = f"ThreeWire_S{int(spacing*1000)}"
    
    # 清理
    try:
        delete_device(device=device_name)
        delete_mesh(mesh=device_name)
    except:
        pass
    
    # 创建网格
    create_three_wire_mesh(device_name, spacing)
    
    # 提取电容矩阵
    C_matrix = extract_capacitance_matrix(device_name, permittivity)
    
    # 计算等效电容
    # C_center_total = C_20 + C_21 + C_22 (自电容+互电容)
    C_center_total = abs(C_matrix[1, 0]) + abs(C_matrix[1, 1]) + abs(C_matrix[1, 2])
    
    # 耦合电容 (中心线与左右线的互电容)
    C_coupling = abs(C_matrix[1, 0]) + abs(C_matrix[1, 2])
    
    # 对地电容
    C_ground = abs(C_matrix[1, 1]) - C_coupling if abs(C_matrix[1, 1]) > C_coupling else 0.0
    
    # 耦合系数
    k_coupling = C_coupling / C_center_total if C_center_total > 0 else 0.0
    
    result = {
        "spacing_um": spacing,
        "permittivity": permittivity / 8.854e-14,  # 相对介电常数
        "C_matrix": C_matrix.tolist(),
        "C_center_total": C_center_total,
        "C_coupling": C_coupling,
        "C_ground": C_ground,
        "coupling_coefficient": k_coupling,
        "C_left": abs(C_matrix[1, 0]),
        "C_right": abs(C_matrix[1, 2]),
    }
    
    return result


def run_parameter_sweep():
    """执行参数扫描"""
    print("=" * 70)
    print("Plan2: 互连线寄生电容参数扫描实验")
    print("=" * 70)
    
    spacings = [0.2, 0.3, 0.4, 0.5]  # um: 200-500nm
    eps_values = [3.9, 2.5, 1.0]  # SiO2, Low-k, Air
    eps0 = 8.854e-14
    
    results = []
    
    for spacing in spacings:
        for eps_r in eps_values:
            spacing_nm = int(spacing * 1000)
            print(f"\n正在仿真: 间距={spacing_nm}nm, 介电常数εr={eps_r}")
            
            try:
                result = run_three_wire_capacitance(spacing, eps_r * eps0)
                result["spacing_nm"] = spacing_nm
                results.append(result)
                
                print(f"  C_total={result['C_center_total']:.3e} F/cm")
                print(f"  C_coupling={result['C_coupling']:.3e} F/cm")
                print(f"  C_ground={result['C_ground']:.3e} F/cm")
                print(f"  Coupling k={result['coupling_coefficient']:.3f}")
                
            except Exception as e:
                print(f"  仿真失败: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # 保存结果
    output_file = "/Users/lihengzhong/Documents/repo/devsim/workspace/plan2/data/final/capacitance_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"实验完成！共完成 {len(results)} 组仿真")
    print(f"结果保存到: {output_file}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    results = run_parameter_sweep()
