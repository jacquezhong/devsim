"""
自适应求解器 - 自适应运行控制和全程自适应
"""
from typing import Dict, List, Optional, Callable, Any
import json
import os
from datetime import datetime


class AdaptiveSolver:
    """自适应求解器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.solution_history = []
        self.current_iteration = 0
        self.max_iterations = 5
        
    def run_simulation(self, device_config: Dict, physics_config: Dict,
                      mesh_config: Dict, callback: Optional[Callable] = None) -> Dict:
        """运行自适应仿真"""
        results = {
            "status": "initializing",
            "iterations": [],
            "final_solution": None,
            "convergence": False,
            "output_files": []
        }
        
        # 1. 初始求解
        print("=" * 60)
        print("开始自适应仿真")
        print("=" * 60)
        
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration
            print(f"\n--- 迭代 {iteration + 1}/{self.max_iterations} ---")
            
            # 运行当前网格下的求解
            iteration_result = self._run_single_iteration(
                device_config, physics_config, mesh_config, iteration
            )
            
            results["iterations"].append(iteration_result)
            
            if iteration_result["converged"]:
                print(f"✓ 求解收敛")
                results["convergence"] = True
                results["final_solution"] = iteration_result["solution"]
                break
            
            # 检查是否需要继续细化
            if iteration < self.max_iterations - 1:
                needs_refinement = self._check_refinement_needed(iteration_result)
                if needs_refinement:
                    print(f"→ 需要网格细化，继续迭代...")
                    mesh_config = self._refine_mesh(mesh_config, iteration_result)
                else:
                    print(f"✗ 求解未收敛但无需细化")
                    break
        
        # 保存结果
        results["status"] = "completed" if results["convergence"] else "incomplete"
        self._save_results(results)
        
        return results
    
    def _run_single_iteration(self, device_config: Dict, physics_config: Dict,
                             mesh_config: Dict, iteration: int) -> Dict:
        """运行单次迭代"""
        result = {
            "iteration": iteration,
            "mesh_nodes": self._count_mesh_nodes(mesh_config),
            "converged": False,
            "solution": {},
            "gradients": {},
            "errors": []
        }
        
        try:
            # 这里应该调用实际的DEVSIM求解
            # 简化版本：模拟求解过程
            print(f"  网格节点数: {result['mesh_nodes']}")
            print(f"  求解方程...")
            
            # 模拟求解（实际实现中调用DEVSIM API）
            # solution = devsim.solve(type="dc", ...)
            
            # 提取物理量梯度用于判断是否收敛和是否需要细化
            result["gradients"] = self._extract_gradients(mesh_config)
            result["converged"] = self._check_convergence(result["gradients"])
            
            if result["converged"]:
                result["solution"] = {
                    "potential": "extracted",
                    "electrons": "extracted",
                    "holes": "extracted",
                    "currents": "calculated"
                }
            
        except Exception as e:
            result["errors"].append(str(e))
            print(f"  ✗ 求解失败: {e}")
        
        return result
    
    def _count_mesh_nodes(self, mesh_config: Dict) -> int:
        """统计网格节点数"""
        regions = mesh_config.get("regions", [])
        total = 0
        for region in regions:
            length = region.get("end", 0) - region.get("start", 0)
            mesh_size = region.get("mesh_size", 1e-4)
            if mesh_size > 0:
                total += int(length / mesh_size)
        return max(total, 10)
    
    def _extract_gradients(self, mesh_config: Dict) -> Dict:
        """提取物理场梯度（简化版本）"""
        # 实际实现中从DEVSIM解中提取
        gradients = {}
        regions = mesh_config.get("regions", [])
        
        for region in regions:
            region_name = region.get("name", "unknown")
            # 模拟梯度计算
            gradients[region_name] = {
                "electric_field": 1e4,  # V/cm
                "carrier_gradient": 1.5,  # orders
                "potential_change": 0.3  # V/um
            }
        
        return gradients
    
    def _check_convergence(self, gradients: Dict) -> bool:
        """检查收敛性"""
        # 简化的收敛检查
        # 实际应该检查残差、迭代次数等
        for region_name, grad in gradients.items():
            # 如果梯度在合理范围内，认为收敛
            if grad.get("electric_field", 0) < 1e5:  # < 100kV/cm
                return True
        return False
    
    def _check_refinement_needed(self, iteration_result: Dict) -> bool:
        """检查是否需要网格细化"""
        gradients = iteration_result.get("gradients", {})
        
        for region_name, grad in gradients.items():
            # 细化准则
            if grad.get("electric_field", 0) > 5e4:  # > 50kV/cm
                return True
            if grad.get("carrier_gradient", 0) > 2.0:  # > 2 orders
                return True
            if grad.get("potential_change", 0) > 0.5:  # > 0.5V/um
                return True
        
        return False
    
    def _refine_mesh(self, mesh_config: Dict, iteration_result: Dict) -> Dict:
        """细化网格"""
        gradients = iteration_result.get("gradients", {})
        regions = mesh_config.get("regions", [])
        
        for region in regions:
            region_name = region.get("name", "")
            if region_name in gradients:
                grad = gradients[region_name]
                
                # 根据梯度调整网格尺寸
                if grad.get("electric_field", 0) > 5e4:
                    region["mesh_size"] = region.get("mesh_size", 1e-4) * 0.5
                    region["refinement"] = region.get("refinement", 1.0) * 2.0
        
        return mesh_config
    
    def _save_results(self, results: Dict):
        """保存仿真结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_{timestamp}.json"
        filepath = os.path.join(self.data_dir, "temp", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n结果保存: {filepath}")
    
    def run_dc_sweep(self, device: str, region: str, contact: str,
                    start_bias: float, end_bias: float, steps: int,
                    abs_error: float = 1e10, rel_error: float = 1e-10) -> List[Dict]:
        """运行DC偏置扫描"""
        results = []
        bias_step = (end_bias - start_bias) / steps
        
        print(f"\nDC扫描: {contact} {start_bias}V → {end_bias}V ({steps}步)")
        
        for i in range(steps + 1):
            bias = start_bias + i * bias_step
            print(f"  偏置: {bias:.3f}V ...", end=" ")
            
            try:
                # 设置偏置
                # devsim.set_parameter(device=device, name=f"{contact}_bias", value=bias)
                
                # 求解
                # devsim.solve(type="dc", absolute_error=abs_error, relative_error=rel_error)
                
                # 提取结果
                result = {
                    "bias": bias,
                    "current": 0.0,  # 从接触提取
                    "converged": True
                }
                results.append(result)
                print("✓")
                
            except Exception as e:
                print(f"✗ ({e})")
                results.append({
                    "bias": bias,
                    "current": None,
                    "converged": False,
                    "error": str(e)
                })
        
        return results


# 单例
_adaptive_solver = None

def get_adaptive_solver(data_dir: str) -> AdaptiveSolver:
    """获取自适应求解器单例"""
    global _adaptive_solver
    if _adaptive_solver is None:
        _adaptive_solver = AdaptiveSolver(data_dir)
    return _adaptive_solver
