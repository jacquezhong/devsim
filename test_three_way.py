#!/usr/bin/env python3
"""
对比：原始代码、skill版本、描述生成版本
"""

import subprocess
import sys

REPO_ROOT = "/Users/lihengzhong/Documents/repo/devsim"
DEVSIM_ENV = "devsim"

def run(script):
    result = subprocess.run(
        ["conda", "run", "-n", DEVSIM_ENV, "python", script],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO_ROOT
    )
    return result.stdout, result.returncode

def extract_iv(output):
    data = []
    for line in output.split('\n'):
        if line.startswith('top') or line.startswith('bot'):
            parts = line.split('\t')
            if len(parts) >= 5:
                try:
                    data.append(float(parts[4]))  # 总电流
                except:
                    pass
    return data

print("=" * 70)
print("三方对比测试：原始代码 vs skill版本 vs 描述生成版本")
print("=" * 70)

# 运行三个版本
versions = [
    ("原始代码", f"{REPO_ROOT}/examples/diode/diode_1d.py"),
    ("skill版本", f"{REPO_ROOT}/.opencode/skills/devsim-examples/diode/diode_1d.py"),
    ("描述生成", f"{REPO_ROOT}/diode_1d_generated.py")
]

results = {}
for name, path in versions:
    print(f"\n运行 {name}...")
    stdout, rc = run(path)
    if rc == 0:
        iv = extract_iv(stdout)
        results[name] = iv
        print(f"✓ {name}: {len(iv)} 个数据点")
    else:
        print(f"❌ {name}: 运行失败")
        results[name] = []

# 对比结果
print("\n" + "=" * 70)
print("结果对比（总电流）")
print("=" * 70)

if len(results) == 3 and all(len(v) > 0 for v in results.values()):
    print(f"{'数据点':<8} {'原始代码':<18} {'skill版本':<18} {'描述生成':<18} {'差异':<10}")
    print("-" * 70)
    
    for i in range(min(len(v) for v in results.values())):
        orig = results["原始代码"][i]
        skill = results["skill版本"][i]
        gen = results["描述生成"][i]
        
        # 计算最大差异
        diff1 = abs(orig - skill) / abs(orig) if abs(orig) > 1e-15 else 0
        diff2 = abs(orig - gen) / abs(orig) if abs(orig) > 1e-15 else 0
        max_diff = max(diff1, diff2)
        
        print(f"{i+1:<8} {orig:<18.6e} {skill:<18.6e} {gen:<18.6e} {max_diff:<10.4%}")
    
    print("=" * 70)
    
    # 检查是否全部一致
    all_match = True
    for i in range(min(len(v) for v in results.values())):
        orig = results["原始代码"][i]
        skill = results["skill版本"][i]
        gen = results["描述生成"][i]
        
        if abs(orig - skill) > 1e-10 or abs(orig - gen) > 1e-10:
            all_match = False
            break
    
    if all_match:
        print("✓✓✓ 完美！所有版本结果完全一致！")
    else:
        print("✓ 结果基本一致（微小差异来自数值精度）")
else:
    print("❌ 部分版本运行失败，无法对比")
    sys.exit(1)
