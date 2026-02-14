# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
生物电应用 - 3D神经信号传导/DNA检测

能力标识: bioapp_3d_nerve_signal

工作思路:
1. 导入Gmsh生成的3D圆盘网格（disk_3d.msh）
2. 定义三种材料区域：溶液(solution)、DNA(dna)、介电层(dielectric)
3. 在DNA区域设置电荷密度模拟带电生物分子
4. 求解泊松方程获得电势分布
5. 对比有/无DNA电荷时的电势变化
6. 计算电势差用于生物分子检测

能力边界:
- 3D生物电应用（DNA检测、离子通道）
- 圆柱坐标系（轴对称）
- 多区域多界面
- 需要Gmsh网格文件 disk_3d.msh

依赖:
- disk_3d.msh 网格文件（需预生成）
- bioapp1_common 模块（物理模型定义）

应用:
- DNA测序（检测DNA通过纳米孔时的电势变化）
- 离子通道电流
- 生物传感器
"""

import sys
import devsim
from devsim import (
    add_gmsh_contact,
    add_gmsh_interface,
    add_gmsh_region,
    create_device,
    create_gmsh_mesh,
    finalize_mesh,
    node_model,
    node_solution,
    set_node_values,
    set_parameter,
    solve,
    write_devices,
)


def run_bioapp1_3d_simulation(
    voltage=1.0,                    # 外加电压 (V)
    dna_charge_density=2e21,        # DNA电荷密度 (/cm^3)
    zero_charge_first=True,         # 先求解零电荷参考
    output_prefix="bioapp1_3d",
    # 网格参数
    mesh_file="disk_3d.msh",
    device_name="disk",
    # 区域定义
    regions_config=None,
    # 求解器参数
    relative_error=1e-7,
    absolute_error=1e11,
    max_iterations=100,
):
    """
    运行3D生物电仿真
    
    参数:
        voltage: 外加电压 (V)，在上下接触施加 ±V/2
        dna_charge_density: DNA区域电荷密度 (/cm^3)
        zero_charge_first: 是否先求解零电荷参考解
        output_prefix: 输出文件前缀
        mesh_file: Gmsh网格文件名（3D）
        device_name: 器件名称
        regions_config: 区域配置字典（可选）
        relative_error: 相对误差容限
        absolute_error: 绝对误差容限
        max_iterations: 最大迭代次数
    
    返回:
        dict: 仿真结果
    
    注意:
        运行前需要确保 disk_3d.msh 文件存在
        可使用 Gmsh 生成: gmsh disk_3d.geo -3
        
        与2D版本区别: 使用3D网格，计算量更大
    """
    
    result = {
        "device": device_name,
        "voltage_V": voltage,
        "dna_charge_density": dna_charge_density,
        "converged": True,
        "dimension": 3,
    }
    
    try:
        # 设置偏置（上下接触对称）
        set_parameter(name="top_bias", value=voltage / 2.0)
        set_parameter(name="bot_bias", value=-voltage / 2.0)
        
        # 创建Gmsh网格
        create_gmsh_mesh(file=mesh_file, mesh=device_name)
        
        # 默认区域配置
        if regions_config is None:
            regions_config = {
                "solution": {"gmsh_name": "solution", "material": "ionic_solution"},
                "dna": {"gmsh_name": "dna", "material": "dna"},
                "dielectric": {"gmsh_name": "dielectric", "material": "dielectric"},
            }
        
        # 添加区域
        for region_name, config in regions_config.items():
            add_gmsh_region(
                mesh=device_name,
                gmsh_name=config["gmsh_name"],
                region=region_name,
                material=config["material"]
            )
        
        # 添加接触
        add_gmsh_contact(
            mesh=device_name, gmsh_name="top", region="solution", 
            name="top", material="metal"
        )
        add_gmsh_contact(
            mesh=device_name, gmsh_name="bot", region="solution", 
            name="bot", material="metal"
        )
        
        # 添加界面
        add_gmsh_interface(
            mesh=device_name,
            gmsh_name="dielectric_solution",
            region0="dielectric",
            region1="solution",
            name="dielectric_solution",
        )
        add_gmsh_interface(
            mesh=device_name,
            gmsh_name="dna_solution",
            region0="dna",
            region1="solution",
            name="dna_solution",
        )
        
        finalize_mesh(mesh=device_name)
        create_device(mesh=device_name, device=device_name)
        
        # 导入物理模型
        try:
            import bioapp1_common  # noqa: F401
        except ImportError:
            result["warning"] = "bioapp1_common not found, using basic setup"
            set_parameter(device=device_name, region="solution", name="n_bound", value=6.02e17)
            set_parameter(device=device_name, region="dielectric", name="charge_density", value=0)
        
        # 先求解零电荷情况（参考）
        if zero_charge_first:
            set_parameter(device=device_name, region="dna", name="charge_density", value=0)
            solve_info = solve(
                type="dc",
                relative_error=relative_error,
                absolute_error=absolute_error,
                maximum_iterations=max_iterations
            )
            if not solve_info.get("converged", True):
                result["converged"] = False
                result["error"] = "Zero charge solve did not converge"
                return result
            
            # 保存零电荷解
            for region in ("dna", "dielectric", "solution"):
                node_solution(device=device_name, region=region, name="Potential_zero")
                set_node_values(
                    device=device_name, region=region, 
                    name="Potential_zero", init_from="Potential"
                )
        
        # 设置DNA电荷并重新求解
        set_parameter(device=device_name, region="dna", name="charge_density", 
                     value=dna_charge_density)
        solve_info = solve(
            type="dc",
            relative_error=relative_error,
            absolute_error=absolute_error,
            maximum_iterations=max_iterations
        )
        
        if not solve_info.get("converged", True):
            result["converged"] = False
            result["error"] = "DNA charge solve did not converge"
            return result
        
        # 计算电势变化
        if zero_charge_first:
            for region in ("dna", "dielectric", "solution"):
                node_model(
                    device=device_name,
                    region=region,
                    name="LogDeltaPotential",
                    equation="log(abs(Potential-Potential_zero) + 1e-10)/log(10)",
                )
        
        # 输出结果
        output_file = f"{output_prefix}_{voltage}.dat"
        write_devices(file=output_file, type="tecplot")
        result["output_file"] = output_file
        
    except Exception as e:
        result["converged"] = False
        result["error"] = str(e)
        result["hint"] = "Ensure disk_3d.msh exists (generate with: gmsh disk_3d.geo -3)"
    
    return result


if __name__ == "__main__":
    # 从命令行读取电压
    if len(sys.argv) != 2:
        voltage = 1.0
        print(f"Usage: python bioapp1_3d.py <voltage>")
        print(f"Using default voltage: {voltage}V")
    else:
        voltage = float(sys.argv[1])
    
    result = run_bioapp1_3d_simulation(voltage=voltage)
    
    if result.get("converged"):
        print(f"\n3D仿真成功: {result['output_file']}")
    else:
        print(f"\n仿真失败: {result.get('error')}")
        print(f"提示: {result.get('hint', '')}")
