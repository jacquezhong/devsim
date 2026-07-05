# 基于开源 DEVSIM 的硅 PIN 二极管反向恢复可复现仿真基准研究

## 摘要

反向恢复是影响二极管及功率变换电路开关损耗、瞬态过冲和电磁干扰的重要过程，其数值结果对器件结构、载流子寿命、偏置历史、时间步长和后处理指标定义均较敏感。现有相关研究多依赖商业 TCAD 平台，能够支撑复杂器件建模和工程校准，但完整输入文件、网格、求解设置、原始瞬态波形及指标提取脚本通常难以同时公开，因而不利于形成可复跑、可审计的基准数据。针对这一问题，本文基于开源器件仿真框架 DEVSIM 建立了一维硅 PIN 二极管反向恢复仿真基准，给出器件结构、漂移-扩散模型、SRH 复合寿命参数、参考面积归一化、正向预偏置协议、反向阶跃瞬态设置及 `$Q_{rr}$`、`$I_{rrm}$`、`$t_{rr}$` 指标提取方法。基准同时比较固定正向电压和固定正向电流两类初始化方式，并引入正向预偏置后的存储移动电荷作为物理一致性诊断。结果表明，在参考面积 `$A=1.0$ cm^2`、目标正向电流密度 `$J_F=1.0\times10^{-3}$ A/cm^2` 下，载流子寿命由 `$1.0\times10^{-8}$ s` 增至 `$1.0\times10^{-5}$ s` 时，反向恢复面电荷 `$Q_{rr}/A$` 由 `$3.495\times10^{-9}$ C/cm^2` 增至 `$4.297\times10^{-9}$ C/cm^2`，存储移动面电荷由 `$3.478\times10^{-9}$ C/cm^2` 增至 `$6.687\times10^{-9}$ C/cm^2`，二者趋势一致且处于同一数量级。进一步的正向电流密度扫描显示，当 `$J_F$` 从 `$1.0\times10^{-4}$ A/cm^2` 增至 `$1.0\times10^{-2}$ A/cm^2` 时，`$Q_{rr}/A$` 从 `$3.772\times10^{-9}$ C/cm^2` 增至 `$5.365\times10^{-9}$ C/cm^2`。时间步长扫描表明，`$Q_{rr}/A$` 对 `$1.0\times10^{-9}$ s` 至 `$5.0\times10^{-9}$ s` 的时间步长变化保持稳定，而 `$I_{rrm}/A$` 对理想电压阶跃下的瞬态离散分辨率高度敏感。本文结果说明，开放仿真代码、原始波形和指标提取流程有助于明确反向恢复仿真的可复现边界；在本文基准条件下，积分电荷较峰值电流更适合作为主要参考指标。

**关键词**：DEVSIM；开源 TCAD；反向恢复；PIN 二极管；漂移-扩散；可复现基准

## Abstract

Reverse recovery is a key transient process affecting switching loss, voltage overshoot, and electromagnetic interference in diode and power-conversion circuits. Its numerical prediction is sensitive to device structure, carrier lifetime, bias history, time-step resolution, and post-processing definitions. Most high-fidelity studies rely on commercial TCAD tools, which provide advanced physical models and industrial calibration capability, but the complete input decks, meshes, solver settings, raw transient waveforms, and metric-extraction scripts are seldom released together. This work develops a reproducible reverse-recovery benchmark for a one-dimensional silicon PIN diode using the open-source DEVSIM device simulator. The benchmark specifies the device geometry, drift-diffusion model, SRH lifetime parameters, reference-area normalization, forward-bias initialization protocols, reverse-step transient setup, and the extraction rules for `$Q_{rr}$`, `$I_{rrm}$`, and `$t_{rr}$`. Fixed-voltage and fixed-current initialization protocols are compared, and the stored mobile charge before reverse switching is used as a physical consistency diagnostic. With a reference area of `$A=1.0$ cm^2` and a target forward current density of `$J_F=1.0\times10^{-3}$ A/cm^2`, increasing the carrier lifetime from `$1.0\times10^{-8}$ s` to `$1.0\times10^{-5}$ s` raises `$Q_{rr}/A$` from `$3.495\times10^{-9}$ C/cm^2` to `$4.297\times10^{-9}$ C/cm^2`, while the stored mobile charge density increases from `$3.478\times10^{-9}$ C/cm^2` to `$6.687\times10^{-9}$ C/cm^2`. A forward-current-density sweep further shows that `$Q_{rr}/A$` increases from `$3.772\times10^{-9}$ C/cm^2` to `$5.365\times10^{-9}$ C/cm^2` as `$J_F$` increases from `$1.0\times10^{-4}$ A/cm^2` to `$1.0\times10^{-2}$ A/cm^2`. Time-step studies show that `$Q_{rr}/A$` is stable for time steps from `$1.0\times10^{-9}$ s` to `$5.0\times10^{-9}$ s`, whereas `$I_{rrm}/A$` is strongly affected by the temporal resolution of the ideal voltage step. These results demonstrate that open code, raw waveforms, and transparent metric extraction are useful for clarifying the reproducibility boundary of reverse-recovery simulation, and that the integrated recovery charge is a more robust reference metric than the peak current under the present benchmark conditions.

**Key words**: DEVSIM; open-source TCAD; reverse recovery; PIN diode; drift-diffusion; reproducible benchmark

## 1 引言

二极管由正向导通切换至反向阻断时，结区和漂移区内的非平衡载流子需要经过抽取与复合过程才能恢复阻断能力。这一反向恢复过程通常表现为短时反向电流脉冲，并通过最大反向恢复电流 `$I_{rrm}$`、反向恢复时间 `$t_{rr}$` 和反向恢复电荷 `$Q_{rr}$` 等指标表征。对于功率二极管、MOSFET 体二极管和含二极管续流通道的功率变换器，反向恢复会影响开关损耗、器件热应力、电压过冲和电磁兼容设计。因此，建立清晰、可比较的反向恢复仿真流程具有实际意义。

从物理机制看，反向恢复与正向导通阶段的少数载流子注入、漂移区电荷存储、载流子寿命和反向边界条件密切相关。经典半导体器件理论和 TCAD 方法已经为该问题提供了成熟基础，包括漂移-扩散方程、Poisson 方程、Scharfetter-Gummel 离散格式和 Shockley-Read-Hall 复合模型等[1-5]。在工程研究中，商业 TCAD 平台能够处理二维或三维结构、复杂掺杂、温度效应、陷阱模型以及外部电路耦合，是研究真实功率器件反向恢复和缺陷寿命效应的重要工具[11-12]。

然而，反向恢复仿真具有较强的流程敏感性。同一器件结构在固定正向电压和固定正向电流两种预偏置条件下，初始存储电荷可能明显不同；同一反向阶跃过程在不同时间步长下，峰值电流也可能发生较大变化。若论文仅给出最终恢复电荷或恢复时间，而缺少完整的输入 deck、网格、求解容差、原始波形和指标提取代码，则其他研究者难以判断差异来自物理模型、数值离散还是后处理定义。商业 TCAD 研究并非缺乏可信度，但其复现通常受软件授权、模型库封闭性和输入文件公开程度限制。对于需要作为教学、算法验证或跨工具对比基础的标准问题，开放性和透明度本身就是重要研究价值。

DEVSIM 是一个开源 TCAD 器件仿真框架，采用有限体积方法，支持 Python 脚本、直流、小信号、瞬态、自定义偏微分方程以及一维、二维和三维仿真[6-7]。与商业 TCAD 相比，DEVSIM 的模型库、工艺集成和工业校准能力有限；但其源代码和脚本接口开放，适合构建小规模、低成本、可复跑的物理仿真基准。开源漂移-扩散工具在光电器件等领域已经被用于提高模型透明度和复用性[10]；更一般地，开源计算研究中，数据、代码和计算环境的公开被认为是结果可复核的重要条件[8-9]。本文并不试图证明开源框架优于商业 TCAD，也不以预测某一真实商业器件为目标，而是尝试回答一个更窄的问题：能否用完全开放的代码、参数和数据，建立一个反向恢复仿真流程基准，使研究者能够复查每一步数值结果和指标定义。

本文主要贡献如下：第一，建立基于 DEVSIM 的一维硅 PIN 二极管反向恢复开源基准，公开器件结构、网格设置、偏置历史和数据格式；第二，引入参考面积归一化，使用电流密度和面电荷密度报告主要指标，避免一维接触电流被误读为特定器件额定电流；第三，比较固定正向电压与固定目标正向电流两种初始化协议，并增加目标正向电流密度扫描，展示 benchmark 对初始导通条件的覆盖能力；第四，将终端恢复电荷 `$Q_{rr}$` 与内部存储移动电荷进行对照，检查反向恢复指标的物理一致性；第五，给出时间步长和网格密度收敛结果，讨论 `$Q_{rr}$` 与 `$I_{rrm}$` 的数值敏感性差异。

## 2 基准模型与仿真方法

### 2.1 器件结构

本文采用一维硅 PIN 二极管作为基准器件。该结构不对应特定商品器件，而用于构造可公开、低成本且稳定收敛的标准问题。器件总长度为 `$3.0\times10^{-4}$ cm`，左侧 P 区和右侧 N 区宽度均为 `$5.0\times10^{-5}$ cm`，中间为低掺杂 I 区。P 区受主浓度和 N 区施主浓度均取 `$1.0\times10^{17}$ cm^{-3}`，I 区背景施主浓度取 `$1.0\times10^{12}$ cm^{-3}`，温度取 300 K。默认过渡区域网格密度为 `$2.0\times10^{-7}$ cm`。器件参数如表1所示。

表1  一维硅 PIN 二极管基准参数

| 参数 | 数值 | 说明 |
|---|---:|---|
| 器件总长度 | `$3.0\times10^{-4}$ cm` | 一维仿真区域 |
| P 区宽度 | `$5.0\times10^{-5}$ cm` | 左端重掺杂区 |
| I 区宽度 | `$2.0\times10^{-4}$ cm` | 轻掺杂漂移区 |
| N 区宽度 | `$5.0\times10^{-5}$ cm` | 右端重掺杂区 |
| P 区受主浓度 | `$1.0\times10^{17}$ cm^{-3}` | 阶跃掺杂 |
| N 区施主浓度 | `$1.0\times10^{17}$ cm^{-3}` | 阶跃掺杂 |
| I 区背景施主浓度 | `$1.0\times10^{12}$ cm^{-3}` | 轻掺杂 |
| 温度 | 300 K | 等温条件 |
| 默认网格密度 | `$2.0\times10^{-7}$ cm` | 过渡区附近 |
| 参考面积 | `$1.0$ cm^2` | 用于电流密度和面电荷密度归一化 |

掺杂分布采用阶跃函数定义。设 P/I 和 I/N 过渡位置分别为 `$x_P$` 和 `$x_N$`，则受主和施主浓度可表示为

$$
N_A(x)=N_P H(x_P-x),
$$

$$
N_D(x)=N_N H(x-x_N)+N_I H(x-x_P)H(x_N-x),
$$

其中 `$H(\cdot)$` 为阶跃函数，`$N_P$`、`$N_N$` 和 `$N_I$` 分别为 P 区、N 区和 I 区掺杂浓度。

### 2.2 物理方程与数值求解

仿真采用硅漂移-扩散模型，包括 Poisson 方程、电子连续性方程和空穴连续性方程。电势、电子浓度和空穴浓度分别记为 `$\psi$`、`$n$` 和 `$p$`。Poisson 方程可写为

$$
\nabla\cdot(\varepsilon\nabla\psi)=-q(p-n+N_D-N_A),
$$

电子和空穴连续性方程为

$$
\frac{\partial n}{\partial t}=\frac{1}{q}\nabla\cdot J_n+G-R,
$$

$$
\frac{\partial p}{\partial t}=-\frac{1}{q}\nabla\cdot J_p+G-R.
$$

其中 `$J_n$` 和 `$J_p$` 分别为电子和空穴电流密度，`$R$` 为复合率。本文采用 SRH 复合模型，且令电子寿命和空穴寿命相等，即 `$\tau_n=\tau_p=\tau$`。寿命扫描范围为 `$1.0\times10^{-8}$ s` 至 `$1.0\times10^{-5}$ s`。

DEVSIM 使用有限体积方法构建离散方程，并通过 Python 接口完成网格、区域模型和接触边界的定义。求解流程包括 0 V 平衡初始化、正向预偏置和反向阶跃瞬态。瞬态阶段采用 BDF1 时间积分。默认反向阶跃电压为 -1.0 V，默认时间步长为 `$2.0\times10^{-9}$ s`，反向恢复仿真总时间为 `$1.0\times10^{-7}$ s`。

### 2.3 偏置协议

本文比较两种正向初始化协议。

第一种为固定正向电压协议。正向预偏置电压固定为 0.8 V，随后将顶部接触电压阶跃至 -1.0 V，并记录终端电流波形。该协议容易实现，能够形成较强的载流子注入和明显的恢复电流脉冲，适合作为数值压力测试。

第二种为固定正向电流协议。脚本先通过 DC I-V 扫描确定目标电流附近的电压区间，再用二分搜索求得使正向电流接近 `$I_F=1.0\times10^{-3}$ A` 的预偏置电压。本文设置参考面积 `$A=1.0$ cm^2`，因此该目标值等价于目标正向电流密度 `$J_F=1.0\times10^{-3}$ A/cm^2`。随后从该正向电流状态切换至 -1.0 V。由于反向恢复测试通常以给定正向电流作为初始条件，固定电流协议更适合比较不同寿命下的恢复特性。

需要说明的是，本文的一维模型并不对应真实封装器件横截面积。为避免将 DEVSIM 一维接触电流误解为实际器件额定电流，本文显式设定参考面积 `$A=1.0$ cm^2`，并将主要电流和电荷结果报告为 `$J=I/A$`、`$Q/A$` 与 `$Q_{stored}/A$`。参考面积只用于统一量纲和便于比较，不代表某个特定商业器件的芯片面积。

### 2.4 指标提取方法

本文采用正向电流为正、反向恢复电流为负的符号约定。反向阶跃后的终端电流记为 `$I(t)$`。最大反向恢复电流定义为

$$
I_{rrm}=\max_{t\geq0}\{-I(t),0\}.
$$

以峰值反向电流后的首次恢复至 `$0.1I_{rrm}$` 为恢复结束条件，即当

$$
I(t)\geq-0.1I_{rrm}
$$

首次满足时记为 `$t_{end}$`。反向恢复时间定义为

$$
t_{rr}=t_{end}-t_0.
$$

反向恢复电荷定义为恢复区间内反向电流幅值积分：

$$
Q_{rr}=\int_{t_0}^{t_{end}}\max\{-I(t),0\}dt.
$$

为检查终端恢复电荷与器件内部存储状态是否具有一致趋势，本文定义正向预偏置后相对 0 V 平衡态的存储移动电荷

$$
Q_{stored}=q\sum_i [\max(n_i-n_{i0},0)+\max(p_i-p_{i0},0)]V_i,
$$

其中 `$n_i$` 和 `$p_i$` 为正向预偏置后的节点载流子浓度，`$n_{i0}$` 和 `$p_{i0}$` 为平衡态浓度，`$V_i$` 为节点控制体积。`$Q_{stored}$` 是内部载流子存储诊断量，并不要求与端口积分电荷 `$Q_{rr}$` 严格相等。

## 3 结果与讨论

### 3.1 DC 特性与目标正向电流

图1给出了寿命 `$\tau=1.0\times10^{-6}$ s` 时基准 PIN 二极管的 DC I-V 曲线。以 `$J_F=1.0\times10^{-3}$ A/cm^2` 为目标正向电流密度，DC 插值得到的正向电压约为 0.415 V；在瞬态脚本中进一步通过二分搜索得到的预偏置电压为 0.4257 V，对应实际正向电流密度约为 `$1.000\times10^{-3}$ A/cm^2`。该步骤保证不同寿命点可从相同正向电流密度条件出发，有利于比较载流子寿命对存储电荷和反向恢复电荷的影响。

### 3.2 载流子寿命对反向恢复指标的影响

固定正向电压协议下，预偏置电压为 0.8 V。寿命从 `$1.0\times10^{-8}$ s` 增加到 `$1.0\times10^{-5}$ s` 时，`$Q_{rr}/A$` 从 `$4.200\times10^{-7}$ C/cm^2` 增至 `$4.618\times10^{-7}$ C/cm^2`，`$I_{rrm}/A$` 从 `$4.120\times10^{2}$ A/cm^2` 增至 `$4.528\times10^{2}$ A/cm^2`。该协议下恢复电流密度较大，适合检查数值求解稳定性；但由于各寿命点使用同一正向电压，不同寿命对应的注入状态并不一定具有相同正向电流背景。

固定目标电流协议下，各寿命点均由约 `$1.0\times10^{-3}$ A/cm^2` 的正向电流密度切换至反向偏置。表2列出了寿命扫描结果。

表2  固定目标电流协议下的寿命扫描结果

| 寿命 `$\tau$` / s | `$V_F$` / V | `$J_F$` / `$A\,cm^{-2}$` | `$Q_{rr}/A$` / `$C\,cm^{-2}$` | `$I_{rrm}/A$` / `$A\,cm^{-2}$` | `$Q_{stored}/A$` / `$C\,cm^{-2}$` |
|---:|---:|---:|---:|---:|---:|
| `$1.0\times10^{-8}$` | 0.2851 | `$1.001\times10^{-3}$` | `$3.495\times10^{-9}$` | 3.493 | `$3.478\times10^{-9}$` |
| `$1.0\times10^{-7}$` | 0.3761 | `$1.001\times10^{-3}$` | `$3.872\times10^{-9}$` | 3.869 | `$4.989\times10^{-9}$` |
| `$1.0\times10^{-6}$` | 0.4257 | `$1.000\times10^{-3}$` | `$4.211\times10^{-9}$` | 4.206 | `$6.345\times10^{-9}$` |
| `$1.0\times10^{-5}$` | 0.4344 | `$9.997\times10^{-4}$` | `$4.297\times10^{-9}$` | 4.291 | `$6.687\times10^{-9}$` |

由表2可见，在固定正向电流密度条件下，寿命增加使恢复面电荷和存储移动面电荷均呈上升趋势。`$Q_{rr}/A$` 的增幅约为 23%，而 `$Q_{stored}/A$` 的增幅约为 92%。二者并不严格相等，这是因为前者是由终端电流、积分阈值和反向边界共同决定的端口量，后者是相对平衡态的内部载流子积分量。但二者同向变化且量级相近，说明本文提取的反向恢复电荷与器件内部存储载流子状态具有合理对应关系。图2进一步比较了两种初始化协议下 `$Q_{rr}/A$` 和 `$Q_{stored}/A$` 随寿命变化的趋势。

### 3.3 两类初始化协议的波形差异

图3比较了固定正向电压和固定目标电流协议下的反向恢复波形。固定电压协议由于 0.8 V 正向偏置导致较强注入，反向峰值电流明显高于固定电流协议。固定目标电流协议下，不同寿命的波形峰值和积分面积随寿命增加而缓慢增大，更能反映给定正向导通条件下的寿命效应。

这一结果表明，反向恢复 benchmark 必须明确偏置历史。若只报告 `$Q_{rr}$`、`$I_{rrm}$` 或 `$t_{rr}$`，而不说明正向预偏置采用固定电压还是固定电流，不同研究之间的数值比较可能缺乏物理一致性。本文因此在每个原始数据文件中保存初始化协议、正向电压、正向电流、反向阶跃电压、时间步长和网格密度等元数据。

### 3.4 目标正向电流密度扫描

为进一步增强基准的覆盖面，本文在 `$\tau=1.0\times10^{-6}$ s`、`$\Delta t=2.0\times10^{-9}$ s` 和反向阶跃电压 -1.0 V 条件下，对目标正向电流密度进行扫描。结果如表3所示。

表3  固定寿命条件下的目标正向电流密度扫描

| 目标 `$J_F$` / `$A\,cm^{-2}$` | 实际 `$J_F$` / `$A\,cm^{-2}$` | `$V_F$` / V | `$Q_{rr}/A$` / `$C\,cm^{-2}$` | `$I_{rrm}/A$` / `$A\,cm^{-2}$` | `$Q_{stored}/A$` / `$C\,cm^{-2}$` |
|---:|---:|---:|---:|---:|---:|
| `$1.0\times10^{-4}$` | `$1.000\times10^{-4}$` | 0.3555 | `$3.772\times10^{-9}$` | 3.770 | `$4.589\times10^{-9}$` |
| `$1.0\times10^{-3}$` | `$1.000\times10^{-3}$` | 0.4257 | `$4.211\times10^{-9}$` | 4.206 | `$6.345\times10^{-9}$` |
| `$1.0\times10^{-2}$` | `$9.990\times10^{-3}$` | 0.4908 | `$5.365\times10^{-9}$` | 5.347 | `$1.096\times10^{-8}$` |

由表3可见，随着目标正向电流密度从 `$1.0\times10^{-4}$ A/cm^2` 增至 `$1.0\times10^{-2}$ A/cm^2`，`$Q_{rr}/A$` 和 `$Q_{stored}/A$` 均增加。相较于寿命扫描，该组实验改变的是正向注入强度，因而可用于检验 benchmark 对初始导通条件的敏感性。图4给出了恢复面电荷和存储移动面电荷随目标正向电流密度变化的趋势。该结果说明，本文基准不只包含单一工作点，而能够通过统一的数据格式和后处理脚本描述不同初始导通条件下的恢复行为。

### 3.5 时间步长敏感性

在 `$\tau=1.0\times10^{-6}$ s`、固定目标电流协议下，对时间步长进行扫描，结果如表4所示。

表4  固定目标电流协议下的时间步长扫描

| 时间步长 `$\Delta t$` / s | `$Q_{rr}/A$` / `$C\,cm^{-2}$` | `$I_{rrm}/A$` / `$A\,cm^{-2}$` | `$t_{rr}$` / s | `$Q_{stored}/A$` / `$C\,cm^{-2}$` |
|---:|---:|---:|---:|---:|
| `$5.0\times10^{-9}$` | `$4.211294\times10^{-9}$` | 1.684 | `$5.0\times10^{-9}$` | `$6.345\times10^{-9}$` |
| `$2.0\times10^{-9}$` | `$4.211263\times10^{-9}$` | 4.206 | `$2.0\times10^{-9}$` | `$6.345\times10^{-9}$` |
| `$1.0\times10^{-9}$` | `$4.211155\times10^{-9}$` | 8.401 | `$1.0\times10^{-9}$` | `$6.345\times10^{-9}$` |

可以看到，`$Q_{rr}/A$` 在三个时间步长下几乎不变，最大相对变化低于 0.004%；而 `$I_{rrm}/A$` 从 1.684 A/cm^2 增至 8.401 A/cm^2，表现出显著时间步长依赖。其原因在于本文采用理想电压阶跃作为反向边界，反向恢复初期的窄脉冲峰值主要由最初几个时间点决定，峰值电流对时间离散分辨率十分敏感。相比之下，`$Q_{rr}/A$` 是时间积分量，对单点峰值误差更稳健。图5给出了相对变化曲线。

该结果提示，在没有外部串联电阻、电感或实际驱动回路的理想阶跃 benchmark 中，应谨慎使用 `$I_{rrm}$` 和 `$t_{rr}$` 作为主评价指标。对于跨时间步长、跨代码或跨工具比较，`$Q_{rr}/A$` 更适合作为主参考指标，峰值电流密度则应作为辅助量并附带时间步长说明。

### 3.6 网格密度收敛性

在固定正向电压协议、`$\tau=1.0\times10^{-6}$ s` 和 `$\Delta t=2.0\times10^{-9}$ s` 条件下，本文测试了 `$5.0\times10^{-7}$ cm`、`$2.0\times10^{-7}$ cm` 和 `$1.0\times10^{-7}$ cm` 三种过渡区网格密度。结果显示，网格加密过程中 `$Q_{rr}/A$` 相对变化约为 0.03%，`$I_{rrm}/A$` 相对变化约为 0.04%，运行时间由约 1.28 s 增加到 4.48 s。图6显示了网格收敛结果。

上述结果说明，在当前一维 PIN 结构和阶跃掺杂条件下，默认网格密度已经能够稳定提取恢复电荷和峰值电流。同时，全部扫描数据规模较小，适合在普通工作站或笔记本上复跑。这是该基准作为开放参考问题的重要条件。

## 4 开放基准的复现性意义与局限

本文基准的主要价值并非替代商业 TCAD 对真实器件的高精度预测，而是提供一个可审计的最小完整流程。该流程包含器件结构、物理模型、参考面积、网格、偏置历史、瞬态波形、指标提取脚本和收敛性检查。对于商业 TCAD 论文而言，受授权软件和专有模型限制，完全公开输入 deck、网格和后处理脚本并不总是可行；而开源基准能够补充这一不足，使研究者在不依赖专有环境的情况下复查反向恢复仿真的基本数值行为。

同时，本文基准具有明确局限。第一，模型为一维硅 PIN 二极管，不包含真实功率器件的终端结构、边缘电场、封装寄生和工艺非均匀性。第二，物理模型采用简化漂移-扩散和 SRH 复合，未考虑温度耦合、Auger 复合、复杂陷阱分布、场依赖寿命或实测参数校准。第三，反向切换边界为理想电压阶跃，缺少实际测试电路中的串联电阻、电感和驱动源动态，因此峰值电流密度不宜直接用于工程损耗预测。第四，参考面积 `$A=1.0$ cm^2` 仅用于归一化和基准比较，并不代表具体器件面积。第五，本文尚未进行与商业 TCAD 或实验波形的定量对比，因此结论限于所定义的开放基准内部。

后续工作可从三个方向扩展：一是加入外部电路边界，减弱理想电压阶跃导致的峰值电流离散敏感性；二是根据具体实验器件引入真实面积、串联电阻和封装寄生，使结果更便于与实验或数据手册对照；三是在保持输入公开的前提下扩展到二维结构、温度扫描和跨工具验证，从而进一步提高基准的普适性。

## 5 结论

本文基于开源 DEVSIM 建立了一维硅 PIN 二极管反向恢复可复现仿真基准，公开了器件结构、参考面积、偏置协议、瞬态波形和指标提取方法。研究表明，固定目标正向电流密度协议比固定正向电压协议更适合比较寿命效应；在 `$J_F=1.0\times10^{-3}$ A/cm^2` 条件下，寿命由 `$1.0\times10^{-8}$ s` 增至 `$1.0\times10^{-5}$ s` 时，`$Q_{rr}/A$` 由 `$3.495\times10^{-9}$ C/cm^2` 增至 `$4.297\times10^{-9}$ C/cm^2`，存储移动面电荷由 `$3.478\times10^{-9}$ C/cm^2` 增至 `$6.687\times10^{-9}$ C/cm^2`。目标正向电流密度扫描进一步表明，`$J_F$` 从 `$1.0\times10^{-4}$ A/cm^2` 增至 `$1.0\times10^{-2}$ A/cm^2` 时，`$Q_{rr}/A$` 从 `$3.772\times10^{-9}$ C/cm^2` 增至 `$5.365\times10^{-9}$ C/cm^2`。时间步长扫描显示，积分电荷 `$Q_{rr}/A$` 对时间步长变化具有较好稳定性，而峰值电流密度 `$I_{rrm}/A$` 在理想电压阶跃下高度依赖时间分辨率。网格扫描表明，当前默认网格能够稳定提取主要指标。本文结果说明，开放代码、开放原始波形和开放后处理流程能够为反向恢复仿真提供透明的参考基准，并为后续跨工具比较和更复杂器件建模奠定基础。

## 参考文献

[1] SZE S M, NG K K. Physics of Semiconductor Devices[M]. 3rd ed. Hoboken: Wiley, 2006.

[2] SELBERHERR S. Analysis and Simulation of Semiconductor Devices[M]. Wien: Springer, 1984.

[3] SCHARFETTER D L, GUMMEL H K. Large-signal analysis of a silicon Read diode oscillator[J]. IEEE Transactions on Electron Devices, 1969, 16(1): 64-77.

[4] SHOCKLEY W, READ W T. Statistics of the recombinations of holes and electrons[J]. Physical Review, 1952, 87(5): 835-842.

[5] HALL R N. Electron-hole recombination in germanium[J]. Physical Review, 1952, 87(2): 387.

[6] DEVSIM LLC. DEVSIM TCAD Device Simulator[EB/OL]. https://github.com/devsim/devsim.

[7] DEVSIM LLC. DEVSIM TCAD Semiconductor Device Simulator Documentation[EB/OL]. https://devsim.org/.

[8] PENG R D. Reproducible research in computational science[J]. Science, 2011, 334(6060): 1226-1227.

[9] ARABAS S, BAREFORD M R, DE SILVA L R, et al. Case studies and challenges in reproducibility in the computational sciences[EB/OL]. arXiv:1408.2123, 2014.

[10] CALADO P, GELMETTI I, HILTON B, et al. Driftfusion: An open source code for simulating ordered semiconductor devices with mixed ionic-electronic conducting materials in one dimension[EB/OL]. arXiv:2009.04384, 2020.

[11] NAYAK D, KUMAR Y R, KUMAR M, et al. Temperature dependent reverse recovery characterization of SiC MOSFETs body diode for switching loss estimation in a half-bridge[EB/OL]. arXiv:2104.09271, 2021.

[12] GAGGL P, BURIN J, GSPONER A, et al. TCAD modeling of radiation-induced defects in 4H-SiC diodes[EB/OL]. arXiv:2407.11776, 2024.
