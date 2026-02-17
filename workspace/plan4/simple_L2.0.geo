// 超简化二极管网格 - 独立区域
// 场板长度: 2.0μm

L = 0.005;   // 50um
Lp = 0.0005;   // 5um
Hp = 0.0002;   // 2um
Ht = 0.002;   // 20um

lc1 = 1e-05;
lc2 = 5e-05;

// 区域1: P+区 - 独立的4个点
Point(1) = {0, 0, 0, lc1};
Point(2) = {Lp, 0, 0, lc1};
Point(3) = {Lp, Hp, 0, lc1};
Point(4) = {0, Hp, 0, lc1};

// 区域2: N区 - 独立的4个点
Point(5) = {0, Hp, 0, lc2};    // 与P+区顶点重合但独立
Point(6) = {Lp, Hp, 0, lc2};
Point(7) = {L, Hp, 0, lc2};
Point(8) = {L, Ht, 0, lc2};
Point(9) = {Lp, Ht, 0, lc2};
Point(10) = {0, Ht, 0, lc2};

// P+区线
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// N区线
Line(5) = {5, 6};
Line(6) = {6, 7};
Line(7) = {7, 8};
Line(8) = {8, 9};
Line(9) = {9, 10};
Line(10) = {10, 5};

// 面
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

Curve Loop(2) = {5, 6, 7, 8, 9, 10};
Plane Surface(2) = {2};

// 物理组
Physical Curve("anode") = {1};
Physical Curve("cathode") = {7};
Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2};

Mesh.CharacteristicLengthMax = 1e-4;
