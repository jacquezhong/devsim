// 带场板的高压二极管 - 独立区域版
// 场板长度: 8.0μm

// 参数 (单位: cm)
L_device = 0.005;
L_pplus  = 0.0005;
H_n      = 0.002;
H_pplus  = 0.0002;
L_fp_total = 0.0013;
T_ox        = 2e-05;
T_fp        = 5e-05;

lc1 = 1e-05;
lc2 = 5e-05;

// =============================
// 区域1: P+区 (左下角)
// =============================
Point(1) = {0, 0, 0, lc1};
Point(2) = {L_pplus, 0, 0, lc1};
Point(3) = {L_pplus, H_pplus, 0, lc1};
Point(4) = {0, H_pplus, 0, lc1};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// =============================
// 区域2: N区 (从P+区右侧到器件右边界)
// =============================
Point(5) = {L_device, 0, 0, lc2};
Point(6) = {L_device, H_n, 0, lc2};
Point(7) = {L_pplus, H_n, 0, lc2};
// Point 3 已经定义

Line(5) = {2, 5};
Line(6) = {5, 6};
Line(7) = {6, 7};
Line(8) = {7, 3};

Curve Loop(2) = {5, 6, 7, 8, -2};  // -2 是 Line 2 的反向
Plane Surface(2) = {2};

// =============================
// 区域3: N区上部 (P+区上方到N区高度)
// =============================
Point(8) = {0, H_n, 0, lc2};
// Point 4 和 Point 3 和 Point 7 已经定义

Line(9) = {4, 8};
Line(10) = {8, 7};
// Line 8: 7->3, Line 3: 3->4

Curve Loop(3) = {9, 10, 8, 3};
Plane Surface(3) = {3};

// =============================
// 区域4: 场板
// =============================
Point(9)  = {0, H_n + T_ox, 0, lc1};
Point(10) = {L_fp_total, H_n + T_ox, 0, lc1};
Point(11) = {L_fp_total, H_n + T_ox + T_fp, 0, lc1};
Point(12) = {0, H_n + T_ox + T_fp, 0, lc1};

Line(11) = {9, 10};
Line(12) = {10, 11};
Line(13) = {11, 12};
Line(14) = {12, 9};

Curve Loop(4) = {11, 12, 13, 14};
Plane Surface(4) = {4};

// =============================
// 物理组
// =============================
Physical Curve("anode") = {1};
Physical Curve("cathode") = {6};
Physical Curve("field_plate") = {12};

Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2, 3};
Physical Surface("fieldplate_metal") = {4};

// 网格控制
Mesh.CharacteristicLengthMin = 0.05e-4;
Mesh.CharacteristicLengthMax = 2.0e-4;
