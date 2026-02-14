# Bioapp1 示例说明

## 目录

- `bioapp1_2d.py` - 2D离子通道/DNA检测仿真
- `bioapp1_3d.py` - 3D生物电仿真

## 前提条件

这些示例需要预生成的 Gmsh 网格文件：
- `disk_2d.msh` - 2D圆盘网格
- `disk_3d.msh` - 3D圆盘网格

生成方法:
```bash
gmsh disk_2d.geo -2  # 生成2D网格
gmsh disk_3d.geo -3  # 生成3D网格
```

## 能力标识说明

### bioapp_2d_ion_channel

**文件**: `bioapp1_2d.py`

**功能**: 2D生物膜离子通道/DNA检测仿真

**核心参数**:
```python
{
    "voltage": 1.0,                # 外加电压 (V)
    "dna_charge_density": 2e21,    # DNA电荷密度 (/cm^3)
    "zero_charge_first": True,     # 先求解零电荷参考
    "mesh_file": "disk_2d.msh",   # 网格文件
}
```

**工作思路**:
1. 导入Gmsh生成的2D圆盘网格
2. 定义三种材料区域：溶液、DNA、介电层
3. 在DNA区域设置电荷密度
4. 求解泊松方程获得电势分布
5. 对比有/无DNA电荷时的电势变化

**能力边界**:
- ✅ 生物电应用（离子通道、DNA检测）
- ✅ 圆柱坐标系（轴对称）
- ✅ 多区域多界面
- ⚠️ 需要 Gmsh 网格文件 disk_2d.msh
- ⚠️ 依赖 bioapp1_common 模块

**应用**:
- DNA测序（纳米孔检测）
- 离子通道电流
- 生物传感器

---

### bioapp_3d_nerve_signal

**文件**: `bioapp1_3d.py`

**功能**: 3D生物电仿真（DNA检测/神经信号）

**核心参数**:
```python
{
    "voltage": 1.0,                # 外加电压 (V)
    "dna_charge_density": 2e21,    # DNA电荷密度 (/cm^3)
    "mesh_file": "disk_3d.msh",   # 3D网格文件
}
```

**与2D版本区别**:
- 使用3D网格（计算量更大）
- 更真实的几何结构
- 适合复杂生物分子结构

**工作思路**: 同2D版本

**能力边界**:
- ✅ 3D生物电仿真
- ✅ 更精确的场分布
- ⚠️ 需要更多计算资源
- ⚠️ 需要 Gmsh 网格文件 disk_3d.msh

---

## 使用示例

### 示例1: 2D DNA检测

```python
from devsim_examples.bioapp1.bioapp1_2d import run_bioapp1_2d_simulation

# 确保 disk_2d.msh 存在
result = run_bioapp1_2d_simulation(
    voltage=1.0,
    dna_charge_density=2e21,  # 带电DNA
    output_prefix="dna_detection"
)
```

### 示例2: 3D生物分子仿真

```python
from devsim_examples.bioapp1.bioapp1_3d import run_bioapp1_3d_simulation

# 确保 disk_3d.msh 存在
result = run_bioapp1_3d_simulation(
    voltage=2.0,
    dna_charge_density=1e21,
    output_prefix="3d_bio"
)
```

## 物理模型

### 电荷密度
- DNA电荷密度: ~2e21 /cm³（双链DNA）
- 离子溶液: K⁺ 浓度 ~6.02e17 /cm³ (0.001 M)

### 离子输运
由 bioapp1_common 模块定义：
- Nernst-Planck 方程
- 泊松方程
- 电中性条件

## 结果分析

### 电势差检测
通过比较有/无DNA时的电势分布：
```
ΔV = V(DNA) - V(no DNA)
```

### 电流计算
从电势梯度计算离子电流

## 参考资料

- 原始示例: `examples/bioapp1/`
- Gmsh 文档: http://gmsh.info/
