# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
一维PN结二极管DC IV特性仿真

能力标识: diode_1d_dc_iv

工作思路:
1. 创建一维网格，结区附近加密
2. 设置硅材料参数（温度相关）
3. 定义阶跃掺杂分布（p区和n区）
4. 先求解泊松方程获得初始电势
5. 加入电子/空穴连续性方程
6. 从0V开始扫描偏置至目标电压
7. 输出各偏置点的电流

能力边界:
- 支持1D硅基PN结二极管
- 漂移扩散输运模型
- SRH复合（可通过参数控制）
- 温度范围: 250K-400K（硅参数有效范围）
- 偏置范围: -1V至1V（默认），可扩展
"""

from devsim import (
    print_node_values,
    set_parameter,
    solve,
    write_devices,
)

import devsim.python_packages.simple_physics as simple_physics


def create_diode_mesh(device="MyDevice", region="MyRegion", junction_position=0.5e-5,
                      device_length=1e-5, mesh_density=1e-9):
    """
    创建一维二极管网格
    
    参数:
        device: 器件名称
        region: 区域名称
        junction_position: 结位置 (cm)，默认5μm
        device_length: 器件总长度 (cm)，默认10μm
        mesh_density: 结区网格密度 (cm)，默认1nm
    """
    from devsim import (
        add_1d_contact,
        add_1d_mesh_line,
        add_1d_region,
        create_1d_mesh,
        create_device,
        finalize_mesh,
    )
    
    create_1d_mesh(mesh="dio")
    # 左边界（p区接触）
    add_1d_mesh_line(mesh="dio", pos=0, ps=1e-7, tag="top")
    # 结区位置（加密）
    add_1d_mesh_line(mesh="dio", pos=junction_position, ps=mesh_density, tag="mid")
    # 右边界（n区接触）
    add_1d_mesh_line(mesh="dio", pos=device_length, ps=1e-7, tag="bot")
    
    add_1d_contact(mesh="dio", name="top", tag="top", material="metal")
    add_1d_contact(mesh="dio", name="bot", tag="bot", material="metal")
    add_1d_region(mesh="dio", material="Si", region=region, tag1="top", tag2="bot")
    finalize_mesh(mesh="dio")
    create_device(mesh="dio", device=device)


def set_silicon_parameters(device, region, temperature=300):
    """
    设置硅材料参数
    
    参数:
        device: 器件名称
        region: 区域名称
        temperature: 温度 (K)，默认300K
    """
    from devsim.python_packages.simple_physics import SetSiliconParameters
    SetSiliconParameters(device, region, temperature)


def set_doping_profile(device, region, p_doping=1e18, n_doping=1e18, 
                       junction_position=0.5e-5):
    """
    设置掺杂分布（阶跃函数）
    
    参数:
        device: 器件名称
        region: 区域名称
        p_doping: p区掺杂浓度 (cm^-3)，默认1e18
        n_doping: n区掺杂浓度 (cm^-3)，默认1e18
        junction_position: 结位置 (cm)，默认5μm
    """
    from devsim.python_packages.model_create import CreateNodeModel
    
    # p区: x < junction_position
    CreateNodeModel(device, region, "Acceptors", 
                    f"{p_doping}*step({junction_position}-x)")
    # n区: x >= junction_position
    CreateNodeModel(device, region, "Donors", 
                    f"{n_doping}*step(x-{junction_position})")
    CreateNodeModel(device, region, "NetDoping", "Donors-Acceptors")


def setup_initial_solution(device, region):
    """
    设置初始电势解（仅泊松方程）
    
    参数:
        device: 器件名称
        region: 区域名称
    """
    from devsim import get_contact_list, set_parameter
    from devsim.python_packages.model_create import CreateSolution
    from devsim.python_packages.simple_physics import (
        CreateSiliconPotentialOnly,
        CreateSiliconPotentialOnlyContact,
        GetContactBiasName,
    )
    
    CreateSolution(device, region, "Potential")
    CreateSiliconPotentialOnly(device, region)
    
    for contact in get_contact_list(device=device):
        set_parameter(device=device, name=GetContactBiasName(contact), value=0.0)
        CreateSiliconPotentialOnlyContact(device, region, contact)


def setup_drift_diffusion(device, region):
    """
    设置漂移扩散方程
    
    参数:
        device: 器件名称
        region: 区域名称
    """
    from devsim import get_contact_list, set_node_values
    from devsim.python_packages.model_create import CreateSolution
    from devsim.python_packages.simple_physics import (
        CreateSiliconDriftDiffusion,
        CreateSiliconDriftDiffusionAtContact,
    )
    
    # 创建载流子解变量
    CreateSolution(device, region, "Electrons")
    CreateSolution(device, region, "Holes")
    
    # 从本征载流子初始化
    set_node_values(device=device, region=region, name="Electrons", 
                    init_from="IntrinsicElectrons")
    set_node_values(device=device, region=region, name="Holes", 
                    init_from="IntrinsicHoles")
    
    # 设置漂移扩散方程
    CreateSiliconDriftDiffusion(device, region)
    for contact in get_contact_list(device=device):
        CreateSiliconDriftDiffusionAtContact(device, region, contact)


def run_diode_1d_simulation(
    device_name="MyDevice",
    region_name="MyRegion",
    # 结构参数
    device_length=1e-5,
    junction_position=0.5e-5,
    mesh_density=1e-9,
    # 掺杂参数
    p_doping=1e18,
    n_doping=1e18,
    # 物理参数
    temperature=300,
    taun=1e-8,          # 电子寿命 (s)
    taup=1e-8,          # 空穴寿命 (s)
    # 偏置扫描参数
    start_voltage=0.0,
    max_voltage=0.5,
    voltage_step=0.1,
    # 求解器参数
    absolute_error=1e10,
    relative_error=1e-10,
    max_iterations=30,
    # 输出参数
    output_file="diode_1d.dat",
    print_doping=False,
    print_currents=True,
    # 智能网格参数（新增）
    use_intelligent_mesh=False,  # 是否使用智能网格策略
):
    """
    运行一维二极管DC IV仿真
    
    参数:
        device_name: 器件名称
        region_name: 区域名称
        device_length: 器件总长度 (cm)，默认10μm
        junction_position: 结位置 (cm)，默认5μm
        mesh_density: 结区网格密度 (cm)，默认1nm
        p_doping: p区掺杂浓度 (cm^-3)，默认1e18
        n_doping: n区掺杂浓度 (cm^-3)，默认1e18
        temperature: 温度 (K)，默认300K
        taun: 电子寿命 (s)，默认1e-8
        taup: 空穴寿命 (s)，默认1e-8
        start_voltage: 起始偏置 (V)，默认0V
        max_voltage: 最大偏置 (V)，默认0.5V
        voltage_step: 偏置步长 (V)，默认0.1V
        absolute_error: 绝对误差容限，默认1e10
        relative_error: 相对误差容限，默认1e-10
        max_iterations: 最大迭代次数，默认30
        output_file: 输出文件名
        print_doping: 是否打印掺杂分布，默认False
        print_currents: 是否打印电流，默认True
        use_intelligent_mesh: 是否使用智能网格策略（基于devsim-simulation原则自动优化网格密度）
    
    返回:
        dict: 包含仿真结果和状态信息
    
    使用示例:
        # 基本使用（默认网格）
        result = run_diode_1d_simulation(p_doping=1e18, n_doping=1e16)
        
        # 使用智能网格（自动根据掺杂梯度优化）
        result = run_diode_1d_simulation(
            p_doping=1e18, 
            n_doping=1e16,
            use_intelligent_mesh=True
        )
    """
    result = {
        "device": device_name,
        "region": region_name,
        "parameters": {
            "device_length_cm": device_length,
            "junction_position_cm": junction_position,
            "p_doping_cm3": p_doping,
            "n_doping_cm3": n_doping,
            "temperature_K": temperature,
            "taun_s": taun,
            "taup_s": taup,
        },
        "bias_points": [],
        "converged": True,
    }
    
    # 智能网格计算（新增）
    if use_intelligent_mesh:
        try:
            from ..common.mesh_strategies import DiodeMeshStrategy, MeshPolicy
            
            policy = MeshPolicy()
            strategy = DiodeMeshStrategy(policy)
            
            mesh_params = strategy.create_1d_mesh_params(
                p_doping=p_doping,
                n_doping=n_doping,
                temperature=temperature,
                device_length=device_length,
                junction_position=junction_position,
                max_voltage=max_voltage
            )
            
            # 使用智能计算的网格密度
            mesh_density = mesh_params['mesh_density']
            
            result['intelligent_mesh'] = {
                'mesh_density_cm': mesh_density,
                'estimated_junction_width_cm': strategy.policy.estimate_junction_width(
                    strategy.policy.__class__.__bases__[0].__call__()  # 获取物理参数
                ) if hasattr(strategy.policy, 'estimate_junction_width') else None,
            }
            
            print(f"[智能网格] 使用优化网格密度: {mesh_density:.2e} cm")
            
        except ImportError:
            print("[警告] 智能网格模块未找到，使用默认网格密度")
        except Exception as e:
            print(f"[警告] 智能网格计算失败: {e}，使用默认网格密度")
    
    # 1. 创建网格
    create_diode_mesh(device_name, region_name, junction_position, 
                     device_length, mesh_density)
    
    # 2. 设置参数
    set_silicon_parameters(device_name, region_name, temperature)
    set_parameter(device=device_name, region=region_name, name="taun", value=taun)
    set_parameter(device=device_name, region=region_name, name="taup", value=taup)
    
    # 3. 设置掺杂
    set_doping_profile(device_name, region_name, p_doping, n_doping, junction_position)
    
    if print_doping:
        print_node_values(device=device_name, region=region_name, name="NetDoping")
    
    # 4. 初始电势解
    setup_initial_solution(device_name, region_name)
    solve(type="dc", absolute_error=1.0, relative_error=1e-10, 
          maximum_iterations=max_iterations)
    
    # 5. 漂移扩散解（平衡态）
    setup_drift_diffusion(device_name, region_name)
    solve(type="dc", absolute_error=absolute_error, relative_error=relative_error,
          maximum_iterations=max_iterations)
    
    # 6. 偏置扫描
    v = start_voltage
    while v <= max_voltage + voltage_step/2:  # 避免浮点误差
        set_parameter(device=device_name, 
                     name=simple_physics.GetContactBiasName("top"), value=v)
        solve_info = solve(type="dc", absolute_error=absolute_error, 
                          relative_error=relative_error, 
                          maximum_iterations=max_iterations)
        
        # DEVSIM solve 可能返回 None，表示成功
        converged = True if solve_info is None else solve_info.get("converged", True)
        if not converged:
            result["converged"] = False
            result["error"] = f"Solver did not converge at V={v}V"
            break
        
        if print_currents:
            simple_physics.PrintCurrents(device_name, "top")
            simple_physics.PrintCurrents(device_name, "bot")
        
        result["bias_points"].append({
            "voltage_V": v,
            "converged": True,
        })
        
        v += voltage_step
    
    # 7. 输出结果
    write_devices(file=output_file, type="tecplot")
    result["output_file"] = output_file
    
    return result


if __name__ == "__main__":
    # 使用默认参数运行
    result = run_diode_1d_simulation()
    print(f"\n仿真完成: {result}")
    
    # 示例：高阻二极管
    # result = run_diode_1d_simulation(
    #     p_doping=1e16,
    #     n_doping=1e16,
    #     max_voltage=1.0,
    #     output_file="high_resistance_diode.dat"
    # )
