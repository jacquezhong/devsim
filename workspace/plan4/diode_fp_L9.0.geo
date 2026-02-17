// ============================================================
// 带场板的高压二极管 - 2D截面 (OpenCASCADE版)
// 场板长度: 9.0μm, 绝缘层厚度: 0.2μm
// ============================================================

SetFactory("OpenCASCADE");

// --- 几何参数 (单位: cm) ---
L_device = 0.005;
L_pplus  = 0.0005;
H_n      = 0.002;
H_pplus  = 0.0002;
L_fp_total = 0.0014000000000000002;
T_ox        = 2e-05;
T_fp        = 5e-05;
H_air       = 0.0005;

// 网格控制参数
Mesh_Junction = 5e-06;
Mesh_FP_Edge  = 5e-06;
Mesh_Normal   = 2e-05;
Mesh_Coarse   = 0.0001;

// ============================================================
// 使用OpenCASCADE的矩形创建功能
// ============================================================

// 1. P+区 (左下角矩形)
pplus = news;
Rectangle(pplus) = {0, 0, 0, L_pplus, H_pplus};

// 2. N区漂移区 (底部大矩形，P+区右侧)
ndrift = news;
Rectangle(ndrift) = {L_pplus, 0, 0, L_device - L_pplus, H_n};

// 3. N区上部 (P+区上方)
nupper = news;
Rectangle(nupper) = {0, H_pplus, 0, L_pplus, H_n - H_pplus};

// 4. 场板金属 (位于器件上方)
fieldplate = news;
Rectangle(fieldplate) = {0, H_n + T_ox, 0, L_fp_total, T_fp};

// 5. 空气层 - 分段创建
// 空气层1: 场板上方
air1 = news;
Rectangle(air1) = {0, H_n + T_ox + T_fp, 0, L_fp_total, H_air};

// 空气层2: 场板右侧到器件右边界
air2 = news;
Rectangle(air2) = {L_fp_total, H_n, 0, L_device - L_fp_total, T_ox + T_fp + H_air};

// 空气层3: 器件上方场板下方
air3 = news;
Rectangle(air3) = {0, H_n, 0, L_device, T_ox};

// 布尔操作：合并所有空气层
air_all = news;
BooleanUnion(air_all) = { Surface{air1}; Surface{air2}; Surface{air3}; };

// --- 物理组 ---
// 找到边界曲线
Physical Curve("anode", 1) = {1};   // P+区底部
Physical Curve("cathode", 2) = {7}; // N区右侧
Physical Curve("field_plate", 3) = {14}; // 场板顶部

Physical Surface("pplus", 1) = {pplus};
Physical Surface("ndrift", 2) = {ndrift, nupper};
Physical Surface("fieldplate_metal", 3) = {fieldplate};
Physical Surface("air", 4) = {air_all};

// 设置网格尺寸控制
Field[1] = Box;
Field[1].VIn = Mesh_Junction;
Field[1].VOut = Mesh_Normal;
Field[1].XMin = 0;
Field[1].XMax = L_pplus * 2;
Field[1].YMin = 0;
Field[1].YMax = H_n;
Field[1].Thickness = L_pplus;

Field[2] = Box;
Field[2].VIn = Mesh_FP_Edge;
Field[2].VOut = Mesh_Normal;
Field[2].XMin = L_fp_total - 2e-4;
Field[2].XMax = L_fp_total + 2e-4;
Field[2].YMin = H_n;
Field[2].YMax = H_n + T_ox + T_fp + 1e-4;
Field[2].Thickness = 2e-4;

Field[3] = Min;
Field[3].FieldsList = {1, 2};
Background Field = 3;

Mesh.CharacteristicLengthMin = 0.01e-4;
Mesh.CharacteristicLengthMax = 2.0e-4;
