#!/usr/bin/env python3
"""
修复图4（原图5）的标注位置，避免被线条盖住
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
with open('data/final/doping_results.json', 'r') as f:
    doping_results = json.load(f)

print("修复图4的标注位置...")

# 图4：掺杂浓度权衡曲线（双坐标轴）
fig, ax1 = plt.subplots(figsize=(12, 8))

dopings = [r['p_doping'] for r in doping_results]
rons_d = [r['r_on_ohm_cm2'] for r in doping_results]
bvs = [r['breakdown_voltage_V'] for r in doping_results]

# 主图：Ron vs Doping
line1 = ax1.loglog(dopings, rons_d, 'ro-', linewidth=3, markersize=12, 
                  markerfacecolor='lightcoral', markeredgecolor='darkred', 
                  markeredgewidth=2, label='$R_{on}$', zorder=5)
ax1.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=14, fontweight='bold')
ax1.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=14, fontweight='bold', color='red')
ax1.tick_params(axis='y', labelcolor='red', labelsize=11)
ax1.tick_params(axis='x', labelsize=11)
ax1.grid(True, alpha=0.4, which='both', linestyle='--')

# 次坐标轴：击穿电压
ax2 = ax1.twinx()
line2 = ax2.loglog(dopings, bvs, 'bs--', linewidth=3, markersize=10, 
                  markerfacecolor='lightblue', markeredgecolor='darkblue', 
                  markeredgewidth=2, label='$BV$', zorder=4)
ax2.set_ylabel('击穿电压 $BV$ (V)', fontsize=14, fontweight='bold', color='blue')
ax2.tick_params(axis='y', labelcolor='blue', labelsize=11)
ax2.set_ylim([1, 5000])

# 添加数据点标注 - 调整位置避免被线条盖住
# 使用交替位置：左、右、左、右、左
annotations_ron = [
    (0, -60, -20),   # 第1个点：左下方
    (1, 60, 30),     # 第2个点：右上方
    (2, -60, 20),    # 第3个点：左上方
    (3, 60, -30),    # 第4个点：右下方
    (4, -60, 10),    # 第5个点：左上方
]

annotations_bv = [
    (0, 50, 30),     # 第1个点：右上方
    (1, -50, -30),   # 第2个点：左下方
    (2, 50, -20),    # 第3个点：右下方
    (3, -50, 20),    # 第4个点：左上方
    (4, 50, 0),      # 第5个点：右侧
]

for i, (d, r, b) in enumerate(zip(dopings, rons_d, bvs)):
    # Ron标注 - 交替左右位置
    if i % 2 == 0:
        x_offset = -70
        ha = 'right'
    else:
        x_offset = 70
        ha = 'left'
    
    if i < 2:
        y_offset = 25
    elif i == 2:
        y_offset = -35
    elif i == 3:
        y_offset = 30
    else:
        y_offset = -25
    
    ax1.annotate(f'{r:.2e}', xy=(d, r), xytext=(x_offset, y_offset),
                textcoords='offset points', fontsize=9, color='red',
                ha=ha, va='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                         edgecolor='red', alpha=0.9, linewidth=1.5),
                zorder=10)
    
    # BV标注 - 交替左右位置（与Ron相反）
    if i % 2 == 0:
        x_offset = 70
        ha = 'left'
    else:
        x_offset = -70
        ha = 'right'
    
    if i == 0:
        y_offset = 35
    elif i == 1:
        y_offset = -30
    elif i == 2:
        y_offset = 25
    elif i == 3:
        y_offset = -35
    else:
        y_offset = 30
    
    ax2.annotate(f'{b:.0f}V', xy=(d, b), xytext=(x_offset, y_offset),
                textcoords='offset points', fontsize=9, color='blue',
                ha=ha, va='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                         edgecolor='blue', alpha=0.9, linewidth=1.5),
                zorder=10)

# 添加最优区域阴影
ax1.axvspan(1e16, 1e17, alpha=0.2, color='green', label='最优设计区域')

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2 + [plt.Rectangle((0,0),1,1, fc='green', alpha=0.2)],
          labels1 + labels2 + ['最优设计区 ($10^{16}-10^{17}$ cm$^{-3}$)'],
          loc='upper right', fontsize=11, framealpha=0.95)

# 不设置标题，标题在Markdown中

plt.tight_layout()
plt.savefig('figures/final/fig4_doping_tradeoff.png', dpi=300, bbox_inches='tight')
print("✓ 图4已保存: fig4_doping_tradeoff.png (标注位置已调整)")
plt.close()

print("\n" + "="*70)
print("✅ 图4标注位置调整完成！")
print("="*70)
