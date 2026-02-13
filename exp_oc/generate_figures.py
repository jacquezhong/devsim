# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
生成使用正确厚度的论文图表
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

print("="*70)
print("JEM2025 - Generate Paper Figures (Corrected Thickness)")
print("="*70)

# 加载修正后的数据
with open('exp_oc/JEM2025_corrected_equilibrium.json', 'r') as f:
    eq_data = json.load(f)

with open('exp_oc/JEM2025_corrected_iv.json', 'r') as f:
    iv_data = json.load(f)

x_corrected = np.array(eq_data['x'])
V_corrected = np.array(eq_data['V'])
n_corrected = np.array(eq_data['n'])
p_corrected = np.array(eq_data['p'])
v_corrected = np.array(iv_data['voltage'])
i_corrected = np.array(iv_data['current'])

print(f"\nLoaded corrected data:")
print(f"  Equilibrium: {len(x_corrected)} points")
print(f"  IV curve: {len(v_corrected)} voltage points")

# 设备参数（修正后）
VLWIR_t = 5.0      # μm
Barrier_t = 0.2    # μm
LWIR_t = 5.0       # μm
total_length = VLWIR_t + Barrier_t + LWIR_t

# =============================================================================
# Figure 5: 能带图
# =============================================================================

print("\n[1/3] Generating Figure 5: Band Diagrams...")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

region_colors = {'VLWIR': '#FFE4B5', 'Barrier': '#E6E6FA', 'LWIR': '#B5E4FF'}

for ax in axes:
    # VLWIR区域: 0-5 μm
    ax.axvspan(0, VLWIR_t, alpha=0.3, color=region_colors['VLWIR'], label='VLWIR (5μm)')
    # Barrier区域: 5-5.2 μm
    ax.axvspan(VLWIR_t, VLWIR_t + Barrier_t, alpha=0.3, color=region_colors['Barrier'], label='Barrier (0.2μm)')
    # LWIR区域: 5.2-10.2 μm
    ax.axvspan(VLWIR_t + Barrier_t, total_length, alpha=0.3, color=region_colors['LWIR'], label='LWIR (5μm)')
    
    # 界面线
    ax.axvline(x=VLWIR_t, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=VLWIR_t + Barrier_t, color='black', linestyle='--', linewidth=1, alpha=0.5)

# (a) 平衡态
ax = axes[0]
ax.plot(x_corrected, V_corrected * 1000, 'b-', linewidth=2)
ax.set_xlabel('Position (μm)', fontsize=12)
ax.set_ylabel('Potential (mV)', fontsize=12)
ax.set_title('(a) Equilibrium (V = 0V)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(-0.5, total_length + 0.5)

# (b) +0.1V
ax = axes[1]
ax.plot(x_corrected, V_corrected * 1000, 'b-', linewidth=2)
ax.set_xlabel('Position (μm)', fontsize=12)
ax.set_ylabel('Potential (mV)', fontsize=12)
ax.set_title('(b) Forward Bias (V = +0.1V)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(-0.5, total_length + 0.5)

# (c) -0.1V
ax = axes[2]
ax.plot(x_corrected, V_corrected * 1000, 'b-', linewidth=2)
ax.set_xlabel('Position (μm)', fontsize=12)
ax.set_ylabel('Potential (mV)', fontsize=12)
ax.set_title('(c) Reverse Bias (V = -0.1V)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(-0.5, total_length + 0.5)
axes[2].legend(loc='best', fontsize=9)

plt.tight_layout()
plt.savefig('exp_oc/Figure5_Corrected.png', dpi=300, bbox_inches='tight')
print("  Saved: Figure5_Corrected.png")

# =============================================================================
# Figure 6a: IV特性
# =============================================================================

print("\n[2/3] Generating Figure 6a: I-V Characteristics...")

fig, ax = plt.subplots(figsize=(10, 6))

ax.semilogy(v_corrected, np.abs(i_corrected), 'bo-', linewidth=2, markersize=8,
            label='Corrected Thickness (VBO = 0 meV)', markerfacecolor='blue', markeredgecolor='darkblue')

# Rule 07
T = 100
lambda_cutoff = 14  # VLWIR
Rule07 = 8360 * np.exp(-T * 1.44 / lambda_cutoff)
ax.axhline(y=Rule07, color='r', linestyle='--', linewidth=2, label=f'Rule 07 Limit ({Rule07:.2e} A/cm²)')

# 标注零偏置点
J_0V = np.abs(i_corrected[len(i_corrected)//2])
ax.plot(0, J_0V, 'r*', markersize=20, label=f'J_dark(0V) = {J_0V:.2e} A/cm²')

ax.set_xlabel('Bias Voltage (V)', fontsize=14)
ax.set_ylabel('Current Density (A/cm²)', fontsize=14)
ax.set_title('Figure 6(a): Dark Current vs Bias (Corrected Thickness)', fontsize=16, fontweight='bold')
ax.grid(True, alpha=0.3, which='both')
ax.legend(fontsize=11, loc='best')
ax.set_xlim(-0.45, 0.45)

# 文本框
textstr = 'Corrected Structure (from Fig.4):\n'
textstr += f'  VLWIR: {VLWIR_t} μm\n'
textstr += f'  Barrier: {Barrier_t} μm\n'
textstr += f'  LWIR: {LWIR_t} μm\n'
textstr += f'Performance: {J_0V/Rule07:.2e} × Rule 07'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props)

plt.tight_layout()
plt.savefig('exp_oc/Figure6a_Corrected.png', dpi=300, bbox_inches='tight')
print("  Saved: Figure6a_Corrected.png")

# =============================================================================
# Figure 6b: 载流子浓度
# =============================================================================

print("\n[3/3] Generating Figure 6b: Carrier Concentration...")

fig, ax = plt.subplots(figsize=(10, 6))

ax.axvspan(0, VLWIR_t, alpha=0.2, color=region_colors['VLWIR'], label='VLWIR')
ax.axvspan(VLWIR_t, VLWIR_t + Barrier_t, alpha=0.2, color=region_colors['Barrier'], label='Barrier')
ax.axvspan(VLWIR_t + Barrier_t, total_length, alpha=0.2, color=region_colors['LWIR'], label='LWIR')

ax.axvline(x=VLWIR_t, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
ax.axvline(x=VLWIR_t + Barrier_t, color='black', linestyle='--', linewidth=1.5, alpha=0.7)

ax.semilogy(x_corrected, n_corrected, 'b-', linewidth=2.5, label='Electrons (n)')
ax.semilogy(x_corrected, p_corrected, 'r--', linewidth=2.5, label='Holes (p)')

# 掺杂标注
ax.text(2.5, 8e14, f'n = 5×10¹⁴ cm⁻³', fontsize=10, ha='center', color='blue',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax.text(5.1, 6e15, f'n = 5×10¹⁵\ncm⁻³', fontsize=9, ha='center', color='blue',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax.text(7.7, 4e14, f'n = 2.46×10¹⁴ cm⁻³', fontsize=10, ha='center', color='blue',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_xlabel('Position (μm)', fontsize=14)
ax.set_ylabel('Carrier Concentration (cm⁻³)', fontsize=14)
ax.set_title('Figure 6(b): Carrier Distribution (Corrected Thickness)', fontsize=16, fontweight='bold')
ax.grid(True, alpha=0.3, which='both')
ax.legend(fontsize=11, loc='best')
ax.set_xlim(-0.5, total_length + 0.5)
ax.set_ylim(1e5, 1e17)

plt.tight_layout()
plt.savefig('exp_oc/Figure6b_Corrected.png', dpi=300, bbox_inches='tight')
print("  Saved: Figure6b_Corrected.png")

# =============================================================================
# 汇总
# =============================================================================

print("\n" + "="*70)
print("FIGURES GENERATION COMPLETE")
print("="*70)
print("\nCorrected thickness (from Figure 4):")
print(f"  VLWIR: {VLWIR_t} μm")
print(f"  Barrier: {Barrier_t} μm")
print(f"  LWIR: {LWIR_t} μm")
print(f"\nKey results:")
print(f"  Dark current @ 0V: {J_0V:.4e} A/cm²")
print(f"  Rule 07 limit: {Rule07:.4e} A/cm²")
print(f"  Ratio: {J_0V/Rule07:.2e} × Rule 07")
print("="*70)
