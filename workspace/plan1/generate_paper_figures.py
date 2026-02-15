#!/usr/bin/env python3
"""
生成学术论文标准图表
按照论文 draft.md 中的图表组织方式
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('figures/final', exist_ok=True)

# 读取数据
with open('data/final/lifetime_results.json', 'r') as f:
    lifetime_results = json.load(f)

with open('data/final/doping_results.json', 'r') as f:
    doping_results = json.load(f)

print("生成学术论文标准图表...")

# ============================================
# 图1：一维PN结二极管结构示意图
# ============================================
fig, ax = plt.subplots(figsize=(10, 6))

# 绘制器件结构
# P+区
p_region = plt.Rectangle((0, 0), 0.4, 1, linewidth=2, 
                         edgecolor='black', facecolor='lightblue', alpha=0.7)
ax.add_patch(p_region)
ax.text(0.2, 0.5, 'P+区\n$N_A = 10^{16}-10^{18}$ cm$^{-3}$', 
        ha='center', va='center', fontsize=12, fontweight='bold')

# N区
n_region = plt.Rectangle((0.4, 0), 0.6, 1, linewidth=2, 
                         edgecolor='black', facecolor='lightyellow', alpha=0.7)
ax.add_patch(n_region)
ax.text(0.7, 0.5, 'N区\n$N_D = 10^{19}$ cm$^{-3}$', 
        ha='center', va='center', fontsize=12, fontweight='bold')

# 结位置标注
ax.axvline(x=0.4, color='red', linewidth=3, linestyle='--', label='PN结')
ax.text(0.4, 1.05, 'PN结', ha='center', fontsize=11, color='red', fontweight='bold')

# 电极
ax.plot([0, 0], [0.3, 0.7], 'k-', linewidth=4)
ax.text(-0.05, 0.5, '阳极\n(A)', ha='right', va='center', fontsize=11, fontweight='bold')

ax.plot([1, 1], [0.3, 0.7], 'k-', linewidth=4)
ax.text(1.05, 0.5, '阴极\n(K)', ha='left', va='center', fontsize=11, fontweight='bold')

# 尺寸标注
ax.annotate('', xy=(0, -0.1), xytext=(1, -0.1),
            arrowprops=dict(arrowstyle='<->', color='black', lw=2))
ax.text(0.5, -0.15, '器件长度: 100 μm', ha='center', fontsize=11)

ax.annotate('', xy=(0.4, -0.05), xytext=(0, -0.05),
            arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
ax.text(0.2, -0.08, 'P+区', ha='center', fontsize=9, color='blue')

ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.25, 1.2)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('图1 一维PN结二极管结构示意图', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('figures/final/fig1_structure.png', dpi=300, bbox_inches='tight')
print("✓ 已保存图1: fig1_structure.png")
plt.close()

# ============================================
# 图2：载流子寿命对器件特性的影响（4个子图）
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

taus = [r['tau'] for r in lifetime_results]
vfs = [r['vf'] for r in lifetime_results]
currents = [r['current_density_A_cm2'] for r in lifetime_results]
rons = [r['r_on_ohm_cm2'] for r in lifetime_results]
qrrs = [r['qrr_C_cm2'] for r in lifetime_results]

# (a) 内建电势与载流子寿命
ax = axes[0, 0]
ax.semilogx(taus, vfs, 'bo-', linewidth=2.5, markersize=10, 
           markerfacecolor='lightblue', markeredgecolor='darkblue', markeredgewidth=2)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=13, fontweight='bold')
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=13, fontweight='bold')
ax.set_title('(a) 内建电势与载流子寿命的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
ax.set_ylim([0.85, 0.90])
ax.text(0.05, 0.95, f'$V_{{bi}} = {np.mean(vfs):.3f}$ V (恒定)', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# (b) 正向电流密度与载流子寿命
ax = axes[0, 1]
ax.loglog(taus, currents, 'rs-', linewidth=2.5, markersize=10, 
         markerfacecolor='lightcoral', markeredgecolor='darkred', markeredgewidth=2)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=13, fontweight='bold')
ax.set_ylabel('正向电流密度 $J_F$ (A/cm$^2$)', fontsize=13, fontweight='bold')
ax.set_title('(b) 正向电流密度与载流子寿命的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 添加趋势线
z = np.polyfit(np.log10(taus), np.log10(currents), 1)
slope_text = f'斜率 = {z[0]:.2f}'
ax.text(0.05, 0.95, slope_text, transform=ax.transAxes, fontsize=11,
       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# (c) 反向恢复电荷与载流子寿命
ax = axes[1, 0]
ax.loglog(taus, qrrs, 'g^-', linewidth=2.5, markersize=10, 
         markerfacecolor='lightgreen', markeredgecolor='darkgreen', markeredgewidth=2)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=13, fontweight='bold')
ax.set_ylabel('反向恢复电荷 $Q_{rr}$ (C/cm$^2$)', fontsize=13, fontweight='bold')
ax.set_title('(c) 反向恢复电荷与载流子寿命的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 添加理论线
qrr_theory = [1e-2 * t for t in taus]  # 理论值
ax.loglog(taus, qrr_theory, 'k--', linewidth=2, alpha=0.5, label='理论值 ($Q_{rr} = \\tau \\cdot J_F$)')
# 计算实际比例系数
ratio = qrrs[2] / (taus[2] * currents[2])
ax.text(0.05, 0.95, f'$Q_{{rr}} \\approx {ratio:.1f} \\cdot \\tau \\cdot J_F$', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
ax.legend(fontsize=11, loc='lower right')

# (d) 导通电阻与载流子寿命
ax = axes[1, 1]
ax.loglog(taus, rons, 'mv-', linewidth=2.5, markersize=10, 
         markerfacecolor='plum', markeredgecolor='purple', markeredgewidth=2)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=13, fontweight='bold')
ax.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=13, fontweight='bold')
ax.set_title('(d) 导通电阻与载流子寿命的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 添加趋势说明
ax.text(0.05, 0.95, '$R_{on} \\propto \\sqrt{\\tau}$', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('figures/final/fig2_lifetime_effects.png', dpi=300, bbox_inches='tight')
print("✓ 已保存图2: fig2_lifetime_effects.png")
plt.close()

# ============================================
# 图3：掺杂浓度对器件特性的影响（3个子图）
# ============================================
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

dopings = [r['p_doping'] for r in doping_results]
vbis = [r['V_bi'] for r in doping_results]
rons_d = [r['r_on_ohm_cm2'] for r in doping_results]
bvs = [r['breakdown_voltage_V'] for r in doping_results]

# (a) 内建电势与掺杂浓度
ax = axes[0]
ax.semilogx(dopings, vbis, 'co-', linewidth=2.5, markersize=10, 
           markerfacecolor='lightcyan', markeredgecolor='darkcyan', markeredgewidth=2)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=13, fontweight='bold')
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=13, fontweight='bold')
ax.set_title('(a) 内建电势与掺杂浓度的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 理论线
n_i = 1.5e10
N_D = 1e19
vbis_theory = [0.02585 * np.log(n * N_D / (n_i**2)) for n in dopings]
ax.semilogx(dopings, vbis_theory, 'r--', linewidth=2, alpha=0.6, label='理论曲线')
ax.legend(fontsize=11)
ax.text(0.05, 0.95, '$V_{bi} = \\frac{kT}{q} \\ln(\\frac{N_A N_D}{n_i^2})$', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# (b) 导通电阻与掺杂浓度
ax = axes[1]
ax.loglog(dopings, rons_d, 'yv-', linewidth=2.5, markersize=10, 
         markerfacecolor='lightyellow', markeredgecolor='orange', markeredgewidth=2)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=13, fontweight='bold')
ax.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=13, fontweight='bold')
ax.set_title('(b) 导通电阻与掺杂浓度的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 添加最优区域
ax.axvspan(1e16, 1e17, alpha=0.2, color='green', label='最优设计区域')
ax.legend(fontsize=11)
ax.text(0.05, 0.95, '$R_{on} \\propto \\frac{1}{\\sqrt{N_A}}$', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# (c) 击穿电压与掺杂浓度
ax = axes[2]
ax.loglog(dopings, bvs, 'bs-', linewidth=2.5, markersize=10, 
         markerfacecolor='lightblue', markeredgecolor='darkblue', markeredgewidth=2)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=13, fontweight='bold')
ax.set_ylabel('击穿电压 $BV$ (V)', fontsize=13, fontweight='bold')
ax.set_title('(c) 击穿电压与掺杂浓度的关系', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.4, which='both', linestyle='--')
# 添加最优区域
ax.axvspan(1e16, 1e17, alpha=0.2, color='green', label='最优设计区域')
ax.legend(fontsize=11)
ax.text(0.05, 0.95, '$BV \\propto \\frac{1}{N_A}$', 
       transform=ax.transAxes, fontsize=11, verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('figures/final/fig3_doping_effects.png', dpi=300, bbox_inches='tight')
print("✓ 已保存图3: fig3_doping_effects.png")
plt.close()

# ============================================
# 图4：Pareto前沿曲线（载流子寿命优化）
# ============================================
fig, ax = plt.subplots(figsize=(12, 9))

qrrs_pareto = [r['qrr_C_cm2'] for r in lifetime_results]
vfs_pareto = [r['vf'] for r in lifetime_results]
taus_labels = ['10 ns', '100 ns', '1 μs', '10 μs', '100 μs']

# 使用对数坐标
ax.set_xscale('log')

# 绘制数据点
colors = plt.cm.viridis(np.linspace(0, 1, len(taus)))
scatter = ax.scatter(qrrs_pareto, vfs_pareto, s=350, c=colors, 
                    edgecolors='black', linewidth=2.5, zorder=5, marker='o')

# 绘制连接线
ax.plot(qrrs_pareto, vfs_pareto, 'k--', alpha=0.4, linewidth=2, zorder=1)

# 添加标签 - 使用连线避免重叠
annotations = [
    {'idx': 0, 'offset': (-150, 30), 'ha': 'right'},
    {'idx': 1, 'offset': (-120, -40), 'ha': 'right'},
    {'idx': 2, 'offset': (0, 50), 'ha': 'center'},
    {'idx': 3, 'offset': (120, -40), 'ha': 'left'},
    {'idx': 4, 'offset': (150, 30), 'ha': 'left'},
]

for ann in annotations:
    idx = ann['idx']
    q = qrrs_pareto[idx]
    v = vfs_pareto[idx]
    tau_label = taus_labels[idx]
    
    # 创建标注文本
    textstr = f"{tau_label}\n$Q_{{rr}}$={q:.1e} C/cm$^2$\n$V_{{bi}}$={v:.3f}V"
    
    # 添加标注
    ax.annotate(textstr, 
                xy=(q, v), 
                xytext=ann['offset'],
                textcoords='offset points',
                ha=ann['ha'],
                va='center',
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', 
                         edgecolor='black', linewidth=1.5, alpha=0.9),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.15',
                              color='black', linewidth=1.2),
                zorder=10)

# 添加设计区域标注
ax.axvspan(5e-11, 5e-10, alpha=0.15, color='blue', label='高速区 (>100 kHz)')
ax.axvspan(5e-9, 5e-8, alpha=0.15, color='green', label='中速区 (10-100 kHz)')
ax.axvspan(5e-7, 5e-6, alpha=0.15, color='red', label='低速区 (<10 kHz)')

ax.set_xlabel('反向恢复电荷 $Q_{rr}$ (C/cm$^2$)', fontsize=14, fontweight='bold')
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=14, fontweight='bold')
ax.set_title('图4 功率二极管载流子寿命Pareto前沿曲线\n$V_{bi}$与$Q_{rr}$的权衡关系', 
            fontsize=15, fontweight='bold', pad=20)

ax.grid(True, alpha=0.3, which='both', linestyle='--')
ax.set_xlim(3e-11, 5e-6)
ax.set_ylim(0.865, 0.885)

# 添加图例
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
               markersize=12, label='τ = 10 ns (超高速)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
               markersize=12, label='τ = 1 μs (平衡型)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
               markersize=12, label='τ = 100 μs (低损耗)'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=11, 
         framealpha=0.95, edgecolor='black')

plt.tight_layout()
plt.savefig('figures/final/fig4_pareto_front.png', dpi=300, bbox_inches='tight')
print("✓ 已保存图4: fig4_pareto_front.png")
plt.close()

# ============================================
# 图5：掺杂浓度权衡曲线（双坐标轴）
# ============================================
fig, ax1 = plt.subplots(figsize=(12, 8))

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

# 添加数据点标注
for i, (d, r, b) in enumerate(zip(dopings, rons_d, bvs)):
    # Ron标注（左侧）
    offset_r = 20 if i % 2 == 0 else -50
    ax1.annotate(f'{r:.2e}', xy=(d, r), xytext=(-40, offset_r),
                textcoords='offset points', fontsize=9, color='red',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='red', alpha=0.8))
    
    # BV标注（右侧）
    offset_b = 30 if i % 2 == 1 else -40
    ax2.annotate(f'{b:.0f}V', xy=(d, b), xytext=(40, offset_b),
                textcoords='offset points', fontsize=9, color='blue',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor='blue', alpha=0.8))

# 添加最优区域阴影
ax1.axvspan(1e16, 1e17, alpha=0.2, color='green', label='最优设计区域')

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2 + [plt.Rectangle((0,0),1,1, fc='green', alpha=0.2)],
          labels1 + labels2 + ['最优设计区 ($10^{16}-10^{17}$ cm$^{-3}$)'],
          loc='center left', fontsize=11, framealpha=0.95)

ax1.set_title('图5 功率二极管掺杂浓度权衡曲线\n$R_{on}$与$BV$的Pareto优化', 
             fontsize=15, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('figures/final/fig5_doping_tradeoff.png', dpi=300, bbox_inches='tight')
print("✓ 已保存图5: fig5_doping_tradeoff.png")
plt.close()

print("\n" + "="*70)
print("✅ 学术论文图表生成完成！")
print("="*70)
print("\n生成的图表列表:")
print("  📊 fig1_structure.png - 图1：一维PN结二极管结构示意图")
print("  📊 fig2_lifetime_effects.png - 图2：载流子寿命对器件特性的影响（4子图）")
print("  📊 fig3_doping_effects.png - 图3：掺杂浓度对器件特性的影响（3子图）")
print("  📊 fig4_pareto_front.png - 图4：Pareto前沿曲线")
print("  📊 fig5_doping_tradeoff.png - 图5：掺杂浓度权衡曲线")
print("="*70)
