import re
import csv
import json 
import numpy as np
from pathlib import Path 
'''
Writes: 
- heat2d_gids.npz with arrays: 
    - timesteps: shape (T,) int32
    - grids: shape (T,H,W) float32
- heat2d_long.csv with columns: timestep,x,y,value
'''
TIME_RE = re.compile(r"\btime\s*=\s*(\d+)\b")

def load_run_config(path = "run.json"):
    with open (path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def parse_heat2d(path, grid_h=100, grid_w=100, max_steps=None):
    """
        Parses a Heat2D-style output file that contains:
            - 'time = N' headers
            - followed by grid_h lines each with grid_w floats
      - interleaved with arbitrary debug/CUDA logs

    Returns:
    timesteps: list[int]
    grids: np.ndarray shape (T, grid_h, grid_w) dtype=np.float32
    """
    timesteps = []
    grids = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = iter(f)

        for line in lines:
            m = TIME_RE.search(line)
            if not m:
                continue

            t = int(m.group(1))

            # Read the next grid_h lines that look like a row of floats
            grid_rows = []
            while len(grid_rows) < grid_h:
                try:
                    row_line = next(lines)
                except StopIteration:
                    break

                row_line = row_line.strip()
                if not row_line:
                    continue

                parts = row_line.split()
                # Only accept rows that match expected width and are numeric
                try:
                    row_vals = [float(p) for p in parts]
                except ValueError:
                    row_vals = None

                if row_vals is not None and len(row_vals) == grid_w:
                    grid_rows.append(row_vals)
                # else: it's likely a debug/log line; skip it

            if len(grid_rows) == grid_h:
                timesteps.append(t)
                grids.append(np.array(grid_rows, dtype=np.float32))

                if max_steps is not None and len(grids) >= max_steps:
                    break

    if not grids:
        raise ValueError("No grids found. Check that your file contains 'time = N' and 100x100 float grids.")

    grids = np.stack(grids, axis=0).astype(np.float32, copy=False)  # (T,H,W)
    return timesteps, grids


def export_long_csv(timesteps, grids, out_csv):
    """
    Writes long-format CSV: timestep,x,y,value
    """
    T, H, W = grids.shape
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestep", "x", "y", "value"])
        for i, t in enumerate(timesteps):
            g = grids[i]
            for y in range(H):
                for x in range(W):
                    writer.writerow([t, x, y, float(g[y, x])])


def main(config_path="run.json"):
    config = load_run_config(config_path)

    dims = config["run"]["dimensions"]
    grid_w = int(dims["width"])
    grid_h = int(dims["height"])

    in_file = config["input"]["raw_log"]
    out_npz = config["outputs"]["grid_npz"]
    out_csv = config["outputs"]["grid_long_csv"]
    timesteps, grids = parse_heat2d(in_file, grid_h=grid_h, grid_w=grid_w)

    # Save structured data
    export_long_csv(timesteps, grids, out_csv)
    np.savez_compressed(
        out_npz,
        timesteps=np.array(timesteps, dtype=np.int32),
        grids=grids
    )

    print(f"Parsed {len(timesteps)} timesteps.")
    print(f"Wrote: {out_csv} and {out_npz}")

if __name__ == "__main__":
    main()
