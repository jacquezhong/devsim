#!/usr/bin/env python3
"""
Plan 1 Experiment: High Voltage Power Diode Reverse Recovery Characteristics
研究方案一：高压功率二极管的反向恢复特性与软度因子优化

This script performs:
1. DC IV characteristic simulation
2. Transient switching simulation with varying carrier lifetimes
3. Analysis of reverse recovery time and softness factor

Author: Research Assistant
Date: 2026-02-14
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json
import sys
import os

# Add path for devsim-examples if needed
try:
    from devsim import (
        set_parameter, solve, write_devices, 
        get_contact_current, get_node_model_values,
        edge_from_node_model, node_model
    )
    import devsim.python_packages.simple_physics as simple_physics
    print("✓ DEVSIM imported successfully")
except ImportError as e:
    print(f"✗ Failed to import DEVSIM: {e}")
    sys.exit(1)

# Create output directories
os.makedirs('data', exist_ok=True)
os.makedirs('figures', exist_ok=True)

# Experiment configuration
CONFIG = {
    'device': 'PowerDiode',
    'region': 'Bulk',
    'length': 1e-2,          # 100 μm
    'p_doping': 1e16,        # p-region doping
    'n_doping': 1e19,        # n-region doping
    'temperature': 300,      # K
}

print("=" * 60)
print("Plan 1: High Voltage Power Diode Reverse Recovery")
print("=" * 60)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Device Length: {CONFIG['length']*1e4:.0f} μm")
print(f"P-region doping: {CONFIG['p_doping']:.0e} cm⁻³")
print(f"N-region doping: {CONFIG['n_doping']:.0e} cm⁻³")
print("=" * 60)

def create_mesh(device, region, length):
    """Create 1D diode mesh"""
    from devsim import (
        create_1d_mesh, add_1d_mesh_line, finalize_mesh, 
        add_1d_region, add_1d_contact, create_device
    )
    
    create_1d_mesh(mesh=device)
    add_1d_mesh_line(mesh=device, pos=0, ps=length/100, tag="top")
    add_1d_mesh_line(mesh=device, pos=length, ps=length/100, tag="bot")
    add_1d_contact(mesh=device, name="top", tag="top", material="metal")
    add_1d_contact(mesh=device, name="bot", tag="bot", material="metal")
    add_1d_region(mesh=device, material="Si", region=region, tag1="top", tag2="bot")
    finalize_mesh(mesh=device)
    create_device(mesh=device, device=device)
    print(f"✓ Created mesh: {device}, region: {region}")

def set_parameters(device, region):
    """Set material and physics parameters"""
    from devsim.python_packages.model_create import CreateNodeModel
    from devsim.python_packages.simple_physics import SetSiliconParameters
    
    # Set all silicon material parameters using simple_physics
    SetSiliconParameters(device, region, CONFIG['temperature'])
    
    # Doping profile (step junction)
    junction_pos = CONFIG['length'] * 0.1  # Junction at 10% of length
    
    # Create doping models using DEVSIM's formula parser
    CreateNodeModel(device, region, "Acceptors", f"{CONFIG['p_doping']}*step({junction_pos}-x)")
    CreateNodeModel(device, region, "Donors", f"{CONFIG['n_doping']}*step(x-{junction_pos})")
    CreateNodeModel(device, region, "NetDoping", "Donors-Acceptors")
    
    print(f"✓ Set doping profile (junction at {junction_pos*1e4:.1f} μm)")

def dc_simulation(device, region, v_stop=2.0, v_step=0.05):
    """Run DC IV simulation"""
    print("\n--- DC Simulation ---")
    from devsim.python_packages.model_create import CreateSolution, set_node_values
    from devsim import get_contact_list
    
    # Step 1: Create Potential solution
    CreateSolution(device, region, "Potential")
    simple_physics.CreateSiliconPotentialOnly(device, region)
    
    # Set up contacts with 0 bias
    for contact in get_contact_list(device=device):
        set_parameter(device=device, name=simple_physics.GetContactBiasName(contact), value=0.0)
        simple_physics.CreateSiliconPotentialOnlyContact(device, region, contact)
    
    # Initial potential-only solve
    print("  Solving for initial potential...")
    solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)
    
    # Step 2: Create Electrons and Holes solutions
    CreateSolution(device, region, "Electrons")
    CreateSolution(device, region, "Holes")
    
    # Set initial values from intrinsic carriers
    set_node_values(device=device, region=region, name="Electrons", init_from="IntrinsicElectrons")
    set_node_values(device=device, region=region, name="Holes", init_from="IntrinsicHoles")
    
    # Step 3: Create drift-diffusion equations
    simple_physics.CreateSiliconDriftDiffusion(device, region)
    for contact in get_contact_list(device=device):
        simple_physics.CreateSiliconDriftDiffusionAtContact(device, region, contact)
    
    # Initial drift-diffusion solve at equilibrium
    print("  Solving for drift-diffusion equilibrium...")
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
    
    # Ramp bias
    voltages = []
    currents = []
    
    v = 0.0
    while v <= v_stop + v_step/2:
        set_parameter(device=device, name=simple_physics.GetContactBiasName("top"), value=v)
        solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=30)
        
        # Get current
        current = get_contact_current(device=device, contact="top")
        voltages.append(v)
        currents.append(current)
        
        if len(voltages) % 10 == 0:
            print(f"  V = {v:.2f} V, I = {current:.3e} A")
        
        v += v_step
    
    print(f"✓ DC simulation complete: {len(voltages)} points")
    return np.array(voltages), np.array(currents)

def transient_simulation(device, region, v_bias=-400.0, t_stop=1e-6, tau_n=1e-6, tau_p=1e-6):
    """Run transient switching simulation"""
    print(f"\n--- Transient Simulation (τn=τp={tau_n:.0e}s) ---")
    
    # Set carrier lifetimes
    set_parameter(device=device, region=region, name="taun", value=tau_n)
    set_parameter(device=device, region=region, name="taup", value=tau_p)
    
    # First apply forward bias to establish steady state
    print("  Applying forward bias (0.7V)...")
    set_parameter(device=device, name=simple_physics.GetContactBiasName("top"), value=0.7)
    solve(type="dc", absolute_error=1e10, relative_error=1e-10, maximum_iterations=50)
    
    # Get initial current
    i_forward = get_contact_current(device=device, contact="top")
    print(f"  Forward current: {i_forward:.3e} A")
    
    # Switch to reverse bias
    print(f"  Switching to reverse bias ({v_bias}V)...")
    set_parameter(device=device, name=simple_physics.GetContactBiasName("top"), value=v_bias)
    
    # Time stepping
    times = []
    currents = []
    
    # Initial transient step
    t = 0
    dt = 1e-9  # Start with 1ns
    
    while t < t_stop:
        solve(type="transient", absolute_error=1e10, relative_error=1e-10, 
              maximum_iterations=30, tdelta=dt)
        
        t += dt
        current = get_contact_current(device=device, contact="top")
        times.append(t)
        currents.append(current)
        
        # Adaptive time stepping
        if len(times) > 10:
            # Increase time step after initial transient
            dt = min(dt * 1.5, 1e-8)
        
        if len(times) % 100 == 0:
            print(f"  t = {t:.2e}s, I = {current:.3e} A")
    
    print(f"✓ Transient simulation complete: {len(times)} time points")
    return np.array(times), np.array(currents), i_forward

def analyze_reverse_recovery(times, currents, i_forward):
    """Analyze reverse recovery characteristics"""
    print("\n--- Reverse Recovery Analysis ---")
    
    # Find peak reverse current
    i_peak_idx = np.argmin(currents)
    i_peak = currents[i_peak_idx]
    t_peak = times[i_peak_idx]
    
    print(f"  Peak reverse current: {i_peak:.3e} A at t={t_peak:.2e}s")
    
    # Calculate reverse recovery time (trr)
    # Time from switching to when current returns to 10% of forward current
    threshold = 0.1 * abs(i_forward)
    
    # Find recovery time
    recovery_idx = i_peak_idx
    while recovery_idx < len(currents) and abs(currents[recovery_idx]) > threshold:
        recovery_idx += 1
    
    if recovery_idx < len(currents):
        trr = times[recovery_idx]
        print(f"  Reverse recovery time (trr): {trr:.2e}s")
    else:
        trr = times[-1]
        print(f"  Reverse recovery time (trr): >{trr:.2e}s (incomplete recovery)")
    
    # Calculate softness factor
    # S = tf / tr, where tf is fall time, tr is rise time
    # Here we use: S = (time from peak to recovery) / (time from 0 to peak)
    tr = t_peak  # Rise time
    tf = trr - t_peak  # Fall time
    softness = tf / tr if tr > 0 else 0
    
    print(f"  Rise time (tr): {tr:.2e}s")
    print(f"  Fall time (tf): {tf:.2e}s")
    print(f"  Softness factor (S): {softness:.2f}")
    
    # Calculate reverse recovery charge (Qrr)
    # Integrate reverse current
    reverse_mask = currents < 0
    if np.any(reverse_mask):
        qrr = np.trapz(np.abs(currents[reverse_mask]), times[reverse_mask])
        print(f"  Reverse recovery charge (Qrr): {qrr:.3e} C")
    else:
        qrr = 0
        print(f"  No reverse current detected")
    
    return {
        'trr': trr,
        'softness': softness,
        'qrr': qrr,
        'i_peak': i_peak,
        't_peak': t_peak
    }

def plot_results(dc_results, transient_results, output_dir='figures'):
    """Generate plots"""
    print("\n--- Generating Plots ---")
    
    # Plot 1: DC IV characteristics
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dc_results['voltage'], dc_results['current'] * 1e3, 'b-', linewidth=2)
    ax.set_xlabel('Voltage (V)', fontsize=12)
    ax.set_ylabel('Current (mA)', fontsize=12)
    ax.set_title('Power Diode DC IV Characteristics', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/dc_iv_characteristics.png', dpi=300)
    print(f"  ✓ Saved: {output_dir}/dc_iv_characteristics.png")
    plt.close()
    
    # Plot 2: Transient waveforms for different lifetimes
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    colors = ['blue', 'red', 'green', 'purple']
    
    for i, (tau, data) in enumerate(transient_results.items()):
        times = data['times']
        currents = data['currents']
        
        # Plot 1: Full transient
        axes[0, 0].plot(times * 1e6, currents * 1e3, 
                       color=colors[i % len(colors)], 
                       label=f'τ = {tau:.0e}s', linewidth=2)
        
        # Plot 2: Zoom on reverse recovery
        reverse_mask = currents < 0
        if np.any(reverse_mask):
            axes[0, 1].plot(times[reverse_mask] * 1e6, 
                           np.abs(currents[reverse_mask]) * 1e3,
                           color=colors[i % len(colors)],
                           label=f'τ = {tau:.0e}s', linewidth=2)
    
    axes[0, 0].set_xlabel('Time (μs)', fontsize=12)
    axes[0, 0].set_ylabel('Current (mA)', fontsize=12)
    axes[0, 0].set_title('Reverse Recovery Waveforms', fontsize=14)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].set_xlabel('Time (μs)', fontsize=12)
    axes[0, 1].set_ylabel('Reverse Current (mA)', fontsize=12)
    axes[0, 1].set_title('Reverse Recovery Detail', fontsize=14)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: trr vs lifetime
    taus = list(transient_results.keys())
    trrs = [transient_results[tau]['analysis']['trr'] * 1e6 for tau in taus]
    axes[1, 0].semilogx(taus, trrs, 'bo-', linewidth=2, markersize=8)
    axes[1, 0].set_xlabel('Carrier Lifetime (s)', fontsize=12)
    axes[1, 0].set_ylabel('Reverse Recovery Time (μs)', fontsize=12)
    axes[1, 0].set_title('trr vs Carrier Lifetime', fontsize=14)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Softness factor vs lifetime
    softness = [transient_results[tau]['analysis']['softness'] for tau in taus]
    axes[1, 1].semilogx(taus, softness, 'rs-', linewidth=2, markersize=8)
    axes[1, 1].set_xlabel('Carrier Lifetime (s)', fontsize=12)
    axes[1, 1].set_ylabel('Softness Factor', fontsize=12)
    axes[1, 1].set_title('Softness Factor vs Carrier Lifetime', fontsize=14)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/transient_analysis.png', dpi=300)
    print(f"  ✓ Saved: {output_dir}/transient_analysis.png")
    plt.close()

def save_results(dc_results, transient_results, output_dir='data'):
    """Save results to files"""
    print("\n--- Saving Results ---")
    
    # Save DC results
    dc_data = np.column_stack([dc_results['voltage'], dc_results['current']])
    np.savetxt(f'{output_dir}/dc_iv_data.txt', dc_data, 
               header='Voltage(V) Current(A)', comments='')
    print(f"  ✓ Saved: {output_dir}/dc_iv_data.txt")
    
    # Save transient results for each lifetime
    summary = {}
    for tau, data in transient_results.items():
        # Save waveform
        waveform = np.column_stack([data['times'], data['currents']])
        np.savetxt(f'{output_dir}/transient_tau{tau:.0e}.txt', waveform,
                   header='Time(s) Current(A)', comments='')
        
        # Collect analysis
        summary[f'tau_{tau:.0e}'] = data['analysis']
    
    # Save summary as JSON
    with open(f'{output_dir}/analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ Saved: {output_dir}/analysis_summary.json")

# Main experiment
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Starting Experiment...")
    print("=" * 60)
    
    # Create mesh
    create_mesh(CONFIG['device'], CONFIG['region'], CONFIG['length'])
    set_parameters(CONFIG['device'], CONFIG['region'])
    
    # Run DC simulation
    v_dc, i_dc = dc_simulation(CONFIG['device'], CONFIG['region'])
    dc_results = {'voltage': v_dc, 'current': i_dc}
    
    # Run transient simulations with different carrier lifetimes
    lifetimes = [1e-8, 1e-7, 1e-6, 1e-5]
    transient_results = {}
    
    for tau in lifetimes:
        try:
            t, i, i_fwd = transient_simulation(
                CONFIG['device'], CONFIG['region'],
                v_bias=-400.0, t_stop=1e-6,
                tau_n=tau, tau_p=tau
            )
            
            analysis = analyze_reverse_recovery(t, i, i_fwd)
            
            transient_results[tau] = {
                'times': t,
                'currents': i,
                'i_forward': i_fwd,
                'analysis': analysis
            }
        except Exception as e:
            print(f"✗ Error in transient simulation (τ={tau:.0e}s): {e}")
            import traceback
            traceback.print_exc()
    
    # Generate plots
    plot_results(dc_results, transient_results)
    
    # Save results
    save_results(dc_results, transient_results)
    
    print("\n" + "=" * 60)
    print("Experiment Complete!")
    print("=" * 60)
    print("\nResults saved to:")
    print("  - data/dc_iv_data.txt")
    print("  - data/transient_tau*.txt")
    print("  - data/analysis_summary.json")
    print("  - figures/dc_iv_characteristics.png")
    print("  - figures/transient_analysis.png")
    print("=" * 60)
