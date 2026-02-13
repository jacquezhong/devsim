# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_compare_results.py - 对比skill优化版与之前的结果
"""

import json
import numpy as np
import matplotlib.pyplot as plt

print("="*70)
print("JEM2025 - Results Comparison")
print("="*70)

# 加载skill版本数据
with open('exp_oc/JEM2025_skill_equilibrium.json', 'r') as f:
    skill_eq = json.load(f)

with open('exp_oc/JEM2025_skill_iv.json', 'r') as f:
    skill_iv = json.load(f)

# 尝试加载之前版本的数据
try:
    with open('exp_oc/simulation_data_refined.json', 'r') as f:
        prev_data = json.load(f)
    has_previous = True
    print("\nLoaded previous simulation data for comparison")
except:
    has_previous = False
    print("\nNo previous data found, showing skill results only")

# 提取skill数据
x_skill = np.array(skill_eq['x'])
V_skill = np.array(skill_eq['V'])
n_skill = np.array(skill_eq['n'])
p_skill = np.array(skill_eq['p'])
v_skill = np.array(skill_iv['voltage'])
i_skill = np.array(skill_iv['current'])

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. 电势分布
ax = axes[0, 0]
ax.plot(x_skill, V_skill, 'b-', linewidth=2, label='Skill-Optimized')
if has_previous and 'equilibrium' in prev_data:
    x_prev = np.array(prev_data['equilibrium']['x'])
    V_prev = np.array(prev_data['equilibrium']['V'])
    ax.plot(x_prev, V_prev, 'r--', linewidth=1.5, alpha=0.7, label='Previous')
ax.set_xlabel('Position (um)', fontsize=12)
ax.set_ylabel('Potential (V)', fontsize=12)
ax.set_title('Potential Distribution at Equilibrium', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend()

# 2. 载流子浓度
ax = axes[0, 1]
ax.semilogy(x_skill, n_skill, 'b-', linewidth=2, label='Electrons (Skill)')
ax.semilogy(x_skill, p_skill, 'b--', linewidth=2, label='Holes (Skill)')
if has_previous and 'equilibrium' in prev_data:
    n_prev = np.array(prev_data['equilibrium']['n'])
    p_prev = np.array(prev_data['equilibrium']['p'])
    ax.semilogy(x_prev, n_prev, 'r-', linewidth=1.5, alpha=0.7, label='Electrons (Prev)')
    ax.semilogy(x_prev, p_prev, 'r--', linewidth=1.5, alpha=0.7, label='Holes (Prev)')
ax.set_xlabel('Position (um)', fontsize=12)
ax.set_ylabel('Carrier Concentration (cm^-3)', fontsize=12)
ax.set_title('Carrier Concentration at Equilibrium', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend()

# 3. IV曲线
ax = axes[1, 0]
ax.semilogy(v_skill, np.abs(i_skill), 'bo-', linewidth=2, markersize=6, label='Skill-Optimized')
if has_previous and 'iv_curve' in prev_data:
    v_prev = np.array(prev_data['iv_curve']['voltage'])
    i_prev = np.array(prev_data['iv_curve']['current'])
    ax.semilogy(v_prev, np.abs(i_prev), 'rs-', linewidth=1.5, markersize=4, 
                alpha=0.7, label='Previous')
ax.set_xlabel('Voltage (V)', fontsize=12)
ax.set_ylabel('Current Density (A/cm2)', fontsize=12)
ax.set_title('I-V Characteristics', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend()

# 4. 暗电流对比 (在0V)
ax = axes[1, 1]
J_dark_skill = np.abs(i_skill[len(i_skill)//2])  # 0V处的电流
ax.bar(['Skill-Optimized'], [J_dark_skill], color='blue', alpha=0.7)
if has_previous and 'iv_curve' in prev_data:
    J_dark_prev = np.abs(i_prev[len(i_prev)//2])
    ax.bar(['Previous'], [J_dark_prev], color='red', alpha=0.7)

# Rule 07 limit for comparison
T = 100  # K
lambda_cutoff = 14  # um (VLWIR)
Rule07 = 8360 * np.exp(-T * 1.44 / lambda_cutoff)  # A/cm2
ax.axhline(y=Rule07, color='g', linestyle='--', linewidth=2, label='Rule 07 Limit')

ax.set_ylabel('Dark Current at 0V (A/cm2)', fontsize=12)
ax.set_title('Dark Current Comparison', fontsize=14, fontweight='bold')
ax.set_yscale('log')
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig('exp_oc/JEM2025_skill_comparison.png', dpi=150, bbox_inches='tight')
print("\n  Saved: JEM2025_skill_comparison.png")

# 打印统计信息
print("\n" + "="*70)
print("Skill-Optimized Results Summary:")
print("="*70)
print(f"\nGrid Statistics:")
print(f"  Total nodes: {len(x_skill)}")
print(f"  LWIR nodes: {len(x_skill[x_skill < 9.0])}")
print(f"  Barrier nodes: {len(x_skill[(x_skill >= 9.0) & (x_skill < 13.35)])}")
print(f"  VLWIR nodes: {len(x_skill[x_skill >= 13.35])}")

print(f"\nPhysical Parameters:")
print(f"  Temperature: {skill_iv['temperature']} K")
print(f"  Dark current at 0V: {J_dark_skill:.4e} A/cm2")

# 计算与Rule 07的对比
print(f"\nRule 07 Benchmark:")
print(f"  Rule 07 limit: {Rule07:.4e} A/cm2")
print(f"  Ratio (J_dark / Rule07): {J_dark_skill/Rule07:.4e}")
if J_dark_skill < Rule07:
    print(f"  Status: BELOW Rule 07 (GOOD)")
else:
    print(f"  Status: ABOVE Rule 07")

print("\n" + "="*70)
print("Comparison Complete!")
print("="*70)
