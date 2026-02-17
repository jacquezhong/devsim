#!/usr/bin/env python3
"""
Plan2: 生成图表
互连线寄生电容可视化
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def load_results():
    """加载仿真结果"""
    with open('/Users/lihengzhong/Documents/repo/devsim/workspace/plan2/data/final/capacitance_results.json', 'r') as f:
        return json.load(f)


def organize_data(results):
    """组织数据按介电常数分组"""
    data = {}
    for r in results:
        eps = r['permittivity']
        if eps not in data:
            data[eps] = {'spacing': [], 'C_total': [], 'C_coupling': [], 
                        'C_ground': [], 'k_coupling': [], 'C_left': [], 'C_right': []}
        data[eps]['spacing'].append(r['spacing_nm'])
        data[eps]['C_total'].append(r['C_center_total'])
        data[eps]['C_coupling'].append(r['C_coupling'])
        data[eps]['C_ground'].append(r['C_ground'])
        data[eps]['k_coupling'].append(r['coupling_coefficient'])
        data[eps]['C_left'].append(r['C_left'])
        data[eps]['C_right'].append(r['C_right'])
    
    # 按间距排序
    for eps in data:
        idx = np.argsort(data[eps]['spacing'])
        for key in data[eps]:
            data[eps][key] = np.array(data[eps][key])[idx]
    
    return data


def plot_capacitance_vs_spacing(data):
    """图1: 总电容和耦合电容随间距变化"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    colors = {3.9: '#1f77b4', 2.5: '#ff7f0e', 1.0: '#2ca02c'}
    labels = {3.9: r'$\varepsilon_r=3.9$ (SiO$_2$)', 
              2.5: r'$\varepsilon_r=2.5$ (Low-k)',
              1.0: r'$\varepsilon_r=1.0$ (Air)'}
    
    # (a) 总电容 vs 间距
    for eps in sorted(data.keys(), reverse=True):
        ax1.plot(data[eps]['spacing'], np.array(data[eps]['C_total'])*1e12, 
                'o-', linewidth=2, markersize=8, color=colors[eps], label=labels[eps])
    
    ax1.set_xlabel('Spacing (nm)', fontsize=12)
    ax1.set_ylabel('Total Capacitance (pF/cm)', fontsize=12)
    ax1.set_title('(a)', fontsize=14, loc='left')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(180, 520)
    
    # (b) 耦合电容 vs 间距
    for eps in sorted(data.keys(), reverse=True):
        ax2.plot(data[eps]['spacing'], np.array(data[eps]['C_coupling'])*1e12, 
                's-', linewidth=2, markersize=8, color=colors[eps], label=labels[eps])
    
    ax2.set_xlabel('Spacing (nm)', fontsize=12)
    ax2.set_ylabel('Coupling Capacitance (pF/cm)', fontsize=12)
    ax2.set_title('(b)', fontsize=14, loc='left')
    ax2.legend(fontsize=10, loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(180, 520)
    
    plt.tight_layout()
    plt.savefig('/Users/lihengzhong/Documents/repo/devsim/workspace/plan2/figures/final/fig1_capacitance_vs_spacing.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("图1已生成: fig1_capacitance_vs_spacing.png")


def plot_inverse_capacitance(data):
    """图2: 电容倒数与间距关系（验证C ∝ 1/S理论）"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = {3.9: '#1f77b4', 2.5: '#ff7f0e', 1.0: '#2ca02c'}
    labels = {3.9: r'$\varepsilon_r=3.9$ (SiO$_2$)', 
              2.5: r'$\varepsilon_r=2.5$ (Low-k)',
              1.0: r'$\varepsilon_r=1.0$ (Air)'}
    
    for eps in sorted(data.keys(), reverse=True):
        # 计算电容倒数
        inv_C = 1.0 / np.array(data[eps]['C_coupling'])
        spacing = np.array(data[eps]['spacing'])
        
        # 绘制数据点
        ax.plot(spacing, inv_C/1e12, '^-', linewidth=2, markersize=10, 
                color=colors[eps], label=labels[eps])
        
        # 线性拟合
        z = np.polyfit(spacing, inv_C/1e12, 1)
        p = np.poly1d(z)
        ax.plot(spacing, p(spacing), '--', linewidth=1.5, color=colors[eps], alpha=0.7)
    
    ax.set_xlabel('Spacing (nm)', fontsize=12)
    ax.set_ylabel('1/C_coupling (1/pF·cm)', fontsize=12)
    # 移除子图标签，因为图2只有一张图
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(180, 520)
    
    # 添加理论说明
    ax.text(0.95, 0.05, r'$C \propto 1/S$ relationship', 
            transform=ax.transAxes, fontsize=10, 
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('/Users/lihengzhong/Documents/repo/devsim/workspace/plan2/figures/final/fig2_inverse_capacitance.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("图2已生成: fig2_inverse_capacitance.png")


def plot_lowk_improvement(data):
    """图3: 低k介质的改进效果"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    spacing = data[3.9]['spacing']
    C_sio2 = np.array(data[3.9]['C_coupling'])
    C_lowk = np.array(data[2.5]['C_coupling'])
    C_air = np.array(data[1.0]['C_coupling'])
    
    improvement_lowk = (C_sio2 - C_lowk) / C_sio2 * 100
    improvement_air = (C_sio2 - C_air) / C_sio2 * 100
    
    # (a) 电容降低百分比
    x = np.arange(len(spacing))
    width = 0.35
    
    ax1.bar(x - width/2, improvement_lowk, width, label='Low-k (εr=2.5)', color='#ff7f0e', alpha=0.8)
    ax1.bar(x + width/2, improvement_air, width, label='Air gap (εr=1.0)', color='#2ca02c', alpha=0.8)
    
    ax1.set_xlabel('Spacing (nm)', fontsize=12)
    ax1.set_ylabel('Capacitance Reduction (%)', fontsize=12)
    ax1.set_title('(a)', fontsize=14, loc='left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(spacing)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # (b) 不同介电常数下的电容对比 (以300nm为例)
    eps_values = [3.9, 2.5, 1.0]
    spacing_300_idx = list(spacing).index(300) if 300 in spacing else 1
    C_at_300nm = [np.array(data[eps]['C_coupling'])[spacing_300_idx]*1e12 for eps in eps_values]
    
    bars = ax2.bar([r'$\varepsilon_r=3.9$', r'$\varepsilon_r=2.5$', r'$\varepsilon_r=1.0$'], 
                   C_at_300nm, color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    ax2.set_ylabel('Coupling Capacitance at 300nm (pF/cm)', fontsize=12)
    ax2.set_title('(b)', fontsize=14, loc='left')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for bar, val in zip(bars, C_at_300nm):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('/Users/lihengzhong/Documents/repo/devsim/workspace/plan2/figures/final/fig3_lowk_improvement.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("图3已生成: fig3_lowk_improvement.png")


def generate_summary_table(data):
    """生成数据摘要表格"""
    print("\n" + "="*70)
    print("仿真数据摘要")
    print("="*70)
    
    for eps in sorted(data.keys(), reverse=True):
        print(f"\n介电常数 εr = {eps}:")
        print("-" * 50)
        print(f"{'Spacing (nm)':<15} {'C_total (pF/cm)':<20} {'C_coupling (pF/cm)':<20} {'k_coupling':<15}")
        print("-" * 50)
        for i in range(len(data[eps]['spacing'])):
            print(f"{data[eps]['spacing'][i]:<15} {data[eps]['C_total'][i]*1e12:<20.3f} "
                  f"{data[eps]['C_coupling'][i]*1e12:<20.3f} {data[eps]['k_coupling'][i]:<15.3f}")
    
    print("\n" + "="*70)
    print("低k介质性能改进 (相对SiO2):")
    print("="*70)
    spacing = data[3.9]['spacing']
    for i in range(len(spacing)):
        C_sio2 = data[3.9]['C_coupling'][i]
        C_lowk = data[2.5]['C_coupling'][i]
        C_air = data[1.0]['C_coupling'][i]
        imp_lowk = (C_sio2 - C_lowk) / C_sio2 * 100
        imp_air = (C_sio2 - C_air) / C_sio2 * 100
        print(f"Spacing {spacing[i]}nm: Low-k改进 {imp_lowk:.1f}%, Air gap改进 {imp_air:.1f}%")


def main():
    """主函数"""
    print("="*70)
    print("生成Plan2图表")
    print("="*70)
    
    # 加载数据
    results = load_results()
    data = organize_data(results)
    
    # 生成图表
    plot_capacitance_vs_spacing(data)
    plot_inverse_capacitance(data)
    plot_lowk_improvement(data)
    
    # 打印摘要
    generate_summary_table(data)
    
    print("\n" + "="*70)
    print("所有图表生成完成！")
    print("="*70)


if __name__ == "__main__":
    main()
