import csv
import json
import re
from pathlib import Path
import numpy as np

'''
Input: raw SugarScape CSV files (META, GRID, AGENT) in ../input_files/ 
Output: state.npz, grid_long.csv, entities_long.csv, run.json in current folder
Transforms many raw SugarScape CSV files into a smaller, standardized visualization package.
'''
INPUT_DIR = "../input_files"
RUN_JSON_PATH = "run.json"

# Supports both:
#   serial_META.csv
#   CILK_000001_META.csv
META_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_META\.csv$")
GRID_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_(?P<timestep>\d{6})_GRID\.csv$")
AGENT_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_(?P<timestep>\d{6})_AGENT\.csv$")

def list_real_csvs(folder: Path):
    return [p for p in folder.glob("*.csv") if not p.name.startswith("._")]

def read_single_row_csv(path: Path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No data rows in {path}")
    return rows[0]

def detect_sugarscape_files(folder: Path):
    files = list_real_csvs(folder)
    meta = None
    prefix = None
    run = None
    grid_by_t = {}
    agent_by_t = {}

    # Find META first
    for p in files:
        m = META_RE.match(p.name)
        if m:
            meta = p
            prefix = m.group("prefix")
            run = m.group("run")  # may be None
            break

    if meta is None:
        raise FileNotFoundError("Could not find *_META.csv (excluding ._* files)")

    # Find GRID / AGENT for same prefix (+ same run if present)
    for p in files:
        mg = GRID_RE.match(p.name)
        if mg:
            same_prefix = (mg.group("prefix") == prefix)
            same_run = (mg.group("run") == run)  # works even if both None
            if same_prefix and same_run:
                t = int(mg.group("timestep"))
                grid_by_t[t] = p
            continue

        ma = AGENT_RE.match(p.name)
        if ma:
            same_prefix = (ma.group("prefix") == prefix)
            same_run = (ma.group("run") == run)
            if same_prefix and same_run:
                t = int(ma.group("timestep"))
                agent_by_t[t] = p
            continue

    if not grid_by_t:
        raise FileNotFoundError("No *_GRID.csv files found for detected run.")

    timesteps = sorted(grid_by_t.keys())
    return {
        "prefix": prefix,
        "run": run,
        "meta_csv": meta,
        "grid_by_t": grid_by_t,
        "agent_by_t": agent_by_t,
        "timesteps": timesteps,
    }

def build_grid_frame_from_csv(grid_csv: Path, height: int, width: int):
    grid = np.zeros((height, width), dtype=np.float32)
    seen = set()

    with open(grid_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = int(row["row"])
            c = int(row["col"])
            v = float(row["sugarCount"])

            if not (0 <= r < height and 0 <= c < width):
                raise ValueError(f"Out-of-bounds cell ({r},{c}) in {grid_csv.name}")

            grid[r, c] = v
            seen.add((r, c))

    # Optional strict check: expect full grid
    expected = height * width
    if len(seen) != expected:
        print(f"Warning: {grid_csv.name} has {len(seen)} unique cells, expected {expected}")

    return grid

def export_grid_long_csv(timesteps, grids, out_csv):
    T, H, W = grids.shape
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestep", "x", "y", "value"])
        for i, t in enumerate(timesteps):
            g = grids[i]
            for y in range(H):
                for x in range(W):
                    writer.writerow([int(t), x, y, float(g[y, x])])

def export_entities_long_csv(agent_by_t, out_csv):
    if not agent_by_t:
        return False

    fieldnames = ["timestep", "id", "x", "y", "wealth", "age", "deathAge", "isMale", "isFertile"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for t in sorted(agent_by_t.keys()):
            path = agent_by_t[t]
            with open(path, "r", newline="", encoding="utf-8") as af:
                for row in csv.DictReader(af):
                    w.writerow({
                        "timestep": t,
                        "id": int(row["agentID"]),
                        "x": int(row["col"]),
                        "y": int(row["row"]),
                        "wealth": float(row["wealth"]),
                        "age": int(row["age"]),
                        "deathAge": int(row["deathAge"]),
                        "isMale": int(row["isMale"]),
                        "isFertile": int(row["isFertile"]),
                    })
    return True

def write_run_json(meta_row, timesteps, input_dir, meta_csv_name, outputs, prefix, run, agent_exists):
    height = int(float(meta_row["Height"]))
    width = int(float(meta_row["width"]))
    total_timesteps_declared = int(float(meta_row["timesteps"]))
    sugar_max = float(meta_row.get("sugarCapacityMax", 0))

    start_t = int(timesteps[0]) if timesteps else 0
    end_t = int(timesteps[-1]) if timesteps else 0
    count_t = len(timesteps)

    run_cfg = {
        "schema_version": "1.0",
        "run": {
            "app_name": "SugarScape",
            "framework": "MASS",
            "backend": "CPU",
            "dimensions": {"type": "grid2d", "width": width, "height": height},
            "value_type": "float32",
            "value_range": {"min": 0.0, "max": sugar_max},
            "timesteps": {"start": start_t, "end": end_t, "count": count_t},
            "state_type": "grid2d",
            "state_semantics": "sugarCount",
            "notes": f"Source meta declares total timesteps={total_timesteps_declared}. Parsed {count_t} GRID frames."
        },
        "input": {
            "folder": str(input_dir),
            "meta_csv": str(Path(input_dir) / meta_csv_name),
            "prefix": prefix,
            "run_id": run if run is not None else ""
        },
        "outputs": outputs,
        "visualization": {
            "frame_stride": 1,
            "show_entities": bool(agent_exists),
            "show_metrics": Path(input_dir, "visualization_parameters.csv").exists()  # just a placeholder flag pattern
        }
    }

    with open(RUN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(run_cfg, f, indent=2)
    print(f"Wrote {RUN_JSON_PATH}")

def main():
    folder = Path(INPUT_DIR)
    if not folder.exists():
        raise FileNotFoundError(f"Input folder not found: {folder.resolve()}")

    detected = detect_sugarscape_files(folder)
    prefix = detected["prefix"]
    run = detected["run"]
    meta_csv = detected["meta_csv"]
    grid_by_t = detected["grid_by_t"]
    agent_by_t = detected["agent_by_t"]
    timesteps = detected["timesteps"]

    meta_row = read_single_row_csv(meta_csv)
    height = int(float(meta_row["Height"]))
    width = int(float(meta_row["width"]))

    grids = []
    for t in timesteps:
        frame = build_grid_frame_from_csv(grid_by_t[t], height, width)
        grids.append(frame)

    grids = np.stack(grids, axis=0).astype(np.float32, copy=False)
    t_arr = np.array(timesteps, dtype=np.int32)

    # Canonical outputs (same pattern as Heat2D)
    out_npz = "state.npz"
    out_grid_long = "grid_long.csv"
    out_entities = "entities_long.csv"

    np.savez_compressed(out_npz, timesteps=t_arr, grids=grids)
    print(f"Wrote {out_npz} with grids shape {grids.shape}")

    export_grid_long_csv(timesteps, grids, out_grid_long)
    print(f"Wrote {out_grid_long}")

    agent_exists = export_entities_long_csv(agent_by_t, out_entities)
    if agent_exists:
        print(f"Wrote {out_entities}")
    else:
        print("No AGENT files found; skipped entities export.")

    outputs = {
        "grid_npz": out_npz,
        "grid_long_csv": out_grid_long,
        "entities_csv": out_entities if agent_exists else "",
        "metrics_csv": "metrics.csv" if (folder / f"{prefix}_TIMESTEPCONSTANTS.csv").exists() else "",
        "viz_params_csv": str(folder / "visualization_parameters.csv") if (folder / "visualization_parameters.csv").exists() else ""
    }

    write_run_json(
        meta_row=meta_row,
        timesteps=timesteps,
        input_dir=folder,
        meta_csv_name=meta_csv.name,
        outputs=outputs,
        prefix=prefix,
        run=run,
        agent_exists=agent_exists
    )

if __name__ == "__main__":
    main()