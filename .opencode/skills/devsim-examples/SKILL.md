# DEVSIM Examples Skill

DEVSIM 官方示例代码库，提供参数化的器件仿真模板。所有示例代码基于官方 examples 目录改造，保留原始实现逻辑，增加参数化接口。

## 目录结构

```
devsim-examples/
├── SKILL.md                    # 本文档 - 总能力说明
├── diode/                      # 二极管器件示例
│   ├── diode_1d.py            # 一维PN结二极管
│   ├── diode_1d_custom.py     # 一维自定义二极管
│   ├── diode_2d.py            # 二维PN结二极管
│   ├── gmsh_diode2d.py        # Gmsh网格二维二极管
│   ├── gmsh_diode3d.py        # Gmsh网格三维二极管
│   ├── tran_diode.py          # 瞬态二极管仿真
│   ├── ssac_diode.py          # 小信号AC分析
│   ├── laux2d.py              # 2D LAUX模型二极管
│   ├── laux3d.py              # 3D LAUX模型二极管
│   ├── diode_common.py        # 共享模块
│   ├── laux_common.py         # LAUX模型共享模块
│   └── README.md              # 详细说明
├── capacitance/                # 电容/静电场示例
│   ├── cap1d.py               # 一维电容
│   ├── cap2d.py               # 二维电容
│   └── README.md
├── mobility/                   # 迁移率模型示例
│   ├── gmsh_mos2d.py          # 2D MOS结构迁移率
│   ├── gmsh_mos2d_kla.py      # KLA迁移率模型
│   ├── pythonmesh2d.py        # Python网格2D仿真
│   └── README.md
├── bioapp1/                    # 生物应用示例
│   ├── bioapp1_2d.py          # 2D生物电应用
│   ├── bioapp1_3d.py          # 3D生物电应用
│   └── README.md
├── vectorpotential/            # 矢量势示例
│   ├── twowire.py             # 双导线磁场
│   └── README.md
└── common/                     # 共享工具
    └── __init__.py
```

## 快速参考

### 按器件类型分类

| 器件类型 | 维度 | 示例文件 | 核心能力 |
|---------|------|---------|---------|
| PN结二极管 | 1D | `diode/diode_1d.py` | DC IV特性、SRH复合、漂移扩散 |
| PN结二极管 | 2D | `diode/diode_2d.py` | 2D电势分布、电流分布 |
| PN结二极管 | 2D | `diode/gmsh_diode2d.py` | Gmsh网格导入、复杂几何 |
| PN结二极管 | 3D | `diode/gmsh_diode3d.py` | 3D器件仿真、Gmsh网格 |
| 二极管 | 1D | `diode/tran_diode.py` | 瞬态响应、时间依赖仿真 |
| 二极管 | 1D | `diode/ssac_diode.py` | 小信号AC分析、C-V特性 |
| MOS电容 | 2D | `mobility/gmsh_mos2d.py` | 栅压扫描、反型层形成 |
| 平板电容 | 1D | `capacitance/cap1d.py` | 静电场、电势分布 |
| 平板电容 | 2D | `capacitance/cap2d.py` | 2D边缘电场、寄生电容 |
| 生物电/DNA检测 | 2D | `bioapp1/bioapp1_2d.py` | 离子通道、纳米孔检测 |
| 生物电/DNA检测 | 3D | `bioapp1/bioapp1_3d.py` | 3D生物分子检测 |
| 静磁场 | 3D | `vectorpotential/twowire.py` | 双导线磁场、矢量势方法 |

### 按仿真类型分类

| 仿真类型 | 适用示例 | 说明 |
|---------|---------|------|
| 稳态DC | diode_1d/2d, cap1d/2d | 偏置扫描、IV曲线 |
| 瞬态 | tran_diode | 脉冲响应、开关特性 |
| 小信号AC | ssac_diode | 电容-电压特性、频率响应 |
| 静电场 | cap1d/2d | 仅泊松方程 |

## 使用方式

### 方式1：直接导入函数

```python
from devsim_examples.diode.diode_1d import run_diode_1d_simulation

# 使用默认参数运行
result = run_diode_1d_simulation()

# 自定义参数
result = run_diode_1d_simulation(
    device_name="MyDiode",
    region_name="MyRegion",
    n_doping=1e18,          # n区掺杂 (cm^-3)
    p_doping=1e16,          # p区掺杂 (cm^-3)
    temperature=300,        # 温度 (K)
    junction_position=0.5e-5,  # 结位置 (cm)
    max_voltage=0.5,        # 最大偏置 (V)
    voltage_step=0.1,       # 偏置步长 (V)
    output_file="diode_result.dat"
)
```

### 方式2：通过 devsim-controller skill 调用

研究计划应当引用具体的能力标识，由 controller 匹配到对应示例：

```yaml
# 研究计划示例
simulation_tasks:
  - task_id: "task_001"
    capability: "diode_1d_dc_iv"           # 能力标识
    description: "硅二极管IV特性仿真"
    parameters:
      n_doping: 1e18
      p_doping: 1e16
      temperature: 300
      max_voltage: 1.0
```

### 方式3：使用智能网格（推荐）

启用 `devsim-simulation` 的物理驱动网格原则，自动优化网格密度：

```python
from devsim_examples import run_diode_1d_simulation

result = run_diode_1d_simulation(
    p_doping=1e18,
    n_doping=1e16,
    use_intelligent_mesh=True  # 自动优化网格密度
)

# 查看使用的网格参数
print(f"优化网格密度: {result['intelligent_mesh']['mesh_density_cm']:.2e} cm")
```

智能网格原则（来自 devsim-simulation）：
- **高梯度区加密**: 掺杂梯度 > 2 orders/μm 时自动加密
- **边界细化**: 接触、界面强制细化
- **特征尺寸**: 薄层(<0.1μm)至少10个节点

详见 [INTELLIGENT_MESH.md](INTELLIGENT_MESH.md)

## 能力标识总览

每个示例代码对应一个或多个能力标识，用于精确引用：

### Diode 能力标识

| 能力标识 | 示例文件 | 描述 |
|---------|---------|------|
| `diode_1d_dc_iv` | diode/diode_1d.py | 一维二极管DC IV特性 |
| `diode_1d_custom_model` | diode/diode_1d_custom.py | 自定义物理模型二极管 |
| `diode_2d_dc_iv` | diode/diode_2d.py | 二维二极管DC IV特性 |
| `diode_2d_gmsh_mesh` | diode/gmsh_diode2d.py | Gmsh网格二维二极管 |
| `diode_3d_gmsh_mesh` | diode/gmsh_diode3d.py | Gmsh网格三维二极管 |
| `diode_1d_transient` | diode/tran_diode.py | 一维二极管瞬态响应 |
| `diode_1d_ssac_cv` | diode/ssac_diode.py | 一极管小信号AC/C-V |
| `diode_2d_laux` | diode/laux2d.py | 2D LAUX模型仿真 |
| `diode_3d_laux` | diode/laux3d.py | 3D LAUX模型仿真 |

### Capacitance 能力标识

| 能力标识 | 示例文件 | 描述 |
|---------|---------|------|
| `capacitance_1d_electrostatic` | capacitance/cap1d.py | 一维静电场电容 |
| `capacitance_2d_electrostatic` | capacitance/cap2d.py | 二维静电场电容 |

### Mobility 能力标识

| 能力标识 | 示例文件 | 描述 |
|---------|---------|------|
| `mos_2d_gmsh_mobility` | mobility/gmsh_mos2d.py | 2D MOS迁移率模型 |
| `mos_2d_kla_mobility` | mobility/gmsh_mos2d_kla.py | 2D MOS KLA迁移率 |

### Bioapp1 能力标识

| 能力标识 | 示例文件 | 描述 |
|---------|---------|------|
| `bioapp_2d_ion_channel` | bioapp1/bioapp1_2d.py | 2D离子通道仿真 |
| `bioapp_3d_nerve_signal` | bioapp1/bioapp1_3d.py | 3D神经信号传导 |

### Vectorpotential 能力标识

| 能力标识 | 示例文件 | 描述 |
|---------|---------|------|
| `magnetic_3d_twowire` | vectorpotential/twowire.py | 双导线磁场分布 |

## 参数约定

### 默认单位

所有参数使用 **CGS 单位制**（DEVSIM 默认）：

| 物理量 | 单位 | 示例值 |
|-------|------|--------|
| 长度 | cm | 1e-4 (1μm) |
| 掺杂浓度 | cm^-3 | 1e16 |
| 电压 | V | 0.5 |
| 温度 | K | 300 |
| 电流密度 | A/cm^2 | 1e-3 |
| 时间 | s | 1e-9 |

### 参数命名规范

- `*_doping`：掺杂浓度
- `*_position`：位置坐标（cm）
- `*_bias`：偏置电压（V）
- `*_thickness`：厚度（cm）
- `temperature`：温度（K）
- `mesh_*`：网格参数
- `solver_*`：求解器参数

## 能力边界

### 明确支持

- 硅基器件（Si）
- 室温（300K）和低温（77K）仿真
- 漂移扩散输运模型
- SRH复合、Auger复合
- 静电场（泊松方程）
- 简单几何结构

### 已知限制

- 不支持量子隧穿效应
- 不支持热-电耦合
- 不支持光子学方程（除了示例中明确包含的）
- Gmsh网格需要外部生成
- 材料数据库有限（主要支持Si）

### 扩展建议

如需超出能力边界的功能，建议：
1. 基于最接近的示例代码修改
2. 查阅 DEVSIM 官方文档添加自定义模型
3. 使用 devsim-simulation skill 的通用生成功能

## 版本信息

- **基于**: DEVSIM 官方 examples 目录
- **适配版本**: DEVSIM 1.x+
- **更新日期**: 2026-02

## 贡献

如需添加新的示例能力：
1. 基于现有示例代码结构
2. 提供完整的参数化接口
3. 在 README.md 中详细说明能力边界
4. 更新本文档的能力标识列表
