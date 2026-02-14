# 智能网格策略使用文档

## 概述

`devsim-examples` 现已集成 `devsim-simulation` 的物理驱动网格原则，支持根据器件物理参数自动优化网格密度。

## 快速开始

### 方式1: 使用参数开关（最简单）

```python
from devsim_examples.diode.diode_1d import run_diode_1d_simulation

# 使用智能网格
result = run_diode_1d_simulation(
    p_doping=1e18,
    n_doping=1e16,
    use_intelligent_mesh=True  # 启用智能网格
)

# 查看使用的网格密度
if 'intelligent_mesh' in result:
    print(f"优化网格密度: {result['intelligent_mesh']['mesh_density_cm']:.2e} cm")
```

### 方式2: 直接使用网格策略

```python
from devsim_examples.common.mesh_strategies import (
    MeshPolicy, 
    DiodeMeshStrategy,
    get_intelligent_mesh_params
)

# 方法A: 获取优化后的参数
params = get_intelligent_mesh_params(
    'diode_1d_dc_iv',
    p_doping=1e18,
    n_doping=1e16
)
print(f"建议网格密度: {params['mesh_density']:.2e} cm")

# 方法B: 完整策略对象
policy = MeshPolicy()
strategy = DiodeMeshStrategy(policy)

mesh_params = strategy.create_1d_mesh_params(
    p_doping=1e18,
    n_doping=1e16,
    temperature=300,
    device_length=1e-5,
    junction_position=0.5e-5,
    max_voltage=0.5
)
```

## 网格原则

### 当前实现的原则（来自 devsim-simulation）

```yaml
物理驱动网格:
  # 1. 高梯度区原则
  high_gradient_threshold: 0.5  # E-field > 0.5V/μm 或掺杂梯度 > 2 orders/μm
  gradient_mesh_factor: 0.1     # 高梯度区网格加密因子
  
  # 2. 边界原则
  boundary_refinement: True
  boundary_layers: 3            # 边界附近加密层数
  boundary_factor: 0.2          # 边界网格相对于体区的比例
  
  # 3. 特征尺寸原则
  min_nodes_per_layer: 10       # 薄层至少10个节点
  layer_thickness_threshold: 0.1e-4  # < 0.1μm 视为薄层
  
  # 4. 默认网格密度
  default_mesh_density: 1e-7    # 默认0.1 μm
  min_mesh_spacing: 1e-9        # 最小0.01 nm（物理极限）
  max_mesh_spacing: 1e-4        # 最大1 μm
```

## 支持的能力标识

| 能力标识 | 智能网格支持 | 说明 |
|---------|------------|------|
| `diode_1d_dc_iv` | ✅ | 1D二极管DC IV，基于掺杂梯度优化 |
| `diode_1d_transient` | ✅ | 1D二极管瞬态，同上 |
| `diode_1d_ssac_cv` | ✅ | 1D二极管AC分析，同上 |
| `diode_2d_dc_iv` | ✅ | 2D二极管，X方向优化 |
| `capacitance_1d_electrostatic` | ⚠️ | 使用默认网格 |
| `capacitance_2d_electrostatic` | ⚠️ | 使用默认网格 |
| `mos_2d_gmsh_mobility` | ❌ | 需要Gmsh预生成网格 |
| 其他 | ⚠️ | 返回默认网格密度 |

## 扩展方法

### 1. 添加新的网格原则

在 `devsim-simulation` 中更新原则后，在这里注册：

```python
from devsim_examples.common.mesh_strategies import register_mesh_principle

# 注册新原则
register_mesh_principle('quantum_refinement', True)
register_mesh_principle('quantum_spacing', 1e-10)
```

### 2. 为新能力添加网格策略

```python
from devsim_examples.common.mesh_strategies import register_capability_strategy

def my_mos_strategy(**kwargs):
    """自定义MOS网格策略"""
    gate_length = kwargs.get('gate_length', 1e-4)
    return {
        'mesh_density': gate_length / 20,  # 栅长至少20个节点
        'custom_param': True
    }

# 注册策略
register_capability_strategy('mos_2d_custom', my_mos_strategy)

# 使用
params = get_intelligent_mesh_params('mos_2d_custom', gate_length=5e-5)
```

### 3. 自定义策略类

继承 `MeshPolicy` 实现特定原则：

```python
from devsim_examples.common.mesh_strategies import MeshPolicy

class QuantumMeshPolicy(MeshPolicy):
    """量子效应网格策略"""
    
    DEFAULT_PRINCIPLES = {
        **MeshPolicy.DEFAULT_PRINCIPLES,
        'quantum_refinement': True,
        'quantum_spacing': 1e-10,  # 10Å for quantum wells
    }
    
    def calculate_mesh_density(self, region, physics):
        # 先调用父类方法
        spacing = super().calculate_mesh_density(region, physics)
        
        # 添加量子效应判断
        if self.principles.get('quantum_refinement'):
            quantum_spacing = self.principles['quantum_spacing']
            spacing = min(spacing, quantum_spacing)
        
        return spacing
```

## 实现架构

```
devsim-simulation/          (原则定义)
└── SKILL.md
    └── 网格生成原则 (物理驱动)
        
devsim-examples/
├── common/
│   └── mesh_strategies.py  ← 原则实现
│       ├── MeshPolicy      ← 基础策略类
│       ├── DiodeMeshStrategy  ← 二极管专用
│       └── get_intelligent_mesh_params()  ← 便捷接口
│
├── diode/
│   └── diode_1d.py         ← 集成智能网格
│       └── use_intelligent_mesh 参数
│
└── CAPABILITY_INDEX.md     ← 更新能力索引
```

## 使用建议

### 1. 何时使用智能网格？

**推荐使用**:
- 高掺杂梯度 (> 2 orders)
- 薄层结构 (< 0.1μm)
- 高电场区 (> 0.5 V/μm)
- 首次仿真，不确定合适的网格密度

**可不用**:
- 已有经验网格参数
- 简单对称结构
- 需要严格控制网格节点数（调试时）

### 2. 网格密度参考

| 应用场景 | 建议网格密度 | 说明 |
|---------|------------|------|
| 一般PN结 | 1e-8 - 1e-7 cm | 标准二极管 |
| 高掺杂梯度 | 1e-9 - 1e-8 cm | 重掺杂/轻掺杂突变 |
| 薄氧化层 | 1e-9 cm | MOS栅氧化层 |
| 量子阱 | 1e-10 cm | 量子效应区域 |

### 3. 验证网格质量

```python
# 仿真后检查网格相关指标
result = run_diode_1d_simulation(use_intelligent_mesh=True)

if result['converged']:
    print("✓ 网格合适，收敛良好")
else:
    print("✗ 可能需要更密的网格")
    # 可手动调整 mesh_density 再次尝试
```

## 示例脚本

运行完整示例：

```bash
cd /Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples
python examples_mesh_intelligent.py
```

## 注意事项

1. **静态网格**: DEVSIM 使用静态网格，智能网格仅在仿真前优化初始网格
2. **收敛性**: 智能网格提高收敛概率，但不保证一定收敛
3. **计算成本**: 更密的网格增加计算时间，需要在精度和效率间权衡
4. **扩展依赖**: 使用智能网格需要 `mesh_strategies.py` 模块（已包含）
