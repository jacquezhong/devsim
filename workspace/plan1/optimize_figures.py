#!/usr/bin/env python3
"""
优化图表可视化 - 修复labels重叠问题
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import json
from matplotlib.patches import FancyBboxPatch

# 读取数据
with open('data/final/lifetime_results.json', 'r') as f:
    lifetime_results = json.load(f)

with open('data/final/doping_results.json', 'r') as f:
    doping_results = json.load(f)

print("优化图表可视化...")

# 创建输出目录
os.makedirs('figures/final', exist_ok=True)

# ============================================
# 图1: 优化后的Pareto前沿图
# ============================================
fig, ax = plt.subplots(figsize=(14, 10))

taus = [r['tau'] for r in lifetime_results]
qrrs = [r['qrr_C_cm2'] for r in lifetime_results]
vfs = [r['vf'] for r in lifetime_results]

# 使用对数坐标
ax.set_xscale('log')
ax.set_yscale('linear')

# 绘制数据点
colors = plt.cm.viridis(np.linspace(0, 1, len(taus)))
scatter = ax.scatter(qrrs, vfs, s=400, c=colors, edgecolors='black', 
                    linewidth=2.5, zorder=5, marker='o')

# 绘制连接线
ax.plot(qrrs, vfs, 'k--', alpha=0.4, linewidth=2, zorder=1)

# 添加标签 - 使用智能布局避免重叠
annotations = [
    {'idx': 0, 'tau': '10 ns', 'offset': (-120, -60), 'ha': 'right'},
    {'idx': 1, 'tau': '100 ns', 'offset': (-100, 40), 'ha': 'right'},
    {'idx': 2, 'tau': '1 μs', 'offset': (0, 60), 'ha': 'center'},
    {'idx': 3, 'tau': '10 μs', 'offset': (100, 40), 'ha': 'left'},
    {'idx': 4, 'tau': '100 μs', 'offset': (120, -60), 'ha': 'left'},
]

for ann in annotations:
    idx = ann['idx']
    q = qrrs[idx]
    v = vfs[idx]
    
    # 创建标注文本
    textstr = f"{ann['tau']}\nQrr={q:.1e} C/cm²\nVbi={v:.3f}V"
    
    # 添加标注
    ax.annotate(textstr, 
                xy=(q, v), 
                xytext=ann['offset'],
                textcoords='offset points',
                ha=ann['ha'],
                va='center',
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightyellow', 
                         edgecolor='black', linewidth=2, alpha=0.95),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2',
                              color='black', linewidth=1.5),
                zorder=10)

# 添加设计区域标注
ax.axhspan(0.85, 0.90, alpha=0.1, color='green', label='Optimal V_bi range')
ax.axvspan(1e-9, 1e-8, alpha=0.1, color='blue', label='High frequency')
ax.axvspan(1e-7, 1e-6, alpha=0.1, color='yellow', label='Medium frequency')
ax.axvspan(1e-5, 1e-4, alpha=0.1, color='red', label='Low frequency')

ax.set_xlabel('Reverse Recovery Charge Q_rr (C/cm²)', fontsize=14, fontweight='bold')
ax.set_ylabel('Built-in Potential V_bi (V)', fontsize=14, fontweight='bold')
ax.set_title('Pareto Front: Trade-off between V_bi and Q_rr\nCarrier Lifetime Optimization for Power Diodes', 
            fontsize=16, fontweight='bold', pad=20)

ax.grid(True, alpha=0.3, which='both', linestyle='--')
ax.set_xlim(5e-11, 5e-6)
ax.set_ylim(0.86, 0.89)

# 添加图例
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
               markersize=15, label='τ = 10 ns (High speed)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
               markersize=15, label='τ = 1 μs (Balanced)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
               markersize=15, label='τ = 100 μs (Low loss)'),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=11, 
         framealpha=0.95, edgecolor='black')

plt.tight_layout()
plt.savefig('figures/final/pareto_front_optimized.png', dpi=300, bbox_inches='tight')
print("✓ 已保存优化后的Pareto前沿图: figures/final/pareto_front_optimized.png")

# ============================================
# 图2: 综合分析图（6个子图）
# ============================================
fig = plt.figure(figsize=(20, 14))

# 载流子寿命分析
if lifetime_results:
    taus = [r['tau'] for r in lifetime_results]
    vfs = [r['vf'] for r in lifetime_results]
    currents = [r['current_density_A_cm2'] for r in lifetime_results]
    rons = [r['r_on_ohm_cm2'] for r in lifetime_results]
    qrrs = [r['qrr_C_cm2'] for r in lifetime_results]
    
    # 图1: V_bi vs 载流子寿命
    ax1 = plt.subplot(2, 3, 1)
    ax1.semilogx(taus, vfs, 'bo-', linewidth=3, markersize=12, markerfacecolor='lightblue', 
                markeredgecolor='darkblue', markeredgewidth=2)
    ax1.set_xlabel('Carrier Lifetime τ (s)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Built-in Potential V_bi (V)', fontsize=12, fontweight='bold')
    ax1.set_title('Built-in Potential vs Carrier Lifetime', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.4, which='both')
    ax1.set_ylim([0.85, 0.90])
    
    # 图2: 电流密度 vs 载流子寿命
    ax2 = plt.subplot(2, 3, 2)
    ax2.loglog(taus, currents, 'rs-', linewidth=3, markersize=12, markerfacecolor='lightcoral',
              markeredgecolor='darkred', markeredgewidth=2)
    ax2.set_xlabel('Carrier Lifetime τ (s)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Current Density J_F (A/cm²)', fontsize=12, fontweight='bold')
    ax2.set_title('Current Density vs Carrier Lifetime', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.4, which='both')
    
    # 图3: Q_rr vs τ
    ax3 = plt.subplot(2, 3, 3)
    ax3.loglog(taus, qrrs, 'g^-', linewidth=3, markersize=12, markerfacecolor='lightgreen',
              markeredgecolor='darkgreen', markeredgewidth=2)
    # 添加趋势线
    z = np.polyfit(np.log10(taus), np.log10(qrrs), 1)
    p = np.poly1d(z)
    ax3.loglog(taus, 10**p(np.log10(taus)), 'k--', alpha=0.5, linewidth=2, 
              label=f'Slope = {z[0]:.2f}')
    ax3.set_xlabel('Carrier Lifetime τ (s)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Q_rr (C/cm²)', fontsize=12, fontweight='bold')
    ax3.set_title('Reverse Recovery Charge vs Carrier Lifetime', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.4, which='both')
    ax3.legend(fontsize=11)
    
    # 图4: Ron vs τ
    ax4 = plt.subplot(2, 3, 4)
    ax4.loglog(taus, rons, 'mv-', linewidth=3, markersize=12, markerfacecolor='plum',
              markeredgecolor='purple', markeredgewidth=2)
    ax4.set_xlabel('Carrier Lifetime τ (s)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('On-Resistance R_on (Ω·cm²)', fontsize=12, fontweight='bold')
    ax4.set_title('On-Resistance vs Carrier Lifetime', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.4, which='both')

# 掺杂浓度分析
if doping_results:
    dopings = [r['p_doping'] for r in doping_results]
    vbis = [r['V_bi'] for r in doping_results]
    rons_d = [r['r_on_ohm_cm2'] for r in doping_results]
    bvs = [r['breakdown_voltage_V'] for r in doping_results]
    
    # 图5: V_bi vs P掺杂
    ax5 = plt.subplot(2, 3, 5)
    ax5.semilogx(dopings, vbis, 'co-', linewidth=3, markersize=12, markerfacecolor='lightcyan',
                markeredgecolor='darkcyan', markeredgewidth=2)
    ax5.set_xlabel('P+ Doping N_A (cm⁻³)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Built-in Potential V_bi (V)', fontsize=12, fontweight='bold')
    ax5.set_title('Built-in Potential vs Doping Concentration', fontsize=13, fontweight='bold')
    ax5.grid(True, alpha=0.4, which='both')
    # 添加最优区域标注
    ax5.axvspan(1e16, 1e17, alpha=0.2, color='green', label='Optimal range')
    ax5.legend(fontsize=10)
    
    # 图6: Ron vs P掺杂（与击穿电压双轴）
    ax6 = plt.subplot(2, 3, 6)
    ax6.loglog(dopings, rons_d, 'yv-', linewidth=3, markersize=12, markerfacecolor='lightyellow',
              markeredgecolor='orange', markeredgewidth=2, label='R_on')
    ax6.set_xlabel('P+ Doping N_A (cm⁻³)', fontsize=12, fontweight='bold')
    ax6.set_ylabel('On-Resistance R_on (Ω·cm²)', fontsize=12, fontweight='bold', color='orange')
    ax6.tick_params(axis='y', labelcolor='orange')
    ax6.grid(True, alpha=0.4, which='both')
    
    # 添加击穿电压（次坐标轴）
    ax6b = ax6.twinx()
    ax6b.loglog(dopings, bvs, 'b^--', linewidth=2, markersize=10, markerfacecolor='lightblue',
               markeredgecolor='darkblue', markeredgewidth=2, label='BV')
    ax6b.set_ylabel('Breakdown Voltage BV (V)', fontsize=12, fontweight='bold', color='blue')
    ax6b.tick_params(axis='y', labelcolor='blue')
    ax6b.set_ylim([1, 10000])
    
    ax6.set_title('On-Resistance & Breakdown Voltage vs Doping', fontsize=13, fontweight='bold')
    
    # 合并图例
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6b.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)
    
    # 添加最优区域
    ax6.axvspan(1e16, 1e17, alpha=0.2, color='green')

plt.tight_layout()
plt.savefig('figures/final/complete_analysis_optimized.png', dpi=300, bbox_inches='tight')
print("✓ 已保存优化后的综合分析图: figures/final/complete_analysis_optimized.png")

# ============================================
# 图3: 掺杂浓度权衡图
# ============================================
fig, ax = plt.subplots(figsize=(12, 8))

dopings = [r['p_doping'] for r in doping_results]
rons_d = [r['r_on_ohm_cm2'] for r in doping_results]
bvs = [r['breakdown_voltage_V'] for r in doping_results]

# 主图：Ron vs Doping
ax.loglog(dopings, rons_d, 'ro-', linewidth=3, markersize=14, markerfacecolor='lightcoral',
         markeredgecolor='darkred', markeredgewidth=2, label='On-Resistance', zorder=5)
ax.set_xlabel('P+ Doping Concentration N_A (cm⁻³)', fontsize=14, fontweight='bold')
ax.set_ylabel('On-Resistance R_on (Ω·cm²)', fontsize=14, fontweight='bold', color='red')
ax.tick_params(axis='y', labelcolor='red')
ax.grid(True, alpha=0.4, which='both')

# 次坐标轴：击穿电压
ax2 = ax.twinx()
ax2.loglog(dopings, bvs, 'bs--', linewidth=3, markersize=12, markerfacecolor='lightblue',
          markeredgecolor='darkblue', markeredgewidth=2, label='Breakdown Voltage', zorder=4)
ax2.set_ylabel('Breakdown Voltage BV (V)', fontsize=14, fontweight='bold', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
ax2.set_ylim([1, 10000])

# 添加数据点标注
for i, (d, r, b) in enumerate(zip(dopings, rons_d, bvs)):
    # Ron标注
    offset_r = 20 if i % 2 == 0 else -50
    ax.annotate(f'{r:.2e}', xy=(d, r), xytext=(20, offset_r),
               textcoords='offset points', fontsize=9, color='red',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor='red', alpha=0.8))
    
    # BV标注
    offset_b = 30 if i % 2 == 1 else -40
    ax2.annotate(f'{b:.1f}V', xy=(d, b), xytext=(20, offset_b),
                textcoords='offset points', fontsize=9, color='blue',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor='blue', alpha=0.8))

# 添加最优区域阴影
ax.axvspan(1e16, 1e17, alpha=0.15, color='green', label='Optimal design zone')

# 合并图例
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2 + [plt.Rectangle((0,0),1,1, fc='green', alpha=0.15)],
         labels1 + labels2 + ['Optimal zone (1e16-1e17 cm⁻³)'],
         loc='center right', fontsize=11, framealpha=0.95)

ax.set_title('Design Trade-off: On-Resistance vs Breakdown Voltage\n(P+ Doping Concentration Optimization)', 
            fontsize=15, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('figures/final/doping_tradeoff_optimized.png', dpi=300, bbox_inches='tight')
print("✓ 已保存优化后的掺杂权衡图: figures/final/doping_tradeoff_optimized.png")

# ============================================
# 清理旧的图表
# ============================================
import glob
old_files = glob.glob('figures/final/*.png')
for f in old_files:
    if 'optimized' not in f:
        os.remove(f)
        print(f"  已删除旧文件: {f}")

# 重命名优化后的文件
import shutil
if os.path.exists('figures/final/pareto_front_optimized.png'):
    shutil.move('figures/final/pareto_front_optimized.png', 'figures/final/pareto_front.png')
    print("✓ 已更新 pareto_front.png")

if os.path.exists('figures/final/complete_analysis_optimized.png'):
    shutil.move('figures/final/complete_analysis_optimized.png', 'figures/final/complete_analysis.png')
    print("✓ 已更新 complete_analysis.png")

print("\n" + "="*70)
print("✅ 图表优化完成！")
print("="*70)
print("\n最终生成的图表:")
print("  📈 figures/final/pareto_front.png - Pareto前沿图（labels已优化）")
print("  📈 figures/final/complete_analysis.png - 综合分析图（6个子图）")
print("  📈 figures/final/doping_tradeoff_optimized.png - 掺杂浓度权衡图")
print("="*70)
