# Capacitance 示例说明

## 目录

- `cap1d.py` - 一维平板电容静电场
- `cap2d.py` - 二维平板电容静电场（含边缘效应）

## 能力标识说明

### capacitance_1d_electrostatic

**文件**: `cap1d.py`

**功能**: 一维平板电容静电场分析

**核心参数**:
```python
{
    "device_length": 1.0,        # 器件长度 (cm)
    "mesh_spacing": 0.1,         # 网格间距 (cm)
    "permittivity": 3.9e-13,    # 介电常数 (F/cm), SiO2默认
    "contact1_bias": 1.0,        # 接触1偏置 (V)
    "contact2_bias": 0.0,        # 接触2偏置 (V)
}
```

**工作思路**:
1. 创建一维网格，两端为金属接触
2. 定义介电常数
3. 建立泊松方程（仅电势）
4. 求解电势分布
5. 计算接触电荷和电容

**能力边界**:
- ✅ 1D静电场分析
- ✅ 仅泊松方程（无载流子输运）
- ✅ 可计算平板电容值
- ❌ 不包含边缘电场效应

**理论验证**:
对于平行板电容，理论值:
```
C = ε * A / d
```
其中A为单位面积(1 cm^2), d为板间距

**常用材料介电常数**:
- 真空: ε₀ = 8.85e-14 F/cm
- SiO₂: 3.9ε₀ = 3.45e-13 F/cm
- Si₃N₄: 7.5ε₀ = 6.64e-13 F/cm
- Si: 11.7ε₀ = 1.04e-12 F/cm

---

### capacitance_2d_electrostatic

**文件**: `cap2d.py`

**功能**: 二维平板电容静电场分析（含边缘效应）

**核心参数**:
```python
{
    # 几何参数 (单位: um)
    "xmin": -25.0, "x1": -24.975, "x2": -2.0, 
    "x3": 2.0, "x4": 24.975, "xmax": 25.0,
    "ymin": 0.0, "y1": 0.1, "y2": 0.2,
    "y3": 0.8, "y4": 0.9, "ymax": 50.0,
    "permittivity": 3.9e-13,  # F/cm
    "top_bias": 1.0,          # V
    "bot_bias": 0.0,          # V
}
```

**工作思路**:
1. 创建二维网格，包含金属电极和介质区域
2. 在电极边缘加密网格
3. 建立泊松方程
4. 求解电势分布（包含边缘电场）
5. 计算接触电荷（包含寄生电容）

**能力边界**:
- ✅ 2D静电场分析
- ✅ 包含边缘电场效应
- ✅ 可模拟非对称电极结构
- ❌ 不支持3D几何

**输出**:
- devsim格式网格文件
- Tecplot格式数据文件
- VTK格式（用于Paraview可视化）

---

## 使用示例

### 示例1: 计算SiO2 MOS电容

```python
from devsim_examples.capacitance.cap1d import run_capacitance_1d_simulation

# 1nm氧化层
result = run_capacitance_1d_simulation(
    device_length=1e-7,       # 1nm = 1e-7 cm
    mesh_spacing=1e-8,        # 0.1nm网格
    permittivity=3.9 * 8.85e-14,  # SiO2
    contact1_bias=1.0,
)

# 理论值: C = 3.45e-13 F/cm^2 (对于1nm厚度)
print(f"仿真电容: {result['capacitance_F_cm2']:.6e} F/cm^2")
```

### 示例2: 空气电容

```python
result = run_capacitance_1d_simulation(
    device_length=1.0,        # 1cm
    permittivity=8.85e-14,    # ε0
    contact1_bias=100.0,      # 100V（空气击穿前）
)
```

### 示例3: 2D边缘效应分析

```python
from devsim_examples.capacitance.cap2d import run_capacitance_2d_simulation

# 修改电极尺寸
result = run_capacitance_2d_simulation(
    x2=-5.0, x3=5.0,          # 上电极宽度10um
    y1=0.1, y2=0.2,           # 下电极厚度
    y3=0.8, y4=0.9,           # 上电极厚度
    permittivity=3.9 * 8.85e-14,
)

# 对比1D和2D结果可得到边缘电容占比
```

## 参数选择指南

### 网格间距
- 简单均匀介质: device_length / 100
- 高介电常数对比: 在界面处加密10倍
- 2D边缘区域: 电极边缘最小间距的1/10

### 介电常数
常用半导体材料:
| 材料 | 相对介电常数 | F/cm |
|-----|------------|------|
| 真空 | 1.0 | 8.85e-14 |
| SiO₂ | 3.9 | 3.45e-13 |
| Si₃N₄ | 7.5 | 6.64e-13 |
| Al₂O₃ | 9.0 | 7.97e-13 |
| HfO₂ | 25 | 2.21e-12 |
| Si | 11.7 | 1.04e-12 |
| GaAs | 12.9 | 1.14e-12 |

### 偏置电压
- 典型值: 0-10V
- 高k介质: 可承受更高电压
- 注意介质击穿场强:
  - SiO₂: ~10 MV/cm
  - HfO₂: ~5 MV/cm

## 结果验证

### 1D电容理论验证
对于平行板电容:
```
C_theoretical = ε * A / d
```

仿真值应接近理论值。偏差来源:
- 网格离散误差
- 边界效应（1D近似）
- 接触电阻（非理想金属）

### 2D边缘效应
边缘电容占总电容的比例:
```
f_edge = (C_2D - C_1D) / C_1D
```

对于大电极间距，f_edge可能>50%

## 应用场景

1. **MOS电容计算**: 栅氧化层电容
2. **互连寄生电容**: 金属线间电容
3. **MEMS器件**: 静电驱动器电容
4. **RF器件**: 高频寄生电容提取
