#!/usr/bin/env python3
"""
场板二极管DEVSIM仿真 - 优化版
使用渐进式偏压扫描和稳健的求解策略
"""
import sys
import os
import json
import time
import signal
from datetime import datetime

sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

try:
    import devsim
    from devsim import (
        create_gmsh_mesh, add_gmsh_region, add_gmsh_contact,
        finalize_mesh, create_device, get_region_list, get_contact_list,
        set_parameter, solve, get_contact_current, get_edge_model_values,
        delete_device, delete_mesh, set_node_values, node_solution
    )
except ImportError as e:
    print(f"✗ DEVSIM加载失败: {e}")
    sys.exit(1)

from devsim.python_packages.simple_physics import (
    SetSiliconParameters, GetContactBiasName
)
from devsim.python_packages.model_create import CreateSolution
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly,
    CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion,
    CreateSiliconDriftDiffusionAtContact,
)

interrupted = False

def signal_handler(signum, frame):
    global interrupted
    print("\n\n⚠️ 收到中断信号，保存进度...")
    interrupted = True

signal.signal(signal.SIGINT, signal_handler)


class RobustFieldPlateSimulator:
    """稳健的场板二极管仿真器"""
    
    def __init__(self, L_fp, mesh_file, output_dir='data/real'):
        self.L_fp = L_fp
        self.mesh_file = mesh_file
        self.output_dir = output_dir
        self.device_name = f"diode_fp_{L_fp:.1f}"
        self.mesh_name = f"mesh_fp_{L_fp:.1f}"
        
        os.makedirs(output_dir, exist_ok=True)
        self.result_file = os.path.join(output_dir, f'result_L{L_fp}_robust.json')
        
        self.results = {
            'L_fp': L_fp,
            'mesh_file': mesh_file,
            'start_time': datetime.now().isoformat(),
            'voltages': [],
            'currents': [],
            'max_electric_fields': [],
            'breakdown_voltage': None,
            'status': 'running',
            'completed_voltages': [],
            'solver_log': []
        }
        
    def load_mesh(self):
        """加载Gmsh网格"""
        print(f"  加载网格: {self.mesh_file}")
        
        try:
            # 清理
            try:
                delete_device(device=self.device_name)
                delete_mesh(mesh=self.mesh_name)
            except:
                pass
            
            # 创建并加载网格
            create_gmsh_mesh(mesh=self.mesh_name, file=self.mesh_file)
            add_gmsh_region(gmsh_name='pplus', mesh=self.mesh_name, 
                          region='pplus', material='Si')
            add_gmsh_region(gmsh_name='ndrift', mesh=self.mesh_name, 
                          region='ndrift', material='Si')
            
            add_gmsh_contact(gmsh_name='anode', mesh=self.mesh_name, 
                           name='anode', material='metal', region='pplus')
            add_gmsh_contact(gmsh_name='cathode', mesh=self.mesh_name, 
                           name='cathode', material='metal', region='ndrift')
            
            finalize_mesh(mesh=self.mesh_name)
            create_device(mesh=self.mesh_name, device=self.device_name)
            
            regions = get_region_list(device=self.device_name)
            contacts = get_contact_list(device=self.device_name)
            
            print(f"  ✓ 网格加载成功: {len(regions)}个区域, {len(contacts)}个接触")
            return True
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            return False
    
    def setup_physics(self):
        """设置物理模型 - 分步进行"""
        print(f"  设置物理模型...")
        
        try:
            # 设置硅参数
            SetSiliconParameters(self.device_name, 'pplus', 300)
            SetSiliconParameters(self.device_name, 'ndrift', 300)
            
            # 使用阶跃掺杂模型
            # P+区: x < 5e-4 cm
            import devsim
            devsim.node_model(device=self.device_name, region='pplus', 
                            name='Acceptors', equation='1e19')
            devsim.node_model(device=self.device_name, region='pplus', 
                            name='Donors', equation='0')
            devsim.node_model(device=self.device_name, region='pplus', 
                            name='NetDoping', equation='Acceptors-Donors')
            
            # N区: 均匀掺杂
            devsim.node_model(device=self.device_name, region='ndrift', 
                            name='Acceptors', equation='0')
            devsim.node_model(device=self.device_name, region='ndrift', 
                            name='Donors', equation='1e14')
            devsim.node_model(device=self.device_name, region='ndrift', 
                            name='NetDoping', equation='Donors-Acceptors')
            
            print(f"    P+区: 1e19 cm^-3, N区: 1e14 cm^-3")
            return True
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def solve_potential_only(self):
        """仅求解势方程（作为初始猜测）"""
        print(f"  求解初始势分布...")
        
        try:
            # 在P+区和N区创建Potential解
            for region in ['pplus', 'ndrift']:
                CreateSolution(self.device_name, region, "Potential")
                CreateSiliconPotentialOnly(self.device_name, region)
                
                # 设置接触偏置为0
                for contact in ['anode', 'cathode']:
                    try:
                        set_parameter(device=self.device_name, 
                                    name=GetContactBiasName(contact), value=0.0)
                        CreateSiliconPotentialOnlyContact(self.device_name, region, contact)
                    except:
                        pass
            
            # 使用宽松的容差求解势
            solve(type="dc", absolute_error=1.0, relative_error=1e-10, 
                  maximum_iterations=100)
            
            print(f"  ✓ 势求解完成")
            return True
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            return False
    
    def add_carriers_and_solve(self):
        """添加载流子并求解漂移扩散方程"""
        print(f"  添加载流子并求解...")
        
        try:
            # 添加载流子解
            for region in ['pplus', 'ndrift']:
                CreateSolution(self.device_name, region, "Electrons")
                CreateSolution(self.device_name, region, "Holes")
                
                # 从本征载流子初始化
                set_node_values(device=self.device_name, region=region, 
                              name="Electrons", init_from="IntrinsicElectrons")
                set_node_values(device=self.device_name, region=region, 
                              name="Holes", init_from="IntrinsicHoles")
                
                CreateSiliconDriftDiffusion(self.device_name, region)
                
                for contact in ['anode', 'cathode']:
                    try:
                        CreateSiliconDriftDiffusionAtContact(self.device_name, region, contact)
                    except:
                        pass
            
            # 求解漂移扩散方程 - 使用较宽松的容差
            solve(type="dc", absolute_error=1e12, relative_error=1e-8, 
                  maximum_iterations=100)
            
            print(f"  ✓ 漂移扩散求解完成")
            return True
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            return False
    
    def ramp_voltage(self, target_v, step=2.0):
        """渐进式电压扫描"""
        print(f"    渐进式升压至 {target_v}V (步长{step}V)...")
        
        current_v = 0.0
        
        # 找到当前电压
        if self.results['voltages']:
            current_v = self.results['voltages'][-1]
        
        # 逐步增加电压
        while current_v > target_v + step/2:  # 注意是负值
            next_v = max(target_v, current_v - step)
            
            try:
                print(f"      V = {next_v}V...", end=' ', flush=True)
                
                set_parameter(device=self.device_name, 
                            name=GetContactBiasName('anode'), value=next_v)
                
                # 使用continuation方法 - 用前一个解作为初始猜测
                solve_info = solve(type="dc", absolute_error=1e12, 
                                 relative_error=1e-8, maximum_iterations=100)
                
                if solve_info and not solve_info.get('converged', True):
                    print(f"未收敛")
                    # 尝试减小步长
                    step = step / 2
                    if step < 0.5:
                        print(f"      步长过小，跳过此点")
                        return False
                    continue
                
                current_v = next_v
                print(f"✓")
                
            except Exception as e:
                print(f"错误: {e}")
                return False
        
        return True
    
    def extract_and_record(self, v):
        """提取并记录结果"""
        try:
            # 提取电流
            try:
                current = get_contact_current(device=self.device_name, contact='anode')
            except:
                current = 0
            
            # 提取峰值电场
            try:
                E_field = get_edge_model_values(device=self.device_name, 
                                               region='ndrift', name='ElectricField')
                max_E = max(E_field) if len(E_field) > 0 else 0
            except:
                max_E = 0
            
            # 记录
            self.results['voltages'].append(v)
            self.results['currents'].append(current)
            self.results['max_electric_fields'].append(max_E)
            self.results['completed_voltages'].append(v)
            
            print(f"    ✓ I={current:.2e}A, Emax={max_E:.2e}V/cm")
            
            # 检测击穿
            if self.results['breakdown_voltage'] is None and len(self.results['currents']) > 1:
                prev_current = abs(self.results['currents'][-2])
                curr_current = abs(current)
                if prev_current > 1e-15:
                    current_ratio = curr_current / prev_current
                    if current_ratio > 3 or max_E > 2.5e5:
                        self.results['breakdown_voltage'] = v
                        print(f"    ✓✓✓ 击穿电压: {v}V")
            
            return True
            
        except Exception as e:
            print(f"    ✗ 提取失败: {e}")
            return False
    
    def run_simulation(self, voltages):
        """运行偏压扫描"""
        print(f"\n  开始偏压扫描 ({len(voltages)}个点)...")
        
        prev_v = 0.0
        
        for i, v in enumerate(voltages):
            if interrupted:
                print(f"\n  ⚠️ 中断，保存进度...")
                self.save_results()
                return False
            
            # 检查是否已完成
            if v in self.results['completed_voltages']:
                print(f"    [{i+1}/{len(voltages)}] V={v}V (已跳过)")
                continue
            
            print(f"\n    [{i+1}/{len(voltages)}] 目标: V={v}V")
            
            # 渐进式升压
            if not self.ramp_voltage(v, step=5.0):
                print(f"    ✗ 无法达到 {v}V")
                break
            
            # 提取结果
            self.extract_and_record(v)
            
            # 每3个点保存一次
            if (i + 1) % 3 == 0:
                self.save_results()
        
        return True
    
    def save_results(self):
        """保存结果"""
        self.results['end_time'] = datetime.now().isoformat()
        self.results['status'] = 'completed' if self.results['breakdown_voltage'] else 'partial'
        
        with open(self.result_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"  结果已保存: {self.result_file}")
    
    def check_existing(self):
        """检查已有结果"""
        if os.path.exists(self.result_file):
            try:
                with open(self.result_file, 'r') as f:
                    existing = json.load(f)
                
                if existing.get('status') == 'completed':
                    print(f"  ✓ 已有完整结果")
                    return True, existing
                else:
                    self.results = existing
                    print(f"  ⚠️ 继续未完成: {len(existing.get('completed_voltages', []))} 点")
                    return False, existing
                    
            except:
                pass
        
        return False, None
    
    def run(self, voltages):
        """运行完整仿真"""
        print(f"\n{'='*70}")
        print(f"场板长度 L_fp = {self.L_fp} μm (稳健模式)")
        print(f"{'='*70}")
        
        # 检查已有结果
        completed, existing = self.check_existing()
        if completed:
            return existing
        
        # 加载网格
        if not self.load_mesh():
            return None
        
        # 设置物理模型
        if not self.setup_physics():
            return None
        
        # 求解势
        if not self.solve_potential_only():
            return None
        
        # 添加载流子
        if not self.add_carriers_and_solve():
            return None
        
        # 偏压扫描
        success = self.run_simulation(voltages)
        
        # 保存结果
        self.save_results()
        
        # 清理
        try:
            delete_device(device=self.device_name)
            delete_mesh(mesh=self.mesh_name)
        except:
            pass
        
        return self.results


def main():
    """主函数"""
    
    print("="*70)
    print("场板二极管DEVSIM仿真 (稳健模式)")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 场板长度
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    
    # 偏压列表 - 从0V开始，逐步到-200V
    voltages = [-5, -10, -15, -20, -25, -30, -40, -50, -60, -70, 
                -80, -90, -100, -110, -120, -130, -140, -150, 
                -160, -170, -180, -190, -200]
    
    print("仿真参数:")
    print(f"  场板长度: {L_fp_values} μm")
    print(f"  电压扫描: {len(voltages)} 个点")
    print(f"  求解策略: 渐进式升压 + Continuation")
    print()
    print("提示: 按 Ctrl+C 中断，会自动保存并恢复")
    print("="*70)
    
    all_results = []
    
    for L_fp in L_fp_values:
        mesh_file = f"diode_fp_L{L_fp}.msh"
        
        if not os.path.exists(mesh_file):
            print(f"\n✗ 网格文件不存在: {mesh_file}")
            continue
        
        simulator = RobustFieldPlateSimulator(L_fp, mesh_file)
        result = simulator.run(voltages)
        
        if result:
            all_results.append(result)
            
            print(f"\n  结果汇总:")
            print(f"    完成点数: {len(result['voltages'])}")
            if result['breakdown_voltage']:
                print(f"    击穿电压: {result['breakdown_voltage']} V")
    
    # 合并保存
    output_file = 'data/final/breakdown_results_robust.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\n{'='*70}")
    print(f"仿真完成!")
    print(f"结果: {output_file}")
    print(f"{'='*70}")
    
    # 总结
    print("\n结果汇总:")
    print(f"{'L_fp (μm)':<15} {'击穿电压 (V)':<20} {'完成点数':<10}")
    print("-" * 70)
    for result in all_results:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage'] if result['breakdown_voltage'] else '未到达'
        n_points = len(result['voltages'])
        print(f"{L_fp:<15} {str(BV):<20} {n_points:<10}")
    print("=" * 70)


if __name__ == '__main__':
    main()
