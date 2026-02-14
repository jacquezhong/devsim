# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
一维二极管瞬态响应仿真

能力标识: diode_1d_transient

工作思路:
1. 创建一维二极管网格（复用diode_1d的网格）
2. 设置DC工作点（0.7V偏置）
3. 使用时间积分方法（BDF1）求解瞬态响应
4. 记录电流随时间变化

能力边界:
- 支持1D硅基二极管瞬态分析
- 需要电路元件集成电流
- 支持电压阶跃响应
- 时间步长需要仔细选择以保证收敛
"""

import devsim
from devsim.python_packages.simple_physics import GetContactBiasName


def create_diode_mesh(device="MyDevice", region="MyRegion", 
                     junction_position=0.5e-5, device_length=1e-5):
    """创建一维二极管网格"""
    from devsim import (
        add_1d_contact, add_1d_mesh_line, add_1d_region,
        create_1d_mesh, create_device, finalize_mesh,
    )
    
    create_1d_mesh(mesh="dio")
    add_1d_mesh_line(mesh="dio", pos=0, ps=1e-7, tag="top")
    add_1d_mesh_line(mesh="dio", pos=junction_position, ps=1e-9, tag="mid")
    add_1d_mesh_line(mesh="dio", pos=device_length, ps=1e-7, tag="bot")
    add_1d_contact(mesh="dio", name="top", tag="top", material="metal")
    add_1d_contact(mesh="dio", name="bot", tag="bot", material="metal")
    add_1d_region(mesh="dio", material="Si", region=region, tag1="top", tag2="bot")
    finalize_mesh(mesh="dio")
    create_device(mesh="dio", device=device)


def set_doping(device, region, p_doping=1e18, n_doping=1e18, junction_position=0.5e-5):
    """设置掺杂分布"""
    from devsim.python_packages.model_create import CreateNodeModel
    CreateNodeModel(device, region, "Acceptors", f"{p_doping}*step({junction_position}-x)")
    CreateNodeModel(device, region, "Donors", f"{n_doping}*step(x-{junction_position})")
    CreateNodeModel(device, region, "NetDoping", "Donors-Acceptors")


def setup_initial_solution(device, region, circuit_contacts=None):
    """设置初始电势解"""
    from devsim import get_contact_list, set_parameter
    from devsim.python_packages.model_create import CreateSolution
    from devsim.python_packages.simple_physics import (
        CreateSiliconPotentialOnly, CreateSiliconPotentialOnlyContact, GetContactBiasName
    )
    
    CreateSolution(device, region, "Potential")
    CreateSiliconPotentialOnly(device, region)
    for contact in get_contact_list(device=device):
        if circuit_contacts and contact in circuit_contacts:
            CreateSiliconPotentialOnlyContact(device, region, contact, True)
        else:
            set_parameter(device=device, name=GetContactBiasName(contact), value=0.0)
            CreateSiliconPotentialOnlyContact(device, region, contact)


def setup_drift_diffusion(device, region, circuit_contacts=None):
    """设置漂移扩散方程"""
    from devsim import get_contact_list, set_node_values
    from devsim.python_packages.model_create import CreateSolution
    from devsim.python_packages.simple_physics import (
        CreateSiliconDriftDiffusion, CreateSiliconDriftDiffusionAtContact
    )
    
    CreateSolution(device, region, "Electrons")
    CreateSolution(device, region, "Holes")
    set_node_values(device=device, region=region, name="Electrons", init_from="IntrinsicElectrons")
    set_node_values(device=device, region=region, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(device, region)
    for contact in get_contact_list(device=device):
        if circuit_contacts and contact in circuit_contacts:
            CreateSiliconDriftDiffusionAtContact(device, region, contact, True)
        else:
            CreateSiliconDriftDiffusionAtContact(device, region, contact)


def run_transient_diode_simulation(
    device_name="MyDevice",
    region_name="MyRegion",
    # 结构参数
    device_length=1e-5,
    junction_position=0.5e-5,
    # 掺杂参数
    p_doping=1e18,
    n_doping=1e18,
    # 物理参数
    temperature=300,
    # DC偏置参数
    dc_voltage=0.7,
    # 瞬态参数
    time_step=1e-3,
    total_time=1e-2,
    # 输出参数
    print_solution=True,
):
    """
    运行一维二极管瞬态仿真
    
    参数:
        device_name: 器件名称
        region_name: 区域名称
        device_length: 器件长度 (cm)
        junction_position: 结位置 (cm)
        p_doping: p区掺杂 (cm^-3)
        n_doping: n区掺杂 (cm^-3)
        temperature: 温度 (K)
        dc_voltage: DC偏置电压 (V)
        time_step: 时间步长 (s)
        total_time: 总仿真时间 (s)
        print_solution: 是否打印电路解
    
    返回:
        dict: 包含时间点和对应的电路解
    """
    from devsim.python_packages.simple_physics import SetSiliconParameters
    
    result = {
        "device": device_name,
        "time_points": [],
        "converged": True,
    }
    
    # 启用扩展精度
    devsim.set_parameter(name="extended_solver", value=True)
    devsim.set_parameter(name="extended_model", value=True)
    devsim.set_parameter(name="extended_equation", value=True)
    
    # 创建电路元件
    devsim.circuit_element(
        name="V1",
        n1=GetContactBiasName("top"),
        n2=0,
        value=0.0,
        acreal=1.0,
        acimag=0.0,
    )
    
    # 创建网格和设置
    create_diode_mesh(device_name, region_name, junction_position, device_length)
    SetSiliconParameters(device_name, region_name, temperature)
    set_doping(device_name, region_name, p_doping, n_doping, junction_position)
    
    # 初始解
    setup_initial_solution(device_name, region_name, circuit_contacts="top")
    devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=30)
    
    setup_drift_diffusion(device_name, region_name, circuit_contacts=["top"])
    devsim.solve(type="transient_dc", absolute_error=1.0, relative_error=1e-14, 
                maximum_iterations=30)
    
    if print_solution:
        print("\nDC Solution:")
        for node in devsim.get_circuit_node_list():
            r = devsim.get_circuit_node_value(solution="dcop", node=node)
            print(f"{node}\t{r:.15e}")
    
    # 改变偏置
    devsim.circuit_alter(name="V1", value=dc_voltage)
    
    # 瞬态仿真
    current_time = 0.0
    while current_time < total_time:
        solve_info = devsim.solve(
            type="transient_bdf1",
            absolute_error=1e10,
            relative_error=1e-10,
            maximum_iterations=30,
            tdelta=time_step,
            charge_error=1,
        )
        
        converged = True if solve_info is None else solve_info.get("converged", True)
        if not converged:
            result["converged"] = False
            result["error"] = f"Solver did not converge at t={current_time}s"
            break
        
        if print_solution:
            print(f"\nt = {current_time:.4e} s")
            for node in devsim.get_circuit_node_list():
                r = devsim.get_circuit_node_value(solution="dcop", node=node)
                print(f"{node}\t{r:.15e}")
        
        result["time_points"].append({
            "time_s": current_time,
            "converged": True,
        })
        current_time += time_step
    
    return result


if __name__ == "__main__":
    result = run_transient_diode_simulation()
    print(f"\n瞬态仿真完成，时间点数: {len(result['time_points'])}")
