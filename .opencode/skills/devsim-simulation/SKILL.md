# DEVSIM Auto Simulation Skill

全自动TCAD器件仿真Skill，基于对话内容自动识别意图并执行DEVSIM仿真。

## 功能特性

- **隐式触发**: 通过自然对话自动识别仿真意图
- **全自动配置**: 温度、物理模型、网格自适应选择
- **智能网格**: 基于物理原则的全程自适应网格细化
- **自动重试**: 仿真不收敛时自动修复并重新运行
- **网络学习**: 自动搜索最新材料参数和最佳实践
- **PDF解析**: 提取文献中的器件参数和结果对比
- **本地缓存**: 材料参数和经验数据库持久化存储

## 触发关键词

### 设备类型
- 基础: diode, pn junction, Schottky
- 场效应: MOSFET, JFET
- 双极: BJT, HBT
- 光电器件: photodetector, solar cell, LED
- 红外: nBn, QWIP, HgCdTe, InSb

### 仿真类型
- DC: IV curve, IV characteristic, static analysis
- 瞬态: transient, time-dependent, pulse response
- 小信号: AC analysis, C-V, capacitance
- 光学: quantum efficiency, responsivity, photocurrent

### 材料
- Silicon, GaAs, InP, GaN, SiC
- HgCdTe, InSb, InGaAs
- 氧化物: SiO2, Al2O3, HfO2

### 分析
- 暗电流: dark current
- 光电流: photocurrent, photo-response
- 提取参数: threshold voltage, mobility, lifetime

## 使用示例

### 示例1: 简单二极管

```
用户: 仿真一个硅二极管，n型掺杂1e18，p型掺杂1e16，温度300K
系统: 
  ✓ 识别: 1D硅二极管
  ✓ 配置: 300K, Poisson+DD+SRH
  ✓ 网格: 基于掺杂梯度自适应
  ✓ 运行: DC扫描 0-1V
  → 结果保存至 results/diode_xxx.dat
```

### 示例2: 红外探测器

```
用户: HgCdTe nBn探测器在77K的暗电流
系统:
  ✓ 识别: 窄禁带红外探测器
  ✓ 配置: 77K, Auger+SRH+FD统计
  ✓ 网格: 势垒层极细(0.01μm), 界面超细(0.005μm)
  ✓ 运行: 暗电流分析 -0.1V→0.5V
  → RA乘积: 8.3e4 Ω·cm²
  → 结果保存
```

### 示例3: 结合文献

```
用户: 复现papers/JEM2025.pdf中的nBn器件性能
系统:
  ✓ 解析PDF...
  ✓ 提取: 三层结构, 厚度, 掺杂, 温度
  ✓ 配置: 匹配文献参数
  ✓ 运行: 仿真并对比Figure 3
  → 提取数据: paper_fig3_data.csv
  → 对比分析完成
```

## 工作机制

### 1. 意图识别
分析用户对话，提取:
- 设备类型和结构
- 材料和参数
- 仿真目标和条件

### 2. 自适应配置
根据物理原则自动选择:
- **温度**: 材料特性决定 (硅→300K, 窄禁带→77K)
- **物理模型**: 
  - 窄禁带(Eg<0.5eV): 必须Auger+FD统计
  - 宽禁带(Eg>2eV): SRH+辐射复合
  - 高频: 位移电流
  - 光电: 光生载流子生成
- **网格**: 基于物理场梯度和边界特征

### 3. 网格生成原则

```yaml
物理驱动网格:
  高梯度区: E-field > 0.5V/μm, dn/dx > 2 orders/μm
  边界优先: 接触、界面强制细化
  特征尺寸: 薄层(<0.1μm)至少10个节点
  
自适应循环:
  1. 初始网格(基于先验)
  2. 求解 → 计算梯度场
  3. 标记高梯度区
  4. 局部细化
  5. 重求解 → 检查收敛
```

### 4. 收敛恢复策略

不收敛时自动尝试:
1. 减小偏置步长 (×0.5)
2. 使用对数阻尼 (log_damping)
3. 改进初始猜测 (插值)
4. 网格细化 (高场区)
5. 切换求解器 (Newton → Gummel)

### 5. 信息缺失处理

关键参数缺失时主动询问:
```
检测到需要更多信息:
1. 器件总长度? [默认: 10um]
2. n区掺杂浓度? [默认: 1e17 cm^-3]
3. 温度? [默认: 300K]
```

## 目录结构

```
devsim-simulation/
├── SKILL.md                    # 本文档
├── core/                       # 核心代码
│   ├── inference_engine.py     # 意图识别
│   ├── mesh_generator.py       # 自适应网格生成
│   ├── physics_selector.py     # 物理模型选择
│   ├── adaptive_solver.py      # 自适应求解器
│   ├── convergence_recovery.py # 收敛恢复
│   ├── result_manager.py       # 结果管理
│   └── web_learner.py          # 网络学习
├── knowledge/                  # 知识库
│   ├── physics_principles.yaml # 物理原则
│   └── materials.yaml          # 材料参数
├── data/                       # 用户数据 (.gitignore)
│   ├── material_cache/         # 材料参数缓存
│   ├── experience_db/          # 经验数据库
│   └── temp/                   # 临时文件
└── integration/                # 外部集成
    └── paper_reader_bridge.py  # PDF文献解析
```

## 输出格式

### 数据文件
- **格式**: DEVSIM原生格式 (`type="devsim_data"`)
- **位置**: `data/temp/sim_<timestamp>.dat`
- **内容**: 完整器件状态和物理场分布

### 结构化报告
- **格式**: JSON
- **位置**: `data/temp/sim_<timestamp>_report.json`
- **内容**: 仿真配置、关键参数、收敛状态、文件列表

## 与可视化分离

本skill专注仿真执行和数据保存，可视化由独立skill处理:
- 调用: `devsim-visualization` skill
- 输入: 仿真数据文件路径
- 输出: 图表和分析

## 限制

### 当前限制
- **维度**: 仅支持1D仿真
- **2D/3D**: 遇到时提示并简化或提供模板

### 不适用场景
- 需要复杂量子效应（隧穿、量子阱能级计算）
- 多物理场耦合（热-电-机械）
- 蒙特卡洛输运模拟

## 依赖

- Python 3.7+
- DEVSIM (已安装)
- paper-reader skill (PDF解析)
- 网络访问 (材料参数搜索)

## 更新计划

- [ ] 2D器件支持
- [ ] 温度扫描自动化
- [ ] 参数优化（自动拟合）
- [ ] 更多材料数据库

## 版本

v1.0.0 - 初始版本，支持1D器件全自动仿真
