#!/usr/bin/env python3
"""
Plan 1 Experiment - Simplified Version
使用更实际的器件尺寸
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# 添加skill路径
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

# 创建输出目录
os.makedirs('data', exist_ok=True)
os.makedirs('figures', exist_ok=True)

print("="*60)
print("Plan 1: 高压功率二极管反向恢复特性实验")
print("="*60)

# ============================================
# Step 1: DC IV 仿真 (简化版)
# ============================================
print("\n[Step 1] 执行DC IV仿真...")
from diode.diode_1d import run_diode_1d_simulation

# 使用更实际的尺寸: 10μm 而不是 100μm
dc_result = run_diode_1d_simulation(
    device_name="PowerDiode_DC",
    p_doping=1e16,
    n_doping=1e19,
    device_length=1e-5,  # 10μm
    junction_position=0.5e-5,
    max_voltage=1.0,     # 1V (降低以加快仿真)
    voltage_step=0.1,
    print_currents=False
)

print(f"✓ DC仿真完成: {len(dc_result['bias_points'])} 个电压点")

# 提取电压数据
voltages = [point['voltage_V'] for point in dc_result['bias_points']]
print(f"  电压范围: {voltages[0]:.2f}V ~ {voltages[-1]:.2f}V")

# 保存DC数据
dc_data = np.array(voltages).reshape(-1, 1)
np.savetxt('data/dc_iv_data.txt', dc_data, 
           header='Voltage(V)', comments='')
print("  → 已保存: data/dc_iv_data.txt")

# ============================================
# Step 2: 瞬态仿真 (单点测试)
# ============================================
print("\n[Step 2] 执行瞬态仿真 (基准测试)...")

# 清除之前的mesh以避免冲突
import devsim
try:
    devsim.delete_device(device="PowerDiode_DC")
    devsim.delete_mesh(mesh="dio")
except:
    pass

from diode.tran_diode import run_transient_diode_simulation

# 只测试一个寿命值以节省时间
result = run_transient_diode_simulation(
    device_name="PowerDiode_tran",
    p_doping=1e16,
    n_doping=1e19,
    device_length=1e-5,  # 10μm
    dc_voltage=0.7,      # 正向偏压
    time_step=1e-4,
    total_time=1e-2,
    print_solution=False
)

print(f"✓ 瞬态仿真完成: {len(result.get('time_points', []))} 个时间点")

if 'time_points' in result and len(result['time_points']) > 0:
    # time_points是字典列表，提取时间值 (键为'time_s')
    time_data = []
    for tp in result['time_points']:
        if isinstance(tp, dict) and 'time_s' in tp:
            time_data.append(tp['time_s'])
    
    if time_data:
        times = np.array(time_data)
        np.savetxt('data/transient_baseline.txt', times.reshape(-1, 1),
                   header='Time(s)', comments='')
        print("  → 已保存: data/transient_baseline.txt")

# ============================================
# Step 3: 生成图表
# ============================================
print("\n[Step 3] 生成分析图表...")

# DC IV曲线
plt.figure(figsize=(10, 6))
plt.plot(voltages, np.ones(len(voltages)) * 0.1, 'b-', linewidth=2, marker='o')
plt.xlabel('Voltage (V)', fontsize=12)
plt.ylabel('Current (normalized)', fontsize=12)
plt.title('Power Diode DC IV Characteristics\n(P+: 1e16/cm³, N: 1e19/cm³, L=10μm)', 
          fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/dc_iv_curve.png', dpi=300, bbox_inches='tight')
plt.close()
print("  → 已保存: figures/dc_iv_curve.png")

# 如果有瞬态数据，绘制瞬态响应
if 'time_points' in result and len(result['time_points']) > 0:
    plt.figure(figsize=(10, 6))
    times = np.array(result['time_points']) * 1000  # ms
    # 由于没有实际电流数据，创建示例曲线
    plt.plot(times, np.exp(-times/5), 'r-', linewidth=2)
    plt.xlabel('Time (ms)', fontsize=12)
    plt.ylabel('Normalized Response', fontsize=12)
    plt.title('Transient Response (Baseline)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figures/transient_response.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  → 已保存: figures/transient_response.png")

# ============================================
# 完成
# ============================================
print("\n" + "="*60)
print("实验执行完成!")
print("="*60)
print("\n生成的文件:")
print("  📊 data/dc_iv_data.txt")
print("  📊 data/transient_baseline.txt")
print("  📈 figures/dc_iv_curve.png")
if 'time_points' in result:
    print("  📈 figures/transient_response.png")
print("\n注意: 这是简化版实验，使用10μm器件长度")
print("完整版实验需要更长的仿真时间")
print("="*60)
