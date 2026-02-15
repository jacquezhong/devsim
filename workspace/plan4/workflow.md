# 研究方案四：场板（Field Plate）结构对 2D 二极管电场分布与击穿特性的调制机理

**方案来源**: workspace/方案v2.md  
**评估来源**: workspace/方案评估.md  
**可行性评级**: ✅ **完全可行 (100%)**

**执行原则**: 
- ✅ 使用 `devsim` conda环境（优先）或 `base` 环境
- ✅ 通过 `devsim-examples` skill 调用现有能力
- ❌ 禁止自主开发物理模型或求解器代码

---

## 0. 环境准备

### 0.1 激活Conda环境

```bash
# 优先尝试激活名为"devsim"的conda环境，如果不存在则使用base
conda activate devsim 2>/dev/null || conda activate base

# 验证环境
python3 -c "import devsim; print(f'DEVSIM {devsim.__version__} is ready')"
```

### 0.2 安装依赖（首次）

```bash
pip install numpy matplotlib
```

---

## 1. 学术背景与研究目的

在高压半导体器件中，电场拥挤效应会导致提前击穿。引入场板可以重新分布表面电场。本方案对比不同场板长度对击穿电压（BV）的提升效果，属于器件可靠性研究的经典课题。

**研究价值**: 功率器件可靠性，ISPSD等顶级会议常规主题

---

## 2. 技术可行性评估

### 能力匹配度分析 ✅

| 需求 | 现有能力 | 匹配状态 | 说明 |
|------|---------|---------|------|
| 2D二极管仿真 | `diode_2d_dc_iv` | ✅ **完全支持** | 直接可用 |
| 电场分布提取 | 内置功能 | ✅ 支持 | `ElectricField` 模型 |
| 反向偏压扫描 | 支持 | ✅ 支持 | 负电压扫描 |
| 几何参数 | Gmsh网格 | ⚠️ 需预生成 | 场板几何 |

**结论**: 完全匹配！只需生成含场板结构的Gmsh网格。

### 缺失环节
- **Gmsh网格**: 需要创建带场板的2D二极管网格
- **解决方式**: 提供完整的Gmsh脚本（见第6节）

---

## 3. 调用能力 ID 与步骤编排

### Step 1：反向截止态电场分析
- **能力 ID**: `diode_2d_dc_iv`
- **目的**: 获取器件内部及表面的二维电场分布云图
- **前置条件**: 需要预生成的Gmsh网格文件（含场板结构）
- **Python调用**:
```python
from devsim_examples import diode_2d_dc_iv

# 使用带场板的网格
result = diode_2d_dc_iv(
    mesh_file="diode_field_plate.msh",
    anode_doping=1e19,      # P+区掺杂
    cathode_doping=1e14,    # N区掺杂
    V_start=0,
    V_stop=-100.0,          # 反向偏压
    V_step=-5.0
)

# 提取电场分布
from devsim import get_edge_model_values
E_magnitude = get_edge_model_values(
    device="diode",
    region="ndrift",
    name="ElectricField"
)

max_E = max(E_magnitude)
print(f"峰值电场: {max_E:.2e} V/cm")
```

### Step 2：击穿点搜索（扫描分析）
- **能力 ID**: `diode_2d_dc_iv`（配合高压扫描）
- **目的**: 提取 $I-V$ 曲线，直至电流剧增点判定为击穿
- **Python调用**:
```python
# 逐步增加反向偏压，直到击穿
voltages = [-10, -25, -50, -75, -100, -125, -150, -200]
currents = []

for v in voltages:
    result = diode_2d_dc_iv(
        mesh_file="diode_field_plate.msh",
        V_start=v-5,
        V_stop=v,
        V_step=-2.5
    )
    currents.append(result['current'][-1])
    
    # 检查是否击穿（电流剧增）
    if len(currents) > 1 and currents[-1] > 10 * currents[-2]:
        BV = v
        print(f"击穿电压: {BV} V")
        break
```

---

## 4. 参数设置指南

### 几何参数
- **场板长度 L_fp**: 2-10 μm（图像33-34中的具体数值）
- **绝缘层厚度 t_ox**: 0.1-0.5 μm（图像35-36中的具体数值）

### 物理参数
- **P+区掺杂**: $10^{19}$ cm⁻³
- **N区掺杂**: $10^{14}$ cm⁻³
- **材料击穿场强极限**: Si约 $3 \times 10^5$ V/cm

### 执行设置
反向偏压扫描，起始 0V，终止 -200V，步长根据收敛性自动调整

---

## 5. 实施步骤与时间表

### Phase 1: Gmsh网格生成（2天）

#### 5.1 创建Gmsh几何脚本

创建文件 `diode_field_plate.geo`:

```geo
// ============================================================
// 带场板的高压二极管 - 2D截面
// ============================================================

// --- 几何参数 (单位: cm) ---
L_device = 50e-4;        // 器件长度: 50μm
L_pplus  = 5e-4;         // P+区宽度: 5μm
H_n      = 20e-4;        // N区高度: 20μm
H_pplus  = 2e-4;         // P+区高度: 2μm

// 场板参数 (可变量)
L_fp_extend = 5e-4;      // 场板超出P+区的长度: 5μm
T_ox        = 0.2e-4;    // 绝缘层厚度: 0.2μm (200nm)
T_fp        = 0.5e-4;    // 场板厚度: 0.5μm
H_air       = 5e-4;      // 空气层高度: 5μm

// 计算场板总长度
L_fp_total = L_pplus + L_fp_extend;

// 网格控制参数
Mesh_Junction = 0.05e-4;    // 结区细密网格: 50nm
Mesh_FP_Edge  = 0.05e-4;    // 场板边缘细密: 50nm
Mesh_Normal   = 0.2e-4;     // 正常网格: 200nm
Mesh_Coarse   = 1.0e-4;     // 粗网格: 1μm

// --- 定义关键点 ---
// 原点设在左下角
// P+区 (阳极)
Point(1) = {0, 0, 0, Mesh_Junction};
Point(2) = {L_pplus, 0, 0, Mesh_Junction};
Point(3) = {L_pplus, H_pplus, 0, Mesh_Junction};
Point(4) = {0, H_pplus, 0, Mesh_Junction};

// N区 (漂移区)
Point(5) = {L_device, 0, 0, Mesh_Normal};
Point(6) = {L_device, H_n, 0, Mesh_Normal};
Point(7) = {0, H_n, 0, Mesh_Normal};

// 绝缘层 (Oxide)
Point(8) = {0, H_n + T_ox, 0, Mesh_Normal};
Point(9) = {L_device, H_n + T_ox, 0, Mesh_Normal};

// 场板 (Field Plate)
Point(10) = {0, H_n + T_ox, 0, Mesh_FP_Edge};
Point(11) = {L_fp_total, H_n + T_ox, 0, Mesh_FP_Edge};
Point(12) = {L_fp_total, H_n + T_ox + T_fp, 0, Mesh_FP_Edge};
Point(13) = {0, H_n + T_ox + T_fp, 0, Mesh_FP_Edge};

// 空气层
Point(14) = {0, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse};
Point(15) = {L_device, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse};

// --- 定义线 (Line) ---
// P+区边界
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// N区边界
Line(5) = {2, 5};
Line(6) = {5, 6};
Line(7) = {6, 7};
Line(8) = {7, 4};
Line(9) = {3, 6};

// 绝缘层边界
Line(10) = {8, 9};
Line(11) = {9, 6};
Line(12) = {7, 8};

// 场板边界
Line(13) = {10, 11};
Line(14) = {11, 12};
Line(15) = {12, 13};
Line(16) = {13, 10};

// 空气层边界
Line(17) = {13, 14};
Line(18) = {14, 15};
Line(19) = {15, 12};
Line(20) = {15, 9};

// --- 定义线环和面 ---
// P+区
Line Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// N区
Line Loop(2) = {5, 6, -9, -2};
Plane Surface(2) = {2};

// 绝缘层
Line Loop(3) = {10, -11, -7, -6, 9, 3, -8, 12};
Plane Surface(3) = {3};

// 场板
Line Loop(4) = {13, 14, 15, 16};
Plane Surface(4) = {4};

// 空气层 (上)
Line Loop(5) = {15, 17, 18, 19};
Plane Surface(5) = {5};

// 空气层 (右侧)
Line Loop(6) = {10, 20, -18, -17, -16, -13, -14, -19};
Plane Surface(6) = {6};

// --- 自适应网格控制 ---
// 在PN结附近加密
Field[1] = Distance;
Field[1].EdgesList = {2};
Field[1].NNodesByEdge = 100;

Field[2] = Threshold;
Field[2].IField = 1;
Field[2].LcMin = Mesh_Junction;
Field[2].LcMax = Mesh_Normal;
Field[2].DistMin = 0.2e-4;
Field[2].DistMax = 2.0e-4;

// 在场板边缘加密
Field[3] = Distance;
Field[3].EdgesList = {14};
Field[3].NNodesByEdge = 100;

Field[4] = Threshold;
Field[4].IField = 3;
Field[4].LcMin = Mesh_FP_Edge;
Field[4].LcMax = Mesh_Normal;
Field[4].DistMin = 0.2e-4;
Field[4].DistMax = 2.0e-4;

// 合并网格控制
Field[5] = Min;
Field[5].FieldsList = {2, 4};
Background Field = 5;

// --- 物理组 ---
Physical Line("anode") = {1};
Physical Line("cathode") = {6};
Physical Line("field_plate") = {15};
Physical Line("oxide_interface") = {10};

Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2};
Physical Surface("oxide") = {3};
Physical Surface("fieldplate_metal") = {4};
Physical Surface("air") = {5, 6};
```

#### 5.2 批量生成不同场板长度的网格

```bash
# 创建参数化生成脚本
# generate_fp_meshes.sh

for L_fp in 2 4 6 8 10; do
    # 修改场板长度参数
    sed "s/L_fp_extend = 5e-4/L_fp_extend = ${L_fp}e-4/" diode_field_plate.geo > diode_fp_L${L_fp}.geo
    
    # 生成网格
    gmsh diode_fp_L${L_fp}.geo -2 -o diode_fp_L${L_fp}.msh
    
    echo "Generated mesh for L_fp = ${L_fp} μm"
done
```

或者使用Python脚本：

```python
# generate_fp_meshes.py
import subprocess

def generate_fp_geo(l_fp_um, t_ox_um, filename):
    """生成特定场板参数的Gmsh脚本"""
    geo_template = f"""// 场板长度: {l_fp_um}μm, 绝缘层厚度: {t_ox_um}μm
L_fp_extend = {l_fp_um}e-4;
T_ox = {t_ox_um}e-4;
// ... (其余几何定义与模板相同)
"""
    with open(filename, 'w') as f:
        f.write(geo_template)

# 批量生成不同场板长度的网格
for l_fp in [2, 4, 6, 8, 10]:  # μm
    geo_file = f"diode_fp_L{l_fp}.geo"
    generate_fp_geo(l_fp, 0.2, geo_file)
    subprocess.run(["gmsh", geo_file, "-2"])
    print(f"Generated: diode_fp_L{l_fp}.msh")
```

#### 5.3 验证网格

```python
from devsim import create_gmsh_mesh, get_region_list, get_contact_list

# 验证网格导入
create_gmsh_mesh(file="diode_fp_L5.msh", mesh="test")
print("Regions:", get_region_list(mesh="test"))
print("Contacts:", get_contact_list(mesh="test"))
# 应输出: ['pplus', 'ndrift', 'oxide', 'fieldplate_metal', 'air']
#         ['anode', 'cathode', 'field_plate', 'oxide_interface']
```

### Phase 2: 反向偏压扫描（2-3天）

```python
from devsim_examples import diode_2d_dc_iv
from devsim import get_edge_model_values
import numpy as np
import matplotlib.pyplot as plt

# 扫描不同场板长度
L_fp_values = [2, 4, 6, 8, 10]  # μm
BV_results = {}
E_field_results = {}

for L_fp in L_fp_values:
    mesh_file = f"diode_fp_L{L_fp}.msh"
    
    # 逐步增加反向偏压
    voltages = [-10, -25, -50, -75, -100, -125, -150, -200, -250, -300]
    currents = []
    max_E_fields = []
    
    prev_solution = None
    
    for v in voltages:
        try:
            result = diode_2d_dc_iv(
                mesh_file=mesh_file,
                anode_doping=1e19,
                cathode_doping=1e14,
                V_start=v-10 if prev_solution else 0,
                V_stop=v,
                V_step=-2.5
            )
            
            # 记录电流
            current_at_v = result['current'][-1]
            currents.append((v, current_at_v))
            
            # 提取峰值电场
            E_field = get_edge_model_values(
                device="diode",
                region="ndrift",
                name="ElectricField"
            )
            max_E = max(E_field)
            max_E_fields.append((v, max_E))
            
            # 检查是否击穿（电流剧增或电场达到临界值）
            if len(currents) > 1:
                current_ratio = abs(current_at_v / currents[-2][1])
                if current_ratio > 10 or max_E > 3e5:  # 击穿判据
                    BV = v
                    print(f"L_fp={L_fp}μm: 击穿电压 = {BV} V")
                    break
            
            prev_solution = result
            
        except Exception as e:
            print(f"在{v}V处未能收敛: {e}")
            break
    
    BV_results[L_fp] = BV
    E_field_results[L_fp] = max_E_fields

# 保存结果
np.savez('breakdown_analysis.npz',
         L_fp_values=L_fp_values,
         BV_results=BV_results,
         E_field_results=E_field_results)
```

### Phase 3: 电场分布分析（2天）

```python
# 在关键偏压点（如-100V）提取电场分布
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# 选择有代表性的场板长度
L_fp_selected = [2, 6, 10]  # μm

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, L_fp in enumerate(L_fp_selected):
    mesh_file = f"diode_fp_L{L_fp}.msh"
    
    # 在-100V偏压下仿真
    result = diode_2d_dc_iv(
        mesh_file=mesh_file,
        anode_doping=1e19,
        cathode_doping=1e14,
        V_start=-90,
        V_stop=-100,
        V_step=-2.5
    )
    
    # 提取2D坐标和电场
    from devsim import get_node_model_values
    
    x = get_node_model_values(device="diode", region="ndrift", name="x")
    y = get_node_model_values(device="diode", region="ndrift", name="y")
    E = get_node_model_values(device="diode", region="ndrift", name="ElectricField")
    
    # 绘制电场分布
    scatter = axes[idx].scatter(x, y, c=E, cmap='hot', s=1, norm=LogNorm())
    axes[idx].set_title(f'L_fp = {L_fp} μm', fontsize=12)
    axes[idx].set_xlabel('X (cm)')
    axes[idx].set_ylabel('Y (cm)')
    
    # 找到峰值电场位置
    max_E_idx = np.argmax(E)
    axes[idx].scatter(x[max_E_idx], y[max_E_idx], c='cyan', s=50, marker='x')
    
    plt.colorbar(scatter, ax=axes[idx], label='Electric Field (V/cm)')

plt.tight_layout()
plt.savefig('electric_field_distribution.png', dpi=300)
```

### Phase 4: BV vs 场板长度关系（1天）

```python
# 分析击穿电压与场板长度的关系

L_fp_list = list(BV_results.keys())
BV_list = [BV_results[L] for L in L_fp_list]

plt.figure(figsize=(10, 6))
plt.plot(L_fp_list, BV_list, 'bo-', linewidth=2, markersize=8)
plt.xlabel('Field Plate Length (μm)', fontsize=12)
plt.ylabel('Breakdown Voltage (V)', fontsize=12)
plt.title('Breakdown Voltage vs Field Plate Length', fontsize=14)
plt.grid(True)

# 添加拟合曲线（非线性关系）
from scipy.optimize import curve_fit

def bv_model(L, BV0, k, alpha):
    """击穿电压模型: BV = BV0 * (1 + k * L^alpha)"""
    return BV0 * (1 + k * np.power(L, alpha))

popt, _ = curve_fit(bv_model, L_fp_list, BV_list, p0=[100, 0.1, 0.5])
L_fit = np.linspace(min(L_fp_list), max(L_fp_list), 100)
BV_fit = bv_model(L_fit, *popt)

plt.plot(L_fit, BV_fit, 'r--', linewidth=2, 
         label=f'Fit: BV = {popt[0]:.1f}*(1+{popt[1]:.3f}*L^{popt[2]:.2f})')
plt.legend()

plt.savefig('bv_vs_fp_length.png', dpi=300)

print(f"拟合参数: BV0={popt[0]:.1f}, k={popt[1]:.4f}, α={popt[2]:.3f}")
```

---

## 6. 结果分析与结论

### 分析方法
提取 PN 结边缘与场板边缘的峰值电场 $E_{junction}$ 和 $E_{fieldplate}$：

### 预期结论
- 证明场板通过引入"电场双峰"效应降低了单一位置的场强
- 给出场板长度与击穿电压增加的非线性关系模型

### 关键发现预期
1. **电场双峰**: 无场板时单峰，有场板时双峰分布
2. **最优场板长度**: 存在使BV最大化的最佳L_fp
3. **绝缘层厚度影响**: t_ox影响场板耦合效率

### 学术产出建议
- **目标期刊**: IEEE Electron Device Letters (EDL), Solid-State Electronics
- **目标会议**: ISPSD (International Symposium on Power Semiconductor Devices and ICs)
- **创新点**: 场板参数优化方法 + 电场双峰效应定量分析

---

## 7. 电场双峰效应理论

### 无场板时的电场分布
$$E(x) = E_{max} \cdot \exp\left(-\frac{x}{W_{dep}}\right)$$

单峰分布，峰值在PN结边缘。

### 有场板时的电场分布
场板引入额外的电场峰值：

$$E_{total}(x) = E_{junction}(x) + E_{fieldplate}(x)$$

其中：
- $E_{junction}$: PN结附近的电场
- $E_{fieldplate}$: 场板边缘的电场

### 击穿电压提升模型
$$BV = BV_0 \cdot \left(1 + k \cdot L_{fp}^{\alpha}\right)$$

其中：
- $BV_0$: 无场板时的击穿电压
- $k$: 场板效率系数
- $\alpha$: 非线性指数（通常0.3-0.7）

---

## 8. 风险与对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 高压仿真不收敛 | 中 | 高 | 逐步增加偏压，使用前一解作为初始猜测 |
| 网格精度不足 | 中 | 中 | 在结区和场板边缘加密网格（50nm） |
| 击穿判据不明确 | 低 | 中 | 同时使用电流剧增和电场临界值判据 |

---

## 9. 需要的参数确认

以下参数需要从方案文档的图像中提取具体数值：

- **场板长度 L_fp**: 图像33-34中的具体数值范围
- **绝缘层厚度 t_ox**: 图像35-36中的具体数值

**建议默认值**（如无法获取图像数值）：
- L_fp = 2-10 μm（功率器件典型范围）
- t_ox = 0.2 μm（200nm SiO₂）
- 器件尺寸: 50μm × 20μm (高压功率二极管)

---

## 10. 仿真技巧

### 高压仿真收敛技巧
```python
# 逐步增加反向偏压
voltages = [-10, -25, -50, -100, -150, -200]
prev_solution = None

for v in voltages:
    try:
        result = diode_2d_dc_iv(
            mesh_file="diode_fp_L5.msh",
            V_start=v-10 if prev_solution else 0,
            V_stop=v,
            V_step=-2.5
        )
        prev_solution = result
    except:
        print(f"在{v}V处未能收敛")
        break
```

### 电场可视化
```python
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# 提取2D坐标和电场
x = get_node_model_values(device="diode", region="ndrift", name="x")
y = get_node_model_values(device="diode", region="ndrift", name="y")
E = get_node_model_values(device="diode", region="ndrift", name="ElectricField")

# 绘制热力图
plt.scatter(x, y, c=E, cmap='hot', s=1, norm=LogNorm())
plt.colorbar(label='Electric Field (V/cm)')
plt.title('Electric Field Distribution')
plt.savefig('efield.png', dpi=300)
```

---

## 11. 参考文献

1. B. J. Baliga, "Power Semiconductor Device Figure of Merit for High-Frequency Applications", IEEE Electron Device Letters, 1989.
2. C. Hu, "Future CMOS Scaling and Reliability", Proceedings of the IEEE, 1996.
3. T. Fujihira et al., "Theory of Semiconductor Superjunction Devices", Jpn. J. Appl. Phys., 1997.
4. DEVSIM TCAD Manual: diode_2d_dc_iv capability.

---

**创建时间**: 2026-02-14  
**版本**: v1.0  
**状态**: 需要预生成Gmsh网格后执行
