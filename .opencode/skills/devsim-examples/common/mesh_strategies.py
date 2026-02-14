"""
DEVSIM 智能网格策略模块

此模块将 devsim-simulation skill 中的物理驱动网格原则具体化，
供 devsim-examples 在创建网格时自动调用。

设计目标：
1. 集中管理网格创建原则
2. 根据物理参数自动计算最优网格密度
3. 支持未来添加更详细的原则
4. 保持与 devsim-examples 的解耦
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable
import math


@dataclass
class MeshRegion:
    """网格区域定义"""
    name: str
    position: float  # 中心位置 (cm)
    min_spacing: float  # 最小网格间距 (cm)
    max_spacing: float  # 最大网格间距 (cm)
    priority: int = 1  # 优先级（越高越优先加密）


@dataclass
class PhysicalParameters:
    """物理参数"""
    # 掺杂参数
    doping_gradient: float = 0.0  # 掺杂梯度 (orders/μm)
    max_doping: float = 1e18  # 最大掺杂 (cm^-3)
    min_doping: float = 1e15  # 最小掺杂 (cm^-3)
    
    # 几何参数
    feature_size: float = 1e-4  # 特征尺寸 (cm)
    layer_thickness: float = 1e-4  # 层厚度 (cm)
    
    # 电场参数
    expected_field: float = 0.0  # 预期电场 (V/μm)
    breakdown_field: float = 10.0  # 击穿电场 (V/μm)
    
    # 电压参数
    max_voltage: float = 1.0  # 最大偏置 (V)
    
    # 温度
    temperature: float = 300.0  # 温度 (K)


class MeshPolicy:
    """
    网格策略基类
    
    定义网格创建的物理原则，可根据不同器件类型扩展
    """
    
    # 来自 devsim-simulation skill 的原则
    DEFAULT_PRINCIPLES = {
        # 高梯度区原则
        'high_gradient_threshold': 0.5,  # E-field > 0.5V/μm 或 dn/dx > 2 orders/μm
        'gradient_mesh_factor': 0.1,  # 高梯度区网格密度因子
        
        # 边界原则
        'boundary_refinement': True,
        'boundary_layers': 3,  # 边界附近加密层数
        'boundary_factor': 0.2,  # 边界网格相对于体区的比例
        
        # 特征尺寸原则
        'min_nodes_per_layer': 10,  # 薄层至少10个节点
        'layer_thickness_threshold': 0.1e-4,  # < 0.1μm 视为薄层 (cm)
        
        # 默认网格密度 (cm)
        'default_mesh_density': 1e-7,  # 0.1 μm
        'min_mesh_spacing': 1e-9,  # 0.01 nm (物理极限)
        'max_mesh_spacing': 1e-4,  # 1 μm
    }
    
    def __init__(self, principles: Optional[Dict] = None):
        """
        初始化网格策略
        
        参数:
            principles: 自定义原则字典，覆盖默认值
        """
        self.principles = self.DEFAULT_PRINCIPLES.copy()
        if principles:
            self.principles.update(principles)
    
    def calculate_mesh_density(self, region: MeshRegion, 
                               physics: PhysicalParameters) -> float:
        """
        计算最优网格密度
        
        基于物理参数和区域特性计算建议的网格间距
        
        参数:
            region: 网格区域定义
            physics: 物理参数
        
        返回:
            float: 建议网格间距 (cm)
        """
        # 基础网格密度
        spacing = region.max_spacing
        
        # 1. 高掺杂梯度区加密
        if physics.doping_gradient > self.principles['high_gradient_threshold']:
            gradient_spacing = region.min_spacing / physics.doping_gradient
            spacing = min(spacing, gradient_spacing)
        
        # 2. 薄层加密
        if physics.layer_thickness < self.principles['layer_thickness_threshold']:
            # 至少 min_nodes_per_layer 个节点
            thin_layer_spacing = physics.layer_thickness / self.principles['min_nodes_per_layer']
            spacing = min(spacing, thin_layer_spacing)
        
        # 3. 高电场区加密
        if physics.expected_field > self.principles['high_gradient_threshold']:
            field_spacing = region.min_spacing * (self.principles['breakdown_field'] / physics.expected_field)
            spacing = min(spacing, field_spacing)
        
        # 4. 边界加密
        if self.principles['boundary_refinement'] and region.priority > 1:
            boundary_spacing = region.min_spacing * self.principles['boundary_factor']
            spacing = min(spacing, boundary_spacing)
        
        # 确保在有效范围内
        spacing = max(spacing, self.principles['min_mesh_spacing'])
        spacing = min(spacing, self.principles['max_mesh_spacing'])
        
        return spacing
    
    def get_mesh_regions_1d_diode(self, physics: PhysicalParameters,
                                   device_length: float = 1e-5,
                                   junction_position: float = 0.5e-5) -> List[MeshRegion]:
        """
        获取1D二极管的网格区域划分
        
        参数:
            physics: 物理参数
            device_length: 器件长度 (cm)
            junction_position: 结位置 (cm)
        
        返回:
            List[MeshRegion]: 网格区域列表
        """
        regions = []
        
        # 左接触区
        regions.append(MeshRegion(
            name="left_contact",
            position=0,
            min_spacing=1e-7,
            max_spacing=1e-6,
            priority=2
        ))
        
        # 结区（最高优先级）
        junction_width = self.estimate_junction_width(physics)
        regions.append(MeshRegion(
            name="junction",
            position=junction_position,
            min_spacing=self.principles['min_mesh_spacing'],
            max_spacing=junction_width / 5,  # 结区至少5个节点
            priority=3
        ))
        
        # 右接触区
        regions.append(MeshRegion(
            name="right_contact",
            position=device_length,
            min_spacing=1e-7,
            max_spacing=1e-6,
            priority=2
        ))
        
        return regions
    
    def estimate_junction_width(self, physics: PhysicalParameters) -> float:
        """
        估算PN结耗尽层宽度
        
        使用突变结近似:
        W = sqrt(2*εs*Vbi/q * (Na+Nd)/(Na*Nd))
        
        参数:
            physics: 物理参数
        
        返回:
            float: 耗尽层宽度 (cm)
        """
        # 简化估算：基于掺杂浓度
        # W ~ 1/sqrt(N) for one-sided junction
        eps_si = 11.7 * 8.85e-14  # F/cm
        q = 1.6e-19  # C
        
        # 使用平均掺杂
        avg_doping = math.sqrt(physics.max_doping * physics.min_doping)
        
        # 内建电势 (简化)
        vt = 0.026  # 热电压 @ 300K (V)
        vbi = vt * math.log(physics.max_doping / physics.min_doping)
        
        # 耗尽层宽度
        w = math.sqrt(2 * eps_si * vbi / (q * avg_doping))
        
        return max(w, 1e-7)  # 最小 1nm
    
    def get_mesh_regions_2d_diode(self, physics: PhysicalParameters,
                                   device_width: float = 1e-5,
                                   device_height: float = 1e-5,
                                   junction_x: float = 0.5e-5) -> Dict[str, List[MeshRegion]]:
        """
        获取2D二极管的网格区域划分
        
        返回:
            Dict: {'x': [...], 'y': [...]}
        """
        # X方向（类似1D）
        x_regions = self.get_mesh_regions_1d_diode(
            physics, device_width, junction_x
        )
        
        # Y方向（均匀分布）
        y_regions = [
            MeshRegion(
                name="bottom",
                position=0,
                min_spacing=1e-6,
                max_spacing=1e-5,
                priority=1
            ),
            MeshRegion(
                name="top",
                position=device_height,
                min_spacing=1e-6,
                max_spacing=1e-5,
                priority=1
            ),
        ]
        
        return {'x': x_regions, 'y': y_regions}


class DiodeMeshStrategy:
    """
    二极管专用网格策略
    
    封装了创建1D/2D二极管网格的智能逻辑
    """
    
    def __init__(self, policy: Optional[MeshPolicy] = None):
        self.policy = policy or MeshPolicy()
    
    def create_1d_mesh_params(self, p_doping: float = 1e18,
                              n_doping: float = 1e18,
                              temperature: float = 300,
                              device_length: float = 1e-5,
                              junction_position: float = 0.5e-5,
                              max_voltage: float = 0.5) -> Dict:
        """
        生成1D二极管的最优网格参数
        
        返回的字典可直接传递给 diode_1d.py 的 create_diode_mesh
        
        参数:
            p_doping: p区掺杂 (cm^-3)
            n_doping: n区掺杂 (cm^-3)
            temperature: 温度 (K)
            device_length: 器件长度 (cm)
            junction_position: 结位置 (cm)
            max_voltage: 最大偏置 (V)
        
        返回:
            Dict: {
                'device_length': ...,
                'junction_position': ...,
                'mesh_density': ...,  # 结区网格密度
            }
        """
        # 计算物理参数
        physics = PhysicalParameters(
            doping_gradient=abs(math.log10(p_doping) - math.log10(n_doping)),
            max_doping=max(p_doping, n_doping),
            min_doping=min(p_doping, n_doping),
            max_voltage=max_voltage,
            temperature=temperature,
        )
        
        # 获取网格区域
        regions = self.policy.get_mesh_regions_1d_diode(
            physics, device_length, junction_position
        )
        
        # 找到结区的网格密度
        junction_region = next(r for r in regions if r.name == "junction")
        mesh_density = self.policy.calculate_mesh_density(junction_region, physics)
        
        return {
            'device_length': device_length,
            'junction_position': junction_position,
            'mesh_density': mesh_density,
            '_mesh_regions': regions,  # 用于调试
            '_physics': physics,  # 用于调试
        }
    
    def create_2d_mesh_params(self, p_doping: float = 1e18,
                              n_doping: float = 1e18,
                              temperature: float = 300,
                              device_width: float = 1e-5,
                              device_height: float = 1e-5,
                              junction_x: float = 0.5e-5,
                              max_voltage: float = 0.5) -> Dict:
        """
        生成2D二极管的最优网格参数
        
        返回:
            Dict: 可直接传递给 diode_2d.py 的 create_diode_2d_mesh
        """
        physics = PhysicalParameters(
            doping_gradient=abs(math.log10(p_doping) - math.log10(n_doping)),
            max_doping=max(p_doping, n_doping),
            min_doping=min(p_doping, n_doping),
            max_voltage=max_voltage,
            temperature=temperature,
        )
        
        regions = self.policy.get_mesh_regions_2d_diode(
            physics, device_width, device_height, junction_x
        )
        
        # X方向（结区）网格密度
        junction_region = next(r for r in regions['x'] if r.name == "junction")
        mesh_density_x = self.policy.calculate_mesh_density(junction_region, physics)
        
        # Y方向（均匀）
        mesh_density_y = 1e-6  # 默认0.1μm
        
        return {
            'device_width': device_width,
            'device_height': device_height,
            'junction_x': junction_x,
            'mesh_density': mesh_density_x,
            '_mesh_regions': regions,
            '_physics': physics,
        }


# 便捷函数
def get_intelligent_mesh_params(capability: str, **kwargs) -> Dict:
    """
    根据能力标识获取智能网格参数
    
    这是 devsim-simulation 和 devsim-examples 之间的桥梁函数
    
    参数:
        capability: 能力标识，如 "diode_1d_dc_iv", "diode_2d_dc_iv"
        **kwargs: 物理参数（掺杂、温度、电压等）
    
    返回:
        Dict: 最优网格参数字典
    
    示例:
        >>> params = get_intelligent_mesh_params(
        ...     "diode_1d_dc_iv",
        ...     p_doping=1e18,
        ...     n_doping=1e16,
        ...     temperature=300
        ... )
        >>> result = run_diode_1d_simulation(**params)
    """
    policy = MeshPolicy()
    
    if capability in ('diode_1d_dc_iv', 'diode_1d_transient', 'diode_1d_ssac_cv'):
        strategy = DiodeMeshStrategy(policy)
        return strategy.create_1d_mesh_params(**kwargs)
    
    elif capability == 'diode_2d_dc_iv':
        strategy = DiodeMeshStrategy(policy)
        return strategy.create_2d_mesh_params(**kwargs)
    
    else:
        # 默认：返回基本网格参数
        return {
            'mesh_density': policy.principles['default_mesh_density'],
            'warning': f'No intelligent mesh strategy for {capability}, using default'
        }


# 扩展点：添加新原则
def register_mesh_principle(principle_name: str, value):
    """
    注册新的网格原则
    
    用于 devsim-simulation 动态添加更详细的原则
    
    示例:
        >>> register_mesh_principle('quantum_refinement', True)
        >>> register_mesh_principle('quantum_spacing', 1e-10)
    """
    MeshPolicy.DEFAULT_PRINCIPLES[principle_name] = value


def register_capability_strategy(capability: str, 
                                 strategy_func: Callable):
    """
    为新的能力标识注册网格策略
    
    示例:
        >>> def my_mos_strategy(**kwargs):
        ...     return {'mesh_density': 1e-8}
        >>> register_capability_strategy('mos_2d_custom', my_mos_strategy)
    """
    _CAPABILITY_STRATEGIES[capability] = strategy_func


_CAPABILITY_STRATEGIES = {}
