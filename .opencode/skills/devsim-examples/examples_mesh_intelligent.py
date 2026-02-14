#!/usr/bin/env python3
"""
DEVSIM 智能网格使用示例

此示例展示如何使用 devsim-simulation 的网格原则自动优化 devsim-examples 的网格
"""

import sys
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

from common.mesh_strategies import (
    get_intelligent_mesh_params,
    MeshPolicy,
    DiodeMeshStrategy,
)

# 仅在 DEVSIM 可用时导入仿真函数
try:
    from diode.diode_1d import run_diode_1d_simulation
    DEVSIM_AVAILABLE = True
except ImportError:
    DEVSIM_AVAILABLE = False
    print("注意: DEVSIM 未安装，示例仅展示网格策略功能")


def example_1_basic_usage():
    """示例1: 基本使用（对比默认 vs 智能网格）"""
    if not DEVSIM_AVAILABLE:
        print("\n跳过示例1（需要 DEVSIM）")
        return
        
    print("=" * 60)
    print("示例1: 默认网格 vs 智能网格")
    print("=" * 60)
    
    # 高掺杂梯度场景
    p_doping = 1e20  # 重掺杂
    n_doping = 1e15  # 轻掺杂
    
    print(f"\n场景: p_doping={p_doping:.0e}, n_doping={n_doping:.0e}")
    print(f"掺杂梯度: {abs(p_doping - n_doping):.0e} orders/μm")
    
    # 使用默认网格
    print("\n[默认网格]")
    result_default = run_diode_1d_simulation(
        p_doping=p_doping,
        n_doping=n_doping,
        max_voltage=0.1,  # 降低电压防止高掺杂下的高电流
        voltage_step=0.02,
        use_intelligent_mesh=False
    )
    print(f"仿真结果: converged={result_default['converged']}")
    
    # 使用智能网格
    print("\n[智能网格]")
    result_smart = run_diode_1d_simulation(
        p_doping=p_doping,
        n_doping=n_doping,
        max_voltage=0.1,
        voltage_step=0.02,
        use_intelligent_mesh=True
    )
    print(f"仿真结果: converged={result_smart['converged']}")
    if 'intelligent_mesh' in result_smart:
        print(f"优化网格密度: {result_smart['intelligent_mesh']['mesh_density_cm']:.2e} cm")


def example_2_direct_strategy():
    """示例2: 直接使用网格策略"""
    print("\n" + "=" * 60)
    print("示例2: 直接使用 MeshPolicy 和 DiodeMeshStrategy")
    print("=" * 60)
    
    # 创建网格策略
    policy = MeshPolicy()
    strategy = DiodeMeshStrategy(policy)
    
    # 计算不同掺杂组合的网格参数
    test_cases = [
        (1e18, 1e18),  # 对称掺杂
        (1e20, 1e15),  # 高梯度
        (1e16, 1e16),  # 低掺杂
    ]
    
    for p, n in test_cases:
        params = strategy.create_1d_mesh_params(
            p_doping=p,
            n_doping=n,
            temperature=300,
            device_length=1e-5,
            junction_position=0.5e-5,
            max_voltage=0.5
        )
        
        print(f"\np={p:.0e}, n={n:.0e}:")
        print(f"  网格密度: {params['mesh_density']:.2e} cm")
        print(f"  器件长度: {params['device_length']:.2e} cm")


def example_3_custom_principles():
    """示例3: 自定义网格原则"""
    print("\n" + "=" * 60)
    print("示例3: 自定义网格原则")
    print("=" * 60)
    
    # 创建自定义原则（更严格）
    custom_principles = {
        'high_gradient_threshold': 0.1,  # 更低的梯度阈值
        'gradient_mesh_factor': 0.05,    # 更密的网格
        'min_nodes_per_layer': 20,       # 薄层更多节点
    }
    
    custom_policy = MeshPolicy(principles=custom_principles)
    custom_strategy = DiodeMeshStrategy(custom_policy)
    
    # 对比默认和自定义
    p_doping, n_doping = 1e19, 1e16
    
    # 默认
    default_params = get_intelligent_mesh_params(
        'diode_1d_dc_iv',
        p_doping=p_doping,
        n_doping=n_doping
    )
    
    # 自定义
    custom_params = custom_strategy.create_1d_mesh_params(
        p_doping=p_doping,
        n_doping=n_doping
    )
    
    print(f"\n掺杂: p={p_doping:.0e}, n={n_doping:.0e}")
    print(f"默认网格密度:  {default_params['mesh_density']:.2e} cm")
    print(f"自定义网格密度: {custom_params['mesh_density']:.2e} cm")


def example_4_capability_based():
    """示例4: 基于能力标识的网格参数获取"""
    print("\n" + "=" * 60)
    print("示例4: 基于能力标识获取网格参数")
    print("=" * 60)
    
    # 二极管能力
    params_1d = get_intelligent_mesh_params(
        'diode_1d_dc_iv',
        p_doping=1e18,
        n_doping=1e16
    )
    print(f"\n1D二极管网格密度: {params_1d['mesh_density']:.2e} cm")
    
    # 尝试其他能力
    params_2d = get_intelligent_mesh_params(
        'diode_2d_dc_iv',
        p_doping=1e18,
        n_doping=1e16,
        device_width=1e-5,
        device_height=1e-5
    )
    print(f"2D二极管网格密度: {params_2d['mesh_density']:.2e} cm")
    
    # 不支持的能力
    params_unknown = get_intelligent_mesh_params(
        'unknown_capability'
    )
    print(f"未知能力: {params_unknown.get('warning', 'N/A')}")


def main():
    """主函数"""
    print("DEVSIM 智能网格使用示例")
    print("=" * 60)
    
    try:
        example_2_direct_strategy()
        example_4_capability_based()
        
        # 注意：example_1 和 example_3 需要 DEVSIM 环境才能运行
        # example_1_basic_usage()
        # example_3_custom_principles()
        
        print("\n" + "=" * 60)
        print("示例完成！")
        print("=" * 60)
        print("\n注意: example_1 和 example_3 需要安装 DEVSIM 才能实际运行仿真")
        print("当前示例展示了如何获取优化的网格参数")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
