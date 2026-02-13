"""
自适应网格生成器 - 基于物理原则的全自适应网格系统
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import json
import os
import math


@dataclass
class MeshRegion:
    """网格区域定义"""
    name: str
    start: float  # cm
    end: float    # cm
    material: str
    doping_type: str  # 'n' or 'p'
    doping_conc: float  # cm^-3
    mesh_size: float = 1e-4  # cm, 默认1um
    refinement: float = 1.0


@dataclass
class MeshConfig:
    """网格配置"""
    base_size: float = 1e-4  # 基准网格尺寸 (cm) = 1um
    regions: List[MeshRegion] = field(default_factory=list)
    contacts: List[Dict[str, Any]] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    adaptive_iterations: int = 3


class AdaptiveMeshGenerator:
    """自适应网格生成器"""
    
    def __init__(self, skill_data_dir: str):
        self.data_dir = skill_data_dir
        self.config = MeshConfig()
        self.mesh_history = []
        
    def generate_initial_mesh(self, device_spec: Dict) -> MeshConfig:
        """基于物理原则生成初始网格"""
        self.config = MeshConfig()
        
        # 1. 解析设备规格
        regions = device_spec.get("regions", [])
        total_length = sum(r.get("length", 1e-4) for r in regions)
        
        # 2. 根据物理原则分配网格尺寸
        for i, region_spec in enumerate(regions):
            region = self._create_region(region_spec, i, total_length)
            self._apply_physics_based_mesh_size(region, regions, i)
            self.config.regions.append(region)
        
        # 3. 识别界面和边界
        self._identify_interfaces_and_boundaries()
        
        # 4. 确保网格平滑过渡
        self._ensure_smooth_transition()
        
        return self.config
    
    def _create_region(self, spec: Dict, index: int, total_length: float) -> MeshRegion:
        """创建区域对象"""
        # 计算区域位置
        start_pos = sum(self.config.regions[j].end for j in range(index)) if index > 0 else 0.0
        length = spec.get("length", total_length / 2)
        
        return MeshRegion(
            name=spec.get("name", f"region_{index}"),
            start=start_pos,
            end=start_pos + length,
            material=spec.get("material", "Silicon"),
            doping_type=spec.get("doping_type", "n"),
            doping_conc=spec.get("doping_conc", 1e16)
        )
    
    def _apply_physics_based_mesh_size(self, region: MeshRegion, all_regions: List[Dict], index: int):
        """应用基于物理原则的网格尺寸"""
        length = region.end - region.start
        
        # 原则1: 薄层加密
        if length < 1e-5:  # < 0.1 um
            region.refinement = 10.0  # 至少10个节点
            region.mesh_size = length / region.refinement
            return
        
        # 原则2: 掺杂梯度区加密
        if index > 0 and index < len(all_regions):
            prev_doping = all_regions[index-1].get("doping_conc", 1e16)
            curr_doping = region.doping_conc
            if abs(math.log10(prev_doping) - math.log10(curr_doping)) > 2:
                # 掺杂变化超过2个数量级
                region.refinement = 2.0
                region.mesh_size = self.config.base_size / region.refinement
                return
        
        # 原则3: 接触区域加密
        if index == 0 or index == len(all_regions) - 1:
            region.refinement = 1.5
            region.mesh_size = self.config.base_size / region.refinement
            return
        
        # 默认: 均匀体区
        region.refinement = 1.0
        region.mesh_size = self.config.base_size
    
    def _identify_interfaces_and_boundaries(self):
        """识别界面和边界"""
        # 添加接触
        for i, region in enumerate(self.config.regions):
            if i == 0:
                self.config.contacts.append({
                    "name": f"contact_{region.name}_left",
                    "position": region.start,
                    "region": region.name,
                    "mesh_size": region.mesh_size * 0.5  # 接触处更细
                })
            if i == len(self.config.regions) - 1:
                self.config.contacts.append({
                    "name": f"contact_{region.name}_right",
                    "position": region.end,
                    "region": region.name,
                    "mesh_size": region.mesh_size * 0.5
                })
            
            # 区域间界面
            if i < len(self.config.regions) - 1:
                next_region = self.config.regions[i + 1]
                if region.material != next_region.material:
                    # 异质结 - 超细网格
                    interface_size = min(region.mesh_size, next_region.mesh_size) * 0.5
                    self.config.interfaces.append({
                        "name": f"interface_{region.name}_{next_region.name}",
                        "position": region.end,
                        "left_region": region.name,
                        "right_region": next_region.name,
                        "mesh_size": interface_size,
                        "nodes": 5  # 界面两侧各5节点
                    })
    
    def _ensure_smooth_transition(self):
        """确保网格尺寸平滑过渡"""
        # 避免相邻区域网格尺寸突变 (>2倍)
        for i in range(len(self.config.regions) - 1):
            curr_region = self.config.regions[i]
            next_region = self.config.regions[i + 1]
            
            if curr_region.mesh_size and next_region.mesh_size:
                ratio = max(curr_region.mesh_size, next_region.mesh_size) / \
                       min(curr_region.mesh_size, next_region.mesh_size)
                
                if ratio > 2.0:
                    # 调整较大的一侧
                    if curr_region.mesh_size > next_region.mesh_size:
                        curr_region.mesh_size = next_region.mesh_size * 1.5
                    else:
                        next_region.mesh_size = curr_region.mesh_size * 1.5
    
    def adaptive_refinement(self, solution_data: Dict) -> MeshConfig:
        """基于求解结果的自适应细化"""
        # 提取物理场梯度
        gradients = self._calculate_gradients(solution_data)
        
        # 标记需要细化的区域
        refine_regions = []
        for region in self.config.regions:
            region_grad = gradients.get(region.name, {})
            
            # 检查是否满足细化条件
            if self._needs_refinement(region_grad):
                refine_regions.append(region)
        
        # 应用细化
        for region in refine_regions:
            region.refinement *= 2.0  # 加密一倍
            region.mesh_size = (region.end - region.start) / max(region.refinement, 10)
        
        # 保存历史
        self.mesh_history.append({
            "iteration": len(self.mesh_history) + 1,
            "refined_regions": [r.name for r in refine_regions],
            "total_nodes": self._estimate_total_nodes()
        })
        
        return self.config
    
    def _calculate_gradients(self, solution_data: Dict) -> Dict:
        """计算物理场梯度"""
        gradients = {}
        
        for region_name, data in solution_data.get("regions", {}).items():
            grad = {
                "electric_field": data.get("max_e_field", 0),
                "carrier_gradient": data.get("max_carrier_gradient", 0),
                "potential_change": data.get("max_potential_change", 0)
            }
            gradients[region_name] = grad
        
        return gradients
    
    def _needs_refinement(self, region_grad: Dict) -> bool:
        """判断是否需要细化"""
        # 细化准则
        thresholds = {
            "electric_field": 5e4,       # V/cm (强电场)
            "carrier_gradient": 2.0,      # orders/um (载流子突变)
            "potential_change": 0.5       # V/um (势能快速变化)
        }
        
        for key, threshold in thresholds.items():
            if region_grad.get(key, 0) > threshold:
                return True
        
        return False
    
    def _estimate_total_nodes(self) -> int:
        """估计总节点数"""
        total = 0
        for region in self.config.regions:
            if region.mesh_size and region.mesh_size > 0:
                nodes = int((region.end - region.start) / region.mesh_size)
                total += max(nodes, 5)  # 至少5个节点
        return total
    
    def to_devsim_commands(self) -> List[str]:
        """生成DEVSIM网格命令"""
        commands = []
        mesh_name = "auto_mesh"
        
        commands.append(f'create_1d_mesh(mesh="{mesh_name}")')
        
        # 添加网格线
        for region in self.config.regions:
            # 起始点
            commands.append(
                f'add_1d_mesh_line(mesh="{mesh_name}", '
                f'pos={region.start}, ps={region.mesh_size}, tag="{region.name}_start")'
            )
            # 结束点
            commands.append(
                f'add_1d_mesh_line(mesh="{mesh_name}", '
                f'pos={region.end}, ps={region.mesh_size}, tag="{region.name}_end")'
            )
        
        # 添加区域
        for region in self.config.regions:
            commands.append(
                f'add_1d_region(mesh="{mesh_name}", material="{region.material}", '
                f'region="{region.name}", tag1="{region.name}_start", '
                f'tag2="{region.name}_end")'
            )
        
        # 添加接触
        for contact in self.config.contacts:
            commands.append(
                f'add_1d_contact(mesh="{mesh_name}", name="{contact["name"]}", '
                f'tag="{contact["region"]}_start", material="metal")'
            )
        
        commands.append(f'finalize_mesh(mesh="{mesh_name}")')
        commands.append(f'create_device(mesh="{mesh_name}", device="mydevice")')
        
        return commands
    
    def save_config(self, filename: str):
        """保存网格配置"""
        config_dict = {
            "base_size": self.config.base_size,
            "regions": [
                {
                    "name": r.name,
                    "start": r.start,
                    "end": r.end,
                    "material": r.material,
                    "doping_type": r.doping_type,
                    "doping_conc": r.doping_conc,
                    "mesh_size": r.mesh_size,
                    "refinement": r.refinement
                }
                for r in self.config.regions
            ],
            "contacts": self.config.contacts,
            "interfaces": self.config.interfaces,
            "history": self.mesh_history
        }
        
        filepath = os.path.join(self.data_dir, "temp", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)


# 辅助函数
def estimate_depletion_width(doping_n: float, doping_p: float, 
                             material: str = "Silicon") -> float:
    """估计耗尽层宽度"""
    # 简化的耗尽层宽度估计
    # W = sqrt(2 * epsilon * V_bi / q * (1/Nd + 1/Na))
    # 使用典型值 epsilon_r=11.7, V_bi=0.7V for Si
    
    epsilon_0 = 8.854e-14  # F/cm
    q = 1.6e-19  # C
    
    # 材料参数 (简化)
    material_params = {
        "Silicon": {"epsilon_r": 11.7, "V_bi": 0.7},
        "GaAs": {"epsilon_r": 12.9, "V_bi": 1.0},
        "HgCdTe": {"epsilon_r": 16.0, "V_bi": 0.2},  # 窄禁带
    }
    
    params = material_params.get(material, material_params["Silicon"])
    
    # 简化的耗尽层计算 (cm)
    W = math.sqrt(2 * params["epsilon_r"] * epsilon_0 * params["V_bi"] / q * 
                (1/doping_n + 1/doping_p))
    
    return W
