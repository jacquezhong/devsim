# DEVSIM Examples 能力索引

本文档用于研究计划引用，精确说明每个能力标识的输入输出。

## 能力标识快速索引

| 能力标识 | 维度 | 主要物理 | 输入参数示例 | 输出结果 |
|---------|------|---------|-------------|---------|
| diode_1d_dc_iv | 1D | 漂移扩散+SRH | n_doping, p_doping, temperature, max_voltage | IV曲线, Tecplot文件 |
| diode_2d_dc_iv | 2D | 漂移扩散+SRH | device_width, device_height, junction_x | 2D场分布, IV曲线 |
| diode_1d_transient | 1D | 瞬态漂移扩散 | dc_voltage, time_step, total_time | 时间-电流曲线 |
| diode_1d_ssac_cv | 1D | 小信号AC | frequency, voltage_range | C-V曲线 |
| capacitance_1d_electrostatic | 1D | 泊松方程 | permittivity, device_length | 电容值, 电势分布 |
| capacitance_2d_electrostatic | 2D | 泊松方程 | geometry, permittivity | 电容值(含边缘), 2D场分布 |
| mos_2d_gmsh_mobility | 2D | 漂移扩散+迁移率 | gate_bias, drain_bias | Id-Vg, Id-Vd曲线 |
| bioapp_2d_ion_channel | 2D | 泊松方程+电荷 | voltage, dna_charge_density | 电势分布, DNA检测 |
| bioapp_3d_nerve_signal | 3D | 泊松方程+电荷 | voltage, dna_charge_density | 3D电势分布 |
| magnetic_3d_twowire | 3D | 矢量势方程 | jz_left, jz_right, mu | B场分布, 矢量势 |

---

## 详细能力规范

### diode_1d_dc_iv

**用途**: 一维PN结二极管DC IV特性仿真

**必需参数**:
```yaml
p_doping: float      # p区掺杂浓度 (cm^-3), 默认: 1e18
n_doping: float      # n区掺杂浓度 (cm^-3), 默认: 1e18
temperature: float   # 温度 (K), 默认: 300
```

**可选参数**:
```yaml
device_length: float        # 器件长度 (cm), 默认: 1e-5
junction_position: float    # 结位置 (cm), 默认: 0.5e-5
mesh_density: float         # 结区网格 (cm), 默认: 1e-9
taun: float                # 电子寿命 (s), 默认: 1e-8
taup: float                # 空穴寿命 (s), 默认: 1e-8
max_voltage: float         # 最大偏置 (V), 默认: 0.5
voltage_step: float        # 偏置步长 (V), 默认: 0.1
```

**输出**:
- 文件: `diode_1d.dat` (Tecplot格式)
- 数据: 各偏置点的电流值
- 结构: 完整的器件状态（电势、载流子浓度）

**能力边界**:
- 温度范围: 250K-400K
- 偏置范围: -1V至1V（建议）
- 掺杂范围: 1e15 - 1e20 cm^-3

---

### diode_2d_dc_iv

**用途**: 二维PN结二极管DC IV特性仿真

**必需参数**:
```yaml
p_doping: float      # p区掺杂 (cm^-3)
n_doping: float      # n区掺杂 (cm^-3)
temperature: float   # 温度 (K)
```

**可选参数**:
```yaml
device_width: float     # 器件宽度 (cm), 默认: 1e-5
device_height: float    # 器件高度 (cm), 默认: 1e-5
junction_x: float       # 结x位置 (cm), 默认: 0.5e-5
mesh_density: float     # 网格密度 (cm), 默认: 1e-8
```

**输出**:
- 文件: `diode_2d.dat` (Tecplot格式)
- 数据: 2D场分布 + IV曲线

---

### diode_1d_transient

**用途**: 一维二极管瞬态响应

**必需参数**:
```yaml
dc_voltage: float    # DC偏置电压 (V)
time_step: float     # 时间步长 (s)
total_time: float    # 总仿真时间 (s)
```

**可选参数**:
```yaml
p_doping: float      # 默认: 1e18
n_doping: float      # 默认: 1e18
temperature: float   # 默认: 300
```

**输出**:
- 数据: 各时间点的电路节点值
- 电流随时间变化

---

### diode_1d_ssac_cv

**用途**: 一维二极管小信号AC分析

**必需参数**:
```yaml
frequency: float     # AC频率 (Hz), 默认: 1.0
start_voltage: float  # 起始偏置 (V), 默认: 0.0
max_voltage: float   # 最大偏置 (V), 默认: 0.5
```

**可选参数**:
```yaml
voltage_step: float  # 步长 (V), 默认: 0.1
```

**输出**:
- 数据: C-V曲线（各偏置点的电容值）

**计算原理**:
```
C = I_imag / (2πfV)
```

---

### capacitance_1d_electrostatic

**用途**: 一维静电场电容计算

**必需参数**:
```yaml
device_length: float    # 器件长度 (cm)
permittivity: float     # 介电常数 (F/cm)
```

**可选参数**:
```yaml
contact1_bias: float    # 接触1偏置 (V), 默认: 1.0
contact2_bias: float    # 接触2偏置 (V), 默认: 0.0
mesh_spacing: float     # 网格间距 (cm)
```

**输出**:
- 电容值 (F/cm^2)
- 接触电荷
- 电势分布

**理论验证**:
```
C = ε * A / d
```

---

### capacitance_2d_electrostatic

**用途**: 二维静电场电容（含边缘效应）

**必需参数**:
```yaml
# 几何坐标 (um)
xmin, x1, x2, x3, x4, xmax: float
ymin, y1, y2, y3, y4, ymax: float
permittivity: float     # 介电常数 (F/cm)
```

**可选参数**:
```yaml
top_bias: float         # 上电极偏置 (V), 默认: 1.0
bot_bias: float         # 下电极偏置 (V), 默认: 0.0
```

**输出**:
- 电容值（含边缘效应）
- 2D电势分布
- VTK格式（Paraview可视化）

---

### mos_2d_gmsh_mobility

**用途**: 2D MOS结构迁移率模型仿真

**前提条件**:
- 需要 `gmsh_mos2d.msh` 网格文件

**必需参数**:
```yaml
device_name: str        # 器件名称, 默认: "mos2d"
silicon_regions: tuple  # 硅区域, 默认: ("gate", "bulk")
oxide_regions: tuple   # 氧化层区域, 默认: ("oxide",)
interfaces: tuple       # 界面, 默认: ("bulk_oxide", "gate_oxide")
```

**可选参数**:
```yaml
temperature: float          # 默认: 300
gate_bias_stop: float       # 默认: 0.5
gate_bias_step: float       # 默认: 0.05
drain_bias_stop: float      # 默认: 0.5
drain_bias_step: float      # 默认: 0.1
```

**输出**:
- Id-Vg曲线（转移特性）
- Id-Vd曲线（输出特性）
- 载流子浓度分布
- 电势分布

**前置条件**:
- 需要 `gmsh_mos2d.msh` 网格文件

---

### bioapp_2d_ion_channel

**用途**: 2D生物电离子通道/DNA检测仿真

**必需参数**:
```yaml
voltage: float                # 外加电压 (V), 默认: 1.0
dna_charge_density: float    # DNA电荷密度 (/cm^3), 默认: 2e21
```

**可选参数**:
```yaml
zero_charge_first: bool      # 是否先求解零电荷参考, 默认: True
mesh_file: str               # 网格文件名, 默认: "disk_2d.msh"
relative_error: float        # 默认: 1e-7
absolute_error: float        # 默认: 1e11
max_iterations: int          # 默认: 100
```

**输出**:
- 电势分布（Tecplot格式）
- LogDeltaPotential（电势变化对数）
- 接触电流

**前置条件**:
- 需要 `disk_2d.msh` 网格文件
- 可选依赖: `bioapp1_common` 模块

**能力边界**:
- ✅ DNA纳米孔检测
- ✅ 离子通道电流
- ✅ 多区域多界面
- ❌ 需要预生成Gmsh网格

---

### bioapp_3d_nerve_signal

**用途**: 3D生物电仿真（DNA检测/神经信号）

**必需参数**:
```yaml
voltage: float                # 外加电压 (V), 默认: 1.0
dna_charge_density: float    # DNA电荷密度 (/cm^3), 默认: 2e21
```

**可选参数**:
```yaml
mesh_file: str               # 网格文件名, 默认: "disk_3d.msh"
```

**输出**:
- 3D电势分布（Tecplot格式）
- 接触电流

**前置条件**:
- 需要 `disk_3d.msh` 网格文件
- 计算量较2D版本大

---

### magnetic_3d_twowire

**用途**: 双导线静磁场分布（矢量势方法）

**必需参数**:
```yaml
jz_left: float              # 左导线电流密度 (A/m^2), 默认: 1.0
jz_right: float             # 右导线电流密度 (A/m^2), 默认: -1.0
```

**可选参数**:
```yaml
mu_air: float               # 空气磁导率 (相对), 默认: 1.0
mu_iron: float              # 铁磁导率 (相对), 默认: 1.0
mesh_file: str              # 网格文件名, 默认: "twowire.msh"
relative_error: float       # 默认: 1e-10
absolute_error: float       # 默认: 1.0
```

**输出**:
- 矢量势 Az 分布
- 磁场分量 Bx, By
- 体积信息
- Tecplot和MSH格式文件

**前置条件**:
- 需要 `twowire.msh` 网格文件

**能力边界**:
- ✅ 静磁场分析
- ✅ 毕奥-萨伐尔定律
- ✅ 多区域界面
- ❌ 不支持高频电磁
- ❌ 非线性磁性材料

**物理模型**:
```
∇²Az = -μJz
Bx = ∂Az/∂y
By = -∂Az/∂x
```

---

## 研究计划引用示例

### 示例1: 简单二极管仿真

```yaml
simulation_tasks:
  - task_id: "diode_iv_001"
    capability: "diode_1d_dc_iv"
    description: "硅二极管IV特性"
    parameters:
      p_doping: 1.0e18
      n_doping: 1.0e16
      temperature: 300
      max_voltage: 1.0
      voltage_step: 0.05
    output:
      - type: "iv_curve"
        file: "diode_iv.dat"
```

### 示例2: 电容提取

```yaml
simulation_tasks:
  - task_id: "cap_001"
    capability: "capacitance_1d_electrostatic"
    description: "MOS电容计算"
    parameters:
      device_length: 1.0e-7    # 1nm氧化层
      permittivity: 3.45e-13   # SiO2
      contact1_bias: 1.0
```

### 示例3: 瞬态分析

```yaml
simulation_tasks:
  - task_id: "transient_001"
    capability: "diode_1d_transient"
    description: "二极管开关特性"
    parameters:
      dc_voltage: 0.7
      time_step: 1.0e-4
      total_time: 1.0e-2
```

### 示例4: 使用智能网格

```yaml
simulation_tasks:
  - task_id: "diode_smart_001"
    capability: "diode_1d_dc_iv"
    description: "高梯度二极管（使用智能网格）"
    parameters:
      p_doping: 1.0e20    # 重掺杂
      n_doping: 1.0e15    # 轻掺杂
      temperature: 300
      max_voltage: 0.1
      use_intelligent_mesh: true  # 启用智能网格优化
    output:
      - type: "iv_curve"
        file: "diode_smart.dat"
      - type: "mesh_info"
        key: "intelligent_mesh"
```

---

## 智能网格参数

支持智能网格的能力标识可接受以下额外参数：

### 通用智能网格参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `use_intelligent_mesh` | bool | False | 是否启用智能网格优化 |

### 启用智能网格后的输出字段

```python
{
    "converged": True,
    "intelligent_mesh": {
        "mesh_density_cm": 1.00e-09,  # 优化的网格密度
        "estimated_junction_width_cm": 1.23e-06  # 估算的结宽
    },
    # ... 其他结果字段
}
```

### 支持智能网格的能力

| 能力标识 | 智能网格支持 | 优化策略 |
|---------|------------|---------|
| `diode_1d_dc_iv` | ✅ | 基于掺杂梯度自动计算结区网格密度 |
| `diode_1d_transient` | ✅ | 同上 |
| `diode_1d_ssac_cv` | ✅ | 同上 |
| `diode_2d_dc_iv` | ✅ | X方向基于掺杂梯度优化 |
| 其他 | ⚠️ | 使用默认网格密度 |

---

## 参数默认值汇总

### 通用参数

| 参数 | 默认值 | 单位 | 说明 |
|-----|-------|------|------|
| temperature | 300 | K | 室温 |
| device_length | 1e-5 | cm | 10μm |
| mesh_density | 1e-9 | cm | 1nm |
| p_doping | 1e18 | cm^-3 | 重掺杂p区 |
| n_doping | 1e18 | cm^-3 | 重掺杂n区 |
| max_iterations | 30 | - | 求解器最大迭代 |
| relative_error | 1e-10 | - | 相对误差容限 |

### 物理常数

| 常数 | 值 | 单位 |
|-----|---|------|
| ε0 (真空) | 8.85e-14 | F/cm |
| ε (SiO2) | 3.45e-13 | F/cm |
| ε (Si) | 1.04e-12 | F/cm |

---

## 错误处理

所有能力在仿真失败时返回:
```python
{
    "converged": False,
    "error": "错误描述",
    "bias_points": [...]  # 已成功计算的点
}
```

常见错误:
- 求解器不收敛 -> 减小步长或检查参数
- 网格生成失败 -> 检查几何参数
- 文件未找到 -> 检查前置条件（如Gmsh网格）
