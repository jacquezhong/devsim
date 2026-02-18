#!/usr/bin/env python3
"""
完整版场板二极管网格 - 带P+区、N区、场板金属区，以及3个contact
"""
import subprocess
import os

def generate_mesh(l_fp_um, filename):
    """生成完整的场板二极管网格（含P+区）"""
    
    # 几何参数 (cm)
    L_device = 50e-4
    L_pplus = 5e-4
    H_pplus = 2e-4
    H_n = 20e-4
    L_fp = L_pplus + l_fp_um * 1e-4
    t_ox = 0.2e-4
    t_fp = 0.5e-4
    
    geo = f'''// 场板二极管 - L_fp={l_fp_um}um (完整版)
L = {L_device}; Lp = {L_pplus}; Hp = {H_pplus}; Hn = {H_n};
Lf = {L_fp}; tox = {t_ox}; tfp = {t_fp};
lc1 = 0.1e-4; lc2 = 0.5e-4;

// P+区
Point(1) = {{0, 0, 0, lc1}};
Point(2) = {{Lp, 0, 0, lc1}};
Point(3) = {{Lp, Hp, 0, lc1}};
Point(4) = {{0, Hp, 0, lc1}};

Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

Curve Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};

// N区
Point(5) = {{L, 0, 0, lc2}};
Point(6) = {{L, Hn, 0, lc2}};
Point(7) = {{Lf, Hn, 0, lc1}};
Point(8) = {{Lp, Hn, 0, lc2}};

Line(5) = {{2, 5}};
Line(6) = {{5, 6}};
Line(7) = {{6, 7}};
Line(8) = {{7, 8}};
Line(9) = {{8, 3}};

Curve Loop(2) = {{5, 6, 7, 8, 9, -2}};
Plane Surface(2) = {{2}};

// 场板金属
Point(9) = {{Lf, Hn+tox, 0, lc1}};
Point(10) = {{Lf, Hn+tox+tfp, 0, lc1}};
Point(11) = {{0, Hn+tox+tfp, 0, lc1}};
Point(12) = {{0, Hn+tox, 0, lc1}};

Line(10) = {{7, 9}};
Line(11) = {{9, 10}};
Line(12) = {{10, 11}};
Line(13) = {{11, 12}};
Line(14) = {{12, 7}};

Curve Loop(3) = {{10, 11, 12, 13, 14}};
Plane Surface(3) = {{3}};

// 物理组
Physical Curve("anode") = {{1}};
Physical Curve("cathode") = {{6}};
Physical Curve("field_plate") = {{8}};
Physical Surface("pplus") = {{1}};
Physical Surface("ndrift") = {{2}};
Physical Surface("fieldplate_metal") = {{3}};
'''
    
    with open(filename, 'w') as f:
        f.write(geo)
    
    msh_file = filename.replace('.geo', '.msh')
    result = subprocess.run(['gmsh', filename, '-2', '-o', msh_file, '-format', 'msh22'], 
                           capture_output=True, timeout=60)
    return os.path.exists(msh_file)

if __name__ == '__main__':
    os.chdir('/Users/lihengzhong/Documents/repo/devsim/workspace/plan4')
    
    for l_fp in [2.0, 4.0, 6.0, 8.0, 10.0]:
        geo_file = f"fp_L{l_fp}.geo"
        if generate_mesh(l_fp, geo_file):
            print(f"✓ L={l_fp}um 完整网格生成成功")
        else:
            print(f"✗ L={l_fp}um 失败")
