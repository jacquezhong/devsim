#!/usr/bin/env python3
"""
优化的场板二极管网格生成脚本
减少网格数量，提高计算效率
"""
import subprocess
import os

def generate_optimized_fp_geo(l_fp_um, t_ox_um, filename):
    """生成优化的Gmsh脚本 - 减少网格数量"""
    
    # 几何参数 (单位: cm)
    L_device = 50e-4        # 器件长度: 50μm
    L_pplus  = 5e-4         # P+区宽度: 5μm
    H_n      = 20e-4        # N区高度: 20μm
    H_pplus  = 2e-4         # P+区高度: 2μm
    
    # 场板参数
    L_fp_extend = l_fp_um * 1e-4  # 场板超出P+区的长度 (cm)
    T_ox        = t_ox_um * 1e-4  # 绝缘层厚度 (cm)
    
    # 计算场板总长度
    L_fp_total = L_pplus + L_fp_extend
    
    # 优化的网格控制参数 - 比原来粗2-5倍
    Mesh_Junction = 0.1e-4     # 结区网格: 100nm (原为50nm)
    Mesh_Normal   = 0.5e-4     # 正常网格: 500nm (原为200nm)
    Mesh_Coarse   = 2.0e-4     # 粗网格: 2μm (原为1μm)
    
    geo_content = f"""// 优化的场板二极管网格 - 计算效率优先
// 场板长度: {l_fp_um}μm

// 参数 (单位: cm)
L_device = {L_device};
L_pplus  = {L_pplus};
H_n      = {H_n};
H_pplus  = {H_pplus};
L_fp_total = {L_fp_total};
T_ox        = {T_ox};

// 优化的网格尺寸 - 粗网格提高速度
lc_fine   = {Mesh_Junction};   // 100nm - 结区
lc_normal = {Mesh_Normal};     // 500nm - 正常区域
lc_coarse = {Mesh_Coarse};     // 2μm - 远处

// =============================
// 点定义 - 最小化数量
// =============================
// P+区 (左下角) - 4个点
Point(1) = {{0, 0, 0, lc_fine}};
Point(2) = {{L_pplus, 0, 0, lc_fine}};
Point(3) = {{L_pplus, H_pplus, 0, lc_fine}};
Point(4) = {{0, H_pplus, 0, lc_fine}};

// N区 - 简化表示
Point(5) = {{L_device, 0, 0, lc_normal}};
Point(6) = {{L_device, H_n, 0, lc_coarse}};
Point(7) = {{L_fp_total, H_n, 0, lc_normal}};
Point(8) = {{0, H_n, 0, lc_normal}};

// 场板位置 (仅作为边界标记)
Point(9) = {{L_fp_total, H_n + T_ox, 0, lc_fine}};

// =============================
// 线定义
// =============================
// P+区边界
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

// N区边界 (简化)
Line(5) = {{2, 5}};
Line(6) = {{5, 6}};
Line(7) = {{6, 7}};
Line(8) = {{7, 3}};
Line(9) = {{3, 8}};
Line(10) = {{8, 4}};

// =============================
// 面定义
// =============================
// P+区
Curve Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};

// N区 (合并为一个区域)
Curve Loop(2) = {{5, 6, 7, 8, -2}};
Plane Surface(2) = {{2}};

// N区左侧上部
Curve Loop(3) = {{9, 10, -3, 8}};
Plane Surface(3) = {{3}};

// =============================
// 物理组 - 简化
// =============================
Physical Curve("anode") = {{1}};
Physical Curve("cathode") = {{6}};
Physical Curve("field_plate_edge") = {{7}};  // 场板边缘用于电场计算

Physical Surface("pplus") = {{1}};
Physical Surface("ndrift") = {{2, 3}};

// 网格控制 - 禁用过于细密的网格
Mesh.CharacteristicLengthMin = 0.05e-4;
Mesh.CharacteristicLengthMax = 3.0e-4;

// 优化选项
Mesh.Algorithm = 6;  // Frontal-Delaunay (更适合2D)
Mesh.RecombineAll = 0;  // 禁用四边形网格，使用三角形
"""
    
    with open(filename, 'w') as f:
        f.write(geo_content)
    
    return filename


def main():
    """批量生成优化的网格"""
    
    os.chdir('/Users/lihengzhong/Documents/repo/devsim/workspace/plan4')
    
    # 场板长度列表 - 5个关键值
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    t_ox = 0.2  # 绝缘层厚度 (μm)
    
    print("=" * 60)
    print("生成优化的场板二极管网格")
    print("=" * 60)
    print("优化策略:")
    print("  - 结区网格: 50nm → 100nm")
    print("  - 正常网格: 200nm → 500nm")  
    print("  - 远处网格: 1μm → 2μm")
    print("  - 去掉场板内部和空气层")
    print("  - 目标节点数: ~3,000-5,000")
    print("=" * 60)
    
    success_count = 0
    
    for l_fp in L_fp_values:
        geo_file = f"diode_fp_L{l_fp}_opt.geo"
        msh_file = f"diode_fp_L{l_fp}_opt.msh"
        
        print(f"\n生成场板长度 L_fp = {l_fp} μm 的优化网格...")
        
        # 生成geo文件
        generate_optimized_fp_geo(l_fp, t_ox, geo_file)
        print(f"  ✓ 创建 {geo_file}")
        
        # 生成msh文件
        try:
            result = subprocess.run(
                ['gmsh', geo_file, '-2', '-o', msh_file, '-format', 'msh22'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and os.path.exists(msh_file):
                file_size = os.path.getsize(msh_file)
                print(f"  ✓ 生成 {msh_file} ({file_size/1024:.1f} KB)")
                success_count += 1
            else:
                print(f"  ✗ 失败: {result.stderr[:150]}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print(f"网格生成完成: {success_count}/{len(L_fp_values)} 成功")
    print("=" * 60)
    
    if success_count > 0:
        print("\n生成的优化网格文件:")
        for l_fp in L_fp_values:
            msh_file = f"diode_fp_L{l_fp}_opt.msh"
            if os.path.exists(msh_file):
                size = os.path.getsize(msh_file) / 1024
                print(f"  - {msh_file} ({size:.1f} KB)")
        
        print("\n与原始网格对比:")
        print("  原始: ~1,400 KB, ~13,000节点")
        print("  优化: 预计 ~400 KB, ~3,000-5,000节点")
        print("  加速比: 3-5倍")


if __name__ == '__main__':
    main()
