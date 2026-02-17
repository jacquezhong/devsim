#!/usr/bin/env python3
"""
场板二极管击穿特性真实DEVSIM仿真
支持断点续传、定期保存、详细日志
"""
import sys
import os
import json
import time
import signal
from datetime import datetime

# 添加路径
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

# 导入DEVSIM
try:
    import devsim
    from devsim import (
        create_gmsh_mesh, add_gmsh_region, add_gmsh_contact,
        finalize_mesh, create_device, get_region_list, get_contact_list,
        set_parameter, solve, get_contact_current, get_edge_model_values,
        delete_device, delete_mesh
    )
    DEVSIM_AVAILABLE = True
    print(f"✓ DEVSIM {devsim.__version__ if hasattr(devsim, '__version__') else '2.7.1'} 已加载")
except ImportError as e:
    print(f"✗ DEVSIM加载失败: {e}")
    DEVSIM_AVAILABLE = False
    sys.exit(1)

# 导入物理模型
from devsim.python_packages.simple_physics import (
    SetSiliconParameters, GetContactBiasName, PrintCurrents
)
from devsim.python_packages.model_create import (
    CreateSolution, CreateNodeModel
)
from devsim.python_packages.simple_physics import (
    CreateSiliconPotentialOnly,
    CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion,
    CreateSiliconDriftDiffusionAtContact,
)

# 全局变量用于信号处理
interrupted = False

def signal_handler(signum, frame):
    """处理中断信号"""
    global interrupted
    print("\n\n⚠️ 收到中断信号，正在保存当前进度...")
    interrupted = True

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class FieldPlateSimulator:
    """场板二极管仿真器"""
    
    def __init__(self, L_fp, mesh_file, output_dir='data/real'):
        """
        初始化仿真器
        
        参数:
            L_fp: 场板长度 (μm)
            mesh_file: Gmsh网格文件路径
            output_dir: 输出目录
        """
        self.L_fp = L_fp
        self.mesh_file = mesh_file
        self.output_dir = output_dir
        self.device_name = f"diode_fp_{L_fp:.1f}"
        self.mesh_name = f"mesh_fp_{L_fp:.1f}"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 结果文件路径
        self.result_file = os.path.join(output_dir, f'result_L{L_fp}.json')
        self.temp_file = os.path.join(output_dir, f'result_L{L_fp}.temp.json')
        
        # 仿真状态
        self.results = {
            'L_fp': L_fp,
            'mesh_file': mesh_file,
            'start_time': datetime.now().isoformat(),
            'voltages': [],
            'currents': [],
            'max_electric_fields': [],
            'breakdown_voltage': None,
            'status': 'running',
            'completed_voltages': []
        }
        
    def load_mesh(self):
        """加载Gmsh网格"""
        print(f"  加载网格: {self.mesh_file}")
        
        try:
            # 清理之前的mesh
            try:
                delete_device(device=self.device_name)
                delete_mesh(mesh=self.mesh_name)
            except:
                pass
            
            # 创建Gmsh mesh
            create_gmsh_mesh(mesh=self.mesh_name, file=self.mesh_file)
            
            # 添加区域
            add_gmsh_region(gmsh_name='pplus', mesh=self.mesh_name, 
                          region='pplus', material='Si')
            add_gmsh_region(gmsh_name='ndrift', mesh=self.mesh_name, 
                          region='ndrift', material='Si')
            add_gmsh_region(gmsh_name='fieldplate_metal', mesh=self.mesh_name, 
                          region='fieldplate', material='metal')
            
            # 添加接触
            add_gmsh_contact(gmsh_name='anode', mesh=self.mesh_name, 
                           name='anode', material='metal', region='pplus')
            add_gmsh_contact(gmsh_name='cathode', mesh=self.mesh_name, 
                           name='cathode', material='metal', region='ndrift')
            add_gmsh_contact(gmsh_name='field_plate', mesh=self.mesh_name, 
                           name='field_plate', material='metal', region='fieldplate')
            
            # 完成网格
            finalize_mesh(mesh=self.mesh_name)
            
            # 创建设备
            create_device(mesh=self.mesh_name, device=self.device_name)
            
            # 验证
            regions = get_region_list(device=self.device_name)
            contacts = get_contact_list(device=self.device_name)
            
            print(f"  ✓ 网格加载成功")
            print(f"    区域: {regions}")
            print(f"    接触: {contacts}")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 网格加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_physics(self, p_doping=1e19, n_doping=1e14, temperature=300):
        """设置物理模型"""
        print(f"  设置物理模型...")
        
        try:
            # 设置硅参数
            SetSiliconParameters(self.device_name, 'pplus', temperature)
            SetSiliconParameters(self.device_name, 'ndrift', temperature)
            SetSiliconParameters(self.device_name, 'fieldplate', temperature)
            
            # 设置掺杂分布
            # P+区: x < 5e-4 cm (5 μm)
            CreateNodeModel(self.device_name, 'pplus', 'Acceptors', f'{p_doping}')
            CreateNodeModel(self.device_name, 'pplus', 'Donors', '0')
            CreateNodeModel(self.device_name, 'pplus', 'NetDoping', 'Acceptors-Donors')
            
            # N区: 均匀掺杂
            CreateNodeModel(self.device_name, 'ndrift', 'Acceptors', '0')
            CreateNodeModel(self.device_name, 'ndrift', 'Donors', f'{n_doping}')
            CreateNodeModel(self.device_name, 'ndrift', 'NetDoping', 'Donors-Acceptors')
            
            print(f"    P+区掺杂: {p_doping:.0e} cm^-3")
            print(f"    N区掺杂: {n_doping:.0e} cm^-3")
            print(f"    温度: {temperature} K")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 物理模型设置失败: {e}")
            return False
    
    def solve_initial(self):
        """求解初始解"""
        print(f"  求解初始解...")
        
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
            
            # 求解
            solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=30)
            
            print(f"  ✓ 初始势求解完成")
            
            # 添加载流子
            for region in ['pplus', 'ndrift']:
                CreateSolution(self.device_name, region, "Electrons")
                CreateSolution(self.device_name, region, "Holes")
                
                devsim.set_node_values(device=self.device_name, region=region, 
                                      name="Electrons", init_from="IntrinsicElectrons")
                devsim.set_node_values(device=self.device_name, region=region, 
                                      name="Holes", init_from="IntrinsicHoles")
                
                CreateSiliconDriftDiffusion(self.device_name, region)
                
                for contact in ['anode', 'cathode']:
                    try:
                        CreateSiliconDriftDiffusionAtContact(self.device_name, region, contact)
                    except:
                        pass
            
            solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
            
            print(f"  ✓ 漂移扩散求解完成")
            
            return True
            
        except Exception as e:
            print(f"  ✗ 初始解失败: {e}")
            return False
    
    def run_simulation(self, voltages):
        """运行偏压扫描仿真"""
        print(f"\n  开始偏压扫描...")
        print(f"    总点数: {len(voltages)}")
        print(f"    范围: {voltages[0]}V ~ {voltages[-1]}V")
        
        start_time = time.time()
        
        for i, v in enumerate(voltages):
            if interrupted:
                print(f"\n  ⚠️ 仿真中断，保存当前进度...")
                self.save_results()
                return False
            
            # 检查是否已完成
            if v in self.results['completed_voltages']:
                print(f"    [{i+1}/{len(voltages)}] V={v}V (已跳过)")
                continue
            
            print(f"    [{i+1}/{len(voltages)}] V={v}V...", end=' ', flush=True)
            
            try:
                # 设置阳极偏置（反向偏压为负）
                set_parameter(device=self.device_name, 
                            name=GetContactBiasName('anode'), value=v)
                
                # 求解
                solve_info = solve(type="dc", absolute_error=1e10, 
                                 relative_error=1e-10, maximum_iterations=50)
                
                converged = True if solve_info is None else solve_info.get('converged', True)
                
                if not converged:
                    print(f"未收敛")
                    continue
                
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
                
                # 记录结果
                self.results['voltages'].append(v)
                self.results['currents'].append(current)
                self.results['max_electric_fields'].append(max_E)
                self.results['completed_voltages'].append(v)
                
                # 检测击穿
                if self.results['breakdown_voltage'] is None and len(self.results['currents']) > 1:
                    prev_current = abs(self.results['currents'][-2])
                    curr_current = abs(current)
                    if prev_current > 1e-15:
                        current_ratio = curr_current / prev_current
                        if current_ratio > 3 or max_E > 2.5e5:
                            self.results['breakdown_voltage'] = v
                            print(f"✓ 击穿! I={current:.2e}A")
                            
                            # 保存中间结果
                            self.save_results()
                            
                            # 击穿后继续5个点
                            remaining = [vv for vv in voltages[i+1:i+6] if vv < v]
                            if remaining:
                                print(f"      继续仿真击穿后特性...")
                            continue
                
                print(f"✓ I={current:.2e}A, Emax={max_E:.2e}V/cm")
                
                # 每5个点保存一次
                if (i + 1) % 5 == 0:
                    self.save_results()
                
            except Exception as e:
                print(f"✗ 错误: {e}")
                # 继续下一个点
                continue
        
        elapsed = time.time() - start_time
        print(f"\n  ✓ 仿真完成，耗时: {elapsed/60:.1f}分钟")
        
        return True
    
    def save_results(self):
        """保存结果"""
        self.results['end_time'] = datetime.now().isoformat()
        self.results['status'] = 'completed' if self.results['breakdown_voltage'] else 'running'
        
        # 保存到临时文件
        with open(self.temp_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # 完成后重命名
        os.rename(self.temp_file, self.result_file)
    
    def check_existing(self):
        """检查是否存在已完成的仿真"""
        if os.path.exists(self.result_file):
            try:
                with open(self.result_file, 'r') as f:
                    existing = json.load(f)
                
                if existing.get('status') == 'completed':
                    print(f"  ✓ 已存在完成的仿真结果")
                    print(f"    击穿电压: {existing.get('breakdown_voltage')}V")
                    return True, existing
                else:
                    # 恢复未完成的状态
                    self.results = existing
                    print(f"  ⚠️ 发现未完成的仿真，继续...")
                    print(f"    已完成: {len(existing.get('completed_voltages', []))} 个点")
                    return False, existing
                    
            except Exception as e:
                print(f"  ⚠️ 无法读取已有结果: {e}")
        
        return False, None
    
    def run(self, voltages):
        """运行完整仿真流程"""
        print(f"\n{'='*70}")
        print(f"场板长度 L_fp = {self.L_fp} μm")
        print(f"{'='*70}")
        
        # 检查是否已完成
        completed, existing = self.check_existing()
        if completed:
            return existing
        
        # 加载网格
        if not self.load_mesh():
            return None
        
        # 设置物理模型
        if not self.setup_physics():
            return None
        
        # 求解初始解
        if not self.solve_initial():
            return None
        
        # 运行偏压扫描
        success = self.run_simulation(voltages)
        
        # 保存最终结果
        self.save_results()
        
        # 清理
        try:
            delete_device(device=self.device_name)
            delete_mesh(mesh=self.mesh_name)
        except:
            pass
        
        if success:
            print(f"  ✓ 结果已保存: {self.result_file}")
        
        return self.results


def main():
    """主函数"""
    
    print("="*70)
    print("场板二极管真实DEVSIM仿真")
    print("支持断点续传、自动保存、中断恢复")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 场板长度列表
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    
    # 偏压列表
    voltages = list(range(-10, -201, -5))  # -10, -15, -20, ..., -200
    
    print("仿真参数:")
    print(f"  场板长度: {L_fp_values} μm")
    print(f"  电压扫描: {len(voltages)} 个点")
    print(f"  预计总时间: {len(L_fp_values) * 30} - {len(L_fp_values) * 60} 分钟")
    print()
    print("提示: 可按 Ctrl+C 中断，进度会自动保存")
    print("      重新运行脚本会自动继续未完成的仿真")
    print("="*70)
    
    all_results = []
    
    for L_fp in L_fp_values:
        mesh_file = f"diode_fp_L{L_fp}.msh"
        
        if not os.path.exists(mesh_file):
            print(f"\n✗ 网格文件不存在: {mesh_file}")
            continue
        
        # 创建仿真器并运行
        simulator = FieldPlateSimulator(L_fp, mesh_file)
        result = simulator.run(voltages)
        
        if result:
            all_results.append(result)
            
            print(f"\n  结果汇总:")
            print(f"    数据点: {len(result['voltages'])}")
            if result['breakdown_voltage']:
                print(f"    击穿电压: {result['breakdown_voltage']} V")
            else:
                print(f"    击穿电压: 未达到")
    
    # 合并所有结果
    output_file = 'data/final/breakdown_results_devsim.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\n{'='*70}")
    print(f"所有仿真完成!")
    print(f"结果已保存: {output_file}")
    print(f"{'='*70}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 打印总结
    print("\n实验结果总结:")
    print(f"{'L_fp (μm)':<15} {'击穿电压 (V)':<20} {'数据点':<10}")
    print("-" * 70)
    for result in all_results:
        L_fp = result['L_fp']
        BV = result['breakdown_voltage'] if result['breakdown_voltage'] else '未击穿'
        n_points = len(result['voltages'])
        print(f"{L_fp:<15} {str(BV):<20} {n_points:<10}")
    print("=" * 70)


if __name__ == '__main__':
    main()
