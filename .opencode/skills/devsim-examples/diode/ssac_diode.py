# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
一维二极管小信号AC分析仿真

能力标识: diode_1d_ssac_cv

工作思路:
1. 创建一维二极管并求解DC工作点
2. 在不同偏置点进行小信号AC分析
3. 计算电容-电压(C-V)特性
4. 基于电路节点电流虚部计算电容

能力边界:
- 支持1D硅基二极管AC分析
- 需要电路元件集成电流
- 固定频率（默认1Hz）
- 可提取耗尽电容和扩散电容
"""

import math
import devsim
from devsim import circuit_alter, circuit_element, solve
from devsim.python_packages.simple_physics import GetContactBiasName, PrintCurrents


def create_diode_mesh(device="MyDevice", region="MyRegion",
                     junction_position=0.5e-5, device_length=1e-5):
    """创建一维二极管网格"""
    from devsim import (
        add_1d_contact, add_1d_mesh_line, add_1d_region,
        create_1d_mesh, create_device, finalize_mesh,
    )
    
    create_1d_mesh(mesh="dio")
    add_1d_mesh_line(mesh="dio", pos=0, ps=1e-7, tag="top")
    add_1d_mesh_line(mesh="dio", pos=junction_position, ps=1e-8, tag="mid")
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


def run_ssac_diode_simulation(
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
    # 扫描参数
    start_voltage=0.0,
    max_voltage=0.5,
    voltage_step=0.1,
    # AC参数
    frequency=1.0,  # Hz
    # 输出参数
    print_cv=True,
):
    """
    运行一维二极管小信号AC仿真
    
    参数:
        device_name: 器件名称
        region_name: 区域名称
        device_length: 器件长度 (cm)
        junction_position: 结位置 (cm)
        p_doping: p区掺杂 (cm^-3)
        n_doping: n区掺杂 (cm^-3)
        temperature: 温度 (K)
        start_voltage: 起始偏置 (V)
        max_voltage: 最大偏置 (V)
        voltage_step: 偏置步长 (V)
        frequency: AC频率 (Hz)
        print_cv: 是否打印C-V数据
    
    返回:
        dict: 包含C-V曲线数据
    """
    from devsim.python_packages.simple_physics import SetSiliconParameters
    from devsim import get_circuit_node_value
    
    result = {
        "device": device_name,
        "frequency_Hz": frequency,
        "cv_data": [],
        "converged": True,
    }
    
    # 创建电路元件
    circuit_element(
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
    solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=30)
    
    # 漂移扩散
    setup_drift_diffusion(device_name, region_name, circuit_contacts=["top"])
    
    # DC扫描和AC分析
    v = start_voltage
    while v <= max_voltage + voltage_step/2:
        circuit_alter(name="V1", value=v)
        solve_info = solve(type="dc", absolute_error=1e10, relative_error=1e-10, 
                          maximum_iterations=30)
        
        converged = True if solve_info is None else solve_info.get("converged", True)
        if not converged:
            result["converged"] = False
            result["error"] = f"DC solver did not converge at V={v}V"
            break
        
        PrintCurrents(device_name, "bot")
        
        # AC小信号分析
        solve(type="ac", frequency=frequency)
        
        # 计算电容：I_imag = jωCV  =>  C = I_imag / (2πf V)
        current_imag = get_circuit_node_value(node="V1.I", solution="ssac_imag")
        cap = current_imag / (-2 * math.pi * frequency)
        
        if print_cv:
            print(f"capacitance {v:.1f} {cap:.6e}")
        
        result["cv_data"].append({
            "voltage_V": v,
            "capacitance_F": cap,
        })
        
        v += voltage_step
    
    return result


if __name__ == "__main__":
    result = run_ssac_diode_simulation()
    print(f"\nAC仿真完成，C-V数据点数: {len(result['cv_data'])}")
