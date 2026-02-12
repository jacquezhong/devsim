# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_plot_paper_figures.py - Generate publication-quality figures matching the paper
Uses existing simulation data to create Figures 5 and 6
"""

import numpy as np
import matplotlib.pyplot as plt
import json

# Set publication style
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 150

print("Generating publication-quality figures...")

# Device parameters
LWIR_thickness = 9.0
Barrier_thickness = 4.35
VLWIR_thickness = 14.0
total_length = LWIR_thickness + Barrier_thickness + VLWIR_thickness

Eg_LWIR = 0.140
Eg_Barrier = 0.285
Eg_VLWIR = 0.091

# Load existing data
print("Loading simulation data...")

# Load potential data (equilibrium)
pot_data = {}
with open('exp_oc/JEM2025_potential_equilibrium.txt', 'r') as f:
    current_region = None
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            if 'LWIR' in line and 'Barrier' not in line:
                current_region = 'LWIR'
                pot_data['LWIR'] = {'x': [], 'V': []}
            elif 'Barrier' in line:
                current_region = 'Barrier'
                pot_data['Barrier'] = {'x': [], 'V': []}
            elif 'VLWIR' in line:
                current_region = 'VLWIR'
                pot_data['VLWIR'] = {'x': [], 'V': []}
            continue
        
        if line and current_region and current_region in pot_data:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    x = float(parts[0])
                    V = float(parts[1])
                    pot_data[current_region]['x'].append(x)
                    pot_data[current_region]['V'].append(V)
                except:
                    pass

# Load carrier data
carrier_data = {}
with open('exp_oc/JEM2025_carrier_concentrations.txt', 'r') as f:
    current_region = None
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            if 'LWIR' in line and 'Barrier' not in line:
                current_region = 'LWIR'
                carrier_data['LWIR'] = {'x': [], 'n': [], 'p': []}
            elif 'Barrier' in line:
                current_region = 'Barrier'
                carrier_data['Barrier'] = {'x': [], 'n': [], 'p': []}
            elif 'VLWIR' in line:
                current_region = 'VLWIR'
                carrier_data['VLWIR'] = {'x': [], 'n': [], 'p': []}
            continue
        
        if line and current_region and current_region in carrier_data:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    x = float(parts[0])
                    n = float(parts[1])
                    p = float(parts[2])
                    carrier_data[current_region]['x'].append(x)
                    carrier_data[current_region]['n'].append(n)
                    carrier_data[current_region]['p'].append(p)
                except:
                    pass

# Load I-V data
iv_data = {'voltage': [], 'current_top': [], 'current_bottom': []}
with open('exp_oc/JEM2025_IV_characteristics.txt', 'r') as f:
    for line in f:
        if line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                v = float(parts[0])
                jt = float(parts[1])
                jb = float(parts[2])
                iv_data['voltage'].append(v)
                iv_data['current_top'].append(abs(jt))
                iv_data['current_bottom'].append(abs(jb))
            except:
                pass

print(f"  Loaded: {sum(len(pot_data[r]['x']) for r in pot_data)} potential points")
print(f"  Loaded: {sum(len(carrier_data[r]['x']) for r in carrier_data)} carrier points")
print(f"  Loaded: {len(iv_data['voltage'])} I-V points")

# =============================================================================
# FIGURE 5: Band Diagrams (Note: Currently only V=0 data available)
# =============================================================================

print("\nGenerating Figure 5: Band Diagrams...")

# Combine all regions for band diagram
x_all = []
V_all = []
region_labels = []

for region in ['LWIR', 'Barrier', 'VLWIR']:
    if region in pot_data:
        for x, V in zip(pot_data[region]['x'], pot_data[region]['V']):
            x_all.append(x)
            V_all.append(V)
            region_labels.append(region)

x_all = np.array(x_all)
V_all = np.array(V_all)

# Convert to energy bands
Ec_all = -V_all  # Conduction band
Ev_all = np.zeros_like(Ec_all)
Ei_all = np.zeros_like(Ec_all)

# Apply bandgaps to get valence band
idx = 0
for region in ['LWIR', 'Barrier', 'VLWIR']:
    if region in pot_data:
        n_points = len(pot_data[region]['x'])
        if region == 'LWIR':
            Ev_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_LWIR
            Ei_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_LWIR/2
        elif region == 'Barrier':
            Ev_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_Barrier
            Ei_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_Barrier/2
        else:  # VLWIR
            Ev_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_VLWIR
            Ei_all[idx:idx+n_points] = Ec_all[idx:idx+n_points] - Eg_VLWIR/2
        idx += n_points

# Create Figure 5
fig, ax = plt.subplots(figsize=(10, 6))

# Plot energy bands
ax.plot(x_all, Ec_all, 'b-', linewidth=2.5, label='Conduction Band (Ec)')
ax.plot(x_all, Ev_all, 'r-', linewidth=2.5, label='Valence Band (Ev)')
ax.plot(x_all, Ei_all, 'g--', linewidth=2, label='Intrinsic Level (Ei)')

# Add region shading
ax.axvspan(0, LWIR_thickness, alpha=0.15, color='blue')
ax.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.15, color='gray')
ax.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.15, color='red')

# Add interface lines
ax.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.5, linewidth=1)
ax.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.5, linewidth=1)

# Set axis limits as specified (0-10 um, though device is 27.35 um)
ax.set_xlim(0, 10)
ax.set_xlabel('Position (µm)', fontsize=12)
ax.set_ylabel('Energy (eV)', fontsize=12)
ax.set_title('Figure 5: Band Diagram at Equilibrium (V=0V, 100K)\n[Note: Paper shows V=0, +0.1V, -0.1V]',
             fontsize=13, fontweight='bold')
ax.legend(loc='upper right', framealpha=0.9)
ax.grid(True, alpha=0.3)

# Add region labels
ax.text(LWIR_thickness/2, max(Ec_all)+0.02, 'LWIR\n(9µm)', 
        ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
ax.text(LWIR_thickness + Barrier_thickness/2, max(Ec_all)+0.02, 'Barrier\n(4.35µm)', 
        ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.7))
ax.text(min(LWIR_thickness + Barrier_thickness + 2, 9.5), max(Ec_all)+0.02, 'VLWIR\n(14µm)', 
        ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))

plt.tight_layout()
plt.savefig('exp_oc/Figure5_Band_Diagram_V0.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure5_Band_Diagram_V0.png")

# Note: To generate all 3 subplots (V=0, +0.1V, -0.1V), run:
# python exp_oc/JEM2025_generate_paper_figures.py
plt.close()

# =============================================================================
# FIGURE 6a: I-V Characteristics
# =============================================================================

print("\nGenerating Figure 6a: I-V Characteristics...")

fig, ax = plt.subplots(figsize=(10, 7))

v = np.array(iv_data['voltage'])
j = np.array(iv_data['current_top'])

# Plot simulation data
ax.semilogy(v, j, 'bo-', linewidth=2.5, markersize=8, label='Simulation (VBO=0meV)')

# Add Rule 07 lines
Rule07_VLWIR = 0.0539
Rule07_LWIR = 0.0001
ax.axhline(y=Rule07_VLWIR, color='r', linestyle='--', linewidth=2, 
           label=f'Rule 07 VLWIR (14µm) = {Rule07_VLWIR:.2e} A/cm²')
ax.axhline(y=Rule07_LWIR, color='orange', linestyle='--', linewidth=2, 
           label=f'Rule 07 LWIR (9µm) = {Rule07_LWIR:.2e} A/cm²')

# Set axis limits as specified
ax.set_xlim(-0.4, 0.4)
ax.set_ylim(1e-8, 1e-1)

ax.set_xlabel('Bias Voltage (V)', fontsize=12)
ax.set_ylabel('Dark Current Density (A/cm²)', fontsize=12)
ax.set_title('Figure 6a: I-V Characteristics at 100K\n[Note: Paper shows VBO=0, 30, 50 meV curves]',
             fontsize=13, fontweight='bold')
ax.legend(loc='lower right', framealpha=0.9)
ax.grid(True, alpha=0.3, which='both')

# Add text annotation
j_eq = j[0] if len(j) > 0 else 2.18e-17
ax.text(0, 3e-8, f'Simulation Result:\nJ = {j_eq:.2e} A/cm²\n@ V = 0V',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8), 
        fontsize=10, ha='center')

plt.tight_layout()
plt.savefig('exp_oc/Figure6a_IV_Characteristics.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure6a_IV_Characteristics.png")
plt.close()

# =============================================================================
# FIGURE 6b: Carrier Concentration
# =============================================================================

print("\nGenerating Figure 6b: Carrier Concentration...")

fig, ax = plt.subplots(figsize=(10, 7))

# Combine all regions
x_n = []
n_conc = []
x_p = []
p_conc = []

for region in ['LWIR', 'Barrier', 'VLWIR']:
    if region in carrier_data:
        for x, n, p in zip(carrier_data[region]['x'], carrier_data[region]['n'], carrier_data[region]['p']):
            x_n.append(x)
            n_conc.append(n)
            x_p.append(x)
            p_conc.append(p)

x_n = np.array(x_n)
n_conc = np.array(n_conc)
x_p = np.array(x_p)
p_conc = np.array(p_conc)

# Plot both electrons and holes on same plot
ax.semilogy(x_n, n_conc, 'b-', linewidth=2.5, label='Electrons (n)')
ax.semilogy(x_p, p_conc, 'r-', linewidth=2.5, label='Holes (p)')

# Add doping reference lines
ax.axhline(y=2.46e14, xmin=0, xmax=LWIR_thickness/20, 
           color='blue', linestyle=':', alpha=0.6, linewidth=1.5)
ax.axhline(y=5e15, xmin=LWIR_thickness/20, xmax=(LWIR_thickness+Barrier_thickness)/20,
           color='gray', linestyle=':', alpha=0.6, linewidth=1.5)
ax.axhline(y=5e14, xmin=(LWIR_thickness+Barrier_thickness)/20, xmax=1,
           color='red', linestyle=':', alpha=0.6, linewidth=1.5)

# Add region shading
ax.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')

# Add interface lines
ax.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.4, linewidth=1)
ax.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.4, linewidth=1)

# Set axis limits as specified
ax.set_xlim(0, 20)
ax.set_ylim(1e4, 1e16)

ax.set_xlabel('Position (µm)', fontsize=12)
ax.set_ylabel('Carrier Concentration (cm⁻³)', fontsize=12)
ax.set_title('Figure 6b: Carrier Concentration Distribution at Equilibrium (100K)',
             fontsize=13, fontweight='bold')
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('exp_oc/Figure6b_Carrier_Concentration.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure6b_Carrier_Concentration.png")
plt.close()

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("FIGURE GENERATION COMPLETE")
print("="*70)
print("\nGenerated figures:")
print("  ✓ Figure5_Band_Diagram_V0.png - Band diagram at equilibrium")
print("  ✓ Figure6a_IV_Characteristics.png - I-V curve with Rule 07")
print("  ✓ Figure6b_Carrier_Concentration.png - Electron and hole concentrations")
print("\nNote:")
print("  - Figure 5 shows only V=0 (equilibrium). Paper has 3 subplots: V=0, +0.1V, -0.1V")
print("  - Figure 6a shows only VBO=0. Paper has 3 curves: VBO=0, 30, 50 meV")
print("  - To generate complete data, run: python exp_oc/JEM2025_generate_paper_figures.py")
print("="*70)
