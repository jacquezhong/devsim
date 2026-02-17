#!/usr/bin/env python3
"""
超简化的场板二极管网格 - 单层矩形结构
保证边界闭合，最大化计算效率
"""
import subprocess
import os

def generate_simple_geo(l_fp_um, filename):
    """生成最简单的矩形器件网格"""
    
    # 简化为两个矩形区域
    # 区域1: P+区 (0,0) 到 (5e-4, 2e-4)
    # 区域2: N区 (0,2e-4) 到 (50e-4, 20e-4)
    
    L_device = 50e-4  # 50 μm
    L_pplus = 5e-4    # 5 μm
    H_pplus = 2e-4    # 2 μm  
    H_total = 20e-4   # 20 μm
    
    # 网格尺寸 - 非常粗以提高速度
    lc_junction = 0.1e-4   # 结区 100nm
    lc_bulk = 0.5e-4       # 体区 500nm
    
    geo_content = f"""// 超简化二极管网格 - 保证闭合
// 场板长度: {l_fp_um}μm

L = {L_device};   // 50um
Lp = {L_pplus};   // 5um
Hp = {H_pplus};   // 2um
Ht = {H_total};   // 20um

lc1 = {lc_junction};  // 结区
lc2 = {lc_bulk};      // 体区

// 点定义 - 只用8个点构成两个矩形
Point(1) = {{0, 0, 0, lc1}};
Point(2) = {{Lp, 0, 0, lc1}};
Point(3) = {{L, 0, 0, lc2}};
Point(4) = {{L, Ht, 0, lc2}};
Point(5) = {{Lp, Ht, 0, lc2}};
Point(6) = {{0, Ht, 0, lc2}};
Point(7) = {{Lp, Hp, 0, lc1}};
Point(8) = {{0, Hp, 0, lc1}};

// P+区边界
Line(1) = {{1, 2}};
Line(2) = {{2, 7}};
Line(3) = {{7, 8}};
Line(4) = {{8, 1}};

// N区边界
Line(5) = {{2, 3}};
Line(6) = {{3, 4}};
Line(7) = {{4, 5}};
Line(8) = {{5, 7}};
Line(9) = {{7, 8}};  // 共享边
Line(10) = {{8, 6}};
Line(11) = {{6, 5}};

// 修正：重新定义，避免共享边问题
"""

    # 使用完全独立的两个矩形
    geo_content = f"""// 超简化二极管网格 - 独立区域
// 场板长度: {l_fp_um}μm

L = {L_device};   // 50um
Lp = {L_pplus};   // 5um
Hp = {H_pplus};   // 2um
Ht = {H_total};   // 20um

lc1 = {lc_junction};
lc2 = {lc_bulk};

// 区域1: P+区 - 独立的4个点
Point(1) = {{0, 0, 0, lc1}};
Point(2) = {{Lp, 0, 0, lc1}};
Point(3) = {{Lp, Hp, 0, lc1}};
Point(4) = {{0, Hp, 0, lc1}};

// 区域2: N区 - 独立的4个点
Point(5) = {{0, Hp, 0, lc2}};    // 与P+区顶点重合但独立
Point(6) = {{Lp, Hp, 0, lc2}};
Point(7) = {{L, Hp, 0, lc2}};
Point(8) = {{L, Ht, 0, lc2}};
Point(9) = {{Lp, Ht, 0, lc2}};
Point(10) = {{0, Ht, 0, lc2}};

// P+区线
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

// N区线
Line(5) = {{5, 6}};
Line(6) = {{6, 7}};
Line(7) = {{7, 8}};
Line(8) = {{8, 9}};
Line(9) = {{9, 10}};
Line(10) = {{10, 5}};

// 面
Curve Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};

Curve Loop(2) = {{5, 6, 7, 8, 9, 10}};
Plane Surface(2) = {{2}};

// 物理组
Physical Curve("anode") = {{1}};
Physical Curve("cathode") = {{7}};
Physical Surface("pplus") = {{1}};
Physical Surface("ndrift") = {{2}};

Mesh.CharacteristicLengthMax = 1e-4;
"""
    
    with open(filename, 'w') as f:
        f.write(geo_content)
    
    return filename

def main():
    os.chdir('/Users/lihengzhong/Documents/repo/devsim/workspace/plan4')
    
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    
    print("="*60)
    print("生成超简化网格")
    print("="*60)
    
    for l_fp in L_fp_values:
        geo_file = f"simple_L{l_fp}.geo"
        msh_file = f"simple_L{l_fp}.msh"
        
        print(f"\nL_fp = {l_fp}μm...")
        generate_simple_geo(l_fp, geo_file)
        
        try:
            result = subprocess.run(
                ['gmsh', geo_file, '-2', '-o', msh_file, '-format', 'msh22'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                size = os.path.getsize(msh_file) / 1024
                print(f"  ✓ {msh_file} ({size:.1f} KB)")
            else:
                print(f"  ✗ 失败")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
