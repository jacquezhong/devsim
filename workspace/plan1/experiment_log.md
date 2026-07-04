# Plan1 Benchmark Experiment Log

## 2026-07-04: Target-Current Reverse-Recovery Extension

### Purpose

This run extends the initial fixed-voltage reverse-recovery benchmark with two
checks needed for a more physically meaningful lifetime comparison:

- Use a fixed target forward current before reverse switching.
- Integrate the internal stored mobile charge before switching and compare it
  with the terminal reverse-recovery charge.

The raw transient waveform arrays are stored as compressed `npz` files under
`data/benchmark/waveforms`. The JSON files under `data/benchmark/raw` keep case
metadata, metrics, solver status, and a pointer to the waveform file.

### Environment

- Python: `/opt/miniconda3/bin/python3`
- DEVSIM: conda base installation
- Cache prefix: `PYTHONPYCACHEPREFIX=/tmp/devsim_pycache`
- Working directory: repository root

### Code Changes

- `benchmark_common.py`
  - Added compressed `npz` writer.
  - Added carrier-profile extraction from `Electrons`, `Holes`, `x`, and
    `NodeVolume`.
  - Added stored-mobile-charge integration:
    `q * sum(max(n-n0, 0) + max(p-p0, 0)) * NodeVolume`.
- `run_reverse_recovery_benchmark.py`
  - Added `--initial-condition target_current`.
  - Added `--sweep lifetime-target-current`.
  - Added coarse DC scan plus bisection to resolve `V_F` for a target current.
  - Added `stored_charge` metrics to output JSON.
  - Moved transient waveform arrays to compressed `npz`.
- `generate_benchmark_figures.py`
  - Added loading for both legacy JSON waveforms and new `npz` waveforms.
  - Prefer new `recovery_vfixed_*` and `recovery_ifixed_*` cases when plotting.
- `benchmark_README.md`
  - Updated commands, storage footprint, representative metrics, and next steps.

### Commands

```bash
PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  -m py_compile workspace/plan1/benchmark/*.py

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --tau 1e-6 --initial-condition target_current

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py --sweep lifetime

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep lifetime-target-current

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep time --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/run_reverse_recovery_benchmark.py \
  --sweep mesh --tau 1e-6

PYTHONPYCACHEPREFIX=/tmp/devsim_pycache /opt/miniconda3/bin/python3 \
  workspace/plan1/benchmark/generate_benchmark_figures.py
```

### Results

Fixed-voltage lifetime sweep (`V_F = 0.8 V`, `V_R = -1 V`):

| tau (s) | Qrr (C) | Irrm (A) | stored mobile charge (C) |
|---:|---:|---:|---:|
| 1e-8 | 4.200e-7 | 4.120e2 | 1.705e-6 |
| 1e-7 | 4.574e-7 | 4.485e2 | 1.856e-6 |
| 1e-6 | 4.614e-7 | 4.524e2 | 1.872e-6 |
| 1e-5 | 4.618e-7 | 4.528e2 | 1.874e-6 |

Target-current lifetime sweep (`I_F = 1e-3 A`, `V_R = -1 V`):

| tau (s) | resolved VF (V) | resolved IF (A) | Qrr (C) | Irrm (A) | stored mobile charge (C) |
|---:|---:|---:|---:|---:|---:|
| 1e-8 | 0.2851 | 1.001e-3 | 3.495e-9 | 3.493 | 3.478e-9 |
| 1e-7 | 0.3761 | 1.001e-3 | 3.872e-9 | 3.869 | 4.989e-9 |
| 1e-6 | 0.4257 | 1.000e-3 | 4.211e-9 | 4.206 | 6.345e-9 |
| 1e-5 | 0.4344 | 9.997e-4 | 4.297e-9 | 4.291 | 6.687e-9 |

Time-step sweep at `tau = 1e-6`, fixed voltage:

| dt (s) | Qrr (C) | Irrm (A) | trr (s) |
|---:|---:|---:|---:|
| 5e-9 | 4.612e-7 | 1.832e2 | 5e-9 |
| 2e-9 | 4.614e-7 | 4.524e2 | 2e-9 |
| 1e-9 | 4.612e-7 | 8.723e2 | 1e-9 |

Mesh sweep at `tau = 1e-6`, fixed voltage:

| mesh density (cm) | Qrr (C) | Irrm (A) | elapsed (s) |
|---:|---:|---:|---:|
| 5e-7 | 4.615e-7 | 4.525e2 | 1.28 |
| 2e-7 | 4.614e-7 | 4.524e2 | 2.45 |
| 1e-7 | 4.614e-7 | 4.523e2 | 4.48 |

### Interpretation

- The fixed-current protocol is more suitable for lifetime comparison because
  each case begins from nearly the same terminal forward current.
- Under the fixed-current protocol, `Qrr` and the internally integrated stored
  mobile charge are of the same order of magnitude. This supports the physical
  meaning of the transient extraction.
- The fixed-voltage protocol creates a much larger injected state at `0.8 V`;
  it is useful as a numerical stress case, but less clean as a lifetime
  comparison.
- `Qrr` is robust in the fixed-voltage time-step sweep, while `Irrm` is strongly
  time-step dependent. This is expected for an ideal voltage step with a very
  narrow current pulse.
- Mesh convergence is good for the tested PIN geometry.

### Storage

After this run:

- `data/benchmark/raw`: about 184 KB.
- `data/benchmark/waveforms`: about 48 KB.
- `data/benchmark/metrics`: about 16 KB.
- `data/benchmark`: about 2.8 MB including old exploratory logs.

The compressed `npz` files are smaller and cleaner than embedding all waveform
arrays directly in JSON.
