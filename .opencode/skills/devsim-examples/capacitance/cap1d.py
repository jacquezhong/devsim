# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
一维平板电容静电场仿真

能力标识: capacitance_1d_electrostatic

工作思路:
1. 创建一维网格，两端为金属接触
2. 定义介电常数（支持不同介质）
3. 建立泊松方程（仅电势）
4. 求解电势分布
5. 计算接触电荷和电容

能力边界:
- 支持1D静电场分析
- 仅泊松方程（无载流子输运）
- 可计算平板电容值
- 支持不同介质材料（通过介电常数）
"""

from devsim import (
    add_1d_contact,
    add_1d_mesh_line,
    add_1d_region,
    contact_equation,
    contact_node_model,
    create_1d_mesh,
    create_device,
    edge_from_node_model,
    edge_model,
    equation,
    finalize_mesh,
    get_contact_charge,
    node_solution,
    set_parameter,
    solve,
)


def run_capacitance_1d_simulation(
    device_name="MyDevice",
    region_name="MyRegion",
    # 结构参数
    device_length=1.0,  # cm
    mesh_spacing=0.1,   # cm
    # 材料参数
    permittivity=3.9 * 8.85e-14,  # SiO2默认 (F/cm)
    # 偏置参数
    contact1_bias=1.0,  # V
    contact2_bias=0.0,  # V
    # 求解器参数
    absolute_error=1.0,
    relative_error=1e-10,
    max_iterations=30,
    # 输出参数
    output_file=None,
):
    """
    运行一维电容静电场仿真
    
    参数:
        device_name: 器件名称
        region_name: 区域名称
        device_length: 器件长度 (cm)，默认1cm
        mesh_spacing: 网格间距 (cm)，默认0.1cm
        permittivity: 介电常数 (F/cm)，默认SiO2 (3.9*ε0)
        contact1_bias: 接触1偏置 (V)，默认1V
        contact2_bias: 接触2偏置 (V)，默认0V
        absolute_error: 绝对误差容限
        relative_error: 相对误差容限
        max_iterations: 最大迭代次数
        output_file: 输出文件名（可选）
    
    返回:
        dict: 包含电容值和电荷信息
    """
    
    result = {
        "device": device_name,
        "region": region_name,
        "parameters": {
            "device_length_cm": device_length,
            "permittivity_F_cm": permittivity,
            "contact1_bias_V": contact1_bias,
            "contact2_bias_V": contact2_bias,
        },
        "converged": True,
    }
    
    # 1. 创建1D网格
    create_1d_mesh(mesh="mesh1")
    add_1d_mesh_line(mesh="mesh1", pos=0.0, ps=mesh_spacing, tag="contact1")
    add_1d_mesh_line(mesh="mesh1", pos=device_length, ps=mesh_spacing, tag="contact2")
    add_1d_contact(mesh="mesh1", name="contact1", tag="contact1", material="metal")
    add_1d_contact(mesh="mesh1", name="contact2", tag="contact2", material="metal")
    add_1d_region(
        mesh="mesh1", material="Si", region=region_name, tag1="contact1", tag2="contact2"
    )
    finalize_mesh(mesh="mesh1")
    create_device(mesh="mesh1", device=device_name)
    
    # 2. 设置介电常数
    set_parameter(device=device_name, region=region_name, 
                 name="Permittivity", value=permittivity)
    
    # 3. 创建电势解变量
    node_solution(device=device_name, region=region_name, name="Potential")
    
    # 4. 创建边缘模型（电势差）
    edge_from_node_model(device=device_name, region=region_name, node_model="Potential")
    
    # 5. 电场模型
    edge_model(
        device=device_name,
        region=region_name,
        name="ElectricField",
        equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
    )
    edge_model(
        device=device_name,
        region=region_name,
        name="ElectricField:Potential@n0",
        equation="EdgeInverseLength",
    )
    edge_model(
        device=device_name,
        region=region_name,
        name="ElectricField:Potential@n1",
        equation="-EdgeInverseLength",
    )
    
    # 6. 电位移场模型
    edge_model(
        device=device_name, region=region_name, 
        name="DField", equation="Permittivity*ElectricField"
    )
    edge_model(
        device=device_name,
        region=region_name,
        name="DField:Potential@n0",
        equation="diff(Permittivity*ElectricField, Potential@n0)",
    )
    edge_model(
        device=device_name,
        region=region_name,
        name="DField:Potential@n1",
        equation="-DField:Potential@n0",
    )
    
    # 7. 创建体方程（泊松方程）
    equation(
        device=device_name,
        region=region_name,
        name="PotentialEquation",
        variable_name="Potential",
        edge_model="DField",
        variable_update="default",
    )
    
    # 8. 接触模型和方程
    for c in ("contact1", "contact2"):
        contact_node_model(
            device=device_name, contact=c, 
            name=f"{c}_bc", equation=f"Potential - {c}_bias"
        )
        contact_node_model(
            device=device_name, contact=c, 
            name=f"{c}_bc:Potential", equation="1"
        )
        contact_equation(
            device=device_name,
            contact=c,
            name="PotentialEquation",
            node_model=f"{c}_bc",
            edge_charge_model="DField",
        )
    
    # 9. 设置接触偏置
    set_parameter(device=device_name, region=region_name, 
                 name="contact1_bias", value=contact1_bias)
    set_parameter(device=device_name, region=region_name, 
                 name="contact2_bias", value=contact2_bias)
    
    # 10. 求解
    solve_info = solve(
        type="dc", 
        absolute_error=absolute_error, 
        relative_error=relative_error, 
        maximum_iterations=max_iterations
    )
    
    converged = True if solve_info is None else solve_info.get("converged", True)
    if not converged:
        result["converged"] = False
        result["error"] = "Solver did not converge"
        return result
    
    # 11. 计算接触电荷
    result["contact_charges"] = {}
    for c in ("contact1", "contact2"):
        charge = get_contact_charge(
            device=device_name, contact=c, equation="PotentialEquation"
        )
        result["contact_charges"][c] = charge
        print(f"contact: {c} charge: {charge:1.5e}")
    
    # 12. 计算电容
    voltage_diff = contact1_bias - contact2_bias
    if abs(voltage_diff) > 1e-10:
        cap = abs(result["contact_charges"]["contact1"]) / voltage_diff
        result["capacitance_F_cm2"] = cap  # 单位: F/cm^2
        print(f"\nCapacitance: {cap:.6e} F/cm^2")
    
    # 13. 输出结果
    if output_file:
        from devsim import write_devices
        write_devices(file=output_file, type="tecplot")
        result["output_file"] = output_file
    
    return result


if __name__ == "__main__":
    # 示例1: SiO2电容
    result = run_capacitance_1d_simulation(
        device_length=1e-4,  # 1um
        mesh_spacing=1e-5,   # 0.1um
        permittivity=3.9 * 8.85e-14,
        contact1_bias=1.0,
    )
    print(f"\n仿真完成: {result}")
    
    # 示例2: 真空电容
    # result = run_capacitance_1d_simulation(
    #     device_length=1.0,
    #     permittivity=8.85e-14,  # ε0
    #     contact1_bias=1.0,
    # )
