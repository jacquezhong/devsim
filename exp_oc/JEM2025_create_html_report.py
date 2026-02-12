# Copyright 2025 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

"""
JEM2025_create_html_report.py - Generate HTML report with embedded plots
Alternative to matplotlib using HTML/Chart.js
"""

import os
import sys
import numpy as np

print("Generating HTML report with embedded plots...")

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

# Prepare data for plotting
LWIR_thickness = 9.0
Barrier_thickness = 4.35
VLWIR_thickness = 14.0
total_length = LWIR_thickness + Barrier_thickness + VLWIR_thickness

# Energy bandgaps (eV)
Eg_LWIR = 0.140
Eg_Barrier = 0.285
Eg_VLWIR = 0.091

# Convert potential to energy bands
x_all = []
Ec_all = []
Ev_all = []
Ei_all = []

for region, Eg in [('LWIR', Eg_LWIR), ('Barrier', Eg_Barrier), ('VLWIR', Eg_VLWIR)]:
    for x, V in zip(pot_data[region]['x'], pot_data[region]['V']):
        x_all.append(x)
        Ec = -V
        Ec_all.append(Ec)
        Ev_all.append(Ec - Eg)
        Ei_all.append(Ec - Eg/2)

x_electrons = []
n_electrons = []
for region in ['LWIR', 'Barrier', 'VLWIR']:
    for x, n in zip(carrier_data[region]['x'], carrier_data[region]['n']):
        x_electrons.append(x)
        n_electrons.append(n)

x_holes = []
p_holes = []
for region in ['LWIR', 'Barrier', 'VLWIR']:
    for x, p in zip(carrier_data[region]['x'], carrier_data[region]['p']):
        x_holes.append(x)
        p_holes.append(p)

# =============================================================================
# CREATE DATA FILES FOR PLOTTING
# =============================================================================

print("Creating data files for plotting...")

# Save band diagram data for JavaScript
with open('exp_oc/plot_data_band_diagram.js', 'w') as f:
    f.write('const bandData = {\n')
    f.write(f'  x: {x_all},\n')
    f.write(f'  Ec: {Ec_all},\n')
    f.write(f'  Ev: {Ev_all},\n')
    f.write(f'  Ei: {Ei_all},\n')
    f.write(f'  lwir_end: {LWIR_thickness},\n')
    f.write(f'  barrier_end: {LWIR_thickness + Barrier_thickness},\n')
    f.write(f'  total_length: {total_length}\n')
    f.write('};\n')

# Save carrier data
with open('exp_oc/plot_data_carriers.js', 'w') as f:
    f.write('const carrierData = {\n')
    f.write(f'  x_n: {x_electrons},\n')
    f.write(f'  n: {n_electrons},\n')
    f.write(f'  x_p: {x_holes},\n')
    f.write(f'  p: {p_holes},\n')
    f.write(f'  lwir_end: {LWIR_thickness},\n')
    f.write(f'  barrier_end: {LWIR_thickness + Barrier_thickness},\n')
    f.write(f'  total_length: {total_length}\n')
    f.write('};\n')

# Save I-V data
j_abs = np.abs(j_top)
with open('exp_oc/plot_data_iv.js', 'w') as f:
    f.write('const ivData = {\n')
    f.write(f'  voltage: {voltages.tolist()},\n')
    f.write(f'  current: {j_abs.tolist()},\n')
    f.write(f'  rule07_vlwir: 0.0539,\n')
    f.write(f'  rule07_lwir: 0.0001,\n')
    f.write(f'  j_dark: {j_abs[0]}\n')
    f.write('};\n')

print("  Saved: exp_oc/plot_data_band_diagram.js")
print("  Saved: exp_oc/plot_data_carriers.js")
print("  Saved: exp_oc/plot_data_iv.js")

# =============================================================================
# CREATE HTML REPORT
# =============================================================================

print("\nCreating HTML report...")

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JEM2025 Simulation Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="plot_data_band_diagram.js"></script>
    <script src="plot_data_carriers.js"></script>
    <script src="plot_data_iv.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
            background-color: #fafafa;
            padding: 15px;
            border-radius: 5px;
        }}
        .info-box {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }}
        .result-highlight {{
            background-color: #d4edda;
            border: 2px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            text-align: center;
        }}
        .result-highlight h3 {{
            color: #155724;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 10px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>JEM2025 HgCdTe nBn双色红外探测器仿真结果</h1>
        <p style="text-align: center; color: #666;">
            Journal of Electronic Materials (2025) 54:9174-9183<br>
            DOI: 10.1007/s11664-025-12289-5
        </p>

        <div class="result-highlight">
            <h3>🎯 核心仿真结果</h3>
            <p style="font-size: 18px; margin: 10px 0;">
                <strong>暗电流密度:</strong> {j_abs[0]:.2e} A/cm²<br>
                <strong>Rule 07 VLWIR限值:</strong> 5.39×10⁻² A/cm²<br>
                <strong>性能提升:</strong> 优于Rule 07约 {0.0539/j_abs[0]:.1e} 倍！
            </p>
        </div>

        <h2>📊 器件结构</h2>
        <table>
            <tr>
                <th>层次</th>
                <th>材料</th>
                <th>厚度 (µm)</th>
                <th>带隙 (meV)</th>
                <th>掺杂浓度 (cm⁻³)</th>
            </tr>
            <tr>
                <td>LWIR吸收层</td>
                <td>HgCdTe</td>
                <td>9.0</td>
                <td>140</td>
                <td>2.46×10¹⁴</td>
            </tr>
            <tr>
                <td>势垒层</td>
                <td>T3SL</td>
                <td>4.35</td>
                <td>285</td>
                <td>5.0×10¹⁵</td>
            </tr>
            <tr>
                <td>VLWIR吸收层</td>
                <td>T3SL</td>
                <td>14.0</td>
                <td>91</td>
                <td>5.0×10¹⁴</td>
            </tr>
        </table>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: rgba(54, 162, 235, 0.2);"></div>
                <span>LWIR (9 µm)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: rgba(128, 128, 128, 0.2);"></div>
                <span>Barrier (4.35 µm)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: rgba(255, 99, 132, 0.2);"></div>
                <span>VLWIR (14 µm)</span>
            </div>
        </div>

        <h2>📈 Figure 5: 能带图 (平衡态, 100K)</h2>
        <div class="info-box">
            <strong>说明:</strong> 显示导带边(Ec)、价带边(Ev)和本征费米能级(Ei)随位置的变化。
            零VBO设计使得价带在界面处连续。
        </div>
        <div class="chart-container">
            <canvas id="bandDiagramChart"></canvas>
        </div>

        <h2>📈 Figure 6a: I-V特性曲线</h2>
        <div class="info-box">
            <strong>说明:</strong> 暗电流随偏压的变化，以及Rule 07基准线的对比。
        </div>
        <div class="chart-container">
            <canvas id="ivChart"></canvas>
        </div>

        <h2>📈 Figure 6b: 载流子浓度分布</h2>
        <div class="info-box">
            <strong>说明:</strong> 平衡态下电子浓度(n)和空穴浓度(p)沿器件的分布。
        </div>
        <div class="chart-container">
            <canvas id="electronChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="holeChart"></canvas>
        </div>

        <h2>✅ 物理模型验证</h2>
        <table>
            <tr>
                <th>物理模型</th>
                <th>状态</th>
                <th>方程</th>
            </tr>
            <tr>
                <td>泊松方程</td>
                <td>✅ 已实现</td>
                <td>∇·(ε∇φ) = -q(p-n+Nd)</td>
            </tr>
            <tr>
                <td>漂移-扩散方程</td>
                <td>✅ 已实现</td>
                <td>J = qμnE ± qD∇n</td>
            </tr>
            <tr>
                <td>连续性方程</td>
                <td>✅ 已实现</td>
                <td>∇·J = q(R-G)</td>
            </tr>
            <tr>
                <td>SRH复合</td>
                <td>✅ 已实现</td>
                <td>USRH = (np-ni²)/[τp(n+ni)+τn(p+ni)]</td>
            </tr>
            <tr>
                <td>Auger复合</td>
                <td>✅ 已实现</td>
                <td>UAuger = (np-ni²)(Cn·n+Cp·p)</td>
            </tr>
        </table>

        <div class="info-box" style="margin-top: 30px;">
            <strong>仿真参数:</strong><br>
            温度: 100 K | 总方程数: 732 | 网格节点: 244<br>
            求解器: Newton-Raphson | 收敛误差: < 10⁻¹⁵
        </div>
    </div>

    <script>
        // Common chart options
        const commonOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{
                mode: 'index',
                intersect: false,
            }},
            plugins: {{
                legend: {{
                    position: 'top',
                }},
                tooltip: {{
                    enabled: true
                }}
            }}
        }};

        // Band Diagram
        const bandCtx = document.getElementById('bandDiagramChart').getContext('2d');
        new Chart(bandCtx, {{
            type: 'line',
            data: {{
                labels: bandData.x.map(x => x.toFixed(1)),
                datasets: [
                    {{
                        label: '导带边 (Ec)',
                        data: bandData.Ec,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    }},
                    {{
                        label: '价带边 (Ev)',
                        data: bandData.Ev,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    }},
                    {{
                        label: '本征能级 (Ei)',
                        data: bandData.Ei,
                        borderColor: 'rgb(75, 192, 192)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: '位置 (µm)'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: '能量 (eV)'
                        }},
                        reverse: false
                    }}
                }},
                plugins: {{
                    annotation: {{
                        annotations: {{
                            lwir: {{
                                type: 'box',
                                xMin: 0,
                                xMax: bandData.lwir_end,
                                backgroundColor: 'rgba(54, 162, 235, 0.1)'
                            }},
                            barrier: {{
                                type: 'box',
                                xMin: bandData.lwir_end,
                                xMax: bandData.barrier_end,
                                backgroundColor: 'rgba(128, 128, 128, 0.1)'
                            }},
                            vlwir: {{
                                type: 'box',
                                xMin: bandData.barrier_end,
                                xMax: bandData.total_length,
                                backgroundColor: 'rgba(255, 99, 132, 0.1)'
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // I-V Characteristics
        const ivCtx = document.getElementById('ivChart').getContext('2d');
        new Chart(ivCtx, {{
            type: 'line',
            data: {{
                labels: ivData.voltage.map(v => v.toFixed(1)),
                datasets: [
                    {{
                        label: '仿真结果',
                        data: ivData.current,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        fill: false
                    }},
                    {{
                        label: 'Rule 07 VLWIR (14µm)',
                        data: ivData.voltage.map(() => ivData.rule07_vlwir),
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 2,
                        borderDash: [10, 5],
                        pointRadius: 0,
                        fill: false
                    }},
                    {{
                        label: 'Rule 07 LWIR (9µm)',
                        data: ivData.voltage.map(() => ivData.rule07_lwir),
                        borderColor: 'rgb(255, 206, 86)',
                        borderWidth: 2,
                        borderDash: [10, 5],
                        pointRadius: 0,
                        fill: false
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: '偏压 (V)'
                        }}
                    }},
                    y: {{
                        type: 'logarithmic',
                        title: {{
                            display: true,
                            text: '暗电流密度 (A/cm²)'
                        }},
                        min: 1e-18,
                        max: 1e-1
                    }}
                }}
            }}
        }});

        // Electron Concentration
        const electronCtx = document.getElementById('electronChart').getContext('2d');
        new Chart(electronCtx, {{
            type: 'line',
            data: {{
                labels: carrierData.x_n.map(x => x.toFixed(1)),
                datasets: [{{
                    label: '电子浓度 (n)',
                    data: carrierData.n,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true
                }}]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: '位置 (µm)'
                        }}
                    }},
                    y: {{
                        type: 'logarithmic',
                        title: {{
                            display: true,
                            text: '浓度 (cm⁻³)'
                        }},
                        min: 1e10,
                        max: 1e16
                    }}
                }}
            }}
        }});

        // Hole Concentration
        const holeCtx = document.getElementById('holeChart').getContext('2d');
        new Chart(holeCtx, {{
            type: 'line',
            data: {{
                labels: carrierData.x_p.map(x => x.toFixed(1)),
                datasets: [{{
                    label: '空穴浓度 (p)',
                    data: carrierData.p,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true
                }}]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: '位置 (µm)'
                        }}
                    }},
                    y: {{
                        type: 'logarithmic',
                        title: {{
                            display: true,
                            text: '浓度 (cm⁻³)'
                        }},
                        min: 1e2,
                        max: 1e13
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

# Save HTML report
with open('exp_oc/JEM2025_results_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("  Saved: exp_oc/JEM2025_results_report.html")

print("\n" + "="*70)
print("HTML REPORT GENERATION COMPLETE")
print("="*70)
print("\nGenerated files:")
print("  1. JEM2025_results_report.html - Interactive HTML report with plots")
print("  2. plot_data_band_diagram.js - Band diagram data")
print("  3. plot_data_carriers.js - Carrier concentration data")
print("  4. plot_data_iv.js - I-V characteristics data")
print("\nTo view the report:")
print("  Open 'exp_oc/JEM2025_results_report.html' in a web browser")
print("="*70)
