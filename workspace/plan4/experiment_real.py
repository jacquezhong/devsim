#!/usr/bin/env python3
"""
场板二极管击穿特性真实仿真实验
基于Gmsh网格和DEVSIM的2D TCAD仿真
"""
import sys
import os
import json
import numpy as np
from datetime import datetime

# 检查DEVSIM是否可用
try:
    import devsim
    from devsim import (
        create_gmsh_mesh, get_edge_model_values, 
        delete_device, delete_mesh, solve
    )
    DEVSIM_AVAILABLE = True
    print(f"✓ DEVSIM可用: {devsim.__version__ if hasattr(devsim, '__version__') else 'installed'}")
except ImportError as e:
    print(f"✗ DEVSIM不可用: {e}")
    DEVSIM_AVAILABLE = False
    sys.exit(1)

# 尝试导入devsim_examples
try:
    sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')
    from devsim_examples import diode_2d_dc_iv
    EXAMPLES_AVAILABLE = True
    print("✓ devsim-examples可用")
except ImportError as e:
    print(f"✗ devsim-examples不可用: {e}")
    EXAMPLES_AVAILABLE = False


def run_real_simulation(L_fp, mesh_file, voltages):
    """
    运行真实的DEVSIM 2D仿真
    
    参数:
        L_fp: 场板长度 (μm)
        mesh_file: Gmsh网格文件路径
        voltages: 反向偏压列表
    
    返回:
        dict: 包含电流、电场等数据
    """
    results = {
        'L_fp': L_fp,
        'voltages': [],
        'currents': [],
        'max_electric_fields': [],
        'breakdown_voltage': None
    }
    
    device_name = f"diode_fp_{L_fp:.1f}"
    
    print(f"  开始真实DEVSIM仿真: L_fp = {L_fp} μm")
    print(f"    使用网格: {mesh_file}")
    
    prev_solution = None
    
    for v in voltages:
        try:
            # 清理之前的设备
            try:
                delete_device(device=device_name)
                delete_mesh(mesh=device_name)
            except:
                pass
            
            # 检查网格文件是否存在
            if not os.path.exists(mesh_file):
                print(f"    ✗ 网格文件不存在: {mesh_file}")
                break
            
            # 运行DEVSIM仿真
            # 使用diode_2d_dc_iv或手动设置仿真
            if EXAMPLES_AVAILABLE:
                result = diode_2d_dc_iv(
                    mesh_file=mesh_file,
                    anode_doping=1e19,
                    cathode_doping=1e14,
                    V_start=v-5 if prev_solution else 0,
                    V_stop=v,
                    V_step=-2.5,
                    device_name=device_name
                )
            else:
                # 手动运行仿真（备选方案）
                print(f"    手动运行仿真 @ V = {v}V...")
                # 这里需要手动设置DEVSIM仿真流程
                # 由于devsim_examples不可用，使用简化模型
                result = simulate_with_devsim_api(mesh_file, v, device_name)
            
            if result is None:
                print(f"    仿真失败 @ V = {v}V")
                break
            
            # 记录数据
            current_at_v = result.get('current', [0])[-1] if 'current' in result else 0
            results['voltages'].append(v)
            results['currents'].append(current_at_v)
            
            # 提取峰值电场
            try:
                E_field = get_edge_model_values(
                    device=device_name,
                    region="ndrift",
                    name="ElectricField"
                )
                max_E = max(E_field) if len(E_field) > 0 else 0
            except Exception as e:
                max_E = 0
                print(f"    警告: 无法提取电场 - {e}")
            
            results['max_electric_fields'].append(max_E)
            
            # 检测击穿
            if len(results['currents']) > 1:
                prev_current = abs(results['currents'][-2])
                curr_current = abs(results['currents'][-1])
                if prev_current > 1e-15:
                    current_ratio = curr_current / prev_current
                    if current_ratio > 3 or max_E > 2.5e5:
                        results['breakdown_voltage'] = v
                        print(f"    ✓ 击穿电压: {v} V")
                        # 继续仿真几个点以观察击穿后特性
                        continue
            
            # 如果已经击穿，记录几个点后停止
            if results['breakdown_voltage'] is not None:
                post_breakdown_count = sum(1 for bv in results['voltages'] if bv <= results['breakdown_voltage'])
                if post_breakdown_count >= 5:  # 击穿后再记录5个点
                    break
            
            prev_solution = result
            
        except Exception as e:
            print(f"    仿真异常 @ V = {v}V: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return results


def simulate_with_devsim_api(mesh_file, voltage, device_name):
    """
    使用DEVSIM API手动运行仿真（当devsim_examples不可用时）
    这是一个简化的实现，完整实现需要更多代码
    """
    # 这是一个占位符函数
    # 真实的实现需要设置物理模型、边界条件、求解器等
    # 由于复杂性，这里返回None表示需要devsim_examples
    return None


def run_experiments():
    """运行所有实验"""
    
    print("=" * 70)
    print("场板二极管击穿特性研究 - 真实DEVSIM仿真")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not DEVSIM_AVAILABLE:
        print("错误: DEVSIM不可用，无法运行真实仿真")
        return
    
    # 场板长度列表 (μm) - 使用已生成的5个网格
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    
    # 反向偏压列表 (V) - 密集的扫描点
    voltages = list(range(-10, -201, -5))  # 从-10V到-200V，步长5V
    
    all_results = []
    
    print("仿真参数:")
    print(f"  场板长度: {L_fp_values} μm (共{len(L_fp_values)}组)")
    print(f"  电压扫描: {voltages[0]}V ~ {voltages[-1]}V, 步长{abs(voltages[1] - voltages[0])}V")
    print(f"  总电压点数: {len(voltages)}")
    print()
    print("注意: DEVSIM 2D仿真耗时较长，每组可能需要5-30分钟")
    print("=" * 70)
    
    for L_fp in L_fp_values:
        print(f"\n\n{'='*70}")
        print(f"扫描场板长度 L_fp = {L_fp} μm...")
        print(f"{'='*70}")
        
        mesh_file = f"diode_fp_L{L_fp}.msh"
        
        # 检查网格文件
        if not os.path.exists(mesh_file):
            print(f"  ✗ 网格文件不存在: {mesh_file}")
            continue
        
        # 运行真实仿真
        result = run_real_simulation(L_fp, mesh_file, voltages)
        all_results.append(result)
        
        print(f"\n  结果汇总:")
        print(f"    数据点: {len(result['voltages'])}")
        if result['breakdown_voltage']:
            print(f"    击穿电压: {result['breakdown_voltage']} V")
        else:
            print(f"    击穿电压: 未达到击穿")
    
    # 保存结果
    output_file = 'data/final/breakdown_results_real.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\n{'='*70}")
    print(f"仿真完成！结果已保存至: {output_file}")
    print(f"{'='*70}")
    
    # 打印总结
    print("\n实验结果总结:")
    print(f"{'L_fp (μm)':<15} {'击穿电压 (V)':<20} {'最大电场 (V/cm)':<20}")
    print("-" * 70)
    
    for result in all_results:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage'] if result['breakdown_voltage'] else '未击穿'
        max_E = max(result['max_electric_fields']) if result['max_electric_fields'] else 0
        print(f"{L_fp:<15} {str(BV):<20} {max_E:<20.2e}")
    
    print("=" * 70)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_results


if __name__ == '__main__':
    results = run_experiments()
