# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
二维MOS结构迁移率模型仿真

能力标识: mos_2d_gmsh_mobility

工作思路:
1. 导入Gmsh生成的2D MOS网格
2. 设置栅氧和硅区域的电势
3. 求解初始电势分布
4. 加入电子/空穴连续性方程
5. 栅压扫描观察反型层形成
6. 漏压扫描获得IV特性

能力边界:
- 需要预生成的Gmsh网格文件
- 支持2D MOS结构
- 包含迁移率模型
- 支持栅压和漏压扫描

依赖:
- gmsh_mos2d.msh 网格文件
- gmsh_mos2d_create 模块（网格定义）
"""

import devsim
from devsim.python_packages.simple_physics import (
    GetContactBiasName,
    SetOxideParameters,
    SetSiliconParameters,
    CreateSiliconPotentialOnly,
    CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion,
    CreateSiliconDriftDiffusionAtContact,
    CreateOxidePotentialOnly,
    CreateSiliconOxideInterface,
)
from devsim.python_packages.ramp import rampbias, printAllCurrents
from devsim.python_packages.model_create import CreateSolution


def run_mos_2d_mobility_simulation(
    device_name="mos2d",
    # 区域定义
    silicon_regions=("gate", "bulk"),
    oxide_regions=("oxide",),
    interfaces=("bulk_oxide", "gate_oxide"),
    # 物理参数
    temperature=300,  # K
    # 栅压扫描
    gate_bias_start=0.0,
    gate_bias_stop=0.5,
    gate_bias_step=0.05,
    # 漏压扫描
    drain_bias_start=0.0,
    drain_bias_stop=0.5,
    drain_bias_step=0.1,
    # 求解器参数
    absolute_error_potential=1.0e-13,
    relative_error_potential=1e-12,
    absolute_error_dd=1.0e30,
    relative_error_dd=1e-5,
    max_iterations=30,
    # 输出参数
    output_potential_file="gmsh_mos2d_potentialonly",
    output_dd_file="gmsh_mos2d_dd.dat",
):
    """
    运行2D MOS迁移率模型仿真
    
    参数:
        device_name: 器件名称
        silicon_regions: 硅区域名称元组
        oxide_regions: 氧化层区域名称元组
        interfaces: 界面名称元组
        temperature: 温度 (K)
        gate_bias_start: 栅压起始值 (V)
        gate_bias_stop: 栅压终止值 (V)
        gate_bias_step: 栅压步长 (V)
        drain_bias_start: 漏压起始值 (V)
        drain_bias_stop: 漏压终止值 (V)
        drain_bias_step: 漏压步长 (V)
        absolute_error_potential: 电势求解绝对误差
        relative_error_potential: 电势求解相对误差
        absolute_error_dd: 漂移扩散求解绝对误差
        relative_error_dd: 漂移扩散求解相对误差
        max_iterations: 最大迭代次数
        output_potential_file: 电势解输出文件
        output_dd_file: 漂移扩散解输出文件
    
    返回:
        dict: 仿真结果和状态
    """
    
    result = {
        "device": device_name,
        "temperature_K": temperature,
        "converged": True,
        "bias_points": [],
    }
    
    regions = silicon_regions + oxide_regions
    
    # 1. 创建电势解变量
    for region in regions:
        CreateSolution(device_name, region, "Potential")
    
    # 2. 设置硅区域参数和模型
    for region in silicon_regions:
        SetSiliconParameters(device_name, region, temperature)
        CreateSiliconPotentialOnly(device_name, region)
    
    # 3. 设置氧化层参数和模型
    for region in oxide_regions:
        SetOxideParameters(device_name, region, temperature)
        CreateOxidePotentialOnly(device_name, region, "log_damp")
    
    # 4. 设置接触
    contacts = devsim.get_contact_list(device=device_name)
    for contact in contacts:
        tmp = devsim.get_region_list(device=device_name, contact=contact)
        region = tmp[0]
        print(f"{region} {contact}")
        CreateSiliconPotentialOnlyContact(device_name, region, contact)
        devsim.set_parameter(device=device_name, 
                            name=GetContactBiasName(contact), value=0.0)
    
    # 5. 设置界面
    for interface in interfaces:
        CreateSiliconOxideInterface(device_name, interface)
    
    # 6. 求解电势
    for _ in range(2):
        solve_info = devsim.solve(
            type="dc",
            absolute_error=absolute_error_potential,
            relative_error=relative_error_potential,
            maximum_iterations=max_iterations,
        )
        if not solve_info.get("converged", True):
            result["converged"] = False
            result["error"] = "Potential solve did not converge"
            return result
    
    devsim.write_devices(file=output_potential_file, type="vtk")
    
    # 7. 设置漂移扩散
    for region in silicon_regions:
        CreateSolution(device_name, region, "Electrons")
        CreateSolution(device_name, region, "Holes")
        devsim.set_node_values(
            device=device_name, region=region, 
            name="Electrons", init_from="IntrinsicElectrons"
        )
        devsim.set_node_values(
            device=device_name, region=region, 
            name="Holes", init_from="IntrinsicHoles"
        )
        CreateSiliconDriftDiffusion(device_name, region, "mu_n", "mu_p")
    
    for contact in contacts:
        tmp = devsim.get_region_list(device=device_name, contact=contact)
        region = tmp[0]
        CreateSiliconDriftDiffusionAtContact(device_name, region, contact)
    
    # 8. 漂移扩散初始解
    solve_info = devsim.solve(
        type="dc",
        absolute_error=absolute_error_dd,
        relative_error=relative_error_dd,
        maximum_iterations=max_iterations,
    )
    if not solve_info.get("converged", True):
        result["converged"] = False
        result["error"] = "Initial DD solve did not converge"
        return result
    
    # 9. 创建后处理模型
    for region in silicon_regions:
        devsim.node_model(
            device=device_name, region=region,
            name="logElectrons", equation="log(Electrons)/log(10)"
        )
        devsim.element_from_edge_model(edge_model="ElectricField", 
                                       device=device_name, region=region)
        devsim.element_from_edge_model(edge_model="ElectronCurrent", 
                                       device=device_name, region=region)
        devsim.element_from_edge_model(edge_model="HoleCurrent", 
                                       device=device_name, region=region)
    
    # 10. 栅压扫描
    print("\n=== Gate Bias Ramp ===")
    rampbias(
        device_name, "gate",
        gate_bias_stop, gate_bias_step, 0.001, 100,
        1e-10, 1e30, printAllCurrents
    )
    
    # 11. 漏压扫描
    print("\n=== Drain Bias Ramp ===")
    rampbias(
        device_name, "drain",
        drain_bias_stop, drain_bias_step, 0.001, 100,
        1e-10, 1e30, printAllCurrents
    )
    
    # 12. 输出结果
    devsim.write_devices(file=output_dd_file, type="tecplot")
    result["output_file"] = output_dd_file
    
    return result


if __name__ == "__main__":
    # 注意：运行前需要确保 gmsh_mos2d.msh 文件存在
    try:
        result = run_mos_2d_mobility_simulation()
        print(f"\nMOS仿真完成: {result}")
    except Exception as e:
        print(f"错误: 需要Gmsh网格文件。错误信息: {e}")
        print("提示: 先运行 gmsh_mos2d_create.py 生成网格")
