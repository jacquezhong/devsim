#!/usr/bin/env python3
"""
生成图表脚本
绘制击穿电压与场板长度关系图、电场分布图等
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """加载实验数据"""
    data_file = 'data/final/breakdown_results.json'
    
    if not os.path.exists(data_file):
        print(f"错误: 数据文件 {data_file} 不存在")
        return None
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    return data


def plot_bv_vs_fp_length(data):
    """
    绘制击穿电压与场板长度关系图
    """
    print("\n生成图1: 击穿电压与场板长度关系")
    
    L_fp_list = []
    BV_list = []
    
    for result in data:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage']
        if BV is not None:
            L_fp_list.append(L_fp)
            BV_list.append(abs(BV))
    
    if len(L_fp_list) == 0:
        print("  无有效数据")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制数据点
    ax.plot(L_fp_list, BV_list, 'bo-', linewidth=2, markersize=10, label='Simulation Data')
    
    # 拟合曲线
    try:
        from scipy.optimize import curve_fit
        
        def bv_model(L, BV0, k, alpha):
            """击穿电压模型: BV = BV0 * (1 + k * L^alpha)"""
            return BV0 * (1 + k * np.power(L, alpha))
        
        popt, _ = curve_fit(bv_model, L_fp_list, BV_list, p0=[80, 0.1, 0.5])
        L_fit = np.linspace(min(L_fp_list), max(L_fp_list), 100)
        BV_fit = bv_model(L_fit, *popt)
        
        ax.plot(L_fit, BV_fit, 'r--', linewidth=2, 
                label=f'Fit: $BV = {popt[0]:.1f}(1+{popt[1]:.3f}L^{{ {popt[2]:.2f} }})$')
        
        print(f"  拟合参数: BV0={popt[0]:.1f}V, k={popt[1]:.4f}, α={popt[2]:.3f}")
    except ImportError:
        print("  未安装scipy，跳过拟合")
    except Exception as e:
        print(f"  拟合失败: {e}")
    
    ax.set_xlabel('Field Plate Length (μm)', fontsize=14)
    ax.set_ylabel('Breakdown Voltage (V)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12, loc='lower right')
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig('figures/final/fig1_bv_vs_fp_length.png', dpi=300, bbox_inches='tight')
    print("  ✓ 已保存: figures/final/fig1_bv_vs_fp_length.png")
    plt.close()


def plot_iv_curves(data):
    """
    绘制不同场板长度的I-V特性曲线
    选择代表性的场板长度进行展示，避免图例过于拥挤
    """
    print("\n生成图2: 反向I-V特性曲线")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # 选择代表性的场板长度（5个）：短、中短、中、中长、长
    selected_indices = [0, 4, 8, 12, 16]  # 对应 2.0, 4.0, 6.0, 8.0, 10.0 μm
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, idx in enumerate(selected_indices):
        if idx >= len(data):
            continue
        result = data[idx]
        L_fp = result['L_fp']
        voltages = np.array(result['voltages'])
        currents = np.array(result['currents'])
        
        if len(voltages) == 0:
            continue
        
        color = colors[i]
        
        # 线性坐标 - 只显示曲线，不显示marker避免拥挤
        ax1.plot(np.abs(voltages), np.abs(currents) * 1e6, 
                color=color, linewidth=2.5,
                label=f'$L_{{fp}}$ = {L_fp:.1f} μm')
        
        # 对数坐标
        ax2.semilogy(np.abs(voltages), np.abs(currents) * 1e6, 
                    color=color, linewidth=2.5,
                    label=f'$L_{{fp}}$ = {L_fp:.1f} μm')
    
    ax1.set_xlabel('Reverse Voltage (V)', fontsize=14)
    ax1.set_ylabel('Current (μA)', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11, loc='upper left')
    ax1.tick_params(labelsize=12)
    ax1.text(0.05, 0.95, '(a)', transform=ax1.transAxes, fontsize=14, 
             verticalalignment='top', fontweight='bold')
    
    ax2.set_xlabel('Reverse Voltage (V)', fontsize=14)
    ax2.set_ylabel('Current (μA)', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11, loc='lower right')
    ax2.tick_params(labelsize=12)
    ax2.text(0.05, 0.95, '(b)', transform=ax2.transAxes, fontsize=14, 
             verticalalignment='top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('figures/final/fig2_iv_curves.png', dpi=300, bbox_inches='tight')
    print("  ✓ 已保存: figures/final/fig2_iv_curves.png")
    plt.close()


def plot_electric_field(data):
    """
    绘制峰值电场与反向偏压关系
    选择代表性的场板长度进行展示
    """
    print("\n生成图3: 峰值电场分布")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 选择代表性的场板长度（5个）
    selected_indices = [0, 4, 8, 12, 16]  # 对应 2.0, 4.0, 6.0, 8.0, 10.0 μm
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, idx in enumerate(selected_indices):
        if idx >= len(data):
            continue
        result = data[idx]
        L_fp = result['L_fp']
        voltages = np.array(result['voltages'])
        e_fields = np.array(result['max_electric_fields'])
        
        if len(voltages) == 0:
            continue
        
        color = colors[i]
        
        ax.plot(np.abs(voltages), e_fields / 1e5, 
                color=color, linewidth=2.5,
                label=f'$L_{{fp}}$ = {L_fp:.1f} μm')
    
    # 添加临界电场线
    ax.axhline(y=3, color='black', linestyle='--', linewidth=2, 
               label='Critical Field (3×10⁵ V/cm)', alpha=0.7)
    
    ax.set_xlabel('Reverse Voltage (V)', fontsize=14)
    ax.set_ylabel('Peak Electric Field (10⁵ V/cm)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11, loc='upper left')
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig('figures/final/fig3_electric_field.png', dpi=300, bbox_inches='tight')
    print("  ✓ 已保存: figures/final/fig3_electric_field.png")
    plt.close()


def plot_bv_improvement(data):
    """
    绘制击穿电压提升百分比
    使用柱状图展示17个数据点的提升效果
    """
    print("\n生成图4: 击穿电压提升效果")
    
    L_fp_list = []
    BV_list = []
    
    for result in data:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage']
        if BV is not None:
            L_fp_list.append(L_fp)
            BV_list.append(abs(BV))
    
    if len(L_fp_list) < 2:
        print("  数据点不足")
        return
    
    # 计算相对于最小场板长度的提升
    BV_base = BV_list[0]  # 基准击穿电压 (最小场板长度)
    improvement = [(BV / BV_base - 1) * 100 for BV in BV_list]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 使用渐变色显示17个数据点
    import matplotlib.cm as cm
    colors = cm.viridis(np.linspace(0, 1, len(L_fp_list)))
    
    bars = ax.bar(L_fp_list, improvement, width=0.35, 
                   color=colors,
                   edgecolor='black', linewidth=0.5)
    
    # 在关键柱子上添加数值标签（只标注部分避免拥挤）
    key_indices = [0, 4, 8, 12, 16]  # 2.0, 4.0, 6.0, 8.0, 10.0 μm
    for idx in key_indices:
        if idx < len(bars):
            bar = bars[idx]
            imp = improvement[idx]
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'+{imp:.0f}%',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Field Plate Length (μm)', fontsize=14)
    ax.set_ylabel('Breakdown Voltage Improvement (%)', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(labelsize=11)
    
    # 设置x轴刻度
    ax.set_xticks(L_fp_list)
    ax.set_xticklabels([f'{x:.1f}' for x in L_fp_list], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('figures/final/fig4_bv_improvement.png', dpi=300, bbox_inches='tight')
    print("  ✓ 已保存: figures/final/fig4_bv_improvement.png")
    plt.close()


def generate_summary_table(data):
    """
    生成结果汇总表
    """
    print("\n生成结果汇总表...")
    
    summary = []
    
    for result in data:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage']
        max_E = max(result['max_electric_fields']) if result['max_electric_fields'] else 0
        
        summary.append({
            'L_fp': L_fp,
            'BV': abs(BV) if BV else None,
            'max_E': max_E
        })
    
    # 保存为JSON
    with open('data/final/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("  ✓ 已保存: data/final/summary.json")
    
    return summary


def main():
    """主函数"""
    
    print("=" * 70)
    print("图表生成")
    print("=" * 70)
    
    # 加载数据
    data = load_data()
    if data is None:
        print("\n错误: 无法加载数据")
        return
    
    print(f"\n加载了 {len(data)} 组实验数据")
    
    # 创建输出目录
    os.makedirs('figures/final', exist_ok=True)
    os.makedirs('data/final', exist_ok=True)
    
    # 生成图表
    plot_bv_vs_fp_length(data)
    plot_iv_curves(data)
    plot_electric_field(data)
    plot_bv_improvement(data)
    
    # 生成汇总表
    summary = generate_summary_table(data)
    
    print("\n" + "=" * 70)
    print("图表生成完成")
    print("=" * 70)
    print("\n生成的文件:")
    print("  - figures/final/fig1_bv_vs_fp_length.png")
    print("  - figures/final/fig2_iv_curves.png")
    print("  - figures/final/fig3_electric_field.png")
    print("  - figures/final/fig4_bv_improvement.png")
    print("  - data/final/summary.json")


if __name__ == '__main__':
    main()
