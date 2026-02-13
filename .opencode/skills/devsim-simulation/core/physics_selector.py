"""
物理模型选择器 - 基于材料和器件类型自适应选择物理模型
"""
from typing import Dict, List, Optional, Any
import os
import yaml


class PhysicsSelector:
    """物理模型选择器"""
    
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = knowledge_dir
        self.materials_db = {}
        self.physics_rules = {}
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        # 加载材料参数
        materials_file = os.path.join(self.knowledge_dir, "materials.yaml")
        if os.path.exists(materials_file):
            with open(materials_file, 'r') as f:
                self.materials_db = yaml.safe_load(f).get("materials", {})
        
        # 加载物理规则
        physics_file = os.path.join(self.knowledge_dir, "physics_principles.yaml")
        if os.path.exists(physics_file):
            with open(physics_file, 'r') as f:
                self.physics_rules = yaml.safe_load(f).get("physics_models", {})
    
    def select_physics_models(self, material: str, device_type: str,
                             temperature: float, simulation_type: str = "dc") -> Dict[str, Any]:
        """为给定配置选择物理模型"""
        
        # 获取材料参数
        mat_params = self.materials_db.get(material, {})
        bandgap = self._get_bandgap(material, temperature)
        
        # 基础模型 (所有器件都需要)
        models = {
            "Poisson": {"required": True, "auto_setup": True},
            "DriftDiffusion": {"required": True, "discretization": "Scharfetter_Gummel"}
        }
        
        # 根据带隙选择复合模型
        if bandgap < 0.5:  # 窄禁带
            models["Auger_Recombination"] = {
                "required": True,
                "reason": "窄禁带材料Auger复合占主导",
                "parameters": mat_params.get("auger_coefficients", {})
            }
            models["SRH_Recombination"] = {
                "required": True,
                "reason": "缺陷辅助复合"
            }
            models["Fermi_Dirac_Statistics"] = {
                "required": True,
                "reason": "简并统计"
            }
        elif bandgap > 2.0:  # 宽禁带
            models["SRH_Recombination"] = {
                "required": True,
                "reason": "缺陷复合为主"
            }
            models["Radiative_Recombination"] = {
                "required": False,
                "reason": "辐射复合"
            }
        else:  # 中等带隙
            models["SRH_Recombination"] = {
                "required": True,
                "reason": "主要复合机制"
            }
        
        # 根据仿真类型添加模型
        if simulation_type == "ac":
            models["Displacement_Current"] = {
                "required": True,
                "reason": "高频分析需要"
            }
        
        if simulation_type == "transient":
            models["Carrier_Dynamics"] = {
                "required": True,
                "reason": "时间依赖分析"
            }
        
        # 器件特定模型
        if device_type in ["photodetector", "solar_cell", "nbn"]:
            models["Optical_Generation"] = {
                "required": True,
                "reason": "光生载流子",
                "parameters": {"spectrum": "AM1.5G"}  # 默认光谱
            }
            models["Quantum_Efficiency"] = {
                "required": False,
                "reason": "量子效率计算"
            }
        
        # 迁移率模型
        models["Mobility"] = self._select_mobility_model(material, device_type)
        
        return {
            "material": material,
            "bandgap_eV": bandgap,
            "temperature_K": temperature,
            "device_type": device_type,
            "simulation_type": simulation_type,
            "models": models
        }
    
    def _get_bandgap(self, material: str, temperature: float) -> float:
        """计算材料在指定温度下的带隙"""
        mat_params = self.materials_db.get(material, {})
        
        # 带隙公式或查表
        bandgap_info = mat_params.get("bandgap", {})
        
        if isinstance(bandgap_info, dict):
            # 温度依赖公式
            formula = bandgap_info.get("formula")
            if formula and material == "HgCdTe":
                # HgCdTe特殊处理 (需要x组分)
                x = bandgap_info.get("x_default", 0.3)
                # Eg = -0.302 + 1.93*x - 0.81*x^2 + 0.832*x^3 + 5.35e-4*(1-2*x)*T
                T = temperature
                Eg = (-0.302 + 1.93*x - 0.81*x**2 + 0.832*x**3 + 
                      5.35e-4*(1-2*x)*T)
                return max(Eg, 0.01)  # 最小0.01eV
            else:
                # Varshini公式: Eg(T) = Eg(0) - alpha*T^2/(T+beta)
                Eg_0 = bandgap_info.get("Eg_0", 1.12)  # 默认硅
                alpha = bandgap_info.get("alpha", 4.73e-4)
                beta = bandgap_info.get("beta", 636)
                return Eg_0 - alpha * temperature**2 / (temperature + beta)
        else:
            # 直接数值 (假设300K值)
            return float(bandgap_info) if bandgap_info else 1.12
    
    def _select_mobility_model(self, material: str, device_type: str) -> Dict:
        """选择迁移率模型"""
        # 基础模型
        mobility = {
            "model": "constant",
            "electron_mobility": 1000,  # cm^2/Vs
            "hole_mobility": 500        # cm^2/Vs
        }
        
        # 材料特定
        if material in self.materials_db:
            mat_params = self.materials_db[material]
            mob_params = mat_params.get("mobility", {})
            
            if mob_params:
                # 使用材料特定参数
                mobility["electron_mobility"] = mob_params.get("electrons", {}).get("mu_max", 1000)
                mobility["hole_mobility"] = mob_params.get("holes", {}).get("mu_max", 500)
                
                # 模型选择
                if "Klaassen" in str(mob_params):
                    mobility["model"] = "Klaassen"
                elif "Canali" in str(mob_params):
                    mobility["model"] = "Canali"
        
        # 器件特定调整
        if device_type in ["mosfet", "fet"]:
            mobility["field_dependent"] = True
            mobility["model"] = "Lombardi"  # 或类似模型
        
        return mobility
    
    def get_model_equations(self, model_name: str) -> Dict[str, str]:
        """获取模型方程"""
        equations = {
            "Poisson": {
                "equation": "epsilon * div(grad(Potential)) + q*(p - n + Nd - Na) = 0",
                "variables": ["Potential"]
            },
            "DriftDiffusion_Electron": {
                "equation": "dn/dt = div(Jn) - R + G",
                "flux": "Jn = q*n*mu_n*E + q*Dn*grad(n)",
                "variables": ["Electrons"]
            },
            "DriftDiffusion_Hole": {
                "equation": "dp/dt = -div(Jp) - R + G",
                "flux": "Jp = q*p*mu_p*E - q*Dp*grad(p)",
                "variables": ["Holes"]
            },
            "SRH_Recombination": {
                "equation": "R_SRH = (n*p - ni^2) / (tau_p*(n+n1) + tau_n*(p+p1))",
                "parameters": ["tau_n", "tau_p"]
            },
            "Auger_Recombination": {
                "equation": "R_Auger = (Cp*n + Cn*p) * (n*p - ni^2)",
                "parameters": ["Cn", "Cp"]
            },
            "Fermi_Dirac_Statistics": {
                "description": "使用Fermi-Dirac统计代替Boltzmann近似",
                "applicable": "n > 1e18 or p > 1e18"
            }
        }
        return equations.get(model_name, {})
    
    def validate_model_combination(self, selected_models: List[str]) -> tuple:
        """验证模型组合的有效性"""
        warnings = []
        errors = []
        
        # 检查必需组合
        if "Auger_Recombination" in selected_models and "Fermi_Dirac_Statistics" not in selected_models:
            warnings.append("窄禁带材料建议启用Fermi-Dirac统计")
        
        if "Optical_Generation" in selected_models and "DriftDiffusion" not in selected_models:
            errors.append("光生载流子需要漂移-扩散模型")
        
        return (len(errors) == 0, errors, warnings)
    
    def generate_devsim_setup(self, physics_config: Dict) -> List[str]:
        """生成DEVSIM设置命令"""
        commands = []
        device = physics_config.get("device", "mydevice")
        region = physics_config.get("region", "bulk")
        
        models = physics_config.get("models", {})
        
        # 基础设置
        commands.append(f"# 物理模型设置 for {physics_config.get('material', 'Silicon')}")
        commands.append(f"# 温度: {physics_config.get('temperature_K', 300)}K")
        commands.append(f"# 带隙: {physics_config.get('bandgap_eV', 1.12)}eV")
        
        # Poisson方程
        if "Poisson" in models:
            commands.append(f"\n# Poisson方程")
            commands.append(f"CreateSolution(device, region, 'Potential')")
            # 这里应该调用simple_physics或自定义函数
        
        # 漂移扩散
        if "DriftDiffusion" in models:
            commands.append(f"\n# 漂移-扩散方程")
            commands.append(f"CreateSolution(device, region, 'Electrons')")
            commands.append(f"CreateSolution(device, region, 'Holes')")
        
        # 复合模型
        if "SRH_Recombination" in models:
            commands.append(f"\n# SRH复合")
            commands.append(f"# tau_n, tau_p 需要设置")
        
        if "Auger_Recombination" in models:
            commands.append(f"\n# Auger复合 (窄禁带)")
            commands.append(f"# Cn, Cp 需要设置")
        
        return commands


# 单例
_physics_selector = None

def get_physics_selector(knowledge_dir: str) -> PhysicsSelector:
    """获取物理模型选择器单例"""
    global _physics_selector
    if _physics_selector is None:
        _physics_selector = PhysicsSelector(knowledge_dir)
    return _physics_selector
