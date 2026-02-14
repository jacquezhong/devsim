# DEVSIM Examples 能力说明书

**版本**: 1.0.0  
**更新日期**: 2026-02-14  
**适用范围**: 研究计划制定与执行

---

## 文档说明

本文档详细说明 DEVSIM Examples Skill 中所有可用的仿真能力。每个能力都是**独立可执行的完整仿真**，研究者可以在研究计划中直接引用能力ID并定制参数。

### 使用方式

研究计划中引用格式：

```yaml
simulation_tasks:
  - task_id: "step_001"
    capability: "diode_1d_dc_iv"      # 能力ID
    description: "硅二极管IV特性测试"
    parameters:                        # 定制参数
      p_doping: 1e18
      n_doping: 1e16
      temperature: 300
      max_voltage: 1.0
    output:
      - file: "iv_curve.dat"
        format: "tecplot"
```

### 可靠性等级

- **A级**: 已通过复现测试，与原始示例100%一致
- **B级**: 基于原始示例，参数化扩展
- **C级**: 占位功能，需要预生成网格文件

---

## 能力清单总览

### 二极管器件 (Diode)

| 能力ID | 维度 | 仿真类型 | 可靠性 | 智能网格 |
|--------|------|----------|--------|----------|
| `diode_1d_dc_iv` | 1D | DC IV特性 | A | ✅ |
| `diode_1d_transient` | 1D | 瞬态响应 | A | ✅ |
| `diode_1d_ssac_cv` | 1D | 小信号AC/C-V | A | ✅ |
| `diode_2d_dc_iv` | 2D | DC IV特性 | A | ✅ |

### 电容/静电场 (Capacitance)

| 能力ID | 维度 | 仿真类型 | 可靠性 | 智能网格 |
|--------|------|----------|--------|----------|
| `capacitance_1d_electrostatic` | 1D | 静电场 | A | ⚠️ |
| `capacitance_2d_electrostatic` | 2D | 静电场 | A | ⚠️ |

### MOS器件 (Mobility)

| 能力ID | 维度 | 仿真类型 | 可靠性 | 备注 |
|--------|------|----------|--------|------|
| `mos_2d_gmsh_mobility` | 2D | 迁移率模型 | B | 需预生成网格 |

### 生物电应用 (Bioapp1)

| 能力ID | 维度 | 仿真类型 | 可靠性 | 备注 |
|--------|------|----------|--------|------|
| `bioapp_2d_ion_channel` | 2D | 离子通道/DNA检测 | B | 需预生成网格 |
| `bioapp_3d_nerve_signal` | 3D | 神经信号传导 | B | 需预生成网格 |

### 电磁场 (Vectorpotential)

| 能力ID | 维度 | 仿真类型 | 可靠性 | 备注 |
|--------|------|----------|--------|------|
| `magnetic_3d_twowire` | 3D | 静磁场分布 | B | 需预生成网格 |

---

## 详细能力说明

### 1. diode_1d_dc_iv

**功能描述**: 一维PN结二极管的直流IV特性仿真，支持偏置扫描获取完整的电流-电压曲线。

**对应文件**: `diode/diode_1d.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 可调范围 | 说明 |
|--------|------|--------|------|----------|------|
| `p_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | p区掺杂浓度，影响内建电势 |
| `n_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | n区掺杂浓度，与p区共同决定结特性 |
| `temperature` | float | 300 | K | 250 - 400 | 工作温度，影响本征载流子浓度 |
| `device_length` | float | 1e-5 | cm | 1e-6 - 1e-4 | 器件总长度（10μm） |
| `junction_position` | float | 0.5e-5 | cm | 0.1e-5 - 0.9e-5 | 结位置（默认居中） |
| `mesh_density` | float | 1e-9 | cm | 1e-10 - 1e-7 | 结区网格密度，越小越精密 |
| `taun` | float | 1e-8 | s | 1e-10 - 1e-6 | 电子寿命，影响SRH复合 |
| `taup` | float | 1e-8 | s | 1e-10 - 1e-6 | 空穴寿命，影响SRH复合 |
| `start_voltage` | float | 0.0 | V | -1.0 - 0.0 | 扫描起始电压 |
| `max_voltage` | float | 0.5 | V | 0.1 - 2.0 | 扫描最大电压 |
| `voltage_step` | float | 0.1 | V | 0.01 - 0.5 | 扫描步长，越小分辨率越高 |
| `use_intelligent_mesh` | bool | False | - | True/False | 启用智能网格优化 |

**关键参数调整建议**:

- **高阻二极管**: 降低掺杂浓度至 1e16-1e17 cm⁻³
- **高温仿真**: 温度升至 350-400K，同时降低 max_voltage 防止击穿
- **精细IV曲线**: 减小 voltage_step 至 0.01-0.02V
- **重掺杂**: 提高掺杂至 1e19-1e20 cm⁻³，注意减小 max_voltage

#### 执行流程

1. **网格创建**: 建立1D网格，结区自动加密
2. **材料设置**: 配置硅材料参数（温度相关）
3. **掺杂定义**: 阶跃掺杂分布 p区/n区
4. **初始求解**: 泊松方程获得平衡态电势
5. **载流子求解**: 加入漂移扩散方程
6. **DC扫描**: 从0V扫描至 max_voltage，步长 voltage_step
7. **电流记录**: 每个偏置点记录电子/空穴/总电流

#### 输出结果

**数据文件**:
- 文件名: `diode_1d.dat`（可定制）
- 格式: Tecplot
- 内容: 
  - 各偏置点的电势分布
  - 电子/空穴浓度分布
  - 电场分布
  - 电流密度分布

**控制台输出**:
- 每个偏置点的接触电流（电子、空穴、总电流）

**返回值** (Python dict):
```python
{
    "device": "MyDevice",
    "region": "MyRegion",
    "parameters": {...},  # 输入参数记录
    "bias_points": [      # 扫描的偏置点
        {"voltage_V": 0.0, "converged": True},
        {"voltage_V": 0.1, "converged": True},
        ...
    ],
    "converged": True,    # 整体收敛状态
    "output_file": "diode_1d.dat",
    "intelligent_mesh": {  # 如启用智能网格
        "mesh_density_cm": 1.00e-09
    }
}
```

#### 能力边界

**明确支持**:
- 硅基PN结二极管（1D）
- 漂移扩散输运模型
- SRH复合（通过 taun/taup 控制）
- 温度范围 250K-400K
- 偏置范围 -1V 至 2V

**不支持**:
- 隧穿效应
- 光生载流子（需改用光电器件示例）
- 雪崩倍增
- 量子效应

#### 使用示例

**示例1: 标准硅二极管**
```yaml
capability: diode_1d_dc_iv
parameters:
  p_doping: 1e18
  n_doping: 1e18
  temperature: 300
  max_voltage: 0.5
  voltage_step: 0.1
```

**示例2: 高阻二极管（低掺杂）**
```yaml
capability: diode_1d_dc_iv
parameters:
  p_doping: 1e16          # 轻掺杂p区
  n_doping: 1e16          # 轻掺杂n区
  temperature: 300
  max_voltage: 1.0        # 可承受更高电压
  voltage_step: 0.05      # 更精细的步长
  use_intelligent_mesh: true  # 自动优化网格
```

**示例3: 高温二极管**
```yaml
capability: diode_1d_dc_iv
parameters:
  p_doping: 1e18
  n_doping: 1e18
  temperature: 400        # 高温
  max_voltage: 0.3        # 降低电压防止热击穿
  taun: 1e-7              # 寿命随温度变化
  taup: 1e-7
```

---

### 2. diode_1d_transient

**功能描述**: 一维二极管瞬态响应仿真，模拟电压阶跃下的电流变化过程。

**对应文件**: `diode/tran_diode.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 可调范围 | 说明 |
|--------|------|--------|------|----------|------|
| `p_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | p区掺杂浓度 |
| `n_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | n区掺杂浓度 |
| `temperature` | float | 300 | K | 250 - 400 | 工作温度 |
| `device_length` | float | 1e-5 | cm | 1e-6 - 1e-4 | 器件长度 |
| `junction_position` | float | 0.5e-5 | cm | - | 结位置 |
| `dc_voltage` | float | 0.7 | V | 0.1 - 1.0 | 阶跃后的DC偏置 |
| `time_step` | float | 1e-3 | s | 1e-6 - 1e-2 | 时间步长 |
| `total_time` | float | 1e-2 | s | 1e-4 - 1e-1 | 总仿真时间 |
| `print_solution` | bool | True | - | True/False | 是否打印中间结果 |

**关键参数调整建议**:

- **快速开关**: 减小 time_step 至 1e-5 ~ 1e-4 s
- **长瞬态**: 增大 total_time 至 0.1 s
- **低电压阶跃**: dc_voltage 设为 0.3-0.5 V（线性区）
- **高电压阶跃**: dc_voltage 设为 0.7-0.8 V（饱和区）

#### 执行流程

1. **建立DC工作点**: 在0V平衡态求解
2. **设置电路元件**: 添加电压源用于电流积分
3. **阶跃电压**: 突然改变偏置至 dc_voltage
4. **瞬态求解**: 使用BDF1方法时间积分
5. **记录响应**: 每个时间步记录电流

#### 输出结果

**控制台输出**:
- 每个时间点的电路节点值（电压、电流）

**返回值**:
```python
{
    "device": "MyDevice",
    "time_points": [
        {"time_s": 0.0, "converged": True},
        {"time_s": 0.001, "converged": True},
        ...
    ],
    "converged": True
}
```

#### 能力边界

**支持**:
- 1D瞬态分析
- 电压阶跃响应
- 电流随时间变化

**不支持**:
- 周期性信号（正弦、方波等）
- 多频响应
- 热瞬态（需热-电耦合模型）

**前置条件**:
- 需要电路元件集成电流
- 时间步长需仔细选择以保证收敛

#### 使用示例

**示例: 二极管开关响应**
```yaml
capability: diode_1d_transient
parameters:
  p_doping: 1e18
  n_doping: 1e18
  dc_voltage: 0.7         # 从0V阶跃到0.7V
  time_step: 1e-4         # 0.1ms步长
  total_time: 5e-3        # 5ms总时间
```

---

### 3. diode_1d_ssac_cv

**功能描述**: 一维二极管小信号AC分析，获取电容-电压（C-V）特性。

**对应文件**: `diode/ssac_diode.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 可调范围 | 说明 |
|--------|------|--------|------|----------|------|
| `p_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | p区掺杂浓度 |
| `n_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | n区掺杂浓度 |
| `temperature` | float | 300 | K | 250 - 400 | 工作温度 |
| `device_length` | float | 1e-5 | cm | - | 器件长度 |
| `junction_position` | float | 0.5e-5 | cm | - | 结位置 |
| `frequency` | float | 1.0 | Hz | 0.1 - 1e6 | AC信号频率 |
| `start_voltage` | float | 0.0 | V | -1.0 - 0.0 | C-V扫描起始 |
| `max_voltage` | float | 0.5 | V | 0.1 - 2.0 | C-V扫描终止 |
| `voltage_step` | float | 0.1 | V | 0.01 - 0.5 | 扫描步长 |

**关键参数调整建议**:

- **低频C-V**: frequency 设为 1-10 Hz（准静态）
- **高频C-V**: frequency 设为 1e4-1e6 Hz（观察界面态影响）
- **耗尽区**: start_voltage 设为 -1.0 ~ 0 V
- **反型区**: max_voltage 提高至 1.0-2.0 V

#### 计算原理

小信号电容计算:
```
C = I_imag / (2πfV)
```

其中:
- I_imag: 电流虚部
- f: 频率
- V: 电压幅值

#### 输出结果

**C-V曲线数据**:
```python
{
    "cv_data": [
        {"voltage_V": 0.0, "capacitance_F": 1.23e-12},
        {"voltage_V": 0.1, "capacitance_F": 1.15e-12},
        ...
    ],
    "frequency_Hz": 1.0
}
```

#### 能力边界

**支持**:
- 固定频率C-V特性
- 耗尽电容和扩散电容提取
- 多偏置点扫描

**不支持**:
- 频率扫描（C-f特性）
- 多频同时分析
- 噪声分析

#### 使用示例

**示例: C-V特性提取**
```yaml
capability: diode_1d_ssac_cv
parameters:
  p_doping: 1e18
  n_doping: 1e18
  frequency: 1.0          # 1Hz
  start_voltage: 0.0
  max_voltage: 0.5
  voltage_step: 0.05      # 精细扫描
```

---

### 4. diode_2d_dc_iv

**功能描述**: 二维PN结二极管的直流IV特性仿真，支持2D电势和电流分布分析。

**对应文件**: `diode/diode_2d.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 可调范围 | 说明 |
|--------|------|--------|------|----------|------|
| `p_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | p区掺杂 |
| `n_doping` | float | 1e18 | cm⁻³ | 1e15 - 1e20 | n区掺杂 |
| `temperature` | float | 300 | K | 250 - 400 | 温度 |
| `device_width` | float | 1e-5 | cm | 1e-6 - 1e-4 | 器件宽度（X方向） |
| `device_height` | float | 1e-5 | cm | 1e-6 - 1e-4 | 器件高度（Y方向） |
| `junction_x` | float | 0.5e-5 | cm | 0.1e-5 - 0.9e-5 | 结X位置 |
| `mesh_density` | float | 1e-8 | cm | 1e-9 - 1e-7 | 结区网格密度 |
| `start_voltage` | float | 0.0 | V | - | 起始偏置 |
| `max_voltage` | float | 0.5 | V | 0.1 - 2.0 | 最大偏置 |
| `voltage_step` | float | 0.1 | V | 0.01 - 0.5 | 扫描步长 |

**关键参数调整建议**:

- **宽器件**: device_width 增至 2e-5 ~ 5e-5 cm
- **窄器件**: device_width 减至 2e-6 ~ 5e-6 cm
- **非对称结**: 调整 junction_x 偏离中心
- **边缘效应**: 减小 mesh_density 更好捕捉边缘场

#### 输出结果

**数据文件**:
- 格式: Tecplot
- 内容: 2D场分布（电势、载流子浓度、电流密度）
- 可可视化: 电势等值线图、电流流线

#### 能力边界

**支持**:
- 2D矩形几何
- 2D电势分布
- 电流分布可视化

**不支持**:
- 复杂几何（需用Gmsh版本）
- 3D效应

#### 使用示例

**示例: 2D二极管分析**
```yaml
capability: diode_2d_dc_iv
parameters:
  device_width: 2e-5       # 20μm宽
  device_height: 1e-5      # 10μm高
  p_doping: 1e18
  n_doping: 1e18
  max_voltage: 0.5
  voltage_step: 0.1
```

---

### 5. capacitance_1d_electrostatic

**功能描述**: 一维静电场电容仿真，仅求解泊松方程，计算平板电容值。

**对应文件**: `capacitance/cap1d.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 可调范围 | 说明 |
|--------|------|--------|------|----------|------|
| `device_length` | float | 1.0 | cm | 1e-7 - 10.0 | 平板间距 |
| `mesh_spacing` | float | 0.1 | cm | 0.001 - 1.0 | 网格间距 |
| `permittivity` | float | 3.9e-13 | F/cm | 8.85e-14 - 1e-11 | 介电常数 |
| `contact1_bias` | float | 1.0 | V | -100 - 100 | 接触1偏置 |
| `contact2_bias` | float | 0.0 | V | -100 - 100 | 接触2偏置 |

**常用材料介电常数**:
- 真空: 8.85e-14 F/cm
- SiO₂: 3.45e-13 F/cm (3.9×ε₀)
- Si₃N₄: 6.64e-13 F/cm (7.5×ε₀)
- Si: 1.04e-12 F/cm (11.7×ε₀)

**关键参数调整建议**:

- **MOS电容**: device_length 设为 1e-7 cm (1nm氧化层)
- **厚氧化层**: device_length 设为 1e-6 ~ 1e-5 cm
- **高k介质**: 使用 HfO₂ (ε~25)
- **真空电容**: permittivity 设为 8.85e-14

#### 计算原理

理论验证:
```
C = ε × A / d
```
其中 A=1 cm²（单位面积）

#### 输出结果

```python
{
    "contact_charges": {
        "contact1": 3.45e-09,   # 接触1电荷 (C/cm²)
        "contact2": -3.45e-09   # 接触2电荷
    },
    "capacitance_F_cm2": 3.45e-09,  # 单位面积电容
    "converged": True
}
```

#### 能力边界

**支持**:
- 1D静电场
- 任意介电常数
- 电容值计算

**不支持**:
- 载流子输运（无漂移扩散）
- 界面态
- 边缘电场（需用2D版本）

#### 使用示例

**示例1: MOS电容 (1nm SiO₂)**
```yaml
capability: capacitance_1d_electrostatic
parameters:
  device_length: 1e-7      # 1nm
  permittivity: 3.45e-13   # SiO₂
  contact1_bias: 1.0
```

**示例2: 厚氧化层**
```yaml
capability: capacitance_1d_electrostatic
parameters:
  device_length: 1e-5      # 100nm
  permittivity: 3.45e-13
  contact1_bias: 10.0      # 可承受更高电压
```

---

### 6. capacitance_2d_electrostatic

**功能描述**: 二维静电场电容仿真，包含边缘电场效应（寄生电容）。

**对应文件**: `capacitance/cap2d.py`

**可靠性等级**: A

#### 可调参数

| 参数名 | 类型 | 默认值 | 单位 | 说明 |
|--------|------|--------|------|------|
| `xmin` ~ `xmax` | float | -25 ~ 25 | μm | X方向几何坐标 |
| `ymin` ~ `ymax` | float | 0 ~ 50 | μm | Y方向几何坐标 |
| `permittivity` | float | 3.9e-13 | F/cm | 介电常数 |
| `top_bias` | float | 1.0 | V | 上电极偏置 |
| `bot_bias` | float | 0.0 | V | 下电极偏置 |

**几何说明**:
- 默认是两个平行金属板结构
- 电极宽度不同，产生边缘电场
- 可通过调整坐标改变电极尺寸和间距

#### 输出结果

- 电容值（含边缘效应）
- 2D电势分布
- VTK格式（Paraview可视化）

#### 能力边界

**支持**:
- 2D静电场
- 边缘电场效应
- 非对称电极

**不支持**:
- 3D几何
- 载流子输运

#### 使用示例

```yaml
capability: capacitance_2d_electrostatic
parameters:
  ymin: 0.0
  ymax: 50.0              # 50μm高度
  xmin: -25.0
  xmax: 25.0              # 50μm宽度
  permittivity: 3.45e-13
  top_bias: 1.0
```

---

### 7. mos_2d_gmsh_mobility

**功能描述**: 2D MOS结构迁移率模型仿真，栅压扫描获得转移特性。

**对应文件**: `mobility/gmsh_mos2d.py`

**可靠性等级**: B

#### 可调参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `temperature` | float | 300 | K，温度 |
| `gate_bias_stop` | float | 0.5 | V，栅压扫描终止 |
| `gate_bias_step` | float | 0.05 | V，栅压步长 |
| `drain_bias_stop` | float | 0.5 | V，漏压扫描终止 |
| `drain_bias_step` | float | 0.1 | V，漏压步长 |

**前置条件**:
- 需要预生成 `gmsh_mos2d.msh` 网格文件
- 生成方法: `gmsh gmsh_mos2d.geo -2`

#### 输出结果

- Id-Vg 曲线（转移特性）
- Id-Vd 曲线（输出特性）
- 载流子浓度分布
- 电势分布

#### 能力边界

**支持**:
- 2D MOS结构
- 栅压扫描（C-V特性）
- 漏压扫描（I-V特性）
- 迁移率模型

**不支持**:
- 自定义网格（依赖Gmsh）
- 3D结构

**备注**: 此能力需要外部网格文件，请确保运行前已生成。

---

### 8. bioapp_2d_ion_channel

**功能描述**: 2D生物电离子通道仿真，模拟DNA通过纳米孔时的电势变化。

**对应文件**: `bioapp1/bioapp1_2d.py`

**可靠性等级**: B

#### 可调参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `voltage` | float | 1.0 | V，外加电压 |
| `dna_charge_density` | float | 2e21 | /cm³，DNA电荷密度 |
| `zero_charge_first` | bool | True | 是否先求解零电荷参考 |

**前置条件**:
- 需要预生成 `disk_2d.msh` 网格文件

#### 输出结果

- 电势分布（Tecplot格式）
- LogDeltaPotential（电势变化对数）
- 接触电流

#### 应用场景

- DNA纳米孔检测
- 离子通道电流
- 生物传感器

---

### 9. bioapp_3d_nerve_signal

**功能描述**: 3D神经信号传导仿真，模拟神经纤维中的离子电流。

**对应文件**: `bioapp1/bioapp1_3d.py`

**可靠性等级**: B

#### 可调参数

同 `bioapp_2d_ion_channel`

**前置条件**:
- 需要预生成 `disk_3d.msh` 网格文件

#### 特点

- 3D几何结构
- 计算量较2D版本大
- 更精确的场分布

---

### 10. magnetic_3d_twowire

**功能描述**: 双导线静磁场分布仿真，使用矢量势方法。

**对应文件**: `vectorpotential/twowire.py`

**可靠性等级**: B

#### 可调参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `jz_left` | float | 1.0 | A/m²，左导线电流密度 |
| `jz_right` | float | -1.0 | A/m²，右导线电流密度 |
| `mu_air` | float | 1.0 | 空气相对磁导率 |
| `mu_iron` | float | 1.0 | 铁磁导率 |

**前置条件**:
- 需要预生成 `twowire.msh` 网格文件

#### 物理模型

控制方程:
```
∇²Az = -μJz
Bx = ∂Az/∂y
By = -∂Az/∂x
```

#### 输出结果

- 矢量势 Az 分布
- 磁场分量 Bx, By
- 体积信息
- Tecplot和MSH格式文件

#### 应用场景

- 电感器设计
- 电磁兼容性分析
- 磁传感器设计

---

## 附录A: 参数速查表

### 常用掺杂浓度

| 应用场景 | p_doping | n_doping |
|---------|----------|----------|
| 标准PN结 | 1e18 | 1e18 |
| 高阻二极管 | 1e16 | 1e16 |
| 重掺杂欧姆接触 | 1e20 | 1e20 |
| 不对称结 | 1e19 | 1e16 |

### 常用温度

| 应用场景 | temperature |
|---------|-------------|
| 室温 | 300 K |
| 高温测试 | 350-400 K |
| 低温红外 | 77 K |

### 网格密度参考

| 应用场景 | mesh_density |
|---------|-------------|
| 一般PN结 | 1e-8 ~ 1e-7 cm |
| 高掺杂梯度 | 1e-9 ~ 1e-8 cm |
| 薄氧化层 | 1e-9 cm |

---

## 附录B: 常见问题

### Q1: 如何选择合适的能力ID？

**按器件类型**:
- 一维二极管 → `diode_1d_dc_iv`
- 二维二极管 → `diode_2d_dc_iv`
- MOS电容 → `capacitance_1d_electrostatic`
- MOS晶体管 → `mos_2d_gmsh_mobility`

**按仿真目标**:
- IV曲线 → `diode_1d_dc_iv`
- 瞬态响应 → `diode_1d_transient`
- C-V特性 → `diode_1d_ssac_cv`

### Q2: 仿真不收敛怎么办？

**尝试以下调整**:
1. 减小 `max_voltage` 或增大 `voltage_step`
2. 启用 `use_intelligent_mesh: true`
3. 减小掺杂浓度梯度
4. 增大 `absolute_error`（如从1e10增至1e12）

### Q3: 如何获取更精细的IV曲线？

减小 `voltage_step`:
```yaml
parameters:
  voltage_step: 0.01  # 10mV步长
```

### Q4: 智能网格和普通网格的区别？

智能网格会自动根据掺杂梯度计算最优网格密度：
```yaml
parameters:
  use_intelligent_mesh: true  # 自动优化
  # 或手动指定
  mesh_density: 1e-9  # 固定值
```

---

## 版本历史

- **v1.0.0** (2026-02-14): 初始版本，包含10个完整能力

---

**文档维护**: 如需添加新能力或更新参数，请同步修改本文档和CAPABILITY_INDEX.md
