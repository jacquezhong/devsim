# Mobility 示例说明

## 目录

- `gmsh_mos2d.py` - 2D MOS结构迁移率模型
- `gmsh_mos2d_kla.py` - KLA迁移率模型
- `pythonmesh2d.py` - Python网格2D仿真

## 前提条件

这些示例需要预生成的Gmsh网格文件：
- `gmsh_mos2d.msh` - MOS结构网格

生成方法:
```bash
gmsh gmsh_mos2d.geo -2  # 生成2D网格
```

或运行:
```python
python gmsh_mos2d_create.py
```

## 能力标识说明

### mos_2d_gmsh_mobility

**文件**: `gmsh_mos2d.py`

**功能**: 2D MOS场效应管迁移率模型仿真

**核心参数**:
```python
{
    "device_name": "mos2d",
    "silicon_regions": ("gate", "bulk"),
    "oxide_regions": ("oxide",),
    "interfaces": ("bulk_oxide", "gate_oxide"),
    "temperature": 300,              # K
    "gate_bias_stop": 0.5,           # V
    "gate_bias_step": 0.05,          # V
    "drain_bias_stop": 0.5,          # V
    "drain_bias_step": 0.1,          # V
}
```

**工作思路**:
1. 导入Gmsh生成的2D MOS网格
2. 设置栅氧和硅区域的电势
3. 求解初始电势分布
4. 加入电子/空穴连续性方程
5. 栅压扫描观察反型层形成
6. 漏压扫描获得IV特性

**能力边界**:
- ✅ 2D MOS结构
- ✅ 栅压扫描（C-V特性）
- ✅ 漏压扫描（I-V特性）
- ✅ 迁移率模型
- ⚠️ 需要预生成Gmsh网格
- ❌ 不支持3D结构

**迁移率模型**:
使用 `mu_n` 和 `mu_p` 迁移率模型，包括：
- 晶格散射
- 电离杂质散射
- 表面粗糙度散射

**输出**:
- 栅压扫描的电流
- 漏压扫描的电流
- 载流子浓度分布
- 电势分布

---

## 使用示例

### 示例1: 标准MOS仿真

```python
from devsim_examples.mobility.gmsh_mos2d import run_mos_2d_mobility_simulation

# 确保 gmsh_mos2d.msh 存在
result = run_mos_2d_mobility_simulation(
    temperature=300,
    gate_bias_stop=1.0,     # 扫描到1V
    drain_bias_stop=0.1,    # 低漏压（线性区）
)
```

### 示例2: 高温MOS特性

```python
result = run_mos_2d_mobility_simulation(
    temperature=400,        # 400K
    gate_bias_stop=0.8,     # 降低栅压防止过大电流
    drain_bias_stop=0.05,
)
```

## 参数选择指南

### 栅压范围
- 阈值电压附近: 0-0.5V
- 强反型区: 0.5-2.0V
- 注意氧化层击穿: SiO₂约10 MV/cm

### 漏压范围
- 线性区: 0.01-0.1V
- 饱和区: 0.5-2.0V
- 热载流子效应: >2V（需小心）

### 温度
- 室温: 300K
- 高温: 350-400K（迁移率下降）
- 低温: 250K（迁移率上升）

## 结果分析

### 阈值电压提取
从栅压扫描的sqrt(Id)-Vg曲线线性外推

### 迁移率提取
从线性区跨导:
```
μ = L/(W*Cox*Vd) * dId/dVg
```

### 亚阈值摆幅
```
SS = dVg/d(log(Id))  [mV/decade]
```
理想值: 60 mV/decade @ 300K

## 网格要求

### 氧化层
- 至少3-5个网格点
- 厚度方向均匀分布

### 硅表面
- 反型层区域加密
- 结附近加密

### 接触
- 接触边缘加密
- 避免尖锐拐角
