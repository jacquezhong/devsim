# DEVSIM Auto Simulation Skill - 快速开始指南

## 安装

此skill已集成到opencode中，无需额外安装。

## 使用方法

### 1. 隐式触发（推荐）

直接在对话中描述仿真需求：

```
用户: 仿真一个硅二极管，n型掺杂1e18，p型掺杂1e16
系统: [自动执行仿真]

用户: HgCdTe探测器在77K的暗电流
系统: [自动识别窄禁带材料，配置Auger模型，运行仿真]

用户: 复现papers/JEM2025.pdf中的nBn器件
系统: [自动提取文献参数并仿真]
```

### 2. 编程接口

```python
# 方法1: 使用便捷函数
from core import auto_simulate, simulate_from_paper

result = auto_simulate("硅二极管 n型1e18 p型1e16")
print(result["summary"])

# 方法2: 从文献仿真
result = simulate_from_paper("papers/JEM2025.pdf")
```

### 3. 交互模式

```bash
cd .opencode/skills/devsim-simulation
python core/__init__.py
```

## 支持的器件类型

- **二极管**: diode, pn junction
- **场效应管**: MOSFET (简化)
- **双极晶体管**: BJT
- **红外探测器**: nBn, QWIP
- **光电器件**: solar cell, photodetector

## 支持的仿真类型

- **DC分析**: IV曲线、静态特性
- **瞬态分析**: 时间响应、脉冲特性
- **AC分析**: C-V特性、小信号响应
- **光学分析**: 光电流、量子效率

## 文件结构

```
devsim-simulation/
├── SKILL.md                    # 主文档
├── core/                       # 核心代码
│   ├── inference_engine.py     # 意图识别
│   ├── mesh_generator.py       # 自适应网格
│   ├── physics_selector.py     # 物理模型选择
│   ├── adaptive_solver.py      # 自适应求解
│   ├── convergence_recovery.py # 收敛恢复
│   ├── result_manager.py       # 结果管理
│   ├── web_learner.py          # 网络学习
│   └── __init__.py             # 主控制器
├── knowledge/                  # 知识库
│   ├── physics_principles.yaml # 物理原则
│   └── materials.yaml          # 材料参数
├── data/                       # 用户数据 (.gitignore)
│   ├── temp/                   # 临时文件
│   ├── material_cache/         # 材料缓存
│   └── experience_db/          # 经验数据库
└── integration/
    └── paper_reader_bridge.py  # PDF解析集成
```

## 自适应特性

### 温度自适应
- **硅**: 默认300K
- **窄禁带**: 默认77K (HgCdTe, InSb)
- **自定义**: 用户指定温度

### 物理模型自适应
根据带隙自动选择：
- **窄禁带 (Eg < 0.5eV)**: Auger + SRH + Fermi-Dirac
- **中等带隙 (0.5-2.0eV)**: SRH
- **宽禁带 (Eg > 2.0eV)**: SRH + 辐射复合

### 网格自适应
- **初始网格**: 基于物理原则 (薄层加密、边界优先)
- **自适应细化**: 根据求解结果在高梯度区细化
- **全程自适应**: 每个偏置点都可能调整

## 收敛恢复策略

不收敛时自动尝试：
1. 减小偏置步长
2. 对数阻尼
3. 改进初始猜测
4. 网格细化
5. 切换求解器 (Newton → Gummel)
6. 放宽容差

## 输出格式

### 数据文件
- **格式**: DEVSIM原生格式
- **位置**: `data/temp/sim_<timestamp>.dat`

### 报告文件
- **格式**: JSON
- **位置**: `data/temp/sim_<timestamp>_report.json`

### 摘要
- **格式**: 文本
- **包含**: 器件信息、物理模型、关键参数、收敛状态

## 限制

### 当前限制
- 仅支持 **1D仿真**
- 2D/3D请求会提示简化
- 需要DEVSIM环境

### 扩展计划
- [ ] 2D器件支持
- [ ] 温度扫描自动化
- [ ] 参数自动优化
- [ ] 更多材料数据库

## 故障排除

### 问题: 仿真不收敛
**解决**: 系统会自动重试，最多5次

### 问题: 缺少参数
**解决**: 系统会询问具体数值，并提供默认值

### 问题: PDF解析失败
**解决**: 系统会提示手动输入参数格式

### 问题: 2D/3D请求
**解决**: 简化为1D近似，或等待后续更新

## 贡献

欢迎提交Issue和PR来改进此skill！

## 许可证

Apache 2.0 (与DEVSIM项目一致)
