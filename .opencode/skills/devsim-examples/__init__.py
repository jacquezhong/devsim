# DEVSIM Examples Package

"""
DEVSIM 官方示例代码参数化库

此包包含基于 DEVSIM 官方示例的参数化仿真代码，
用于器件仿真研究计划的标准化执行。

使用方式:
    from devsim_examples.diode.diode_1d import run_diode_1d_simulation
    result = run_diode_1d_simulation(
        p_doping=1e18,
        n_doping=1e16,
        max_voltage=1.0
    )
"""

__version__ = "1.0.0"
__author__ = "DEVSIM Examples Skill"

# 导出主要函数
from .diode.diode_1d import run_diode_1d_simulation
from .diode.diode_2d import run_diode_2d_simulation
from .diode.tran_diode import run_transient_diode_simulation
from .diode.ssac_diode import run_ssac_diode_simulation
from .capacitance.cap1d import run_capacitance_1d_simulation
from .capacitance.cap2d import run_capacitance_2d_simulation
from .mobility.gmsh_mos2d import run_mos_2d_mobility_simulation
from .bioapp1.bioapp1_2d import run_bioapp1_2d_simulation
from .bioapp1.bioapp1_3d import run_bioapp1_3d_simulation
from .vectorpotential.twowire import run_twowire_magnetic_simulation

# 导出智能网格策略
from .common.mesh_strategies import (
    MeshPolicy,
    DiodeMeshStrategy,
    get_intelligent_mesh_params,
    register_mesh_principle,
    register_capability_strategy,
)

__all__ = [
    # 仿真函数
    "run_diode_1d_simulation",
    "run_diode_2d_simulation",
    "run_transient_diode_simulation",
    "run_ssac_diode_simulation",
    "run_capacitance_1d_simulation",
    "run_capacitance_2d_simulation",
    "run_mos_2d_mobility_simulation",
    "run_bioapp1_2d_simulation",
    "run_bioapp1_3d_simulation",
    "run_twowire_magnetic_simulation",
    # 智能网格
    "MeshPolicy",
    "DiodeMeshStrategy",
    "get_intelligent_mesh_params",
    "register_mesh_principle",
    "register_capability_strategy",
]
