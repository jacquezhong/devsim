"""
意图识别引擎 - 从用户对话中提取仿真参数
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SimulationIntent:
    """仿真意图数据结构"""
    device_type: Optional[str] = None
    material: Optional[str] = None
    dimension: int = 1  # 默认1D
    temperature: Optional[float] = None
    doping_profile: Optional[Dict] = None
    simulation_type: str = "dc"  # dc, transient, ac
    bias_range: Tuple[float, float] = (0.0, 1.0)
    sweep_steps: int = 10
    missing_params: Optional[List[str]] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.doping_profile is None:
            self.doping_profile = {}
        if self.missing_params is None:
            self.missing_params = []


class InferenceEngine:
    """意图识别引擎"""
    
    # 设备类型关键词
    DEVICE_PATTERNS = {
        "diode": [r"二极管", r"diode", r"pn.?junction", r"p-n", r"PIN"],
        "mosfet": [r"mosfet", r"场效应管", r"MOS", r"FET"],
        "bjt": [r"bjt", r"晶体管", r"transistor", r"bipolar"],
        "nbn": [r"nbn", r"nBn", r"barrier"],
        "photodetector": [r"探测器", r"detector", r"photodiode"],
        "solar_cell": [r"太阳\w*电池", r"solar", r"光伏"],
    }
    
    # 材料关键词
    MATERIAL_PATTERNS = {
        "Silicon": [r"硅", r"silicon", r"Si\b"],
        "GaAs": [r"砷化镓", r"GaAs"],
        "HgCdTe": [r"碲镉汞", r"HgCdTe", r"MCT"],
        "InSb": [r"锑化铟", r"InSb"],
        "GaN": [r"氮化镓", r"GaN"],
        "SiC": [r"碳化硅", r"SiC"],
    }
    
    # 仿真类型
    SIMULATION_PATTERNS = {
        "dc": [r"IV曲线", r"IV特性", r"静态", r"dc", r"static"],
        "transient": [r"瞬态", r"transient", r"脉冲", r"时间", r"time."],
        "ac": [r"交流", r"ac", r"小信号", r"电容", r"C-V"],
    }
    
    # 分析类型
    ANALYSIS_PATTERNS = {
        "dark_current": [r"暗电流", r"dark.current"],
        "photo_response": [r"光电流", r"光响应", r"photo", r"quantum.efficiency"],
        "cv": [r"电容", r"C-V", r"capacitance"],
    }
    
    # 数值提取模式
    NUMBER_PATTERN = r"(\d+\.?\d*)\s*([a-zA-Zμµ]+)?"
    DOPING_PATTERN = r"(\d+\.?\d*)\s*[eE]?\s*(\d*)\s*(?:cm\s*[-\^]?\s*3|掺杂)"
    TEMPERATURE_PATTERN = r"(\d+)\s*[Kk°]?"
    
    def parse_user_input(self, user_input: str) -> SimulationIntent:
        """解析用户输入，返回仿真意图"""
        intent = SimulationIntent()
        text = user_input.lower()
        
        # 1. 识别设备类型
        intent.device_type = self._extract_device_type(text)
        
        # 2. 识别材料
        intent.material = self._extract_material(text)
        
        # 3. 识别维度 (检查是否有2D/3D关键词)
        intent.dimension = self._extract_dimension(text)
        
        # 4. 提取温度
        intent.temperature = self._extract_temperature(text)
        
        # 5. 提取掺杂信息
        intent.doping_profile = self._extract_doping(text)
        
        # 6. 识别仿真类型
        intent.simulation_type = self._extract_simulation_type(text)
        
        # 7. 提取偏置范围
        intent.bias_range = self._extract_bias_range(text)
        
        # 8. 检查缺失参数
        intent.missing_params = self._identify_missing_params(intent)
        
        # 9. 计算置信度
        intent.confidence = self._calculate_confidence(intent)
        
        return intent
    
    def _extract_device_type(self, text: str) -> Optional[str]:
        """提取设备类型"""
        for device, patterns in self.DEVICE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return device
        return None
    
    def _extract_material(self, text: str) -> Optional[str]:
        """提取材料类型"""
        for material, patterns in self.MATERIAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return material
        return None
    
    def _extract_dimension(self, text: str) -> int:
        """提取维度"""
        if re.search(r"\b3d\b|三维", text, re.IGNORECASE):
            return 3
        elif re.search(r"\b2d\b|二维", text, re.IGNORECASE):
            return 2
        return 1
    
    def _extract_temperature(self, text: str) -> Optional[float]:
        """提取温度"""
        # 匹配 "300K", "77 K", "温度300" 等
        patterns = [
            r"(?:温度|temperature|T=?)\s*(\d+)\s*[Kk]?",
            r"(\d+)\s*[Kk](?:温度)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_doping(self, text: str) -> Dict:
        """提取掺杂信息"""
        doping = {}
        
        # 匹配掺杂浓度 (如: 1e18, 1e16 cm^-3)
        doping_pattern = r"(n型?|p型?|n-type|p-type)?\s*(\d+\.?\d*)\s*[eE]\s*(\d+)\s*(?:cm\s*[-\^]?\s*3)?"
        matches = re.findall(doping_pattern, text, re.IGNORECASE)
        
        for i, match in enumerate(matches):
            dtype = match[0] if match[0] else ("n" if i == 0 else "p")
            base = float(match[1])
            exp = int(match[2])
            conc = base * (10 ** exp)
            
            if "n" in dtype.lower():
                doping["n_type"] = conc
            else:
                doping["p_type"] = conc
        
        return doping
    
    def _extract_simulation_type(self, text: str) -> str:
        """提取仿真类型"""
        for sim_type, patterns in self.SIMULATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return sim_type
        return "dc"
    
    def _extract_bias_range(self, text: str) -> Tuple[float, float]:
        """提取偏置范围"""
        # 匹配 "0-1V", "0到1伏", "range 0 1" 等
        patterns = [
            r"(\d+\.?\d*)\s*[-~到]\s*(\d+\.?\d*)\s*[Vv伏]?",
            r"range\s*(\d+\.?\d*)\s*(\d+\.?\d*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (float(match.group(1)), float(match.group(2)))
        return (0.0, 1.0)
    
    def _identify_missing_params(self, intent: SimulationIntent) -> List[str]:
        """识别缺失的关键参数"""
        missing = []
        
        if not intent.device_type:
            missing.append("device_type")
        
        if not intent.material:
            missing.append("material")
        
        if intent.temperature is None:
            missing.append("temperature")
        
        if not intent.doping_profile:
            missing.append("doping")
        
        if intent.dimension > 1:
            missing.append("2D/3D not supported yet")
        
        return missing
    
    def _calculate_confidence(self, intent: SimulationIntent) -> float:
        """计算意图识别置信度"""
        score = 0.0
        total = 4  # device, material, temp, doping
        
        if intent.device_type:
            score += 1
        if intent.material:
            score += 1
        if intent.temperature is not None:
            score += 1
        if intent.doping_profile:
            score += 1
            
        return score / total
    
    def generate_prompt_for_missing(self, intent: SimulationIntent) -> str:
        """为缺失参数生成询问提示"""
        prompts = []
        missing = intent.missing_params or []
        
        if "device_type" in missing:
            prompts.append("1. 器件类型? (二极管/MOSFET/探测器等)")
        
        if "material" in missing:
            prompts.append("2. 材料类型? (硅/GaAs/HgCdTe等)")
        
        if "temperature" in missing:
            # 根据材料建议默认值
            if intent.material in ["HgCdTe", "InSb"]:
                prompts.append("3. 温度? [默认: 77K] (窄禁带材料)")
            else:
                prompts.append("3. 温度? [默认: 300K]")
        
        if "doping" in missing:
            prompts.append("4. 掺杂浓度? (如: n型1e18, p型1e16 cm^-3)")
        
        if "2D/3D not supported yet" in missing:
            prompts.append("\n注意: 当前仅支持1D仿真")
        
        return "检测到需要更多信息:\n" + "\n".join(prompts)


# 单例模式
_inference_engine = None

def get_inference_engine() -> InferenceEngine:
    """获取意图识别引擎单例"""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = InferenceEngine()
    return _inference_engine
