"""
网络学习模块 - 搜索最新材料参数和最佳实践
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class WebLearner:
    """网络学习器 - 获取最新材料参数"""
    
    def __init__(self, data_dir: str, cache_duration_days: int = 30):
        self.data_dir = data_dir
        self.cache_dir = os.path.join(data_dir, "material_cache")
        self.cache_duration = timedelta(days=cache_duration_days)
        
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_material_parameters(self, material: str, force_refresh: bool = False) -> Dict:
        """
        获取材料参数（优先缓存，必要时网络搜索）
        
        Args:
            material: 材料名称
            force_refresh: 强制刷新缓存
            
        Returns:
            材料参数字典
        """
        cache_file = os.path.join(self.cache_dir, f"{material.lower()}.json")
        
        # 检查缓存
        if not force_refresh and os.path.exists(cache_file):
            cache_age = self._get_cache_age(cache_file)
            if cache_age < self.cache_duration:
                print(f"  使用缓存参数: {material}")
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        # 网络搜索最新参数
        print(f"  搜索最新参数: {material}...")
        params = self._search_material_online(material)
        
        # 保存缓存
        if params:
            self._save_cache(cache_file, params)
        
        return params
    
    def _get_cache_age(self, cache_file: str) -> timedelta:
        """获取缓存文件年龄"""
        mtime = os.path.getmtime(cache_file)
        cache_time = datetime.fromtimestamp(mtime)
        return datetime.now() - cache_time
    
    def _save_cache(self, cache_file: str, params: Dict):
        """保存参数缓存"""
        cache_data = {
            "material": params.get("name", "unknown"),
            "cached_at": datetime.now().isoformat(),
            "parameters": params
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"  参数已缓存: {cache_file}")
    
    def _search_material_online(self, material: str) -> Dict:
        """
        搜索材料参数
        
        注意: 这里模拟网络搜索，实际实现应调用websearch工具
        """
        # 模拟搜索结果 - 实际应使用websearch工具
        search_query = f"{material} material parameters TCAD bandgap mobility"
        
        # 预定义的材料数据库（作为fallback）
        known_materials = {
            "Silicon": {
                "name": "Silicon",
                "bandgap": {"Eg_0": 1.17, "alpha": 4.73e-4, "beta": 636},
                "permittivity": 11.7,
                "affinity": 4.05,
                "mobility": {
                    "electrons": {"mu_min": 52.2, "mu_max": 1360, "alpha": 2.3},
                    "holes": {"mu_min": 44.9, "mu_max": 462, "alpha": 2.2}
                }
            },
            "GaAs": {
                "name": "GaAs",
                "bandgap": {"Eg_0": 1.519, "alpha": 5.41e-4, "beta": 204},
                "permittivity": 12.9,
                "affinity": 4.07,
                "mobility": {
                    "electrons": {"mu_min": 800, "mu_max": 8000},
                    "holes": {"mu_min": 100, "mu_max": 400}
                }
            },
            "HgCdTe": {
                "name": "HgCdTe",
                "bandgap": {
                    "formula": "-0.302 + 1.93*x - 0.81*x^2 + 0.832*x^3 + 5.35e-4*(1-2*x)*T",
                    "x_default": 0.3,
                    "temperature_dependent": True
                },
                "permittivity": 16.0,
                "auger_coefficients": {
                    "Cn_formula": "9.0e-30 * exp(-0.46*q/(k*T))",
                    "Cp_formula": "6.0e-30 * exp(-0.23*q/(k*T))"
                }
            }
        }
        
        # 返回已知材料或通用模板
        if material in known_materials:
            print(f"  ✓ 找到参数: {material}")
            return known_materials[material]
        else:
            print(f"  ! 未找到特定参数，使用通用模板")
            return self._generate_generic_template(material)
    
    def _generate_generic_template(self, material: str) -> Dict:
        """生成通用材料模板"""
        return {
            "name": material,
            "bandgap": {"Eg_0": 1.0, "alpha": 5e-4, "beta": 500},
            "permittivity": 10.0,
            "mobility": {
                "electrons": {"mu_min": 100, "mu_max": 1000},
                "holes": {"mu_min": 50, "mu_max": 500}
            },
            "note": "通用模板参数，建议根据文献校准"
        }
    
    def search_best_practices(self, device_type: str) -> List[str]:
        """搜索器件类型的最佳实践"""
        print(f"  搜索 {device_type} 最佳实践...")
        
        # 模拟搜索结果
        best_practices = {
            "diode": [
                "网格: 结区至少50个节点",
                "初值: 先用Poisson方程求解电势",
                "偏置: 使用对数步长扫描反向偏置"
            ],
            "nbn": [
                "必须包含Auger复合模型",
                "势垒层需要极细网格(0.01um)",
                "低温下使用Fermi-Dirac统计",
                "界面处加密防止数值振荡"
            ],
            "mosfet": [
                "沟道区需要高网格密度",
                "考虑场相关迁移率",
                "界面态可能影响阈值电压"
            ]
        }
        
        return best_practices.get(device_type, ["建议参考类似器件的仿真设置"])
    
    def check_for_updates(self) -> List[str]:
        """检查哪些缓存需要更新"""
        outdated = []
        
        if not os.path.exists(self.cache_dir):
            return outdated
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                cache_age = self._get_cache_age(filepath)
                
                if cache_age > self.cache_duration:
                    material = filename[:-5]  # 去掉.json
                    outdated.append(material)
        
        return outdated
    
    def update_all_cache(self):
        """更新所有过期缓存"""
        outdated = self.check_for_updates()
        
        if not outdated:
            print("所有参数缓存都是最新的")
            return
        
        print(f"\n更新 {len(outdated)} 个过期缓存:")
        for material in outdated:
            print(f"  更新 {material}...")
            self.get_material_parameters(material, force_refresh=True)
            time.sleep(0.5)  # 避免请求过快
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        stats = {
            "total_cached": 0,
            "outdated": 0,
            "up_to_date": 0,
            "materials": []
        }
        
        if not os.path.exists(self.cache_dir):
            return stats
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                material = filename[:-5]
                filepath = os.path.join(self.cache_dir, filename)
                cache_age = self._get_cache_age(filepath)
                
                is_outdated = cache_age > self.cache_duration
                
                stats["total_cached"] += 1
                if is_outdated:
                    stats["outdated"] += 1
                else:
                    stats["up_to_date"] += 1
                
                stats["materials"].append({
                    "name": material,
                    "age_days": cache_age.days,
                    "outdated": is_outdated
                })
        
        return stats


# 便捷函数
def enrich_material_database(material: str, knowledge_dir: str) -> Dict:
    """
    便捷函数：丰富材料数据库
    
    使用示例:
        params = enrich_material_database("InGaAs", "/path/to/data")
        # 自动搜索并缓存参数
    """
    data_dir = os.path.dirname(knowledge_dir)
    learner = WebLearner(data_dir)
    return learner.get_material_parameters(material)
