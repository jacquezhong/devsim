#!/usr/bin/env python3
"""
重新生成论文图表 - 去掉 matplotlib 中的标题，标题只在 Markdown 中
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
with open('data/final/lifetime_results.json', 'r') as f:
    lifetime_results = json.load(f)

with open('data/final/doping_results.json', 'r') as f:
    doping_results = json.load(f)

print("重新生成论文图表（去掉标题，只保留坐标轴标签）...")

# ============================================
# 图1：一维PN结二极管结构示意图
# ============================================
fig, ax = plt.subplots(figsize=(10, 6))

# P+区
p_region = plt.Rectangle((0, 0), 0.4, 1, linewidth=2, 
                         edgecolor='black', facecolor='lightblue', alpha=0.7)
ax.add_patch(p_region)
ax.text(0.2, 0.5, 'P+\n$N_A = 10^{16}-10^{18}$ cm$^{-3}$', 
        ha='center', va='center', fontsize=11, fontweight='bold')

# N区
n_region = plt.Rectangle((0.4, 0), 0.6, 1, linewidth=2, 
                         edgecolor='black', facecolor='lightyellow', alpha=0.7)
ax.add_patch(n_region)
ax.text(0.7, 0.5, 'N\n$N_D = 10^{19}$ cm$^{-3}$', 
        ha='center', va='center', fontsize=11, fontweight='bold')

# 结位置
ax.axvline(x=0.4, color='red', linewidth=3, linestyle='--')
ax.text(0.4, 1.05, 'PN结', ha='center', fontsize=10, color='red', fontweight='bold')

# 电极
ax.plot([0, 0], [0.3, 0.7], 'k-', linewidth=4)
ax.text(-0.05, 0.5, '阳极\n(A)', ha='right', va='center', fontsize=10, fontweight='bold')
ax.plot([1, 1], [0.3, 0.7], 'k-', linewidth=4)
ax.text(1.05, 0.5, '阴极\n(K)', ha='left', va='center', fontsize=10, fontweight='bold')

# 尺寸标注
ax.annotate('', xy=(0, -0.1), xytext=(1, -0.1),
            arrowprops=dict(arrowstyle='<->', color='black', lw=2))
ax.text(0.5, -0.15, '100 μm', ha='center', fontsize=10)

ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.25, 1.2)
ax.set_aspect('equal')
ax.axis('off')
# 不设置标题！标题在 Markdown 中

plt.tight_layout()
plt.savefig('figures/final/fig1_structure.png', dpi=300, bbox_inches='tight')
print("✓ 图1（无标题）: fig1_structure.png")
plt.close()

# ============================================
# 图2：载流子寿命影响（4子图，无总标题）
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

taus = [r['tau'] for r in lifetime_results]
vfs = [r['vf'] for r in lifetime_results]
currents = [r['current_density_A_cm2'] for r in lifetime_results]
rons = [r['r_on_ohm_cm2'] for r in lifetime_results]
qrrs = [r['qrr_C_cm2'] for r in lifetime_results]

# (a) 内建电势
ax = axes[0, 0]
ax.semilogx(taus, vfs, 'bo-', linewidth=2.5, markersize=10)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=12)
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=12)
ax.text(0.05, 0.95, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)
ax.set_ylim([0.85, 0.90])

# (b) 正向电流密度
ax = axes[0, 1]
ax.loglog(taus, currents, 'rs-', linewidth=2.5, markersize=10)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=12)
ax.set_ylabel('正向电流密度 $J_F$ (A/cm$^2$)', fontsize=12)
ax.text(0.05, 0.95, '(b)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# (c) 反向恢复电荷
ax = axes[1, 0]
ax.loglog(taus, qrrs, 'g^-', linewidth=2.5, markersize=10)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=12)
ax.set_ylabel('反向恢复电荷 $Q_{rr}$ (C/cm$^2$)', fontsize=12)
ax.text(0.05, 0.95, '(c)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# (d) 导通电阻
ax = axes[1, 1]
ax.loglog(taus, rons, 'mv-', linewidth=2.5, markersize=10)
ax.set_xlabel('载流子寿命 τ (s)', fontsize=12)
ax.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=12)
ax.text(0.05, 0.95, '(d)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# 不设置总标题！
plt.tight_layout()
plt.savefig('figures/final/fig2_lifetime_effects.png', dpi=300, bbox_inches='tight')
print("✓ 图2（无总标题）: fig2_lifetime_effects.png")
plt.close()

# ============================================
# 图3：掺杂浓度影响（3子图，无总标题）
# ============================================
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

dopings = [r['p_doping'] for r in doping_results]
vbis = [r['V_bi'] for r in doping_results]
rons_d = [r['r_on_ohm_cm2'] for r in doping_results]
bvs = [r['breakdown_voltage_V'] for r in doping_results]

# (a) 内建电势
ax = axes[0]
ax.semilogx(dopings, vbis, 'co-', linewidth=2.5, markersize=10)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=12)
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=12)
ax.text(0.05, 0.95, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# (b) 导通电阻
ax = axes[1]
ax.loglog(dopings, rons_d, 'yv-', linewidth=2.5, markersize=10)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=12)
ax.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=12)
ax.text(0.05, 0.95, '(b)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# (c) 击穿电压
ax = axes[2]
ax.loglog(dopings, bvs, 'bs-', linewidth=2.5, markersize=10)
ax.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=12)
ax.set_ylabel('击穿电压 $BV$ (V)', fontsize=12)
ax.text(0.05, 0.95, '(c)', transform=ax.transAxes, fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4)

# 不设置总标题！
plt.tight_layout()
plt.savefig('figures/final/fig3_doping_effects.png', dpi=300, bbox_inches='tight')
print("✓ 图3（无总标题）: fig3_doping_effects.png")
plt.close()

# ============================================
# 图4：Pareto前沿曲线（无标题）
# ============================================
fig, ax = plt.subplots(figsize=(12, 9))

qrrs_pareto = [r['qrr_C_cm2'] for r in lifetime_results]
vfs_pareto = [r['vf'] for r in lifetime_results]
taus_labels = ['10 ns', '100 ns', '1 μs', '10 μs', '100 μs']

ax.set_xscale('log')

colors = plt.cm.viridis(np.linspace(0, 1, len(taus)))
scatter = ax.scatter(qrrs_pareto, vfs_pareto, s=350, c=colors, 
                    edgecolors='black', linewidth=2.5, zorder=5)
ax.plot(qrrs_pareto, vfs_pareto, 'k--', alpha=0.4, linewidth=2)

# 添加标注
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
    textstr = f"{tau_label}\n$Q_{{rr}}$={q:.1e}\n$V_{{bi}}$={v:.3f}V"
    ax.annotate(textstr, xy=(q, v), xytext=ann['offset'],
                textcoords='offset points', ha=ann['ha'], va='center',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', 
                         edgecolor='black', linewidth=1.5, alpha=0.9),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.15',
                              color='black', linewidth=1.2), zorder=10)

# 区域标注
ax.axvspan(5e-11, 5e-10, alpha=0.15, color='blue', label='高速区')
ax.axvspan(5e-9, 5e-8, alpha=0.15, color='green', label='中速区')
ax.axvspan(5e-7, 5e-6, alpha=0.15, color='red', label='低速区')

ax.set_xlabel('反向恢复电荷 $Q_{rr}$ (C/cm$^2$)', fontsize=13)
ax.set_ylabel('内建电势 $V_{bi}$ (V)', fontsize=13)
ax.grid(True, alpha=0.3)
ax.set_xlim(3e-11, 5e-6)
ax.set_ylim(0.865, 0.885)
ax.legend(loc='upper right', fontsize=10)
# 不设置标题！标题在 Markdown 中

plt.tight_layout()
plt.savefig('figures/final/fig4_pareto_front.png', dpi=300, bbox_inches='tight')
print("✓ 图4（无标题）: fig4_pareto_front.png")
plt.close()

# ============================================
# 图5：掺杂浓度权衡（无标题）
# ============================================
fig, ax1 = plt.subplots(figsize=(12, 8))

line1 = ax1.loglog(dopings, rons_d, 'ro-', linewidth=3, markersize=12, 
                  markerfacecolor='lightcoral', markeredgecolor='darkred', 
                  markeredgewidth=2, label='$R_{on}$', zorder=5)
ax1.set_xlabel('P区掺杂浓度 $N_A$ (cm$^{-3}$)', fontsize=13)
ax1.set_ylabel('导通电阻 $R_{on}$ (Ω·cm$^2$)', fontsize=13, color='red')
ax1.tick_params(axis='y', labelcolor='red', labelsize=11)
ax1.grid(True, alpha=0.4)

ax2 = ax1.twinx()
line2 = ax2.loglog(dopings, bvs, 'bs--', linewidth=3, markersize=10, 
                  markerfacecolor='lightblue', markeredgecolor='darkblue', 
                  markeredgewidth=2, label='$BV$', zorder=4)
ax2.set_ylabel('击穿电压 $BV$ (V)', fontsize=13, color='blue')
ax2.tick_params(axis='y', labelcolor='blue', labelsize=11)
ax2.set_ylim([1, 5000])

# 数据标注
for i, (d, r, b) in enumerate(zip(dopings, rons_d, bvs)):
    offset_r = 20 if i % 2 == 0 else -50
    ax1.annotate(f'{r:.2e}', xy=(d, r), xytext=(-40, offset_r),
                textcoords='offset points', fontsize=9, color='red',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.8))
    offset_b = 30 if i % 2 == 1 else -40
    ax2.annotate(f'{b:.0f}V', xy=(d, b), xytext=(40, offset_b),
                textcoords='offset points', fontsize=9, color='blue',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='blue', alpha=0.8))

ax1.axvspan(1e16, 1e17, alpha=0.2, color='green', label='最优区')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)
# 不设置标题！标题在 Markdown 中

plt.tight_layout()
plt.savefig('figures/final/fig5_doping_tradeoff.png', dpi=300, bbox_inches='tight')
print("✓ 图5（无标题）: fig5_doping_tradeoff.png")
plt.close()

print("\n" + "="*70)
print("✅ 所有图表重新生成完成！（图片无标题，标题在Markdown中）")
print("="*70)
