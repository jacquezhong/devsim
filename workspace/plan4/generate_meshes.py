#!/usr/bin/env python3
"""
场板二极管网格生成脚本 - 最终版
使用三个独立不重叠的区域
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
    
    # 计算场板总长度
    L_fp_total = L_pplus + L_fp_extend
    
    # 网格控制参数
    lc_fine   = 0.1e-4     # 细密网格: 1μm
    lc_normal = 0.5e-4     # 正常网格: 5μm
    
    geo_content = f"""// 带场板的高压二极管
// 场板长度: {l_fp_um}μm

// 参数 (单位: cm)
L_device = {L_device};
L_pplus  = {L_pplus};
H_n      = {H_n};
H_pplus  = {H_pplus};
L_fp_total = {L_fp_total};
T_ox        = {T_ox};
T_fp        = {T_fp};

lc1 = {lc_fine};
lc2 = {lc_normal};

// =============================
// 点定义
// =============================
// P+区: 左下角矩形
Point(1) = {{0, 0, 0, lc1}};
Point(2) = {{L_pplus, 0, 0, lc1}};
Point(3) = {{L_pplus, H_pplus, 0, lc1}};
Point(4) = {{0, H_pplus, 0, lc1}};

// N区右侧: (L_pplus, 0) 到 (L_device, H_n)
Point(5) = {{L_device, 0, 0, lc2}};
Point(6) = {{L_device, H_n, 0, lc2}};
Point(7) = {{L_pplus, H_n, 0, lc2}};

// N区左侧上部: (0, H_pplus) 到 (L_pplus, H_n)
Point(8) = {{0, H_n, 0, lc2}};

// 场板: 位于 (0, H_n+T_ox) 到 (L_fp_total, H_n+T_ox+T_fp)
Point(9)  = {{0, H_n + T_ox, 0, lc1}};
Point(10) = {{L_fp_total, H_n + T_ox, 0, lc1}};
Point(11) = {{L_fp_total, H_n + T_ox + T_fp, 0, lc1}};
Point(12) = {{0, H_n + T_ox + T_fp, 0, lc1}};

// =============================
// 线定义
// =============================
// P+区边界
Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

// N区右侧边界 (与P+区共用线2作为左边界)
Line(5) = {{2, 5}};
Line(6) = {{5, 6}};
Line(7) = {{6, 7}};
Line(8) = {{7, 3}};  // 连接到Point 3

// N区左侧上部边界 (与P+区共用线3作为下边界的一部分，Point 4到Point 3)
Line(9) = {{3, 7}};  // 注意与Line 8是同一条线但方向不同
Line(10) = {{7, 8}};
Line(11) = {{8, 4}};

// 修正：N区应该分成两个矩形
// 删除上面的，重新定义

// N区右部: Point 2 -> 5 -> 6 -> 7 -> 3 -> 2
// 但3->2是Line 2的反向，这样会有问题

// 让我重新定义所有点，确保不共用边界线
"""

    # 使用更简单的方法：不共享边界的独立矩形
    geo_content = f"""// 带场板的高压二极管 - 独立区域版
// 场板长度: {l_fp_um}μm

// 参数 (单位: cm)
L_device = {L_device};
L_pplus  = {L_pplus};
H_n      = {H_n};
H_pplus  = {H_pplus};
L_fp_total = {L_fp_total};
T_ox        = {T_ox};
T_fp        = {T_fp};

lc1 = {lc_fine};
lc2 = {lc_normal};

// =============================
// 区域1: P+区 (左下角)
// =============================
Point(1) = {{0, 0, 0, lc1}};
Point(2) = {{L_pplus, 0, 0, lc1}};
Point(3) = {{L_pplus, H_pplus, 0, lc1}};
Point(4) = {{0, H_pplus, 0, lc1}};

Line(1) = {{1, 2}};
Line(2) = {{2, 3}};
Line(3) = {{3, 4}};
Line(4) = {{4, 1}};

Curve Loop(1) = {{1, 2, 3, 4}};
Plane Surface(1) = {{1}};

// =============================
// 区域2: N区 (从P+区右侧到器件右边界)
// =============================
Point(5) = {{L_device, 0, 0, lc2}};
Point(6) = {{L_device, H_n, 0, lc2}};
Point(7) = {{L_pplus, H_n, 0, lc2}};
// Point 3 已经定义

Line(5) = {{2, 5}};
Line(6) = {{5, 6}};
Line(7) = {{6, 7}};
Line(8) = {{7, 3}};

Curve Loop(2) = {{5, 6, 7, 8, -2}};  // -2 是 Line 2 的反向
Plane Surface(2) = {{2}};

// =============================
// 区域3: N区上部 (P+区上方到N区高度)
// =============================
Point(8) = {{0, H_n, 0, lc2}};
// Point 4 和 Point 3 和 Point 7 已经定义

Line(9) = {{4, 8}};
Line(10) = {{8, 7}};
// Line 8: 7->3, Line 3: 3->4

Curve Loop(3) = {{9, 10, 8, 3}};
Plane Surface(3) = {{3}};

// =============================
// 区域4: 场板
// =============================
Point(9)  = {{0, H_n + T_ox, 0, lc1}};
Point(10) = {{L_fp_total, H_n + T_ox, 0, lc1}};
Point(11) = {{L_fp_total, H_n + T_ox + T_fp, 0, lc1}};
Point(12) = {{0, H_n + T_ox + T_fp, 0, lc1}};

Line(11) = {{9, 10}};
Line(12) = {{10, 11}};
Line(13) = {{11, 12}};
Line(14) = {{12, 9}};

Curve Loop(4) = {{11, 12, 13, 14}};
Plane Surface(4) = {{4}};

// =============================
// 物理组
// =============================
Physical Curve("anode") = {{1}};
Physical Curve("cathode") = {{6}};
Physical Curve("field_plate") = {{12}};

Physical Surface("pplus") = {{1}};
Physical Surface("ndrift") = {{2, 3}};
Physical Surface("fieldplate_metal") = {{4}};

// 网格控制
Mesh.CharacteristicLengthMin = 0.05e-4;
Mesh.CharacteristicLengthMax = 2.0e-4;
"""
    
    with open(filename, 'w') as f:
        f.write(geo_content)
    
    return filename


def main():
    """批量生成不同场板长度的网格"""
    
    os.chdir('/Users/lihengzhong/Documents/repo/devsim/workspace/plan4')
    
    # 场板长度列表 (μm) - 5个代表性点
    L_fp_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    t_ox = 0.2  # 绝缘层厚度 (μm)
    
    print("=" * 60)
    print("场板二极管网格生成 (最终版)")
    print("=" * 60)
    
    success_count = 0
    
    for l_fp in L_fp_values:
        geo_file = f"diode_fp_L{l_fp}.geo"
        msh_file = f"diode_fp_L{l_fp}.msh"
        
        print(f"\n生成场板长度 L_fp = {l_fp} μm 的网格...")
        
        generate_fp_geo(l_fp, t_ox, geo_file)
        
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
    print(f"结果: {success_count}/{len(L_fp_values)} 成功")
    print("=" * 60)


if __name__ == '__main__':
    main()
