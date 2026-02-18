// 场板二极管 - L_fp=8.0um (完整版)
L = 0.005; Lp = 0.0005; Hp = 0.0002; Hn = 0.002;
Lf = 0.0013; tox = 2e-05; tfp = 5e-05;
lc1 = 0.1e-4; lc2 = 0.5e-4;

// P+区
Point(1) = {0, 0, 0, lc1};
Point(2) = {Lp, 0, 0, lc1};
Point(3) = {Lp, Hp, 0, lc1};
Point(4) = {0, Hp, 0, lc1};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// N区
Point(5) = {L, 0, 0, lc2};
Point(6) = {L, Hn, 0, lc2};
Point(7) = {Lf, Hn, 0, lc1};
Point(8) = {Lp, Hn, 0, lc2};

Line(5) = {2, 5};
Line(6) = {5, 6};
Line(7) = {6, 7};
Line(8) = {7, 8};
Line(9) = {8, 3};

Curve Loop(2) = {5, 6, 7, 8, 9, -2};
Plane Surface(2) = {2};

// 场板金属
Point(9) = {Lf, Hn+tox, 0, lc1};
Point(10) = {Lf, Hn+tox+tfp, 0, lc1};
Point(11) = {0, Hn+tox+tfp, 0, lc1};
Point(12) = {0, Hn+tox, 0, lc1};

Line(10) = {7, 9};
Line(11) = {9, 10};
Line(12) = {10, 11};
Line(13) = {11, 12};
Line(14) = {12, 7};

Curve Loop(3) = {10, 11, 12, 13, 14};
Plane Surface(3) = {3};

// 物理组
Physical Curve("anode") = {1};
Physical Curve("cathode") = {6};
Physical Curve("field_plate") = {8};
Physical Surface("pplus") = {1};
Physical Surface("ndrift") = {2};
Physical Surface("fieldplate_metal") = {3};
