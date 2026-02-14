#!/usr/bin/env python3
"""
DEVSIM Examples 复现测试脚本 - 简化版

测试目标：验证 skill 版本的 diode_1d 与原始示例的一致性
"""

import subprocess
import sys
import os

# 配置
DEVSIM_ENV = "devsim"
REPO_ROOT = "/Users/lihengzhong/Documents/repo/devsim"

def run_script(script_path, timeout=120):
    """运行 Python 脚本并捕获输出"""
    try:
        result = subprocess.run(
            ["conda", "run", "-n", DEVSIM_ENV, "python", script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def extract_iv_data(output):
    """从输出中提取 IV 曲线数据"""
    iv_data = []
    for line in output.split('\n'):
        if line.startswith('top') or line.startswith('bot'):
            parts = line.split('\t')
            if len(parts) >= 5:
                try:
                    iv_data.append({
                        'contact': parts[0],
                        'voltage': float(parts[1]),
                        'electron': float(parts[2]),
                        'hole': float(parts[3]),
                        'total': float(parts[4])
                    })
                except:
                    pass
    return iv_data

print("=" * 70)
print("DEVSIM Examples 复现测试")
print("=" * 70)
print("测试: diode_1d")
print("=" * 70)

# 1. 运行原始示例
print("\n1. 运行原始示例...")
stdout1, stderr1, rc1 = run_script(f"{REPO_ROOT}/examples/diode/diode_1d.py")

if rc1 != 0:
    print(f"❌ 原始示例失败: {stderr1[:200]}")
    sys.exit(1)

original_iv = extract_iv_data(stdout1)
print(f"✓ 原始示例成功，提取 {len(original_iv)} 个数据点")

# 2. 运行 skill 版本
print("\n2. 运行 skill 版本...")
stdout2, stderr2, rc2 = run_script(f"{REPO_ROOT}/.opencode/skills/devsim-examples/diode/diode_1d.py")

if rc2 != 0:
    print(f"❌ skill 版本失败: {stderr2[:200]}")
    sys.exit(1)

skill_iv = extract_iv_data(stdout2)
print(f"✓ skill 版本成功，提取 {len(skill_iv)} 个数据点")

# 3. 对比结果
print("\n3. 对比结果...")
if len(original_iv) != len(skill_iv):
    print(f"⚠️  数据点数量不同: {len(original_iv)} vs {len(skill_iv)}")

# 对比电流值
max_diff = 0
for i, (o, s) in enumerate(zip(original_iv, skill_iv)):
    if o['contact'] != s['contact'] or abs(o['voltage'] - s['voltage']) > 1e-10:
        continue
    
    for key in ['electron', 'hole', 'total']:
        if abs(o[key]) < 1e-15 and abs(s[key]) < 1e-15:
            continue
        if abs(o[key]) > 1e-15:
            diff = abs(o[key] - s[key]) / abs(o[key])
        else:
            diff = abs(o[key] - s[key])
        max_diff = max(max_diff, diff)
        
        if diff > 0.01:
            print(f"❌ 数据点 {i}: {key} 电流不一致 (误差 {diff:.2%})")
            print(f"   原始: {o[key]:.6e}")
            print(f"   skill: {s[key]:.6e}")

if max_diff < 0.01:
    print(f"✓ 所有数据点一致 (最大相对误差: {max_diff:.4%})")
    print("\n" + "=" * 70)
    print("✓✓✓ 测试通过！skill 版本与原始示例完全一致！")
    print("=" * 70)
    sys.exit(0)
else:
    print(f"\n⚠️  最大相对误差: {max_diff:.2%}")
    print("=" * 70)
    print("❌ 测试未通过")
    print("=" * 70)
    sys.exit(1)
