#!/usr/bin/env python3
"""
图表生成脚本 - 离子通道传感器灵敏度研究
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 路径设置
data_dir = "/Users/lihengzhong/Documents/repo/devsim/workspace/plan3/data/final"
fig_dir = "/Users/lihengzhong/Documents/repo/devsim/workspace/plan3/figures/final"
os.makedirs(fig_dir, exist_ok=True)

print("=" * 60)
print("生成图表")
print("=" * 60)

# 加载数据
with open(f"{data_dir}/baseline_iv.json", "r") as f:
    baseline_data = json.load(f)

with open(f"{data_dir}/occupancy_analysis.json", "r") as f:
    occupancy_data = json.load(f)

with open(f"{data_dir}/debye_analysis.json", "r") as f:
    debye_data = json.load(f)

with open(f"{data_dir}/snr_analysis.json", "r") as f:
    snr_data = json.load(f)

voltages = np.array(baseline_data["voltage_V"])
current_clean = np.array(baseline_data["current_A"])

# ============================================================
# 图1: 基准I-V特性
# ============================================================
print("\n[图1] 生成基准I-V特性曲线...")

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(voltages, current_clean * 1e9, 'b-', linewidth=2.5, label='Clean Channel')
ax.set_xlabel('Voltage (V)', fontsize=12)
ax.set_ylabel('Current (nA)', fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)
ax.tick_params(labelsize=10)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig1_baseline_iv.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ 已保存: fig1_baseline_iv.png")

# ============================================================
# 图2: 不同占据率下的I-V曲线
# ============================================================
print("\n[图2] 生成占据率效应I-V曲线...")

fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
for i, (occ_key, data) in enumerate(occupancy_data.items()):
    occ = float(occ_key)
    current = np.array(data["current_A"])
    ax.plot(voltages, current * 1e9, '-', linewidth=2, 
            color=colors[i], label=f'Occupancy {occ*100:.0f}%')

ax.set_xlabel('Voltage (V)', fontsize=12)
ax.set_ylabel('Current (nA)', fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11, loc='best')
ax.tick_params(labelsize=10)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig2_occupancy_iv.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ 已保存: fig2_occupancy_iv.png")

# ============================================================
# 图3: 灵敏度与占据率关系
# ============================================================
print("\n[图3] 生成灵敏度分析图...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# (a) 平均灵敏度 vs 占据率
occupancies = []
avg_sensitivities = []
for occ_key, data in occupancy_data.items():
    occ = float(occ_key)
    if occ > 0:  # 排除0
        occupancies.append(occ * 100)
        avg_sensitivities.append(data["average_sensitivity"] * 100)

ax1.plot(occupancies, avg_sensitivities, 'ro-', linewidth=2, markersize=10)
ax1.set_xlabel('Occupancy (%)', fontsize=12)
ax1.set_ylabel('Average Sensitivity (%)', fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.tick_params(labelsize=10)

# (b) 电流变化 vs 电压 (25%占据示例)
occ_25_data = occupancy_data["0.25"]
delta_I = np.array(occ_25_data["delta_I_A"])
ax2.plot(voltages, delta_I * 1e9, 'g-', linewidth=2.5)
ax2.set_xlabel('Voltage (V)', fontsize=12)
ax2.set_ylabel('Current Change (nA)', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.tick_params(labelsize=10)

# 添加子图标签
ax1.text(-0.15, 1.05, '(a)', transform=ax1.transAxes, fontsize=14, fontweight='bold')
ax2.text(-0.15, 1.05, '(b)', transform=ax2.transAxes, fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig3_sensitivity_analysis.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ 已保存: fig3_sensitivity_analysis.png")

# ============================================================
# 图4: 德拜长度效应
# ============================================================
print("\n[图4] 生成德拜长度效应图...")

fig, ax = plt.subplots(figsize=(10, 6))

concentrations = debye_data["concentrations_M"]
debye_lengths_nm = debye_data["debye_lengths_nm"]
sensitivities = [s * 100 for s in debye_data["sensitivities"]]

# 计算德拜长度/半径比
r_nm = debye_data["channel_radius_nm"]
lambda_ratio = [ld / r_nm for ld in debye_lengths_nm]

ax.semilogy(lambda_ratio, sensitivities, 'mo-', linewidth=2.5, markersize=10)
ax.set_xlabel('Debye Length / Channel Radius', fontsize=12)
ax.set_ylabel('Detection Sensitivity (%)', fontsize=12)
ax.grid(True, alpha=0.3, which='both')
ax.tick_params(labelsize=10)

# 添加浓度标注
for i, conc in enumerate(concentrations):
    ax.annotate(f'{conc*1000:.0f}mM', 
                xy=(lambda_ratio[i], sensitivities[i]),
                xytext=(10, 10), textcoords='offset points',
                fontsize=9, alpha=0.8)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig4_debye_effect.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ 已保存: fig4_debye_effect.png")

# ============================================================
# 图5: SNR分析
# ============================================================
print("\n[图5] 生成SNR分析图...")

fig, ax = plt.subplots(figsize=(10, 6))

radii_nm = snr_data["radii_nm"]
snr_values = snr_data["snr_values"]

ax.plot(radii_nm, snr_values, 'cs-', linewidth=2.5, markersize=10)
ax.set_xlabel('Channel Radius (nm)', fontsize=12)
ax.set_ylabel('Signal-to-Noise Ratio', fontsize=12)
ax.grid(True, alpha=0.3)
ax.tick_params(labelsize=10)

# 添加SNR=3阈值线（检测极限）
ax.axhline(y=3, color='r', linestyle='--', linewidth=1.5, alpha=0.7, label='Detection Limit (SNR=3)')
ax.legend(fontsize=10)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig5_snr_analysis.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✓ 已保存: fig5_snr_analysis.png")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("图表生成完成！")
print("=" * 60)
print(f"\n图表保存在: {fig_dir}/")
print("  - fig1_baseline_iv.png: 基准I-V特性")
print("  - fig2_occupancy_iv.png: 占据率效应")
print("  - fig3_sensitivity_analysis.png: 灵敏度分析")
print("  - fig4_debye_effect.png: 德拜长度效应")
print("  - fig5_snr_analysis.png: 信噪比分析")
print("\n下一步: 运行 generate_docx.py 生成论文")
