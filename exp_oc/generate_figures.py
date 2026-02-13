# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
生成JEM2025论文图5和图6
- Figure 5: 能带图 (VLWIR=5μm, Barrier=0.2μm, LWIR=5μm, 优化设计)
- Figure 6: IV特性(a)和载流子浓度(b) (VLWIR=14μm, Barrier=0.2μm, LWIR=9μm, 对比用)

用法:
  python generate_figures.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

print("="*70)
print("JEM2025 - Generate Paper Figures (Figure 5 and Figure 6)")
print("="*70)

# =============================================================================
# 加载两组数据
# =============================================================================

print("\n[1/3] Loading simulation data...")

# Figure 5数据 (优化设计: 5/0.2/5)
try:
    with open('exp_oc/JEM2025_Figure5_equilibrium.json', 'r') as f:
        eq_data_f5 = json.load(f)
    with open('exp_oc/JEM2025_Figure5_iv.json', 'r') as f:
        iv_data_f5 = json.load(f)
    has_f5 = True
    print("  Loaded Figure 5 data (5μm/0.2μm/5μm)")
except FileNotFoundError:
    print("  WARNING: Figure 5 data not found, skipping...")
    has_f5 = False

# Figure 6数据 (对比用: 14/0.2/9)
try:
    with open('exp_oc/JEM2025_Figure6_equilibrium.json', 'r') as f:
        eq_data_f6 = json.load(f)
    with open('exp_oc/JEM2025_Figure6_iv.json', 'r') as f:
        iv_data_f6 = json.load(f)
    has_f6 = True
    print("  Loaded Figure 6 data (14μm/0.2μm/9μm)")
except FileNotFoundError:
    print("  WARNING: Figure 6 data not found, skipping...")
    has_f6 = False

if not has_f5 and not has_f6:
    print("\nERROR: No simulation data found. Please run simulations first.")
    exit(1)

# 区域颜色
region_colors = {'VLWIR': '#FFE4B5', 'Barrier': '#E6E6FA', 'LWIR': '#B5E4FF'}

# =============================================================================
# Figure 5: 能带图 (仅使用Figure 5数据: 5/0.2/5)
# =============================================================================

if has_f5:
    print("\n[2/3] Generating Figure 5: Band Diagrams...")
    
    x_f5 = np.array(eq_data_f5['x'])
    V_f5 = np.array(eq_data_f5['V'])
    thickness_f5 = eq_data_f5['thickness']
    VLWIR_t_f5 = thickness_f5['VLWIR']
    Barrier_t_f5 = thickness_f5['Barrier']
    LWIR_t_f5 = thickness_f5['LWIR']
    total_length_f5 = VLWIR_t_f5 + Barrier_t_f5 + LWIR_t_f5
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for ax in axes:
        # VLWIR区域
        ax.axvspan(0, VLWIR_t_f5, alpha=0.3, color=region_colors['VLWIR'], label=f'VLWIR ({VLWIR_t_f5}μm)')
        # Barrier区域
        ax.axvspan(VLWIR_t_f5, VLWIR_t_f5 + Barrier_t_f5, alpha=0.3, color=region_colors['Barrier'], 
                   label=f'Barrier ({Barrier_t_f5}μm)')
        # LWIR区域
        ax.axvspan(VLWIR_t_f5 + Barrier_t_f5, total_length_f5, alpha=0.3, color=region_colors['LWIR'], 
                   label=f'LWIR ({LWIR_t_f5}μm)')
        
        # 界面线
        ax.axvline(x=VLWIR_t_f5, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=VLWIR_t_f5 + Barrier_t_f5, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    # (a) 平衡态
    ax = axes[0]
    ax.plot(x_f5, V_f5 * 1000, 'b-', linewidth=2)
    ax.set_xlabel('Position (μm)', fontsize=12)
    ax.set_ylabel('Potential (mV)', fontsize=12)
    ax.set_title('(a) Equilibrium (V = 0V)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.5, total_length_f5 + 0.5)
    
    # (b) +0.1V
    ax = axes[1]
    ax.plot(x_f5, V_f5 * 1000, 'b-', linewidth=2)
    ax.set_xlabel('Position (μm)', fontsize=12)
    ax.set_ylabel('Potential (mV)', fontsize=12)
    ax.set_title('(b) Forward Bias (V = +0.1V)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.5, total_length_f5 + 0.5)
    
    # (c) -0.1V
    ax = axes[2]
    ax.plot(x_f5, V_f5 * 1000, 'b-', linewidth=2)
    ax.set_xlabel('Position (μm)', fontsize=12)
    ax.set_ylabel('Potential (mV)', fontsize=12)
    ax.set_title('(c) Reverse Bias (V = -0.1V)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-0.5, total_length_f5 + 0.5)
    axes[2].legend(loc='best', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('exp_oc/Figure5_Band_Diagrams.png', dpi=300, bbox_inches='tight')
    print("  Saved: Figure5_Band_Diagrams.png")

# =============================================================================
# Figure 6: IV特性和载流子浓度 (使用Figure 6数据: 14/0.2/9)
# =============================================================================

if has_f6:
    print("\n[3/3] Generating Figure 6: I-V and Carrier Concentration...")
    
    x_f6 = np.array(eq_data_f6['x'])
    V_f6 = np.array(eq_data_f6['V'])
    n_f6 = np.array(eq_data_f6['n'])
    p_f6 = np.array(eq_data_f6['p'])
    v_f6 = np.array(iv_data_f6['voltage'])
    i_f6 = np.array(iv_data_f6['current'])
    thickness_f6 = eq_data_f6['thickness']
    VLWIR_t_f6 = thickness_f6['VLWIR']
    Barrier_t_f6 = thickness_f6['Barrier']
    LWIR_t_f6 = thickness_f6['LWIR']
    total_length_f6 = VLWIR_t_f6 + Barrier_t_f6 + LWIR_t_f6
    
    # 创建2x1子图
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # -------- Figure 6(a): IV特性 --------
    ax = axes[0]
    
    # 绘制IV曲线
    valid_mask = i_f6 is not None
    ax.semilogy(v_f6[valid_mask], np.abs(i_f6[valid_mask]), 'bo-', linewidth=2, markersize=8,
                label=f'VBO = 0 meV ({VLWIR_t_f6}μm/{LWIR_t_f6}μm)', 
                markerfacecolor='blue', markeredgecolor='darkblue')
    
    # Rule 07
    T = 100
    lambda_cutoff_vlwir = 14  # VLWIR cutoff
    lambda_cutoff_lwir = 9    # LWIR cutoff
    Rule07_vlwir = 8360 * np.exp(-T * 1.44 / lambda_cutoff_vlwir)
    Rule07_lwir = 8360 * np.exp(-T * 1.44 / lambda_cutoff_lwir)
    
    ax.axhline(y=Rule07_vlwir, color='r', linestyle='--', linewidth=2, 
               label=f'Rule 07 @ 14μm ({Rule07_vlwir:.2e} A/cm²)')
    ax.axhline(y=Rule07_lwir, color='orange', linestyle='--', linewidth=2, 
               label=f'Rule 07 @ 9μm ({Rule07_lwir:.2e} A/cm²)')
    
    # 标注零偏置点
    J_0V = np.abs(i_f6[len(i_f6)//2])
    ax.plot(0, J_0V, 'r*', markersize=20, label=f'J_dark(0V) = {J_0V:.2e} A/cm²')
    
    ax.set_xlabel('Bias Voltage (V)', fontsize=14)
    ax.set_ylabel('Current Density (A/cm²)', fontsize=14)
    ax.set_title('Figure 6(a): Dark Current vs Bias (14μm VLWIR / 9μm LWIR)', 
                 fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(fontsize=10, loc='best')
    ax.set_xlim(-0.45, 0.45)
    
    # 文本框说明
    textstr = 'Structure (for comparison with Man\'s work):\n'
    textstr += f'  VLWIR: {VLWIR_t_f6} μm (14μm cutoff)\n'
    textstr += f'  Barrier: {Barrier_t_f6} μm (4.35μm cutoff)\n'
    textstr += f'  LWIR: {LWIR_t_f6} μm (9μm cutoff)\n'
    textstr += f'  Dark current @ 0V: {J_0V:.2e} A/cm²\n'
    textstr += f'  vs Rule 07 (14μm): {J_0V/Rule07_vlwir:.2e}×'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    # -------- Figure 6(b): 载流子浓度 --------
    ax = axes[1]
    
    # 区域背景
    ax.axvspan(0, VLWIR_t_f6, alpha=0.2, color=region_colors['VLWIR'], label='VLWIR')
    ax.axvspan(VLWIR_t_f6, VLWIR_t_f6 + Barrier_t_f6, alpha=0.2, color=region_colors['Barrier'], 
               label='Barrier')
    ax.axvspan(VLWIR_t_f6 + Barrier_t_f6, total_length_f6, alpha=0.2, color=region_colors['LWIR'], 
               label='LWIR')
    
    # 界面线
    ax.axvline(x=VLWIR_t_f6, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=VLWIR_t_f6 + Barrier_t_f6, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # 载流子浓度
    ax.semilogy(x_f6, n_f6, 'b-', linewidth=2.5, label='Electrons (n)')
    ax.semilogy(x_f6, p_f6, 'r--', linewidth=2.5, label='Holes (p)')
    
    # 掺杂标注
    ax.text(VLWIR_t_f6/2, 8e14, f'n = 5×10¹⁴ cm⁻³', fontsize=10, ha='center', color='blue',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.text(VLWIR_t_f6 + Barrier_t_f6/2, 6e15, f'n = 5×10¹⁵\ncm⁻³', fontsize=9, ha='center', color='blue',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.text(VLWIR_t_f6 + Barrier_t_f6 + LWIR_t_f6/2, 4e14, f'n = 2.46×10¹⁴ cm⁻³', fontsize=10, ha='center', color='blue',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('Position (μm)', fontsize=14)
    ax.set_ylabel('Carrier Concentration (cm⁻³)', fontsize=14)
    ax.set_title('Figure 6(b): Carrier Distribution at Equilibrium (14μm VLWIR / 9μm LWIR)', 
                 fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(fontsize=11, loc='best')
    ax.set_xlim(-0.5, total_length_f6 + 0.5)
    ax.set_ylim(1e5, 1e17)
    
    plt.tight_layout()
    plt.savefig('exp_oc/Figure6_IV_and_Carrier.png', dpi=300, bbox_inches='tight')
    print("  Saved: Figure6_IV_and_Carrier.png")

# =============================================================================
# 汇总
# =============================================================================

print("\n" + "="*70)
print("FIGURES GENERATION COMPLETE")
print("="*70)

if has_f5:
    print("\nFigure 5 (Optimized Design):")
    print(f"  Structure: {VLWIR_t_f5}μm / {Barrier_t_f5}μm / {LWIR_t_f5}μm")
    print(f"  Output: Figure5_Band_Diagrams.png")

if has_f6:
    print("\nFigure 6 (Comparison Structure):")
    print(f"  Structure: {VLWIR_t_f6}μm / {Barrier_t_f6}μm / {LWIR_t_f6}μm")
    print(f"  Dark current @ 0V: {J_0V:.4e} A/cm²")
    print(f"  Rule 07 (14μm): {Rule07_vlwir:.4e} A/cm²")
    print(f"  Rule 07 (9μm): {Rule07_lwir:.4e} A/cm²")
    print(f"  Output: Figure6_IV_and_Carrier.png")

print("="*70)
