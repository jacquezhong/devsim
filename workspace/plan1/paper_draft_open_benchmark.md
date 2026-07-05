# 基于开源 DEVSIM 的二极管反向恢复可复现仿真基准与寿命效应分析

> 初稿 v1，2026-07-04  
> 本文为新研究主线草稿，不沿用旧稿 `draft_modified.md` 的“高压功率二极管优化”叙事。正式投稿前需进一步核查参考文献格式、目标期刊模板与全部引用来源。

## 摘要

二极管反向恢复过程由正向导通阶段积累的载流子存储电荷和反向切换阶段的电荷抽取共同决定，是功率器件开关损耗、瞬态电磁干扰和电路可靠性分析中的重要问题。现有高水平研究多依赖商业 TCAD 工具，并通常能够给出器件结构、物理模型和实验对比，但完整输入 deck、网格、求解设置、原始瞬态波形与指标提取脚本往往难以完全公开，从而限制了计算流程层面的复现性。针对这一问题，本文建立了一个基于开源 DEVSIM 的一维硅 PIN 二极管反向恢复仿真基准，公开器件结构、网格参数、漂移-扩散物理模型、偏置协议、时间步长、压缩波形数据和 `Q_rr/I_rrm/t_rr` 指标提取过程。基准包含固定正向电压和固定正向电流两种初始化协议，并引入由节点载流子浓度积分得到的存储移动电荷作为物理一致性诊断。结果表明，在目标正向电流 `I_F=1e-3 A` 下，载流子寿命从 `1e-8 s` 增加到 `1e-5 s` 时，反向恢复电荷从 `3.495e-9 C` 增至 `4.297e-9 C`，存储移动电荷从 `3.478e-9 C` 增至 `6.687e-9 C`。目标电流协议下的时间步长扫描显示，`Q_rr` 对 `1e-9` 到 `5e-9 s` 的时间步长变化保持高度稳定，而峰值反向电流 `I_rrm` 显著依赖时间步长。该结果说明，积分电荷比峰值电流更适合作为理想电压阶跃瞬态基准的主参考指标。本文不试图替代商业 TCAD 的复杂器件预测能力，而是提供一个低成本、透明、可审计的开源参考实现，用于反向恢复仿真流程、指标定义和数值收敛性的可复现评价。

**关键词**：DEVSIM；开源 TCAD；反向恢复；PIN 二极管；漂移-扩散；可复现基准；存储电荷

## 1. 引言

二极管从正向导通切换到反向阻断时，器件内部存储的少数载流子不能瞬时消失，因而会形成一段短暂的反向电流。该过程通常称为反向恢复，常用指标包括最大反向恢复电流 `I_rrm`、反向恢复时间 `t_rr` 和反向恢复电荷 `Q_rr`。对于 PN 或 PIN 结构，正向导通期间的少数载流子注入和漂移区存储电荷会显著影响关断过程；对功率器件和高速开关电路而言，反向恢复直接关系到开关损耗、过冲、电磁干扰和热设计。

反向恢复已经被大量研究。成熟研究方向包括寿命控制、阳极注入效率调节、漂移区结构设计、混合模式 TCAD 与外部电路耦合、以及基于实测波形的紧凑模型提取。商业 TCAD 工具在此类问题上具有明显优势：它们提供更完整的材料模型、复杂结构建模能力、工艺流程支持、混合模式电路接口和工业级数值稳健性。因此，本文并不试图证明开源 DEVSIM 在工程预测能力上优于 Sentaurus、Silvaco 等商业 TCAD。

然而，从可复现计算研究的角度看，现有商业 TCAD 论文常存在一个结构性限制：论文通常报告器件结构、物理模型、关键参数扫描和代表性曲线，但完整 deck、网格文件、求解容差、时间积分设置、原始波形和指标提取脚本很少全部公开。这并不意味着相关研究不可信，而是说明其更偏向“物理趋势和工程结论可理解”，而非“计算流程可逐步复跑”。对于反向恢复这类对偏置历史、时间步长、电路边界和积分区间高度敏感的问题，仅公开最终 `Q_rr` 或 `t_rr` 往往不足以支持严格的 benchmark 比较。

开源基准的意义正在于此。一个简化的一维 PN/PIN 二极管不能代表真实商业快恢复器件，但可以公开完整的器件定义、物理方程、数值设置、原始数据和后处理方法，从而为后续算法比较、指标定义、教学复现和跨工具验证提供共同参考。DEVSIM 是开源 TCAD 设备模拟器，支持 Python 脚本、DC、小信号 AC、瞬态、自定义 PDE、扩展浮点精度以及 1D/2D/3D 仿真，许可证为 Apache-2.0。其透明和可脚本化特征使其适合作为低成本反向恢复基准的实现平台。

本文的主要贡献如下：

1. 建立一个基于 DEVSIM 的一维硅 PIN 二极管反向恢复开源 benchmark，公开结构、网格、偏置流程、数据格式和指标提取脚本。
2. 比较固定正向电压和固定正向电流两种初始化协议，说明固定电流协议更适合寿命效应比较。
3. 引入存储移动电荷积分作为物理一致性诊断，并将其与终端反向恢复电荷进行对照。
4. 给出时间步长和网格密度收敛结果，展示 `Q_rr` 与 `I_rrm` 在理想电压阶跃下的不同数值敏感性。
5. 提供压缩 `npz` 原始波形和 JSON 指标文件，降低数据存储成本并提高复现实验的可审计性。

## 2. 仿真模型与基准定义

### 2.1 开源仿真平台

本文使用 DEVSIM `2.7.1` 进行器件仿真。本地运行环境为 `/opt/miniconda3/bin/python3`，DEVSIM 安装于 conda base 环境。DEVSIM 通过 Python 接口创建网格、定义节点模型和边模型、设置接触边界条件，并调用 DC 与 transient BDF1 求解器完成漂移-扩散仿真。

本文使用的代码位于：

- `workspace/plan1/benchmark/config.json`
- `workspace/plan1/benchmark/benchmark_common.py`
- `workspace/plan1/benchmark/run_dc_benchmark.py`
- `workspace/plan1/benchmark/run_reverse_recovery_benchmark.py`
- `workspace/plan1/benchmark/extract_metrics.py`
- `workspace/plan1/benchmark/generate_benchmark_figures.py`

原始波形以压缩 `npz` 文件保存于 `workspace/plan1/data/benchmark/waveforms`，指标与元数据以 JSON 文件保存于 `workspace/plan1/data/benchmark/raw` 和 `workspace/plan1/data/benchmark/metrics`。

### 2.2 器件结构

基准器件为一维硅 PIN 二极管。几何和掺杂参数如表 1 所示。该结构并不模拟特定商业器件，而是作为公开、低成本、可稳定复跑的标准问题。

表 1  一维 PIN 二极管基准参数

| 参数 | 数值 | 说明 |
|---|---:|---|
| 器件总长度 | `3e-4 cm` | 3 微米 |
| P 区宽度 | `5e-5 cm` | 左端接触区 |
| N 区宽度 | `5e-5 cm` | 右端接触区 |
| P 区受主浓度 | `1e17 cm^-3` | 阶跃掺杂 |
| N 区施主浓度 | `1e17 cm^-3` | 阶跃掺杂 |
| I 区背景施主浓度 | `1e12 cm^-3` | 轻掺杂漂移区 |
| 温度 | `300 K` | 基准温度 |
| 默认网格密度 | `2e-7 cm` | PIN 过渡位置附近 |
| 默认寿命 | `1e-6 s` | `tau_n=tau_p` |

P 区、I 区和 N 区通过 DEVSIM 节点模型定义。基准采用阶跃掺杂分布：

$$
N_A(x)=N_P H(x_P-x),
$$

$$
N_D(x)=N_N H(x-x_N)+N_I H(x-x_P)H(x_N-x),
$$

其中 `H` 为阶跃函数，`x_P` 与 `x_N` 分别为 P/I 和 I/N 过渡位置。

### 2.3 物理模型与求解流程

本文采用 DEVSIM `simple_physics` 中的硅漂移-扩散模型。该模型包括 Poisson 方程、电子连续性方程、空穴连续性方程、Scharfetter-Gummel 型载流子电流离散以及 SRH 复合模型。载流子寿命通过区域参数 `taun` 和 `taup` 设置，本文取 `tau_n=tau_p=tau`。

求解流程分为三步：

1. **平衡初始化**：在 0 V 下求解 Poisson 方程，随后加入电子和空穴连续性方程求解漂移-扩散平衡态。
2. **正向预偏置**：设置正向初始条件。本文比较固定正向电压和固定目标正向电流两种协议。
3. **反向阶跃瞬态**：将顶部接触电压切换至 `-1.0 V`，使用 BDF1 时间积分记录接触电流波形。

默认瞬态参数如表 2 所示。

表 2  反向恢复瞬态参数

| 参数 | 数值 |
|---|---:|
| 固定正向电压 | `0.8 V` |
| 目标正向电流 | `1e-3 A` |
| 反向阶跃电压 | `-1.0 V` |
| 默认时间步长 | `2e-9 s` |
| 反向仿真时间 | `1e-7 s` |
| 正向预偏置 transient 步数 | 10 |
| 恢复阈值 | `0.1 I_rrm` |

需要说明的是，本文中的接触电流为 DEVSIM 一维接触电流接口给出的基准电流。由于基准没有引入真实器件横截面积，该电流不应直接解释为某个实际封装器件的额定电流，而应作为同一开放基准中的一致比较量。

### 2.4 固定电压与固定电流初始化

固定正向电压协议直接令顶部接触为 `0.8 V`。该协议计算简单，适合形成数值压力测试，但不同寿命下正向注入状态可能并不完全可比。

固定正向电流协议先通过 DC I-V 粗扫找到目标电流附近的电压区间，再用二分法求得使接触电流接近 `I_F=1e-3 A` 的正向电压。该协议更接近反向恢复测试中“给定正向电流后关断”的物理语境，因此本文将其作为寿命效应分析的主协议。

### 2.5 指标定义

本文采用“正向电流为正、反向恢复电流为负”的符号约定。反向阶跃后的终端电流记为 `I(t)`。

最大反向恢复电流定义为：

$$
I_{rrm}=\max_{t \ge 0}[-I(t),0].
$$

恢复结束时间 `t_end` 定义为从反向峰值之后首次满足：

$$
I(t) \ge -0.1 I_{rrm}
$$

的时间点。反向恢复时间为：

$$
t_{rr}=t_{end}-t_0.
$$

反向恢复电荷定义为反向电流幅值积分：

$$
Q_{rr}=\int_{t_0}^{t_{end}}\max[-I(t),0]dt.
$$

为检查终端 `Q_rr` 是否与器件内部载流子存储状态同量级，本文计算正向切换前相对 0 V 平衡态的存储移动电荷：

$$
Q_{stored}=q\sum_i \left[\max(n_i-n_{i0},0)+\max(p_i-p_{i0},0)\right]V_i,
$$

其中 `n_i`、`p_i` 分别为正向预偏置后的电子和空穴浓度，`n_i0`、`p_i0` 为 0 V 平衡态浓度，`V_i` 为节点体积。该量是存储载流子诊断指标，并不等同于严格的端口电荷守恒项。

## 3. 数据与图表

本文使用的主要图表如下：

- 图 1：`fig_pub_dc_iv.png`，DC I-V 曲线与目标电流工作点。
- 图 2：`fig_pub_lifetime_summary.png`，寿命扫描下 `Q_rr` 与存储移动电荷。
- 图 3：`fig_pub_recovery_waveforms.png`，固定电压与固定电流协议下的反向恢复波形。
- 图 4：`fig_pub_time_step_convergence.png`，固定电流协议下时间步长收敛。
- 图 5：`fig_pub_mesh_convergence.png`，固定电压协议下网格密度收敛。

PNG 和 PDF 图均位于 `workspace/plan1/figures/benchmark`。

## 4. 结果与讨论

### 4.1 DC I-V 与目标电流工作点

图 1 展示了 `tau=1e-6 s` 时基准 PIN 二极管的 DC I-V 曲线。目标正向电流设为 `1e-3 A`，由 DC 插值得到对应正向电压约为 `0.415 V`。在后续固定电流瞬态中，脚本进一步通过局部二分求解得到更精确的预偏置电压。例如在 `tau=1e-6 s` 时，目标电流协议得到 `V_F=0.4257 V`，实际正向电流为 `1.000e-3 A`。

这一过程说明，固定目标电流协议并非人为指定同一电压，而是根据每个寿命点的 DC 状态自动确定正向工作点。对于寿命扫描，这比固定 `0.8 V` 更适合比较内部存储电荷和反向恢复指标。

### 4.2 寿命扫描：固定电压协议

固定电压协议下，正向预偏置电压固定为 `0.8 V`。寿命从 `1e-8 s` 到 `1e-5 s` 时，`Q_rr` 从 `4.200e-7 C` 增加到 `4.618e-7 C`，`I_rrm` 从 `4.120e2 A` 增加到 `4.528e2 A`，存储移动电荷从 `1.705e-6 C` 增加到 `1.874e-6 C`。这些指标随寿命增加而上升，但变化幅度较小。

固定电压结果可以作为数值压力测试，因为 `0.8 V` 下正向注入很强，反向阶跃后出现较大的峰值电流。然而，该协议下不同寿命点的正向注入状态由同一电压控制，不能保证具有相同导通电流条件。因此，本文不将固定电压结果作为寿命效应的主要物理结论，而将其作为基准的补充场景和网格收敛测试条件。

### 4.3 寿命扫描：固定目标电流协议

固定目标电流协议下，各寿命点均从约 `1e-3 A` 的正向电流出发。结果如表 3 所示。

表 3  固定目标电流协议下的寿命扫描结果

| 寿命 tau (s) | `V_F` (V) | `I_F` (A) | `Q_rr` (C) | `I_rrm` (A) | `Q_stored` (C) |
|---:|---:|---:|---:|---:|---:|
| `1e-8` | 0.2851 | `1.001e-3` | `3.495e-9` | 3.493 | `3.478e-9` |
| `1e-7` | 0.3761 | `1.001e-3` | `3.872e-9` | 3.869 | `4.989e-9` |
| `1e-6` | 0.4257 | `1.000e-3` | `4.211e-9` | 4.206 | `6.345e-9` |
| `1e-5` | 0.4344 | `9.997e-4` | `4.297e-9` | 4.291 | `6.687e-9` |

可以看到，随着寿命增加，`Q_rr` 从 `3.495e-9 C` 增至 `4.297e-9 C`，增幅约为 23%；存储移动电荷从 `3.478e-9 C` 增至 `6.687e-9 C`，增幅约为 92%。两者变化方向一致，并保持同一数量级。这支持了本文的物理解释：在固定正向电流条件下，寿命增加会提高正向预偏置后的移动载流子存储量，反向阶跃时需要抽取的终端电荷也随之增加。

需要注意的是，`Q_stored` 大于 `Q_rr`，且二者并非严格相等。这是合理的：`Q_stored` 是相对平衡态的内部移动载流子积分诊断，而 `Q_rr` 是由指定终端电流、积分阈值和理想反向阶跃共同决定的端口指标。本文关注的是二者是否同量级且趋势一致，而不是把二者作为同一物理量。

### 4.4 反向恢复波形

图 3 展示了两种初始化协议下的反向电流幅值波形。固定电压协议产生较大的反向峰值电流，且不同寿命点的波形高度接近；固定电流协议下峰值电流约为数安培量级，寿命增加导致波形尾部和积分电荷略有增加。

该结果进一步说明，反向恢复 benchmark 必须明确初始条件。如果只报告 `Q_rr` 而不说明正向预偏置协议，不同研究之间的数值比较可能缺乏意义。本文因此在所有 JSON 元数据中记录 `initial_condition`、`v_forward_V`、`forward_current_A`、`v_reverse_V`、`time_step_s` 和 `mesh_density_cm`。

### 4.5 时间步长收敛

表 4 给出了固定目标电流协议下 `tau=1e-6 s` 的时间步长扫描结果。

表 4  固定目标电流协议下的时间步长扫描

| 时间步长 dt (s) | `Q_rr` (C) | `I_rrm` (A) | `t_rr` (s) | `Q_stored` (C) |
|---:|---:|---:|---:|---:|
| `5e-9` | `4.211294e-9` | 1.684 | `5e-9` | `6.345e-9` |
| `2e-9` | `4.211263e-9` | 4.206 | `2e-9` | `6.345e-9` |
| `1e-9` | `4.211155e-9` | 8.401 | `1e-9` | `6.345e-9` |

`Q_rr` 在三个时间步长下几乎不变，最大相对变化低于 0.004%。相比之下，`I_rrm` 从 `1.684 A` 增至 `8.401 A`，表现出强烈时间步长依赖。这说明，在理想电压阶跃和极窄恢复脉冲条件下，峰值电流主要由第一个或前几个时间步捕捉，容易受到离散时间分辨率影响；而积分电荷对步长更稳健，更适合作为 reference metric。

`t_rr` 在本基准中也呈现明显时间步长量化特征。因此，本文仅将 `t_rr` 作为辅助输出，不将其作为主要结论指标。

### 4.6 网格密度收敛

固定电压协议下，`tau=1e-6 s`、`dt=2e-9 s` 时的网格扫描结果显示，网格密度从 `5e-7 cm` 到 `1e-7 cm` 变化时，`Q_rr` 相对变化约为 0.03%，`I_rrm` 相对变化约为 0.04%。运行时间随网格加密从约 `1.28 s` 增加到 `4.48 s`。

该结果说明，在当前一维 PIN 几何和阶跃掺杂设置下，默认网格 `2e-7 cm` 已足以稳定提取 `Q_rr` 和 `I_rrm`。这也说明本 benchmark 的计算代价较低，适合用于可复现实验和算法调试。

## 5. 作为开源基准的意义

本文结果的核心价值不在于给出某种商业二极管的真实性能预测，而在于把反向恢复仿真中容易被忽略的流程细节显式化：

1. **偏置历史显式化**：区分固定正向电压和固定正向电流协议。
2. **指标定义显式化**：公开 `I_rrm`、`t_rr` 和 `Q_rr` 的计算规则。
3. **原始波形开放**：保存 `npz` 波形文件，而不是只给最终表格。
4. **后处理脚本开放**：指标由 `extract_metrics.py` 自动提取，避免手工读图。
5. **数值收敛可检查**：提供时间步长和网格密度扫描。
6. **物理一致性诊断**：用存储移动电荷检查终端 `Q_rr` 是否与内部载流子状态同量级。

这些要素共同构成了 benchmark 的基本属性。即使未来更换工具、改变器件长度、加入外部电路或扩展到二维结构，也可以沿用相同的数据格式和评价指标。

## 6. 局限性

本文基准具有明确局限，必须在正式论文中保留。

首先，本文使用一维硅 PIN 二极管，不包含真实功率器件的终端结构、场板、边缘效应、封装寄生参数和工艺非均匀性。因此，结果不能直接外推到商业快恢复二极管或 SiC 器件。

其次，本文采用简化漂移-扩散与 SRH 复合模型，未引入复杂寿命分布、陷阱能级、Auger 复合、场依赖迁移率、热效应或实验校准参数。因此，寿命扫描反映的是基准模型内的趋势，而不是某种具体寿命控制工艺的定量预测。

第三，本文使用理想电压阶跃作为反向切换边界。该设置有利于构造简单、可复现的瞬态 benchmark，但会使峰值电流对时间步长高度敏感。若研究实际开关损耗，应进一步加入串联电阻、电感或混合模式外部电路。

第四，本文中的接触电流采用 DEVSIM 一维器件约定，没有定义真实横截面积。后续若需要与实验或数据手册比较，应引入面积归一化或明确电流密度定义。

最后，本文的参考文献和相关工作仍需在正式投稿前进一步扩展和核查，尤其应补充经典半导体器件教材、反向恢复模型论文和商业 TCAD 研究论文。

## 7. 结论

本文建立了一个基于开源 DEVSIM 的一维硅 PIN 二极管反向恢复仿真基准，公开了器件结构、网格、偏置协议、瞬态波形、指标提取和数值收敛结果。通过固定电压和固定电流两种初始化协议的比较，本文指出固定目标正向电流更适合寿命效应分析。在 `I_F=1e-3 A` 的固定电流条件下，寿命从 `1e-8 s` 增至 `1e-5 s` 时，`Q_rr` 从 `3.495e-9 C` 增至 `4.297e-9 C`，存储移动电荷从 `3.478e-9 C` 增至 `6.687e-9 C`，二者趋势一致且同量级。时间步长扫描显示，`Q_rr` 对 `1e-9` 到 `5e-9 s` 的步长变化高度稳定，而 `I_rrm` 显著依赖时间步长，说明积分电荷更适合作为理想阶跃反向恢复 benchmark 的主参考指标。

本文的贡献是提供一个透明、低成本、可复跑的开源参考实现，而不是替代商业 TCAD 对真实器件的工程预测。后续工作可在该基准上加入外部电路、面积归一化、温度扫描、二维结构和跨工具对比，从而进一步提高反向恢复仿真研究的开放性和可复现性。

## 参考文献（初稿，正式投稿前需按目标期刊格式逐条核查）

[1] DEVSIM LLC. DEVSIM TCAD Device Simulator, GitHub repository. https://github.com/devsim/devsim

[2] DEVSIM LLC. DEVSIM TCAD Semiconductor Device Simulator official website. https://devsim.org/

[3] Calado P, Gelmetti I, Hilton B, Azzouzi M, Nelson J, Barnes P R F. Driftfusion: an open source code for simulating ordered semiconductor devices with mixed ionic-electronic conducting materials in one dimension. arXiv:2009.04384, 2020.

[4] Nayak D, Kumar Y R, Kumar M, Pramanick S. Temperature Dependent Reverse Recovery Characterization of SiC MOSFETs Body Diode for Switching Loss Estimation in a Half-Bridge. arXiv:2104.09271, 2021.

[5] Gaggl P, et al. TCAD modeling of radiation-induced defects in 4H-SiC diodes. arXiv:2407.11776, 2024.

[6] Burin J, et al. TCAD Simulations of Radiation Damage in 4H-SiC. arXiv:2407.16710, 2024.

[7] Tunga A, et al. A comparison of a commercial hydrodynamics TCAD solver and Fermi kinetics transport convergence for GaN HEMTs. arXiv:2208.03576, 2022.

[8] Sze S M, Ng K K. Physics of Semiconductor Devices. 3rd ed. Wiley, 2006.（经典教材，正式稿需按目标格式核查出版信息）

## 附录 A：数据与复现命令

核心命令如下：

```bash
PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_dc_benchmark.py --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep lifetime

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep lifetime-target-current

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep time-target-current --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep mesh --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/generate_benchmark_figures.py
```

核心输出文件：

- `workspace/plan1/data/benchmark/metrics/metrics_lifetime_sweep.json`
- `workspace/plan1/data/benchmark/metrics/metrics_lifetime_sweep_target_current.json`
- `workspace/plan1/data/benchmark/metrics/metrics_time_step_sweep_target_current.json`
- `workspace/plan1/data/benchmark/metrics/metrics_mesh_sweep.json`
- `workspace/plan1/data/benchmark/waveforms/*.npz`
- `workspace/plan1/figures/benchmark/fig_pub_*.png`
- `workspace/plan1/figures/benchmark/fig_pub_*.pdf`

