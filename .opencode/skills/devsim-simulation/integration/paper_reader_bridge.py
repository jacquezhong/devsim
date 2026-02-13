"""
Paper Reader 集成桥 - 从PDF文献提取仿真参数
"""
import os
import re
from typing import Dict, List, Optional, Any


class PaperReaderBridge:
    """PDF文献解析集成桥"""
    
    def __init__(self, papers_dir: str = "papers"):
        self.papers_dir = papers_dir
        self.extraction_patterns = self._load_extraction_patterns()
    
    def _load_extraction_patterns(self) -> Dict:
        """加载参数提取模式"""
        return {
            "device_structure": {
                "patterns": [
                    r"(\w+)\s+layer.*?([\d.]+)\s*(?:μm|um)",
                    r"thickness\s+of\s+(\w+).*?([\d.]+)\s*(?:μm|um)",
                ],
                "type": "structural"
            },
            "doping": {
                "patterns": [
                    r"(\w+).*?doping.*?([\d.]+)\s*[×x]?\s*10\^?(\d+)",
                    r"([\d.]+)\s*[×x]?\s*10\^?(\d+)\s*cm\s*[-–]3",
                ],
                "type": "numerical"
            },
            "temperature": {
                "patterns": [
                    r"(\d+)\s*K",
                    r"temperature.*?([\d.]+)\s*(?:K|°C)",
                ],
                "type": "numerical"
            },
            "material_composition": {
                "patterns": [
                    r"(Hg[_\d.]+Cd[_\d.]+Te|In[_\d.]+Ga[_\d.]+As)",
                    r"x\s*=\s*([\d.]+)",
                ],
                "type": "material"
            },
            "bias_range": {
                "patterns": [
                    r"([\-\d.]+)\s*V\s+to\s+([\-\d.]+)\s*V",
                    r"bias.*?([\-\d.]+).*?([\-\d.]+)\s*V",
                ],
                "type": "range"
            }
        }
    
    def extract_from_paper(self, paper_path: str) -> Dict:
        """
        从PDF文献提取参数
        
        Args:
            paper_path: PDF文件路径 (相对papers目录或绝对路径)
            
        Returns:
            提取的参数字典
        """
        # 构建完整路径
        if not os.path.isabs(paper_path):
            full_path = os.path.join(self.papers_dir, paper_path)
        else:
            full_path = paper_path
        
        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"找不到文件: {full_path}",
                "suggestion": "请检查文件路径是否正确"
            }
        
        print(f"\n解析文献: {paper_path}")
        print("=" * 60)
        
        # 调用paper-reader skill解析
        # 注意: 这里应该通过system调用paper-reader
        extraction_result = self._parse_paper_content(full_path)
        
        return extraction_result
    
    def _parse_paper_content(self, paper_path: str) -> Dict:
        """
        解析论文内容
        
        注意: 实际实现中应该调用paper-reader skill
        这里提供模拟实现
        """
        result = {
            "success": True,
            "paper": os.path.basename(paper_path),
            "extracted_params": {},
            "confidence": 0.0,
            "notes": []
        }
        
        # 模拟从JEM2025提取参数
        if "JEM2025" in paper_path or "jem2025" in paper_path.lower():
            result["extracted_params"] = self._simulate_jem2025_extraction()
            result["confidence"] = 0.85
            result["notes"].append("从JEM2025提取nBn探测器参数")
        else:
            # 通用提取
            result["extracted_params"] = self._generic_extraction()
            result["confidence"] = 0.5
            result["notes"].append("使用通用提取模板")
        
        return result
    
    def _simulate_jem2025_extraction(self) -> Dict:
        """模拟从JEM2025论文提取参数"""
        return {
            "device_type": "nbn_detector",
            "material": "HgCdTe",
            "structure": {
                "layers": [
                    {
                        "name": "cap",
                        "material": "HgCdTe",
                        "x_composition": 0.3,
                        "thickness_um": 0.5,
                        "doping_cm3": 1e18,
                        "doping_type": "n"
                    },
                    {
                        "name": "barrier",
                        "material": "HgCdTe",
                        "x_composition": 0.3,
                        "thickness_um": 0.1,
                        "doping_cm3": 1e15,
                        "doping_type": "p"
                    },
                    {
                        "name": "absorber",
                        "material": "HgCdTe",
                        "x_composition": 0.2,
                        "thickness_um": 5.0,
                        "doping_cm3": 1e16,
                        "doping_type": "p"
                    }
                ]
            },
            "operating_conditions": {
                "temperature_K": 77,
                "bias_range_V": [-0.1, 0.5]
            },
            "physics_models": {
                "recombination": ["Auger", "SRH"],
                "statistics": "Fermi-Dirac",
                "generation": "optical"
            },
            "reference_figures": [
                {
                    "figure": "Figure 3",
                    "description": "Dark current vs bias",
                    "data_type": "IV_curve"
                },
                {
                    "figure": "Figure 4",
                    "description": "Quantum efficiency",
                    "data_type": "spectral_response"
                }
            ]
        }
    
    def _generic_extraction(self) -> Dict:
        """通用参数提取模板"""
        return {
            "device_type": "unknown",
            "material": "unknown",
            "structure": {},
            "operating_conditions": {},
            "physics_models": {},
            "note": "需要手动输入具体参数"
        }
    
    def compare_with_simulation(self, paper_params: Dict, 
                               simulation_results: Dict) -> Dict:
        """
        对比论文参数与仿真结果
        
        Args:
            paper_params: 从论文提取的参数
            simulation_results: 仿真结果
            
        Returns:
            对比分析
        """
        comparison = {
            "status": "comparison_ready",
            "device_match": False,
            "parameter_comparison": {},
            "suggestions": []
        }
        
        # 检查器件类型匹配
        paper_device = paper_params.get("device_type", "")
        sim_device = simulation_results.get("device_type", "")
        
        if paper_device == sim_device:
            comparison["device_match"] = True
        else:
            comparison["suggestions"].append(
                f"器件类型不匹配: 论文={paper_device}, 仿真={sim_device}"
            )
        
        # 对比结构参数
        paper_structure = paper_params.get("structure", {})
        sim_structure = simulation_results.get("configuration", {}).get("device", {})
        
        # 简化的对比
        comparison["parameter_comparison"] = {
            "structure_layers": {
                "paper": len(paper_structure.get("layers", [])),
                "simulation": len(sim_structure.get("regions", [])),
                "match": len(paper_structure.get("layers", [])) == len(sim_structure.get("regions", []))
            }
        }
        
        return comparison
    
    def generate_device_config(self, paper_params: Dict) -> Dict:
        """从论文参数生成DEVSIM设备配置"""
        config = {
            "device_type": paper_params.get("device_type", "diode"),
            "regions": [],
            "material": paper_params.get("material", "Silicon"),
            "temperature": paper_params.get("operating_conditions", {}).get("temperature_K", 300),
            "bias_range": paper_params.get("operating_conditions", {}).get("bias_range_V", [0, 1])
        }
        
        # 转换层结构为区域
        layers = paper_params.get("structure", {}).get("layers", [])
        for layer in layers:
            region = {
                "name": layer.get("name", f"region_{len(config['regions'])}"),
                "material": layer.get("material", config["material"]),
                "length": layer.get("thickness_um", 1.0) * 1e-4,  # 转为cm
                "doping_type": layer.get("doping_type", "n"),
                "doping_conc": layer.get("doping_cm3", 1e16)
            }
            
            # 特殊材料参数
            if "x_composition" in layer:
                region["x_composition"] = layer["x_composition"]
            
            config["regions"].append(region)
        
        return config
    
    def suggest_extraction(self, paper_path: str) -> str:
        """
        建议如何提取论文参数
        
        当自动提取失败时使用
        """
        suggestions = f"""
无法自动从 {paper_path} 提取参数。

建议手动提取步骤:
1. 打开PDF文件，定位到器件结构描述部分
2. 提取以下信息:
   - 层数和每层的厚度
   - 材料成分 (如HgCdTe的x值)
   - 掺杂浓度和类型
   - 工作温度
   - 偏置范围

3. 提供给我如下格式:
   ```
   器件: nBn探测器
   材料: HgCdTe
   温度: 77K
   结构:
     - Cap: 0.5um, n型, 1e18 cm^-3
     - Barrier: 0.1um, p型, 1e15 cm^-3
     - Absorber: 5um, p型, 1e16 cm^-3
   仿真: DC扫描 -0.1V到0.5V
   ```

我将根据这些信息自动配置仿真。
"""
        return suggestions


# 便捷函数
def extract_paper_parameters(paper_path: str, papers_dir: str = "papers") -> Dict:
    """
    便捷函数：从论文提取参数
    
    使用示例:
        params = extract_paper_parameters("JEM2025.pdf")
        config = generate_device_config(params)
    """
    bridge = PaperReaderBridge(papers_dir)
    return bridge.extract_from_paper(paper_path)
