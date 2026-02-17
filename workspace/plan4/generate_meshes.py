#!/usr/bin/env python3
"""
场板二极管网格生成脚本
生成不同场板长度的Gmsh网格
"""
import subprocess
import os

def generate_fp_geo(l_fp_um, t_ox_um, filename):
    """生成特定场板参数的Gmsh脚本"""
    
    # 几何参数 (单位: cm)
    L_device = 50e-4        # 器件长度: 50μm
    L_pplus  = 5e-4         # P+区宽度: 5μm
    H_n      = 20e-4        # N区高度: 20μm
    H_pplus  = 2e-4         # P+区高度: 2μm
    
    # 场板参数
    L_fp_extend = l_fp_um * 1e-4  # 场板超出P+区的长度 (cm)
    T_ox        = t_ox_um * 1e-4  # 绝缘层厚度 (cm)
    T_fp        = 0.5e-4          # 场板厚度: 0.5μm
    H_air       = 5e-4            # 空气层高度: 5μm
    
    # 计算场板总长度
    L_fp_total = L_pplus + L_fp_extend
    
    # 网格控制参数
    Mesh_Junction = 0.05e-4    # 结区细密网格: 50nm
    Mesh_FP_Edge  = 0.05e-4    # 场板边缘细密: 50nm
    Mesh_Normal   = 0.2e-4     # 正常网格: 200nm
    Mesh_Coarse   = 1.0e-4     # 粗网格: 1μm
    
    geo_content = f"""// ============================================================
// 带场板的高压二极管 - 2D截面
// 场板长度: {l_fp_um}μm, 绝缘层厚度: {t_ox_um}μm
// ============================================================

// --- 几何参数 (单位: cm) ---
L_device = {L_device};
L_pplus  = {L_pplus};
H_n      = {H_n};
H_pplus  = {H_pplus};

// 场板参数
L_fp_extend = {L_fp_extend};
T_ox        = {T_ox};
T_fp        = {T_fp};
H_air       = {H_air};

// 计算场板总长度
L_fp_total = L_pplus + L_fp_extend;

// 网格控制参数
Mesh_Junction = {Mesh_Junction};
Mesh_FP_Edge  = {Mesh_FP_Edge};
Mesh_Normal   = {Mesh_Normal};
Mesh_Coarse   = {Mesh_Coarse};

// --- 定义关键点 ---
// P+区 (阳极)
Point(1) = {{0, 0, 0, Mesh_Junction}};
Point(2) = {{L_pplus, 0, 0, Mesh_Junction}};
Point(3) = {{L_pplus, H_pplus, 0, Mesh_Junction}};
Point(4) = {{0, H_pplus, 0, Mesh_Junction}};

// N区 (漂移区)
Point(5) = {{L_device, 0, 0, Mesh_Normal}};
Point(6) = {{L_device, H_n, 0, Mesh_Normal}};
Point(7) = {{0, H_n, 0, Mesh_Normal}};

// 绝缘层 (Oxide)
Point(8) = {{0, H_n + T_ox, 0, Mesh_Normal}};
Point(9) = {{L_device, H_n + T_ox, 0, Mesh_Normal}};

// 场板 (Field Plate)
Point(10) = {{0, H_n + T_ox, 0, Mesh_FP_Edge}};
Point(11) = {{L_fp_total, H_n + T_ox, 0, Mesh_FP_Edge}};
Point(12) = {{L_fp_total, H_n + T_ox + T_fp, 0, Mesh_FP_Edge}};
Point(13) = {{0, H_n + T_ox + T_fp, 0, Mesh_FP_Edge}};

// 空气层
Point(14) = {{0, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse}};
Point(15) = {{L_device, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse}};

// --- 定义线 (Line) ---
// P+区边界
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

// N区边界
Line(5) = {{2, 5}};
Line(6) = {{5, 6}};
Line(7) = {{6, 7}};
Line(8) = {{7, 4}};
Line(9) = {{3, 6}};

// 绝缘层边界
Line(10) = {{8, 9}};
Line(11) = {{9, 6}};
Line(12) = {{7, 8}};

// 场板边界
Line(13) = {{10, 11}};
Line(14) = {{11, 12}};
Line(15) = {{12, 13}};
Line(16) = {{13, 10}};

// 空气层边界
Line(17) = {{13, 14}};
Line(18) = {{14, 15}};
Line(19) = {{15, 12}};
Line(20) = {{15, 9}};

// --- 定义线环和面 ---
// P+区
Line Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};

// N区
Line Loop(2) = {{5, 6, -9, -2}};
Plane Surface(2) = {{2}};

// 绝缘层
Line Loop(3) = {{10, -11, -7, -6, 9, 3, -8, 12}};
Plane Surface(3) = {{3}};

// 场板
Line Loop(4) = {{13, 14, 15, 16}};
Plane Surface(4) = {{4}};

// 空气层 (上)
Line Loop(5) = {{15, 17, 18, 19}};
Plane Surface(5) = {{5}};

// 空气层 (右侧)
Line Loop(6) = {{10, 20, -18, -17, -16, -13, -14, -19}};
Plane Surface(6) = {{6}};

// --- 物理组 ---
Physical Line("anode") = {{1}};
Physical Line("cathode") = {{6}};
Physical Line("field_plate") = {{15}};
Physical Line("oxide_interface") = {{10}};

Physical Surface("pplus") = {{1}};
Physical Surface("ndrift") = {{2}};
Physical Surface("oxide") = {{3}};
Physical Surface("fieldplate_metal") = {{4}};
Physical Surface("air") = {{5, 6}};
"""
    
    with open(filename, 'w') as f:
        f.write(geo_content)
    
    return filename


def main():
    """批量生成不同场板长度的网格"""
    
    # 切换到plan4目录
    os.chdir('/Users/lihengzhong/Documents/repo/devsim/workspace/plan4')
    
    # 场板长度列表 (μm)
    L_fp_values = [2, 4, 6, 8, 10]
    t_ox = 0.2  # 绝缘层厚度 (μm)
    
    print("=" * 60)
    print("场板二极管网格生成")
    print("=" * 60)
    
    for l_fp in L_fp_values:
        geo_file = f"diode_fp_L{l_fp}.geo"
        msh_file = f"diode_fp_L{l_fp}.msh"
        
        print(f"\n生成场板长度 L_fp = {l_fp} μm 的网格...")
        
        # 生成geo文件
        generate_fp_geo(l_fp, t_ox, geo_file)
        print(f"  ✓ 创建 {geo_file}")
        
        # 生成msh文件
        try:
            result = subprocess.run(
                ['gmsh', geo_file, '-2', '-o', msh_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"  ✓ 生成 {msh_file}")
            else:
                print(f"  ✗ 生成失败: {result.stderr}")
        except FileNotFoundError:
            print(f"  ✗ 未找到gmsh命令，请安装Gmsh")
            break
        except subprocess.TimeoutExpired:
            print(f"  ✗ 生成超时")
            break
    
    print("\n" + "=" * 60)
    print("网格生成完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
