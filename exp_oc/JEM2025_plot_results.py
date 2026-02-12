# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_plot_results.py - Generate publication-quality plots from simulation data
Reproduces Figures 5 and 6 from the paper
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Set publication-quality style
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300

print("Generating publication-quality plots for JEM2025 simulation...")

# =============================================================================
# LOAD DATA
# =============================================================================

def load_potential_data(filename):
    """Load potential distribution data"""
    data = {'LWIR': {'x': [], 'V': []},
            'Barrier': {'x': [], 'V': []},
            'VLWIR': {'x': [], 'V': []}}
    
    current_region = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                if 'LWIR' in line:
                    current_region = 'LWIR'
                elif 'Barrier' in line:
                    current_region = 'Barrier'
                elif 'VLWIR' in line:
                    current_region = 'VLWIR'
                continue
            
            if line and current_region:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        x = float(parts[0])
                        V = float(parts[1])
                        data[current_region]['x'].append(x)
                        data[current_region]['V'].append(V)
                    except ValueError:
                        pass
    
    return data

def load_carrier_data(filename):
    """Load carrier concentration data"""
    data = {'LWIR': {'x': [], 'n': [], 'p': []},
            'Barrier': {'x': [], 'n': [], 'p': []},
            'VLWIR': {'x': [], 'n': [], 'p': []}}
    
    current_region = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                if 'LWIR' in line:
                    current_region = 'LWIR'
                elif 'Barrier' in line:
                    current_region = 'Barrier'
                elif 'VLWIR' in line:
                    current_region = 'VLWIR'
                continue
            
            if line and current_region:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        x = float(parts[0])
                        n = float(parts[1])
                        p = float(parts[2])
                        data[current_region]['x'].append(x)
                        data[current_region]['n'].append(n)
                        data[current_region]['p'].append(p)
                    except ValueError:
                        pass
    
    return data

def load_iv_data(filename):
    """Load I-V characteristics data"""
    voltages = []
    j_top = []
    j_bottom = []
    
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    voltages.append(float(parts[0]))
                    j_top.append(float(parts[1]))
                    j_bottom.append(float(parts[2]))
                except ValueError:
                    pass
    
    return np.array(voltages), np.array(j_top), np.array(j_bottom)

# Load all data
print("Loading simulation data...")
pot_data = load_potential_data('exp_oc/JEM2025_potential_equilibrium.txt')
carrier_data = load_carrier_data('exp_oc/JEM2025_carrier_concentrations.txt')
voltages, j_top, j_bottom = load_iv_data('exp_oc/JEM2025_IV_characteristics.txt')

print(f"  Potential data: {sum(len(pot_data[r]['x']) for r in pot_data)} points")
print(f"  Carrier data: {sum(len(carrier_data[r]['x']) for r in carrier_data)} points")
print(f"  I-V data: {len(voltages)} points")

# =============================================================================
# FIGURE 5: BAND DIAGRAM (类似论文Figure 5)
# =============================================================================

print("\nGenerating Figure 5: Band diagram...")

fig, ax = plt.subplots(figsize=(10, 6))

# Device parameters
LWIR_thickness = 9.0
Barrier_thickness = 4.35
VLWIR_thickness = 14.0
total_length = LWIR_thickness + Barrier_thickness + VLWIR_thickness

# Energy bandgaps (eV)
Eg_LWIR = 0.140
Eg_Barrier = 0.285
Eg_VLWIR = 0.091

# Convert potential to energy bands
# Ec = -q*V (relative energy, where q is positive)
# We set the reference such that Ec is negative of potential

# Combine all regions
x_all = []
Ec_all = []  # Conduction band
Ev_all = []  # Valence band
Ei_all = []  # Intrinsic Fermi level

# LWIR region
for x, V in zip(pot_data['LWIR']['x'], pot_data['LWIR']['V']):
    x_all.append(x)
    # Ec = -V (in eV, assuming q=1)
    Ec = -V
    Ec_all.append(Ec)
    Ev_all.append(Ec - Eg_LWIR)
    Ei_all.append(Ec - Eg_LWIR/2)

# Barrier region
for x, V in zip(pot_data['Barrier']['x'], pot_data['Barrier']['V']):
    x_all.append(x)
    Ec = -V
    Ec_all.append(Ec)
    Ev_all.append(Ec - Eg_Barrier)
    Ei_all.append(Ec - Eg_Barrier/2)

# VLWIR region
for x, V in zip(pot_data['VLWIR']['x'], pot_data['VLWIR']['V']):
    x_all.append(x)
    Ec = -V
    Ec_all.append(Ec)
    Ev_all.append(Ec - Eg_VLWIR)
    Ei_all.append(Ec - Eg_VLWIR/2)

x_all = np.array(x_all)
Ec_all = np.array(Ec_all)
Ev_all = np.array(Ev_all)
Ei_all = np.array(Ei_all)

# Plot energy bands
ax.plot(x_all, Ec_all, 'b-', linewidth=2, label='Conduction Band (Ec)')
ax.plot(x_all, Ev_all, 'r-', linewidth=2, label='Valence Band (Ev)')
ax.plot(x_all, Ei_all, 'g--', linewidth=1.5, label='Intrinsic Level (Ei)')

# Add region shading
ax.axvspan(0, LWIR_thickness, alpha=0.1, color='blue', label='LWIR (9 um)')
ax.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, 
           alpha=0.1, color='gray', label='Barrier (4.35 um)')
ax.axvspan(LWIR_thickness + Barrier_thickness, total_length, 
           alpha=0.1, color='red', label='VLWIR (14 um)')

# Add interface lines
ax.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.5)
ax.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.5)

ax.set_xlabel('Position (um)', fontsize=12)
ax.set_ylabel('Energy (eV)', fontsize=12)
ax.set_title('Figure 5: Band Diagram at Equilibrium (100K)', fontsize=14)
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, total_length)

# Add text annotations
ax.text(LWIR_thickness/2, max(Ec_all)+0.02, 'LWIR\n(Eg=140meV)', 
        ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax.text(LWIR_thickness + Barrier_thickness/2, max(Ec_all)+0.02, 'Barrier\n(Eg=285meV)', 
        ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
ax.text(LWIR_thickness + Barrier_thickness + VLWIR_thickness/2, max(Ec_all)+0.02, 
        'VLWIR\n(Eg=91meV)', ha='center', fontsize=9, 
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

plt.tight_layout()
plt.savefig('exp_oc/Figure5_band_diagram.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure5_band_diagram.png")

# =============================================================================
# FIGURE 6a: I-V CHARACTERISTICS (类似论文Figure 6a)
# =============================================================================

print("\nGenerating Figure 6a: I-V characteristics...")

fig, ax = plt.subplots(figsize=(8, 6))

# Use absolute value of current for log scale
j_abs = np.abs(j_top)

ax.semilogy(voltages, j_abs, 'bo-', linewidth=2, markersize=8, label='Simulation')

# Add Rule 07 reference line
Rule07_VLWIR = 0.0539
ax.axhline(y=Rule07_VLWIR, color='r', linestyle='--', linewidth=2, 
           label=f'Rule 07 VLWIR (14um) = {Rule07_VLWIR:.2e} A/cm^2')
ax.axhline(y=0.0001, color='g', linestyle='--', linewidth=2, 
           label='Rule 07 LWIR (9um) = 1e-4 A/cm^2')

ax.set_xlabel('Bias Voltage (V)', fontsize=12)
ax.set_ylabel('Dark Current Density (A/cm^2)', fontsize=12)
ax.set_title('Figure 6a: I-V Characteristics at 100K', fontsize=14)
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3, which='both')
ax.set_xlim(0, 0.5)

# Add text annotation for our result
j_eq = j_abs[0]
ax.text(0.25, j_eq*3, f'Simulation Result:\nJ = {j_eq:.2e} A/cm^2\n({Rule07_VLWIR/j_eq:.1e}x better than Rule 07)',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7), fontsize=9)

plt.tight_layout()
plt.savefig('exp_oc/Figure6a_IV_curve.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure6a_IV_curve.png")

# Linear scale version
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(voltages, j_top*1e16, 'bo-', linewidth=2, markersize=8, label='Simulation (x1e16)')
ax.set_xlabel('Bias Voltage (V)', fontsize=12)
ax.set_ylabel('Dark Current Density (x10^-16 A/cm^2)', fontsize=12)
ax.set_title('Figure 6a: I-V Characteristics (Linear Scale)', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('exp_oc/Figure6a_IV_linear.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure6a_IV_linear.png")

# =============================================================================
# FIGURE 6b: CARRIER CONCENTRATION (类似论文Figure 6b)
# =============================================================================

print("\nGenerating Figure 6b: Carrier concentration distribution...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Combine all regions for electron concentration
x_electrons = []
n_electrons = []

for region in ['LWIR', 'Barrier', 'VLWIR']:
    for x, n in zip(carrier_data[region]['x'], carrier_data[region]['n']):
        x_electrons.append(x)
        n_electrons.append(n)

x_electrons = np.array(x_electrons)
n_electrons = np.array(n_electrons)

# Plot electron concentration
ax1.semilogy(x_electrons, n_electrons, 'b-', linewidth=2, label='Electrons (n)')

# Add doping reference lines
ax1.axhline(y=2.46e14, xmin=0, xmax=LWIR_thickness/total_length, 
            color='b', linestyle='--', alpha=0.5, label='Nd (LWIR) = 2.46e14')
ax1.axhline(y=5e15, xmin=LWIR_thickness/total_length, 
            xmax=(LWIR_thickness+Barrier_thickness)/total_length,
            color='gray', linestyle='--', alpha=0.5, label='Nd (Barrier) = 5e15')
ax1.axhline(y=5e14, xmin=(LWIR_thickness+Barrier_thickness)/total_length, xmax=1,
            color='r', linestyle='--', alpha=0.5, label='Nd (VLWIR) = 5e14')

# Add region shading
ax1.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax1.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax1.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')

ax1.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.5)

ax1.set_ylabel('Electron Concentration (cm^-3)', fontsize=11)
ax1.set_title('Figure 6b: Carrier Concentration Distribution at Equilibrium', fontsize=13)
ax1.legend(loc='best', fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, total_length)
ax1.set_ylim(1e10, 1e16)

# Combine all regions for hole concentration
x_holes = []
p_holes = []

for region in ['LWIR', 'Barrier', 'VLWIR']:
    for x, p in zip(carrier_data[region]['x'], carrier_data[region]['p']):
        x_holes.append(x)
        p_holes.append(p)

x_holes = np.array(x_holes)
p_holes = np.array(p_holes)

# Plot hole concentration
ax2.semilogy(x_holes, p_holes, 'r-', linewidth=2, label='Holes (p)')

# Add region shading
ax2.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax2.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax2.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')

ax2.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.5)
ax2.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.5)

ax2.set_xlabel('Position (um)', fontsize=11)
ax2.set_ylabel('Hole Concentration (cm^-3)', fontsize=11)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, total_length)
ax2.set_ylim(1e2, 1e13)

plt.tight_layout()
plt.savefig('exp_oc/Figure6b_carrier_concentration.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/Figure6b_carrier_concentration.png")

# =============================================================================
# SUMMARY PLOT: ALL IN ONE
# =============================================================================

print("\nGenerating summary plot with all results...")

fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# (a) Band diagram
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(x_all, Ec_all, 'b-', linewidth=2, label='Conduction Band (Ec)')
ax1.plot(x_all, Ev_all, 'r-', linewidth=2, label='Valence Band (Ev)')
ax1.plot(x_all, Ei_all, 'g--', linewidth=1.5, label='Intrinsic Level (Ei)')
ax1.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax1.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax1.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')
ax1.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.5)
ax1.set_xlabel('Position (um)', fontsize=11)
ax1.set_ylabel('Energy (eV)', fontsize=11)
ax1.set_title('(a) Band Diagram at Equilibrium (100K)', fontsize=12)
ax1.legend(loc='best', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, total_length)

# (b) I-V curve (log)
ax2 = fig.add_subplot(gs[1, 0])
ax2.semilogy(voltages, j_abs, 'bo-', linewidth=2, markersize=6)
ax2.axhline(y=Rule07_VLWIR, color='r', linestyle='--', linewidth=1.5, label='Rule 07 VLWIR')
ax2.set_xlabel('Voltage (V)', fontsize=11)
ax2.set_ylabel('J (A/cm^2)', fontsize=11)
ax2.set_title('(b) I-V Characteristics (Log)', fontsize=12)
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3, which='both')

# (c) I-V curve (linear)
ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(voltages, j_top, 'bo-', linewidth=2, markersize=6)
ax3.set_xlabel('Voltage (V)', fontsize=11)
ax3.set_ylabel('J (A/cm^2)', fontsize=11)
ax3.set_title('(c) I-V Characteristics (Linear)', fontsize=12)
ax3.grid(True, alpha=0.3)

# (d) Electron concentration
ax4 = fig.add_subplot(gs[2, 0])
ax4.semilogy(x_electrons, n_electrons, 'b-', linewidth=2)
ax4.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax4.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax4.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')
ax4.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.3)
ax4.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.3)
ax4.set_xlabel('Position (um)', fontsize=11)
ax4.set_ylabel('n (cm^-3)', fontsize=11)
ax4.set_title('(d) Electron Concentration', fontsize=12)
ax4.grid(True, alpha=0.3)
ax4.set_xlim(0, total_length)

# (e) Hole concentration
ax5 = fig.add_subplot(gs[2, 1])
ax5.semilogy(x_holes, p_holes, 'r-', linewidth=2)
ax5.axvspan(0, LWIR_thickness, alpha=0.1, color='blue')
ax5.axvspan(LWIR_thickness, LWIR_thickness + Barrier_thickness, alpha=0.1, color='gray')
ax5.axvspan(LWIR_thickness + Barrier_thickness, total_length, alpha=0.1, color='red')
ax5.axvline(x=LWIR_thickness, color='k', linestyle='--', alpha=0.3)
ax5.axvline(x=LWIR_thickness + Barrier_thickness, color='k', linestyle='--', alpha=0.3)
ax5.set_xlabel('Position (um)', fontsize=11)
ax5.set_ylabel('p (cm^-3)', fontsize=11)
ax5.set_title('(e) Hole Concentration', fontsize=12)
ax5.grid(True, alpha=0.3)
ax5.set_xlim(0, total_length)

plt.suptitle('JEM2025 HgCdTe nBn Detector Simulation Results (100K)', 
             fontsize=14, fontweight='bold', y=0.995)

plt.savefig('exp_oc/JEM2025_all_results.png', dpi=300, bbox_inches='tight')
print("  Saved: exp_oc/JEM2025_all_results.png")

# =============================================================================
# PRINT SUMMARY
# =============================================================================

print("\n" + "="*70)
print("PLOT GENERATION COMPLETE")
print("="*70)
print("\nGenerated figures:")
print("  1. Figure5_band_diagram.png - Band diagram (Ec, Ev, Ei)")
print("  2. Figure6a_IV_curve.png - I-V characteristics (log scale)")
print("  3. Figure6a_IV_linear.png - I-V characteristics (linear scale)")
print("  4. Figure6b_carrier_concentration.png - n(x) and p(x)")
print("  5. JEM2025_all_results.png - Summary with all plots")
print("\nKey results shown in plots:")
print(f"  - Dark current at 0V: {j_abs[0]:.2e} A/cm^2")
print(f"  - Rule 07 VLWIR benchmark: {Rule07_VLWIR:.2e} A/cm^2")
print(f"  - Performance: {Rule07_VLWIR/j_abs[0]:.1e}x better than Rule 07")
print("\nAll plots saved to exp_oc/ directory")
print("="*70)
