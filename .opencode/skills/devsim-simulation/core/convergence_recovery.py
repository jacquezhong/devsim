"""
收敛恢复模块 - 自动重试和修复策略
"""
from typing import Dict, List, Optional, Callable
from enum import Enum
import time


class ConvergenceStrategy(Enum):
    """收敛恢复策略"""
    REDUCE_STEP = "reduce_step"           # 减小偏置步长
    LOG_DAMPING = "log_damping"          # 对数阻尼
    BETTER_INITIAL = "better_initial"    # 改进初始猜测
    REFINE_MESH = "refine_mesh"          # 网格细化
    SWITCH_SOLVER = "switch_solver"      # 切换求解器
    RELAX_TOLERANCE = "relax_tolerance"  # 放宽容差


class ConvergenceRecovery:
    """收敛恢复管理器"""
    
    # 策略库
    STRATEGIES = {
        ConvergenceStrategy.REDUCE_STEP: {
            "priority": 1,
            "applicable": ["diverged_at_bias"],
            "action": lambda cfg: {**cfg, "step_size": cfg.get("step_size", 0.1) * 0.5},
            "description": "减小偏置步长至50%"
        },
        ConvergenceStrategy.LOG_DAMPING: {
            "priority": 2,
            "applicable": ["oscillating", "potential_diverge"],
            "action": lambda cfg: {**cfg, "damping": "log", "potential_update": "log_damp"},
            "description": "启用对数阻尼"
        },
        ConvergenceStrategy.BETTER_INITIAL: {
            "priority": 3,
            "applicable": ["poor_initial", "first_iteration"],
            "action": lambda cfg: {**cfg, "initial_guess": "interpolate", "gummel_first": True},
            "description": "使用Gummel迭代改进初值"
        },
        ConvergenceStrategy.REFINE_MESH: {
            "priority": 4,
            "applicable": ["high_field_region", "interface_issue"],
            "action": lambda cfg: {**cfg, "mesh_refinement": 2.0},
            "description": "高梯度区网格细化2倍"
        },
        ConvergenceStrategy.SWITCH_SOLVER: {
            "priority": 5,
            "applicable": ["newton_fail", "jacobian_singular"],
            "action": lambda cfg: {**cfg, "solver": "gummel", "newton": False},
            "description": "Newton → Gummel求解器"
        },
        ConvergenceStrategy.RELAX_TOLERANCE: {
            "priority": 6,
            "applicable": ["tight_tolerance", "slow_convergence"],
            "action": lambda cfg: {
                **cfg, 
                "rel_error": cfg.get("rel_error", 1e-10) * 10,
                "abs_error": cfg.get("abs_error", 1e10) * 10
            },
            "description": "放宽收敛容差10倍"
        }
    }
    
    def __init__(self, max_retries: int = 5):
        self.max_retries = max_retries
        self.retry_count = 0
        self.attempt_history = []
        self.current_config = {}
    
    def run_with_recovery(self, solve_func: Callable, config: Dict) -> Dict:
        """
        带自动恢复的求解运行
        
        Args:
            solve_func: 求解函数
            config: 求解配置
            
        Returns:
            求解结果字典
        """
        self.current_config = config.copy()
        self.retry_count = 0
        self.attempt_history = []
        
        print("\n" + "=" * 60)
        print("开始求解 (带自动恢复)")
        print("=" * 60)
        
        while self.retry_count < self.max_retries:
            self.retry_count += 1
            print(f"\n--- 尝试 {self.retry_count}/{self.max_retries} ---")
            
            try:
                # 尝试求解
                result = solve_func(self.current_config)
                
                if result.get("converged", False):
                    print("✓ 求解成功收敛!")
                    result["recovery_attempts"] = self.retry_count - 1
                    result["recovery_success"] = True
                    return result
                else:
                    # 未收敛但未抛异常
                    error_info = self._analyze_divergence(result)
                    
            except Exception as e:
                # 求解失败
                error_info = self._analyze_error(str(e))
                print(f"✗ 求解失败: {e}")
            
            # 记录尝试
            self.attempt_history.append({
                "attempt": self.retry_count,
                "config": self.current_config.copy(),
                "error": error_info
            })
            
            # 选择并应用恢复策略
            if self.retry_count < self.max_retries:
                strategy = self._select_strategy(error_info)
                if strategy:
                    print(f"→ 应用策略: {strategy.value}")
                    self._apply_strategy(strategy)
                else:
                    print("✗ 无可用恢复策略")
                    break
        
        # 所有尝试失败
        print(f"\n✗ 所有{self.max_retries}次尝试均失败")
        return {
            "converged": False,
            "recovery_attempts": self.retry_count,
            "recovery_success": False,
            "history": self.attempt_history
        }
    
    def _analyze_error(self, error_msg: str) -> Dict:
        """分析错误信息"""
        error_lower = error_msg.lower()
        
        error_info = {
            "message": error_msg,
            "type": "unknown",
            "symptoms": []
        }
        
        # 识别错误类型
        if "convergence" in error_lower or "not converge" in error_lower:
            error_info["type"] = "convergence"
            error_info["symptoms"].append("diverged_at_bias")
        
        if "singular" in error_lower or "jacobian" in error_lower:
            error_info["type"] = "numerical"
            error_info["symptoms"].append("jacobian_singular")
        
        if "oscillat" in error_lower or "diverge" in error_lower:
            error_info["symptoms"].append("oscillating")
        
        if "initial" in error_lower or "guess" in error_lower:
            error_info["symptoms"].append("poor_initial")
        
        if "tolerance" in error_lower or "error" in error_lower:
            error_info["symptoms"].append("tight_tolerance")
        
        return error_info
    
    def _analyze_divergence(self, result: Dict) -> Dict:
        """分析未收敛结果"""
        error_info = {
            "type": "convergence",
            "symptoms": ["diverged_at_bias"],
            "residual": result.get("residual", 0),
            "iterations": result.get("iterations", 0)
        }
        
        # 根据迭代历史判断
        iterations = result.get("iterations", 0)
        if iterations > 20:
            error_info["symptoms"].append("slow_convergence")
        
        return error_info
    
    def _select_strategy(self, error_info: Dict) -> Optional[ConvergenceStrategy]:
        """选择恢复策略"""
        symptoms = error_info.get("symptoms", [])
        
        # 按优先级排序策略
        sorted_strategies = sorted(
            self.STRATEGIES.items(),
            key=lambda x: x[1]["priority"]
        )
        
        for strategy, info in sorted_strategies:
            # 检查策略是否适用
            applicable = info["applicable"]
            if any(s in symptoms for s in applicable):
                # 检查是否已尝试过
                if not self._was_strategy_tried(strategy):
                    return strategy
        
        # 如果没有特定匹配，选择未尝试过的最低优先级策略
        for strategy, _ in sorted_strategies:
            if not self._was_strategy_tried(strategy):
                return strategy
        
        return None
    
    def _was_strategy_tried(self, strategy: ConvergenceStrategy) -> bool:
        """检查策略是否已尝试过"""
        for attempt in self.attempt_history:
            if attempt.get("strategy") == strategy:
                return True
        return False
    
    def _apply_strategy(self, strategy: ConvergenceStrategy):
        """应用恢复策略"""
        strategy_info = self.STRATEGIES[strategy]
        
        # 应用策略动作
        self.current_config = strategy_info["action"](self.current_config)
        
        # 记录策略
        if self.attempt_history:
            self.attempt_history[-1]["strategy"] = strategy
            self.attempt_history[-1]["strategy_description"] = strategy_info["description"]
        
        print(f"  配置更新: {strategy_info['description']}")
    
    def get_recovery_report(self) -> str:
        """生成恢复报告"""
        lines = ["\n收敛恢复报告:", "=" * 60]
        
        for attempt in self.attempt_history:
            lines.append(f"\n尝试 {attempt['attempt']}:")
            lines.append(f"  错误: {attempt['error'].get('message', 'Unknown')}")
            if 'strategy' in attempt:
                lines.append(f"  策略: {attempt['strategy_description']}")
        
        return "\n".join(lines)


# 便捷函数
def solve_with_auto_recovery(solve_func: Callable, config: Dict, 
                            max_retries: int = 5) -> Dict:
    """
    便捷函数：自动恢复的求解包装器
    
    使用示例:
        def my_solver(config):
            # DEVSIM求解代码
            result = devsim.solve(type="dc", ...)
            return {"converged": True, "solution": result}
        
        result = solve_with_auto_recovery(my_solver, config)
    """
    recovery = ConvergenceRecovery(max_retries=max_retries)
    return recovery.run_with_recovery(solve_func, config)
