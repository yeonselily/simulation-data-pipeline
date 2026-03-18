# Tuberculosis Data Specification

## Design Principle

All data required for visualization is exported as **numerical simulation state**.

The visualization layer should:

- not depend on SimViz or pre-rendered RGB output
- not perform additional simulation logic or derived calculations beyond basic rendering (i.e., “if this is 1, draw it”)
- interpret exported state only and render it

The Tuberculosis model’s visualization-relevant environment attributes are:

- bacteria presence
- macrophage presence
- macrophage state
- T-cell presence
- chemokine level
- optionally: blood vessel flag (not required for the first usable visualization)

---

## Grid

The simulation is a **2D grid of lung cells**. Each grid cell corresponds to one environment place (e.g., an `EnvironmentPlace` in the model).

Each cell may contain:

- **bacteria**: whether bacteria is present (binary)
- **macrophage**: whether a macrophage is present (binary)
- **macrophageState**: macrophage category/state (categorical; only meaningful if macrophage is present)
- **tcell**: whether a T-cell is present (binary)
- **chemokine**: chemokine level (integer)
- **bloodVessel** (optional): whether the cell is a blood vessel (binary)

These correspond to environment-level model state.

---

## Files

The Tuberculosis dataset is expected to contain:

- `META.csv`: one file describing dataset shape and global constants
- `GRID_*.csv`: one file per exported timestep; each row is one grid cell

---

## Example Headers

### `META.csv`

```csv
height,width,timesteps,outputInterval,maxChemokine,tcellEntrance
40,40,101,1,2,10
```

### `GRID_00001.csv`

```csv
row,col,bacteria,macrophage,macrophageState,tcell,chemokine
0,0,0,0,-1,0,0
0,1,0,1,0,0,2
0,2,0,1,0,0,2
0,3,0,0,-1,0,2
0,4,0,0,-1,0,2
0,5,0,1,0,0,2
```

**Note:** an optional `bloodVessel` column may be added later if needed, but it is not required for the first usable visualization.

---

## Grid State Format

### Preferred per-timestep file name

`LIBRARY_RUN#(Zero-padded to 6)_TIMESTEP(Zero-padded to 6)_GRID.csv`

**Example**

`CUDA_000001_000010_GRID.csv`

### Minimum supported prototype naming

For prototype or converted output, a simpler naming pattern is also acceptable:

- `GRID_00000.csv`
- `GRID_00001.csv`
- `GRID_00002.csv`
- …
- `META.csv`

---

## `META.csv` (Required)

### Schema

`META.csv` is a single-row CSV with the following fields:

- `height`: grid height \(H\), number of rows (int)
- `width`: grid width \(W\), number of columns (int)
- `timesteps`: number of exported `GRID_*.csv` files \(T\) (int)
- `outputInterval`: simulation steps between exports (int)
- `maxChemokine`: maximum chemokine level used by the model (int; TB currently uses 2)
- `tcellEntrance`: day/step after which T-cells can enter (int; TB currently uses 10)

### Contract

- The dataset must contain exactly `timesteps` grid files.
- `height` and `width` must match the grid resolution used downstream.
- These values are treated as run-level metadata and do not change across files.

---

## `GRID_*.csv` (Required, One Per Timestep)

Each `GRID_*.csv` file represents one exported state snapshot.

### Required columns

- `row`: 0-indexed row coordinate in `[0, height - 1]`
- `col`: 0-indexed column coordinate in `[0, width - 1]`
- `bacteria`: int in `{0,1}`; 1 means bacteria present at that cell
- `macrophage`: int in `{0,1}`; 1 means a macrophage is present
- `macrophageState`:
  - int in `{0,1,2,3}` when `macrophage = 1`
  - `-1` when `macrophage = 0` (recommended sentinel)
- `tcell`: int in `{0,1}`; 1 means T-cell present
- `chemokine`: int in `[0, maxChemokine]` (TB currently uses `0,1,2`)

### Optional columns

- `bloodVessel`: int in `{0,1}`; 1 means blood vessel present at that cell

### Example headers

Without `bloodVessel`:

```csv
row,col,bacteria,macrophage,macrophageState,tcell,chemokine
```

With optional `bloodVessel`:

```csv
row,col,bacteria,macrophage,macrophageState,tcell,chemokine,bloodVessel
```

---

## Macrophage State Categories

Macrophage state should be exported as a numeric code with documented meaning.

### Suggested mapping

- `-1` = no macrophage present
- `0` = RESTING
- `1` = INFECTED
- `2` = ACTIVATED
- `3` = CHRONICALLY_INFECTED

If the benchmark uses a different internal encoding, the export must document that encoding in metadata or accompanying documentation.

---

## Row Ordering and Completeness Requirements

Each `GRID_*.csv` file must contain:

- exactly `height * width` data rows (plus 1 header row)
- every `(row, col)` coordinate exactly once
- no missing cells
- no duplicate cells

### Preferred ordering

Files should use row-major order:

- sort first by `row`
- then by `col`

Example: `(0,0), (0,1), (0,2), ...`

This makes parsing simple and consistent.

---

## What “One File Per Timestep” Means

- `GRID_00000.csv` is the first exported snapshot
- `GRID_00001.csv` is the next exported snapshot
- and so on

The file index is the export index, not necessarily the raw simulation day number.

If the actual simulation step needs to be preserved later, an optional `timestep` column may be added.

---

## (Optional) Timestep Data

Run-level summary metrics for each timestep (useful for side charts). Not required for the first usable visualization.

### Format

`LibraryName_RUN#(0-padded size 6)_TIMESTEP(0-padded size 6)_TIMESTEPCONSTANTS.csv`

### Data in file

```csv
timestep,bacteriaCellCount,macrophageCount,tcellCount,infectedMacrophageCount,chronicallyInfectedMacrophageCount,totalChemokine,bloodVesselOccupiedCount
```

---

## Visualization Semantics (Guidance)

The generalized visualizer should interpret the exported state as layered grid data.

Suggested layers:

- Layer 0: `chemokine` (heatmap background)
- Layer 1: `bacteria` (binary overlay)
- Layer 2: `macrophageState` (categorical overlay)
- Layer 3: `tcell` (binary overlay)
- Layer 4: `bloodVessel` markers (optional)

---

## Minimum Required Export (First Usable Visualization)

For a first usable Tuberculosis visualization, the benchmark only needs to export:

- `META.csv`
- one `GRID_*.csv` per timestep containing:

`row,col,bacteria,macrophage,macrophageState,tcell,chemokine`

That is enough to build:

- `state.npz`
- `run.json`
- a Plotly visualization