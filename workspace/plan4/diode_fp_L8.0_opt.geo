// 优化的场板二极管网格 - 计算效率优先
// 场板长度: 8.0μm

// 参数 (单位: cm)
L_device = 0.005;
L_pplus  = 0.0005;
H_n      = 0.002;
H_pplus  = 0.0002;
L_fp_total = 0.0013;
T_ox        = 2e-05;

// 优化的网格尺寸 - 粗网格提高速度
lc_fine   = 1e-05;   // 100nm - 结区
lc_normal = 5e-05;     // 500nm - 正常区域
lc_coarse = 0.0002;     // 2μm - 远处

// =============================
// 点定义 - 最小化数量
// =============================
// P+区 (左下角) - 4个点
Point(1) = {0, 0, 0, lc_fine};
Point(2) = {L_pplus, 0, 0, lc_fine};
Point(3) = {L_pplus, H_pplus, 0, lc_fine};
Point(4) = {0, H_pplus, 0, lc_fine};

// N区 - 简化表示
Point(5) = {L_device, 0, 0, lc_normal};
Point(6) = {L_device, H_n, 0, lc_coarse};
Point(7) = {L_fp_total, H_n, 0, lc_normal};
Point(8) = {0, H_n, 0, lc_normal};

// 场板位置 (仅作为边界标记)
Point(9) = {L_fp_total, H_n + T_ox, 0, lc_fine};

// =============================
// 线定义
// =============================
// P+区边界
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// N区边界 (简化)
Line(5) = {2, 5};
Line(6) = {5, 6};
Line(7) = {6, 7};
Line(8) = {7, 3};
Line(9) = {3, 8};
Line(10) = {8, 4};

// =============================
// 面定义
// =============================
// P+区
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// N区 (合并为一个区域)
Curve Loop(2) = {5, 6, 7, 8, -2};
Plane Surface(2) = {2};

// N区左侧上部
Curve Loop(3) = {9, 10, -3, 8};
Plane Surface(3) = {3};

// =============================
// 物理组 - 简化
// =============================
Physical Curve("anode") = {1};
Physical Curve("cathode") = {6};
Physical Curve("field_plate_edge") = {7};  // 场板边缘用于电场计算

Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2, 3};

// 网格控制 - 禁用过于细密的网格
Mesh.CharacteristicLengthMin = 0.05e-4;
Mesh.CharacteristicLengthMax = 3.0e-4;

// 优化选项
Mesh.Algorithm = 6;  // Frontal-Delaunay (更适合2D)
Mesh.RecombineAll = 0;  // 禁用四边形网格，使用三角形
