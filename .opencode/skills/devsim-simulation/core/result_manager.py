"""
结果管理器 - 管理和保存仿真结果
"""
import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any


class ResultManager:
    """仿真结果管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.temp_dir = os.path.join(data_dir, "temp")
        self.cache_dir = os.path.join(data_dir, "cache")
        
        # 确保目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def save_simulation_results(self, results: Dict, device_config: Dict,
                                physics_config: Dict, mesh_config: Dict) -> str:
        """保存完整的仿真结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建结果包
        result_package = {
            "metadata": {
                "timestamp": timestamp,
                "version": "1.0.0",
                "status": results.get("status", "unknown")
            },
            "configuration": {
                "device": device_config,
                "physics": physics_config,
                "mesh": mesh_config
            },
            "results": results
        }
        
        # 保存JSON报告
        json_file = os.path.join(self.temp_dir, f"simulation_{timestamp}_report.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_package, f, indent=2, ensure_ascii=False)
        
        # 保存CSV数据（IV曲线等）
        if "iv_data" in results:
            csv_file = os.path.join(self.temp_dir, f"simulation_{timestamp}_iv.csv")
            self._save_iv_csv(results["iv_data"], csv_file)
        
        # 生成摘要
        summary = self._generate_summary(result_package)
        summary_file = os.path.join(self.temp_dir, f"simulation_{timestamp}_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"\n结果已保存:")
        print(f"  报告: {json_file}")
        print(f"  摘要: {summary_file}")
        
        return json_file
    
    def _save_iv_csv(self, iv_data: List[Dict], filepath: str):
        """保存IV曲线数据到CSV"""
        if not iv_data:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # 表头
            headers = iv_data[0].keys()
            writer.writerow(headers)
            # 数据
            for row in iv_data:
                writer.writerow(row.values())
    
    def _generate_summary(self, result_package: Dict) -> str:
        """生成文本摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("DEVSIM 仿真结果摘要")
        lines.append("=" * 60)
        
        # 元信息
        meta = result_package.get("metadata", {})
        lines.append(f"\n时间戳: {meta.get('timestamp', 'N/A')}")
        lines.append(f"状态: {meta.get('status', 'N/A')}")
        
        # 配置信息
        config = result_package.get("configuration", {})
        device = config.get("device", {})
        physics = config.get("physics", {})
        
        lines.append(f"\n器件类型: {device.get('device_type', 'N/A')}")
        lines.append(f"材料: {physics.get('material', 'N/A')}")
        lines.append(f"温度: {physics.get('temperature_K', 'N/A')} K")
        lines.append(f"带隙: {physics.get('bandgap_eV', 'N/A')} eV")
        
        # 结果
        results = result_package.get("results", {})
        lines.append(f"\n收敛状态: {'✓ 成功' if results.get('convergence') else '✗ 失败'}")
        
        if "iterations" in results:
            lines.append(f"迭代次数: {len(results['iterations'])}")
        
        # 关键参数提取
        if "iv_data" in results and results["iv_data"]:
            iv = results["iv_data"]
            # 简单分析
            currents = [r.get("current", 0) for r in iv if r.get("current")]
            if currents:
                lines.append(f"\n电流范围: {min(currents):.2e} ~ {max(currents):.2e} A")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def list_simulations(self) -> List[Dict]:
        """列出所有保存的仿真"""
        simulations = []
        
        if not os.path.exists(self.temp_dir):
            return simulations
        
        for filename in os.listdir(self.temp_dir):
            if filename.endswith("_report.json"):
                filepath = os.path.join(self.temp_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        simulations.append({
                            "filename": filename,
                            "filepath": filepath,
                            "timestamp": data.get("metadata", {}).get("timestamp"),
                            "device": data.get("configuration", {}).get("device", {}).get("device_type"),
                            "status": data.get("metadata", {}).get("status")
                        })
                except:
                    pass
        
        return sorted(simulations, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def load_simulation(self, filename: str) -> Optional[Dict]:
        """加载指定仿真结果"""
        filepath = os.path.join(self.temp_dir, filename)
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def export_for_visualization(self, simulation_file: str, export_format: str = "csv") -> str:
        """
        导出数据用于可视化
        
        Returns:
            导出文件路径
        """
        data = self.load_simulation(simulation_file)
        if not data:
            return ""
        
        timestamp = data.get("metadata", {}).get("timestamp", "unknown")
        
        if export_format == "csv":
            # 导出所有数据到CSV
            export_file = os.path.join(self.temp_dir, f"viz_export_{timestamp}.csv")
            
            results = data.get("results", {})
            if "iv_data" in results:
                self._save_iv_csv(results["iv_data"], export_file)
            
            return export_file
        
        return ""
    
    def compare_with_reference(self, simulation_file: str, 
                              reference_data: Dict) -> Dict:
        """
        与参考数据对比
        
        Args:
            simulation_file: 仿真结果文件
            reference_data: 参考数据 (如从文献提取)
        
        Returns:
            对比结果
        """
        sim_data = self.load_simulation(simulation_file)
        if not sim_data:
            return {"error": "无法加载仿真数据"}
        
        comparison = {
            "simulation": simulation_file,
            "reference": reference_data.get("source", "unknown"),
            "metrics": {}
        }
        
        # 提取仿真IV数据
        sim_iv = sim_data.get("results", {}).get("iv_data", [])
        ref_iv = reference_data.get("iv_data", [])
        
        if sim_iv and ref_iv:
            # 计算误差
            errors = self._calculate_iv_error(sim_iv, ref_iv)
            comparison["metrics"]["iv_error"] = errors
        
        return comparison
    
    def _calculate_iv_error(self, sim_iv: List[Dict], ref_iv: List[Dict]) -> Dict:
        """计算IV曲线误差"""
        # 插值到相同偏置点
        # 简化版本
        return {
            "rms_error": 0.0,  # 均方根误差
            "max_error": 0.0,  # 最大误差
            "correlation": 0.0  # 相关系数
        }


# 单例
_result_manager = None

def get_result_manager(data_dir: str) -> ResultManager:
    """获取结果管理器单例"""
    global _result_manager
    if _result_manager is None:
        _result_manager = ResultManager(data_dir)
    return _result_manager
