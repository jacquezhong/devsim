#!/usr/bin/env python3
"""
从日志文件中提取已完成的仿真数据
"""
import re
import json
from datetime import datetime

print("从日志提取已完成的DEVSIM仿真数据...")

# 读取日志文件
log_file = "dd_simulation_L2.0.log"
try:
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 提取电压和电流数据
    # 格式: "✓ V={v}V: I={current:.2e}A, Emax={E:.2e}V/cm"
    pattern = r'✓ V=(-?\d+)V: I=([\d.e+-]+)A, Emax=([\d.e+-]+)V/cm'
    matches = re.findall(pattern, content)
    
    results = []
    for v, i, e in matches:
        results.append({
            "V": int(v),
            "I": float(i),
            "E": float(e)
        })
    
    print(f"找到 {len(results)} 个完成的电压点:")
    for r in results:
        print(f"  V={r['V']}V: I={r['I']:.2e}A, Emax={r['E']:.2e}V/cm")
    
    # 检测击穿电压
    breakdown_voltage = None
    for i in range(1, len(results)):
        prev_I = abs(results[i-1]['I'])
        curr_I = abs(results[i]['I'])
        if prev_I > 1e-15 and curr_I / prev_I > 5:
            breakdown_voltage = results[i]['V']
            print(f"\n✓✓✓ 击穿检测: {breakdown_voltage}V")
            break
    
    # 保存结果
    result_data = {
        "L_fp": 2.0,
        "timestamp": datetime.now().isoformat(),
        "status": "partial - 11 of 12 points completed",
        "note": "V=-200V not converged due to large step size",
        "voltages": [r['V'] for r in results],
        "currents": [r['I'] for r in results],
        "max_electric_fields": [r['E'] for r in results],
        "breakdown_voltage": breakdown_voltage,
        "n_points": len(results)
    }
    
    with open("data/final/devsim_partial_results_L2.0.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\n✓ 结果已保存: data/final/devsim_partial_results_L2.0.json")
    print(f"\n数据质量: {len(results)}/12 电压点 (91.7% 完成)")
    
    if breakdown_voltage:
        print(f"击穿电压: {breakdown_voltage} V")
    
    print("\n建议: 继续运行剩余4组场板长度仿真")
    
except Exception as e:
    print(f"✗ 提取失败: {e}")
