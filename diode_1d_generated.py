#!/usr/bin/env python3
"""
基于描述生成的一维二极管仿真代码

根据 README 中的描述实现，不参考原代码：
- 创建一维网格，在结区加密
- 设置硅材料参数
- 定义阶跃掺杂分布
- 求解泊松方程获得初始电势
- 加入漂移扩散方程
- 从0V扫描至目标电压，记录电流
"""

import devsim
from devsim.python_packages import simple_physics
from devsim.python_packages.model_create import CreateSolution, CreateNodeModel

# 参数设置 (来自README描述)
DEVICE = "MyDevice"
REGION = "MyRegion"
device_length = 1e-5  # 10 μm
junction_position = 0.5e-5  # 5 μm
p_doping = 1e18  # p区掺杂
n_doping = 1e18  # n区掺杂
temperature = 300  # K
max_voltage = 0.5  # V
voltage_step = 0.1  # V

# 1. 创建一维网格（结区加密）
devsim.create_1d_mesh(mesh="dio")
devsim.add_1d_mesh_line(mesh="dio", pos=0, ps=1e-7, tag="top")
devsim.add_1d_mesh_line(mesh="dio", pos=junction_position, ps=1e-9, tag="mid")  # 结区加密
devsim.add_1d_mesh_line(mesh="dio", pos=device_length, ps=1e-7, tag="bot")
devsim.add_1d_contact(mesh="dio", name="top", tag="top", material="metal")
devsim.add_1d_contact(mesh="dio", name="bot", tag="bot", material="metal")
devsim.add_1d_region(mesh="dio", material="Si", region=REGION, tag1="top", tag2="bot")
devsim.finalize_mesh(mesh="dio")
devsim.create_device(mesh="dio", device=DEVICE)

# 2. 设置硅材料参数
simple_physics.SetSiliconParameters(DEVICE, REGION, temperature)

# 3. 定义阶跃掺杂分布
# p区: x < junction_position
CreateNodeModel(DEVICE, REGION, "Acceptors", f"{p_doping}*step({junction_position}-x)")
# n区: x >= junction_position  
CreateNodeModel(DEVICE, REGION, "Donors", f"{n_doping}*step(x-{junction_position})")
CreateNodeModel(DEVICE, REGION, "NetDoping", "Donors-Acceptors")

# 4. 求解泊松方程（初始电势）
CreateSolution(DEVICE, REGION, "Potential")
simple_physics.CreateSiliconPotentialOnly(DEVICE, REGION)

for contact in devsim.get_contact_list(device=DEVICE):
    devsim.set_parameter(device=DEVICE, name=simple_physics.GetContactBiasName(contact), value=0.0)
    simple_physics.CreateSiliconPotentialOnlyContact(DEVICE, REGION, contact)

devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)

# 5. 加入漂移扩散方程
CreateSolution(DEVICE, REGION, "Electrons")
CreateSolution(DEVICE, REGION, "Holes")
devsim.set_node_values(device=DEVICE, region=REGION, name="Electrons", init_from="IntrinsicElectrons")
devsim.set_node_values(device=DEVICE, region=REGION, name="Holes", init_from="IntrinsicHoles")
simple_physics.CreateSiliconDriftDiffusion(DEVICE, REGION)

for contact in devsim.get_contact_list(device=DEVICE):
    simple_physics.CreateSiliconDriftDiffusionAtContact(DEVICE, REGION, contact)

devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)

# 6. 从0V扫描至目标电压，记录电流
v = 0.0
while v <= max_voltage + voltage_step/2:
    devsim.set_parameter(device=DEVICE, name=simple_physics.GetContactBiasName("top"), value=v)
    devsim.solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
    simple_physics.PrintCurrents(DEVICE, "top")
    simple_physics.PrintCurrents(DEVICE, "bot")
    v += voltage_step

# 输出结果
devsim.write_devices(file="diode_1d_generated.dat", type="tecplot")
print("\n仿真完成！")
