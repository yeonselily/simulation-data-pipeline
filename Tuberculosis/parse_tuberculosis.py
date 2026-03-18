import csv
import json
import re
from pathlib import Path
import numpy as np

"""
Tuberculosis parser

Input (per specification.md):
- META.csv       : single-row metadata
- GRID_*.csv     : one file per exported timestep; each row is one grid cell

Output (in current folder):
- state.npz      : compact numeric state for visualization
- grid_long.csv  : long-format chemokine grid (optional helper)
- run.json       : metadata and visualization config

NPZ contents:
- timesteps      : (T,)
- grids          : (T,H,W)  -> alias for chemokine, for backward compatibility
- chemokine      : (T,H,W)
- bacteria       : (T,H,W)
- macrophage     : (T,H,W)
- macrophageState: (T,H,W)
- tcell          : (T,H,W)
- bloodVessel    : (T,H,W) [only if column exists]
"""

INPUT_DIR = "tb_csv"
RUN_JSON_PATH = "run.json"

# Support both:
# - META.csv
# - <prefix>_META.csv
META_RE = re.compile(r"^(?P<prefix>.+?)_META\.csv$", re.IGNORECASE)
SIMPLE_META_RE = re.compile(r"^META\.csv$", re.IGNORECASE)

# Support:
# - <LIB>_<RUN>_<TIMESTEP>_GRID.csv  (CUDA_000001_000010_GRID.csv)
# - GRID_00000.csv / GRID_00001.csv  (prototype naming)
GRID_FULL_RE = re.compile(
    r"^(?P<prefix>.+?)_(?P<run>\d{6})_(?P<timestep>\d{5,6})_GRID\.csv$", re.IGNORECASE
)
GRID_SIMPLE_RE = re.compile(r"^GRID_(?P<timestep>\d{5,6})\.csv$", re.IGNORECASE)


def list_real_csvs(folder: Path):
    return [p for p in folder.glob("*.csv") if not p.name.startswith("._")]


def read_single_row_csv(path: Path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No data rows in {path}")
    return rows[0]


def detect_tb_files(folder: Path):
    """
    Find META + GRID_* files for one run, per specification.md.
    """
    files = list_real_csvs(folder)
    meta = None
    grid_by_t = {}

    # Find META
    for p in files:
        if SIMPLE_META_RE.match(p.name) or META_RE.match(p.name):
            meta = p
            break

    if meta is None:
        raise FileNotFoundError("Could not find META.csv or *_META.csv (excluding ._* files)")

    # Find GRID_* files
    for p in files:
        name = p.name
        m_full = GRID_FULL_RE.match(name)
        m_simple = GRID_SIMPLE_RE.match(name)

        if m_full:
            t = int(m_full.group("timestep"))
            grid_by_t[t] = p
        elif m_simple:
            t = int(m_simple.group("timestep"))
            grid_by_t[t] = p

    if not grid_by_t:
        raise FileNotFoundError("No GRID_*.csv files found in input folder")

    timesteps = sorted(grid_by_t.keys())
    return {
        "meta_csv": meta,
        "grid_by_t": grid_by_t,
        "timesteps": timesteps,
    }


def build_tb_frame_from_csv(grid_csv: Path, height: int, width: int):
    """
    Read one Tuberculosis GRID_*.csv and return per-attribute 2D arrays.

    Required columns:
        row,col,bacteria,macrophage,macrophageState,tcell,chemokine
    Optional:
        bloodVessel
    """
    bacteria = np.zeros((height, width), dtype=np.int8)
    macrophage = np.zeros((height, width), dtype=np.int8)
    macrophage_state = np.full((height, width), -1, dtype=np.int8)
    tcell = np.zeros((height, width), dtype=np.int8)
    chemokine = np.zeros((height, width), dtype=np.int16)
    blood_vessel = np.zeros((height, width), dtype=np.int8)

    seen = set()

    with open(grid_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn.strip() for fn in reader.fieldnames or []]
        has_blood = "bloodVessel" in fieldnames

        required = [
            "row",
            "col",
            "bacteria",
            "macrophage",
            "macrophageState",
            "tcell",
            "chemokine",
        ]
        missing = [c for c in required if c not in fieldnames]
        if missing:
            raise ValueError(f"{grid_csv.name} missing required columns: {missing}")

        for row in reader:
            r = int(row["row"])
            c = int(row["col"])

            if not (0 <= r < height and 0 <= c < width):
                raise ValueError(f"Out-of-bounds cell ({r},{c}) in {grid_csv.name}")

            bacteria[r, c] = int(row["bacteria"])
            macrophage[r, c] = int(row["macrophage"])
            macrophage_state[r, c] = int(row["macrophageState"])
            tcell[r, c] = int(row["tcell"])
            chemokine[r, c] = int(row["chemokine"])

            if has_blood:
                blood_vessel[r, c] = int(row["bloodVessel"])

            seen.add((r, c))

    expected = height * width
    if len(seen) != expected:
        print(
            f"Warning: {grid_csv.name} has {len(seen)} unique cells, expected {expected} "
            "(every (row,col) exactly once)."
        )

    return {
        "bacteria": bacteria,
        "macrophage": macrophage,
        "macrophageState": macrophage_state,
        "tcell": tcell,
        "chemokine": chemokine,
        "bloodVessel": blood_vessel if np.any(blood_vessel) else None,
    }


def export_chemokine_long_csv(timesteps, chemokine, out_csv):
    """
    Optional helper: long-format chemokine grid.

    Columns: timestep,x,y,chemokine
    """
    T, H, W = chemokine.shape
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestep", "x", "y", "chemokine"])
        for i, t in enumerate(timesteps):
            g = chemokine[i]
            for y in range(H):
                for x in range(W):
                    writer.writerow([int(t), x, y, int(g[y, x])])


def write_run_json(meta_row, timesteps, input_dir, meta_csv_name, outputs):
    height = int(meta_row["height"])
    width = int(meta_row["width"])
    total_timesteps_declared = int(meta_row["timesteps"])
    max_chemokine = int(meta_row["maxChemokine"])
    output_interval = int(meta_row["outputInterval"])
    tcell_entrance = int(meta_row["tcellEntrance"])

    start_t = int(timesteps[0]) if timesteps else 0
    end_t = int(timesteps[-1]) if timesteps else 0
    count_t = len(timesteps)

    run_cfg = {
        "schema_version": "1.0",
        "run": {
            "app_name": "Tuberculosis",
            "framework": "MASS",
            "backend": "CUDA",
            "dimensions": {"type": "grid2d", "width": width, "height": height},
            # chemokine is the primary scalar grid used for the main heatmap
            "value_type": "int32",
            "value_range": {"min": 0, "max": max_chemokine},
            "timesteps": {"start": start_t, "end": end_t, "count": count_t},
            "state_type": "grid2d_multi_channel",
            "state_semantics": "Chemokine level",      
            "overlay_semantics": ["Bacteria", "Macrophage", "Macrophage state", "T-cell", "Blood vessel"],     
"notes": (
                f"META declares timesteps={total_timesteps_declared}, "
                f"outputInterval={output_interval}, tcellEntrance={tcell_entrance}. "
                f"Parsed {count_t} GRID frames."
            ),
            "chemokine_max": max_chemokine,
            "output_interval": output_interval,
            "tcell_entrance": tcell_entrance,
            "channels": {
                "chemokine": {"dtype": "int", "range": [0, max_chemokine], "label": "Chemokine level"},
                "bacteria": {"dtype": "int", "values": [0, 1], "label": "Bacteria"},
                "macrophage": {"dtype": "int", "values": [0, 1], "label": "Macrophage"},
                "macrophageState": {"dtype": "int", "values": [-1, 0, 1, 2, 3], "label": "Macrophage state"},
                "tcell": {"dtype": "int", "values": [0, 1], "label": "T-cell"},
                "bloodVessel": {"dtype": "int", "values": [0, 1], "label": "Blood vessel"},
            },
        },
        "input": {
            "folder": str(input_dir),
            "meta_csv": str(Path(input_dir) / meta_csv_name),
        },
        "outputs": outputs,
        "visualization": {
            "frame_stride": 1,
            "show_entities": False,
            "show_metrics": False,
        },
    }

    with open(RUN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(run_cfg, f, indent=2)
    print(f"Wrote {RUN_JSON_PATH}")


def main():
    folder = Path(INPUT_DIR)
    if not folder.exists():
        raise FileNotFoundError(f"Input folder not found: {folder.resolve()}")

    detected = detect_tb_files(folder)
    meta_csv = detected["meta_csv"]
    grid_by_t = detected["grid_by_t"]
    timesteps = detected["timesteps"]

    meta_row = read_single_row_csv(meta_csv)
    height = int(meta_row["height"])
    width = int(meta_row["width"])

    # Build per-timestep frames for each attribute
    bacteria_list = []
    macrophage_list = []
    macrophage_state_list = []
    tcell_list = []
    chemokine_list = []
    blood_vessel_list = []

    any_blood = False

    for t in timesteps:
        frame = build_tb_frame_from_csv(grid_by_t[t], height, width)
        bacteria_list.append(frame["bacteria"])
        macrophage_list.append(frame["macrophage"])
        macrophage_state_list.append(frame["macrophageState"])
        tcell_list.append(frame["tcell"])
        chemokine_list.append(frame["chemokine"])

        if frame["bloodVessel"] is not None:
            any_blood = True
            blood_vessel_list.append(frame["bloodVessel"])
        else:
            blood_vessel_list.append(np.zeros((height, width), dtype=np.int8))

    bacteria = np.stack(bacteria_list, axis=0)
    macrophage = np.stack(macrophage_list, axis=0)
    macrophage_state = np.stack(macrophage_state_list, axis=0)
    tcell = np.stack(tcell_list, axis=0)
    chemokine = np.stack(chemokine_list, axis=0)
    blood_vessel = np.stack(blood_vessel_list, axis=0) if any_blood else None

    t_arr = np.array(timesteps, dtype=np.int32)

    # Canonical outputs
    out_npz = "state.npz"
    out_grid_long = "grid_long.csv"

    # Save NPZ. 'grids' is an alias to chemokine for existing visualizer.
    npz_arrays = {
        "timesteps": t_arr,
        "grids": chemokine.astype(np.int32, copy=False),
        "chemokine": chemokine.astype(np.int32, copy=False),
        "bacteria": bacteria.astype(np.int8, copy=False),
        "macrophage": macrophage.astype(np.int8, copy=False),
        "macrophageState": macrophage_state.astype(np.int8, copy=False),
        "tcell": tcell.astype(np.int8, copy=False),
    }
    if any_blood:
        npz_arrays["bloodVessel"] = blood_vessel.astype(np.int8, copy=False)

    np.savez_compressed(out_npz, **npz_arrays)
    print(f"Wrote {out_npz} with chemokine shape {chemokine.shape}")

    export_chemokine_long_csv(timesteps, chemokine, out_grid_long)
    print(f"Wrote {out_grid_long}")

    outputs = {
        "grid_npz": out_npz,
        "grid_long_csv": out_grid_long,
        "entities_csv": "",
        "metrics_csv": "",
        "viz_params_csv": "",
    }

    write_run_json(
        meta_row=meta_row,
        timesteps=timesteps,
        input_dir=folder,
        meta_csv_name=meta_csv.name,
        outputs=outputs,
    )


if __name__ == "__main__":
    main()