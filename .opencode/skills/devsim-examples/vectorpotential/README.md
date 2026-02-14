# Vectorpotential 示例说明

## 目录

- `twowire.py` - 双导线磁场分布（矢量势方法）

## 前提条件

此示例需要预生成的 Gmsh 网格文件：
- `twowire.msh` - 双导线3D网格

生成方法:
```bash
gmsh twowire.geo -3  # 生成3D网格
```

## 能力标识说明

### magnetic_3d_twowire

**文件**: `twowire.py`

**功能**: 使用矢量势方法计算双导线静磁场分布

**核心参数**:
```python
{
    "mesh_file": "twowire.msh",
    "mu_air": 1.0,          # 空气磁导率 (相对)
    "mu_iron": 1.0,       # 铁磁导率 (相对)
    "jz_left": 1.0,       # 左导线电流密度 (A/m^2)
    "jz_right": -1.0,     # 右导线电流密度 (A/m^2)
}
```

**物理原理**:

控制方程（矢量势泊松方程）:
```
∇²Az = -μJz
```

其中:
- Az: z方向矢量势 (Wb/m)
- μ: 磁导率 (H/m)
- Jz: z方向电流密度 (A/m²)

磁场计算:
```
Bx = ∂Az/∂y
By = -∂Az/∂x
Bz = 0  (二维情况)
```

毕奥-萨伐尔定律验证:
对于长直导线，理论磁场:
```
B = μI / (2πr)
```

**工作思路**:
1. 导入Gmsh生成的3D网格
2. 定义三个区域：空气、左导线、右导线
3. 设置材料磁导率和电流密度
4. 定义矢量势Az的方程
5. 求解矢量势泊松方程
6. 从Az计算磁场分量
7. 应用界面连续性和边界条件

**能力边界**:
- ✅ 静磁场分析
- ✅ 毕奥-萨伐尔定律
- ✅ 矢量势方法
- ✅ 多区域多界面
- ⚠️ 需要 Gmsh 网格文件
- ❌ 不支持高频电磁（无位移电流）
- ❌ 非线性磁性材料（B-H曲线）

---

## 使用示例

### 示例1: 标准双导线仿真

```python
from devsim_examples.vectorpotential.twowire import run_twowire_magnetic_simulation

# 确保 twowire.msh 存在
result = run_twowire_magnetic_simulation(
    mesh_file="twowire.msh",
    jz_left=1.0,      # 左导线电流 +1 A/m^2
    jz_right=-1.0,    # 右导线电流 -1 A/m^2
    mu_air=1.0,       # 相对磁导率
    output_prefix="twowire_field"
)

print(f"磁场Bx分布: {result['magnetic_field']['air']['Bx']}")
```

### 示例2: 不同材料磁导率

```python
result = run_twowire_magnetic_simulation(
    mu_air=1.0,
    mu_iron=1000.0,   # 铁磁材料
    jz_left=10.0,
    jz_right=-10.0,
)
```

## 结果分析

### 磁场分布
从输出文件可视化:
- Az: 矢量势分布
- Bx, By: 磁场分量
- B = √(Bx² + By²): 磁场强度

### 理论验证
对于两条平行长直导线:
- 导线间: 磁场增强（同向）或抵消（反向）
- 远处: 偶极子场分布（~1/r²）

### 磁场线
从矢量势等值线可得磁场线

## 应用场景

1. **电感器设计**: 计算线圈磁场分布
2. **电磁兼容性**: 分析导线间磁场耦合
3. **电机设计**: 定子-转子磁场
4. **磁传感器**: 磁场检测器设计

## 扩展

如需更复杂的电磁仿真，考虑：
- 时谐分析（AC磁场）
- 涡流计算
- 磁饱和效应

## 参考资料

- 原始示例: `examples/vectorpotential/`
- 电磁理论: Jackson, "Classical Electrodynamics"
