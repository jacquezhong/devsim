# Copyright 2013-2025 DEVSIM LLC
# SPDX-License-Identifier: Apache-2.0

"""
双导线磁场分布（矢量势方法）

能力标识: magnetic_3d_twowire

工作思路:
1. 导入Gmsh生成的3D网格（twowire.msh）
2. 定义三个区域：空气(air)、左导线(left)、右导线(right)
3. 设置材料磁导率(mu)和电流密度(jz)
4. 定义矢量势Az的方程
5. 求解矢量势泊松方程：∇²Az = -μJz
6. 从Az计算磁场分量：Bx = ∂Az/∂y, By = -∂Az/∂x
7. 应用界面连续性和边界条件

能力边界:
- 静磁场分析
- 毕奥-萨伐尔定律
- 矢量势方法
- 低频近似（无位移电流）
- 需要Gmsh网格文件 twowire.msh

物理模型:
- 控制方程: ∇²Az = -μJz
- 磁场: B = ∇×A = (∂Az/∂y, -∂Az/∂x, 0)
- 左导线电流: +1 (z方向)
- 右导线电流: -1 (z方向)
"""

import devsim
from devsim import (
    add_gmsh_contact,
    add_gmsh_interface,
    add_gmsh_region,
    contact_equation,
    contact_node_model,
    create_device,
    create_gmsh_mesh,
    edge_from_node_model,
    edge_model,
    equation,
    finalize_mesh,
    get_element_model_values,
    get_node_model_values,
    interface_equation,
    interface_model,
    node_model,
    node_solution,
    set_parameter,
    solve,
    vector_gradient,
    write_devices,
)


def run_twowire_magnetic_simulation(
    mesh_file="twowire.msh",
    device_name="twowire",
    # 区域定义
    regions_config=None,
    interfaces_config=None,
    # 物理参数
    mu_air=1.0,             # 空气磁导率 (相对)
    mu_iron=1.0,          # 铁磁导率 (相对)
    jz_left=1.0,           # 左导线电流密度 (A/m^2)
    jz_right=-1.0,         # 右导线电流密度 (A/m^2)
    jz_air=0.0,            # 空气电流密度
    # 求解器参数
    relative_error=1e-10,
    absolute_error=1.0,
    # 输出参数
    output_prefix="twowire",
    print_volumes=True,
):
    """
    运行双导线静磁场仿真
    
    参数:
        mesh_file: Gmsh网格文件名
        device_name: 器件名称
        regions_config: 区域配置字典
        interfaces_config: 界面配置字典
        mu_air: 空气相对磁导率
        mu_iron: 铁相对磁导率
        jz_left: 左导线电流密度
        jz_right: 右导线电流密度
        jz_air: 空气电流密度
        relative_error: 相对误差容限
        absolute_error: 绝对误差容限
        output_prefix: 输出文件前缀
        print_volumes: 是否打印体积信息
    
    返回:
        dict: 仿真结果和磁场数据
    
    注意:
        运行前需要确保 twowire.msh 文件存在
        可使用 Gmsh 生成: gmsh twowire.geo -3
    """
    
    result = {
        "device": device_name,
        "mu_air": mu_air,
        "mu_iron": mu_iron,
        "jz_left": jz_left,
        "jz_right": jz_right,
        "converged": True,
    }
    
    try:
        # 1. 创建Gmsh网格
        create_gmsh_mesh(file=mesh_file, mesh=device_name)
        
        # 默认区域配置
        if regions_config is None:
            regions_config = {
                "air": {"gmsh_name": "air", "material": "air"},
                "left": {"gmsh_name": "left", "material": "iron"},
                "right": {"gmsh_name": "right", "material": "iron"},
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
            mesh=device_name, gmsh_name="bottom", region="air", 
            material="metal", name="bottom"
        )
        
        # 默认界面配置
        if interfaces_config is None:
            interfaces_config = {
                "air_left": {"gmsh_name": "air_left_interface", "region0": "air", "region1": "left"},
                "air_right": {"gmsh_name": "air_right_interface", "region0": "air", "region1": "right"},
            }
        
        # 添加界面
        for interface_name, config in interfaces_config.items():
            add_gmsh_interface(
                mesh=device_name,
                gmsh_name=config["gmsh_name"],
                region0=config["region0"],
                region1=config["region1"],
                name=interface_name,
            )
        
        finalize_mesh(mesh=device_name)
        create_device(mesh=device_name, device=device_name)
        
        # 2. 设置材料参数
        set_parameter(device=device_name, region="air", name="mu", value=mu_air)
        set_parameter(device=device_name, region="left", name="mu", value=mu_iron)
        set_parameter(device=device_name, region="right", name="mu", value=mu_iron)
        
        # 3. 设置电流密度
        set_parameter(device=device_name, region="air", name="jz", value=jz_air)
        set_parameter(device=device_name, region="left", name="jz", value=jz_left)
        set_parameter(device=device_name, region="right", name="jz", value=jz_right)
        
        # 4. 设置矢量势方程
        for region in ("air", "left", "right"):
            # 创建Az解变量
            node_solution(device=device_name, region=region, name="Az")
            edge_from_node_model(device=device_name, region=region, node_model="Az")
            
            # Az梯度（用于方程）
            edge_model(
                device=device_name,
                region=region,
                name="delAz",
                equation="(Az@n1 - Az@n0) * EdgeInverseLength",
            )
            edge_model(
                device=device_name, region=region, 
                name="delAz:Az@n1", equation="EdgeInverseLength"
            )
            edge_model(
                device=device_name, region=region, 
                name="delAz:Az@n0", equation="-EdgeInverseLength"
            )
            
            # 电流源项
            node_model(device=device_name, region=region, name="Jz", equation="mu * jz")
            
            # Az方程: ∇²Az = -μJz
            equation(
                device=device_name,
                region=region,
                name="Az_Equation",
                variable_name="Az",
                edge_model="delAz",
                node_model="Jz",
            )
            
            # 计算矢量梯度（用于磁场）
            vector_gradient(device=device_name, region=region, 
                           node_model="Az", calc_type="default")
            
            # 计算磁场分量: Bx = dAz/dy, By = -dAz/dx
            node_model(device=device_name, region=region, name="Bx", equation="Az_grady")
            node_model(device=device_name, region=region, name="By", equation="-Az_gradx")
        
        # 5. 界面连续性条件
        for interface in ("air_left", "air_right"):
            interface_model(
                device=device_name,
                interface=interface,
                name="continuousAz",
                equation="Az@r0 - Az@r1",
            )
            interface_model(
                device=device_name, interface=interface, 
                name="continuousAz:Az@r0", equation="1.0"
            )
            interface_model(
                device=device_name, interface=interface, 
                name="continuousAz:Az@r1", equation="-1.0"
            )
            interface_equation(
                device=device_name,
                interface=interface,
                name="Az_Equation",
                interface_model="continuousAz",
                type="continuous",
            )
        
        # 6. 边界条件（底部接触Az=0）
        contact_node_model(device=device_name, contact="bottom", 
                          name="Az_zero", equation="Az - 0")
        contact_node_model(device=device_name, contact="bottom", 
                          name="Az_zero:Az", equation="1.0")
        contact_equation(
            device=device_name, contact="bottom", 
            name="Az_Equation", node_model="Az_zero"
        )
        
        # 7. 求解
        solve_info = solve(
            relative_error=relative_error,
            absolute_error=absolute_error,
            type="dc"
        )
        
        if not solve_info.get("converged", True):
            result["converged"] = False
            result["error"] = "Solver did not converge"
            return result
        
        # 8. 输出结果
        msh_file = f"{output_prefix}_out.msh"
        dat_file = f"{output_prefix}_out.dat"
        write_devices(file=msh_file)
        write_devices(file=dat_file, type="tecplot")
        
        result["output_files"] = [msh_file, dat_file]
        
        # 9. 打印体积信息
        if print_volumes:
            print("\n=== Volume Information ===")
            for region in ("air", "left", "right"):
                elem_vol = sum(get_element_model_values(
                    device=device_name, region=region, name="ElementNodeVolume"
                ))
                node_vol = sum(get_node_model_values(
                    device=device_name, region=region, name="NodeVolume"
                ))
                print(f"Region {region}:")
                print(f"  ElementNodeVolume: {elem_vol:.6e}")
                print(f"  NodeVolume: {node_vol:.6e}")
                
                result[f"{region}_volume"] = {
                    "element": elem_vol,
                    "node": node_vol,
                }
        
        # 10. 获取磁场数据
        result["magnetic_field"] = {}
        for region in ("air", "left", "right"):
            bx_values = get_node_model_values(device=device_name, region=region, name="Bx")
            by_values = get_node_model_values(device=device_name, region=region, name="By")
            result["magnetic_field"][region] = {
                "Bx": bx_values,
                "By": by_values,
            }
        
    except Exception as e:
        result["converged"] = False
        result["error"] = str(e)
        result["hint"] = "Ensure twowire.msh exists (generate with: gmsh twowire.geo -3)"
    
    return result


if __name__ == "__main__":
    result = run_twowire_magnetic_simulation()
    
    if result.get("converged"):
        print(f"\n磁场仿真成功!")
        print(f"输出文件: {result['output_files']}")
    else:
        print(f"\n仿真失败: {result.get('error')}")
        print(f"提示: {result.get('hint', '')}")
