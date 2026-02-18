#!/usr/bin/env python3
"""
简化测试：基本PN结二极管（无场板）- 使用air区域技巧
验证内置2D网格和contact是否正常工作
"""
import sys
import os
sys.path.insert(0, '/Users/lihengzhong/Documents/repo/devsim/.opencode/skills/devsim-examples')

import devsim

device_name = "test_diode"
L_device = 50.0  # μm
H_n = 20.0       # μm  
H_pplus = 2.0    # μm
L_pplus = 5.0    # μm
scale = 1e-4     # μm to cm

try:
    devsim.delete_device(device=device_name)
    devsim.delete_mesh(mesh=device_name)
except:
    pass

print("创建网格...")
devsim.create_2d_mesh(mesh=device_name)

# X方向网格线 - 包含边界air区域
devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=-1e-8, ps=1e-8)  # 左边界air
devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=0.0, ps=0.5*scale)
devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_pplus*scale, ps=0.05*scale)
devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_device*scale, ps=0.5*scale)
devsim.add_2d_mesh_line(mesh=device_name, dir="x", pos=L_device*scale+1e-8, ps=1e-8)  # 右边界air

# Y方向网格线
devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=0.0, ps=0.5*scale)
devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=H_pplus*scale, ps=0.05*scale)
devsim.add_2d_mesh_line(mesh=device_name, dir="y", pos=H_n*scale, ps=0.2*scale)

# 定义区域 - 使用air区域技巧
# P+区
devsim.add_2d_region(mesh=device_name, material="Si", region="pplus",
                    xl=0.0, xh=L_pplus*scale, yl=0.0, yh=H_pplus*scale)

# N区
devsim.add_2d_region(mesh=device_name, material="Si", region="ndrift",
                    xl=L_pplus*scale, xh=L_device*scale, yl=0.0, yh=H_n*scale)

# Air区域（用于定义边界contact）
devsim.add_2d_region(mesh=device_name, material="metal", region="air_left",
                     xl=-1e-8, xh=0.0, yl=0.0, yh=H_n*scale)
devsim.add_2d_region(mesh=device_name, material="metal", region="air_right",
                     xl=L_device*scale, xh=L_device*scale+1e-8, yl=0.0, yh=H_n*scale)

# Contact定义 - 在air区域和主区域之间
# Anode: air_left和pplus之间
devsim.add_2d_contact(mesh=device_name, name="anode", material="metal", region="pplus",
                      yl=0.0, yh=0.0, xl=0.0, xh=L_pplus*scale, bloat=1e-10)

# Cathode: air_right和ndrift之间
devsim.add_2d_contact(mesh=device_name, name="cathode", material="metal", region="ndrift",
                      xl=L_device*scale, xh=L_device*scale, 
                      yl=0.0, yh=H_n*scale, bloat=1e-10)

devsim.finalize_mesh(mesh=device_name)
devsim.create_device(mesh=device_name, device=device_name)

contacts = devsim.get_contact_list(device=device_name)
regions = devsim.get_region_list(device=device_name)
print(f"✓ 创建完成！")
print(f"  Contacts: {contacts}")
print(f"  Regions: {regions}")

if len(contacts) >= 2:
    print("\n✅ 测试通过：至少2个contact被创建")
else:
    print(f"\n❌ 测试失败：只有{len(contacts)}个contact")
