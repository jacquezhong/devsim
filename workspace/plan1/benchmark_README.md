# Plan1 Open Reverse-Recovery Benchmark

This directory contains the first executable benchmark implementation for the
reframed plan1 study:

> An Open DEVSIM Benchmark for Reproducible Reverse-Recovery Simulation and
> Lifetime Trade-off Analysis in Silicon PN/PIN Diodes.

## Scope

This benchmark is intentionally modest. It does not attempt to reproduce a
commercial fast-recovery diode. Instead, it defines a transparent 1D silicon PIN
test problem in DEVSIM and records:

- DC I-V behavior.
- A reverse-voltage-step transient waveform.
- Extracted `Q_rr`, `I_rrm`, and `t_rr`.
- Lifetime, time-step, and mesh-density sweeps.
- A target-forward-current initial condition for a more physical lifetime
  comparison.
- A stored-mobile-charge diagnostic from electron/hole node values before the
  reverse step.

## Current Baseline

The current baseline uses `workspace/plan1/benchmark/config.json`:

- 1D PIN diode.
- Length: `3e-4 cm`.
- P/N contact regions: `5e-5 cm` each.
- P/N doping: `1e17 cm^-3`.
- I-region background donor density: `1e12 cm^-3`.
- Forward bias: `0.8 V`.
- Reverse step: `-1.0 V`.
- Default time step: `2e-9 s`.
- Default mesh density near PIN transitions: `2e-7 cm`.

## Commands

Run from repository root:

```bash
PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_dc_benchmark.py --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep lifetime

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep lifetime-target-current

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep time --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep mesh --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/generate_benchmark_figures.py
```

## First Results

Storage footprint after the current run remains small:

- `data/benchmark`: about 2.8 MB, including old exploratory logs.
- `data/benchmark/raw`: about 0.18 MB.
- `data/benchmark/waveforms`: about 0.05 MB using compressed `npz`.
- `figures/benchmark`: about 0.9 MB.
- benchmark scripts: about 32 KB.

Observed wall-clock time on the local machine:

- DC I-V, `tau=1e-6`: about 1.6 s.
- Single reverse-recovery transient: about 2.5 s.
- Four-point lifetime sweep: about 11 s.
- Three-point time-step sweep: about 9 s.
- Three-point mesh sweep: about 9 s.
- Four-point target-current lifetime sweep: about 13 s.

Representative metrics for `tau=1e-6`, `dt=2e-9`, `mesh=2e-7`:

Fixed-voltage initial condition (`V_F = 0.8 V`):

- `Q_rr = 4.614e-7 C`.
- `I_rrm = 4.524e2 A`.
- `t_rr = 2e-9 s`.
- `V_F @ 1e-3 A = 0.415 V`.
- Stored mobile charge before switching: `1.872e-6 C`.

Target-current initial condition (`I_F = 1e-3 A`):

- Resolved `V_F = 0.4257 V`.
- Resolved `I_F = 1.000e-3 A`.
- `Q_rr = 4.211e-9 C`.
- `I_rrm = 4.206 A`.
- Stored mobile charge before switching: `6.345e-9 C`.

The first results show an important benchmark behavior:

- `Q_rr` is very stable across tested time steps and mesh densities.
- `I_rrm` is strongly time-step dependent because the recovery pulse is very
  narrow.
- Lifetime changes affect `Q_rr` and `I_rrm`, but the current baseline only
  shows a modest change. A longer PIN region, stronger stored charge, or a
  target-current initial condition should be tested if the paper needs a larger
  lifetime trade-off signal.
- Under the target-current condition, the terminal `Q_rr` and internally
  integrated stored mobile charge are of the same order of magnitude, which is
  an important sanity check for the physical meaning of the transient.

## Interpretation

The current result is already useful as a reproducibility benchmark because it
demonstrates that different metrics have different numerical robustness:

- Integrated charge (`Q_rr`) is a better reference metric for this fast transient.
- Peak current (`I_rrm`) is useful but must be reported together with time-step
  settings.
- `t_rr` is quantized by time step in the current baseline and should not be
  over-interpreted.

## Next Improvements

- Add a circuit-limited reverse step, such as a voltage source with series
  resistance, so that peak recovery current is less dominated by the ideal
  voltage step.
- Add target-current time-step convergence to check whether `Q_rr` remains
  robust under the more physical initialization.
- Test a longer PIN region if runtime remains acceptable.
