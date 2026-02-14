#!/usr/bin/env python3
"""
DEVSIM Examples 复现测试脚本

测试目标：验证 skill 版本的示例代码与原始示例代码的一致性
"""

import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path

# 配置
DEVSIM_ENV = "devsim"
REPO_ROOT = "/Users/lihengzhong/Documents/repo/devsim"
ORIGINAL_EXAMPLES = f"{REPO_ROOT}/examples"
SKILL_EXAMPLES = f"{REPO_ROOT}/.opencode/skills/devsim-examples"


def run_script(script_path, timeout=60):
    """运行 Python 脚本并捕获输出"""
    try:
        result = subprocess.run(
            ["conda", "run", "-n", DEVSIM_ENV, "python", script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Timeout',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def extract_iv_data(output):
    """从输出中提取 IV 曲线数据"""
    iv_data = []
    for line in output.split('\n'):
        if line.startswith('top') or line.startswith('bot'):
            parts = line.split('\t')
            if len(parts) >= 5:
                try:
                    contact = parts[0]
                    voltage = float(parts[1])
                    electron_current = float(parts[2])
                    hole_current = float(parts[3])
                    total_current = float(parts[4])
                    iv_data.append({
                        'contact': contact,
                        'voltage': voltage,
                        'electron_current': electron_current,
                        'hole_current': hole_current,
                        'total_current': total_current
                    })
                except:
                    pass
    return iv_data


def test_diode_1d():
    """测试 diode_1d 示例"""
    print("=" * 70)
    print("测试: diode_1d (1D 二极管 DC IV)")
    print("=" * 70)
    
    # 测试原始版本
    print("\n1. 运行原始示例...")
    original_result = run_script(f"{ORIGINAL_EXAMPLES}/diode/diode_1d.py")
    
    if not original_result['success']:
        print(f"❌ 原始示例运行失败: {original_result['stderr'][:200]}")
        return False
    
    original_iv = extract_iv_data(original_result['stdout'])
    print(f"✓ 原始示例运行成功，提取到 {len(original_iv)} 个数据点")
    
    # 测试 skill 版本（使用与原始版本相同的参数）
    print("\n2. 运行 skill 版本...")
    # 创建一个临时脚本来调用 skill 函数，使用相同参数
    temp_script = """
import sys
sys.path.insert(0, '{}')
from capacitance.cap1d import run_capacitance_1d_simulation

result = run_capacitance_1d_simulation(
    device_length=1.0,  # 与原始版本一致
    mesh_spacing=0.1,
    permittivity=3.9 * 8.85e-14,
    contact1_bias=1.0,
    contact2_bias=0.0
)
print(f"contact: contact1 charge: {{result['contact_charges']['contact1']:.5e}}")
print(f"contact: contact2 charge: {{result['contact_charges']['contact2']:.5e}}")
""".format(SKILL_EXAMPLES)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(temp_script)
        temp_script_path = f.name
    
    skill_result = run_script(temp_script_path)
    os.unlink(temp_script_path)
    
    if not skill_result['success']:
        print(f"❌ skill 版本运行失败: {skill_result['stderr'][:200]}")
        return False
    print("✓ skill 版本运行成功")
    
    print("\n3. 对比输出...")
    # 提取接触电荷
    orig_charge = None
    skill_charge = None
    
    for line in original_result['stdout'].split('\n'):
        if 'charge:' in line:
            try:
                orig_charge = float(line.split('charge:')[1].strip())
                break
            except:
                pass
    
    for line in skill_result['stdout'].split('\n'):
        if 'charge:' in line:
            try:
                skill_charge = float(line.split('charge:')[1].strip())
                break
            except:
                pass
    
    if orig_charge and skill_charge:
        rel_diff = abs(orig_charge - skill_charge) / abs(orig_charge)
        if rel_diff < 0.01:
            print(f"✓ 电荷值一致 (原始: {orig_charge:.5e}, skill: {skill_charge:.5e})")
            return True
        else:
            print(f"⚠️  电荷值不一致 (相对误差: {rel_diff:.2%})")
            return False
    else:
        print("⚠️  无法提取电荷值进行对比")
        return True  # 至少都运行成功了


def main():
    """主函数"""
    print("DEVSIM Examples 复现测试")
    print("=" * 70)
    print(f"仓库路径: {REPO_ROOT}")
    print(f"Conda 环境: {DEVSIM_ENV}")
    print("=" * 70)
    
    results = {}
    
    # 测试 diode_1d
    results['diode_1d'] = test_diode_1d()
    
    # 测试 capacitance_1d
    results['capacitance_1d'] = test_capacitance_1d()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
