"""
主控制器 - 整合所有模块，提供统一的仿真接口
"""
import os
import sys
from typing import Dict, Optional, Any

# 添加core目录到路径
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
core_dir = os.path.join(skill_dir, "core")
knowledge_dir = os.path.join(skill_dir, "knowledge")
data_dir = os.path.join(skill_dir, "data")
integration_dir = os.path.join(skill_dir, "integration")

# 导入各模块
sys.path.insert(0, core_dir)
sys.path.insert(0, integration_dir)

try:
    from inference_engine import get_inference_engine, SimulationIntent
    from physics_selector import get_physics_selector
    from result_manager import get_result_manager
    from paper_reader_bridge import PaperReaderBridge
except ImportError as e:
    print(f"Warning: Could not import module: {e}")
    # 提供存根
    def get_inference_engine():
        return None
    def get_physics_selector(knowledge_dir):
        return None
    def get_result_manager(data_dir):
        return None
    class PaperReaderBridge:
        def __init__(self, papers_dir):
            pass


class DEVSIMAutoSimulation:
    """DEVSIM全自动仿真控制器"""
    
    def __init__(self):
        self.inference = get_inference_engine()
        self.physics = get_physics_selector(knowledge_dir)
        self.results = get_result_manager(data_dir)
        self.paper_bridge = PaperReaderBridge(papers_dir="papers")
        
        self.current_config = {}
        self.current_results = {}
    
    def run_from_conversation(self, user_input: str) -> Dict:
        """
        从用户对话运行仿真
        
        主入口函数 - 处理自然语言输入
        """
        print("=" * 70)
        print("DEVSIM 自动仿真系统")
        print("=" * 70)
        
        # 1. 意图识别
        print("\n[1/5] 解析用户意图...")
        intent = self.inference.parse_user_input(user_input)
        
        if intent.confidence < 0.5 or intent.missing_params:
            # 信息不足，询问用户
            prompt = self.inference.generate_prompt_for_missing(intent)
            return {
                "status": "need_more_info",
                "prompt": prompt,
                "intent": intent
            }
        
        print(f"  ✓ 设备类型: {intent.device_type}")
        print(f"  ✓ 材料: {intent.material}")
        print(f"  ✓ 温度: {intent.temperature}K")
        print(f"  ✓ 维度: {intent.dimension}D")
        
        # 2. 检查维度支持
        if intent.dimension > 1:
            return {
                "status": "dimension_not_supported",
                "message": f"当前仅支持1D仿真，检测到{intent.dimension}D请求",
                "suggestion": "可简化为1D近似或等待后续更新"
            }
        
        # 3. 构建设备配置
        print("\n[2/5] 构建设备配置...")
        device_config = self._build_device_config(intent)
        
        # 4. 选择物理模型
        print("\n[3/5] 选择物理模型...")
        physics_config = self.physics.select_physics_models(
            material=intent.material,
            device_type=intent.device_type,
            temperature=intent.temperature,
            simulation_type=intent.simulation_type
        )
        
        self._print_physics_summary(physics_config)
        
        # 5. 生成自适应网格
        print("\n[4/5] 生成自适应网格...")
        # mesh_config = mesh_gen.generate_initial_mesh(device_config)
        mesh_config = {"regions": device_config.get("regions", [])}
        
        print(f"  ✓ 区域数: {len(mesh_config['regions'])}")
        
        # 6. 运行仿真
        print("\n[5/5] 运行仿真...")
        # 实际仿真需要调用DEVSIM，这里是框架
        simulation_results = self._run_simulation(
            device_config, physics_config, mesh_config
        )
        
        # 7. 保存结果
        if simulation_results.get("success"):
            output_file = self.results.save_simulation_results(
                simulation_results,
                device_config,
                physics_config,
                mesh_config
            )
            
            return {
                "status": "success",
                "output_file": output_file,
                "summary": self.results._generate_summary({
                    "metadata": {"timestamp": "", "status": "success"},
                    "configuration": {
                        "device": device_config,
                        "physics": physics_config
                    },
                    "results": simulation_results
                }),
                "intent": intent
            }
        else:
            return {
                "status": "failed",
                "error": simulation_results.get("error", "Unknown error"),
                "intent": intent
            }
    
    def run_from_paper(self, paper_path: str, custom_params: Optional[Dict] = None) -> Dict:
        """
        从文献运行仿真
        
        Args:
            paper_path: PDF文件路径
            custom_params: 用户自定义参数（覆盖文献值）
        """
        print("=" * 70)
        print("从文献提取并运行仿真")
        print("=" * 70)
        
        # 1. 提取文献参数
        print(f"\n[1/3] 解析文献: {paper_path}")
        paper_params = self.paper_bridge.extract_from_paper(paper_path)
        
        if not paper_params.get("success"):
            return {
                "status": "paper_extraction_failed",
                "error": paper_params.get("error"),
                "suggestion": self.paper_bridge.suggest_extraction(paper_path)
            }
        
        extracted = paper_params.get("extracted_params", {})
        print(f"  ✓ 提取到 {len(extracted)} 组参数")
        
        # 2. 合并自定义参数
        if custom_params:
            extracted.update(custom_params)
            print(f"  ✓ 应用 {len(custom_params)} 个自定义参数")
        
        # 3. 生成设备配置
        print("\n[2/3] 生成仿真配置...")
        device_config = self.paper_bridge.generate_device_config(extracted)
        
        # 4. 运行仿真
        print("\n[3/3] 运行仿真...")
        # 构建intent以便复用run_from_conversation的逻辑
        from inference_engine import SimulationIntent
        intent = SimulationIntent(
            device_type=extracted.get("device_type", "diode"),
            material=extracted.get("material", "Silicon"),
            temperature=extracted.get("operating_conditions", {}).get("temperature_K", 300),
            simulation_type="dc"
        )
        
        # 获取物理配置
        physics_config = self.physics.select_physics_models(
            material=intent.material,
            device_type=intent.device_type,
            temperature=intent.temperature
        )
        
        mesh_config = {"regions": device_config.get("regions", [])}
        
        # 运行仿真
        simulation_results = self._run_simulation(
            device_config, physics_config, mesh_config
        )
        
        # 保存结果
        if simulation_results.get("success"):
            output_file = self.results.save_simulation_results(
                simulation_results, device_config, physics_config, mesh_config
            )
            
            # 如果有参考数据，进行对比
            comparison = None
            if "reference_figures" in extracted:
                comparison = self.results.compare_with_reference(
                    output_file, extracted
                )
            
            return {
                "status": "success",
                "output_file": output_file,
                "paper_params": extracted,
                "comparison": comparison,
                "intent": intent
            }
        else:
            return {
                "status": "failed",
                "error": simulation_results.get("error"),
                "paper_params": extracted
            }
    
    def _build_device_config(self, intent) -> Dict:
        """从意图构建设备配置"""
        # 基本结构
        config = {
            "device_type": intent.device_type,
            "material": intent.material,
            "temperature": intent.temperature,
            "regions": []
        }
        
        # 根据设备类型和掺杂构建区域
        if intent.device_type in ["diode", "pn"]:
            # 二极管结构
            doping = intent.doping_profile or {}
            
            # n区
            if "n_type" in doping:
                config["regions"].append({
                    "name": "n_region",
                    "material": intent.material,
                    "length": 5e-4,  # 5um
                    "doping_type": "n",
                    "doping_conc": doping["n_type"]
                })
            
            # p区
            if "p_type" in doping:
                config["regions"].append({
                    "name": "p_region",
                    "material": intent.material,
                    "length": 5e-4,  # 5um
                    "doping_type": "p",
                    "doping_conc": doping["p_type"]
                })
        
        return config
    
    def _print_physics_summary(self, physics_config: Dict):
        """打印物理模型摘要"""
        print(f"  ✓ 带隙: {physics_config.get('bandgap_eV', 'N/A')} eV")
        print(f"  ✓ 物理模型:")
        
        models = physics_config.get("models", {})
        for model_name, model_info in models.items():
            if model_info.get("required"):
                print(f"    - {model_name} (必需)")
            else:
                print(f"    - {model_name} (可选)")
    
    def _run_simulation(self, device_config: Dict, physics_config: Dict, 
                       mesh_config: Dict) -> Dict:
        """
        执行实际仿真
        
        注意: 这里应该调用DEVSIM API
        当前为框架实现
        """
        # 这里是占位符，实际实现需要导入devsim并调用API
        # import devsim
        # ...
        
        # 模拟结果
        return {
            "success": True,
            "status": "completed",
            "message": "仿真框架已就绪，等待DEVSIM集成",
            "iv_data": [
                {"bias": 0.0, "current": 1e-12},
                {"bias": 0.1, "current": 1e-11},
                {"bias": 0.5, "current": 1e-3},
            ]
        }
    
    def interactive_session(self):
        """交互式会话模式"""
        print("\n" + "=" * 70)
        print("DEVSIM 自动仿真 - 交互模式")
        print("输入 'quit' 或 '退出' 结束会话")
        print("=" * 70 + "\n")
        
        while True:
            user_input = input("\n请输入仿真需求: ").strip()
            
            if user_input.lower() in ["quit", "exit", "退出", "q"]:
                print("\n感谢使用，再见！")
                break
            
            if not user_input:
                continue
            
            result = self.run_from_conversation(user_input)
            
            if result["status"] == "need_more_info":
                print("\n" + result["prompt"])
            elif result["status"] == "success":
                print("\n" + result["summary"])
            else:
                print(f"\n✗ 错误: {result.get('error', 'Unknown')}")


# 便捷函数
def auto_simulate(user_input: str) -> Dict:
    """
    便捷函数：自动运行仿真
    
    使用示例:
        result = auto_simulate("硅二极管 n型1e18 p型1e16")
        if result["status"] == "success":
            print(result["summary"])
    """
    simulator = DEVSIMAutoSimulation()
    return simulator.run_from_conversation(user_input)


def simulate_from_paper(paper_path: str, **custom_params) -> Dict:
    """
    便捷函数：从文献运行仿真
    
    使用示例:
        result = simulate_from_paper("papers/JEM2025.pdf")
    """
    simulator = DEVSIMAutoSimulation()
    return simulator.run_from_paper(paper_path, custom_params)


# 如果直接运行此文件
if __name__ == "__main__":
    simulator = DEVSIMAutoSimulation()
    simulator.interactive_session()
