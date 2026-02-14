# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
二维平板电容静电场仿真

能力标识: capacitance_2d_electrostatic

工作思路:
1. 创建二维网格，包含金属电极和介质区域
2. 在电极边缘加密网格以捕捉边缘电场
3. 建立泊松方程求解电势分布
4. 计算接触电荷（包含边缘效应）
5. 输出电势和电场分布

能力边界:
- 支持2D静电场分析
- 包含边缘电场效应（寄生电容）
- 可模拟非对称电极结构
- 仅泊松方程（无载流子输运）
"""

from devsim import (
    add_2d_contact,
    add_2d_mesh_line,
    add_2d_region,
    contact_equation,
    contact_node_model,
    create_2d_mesh,
    create_device,
    edge_from_node_model,
    edge_model,
    element_from_edge_model,
    equation,
    finalize_mesh,
    get_contact_charge,
    node_model,
    node_solution,
    set_parameter,
    solve,
    write_devices,
)


def run_capacitance_2d_simulation(
    device_name="MyDevice",
    air_region="air",
    # 几何参数
    xmin=-25.0, x1=-24.975, x2=-2.0, x3=2.0, x4=24.975, xmax=25.0,  # x坐标 (um)
    ymin=0.0, y1=0.1, y2=0.2, y3=0.8, y4=0.9, ymax=50.0,  # y坐标 (um)
    # 材料参数
    permittivity=3.9 * 8.85e-14,  # SiO2 (F/cm)
    # 偏置参数
    top_bias=1.0,   # V
    bot_bias=0.0,   # V
    # 求解器参数
    absolute_error=1.0,
    relative_error=1e-10,
    max_iterations=30,
    # 输出参数
    output_mesh_file="cap2d.msh",
    output_data_file="cap2d.dat",
):
    """
    运行二维电容静电场仿真
    
    参数:
        device_name: 器件名称
        air_region: 空气区域名称
        xmin, x1, x2, x3, x4, xmax: x方向位置 (um)
        ymin, y1, y2, y3, y4, ymax: y方向位置 (um)
        permittivity: 介电常数 (F/cm)
        top_bias: 上电极偏置 (V)
        bot_bias: 下电极偏置 (V)
        absolute_error: 绝对误差容限
        relative_error: 相对误差容限
        max_iterations: 最大迭代次数
        output_mesh_file: 网格输出文件
        output_data_file: 数据输出文件
    
    返回:
        dict: 包含电容值和电荷信息
    """
    
    result = {
        "device": device_name,
        "parameters": {
            "top_bias_V": top_bias,
            "bot_bias_V": bot_bias,
            "permittivity_F_cm": permittivity,
        },
        "converged": True,
    }
    
    # 单位转换: um -> cm
    scale = 1e-4
    
    # 1. 创建2D网格
    create_2d_mesh(mesh=device_name)
    
    # y方向网格线
    add_2d_mesh_line(mesh=device_name, dir="y", pos=ymin*scale, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=y1*scale, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=y2*scale, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=y3*scale, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=y4*scale, ps=0.1*scale)
    add_2d_mesh_line(mesh=device_name, dir="y", pos=ymax*scale, ps=5.0*scale)
    
    # x方向网格线
    add_2d_mesh_line(mesh=device_name, dir="x", pos=xmin*scale, ps=5*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=x1*scale, ps=2*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=x2*scale, ps=0.05*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=x3*scale, ps=0.05*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=x4*scale, ps=2*scale)
    add_2d_mesh_line(mesh=device_name, dir="x", pos=xmax*scale, ps=5*scale)
    
    # 定义区域
    add_2d_region(
        mesh=device_name, material="gas", region=air_region,
        yl=ymin*scale, yh=ymax*scale, xl=xmin*scale, xh=xmax*scale
    )
    add_2d_region(
        mesh=device_name, material="metal", region="m1",
        yl=y1*scale, yh=y2*scale, xl=x1*scale, xh=x4*scale
    )
    add_2d_region(
        mesh=device_name, material="metal", region="m2",
        yl=y3*scale, yh=y4*scale, xl=x2*scale, xh=x3*scale
    )
    
    # 定义接触
    add_2d_contact(
        mesh=device_name, name="bot", region=air_region,
        yl=y1*scale, yh=y2*scale, xl=x1*scale, xh=x4*scale, material="metal"
    )
    add_2d_contact(
        mesh=device_name, name="top", region=air_region,
        yl=y3*scale, yh=y4*scale, xl=x2*scale, xh=x3*scale, material="metal"
    )
    
    finalize_mesh(mesh=device_name)
    create_device(mesh=device_name, device=device_name)
    
    # 2. 设置介电常数
    set_parameter(device=device_name, region=air_region, 
                 name="Permittivity", value=permittivity)
    
    # 3. 创建电势解变量
    node_solution(device=device_name, region=air_region, name="Potential")
    
    # 4. 创建边缘模型
    edge_from_node_model(device=device_name, region=air_region, node_model="Potential")
    
    # 5. 电场模型
    edge_model(
        device=device_name,
        region=air_region,
        name="ElectricField",
        equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
    )
    edge_model(
        device=device_name,
        region=air_region,
        name="ElectricField:Potential@n0",
        equation="EdgeInverseLength",
    )
    edge_model(
        device=device_name,
        region=air_region,
        name="ElectricField:Potential@n1",
        equation="-EdgeInverseLength",
    )
    
    # 6. 电位移场模型
    edge_model(
        device=device_name, region=air_region, 
        name="DField", equation="Permittivity*ElectricField"
    )
    edge_model(
        device=device_name,
        region=air_region,
        name="DField:Potential@n0",
        equation="diff(Permittivity*ElectricField, Potential@n0)",
    )
    edge_model(
        device=device_name,
        region=air_region,
        name="DField:Potential@n1",
        equation="-DField:Potential@n0",
    )
    
    # 7. 创建体方程
    equation(
        device=device_name,
        region=air_region,
        name="PotentialEquation",
        variable_name="Potential",
        edge_model="DField",
        variable_update="default",
    )
    
    # 8. 接触模型和方程
    for c in ("top", "bot"):
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
    
    # 9. 设置偏置
    set_parameter(device=device_name, name="top_bias", value=top_bias)
    set_parameter(device=device_name, name="bot_bias", value=bot_bias)
    
    # 10. 金属区域电势固定
    edge_model(device=device_name, region="m1", name="ElectricField", equation="0")
    edge_model(device=device_name, region="m2", name="ElectricField", equation="0")
    node_model(device=device_name, region="m1", name="Potential", equation="bot_bias;")
    node_model(device=device_name, region="m2", name="Potential", equation="top_bias;")
    
    # 11. 求解
    solve_info = solve(
        type="dc",
        absolute_error=absolute_error,
        relative_error=relative_error,
        maximum_iterations=max_iterations,
        solver_type="direct",
    )
    
    if not solve_info.get("converged", True):
        result["converged"] = False
        result["error"] = "Solver did not converge"
        return result
    
    # 12. 计算单元电场
    element_from_edge_model(edge_model="ElectricField", device=device_name, region=air_region)
    
    # 13. 打印接触电荷
    result["contact_charges"] = {}
    for c in ("top", "bot"):
        charge = get_contact_charge(device=device_name, contact=c, equation="PotentialEquation")
        result["contact_charges"][c] = charge
        print(charge)
    
    # 14. 输出结果
    write_devices(file=output_mesh_file, type="devsim")
    write_devices(file=output_data_file, type="tecplot")
    write_devices(file=output_data_file.replace(".dat", ""), type="vtk")
    
    result["output_files"] = [output_mesh_file, output_data_file]
    
    return result


if __name__ == "__main__":
    result = run_capacitance_2d_simulation()
    print(f"\n2D电容仿真完成: {result}")
