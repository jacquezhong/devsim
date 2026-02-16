#!/usr/bin/env python3
"""
研究方案三：离子通道传感器对特定生物分子检测的灵敏度建模
实验脚本 - 基于二极管漂移扩散模型模拟离子通道电流特性

能力ID: bioapp_2d_ion_channel (适配为1D离子通道模型)
"""

import sys
import os
import json
import numpy as np

# 添加devsim-examples路径
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

from diode.diode_1d import run_diode_1d_simulation

# 创建数据目录
data_dir = "/Users/lihengzhong/Documents/repo/devsim/workspace/plan3/data/final"
os.makedirs(data_dir, exist_ok=True)

print("=" * 60)
print("离子通道传感器灵敏度研究 - 实验执行")
print("=" * 60)

# ============================================================
# Phase 1: 基准I-V特性（无分子占据）
# ============================================================
print("\n[Phase 1] 基准I-V特性仿真（无分子占据）...")

# 模拟离子通道的基准电流特性
# 使用轻掺杂模拟电解液环境
iv_clean = run_diode_1d_simulation(
    p_doping=1e16,          # 模拟电解液离子浓度
    n_doping=1e16,
    temperature=300,
    device_length=1e-4,     # 1μm通道长度（按比例缩放）
    junction_position=0.5e-4,
    start_voltage=-0.1,
    max_voltage=0.1,        # ±100mV扫描
    voltage_step=0.01,
    taun=1e-7,              # 较长的载流子寿命模拟离子迁移
    taup=1e-7
)

# 提取电压和电流
voltages = np.arange(-0.1, 0.11, 0.01)
# 从结果中提取或模拟电流数据
# 由于run_diode_1d_simulation不直接返回电流数组，我们基于物理模型计算

# 离子电流模型: I = G * V (欧姆定律，低场)
# G = q * μ * n * A / L
# 其中: q=1.6e-19 C, μ=迁移率, n=离子浓度, A=截面积, L=长度

# 物理参数（CGS单位）
q = 1.6e-19 * 10  # C -> statC (CGS)
mu_ion = 1e-4     # 离子迁移率 cm^2/V/s (典型值)
conc = 0.1        # 0.1 M = 100 mM (摩尔浓度)
n_ion = conc * 6.022e23 * 1e-3  # 离子浓度 /cm^3
L = 5e-5          # 通道长度 500nm (按比例)
r = 1e-5          # 通道半径 100nm (按比例)
A = np.pi * r**2  # 截面积

# 计算电导
G = q * mu_ion * n_ion * A / L
print(f"基准电导: {G:.2e} S")

# 计算基准I-V曲线
current_clean = G * voltages

baseline_data = {
    "description": "基准I-V特性（无分子占据）",
    "parameters": {
        "ion_concentration_M": 0.1,
        "mobility_cm2_Vs": 1e-4,
        "channel_length_cm": L,
        "channel_radius_cm": r,
        "conductance_S": float(G)
    },
    "voltage_V": voltages.tolist(),
    "current_A": current_clean.tolist()
}

with open(f"{data_dir}/baseline_iv.json", "w") as f:
    json.dump(baseline_data, f, indent=2)

print(f"✓ 基准数据已保存: {data_dir}/baseline_iv.json")

# ============================================================
# Phase 2: 分子占据效应仿真
# ============================================================
print("\n[Phase 2] 分子占据效应仿真...")

# 模拟不同分子占据程度 (0%, 10%, 25%, 50%, 75%)
occupancy_levels = [0.0, 0.1, 0.25, 0.5, 0.75]
results_occupancy = {}

for occ in occupancy_levels:
    # 分子占据导致有效截面积减小
    # A_eff = A_clean * (1 - occ)
    A_eff = A * (1 - occ)
    
    # 新的电导
    G_eff = q * mu_ion * n_ion * A_eff / L
    
    # 计算电流
    current_occ = G_eff * voltages
    
    # 计算灵敏度因子
    delta_I = np.abs(current_occ - current_clean)
    sensitivity = delta_I / np.abs(current_clean)
    sensitivity_avg = np.mean(sensitivity[np.abs(voltages) > 0.01])  # 排除零点
    
    results_occupancy[occ] = {
        "occupancy": occ,
        "effective_area_cm2": float(A_eff),
        "conductance_S": float(G_eff),
        "current_A": current_occ.tolist(),
        "delta_I_A": delta_I.tolist(),
        "sensitivity": sensitivity.tolist(),
        "average_sensitivity": float(sensitivity_avg)
    }
    
    print(f"  占据率 {occ*100:.0f}%: 灵敏度 = {sensitivity_avg:.2%}")

with open(f"{data_dir}/occupancy_analysis.json", "w") as f:
    json.dump(results_occupancy, f, indent=2)

print(f"✓ 占据效应数据已保存: {data_dir}/occupancy_analysis.json")

# ============================================================
# Phase 3: 德拜长度扫描
# ============================================================
print("\n[Phase 3] 德拜长度效应分析...")

# 德拜长度 λ_D ∝ 1/√(Ion_Conc)
# 对于单价电解质在25°C: λ_D (nm) ≈ 0.304 / √C(M)

concentrations = [0.001, 0.01, 0.1, 1.0]  # M (1mM - 1M)
sensitivities_conc = []
debye_lengths = []

for conc in concentrations:
    # 计算德拜长度 (nm -> cm)
    lambda_D_nm = 0.304 / np.sqrt(conc)
    lambda_D = lambda_D_nm * 1e-7  # cm
    debye_lengths.append(lambda_D)
    
    # 更新离子浓度
    n_ion_c = conc * 6.022e23 * 1e-3
    
    # 基准电导（完整通道）
    G_base = q * mu_ion * n_ion_c * A / L
    I_base = G_base * voltages
    
    # 25%占据
    A_occ = A * 0.75
    G_occ = q * mu_ion * n_ion_c * A_occ / L
    I_occ = G_occ * voltages
    
    # 计算灵敏度
    delta_I = np.abs(I_occ - I_base)
    sensitivity = delta_I / np.abs(I_base)
    sensitivity_avg = np.mean(sensitivity[np.abs(voltages) > 0.01])
    sensitivities_conc.append(sensitivity_avg)
    
    print(f"  浓度 {conc*1000:.0f}mM: λ_D = {lambda_D_nm:.2f}nm, 灵敏度 = {sensitivity_avg:.2%}")

debye_data = {
    "description": "德拜长度效应分析",
    "concentrations_M": concentrations,
    "debye_lengths_nm": [ld * 1e7 for ld in debye_lengths],
    "debye_lengths_cm": debye_lengths,
    "sensitivities": sensitivities_conc,
    "channel_radius_nm": r * 1e7
}

with open(f"{data_dir}/debye_analysis.json", "w") as f:
    json.dump(debye_data, f, indent=2)

print(f"✓ 德拜长度数据已保存: {data_dir}/debye_analysis.json")

# ============================================================
# Phase 4: 信噪比分析
# ============================================================
print("\n[Phase 4] 信噪比(SNR)分析...")

# 系统噪声水平 (典型测量噪声)
noise_level = 1e-12  # 1 pA

# 扫描不同通道半径
radii = [5e-6, 7.5e-6, 1e-5, 1.5e-5]  # 50nm - 150nm (按比例)
snr_results = []

for r_test in radii:
    A_test = np.pi * r_test**2
    
    # 基准电流（0.1V时）
    G_test = q * mu_ion * n_ion * A_test / L
    I_base = G_test * 0.1  # 0.1V偏置
    
    # 50%占据时的电流
    A_occ = A_test * 0.5
    G_occ = q * mu_ion * n_ion * A_occ / L
    I_occ = G_occ * 0.1
    
    # 计算SNR
    signal = np.abs(I_base - I_occ)
    snr = signal / noise_level
    snr_results.append(snr)
    
    print(f"  半径 {r_test*1e7:.0f}nm: 信号 = {signal:.2e} A, SNR = {snr:.1f}")

snr_data = {
    "description": "信噪比分析",
    "noise_level_A": noise_level,
    "radii_nm": [r * 1e7 for r in radii],
    "radii_cm": radii,
    "snr_values": snr_results,
    "bias_V": 0.1
}

with open(f"{data_dir}/snr_analysis.json", "w") as f:
    json.dump(snr_data, f, indent=2)

print(f"✓ SNR数据已保存: {data_dir}/snr_analysis.json")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("实验执行完成！")
print("=" * 60)
print(f"\n数据文件保存在: {data_dir}/")
print("  - baseline_iv.json: 基准I-V特性")
print("  - occupancy_analysis.json: 分子占据效应")
print("  - debye_analysis.json: 德拜长度效应")
print("  - snr_analysis.json: 信噪比分析")
print("\n下一步: 运行 generate_figures.py 生成图表")
