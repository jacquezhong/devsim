#!/usr/bin/env python3
"""
修复版场板二极管网格 - 带field_plate contact（Gmsh几何已修复）
关键设计：field_plate contact是N区边界的一部分
"""
import subprocess
import os

def generate_mesh(l_fp_um, filename):
    """生成带场板的二极管网格 - 修复版"""
    
    # 几何参数 (cm)
    L_device = 50e-4
    L_pplus = 5e-4
    H_pplus = 2e-4
    H_n = 20e-4
    L_fp = L_pplus + l_fp_um * 1e-4  # 场板总长度
    t_ox = 0.2e-4  # 氧化层厚度
    t_fp = 0.5e-4  # 场板厚度
    
    geo = f'''// 场板二极管 - L_fp={l_fp_um}um (修复版)
// 关键设计：field_plate contact是N区边界的一部分
L = {L_device}; Lp = {L_pplus}; Hp = {H_pplus}; Hn = {H_n};
Lf = {L_fp}; tox = {t_ox}; tfp = {t_fp};
lc1 = 0.1e-4; lc2 = 0.5e-4;

// ===== N区（硅）- 精确定义边界点 =====
Point(1) = {{0, 0, 0, lc1}};        // N区左下
Point(2) = {{L, 0, 0, lc2}};        // N区右下  
Point(3) = {{L, Hn, 0, lc2}};       // N区右上
Point(4) = {{Lf, Hn, 0, lc1}};      // N区上：场板右边缘（关键分割点）
Point(5) = {{Lp, Hn, 0, lc2}};      // N区上：P+边缘投影（关键分割点）
Point(6) = {{0, Hn, 0, lc1}};       // N区左上

// N区边界线（顶部分为3段，其中中段是field_plate contact）
Line(1) = {{1, 2}};      // 底部 - anode contact
Line(2) = {{2, 3}};      // 右侧 - cathode contact
Line(3) = {{3, 4}};      // 顶部右段（x: Lf -> L）
Line(4) = {{4, 5}};      // 顶部中段（x: Lp -> Lf）- field_plate contact ⭐
Line(5) = {{5, 6}};      // 顶部左段（x: 0 -> Lp）
Line(6) = {{6, 1}};      // 左侧

// N区面（闭合loop）
Curve Loop(1) = {{1, 2, 3, 4, 5, 6}};
Plane Surface(1) = {{1}};

// ===== 场板金属区域（在N区上方，有氧化层间隙）=====
Point(7) = {{Lf, Hn+tox, 0, lc1}};           // 场板右下
Point(8) = {{Lf, Hn+tox+tfp, 0, lc1}};       // 场板右上
Point(9) = {{0, Hn+tox+tfp, 0, lc1}};        // 场板左上
Point(10) = {{0, Hn+tox, 0, lc1}};           // 场板左下

// 场板边界线（完全独立，不与N区共享点）
Line(7) = {{7, 8}};      // 右侧
Line(8) = {{8, 9}};      // 顶部
Line(9) = {{9, 10}};     // 左侧
Line(10) = {{10, 7}};    // 底部

// 场板面
Curve Loop(2) = {{7, 8, 9, 10}};
Plane Surface(2) = {{2}};

// 物理组
Physical Curve("anode") = {{1}};        // N区底部
Physical Curve("cathode") = {{2}};      // N区右侧
Physical Curve("field_plate") = {{4}};  // N区顶部中段 ⭐
Physical Surface("ndrift") = {{1}};
Physical Surface("fieldplate_metal") = {{2}};
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
            print(f"✓ L={l_fp}um 网格生成成功")
        else:
            print(f"✗ L={l_fp}um 失败")
