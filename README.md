# scaps_db_generator

> Automated dataset generator for solar cell simulations using [SCAPS-1D](https://scaps.elis.ugent.be/).

---

## Overview

`scaps_db_generator` is a Python toolkit that automates the execution of **SCAPS-1D** simulations over a parametric space and aggregates the results into structured CSV datasets. It is designed to build large-scale databases of I-V curves for solar cells — useful for machine learning, sensitivity analysis, or device physics research.

The tool varies three key physical parameters across configurable ranges:

- **Interface defect density** (`Nt` at interface, in cm⁻²)
- **Bulk defect density** (`Nt` in the absorber layer, in cm⁻³)
- **Absorber layer thickness** (in µm)

For each parameter combination, SCAPS is invoked via a generated script, the resulting `.iv` file is parsed, and the extracted I-V data is appended to a CSV file.

---

## Features

- Single and batch simulation modes
- Multicore parallelism: the surface defect density range is automatically split across all available CPU cores
- Automatic script generation, simulation execution, and result parsing
- Clean-up of temporary files after each run
- I-V curve plotting utility
- Configurable via a `.env` file — no hardcoded paths

---

## Project Structure

```
scaps_db_generator/
│
├── baseline/               # Reference .def file used as simulation template
├── csv/                    # Output directory for generated CSV datasets
├── scripts/                # Temporary SCAPS script files (auto-generated)
│
├── config.py               # Central configuration: paths, physical parameter ranges, batch setup
├── scaps_simulation.py     # Core simulation logic (script generation, SCAPS execution, result parsing)
├── scaps_batch_simulation.py  # Batch simulation orchestration
├── db_generator.py         # Single-run dataset generation entry point
├── db_batch_generator.py   # Parallel/batch dataset generation entry point
├── plot_iv_curves.py       # I-V curve visualization
├── utils.py                # Helper functions (interval splitting, etc.)
├── requirements.txt
└── .env                    # Environment variables (not committed)
```

---

## Requirements

- Python 3.8+
- [SCAPS-1D](https://scaps.elis.ugent.be/) installed and accessible on the system
- Python dependencies:

```bash
pip install -r requirements.txt
```

Key packages: `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `scipy`, `python-dotenv`.

---

## Configuration

Copy or create a `.env` file at the project root with the following variables:

```env
# SCAPS paths
SCAPS_EXE_PATH=C:/path/to/scaps.exe
SCAPS_DEF_DIR=C:/path/to/scaps/def/
SCAPS_RESULTS_DIR=C:/path/to/scaps/results/
SCAPS_BATCH_DIR=C:/path/to/scaps/batch/

# Project paths
SCRIPTS_DIR=./scripts
SCRIPT_NAME=sim_script
BASELINE_DIR=./baseline
BASELINE_FILENAME=my_solar_cell.def

# Output
OUTPUT_CSV_PATH=./csv/iv_curves.csv
V_CSV_PATH=./csv/voltages.csv
SIMULATION_FILENAME=sim_result
```

Physical parameter ranges can be adjusted directly in `config.py`:

```python
DEFAULT_DENSITY_SURFACE_FROM = 5e14   # cm⁻²
DEFAULT_DENSITY_SURFACE_TO   = 5e15
DEFAULT_DENSITY_SURFACE_STEPS = 10

DEFAULT_DENSITY_VOLUME_FROM  = 5e15   # cm⁻³
DEFAULT_DENSITY_VOLUME_TO    = 5e17
DEFAULT_DENSITY_VOLUME_STEPS = 2

THICKNESS_FROM = 1.5e-2               # µm
THICKNESS_TO   = 1.5e-1
THICKNESS_STEPS = 2
```

---

## Usage

### Single simulation

Run a single simulation with default parameter values:

```bash
python db_generator.py
```

### Batch simulation (parallelized)

Run the full parameter sweep using all available CPU cores:

```bash
python db_batch_generator.py
```

The surface defect density interval is automatically divided into as many sub-intervals as there are CPU cores (`os.cpu_count()`), and each sub-interval is processed in parallel.

### Plot I-V curves

Visualize the generated dataset:

```bash
python plot_iv_curves.py
```

---

## How It Works

1. **Script generation** — For each `(Nt_surface, Nt_volume, thickness)` triplet, a `.script` file is generated and passed to SCAPS.
2. **SCAPS execution** — SCAPS is launched as a subprocess with the generated script. It loads the baseline `.def` file, sets the parameters, runs the I-V calculation, and saves a `.iv` result file.
3. **Result parsing** — The `.iv` file is read to extract current values and solar cell parameters (Voc, Jsc, FF, efficiency). The data is appended as a new row in the output CSV.
4. **Clean-up** — Temporary script and `.iv` files are deleted after processing.

---

## Output Format

The output CSV (`iv_curves.csv`) contains one row per simulation. Each row holds the current values at each voltage step, followed by the deduced solar cell performance metrics (Voc, Jsc, FF, PCE).

---

## Notes

- SCAPS-1D is a Windows application; this tool is primarily designed to run on Windows.
- The `.def` baseline file must be compatible with the parameter labels defined in `config.py` (`interface1.IFdefect1.Ntotal`, `layer1.defect1.Ntotal`, `layer2.thickness`). Adjust these labels to match your own device structure if needed.
- The `baseline/` folder should contain the reference `.def` file specified in `.env`.

---

## License

No license specified. Contact the author for usage permissions.

---

## Author

[HCWassim](https://github.com/HCWassim)