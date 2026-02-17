// ============================================================
// 带场板的高压二极管 - 2D截面
// 场板长度: 4μm, 绝缘层厚度: 0.2μm
// ============================================================

// --- 几何参数 (单位: cm) ---
L_device = 0.005;
L_pplus  = 0.0005;
H_n      = 0.002;
H_pplus  = 0.0002;

// 场板参数
L_fp_extend = 0.0004;
T_ox        = 2e-05;
T_fp        = 5e-05;
H_air       = 0.0005;

// 计算场板总长度
L_fp_total = L_pplus + L_fp_extend;

// 网格控制参数
Mesh_Junction = 5e-06;
Mesh_FP_Edge  = 5e-06;
Mesh_Normal   = 2e-05;
Mesh_Coarse   = 0.0001;

// --- 定义关键点 ---
// P+区 (阳极)
Point(1) = {0, 0, 0, Mesh_Junction};
Point(2) = {L_pplus, 0, 0, Mesh_Junction};
Point(3) = {L_pplus, H_pplus, 0, Mesh_Junction};
Point(4) = {0, H_pplus, 0, Mesh_Junction};

// N区 (漂移区)
Point(5) = {L_device, 0, 0, Mesh_Normal};
Point(6) = {L_device, H_n, 0, Mesh_Normal};
Point(7) = {0, H_n, 0, Mesh_Normal};

// 绝缘层 (Oxide)
Point(8) = {0, H_n + T_ox, 0, Mesh_Normal};
Point(9) = {L_device, H_n + T_ox, 0, Mesh_Normal};

// 场板 (Field Plate)
Point(10) = {0, H_n + T_ox, 0, Mesh_FP_Edge};
Point(11) = {L_fp_total, H_n + T_ox, 0, Mesh_FP_Edge};
Point(12) = {L_fp_total, H_n + T_ox + T_fp, 0, Mesh_FP_Edge};
Point(13) = {0, H_n + T_ox + T_fp, 0, Mesh_FP_Edge};

// 空气层
Point(14) = {0, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse};
Point(15) = {L_device, H_n + T_ox + T_fp + H_air, 0, Mesh_Coarse};

// --- 定义线 (Line) ---
// P+区边界
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// N区边界
Line(5) = {2, 5};
Line(6) = {5, 6};
Line(7) = {6, 7};
Line(8) = {7, 4};
Line(9) = {3, 6};

// 绝缘层边界
Line(10) = {8, 9};
Line(11) = {9, 6};
Line(12) = {7, 8};

// 场板边界
Line(13) = {10, 11};
Line(14) = {11, 12};
Line(15) = {12, 13};
Line(16) = {13, 10};

// 空气层边界
Line(17) = {13, 14};
Line(18) = {14, 15};
Line(19) = {15, 12};
Line(20) = {15, 9};

// --- 定义线环和面 ---
// P+区
Line Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// N区
Line Loop(2) = {5, 6, -9, -2};
Plane Surface(2) = {2};

// 绝缘层
Line Loop(3) = {10, -11, -7, -6, 9, 3, -8, 12};
Plane Surface(3) = {3};

// 场板
Line Loop(4) = {13, 14, 15, 16};
Plane Surface(4) = {4};

// 空气层 (上)
Line Loop(5) = {15, 17, 18, 19};
Plane Surface(5) = {5};

// 空气层 (右侧)
Line Loop(6) = {10, 20, -18, -17, -16, -13, -14, -19};
Plane Surface(6) = {6};

// --- 物理组 ---
Physical Line("anode") = {1};
Physical Line("cathode") = {6};
Physical Line("field_plate") = {15};
Physical Line("oxide_interface") = {10};

Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2};
Physical Surface("oxide") = {3};
Physical Surface("fieldplate_metal") = {4};
Physical Surface("air") = {5, 6};
