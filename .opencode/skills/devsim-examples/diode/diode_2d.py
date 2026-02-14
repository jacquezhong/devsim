# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
二维PN结二极管DC IV特性仿真

能力标识: diode_2d_dc_iv

工作思路:
1. 创建二维网格，包含器件区域和空气区域
2. 在结区附近进行网格加密
3. 设置硅材料参数和阶跃掺杂
4. 求解泊松方程获得初始电势分布
5. 加入漂移扩散方程求解载流子
6. 扫描偏置并输出各接触电流

能力边界:
- 支持2D硅基PN结二极管
- 简单矩形几何结构
- 漂移扩散输运模型
- 可查看2D电势和电流分布
"""

from devsim import set_parameter, solve
from devsim.python_packages.simple_physics import GetContactBiasName, PrintCurrents


def create_diode_2d_mesh(device="MyDevice", region="MyRegion",
                         device_width=1e-5, device_height=1e-5,
                         junction_x=0.5e-5, mesh_density=1e-8):
    """
    创建二维二极管网格
    
    参数:
        device: 器件名称
        region: 区域名称
        device_width: 器件宽度 (cm)，默认10μm
        device_height: 器件高度 (cm)，默认10μm
        junction_x: 结位置x坐标 (cm)，默认5μm
        mesh_density: 结区网格密度 (cm)，默认0.1μm
    """
    from devsim import (
        add_2d_contact,
        add_2d_mesh_line,
        add_2d_region,
        create_2d_mesh,
        create_device,
        finalize_mesh,
    )
    
    create_2d_mesh(mesh=device)
    
    # x方向网格线
    add_2d_mesh_line(mesh=device, dir="x", pos=0, ps=1e-6)
    add_2d_mesh_line(mesh=device, dir="x", pos=junction_x, ps=mesh_density)
    add_2d_mesh_line(mesh=device, dir="x", pos=device_width, ps=1e-6)
    
    # 边界扩展（用于接触定义）
    add_2d_mesh_line(mesh=device, dir="x", pos=-1e-8, ps=1e-8)
    add_2d_mesh_line(mesh=device, dir="x", pos=device_width+1e-8, ps=1e-8)
    
    # y方向网格线
    add_2d_mesh_line(mesh=device, dir="y", pos=0, ps=1e-6)
    add_2d_mesh_line(mesh=device, dir="y", pos=device_height, ps=1e-6)
    
    # 定义区域
    add_2d_region(mesh=device, material="Si", region=region)
    add_2d_region(mesh=device, material="Si", region="air1", xl=-1e-8, xh=0)
    add_2d_region(mesh=device, material="Si", region="air2", 
                  xl=device_width, xh=device_width+1e-8)
    
    # 定义接触
    contact_y_start = device_height * 0.8
    add_2d_contact(
        mesh=device, name="top", material="metal", region=region,
        yl=contact_y_start, yh=device_height, xl=0, xh=0, bloat=1e-10
    )
    add_2d_contact(
        mesh=device, name="bot", material="metal", region=region,
        xl=device_width, xh=device_width, yl=0, yh=device_height, bloat=1e-10
    )
    
    finalize_mesh(mesh=device)
    create_device(mesh=device, device=device)


def set_doping_profile_2d(device, region, p_doping=1e18, n_doping=1e18, junction_x=0.5e-5):
    """
    设置2D掺杂分布
    
    参数:
        device: 器件名称
        region: 区域名称
        p_doping: p区掺杂浓度 (cm^-3)
        n_doping: n区掺杂浓度 (cm^-3)
        junction_x: 结位置x坐标 (cm)
    """
    from devsim.python_packages.model_create import CreateNodeModel
    
    CreateNodeModel(device, region, "Acceptors", f"{p_doping}*step({junction_x}-x)")
    CreateNodeModel(device, region, "Donors", f"{n_doping}*step(x-{junction_x})")
    CreateNodeModel(device, region, "NetDoping", "Donors-Acceptors")


def run_diode_2d_simulation(
    device_name="MyDevice",
    region_name="MyRegion",
    # 结构参数
    device_width=1e-5,
    device_height=1e-5,
    junction_x=0.5e-5,
    mesh_density=1e-8,
    # 掺杂参数
    p_doping=1e18,
    n_doping=1e18,
    # 物理参数
    temperature=300,
    # 偏置参数
    start_voltage=0.0,
    max_voltage=0.5,
    voltage_step=0.1,
    # 求解器参数
    absolute_error=1e10,
    relative_error=1e-10,
    max_iterations=30,
    # 输出参数
    output_file="diode_2d.dat",
):
    """
    运行二维二极管DC IV仿真
    
    参数:
        device_name: 器件名称
        region_name: 区域名称
        device_width: 器件宽度 (cm)
        device_height: 器件高度 (cm)
        junction_x: 结位置x坐标 (cm)
        mesh_density: 结区网格密度 (cm)
        p_doping: p区掺杂浓度 (cm^-3)
        n_doping: n区掺杂浓度 (cm^-3)
        temperature: 温度 (K)
        start_voltage: 起始偏置 (V)
        max_voltage: 最大偏置 (V)
        voltage_step: 偏置步长 (V)
        absolute_error: 绝对误差容限
        relative_error: 相对误差容限
        max_iterations: 最大迭代次数
        output_file: 输出文件名
    
    返回:
        dict: 仿真结果
    """
    from devsim.python_packages.simple_physics import SetSiliconParameters
    from devsim.python_packages.model_create import CreateSolution
    from devsim.python_packages.simple_physics import (
        CreateSiliconPotentialOnly,
        CreateSiliconPotentialOnlyContact,
        CreateSiliconDriftDiffusion,
        CreateSiliconDriftDiffusionAtContact,
    )
    from devsim import get_contact_list, set_node_values, write_devices
    
    result = {
        "device": device_name,
        "region": region_name,
        "parameters": {
            "device_width_cm": device_width,
            "device_height_cm": device_height,
            "junction_x_cm": junction_x,
            "p_doping_cm3": p_doping,
            "n_doping_cm3": n_doping,
            "temperature_K": temperature,
        },
        "bias_points": [],
        "converged": True,
    }
    
    # 创建网格
    create_diode_2d_mesh(device_name, region_name, device_width, 
                        device_height, junction_x, mesh_density)
    
    # 设置参数
    SetSiliconParameters(device_name, region_name, temperature)
    set_doping_profile_2d(device_name, region_name, p_doping, n_doping, junction_x)
    
    # 初始解
    CreateSolution(device_name, region_name, "Potential")
    CreateSiliconPotentialOnly(device_name, region_name)
    for contact in get_contact_list(device=device_name):
        set_parameter(device=device_name, name=GetContactBiasName(contact), value=0.0)
        CreateSiliconPotentialOnlyContact(device_name, region_name, contact)
    
    solve(type="dc", absolute_error=1.0, relative_error=1e-12, 
          maximum_iterations=max_iterations)
    
    # 漂移扩散
    CreateSolution(device_name, region_name, "Electrons")
    CreateSolution(device_name, region_name, "Holes")
    set_node_values(device=device_name, region=region_name, 
                   name="Electrons", init_from="IntrinsicElectrons")
    set_node_values(device=device_name, region=region_name, 
                   name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(device_name, region_name)
    for contact in get_contact_list(device=device_name):
        CreateSiliconDriftDiffusionAtContact(device_name, region_name, contact)
    
    solve(type="dc", absolute_error=absolute_error, relative_error=relative_error,
          maximum_iterations=max_iterations)
    
    # 偏置扫描
    v = start_voltage
    while v <= max_voltage + voltage_step/2:
        set_parameter(device=device_name, name=GetContactBiasName("top"), value=v)
        solve_info = solve(type="dc", absolute_error=absolute_error,
                          relative_error=relative_error,
                          maximum_iterations=max_iterations)
        
        converged = True if solve_info is None else solve_info.get("converged", True)
        if not converged:
            result["converged"] = False
            result["error"] = f"Solver did not converge at V={v}V"
            break
        
        PrintCurrents(device_name, "top")
        PrintCurrents(device_name, "bot")
        
        result["bias_points"].append({"voltage_V": v, "converged": True})
        v += voltage_step
    
    # 输出结果
    write_devices(file=output_file, type="tecplot")
    result["output_file"] = output_file
    
    return result


if __name__ == "__main__":
    result = run_diode_2d_simulation()
    print(f"\n仿真完成: {result}")
