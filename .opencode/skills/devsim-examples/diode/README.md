# Diode 示例说明

## 目录

- `diode_1d.py` - 一维PN结二极管DC IV特性
- `diode_1d_custom.py` - 一维自定义物理模型二极管
- `diode_2d.py` - 二维PN结二极管DC IV特性
- `tran_diode.py` - 一维二极管瞬态响应
- `ssac_diode.py` - 一维二极管小信号AC分析

## 能力标识说明

### diode_1d_dc_iv

**文件**: `diode_1d.py`

**功能**: 一维硅PN结二极管的DC IV特性仿真

**核心参数**:
```python
{
    "device_length": 1e-5,        # 器件长度 (cm), 默认10μm
    "junction_position": 0.5e-5,  # 结位置 (cm), 默认5μm
    "p_doping": 1e18,            # p区掺杂 (cm^-3)
    "n_doping": 1e18,            # n区掺杂 (cm^-3)
    "temperature": 300,          # 温度 (K)
    "taun": 1e-8,                # 电子寿命 (s)
    "taup": 1e-8,                # 空穴寿命 (s)
    "max_voltage": 0.5,          # 最大偏置 (V)
    "voltage_step": 0.1,         # 偏置步长 (V)
}
```

**工作思路**:
1. 创建一维网格，在结区加密
2. 设置硅材料参数（温度相关）
3. 定义阶跃掺杂分布
4. 先求解泊松方程获得初始电势
5. 加入漂移扩散方程求解载流子
6. 从0V扫描至目标电压，记录电流

**能力边界**:
- ✅ 1D硅基PN结二极管
- ✅ 漂移扩散输运模型
- ✅ SRH复合（通过taun/taup参数）
- ❌ 不支持隧穿效应
- ❌ 不支持光生载流子

**输出**:
- Tecplot格式数据文件
- 各偏置点的电流值

---

### diode_2d_dc_iv

**文件**: `diode_2d.py`

**功能**: 二维硅PN结二极管DC IV特性仿真

**核心参数**:
```python
{
    "device_width": 1e-5,        # 器件宽度 (cm)
    "device_height": 1e-5,       # 器件高度 (cm)
    "junction_x": 0.5e-5,        # 结位置x坐标 (cm)
    "p_doping": 1e18,           # p区掺杂 (cm^-3)
    "n_doping": 1e18,           # n区掺杂 (cm^-3)
    "temperature": 300,         # 温度 (K)
}
```

**工作思路**:
1. 创建二维矩形网格
2. 在结区附近进行网格加密
3. 设置材料参数和掺杂分布
4. 求解泊松方程获得初始电势分布
5. 加入漂移扩散方程
6. 扫描偏置并输出各接触电流

**能力边界**:
- ✅ 2D硅基PN结二极管
- ✅ 简单矩形几何
- ✅ 可查看2D电势分布
- ❌ 不支持复杂几何（需用Gmsh版本）

**输出**:
- Tecplot格式数据文件（包含2D场分布）
- 各偏置点的电流值

---

### diode_1d_transient

**文件**: `tran_diode.py`

**功能**: 一维二极管瞬态响应仿真

**核心参数**:
```python
{
    "dc_voltage": 0.7,           # DC偏置电压 (V)
    "time_step": 1e-3,          # 时间步长 (s)
    "total_time": 1e-2,         # 总仿真时间 (s)
    "p_doping": 1e18,
    "n_doping": 1e18,
}
```

**工作思路**:
1. 建立DC工作点
2. 改变偏置电压（阶跃）
3. 使用BDF1时间积分求解瞬态响应
4. 记录电流随时间变化

**能力边界**:
- ✅ 1D瞬态分析
- ✅ 电压阶跃响应
- ⚠️ 需要电路元件集成电流
- ❌ 不支持周期性信号（需修改）

**输出**:
- 各时间点的电路节点值

---

### diode_1d_ssac_cv

**文件**: `ssac_diode.py`

**功能**: 一维二极管小信号AC分析和C-V特性

**核心参数**:
```python
{
    "frequency": 1.0,            # AC频率 (Hz)
    "start_voltage": 0.0,        # 起始偏置 (V)
    "max_voltage": 0.5,          # 最大偏置 (V)
    "voltage_step": 0.1,         # 偏置步长 (V)
}
```

**工作思路**:
1. 求解各偏置点的DC解
2. 进行小信号AC分析
3. 从电流虚部计算电容
4. 生成C-V曲线

**能力边界**:
- ✅ 小信号AC分析
- ✅ C-V特性提取
- ✅ 固定频率分析
- ❌ 不支持频率扫描（需修改）

**输出**:
- C-V曲线数据
- 各偏置点的电容值

---

## 使用示例

### 示例1: 高阻二极管仿真

```python
from devsim_examples.diode.diode_1d import run_diode_1d_simulation

result = run_diode_1d_simulation(
    p_doping=1e16,          # 轻掺杂p区
    n_doping=1e16,          # 轻掺杂n区
    max_voltage=1.0,        # 更高偏置
    output_file="high_resistance_diode.dat"
)
```

### 示例2: 高温二极管仿真

```python
result = run_diode_1d_simulation(
    temperature=400,        # 400K高温
    max_voltage=0.3,        # 降低偏置防止热击穿
)
```

### 示例3: 瞬态开关响应

```python
from devsim_examples.diode.tran_diode import run_transient_diode_simulation

result = run_transient_diode_simulation(
    dc_voltage=0.7,
    time_step=1e-4,         # 更小时间步长
    total_time=5e-3,        # 5ms仿真
)
```

## 参数选择指南

### 掺杂浓度
- 典型PN结: 1e16 - 1e18 cm^-3
- 重掺杂: >1e19 cm^-3（欧姆接触）
- 轻掺杂: <1e15 cm^-3（高阻区）

### 温度
- 室温: 300K
- 低温: 77K（液氮，用于窄禁带材料）
- 高温: 350-400K（需注意本征载流子浓度增加）

### 载流子寿命
- 高质量硅: 1e-6 - 1e-4 s
- 一般器件: 1e-8 - 1e-6 s
- 辐射损伤: <1e-9 s

### 网格密度
- 结区: 1e-9 - 1e-8 cm（1-10nm）
- 体区: 1e-7 - 1e-6 cm（0.1-1μm）

## 收敛问题处理

如果仿真不收敛，尝试：
1. 减小偏置步长
2. 增加网格密度（特别是结区）
3. 增大绝对误差容限（1e10 -> 1e12）
4. 减小最大迭代次数后逐步增加
5. 检查掺杂浓度是否合理（避免>1e20 cm^-3）
