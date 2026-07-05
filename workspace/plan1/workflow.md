# 研究方案一：基于开源 DEVSIM 的二极管反向恢复可复现仿真基准

**当前定位**: 从“高压功率二极管优化”调整为“开放、透明、可复现的反向恢复仿真与指标提取基准”  
**综述依据**: `workspace/plan1/review.md`  
**核心目标**: 建立一个低成本 1D PN/PIN 二极管 benchmark，公开器件定义、网格、偏置流程、瞬态波形和 `Q_rr/I_rrm/t_rr` 指标提取脚本。  
**当前补强**: 已加入参考面积归一化、目标正向电流密度扫描和正式论文稿修订。  

---

## 0. 研究立场

本研究不声称 DEVSIM 可替代 Synopsys Sentaurus、Silvaco 等商业 TCAD，也不以“发现新的反向恢复物理机制”为目标。商业 TCAD 在模型库、复杂结构、工艺校准和工业预测能力方面更强；本研究的价值在于补充一个开源、可检查、可复跑的基准流程。

更准确的研究贡献是：

- 给出一个标准化 1D 硅 PN/PIN 二极管反向恢复测试问题。
- 公开 DEVSIM 实现、输入参数、网格设置、求解流程和指标提取代码。
- 提供 reference waveforms 和 reference metrics。
- 通过寿命扫描、目标正向电流密度扫描、时间步长收敛和网格收敛展示该 benchmark 的稳定性和边界。
- 将旧版公式估算结果降级为“解析趋势参考”，新结论以 DEVSIM DC/transient 直接提取结果为准。

---

## 1. 环境准备

### 1.1 Conda 环境

```bash
conda activate devsim 2>/dev/null || conda activate base
python3 -c "import devsim; print(f'DEVSIM {devsim.__version__} is ready')"
```

如缺少依赖：

```bash
pip install devsim numpy matplotlib
```

### 1.2 计划使用的本地能力

- `devsim`
- `devsim.python_packages.simple_physics`
- `.opencode/skills/devsim-examples/diode/diode_1d.py`
- `.opencode/skills/devsim-examples/diode/tran_diode.py`

注意：现有 `tran_diode.py` 示例需要扩展，因为它目前主要保存时间点和电路节点状态，不足以直接形成 `Q_rr/I_rrm/t_rr` benchmark。新脚本应在每个瞬态时间点显式保存接触电流或电路电流。

---

## 2. 现有资产复用策略

### 2.1 可以继续使用

| 文件/目录 | 用途 |
|---|---|
| `review.md` | 文献综述和 benchmark 立意依据 |
| `draft_modified.md` | 旧论文素材库，不再作为本文主线 |
| `paper_draft_open_benchmark.md` | 新研究主线的 Markdown 初稿 |
| `基于开源DEVSIM的二极管反向恢复可复现仿真基准.docx` | 依据新稿生成的 Word 初稿 |
| `paper_formal_open_benchmark.md` | 面向中文期刊风格重写的正式论文 Markdown 稿 |
| `基于开源DEVSIM的硅PIN二极管反向恢复可复现仿真基准研究.docx` | 正式论文 Word 初稿 |
| `generate_docx.py` / `generate_docx_semantic*.py` | 后续文档生成逻辑可复用 |
| `generate_paper_figures*.py` | 图表风格、字体和结构图逻辑可复用 |
| `figures/final/fig1_structure.png` | 可作为初版结构示意图，后续需按 benchmark 参数更新 |

### 2.2 只能作为解析/探索性参考

| 文件 | 限制 |
|---|---|
| `data/final/lifetime_results.json` | `Q_rr/R_on` 主要来自解析或经验估算，不可作为 benchmark reference |
| `data/final/doping_results.json` | `BV/R_on` 主要来自简化公式，不可作为 TCAD 直接结果 |
| `data/final/final_scientific_report.json` | 可作为旧版结论记录，但新研究中需明确标注为旧探索结果 |

### 2.3 建议新增目录

```text
workspace/plan1/
  benchmark/
    config.json
    run_dc_benchmark.py
    run_reverse_recovery_benchmark.py
    extract_metrics.py
    generate_benchmark_figures.py
  data/benchmark/
    raw/
    metrics/
    reference/
  figures/benchmark/
  benchmark_README.md
```

---

## 3. Benchmark 问题定义

### 3.1 基准器件

优先采用 1D 硅 PN 或 PIN 二极管。初始阶段建议 PN 结构，确保计算代价低、收敛稳定；若瞬态结果过弱，再扩展到 PIN 结构以增强存储电荷效应。

建议初始参数：

| 参数 | 建议值 | 说明 |
|---|---:|---|
| 器件长度 | `1e-4 cm` | 1 μm，低成本；如需更强存储效应可扩展到 10 μm |
| 结位置 | `0.5e-4 cm` | 居中 |
| P 区掺杂 | `1e16 cm^-3` | 基准值 |
| N 区掺杂 | `1e16 cm^-3` 或 `1e17 cm^-3` | 先用对称/近对称掺杂保证稳定 |
| 温度 | `300 K` | 基准温度 |
| 寿命 | `1e-8` 到 `1e-5 s` | 主扫描变量 |
| 结区网格 | `1e-7, 5e-8, 1e-8 cm` | 用于网格收敛 |

说明：旧方案中的 `1e19 cm^-3` 高掺杂和 `100 μm` 高压设定更偏“功率器件叙事”，但会提高收敛难度，也不利于先建立 benchmark。新方案先追求标准化、可复现和低成本。

### 3.2 偏置流程

反向恢复 benchmark 必须明确偏置历史。建议采用三段流程：

1. **平衡态**：0 V 求解 DC。
2. **正向预偏置**：施加 `V_fwd = +0.8 V`，保持若干时间步或求解到准稳态。
3. **反向阶跃**：切换到 `V_rev = -1 V` 或 `-2 V`，记录瞬态电流波形。

已实现目标电流模式：先通过 DC I-V 找到达到 `I_target` 的 `V_fwd`，再以该正向电流作为统一初始条件。该模式已用于寿命扫描、时间步长扫描和目标正向电流扫描。当前 benchmark 设置参考面积 `A = 1 cm^2`，主要论文结果报告为 `J = I/A`、`Q_rr/A` 和 `Q_stored/A`。

---

## 4. 实验系列

### Level 0: DC 基准

**目的**: 验证基本漂移-扩散器件设置，提供导通损耗参考。

输入：

- 固定器件结构与寿命。
- 扫描 `V = 0 -> 1.0 V`，步长 `0.02` 或 `0.05 V`。

输出：

- `dc_iv.csv/json`
- `voltage_V`
- `contact_current_A`
- `converged`
- `V_F @ I_target`
- `R_diff = dV/dI`

注意：现有 `diode_1d.py` 返回 `bias_points`，但未保存电流数组。新 benchmark 脚本必须直接调用 DEVSIM 接触电流接口或解析输出，保存真实电流值。

### Level 1: 单点反向恢复基准

**目的**: 建立一个最小可复现 transient case。

基准参数：

- `tau_n = tau_p = 1e-6 s`
- `V_fwd = +0.8 V`
- `V_rev = -1 V`
- `dt = 1e-9` 或根据收敛情况调整
- `t_stop = 1e-6 s`

输出：

- 原始瞬态波形 `time_s, current_A, voltage_V`
- `I_rrm`: 最大反向恢复电流
- `t_peak`: 反向峰值时间
- `t_rr`: 恢复时间，阈值定义为反向峰值的 10%
- `Q_rr`: 反向电流积分，积分区间必须在脚本中固定
- 收敛状态和失败时间点

### Level 2: 寿命扫描基准

**目的**: 展示寿命控制对反向恢复波形和导通损耗的趋势性影响。

寿命点：

```python
lifetimes = [1e-8, 1e-7, 1e-6, 1e-5]
```

每个寿命点执行：

- DC I-V
- 正向预偏置 transient 或准稳态
- 反向阶跃 transient
- 指标提取

主图：

- `I(t)` 反向恢复波形叠加图
- `Q_rr vs tau`
- `I_rrm vs tau`
- `t_rr vs tau`
- `V_F @ I_target vs Q_rr` 权衡图

说明：这一层是论文主体实验。它不应再使用旧的 `Q_rr = tau * J_F` 公式生成结果，而应从瞬态电流波形积分得到。

### Level 2b: 目标正向电流密度扫描基准

**目的**: 验证 benchmark 不只适用于单一工作点，并检查正向注入强度对恢复面电荷的影响。

当前已完成：

- 固定 `tau = 1e-6 s`。
- 固定 `dt = 2e-9 s` 和默认网格。
- 扫描 `I_target = 1e-4, 1e-3, 1e-2 A`；在参考面积 `1 cm^2` 下等价于 `J_F = 1e-4, 1e-3, 1e-2 A/cm^2`。
- 输出 `metrics_forward_current_sweep.json` 和 `fig_pub_forward_current_sweep.png/pdf`。

### Level 3: 数值可复现性基准

**目的**: 让实验具备 benchmark 特征，而不是普通案例。

#### 4.4.1 时间步长收敛

固定结构和寿命，测试：

```python
time_steps = [5e-9, 2e-9, 1e-9]
```

比较：

- `Q_rr` 相对变化
- `I_rrm` 相对变化
- `t_rr` 相对变化
- 运行时间
- 收敛失败点

#### 4.4.2 网格收敛

固定时间步长和寿命，测试：

```python
mesh_densities = [1e-7, 5e-8, 1e-8]
```

比较同上。

### Level 4: 可选扩展

在 Level 0-3 稳定后再考虑：

- 反向电压扫描：`V_rev = -1, -2, -5 V`
- 温度扫描：`300, 350, 400 K`
- PIN 结构版本
- 简单外部电路或电流源切换
- 与解析模型 `Q_s ~ I_F * tau` 的趋势对比

这些扩展不是第一阶段必要条件，避免计算复杂度过早失控。

---

## 5. 指标定义

### 5.1 电流符号约定

必须在 `extract_metrics.py` 中固定电流方向。建议统一为：

- 正向导通电流为正。
- 反向恢复电流为负。

若 DEVSIM 接触电流符号相反，应在数据保存阶段转换，并记录 `current_sign_convention`。

### 5.2 `I_rrm`

```python
I_rrm = abs(min(current_after_reverse_step))
```

### 5.3 `Q_rr`

建议定义为：

```python
Q_rr = integral(abs(I_reverse), t_start, t_end)
```

其中：

- `t_start`: 反向阶跃发生时刻。
- `t_end`: 电流恢复到 `0.1 * I_rrm` 且之后保持接近稳态的第一个时间点。

若波形没有清晰恢复，记录 `t_end = t_stop` 并标注 `recovery_incomplete = true`。

### 5.4 `t_rr`

```python
t_rr = t_end - t_start
```

恢复阈值默认取 `10% I_rrm`，并在结果 JSON 中记录。

### 5.5 `V_F @ I_target`

从 DC I-V 曲线插值得到。若电流未达到目标值，记录为 `null` 并标注 `target_not_reached = true`。

---

## 6. 数据格式

### 6.1 原始波形

`data/benchmark/raw/recovery_vfixed_tau_1e-06_dt_2e-09_mesh_2e-07.json`

```json
{
  "case_id": "recovery_vfixed_tau_1e-06_dt_2e-09_mesh_2e-07",
  "parameters": {
    "initial_condition": "fixed_voltage",
    "device_length_cm": 3e-4,
    "junction_position_cm": 5e-5,
    "p_doping_cm3": 1e17,
    "n_doping_cm3": 1e17,
    "taun_s": 1e-6,
    "taup_s": 1e-6,
    "temperature_K": 300,
    "v_forward_V": 0.8,
    "forward_current_A": 378.6,
    "v_reverse_V": -1.0,
    "time_step_s": 2e-9
  },
  "waveform": {
    "format": "npz",
    "file": "data/benchmark/waveforms/recovery_vfixed_tau_1e-06_dt_2e-09_mesh_2e-07.npz",
    "points": 51
  },
  "stored_charge": {
    "stored_mobile_charge_C": 1.87e-6
  },
  "solver": {
    "converged": true,
    "failed_at_s": null
  }
}
```

### 6.2 指标结果

`data/benchmark/metrics/metrics_lifetime_sweep.json`

```json
[
  {
    "case_id": "recovery_ifixed_tau_1e-06_dt_2e-09_mesh_2e-07",
    "tau_s": 1e-6,
    "target_current_A": 1e-3,
    "v_forward_V": 0.426,
    "forward_current_A": 1.000e-3,
    "I_rrm_A": 0.0,
    "Q_rr_C": 0.0,
    "t_rr_s": 0.0,
    "stored_mobile_charge_C": 0.0,
    "converged": true,
    "recovery_incomplete": false
  }
]
```

---

## 7. 实施顺序

### Phase 1: 最小可行 benchmark

1. 创建 `benchmark/config.json`。
2. 创建 `benchmark/extract_metrics.py`。
3. 创建 `benchmark/run_dc_benchmark.py`，确保能保存真实 DC 电流。
4. 创建 `benchmark/run_reverse_recovery_benchmark.py`，确保能保存 transient 电流波形。
5. 运行单个 `tau=1e-6` case。
6. 生成最小图：DC I-V、单点反向恢复波形。

### Phase 2: 寿命扫描

1. 跑 `tau = 1e-8, 1e-7, 1e-6, 1e-5`。
2. 保存所有 raw waveforms。
3. 提取并保存 metrics。
4. 生成寿命扫描图。

### Phase 3: 可复现性测试

1. 时间步长收敛。
2. 网格收敛。
3. 目标正向电流密度扫描。
4. 生成误差表和收敛图。
5. 写 `benchmark_README.md`，说明如何复跑、如何比较误差。

### Phase 4: 文稿重写

1. 已根据 `review.md` 和 benchmark 结果形成报告型新稿 `paper_draft_open_benchmark.md`。
2. 已另写面向中文期刊风格的正式论文稿 `paper_formal_open_benchmark.md`。
3. 已生成独立 Word 初稿 `基于开源DEVSIM的硅PIN二极管反向恢复可复现仿真基准研究.docx`，旧稿 `draft_modified.md` 未纳入新文档。
4. 已按审稿风险补充参考面积归一化、目标正向电流密度扫描和可复现性文献论证。
5. 正式投稿前仍需继续核查参考文献、按目标期刊模板调整格式，并补充外部电路或跨工具对比等后续实验。

---

## 8. 预期产出

### 8.1 工程产物

- `benchmark/` 可运行脚本。
- `data/benchmark/raw/` 原始波形。
- `data/benchmark/metrics/` 指标数据。
- `data/benchmark/reference/` 推荐 reference 结果。
- `figures/benchmark/` 图表。
- `benchmark_README.md`。

### 8.2 论文/报告题目建议

中文：

> 基于开源 DEVSIM 的硅 PN 二极管反向恢复可复现仿真基准与寿命权衡分析

英文：

> An Open DEVSIM Benchmark for Reproducible Reverse-Recovery Simulation and Lifetime Trade-off Analysis in Silicon PN Diodes

### 8.3 核心结论边界

可以说：

- 本研究建立了一个开放、透明、低成本的 1D 反向恢复 benchmark。
- 寿命扫描结果展示了存储电荷与恢复指标之间的趋势性关系。
- 时间步长和网格收敛测试说明 benchmark 结果的数值稳定性边界。
- 该 benchmark 可作为商业 TCAD 研究的透明补充，而非替代。

不能说：

- DEVSIM 结果可精确预测真实商业快恢复二极管。
- 本研究解决了高压功率二极管优化问题。
- 本研究优于商业 TCAD。
- 在没有真实外部电路和实验校准的情况下精确预测 EMI、击穿或工业 `Q_rr`。
