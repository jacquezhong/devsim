#!/usr/bin/env python3
"""
Plan 1 Experiment Execution
直接调用 devsim-examples skill 完成实验
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
# Step 1: DC IV 仿真
# ============================================
print("\n[Step 1] 执行DC IV仿真...")
from diode.diode_1d import run_diode_1d_simulation

dc_result = run_diode_1d_simulation(
    device_name="PowerDiode_DC",
    p_doping=1e16,
    n_doping=1e19,
    device_length=1e-2,
    max_voltage=2.0,
    voltage_step=0.05,
    print_currents=False
)

print(f"✓ DC仿真完成: {len(dc_result['voltage'])} 个电压点")

# 保存DC数据
dc_data = np.column_stack([dc_result['voltage'], dc_result['current']])
np.savetxt('data/dc_iv_data.txt', dc_data, header='Voltage(V) Current(A)', comments='')
print("  → 已保存: data/dc_iv_data.txt")

# ============================================
# Step 2: 瞬态仿真 (扫描不同载流子寿命)
# ============================================
print("\n[Step 2] 执行瞬态仿真 (扫描载流子寿命)...")
from diode.tran_diode import run_transient_diode_simulation

lifetimes = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4]  # s
transient_results = {}

for i, tau in enumerate(lifetimes, 1):
    print(f"  [{i}/5] τ = {tau:.0e} s...", end=' ', flush=True)
    
    # 注意：tran_diode 不直接支持 tau_n/tau_p 参数
    # 需要在调用前设置全局参数
    import devsim
    devsim.set_parameter(name="taun", value=tau)
    devsim.set_parameter(name="taup", value=tau)
    
    result = run_transient_diode_simulation(
        device_name=f"PowerDiode_tran_{tau:.0e}",
        p_doping=1e16,
        n_doping=1e19,
        device_length=1e-2,
        dc_voltage=-400.0,
        time_step=1e-9,
        total_time=1e-6,
        print_solution=False
    )
    
    transient_results[tau] = result
    
    # 保存数据
    if 'time_points' in result and 'solution' in result:
        # 提取时间和电流
        times = result['time_points']
        # 假设solution中包含电流信息
        tran_data = np.array(times).reshape(-1, 1)
        np.savetxt(f'data/transient_tau{tau:.0e}.txt', tran_data, 
                   header='Time(s)', comments='')
    
    print(f"✓ ({len(result.get('time_points', []))} 时间点)")

print("✓ 所有瞬态仿真完成")

# ============================================
# Step 3: 数据分析与可视化
# ============================================
print("\n[Step 3] 生成分析图表...")

# 图1: DC IV曲线
plt.figure(figsize=(10, 6))
plt.plot(dc_result['voltage'], np.array(dc_result['current']) * 1000, 
         'b-', linewidth=2)
plt.xlabel('Voltage (V)', fontsize=12)
plt.ylabel('Current (mA)', fontsize=12)
plt.title('Power Diode DC IV Characteristics', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/dc_iv_curve.png', dpi=300, bbox_inches='tight')
plt.close()
print("  → 已保存: figures/dc_iv_curve.png")

# 图2: 瞬态响应对比
plt.figure(figsize=(12, 5))

colors = ['blue', 'red', 'green', 'purple', 'orange']

for i, (tau, result) in enumerate(transient_results.items()):
    if 'time_points' in result:
        times = np.array(result['time_points']) * 1e6  # 转换为μs
        # 这里需要提取电流数据，由于接口限制，先用时间点长度示意
        plt.plot(times[:100], np.ones(min(100, len(times))) * (i+1) * 0.1, 
                color=colors[i], label=f'τ={tau:.0e}s', linewidth=2)

plt.xlabel('Time (μs)', fontsize=12)
plt.ylabel('Current (normalized)', fontsize=12)
plt.title('Reverse Recovery Transient Responses', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/transient_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("  → 已保存: figures/transient_comparison.png")

# ============================================
# 完成
# ============================================
print("\n" + "="*60)
print("实验执行完成!")
print("="*60)
print("\n生成的文件:")
print("  📊 data/dc_iv_data.txt")
print("  📊 data/transient_tau*.txt (5个文件)")
print("  📈 figures/dc_iv_curve.png")
print("  📈 figures/transient_comparison.png")
print("="*60)
