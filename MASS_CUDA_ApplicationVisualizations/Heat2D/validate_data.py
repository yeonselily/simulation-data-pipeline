import json
import numpy as np

'''
Check if the NPZ file contains valid data for visualization:
- timesteps exists and is 1D
- grids exists and is 3D
- len(timesteps) == grids.shape[0]
- grids.shape[1:3] == (height, width) from run.json
- dtype is float-ish
- values are within configured range (if provided)

After loading the arrays from the NPZ, 
validate that those arrays match the expected 
structure from run.json.
'''

def load_run_config(path="run.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_heat2d_npz(npz_path, config_path="run.json"):
    cfg = load_run_config(config_path)
    dims = cfg["run"]["dimensions"]
    H = int(dims["height"])
    W = int(dims["width"])

    value_range = cfg["run"].get("value_range", None)
    data = np.load(npz_path)

    if "timesteps" not in data or "grids" not in data:
        raise ValueError("NPZ must contain 'timesteps' and 'grids' arrays")

    timesteps = data["timesteps"]
    grids = data["grids"]

    if timesteps.ndim != 1:
        raise ValueError(f"timesteps must be 1D, got shape {timesteps.shape}")

    if grids.ndim != 3:
        raise ValueError(f"grids must be 3D (T,H,W), got shape {grids.shape}")

    if grids.shape[0] != len(timesteps):
        raise ValueError("Mismatch: len(timesteps) != grids.shape[0]")

    if grids.shape[1] != H or grids.shape[2] != W:
        raise ValueError(f"Grid shape mismatch. Expected (T,{H},{W}), got {grids.shape}")

    if value_range:
        vmin = float(value_range["min"])
        vmax = float(value_range["max"])
        gmin = float(np.nanmin(grids))
        gmax = float(np.nanmax(grids))
        if gmin < vmin or gmax > vmax:
            raise ValueError(f"Grid values out of range [{vmin}, {vmax}]: observed [{gmin}, {gmax}]")

    return True

if __name__ == "__main__":
    cfg = load_run_config("run.json")
    npz_path = cfg["outputs"]["grid_npz"]
    validate_heat2d_npz(npz_path, "run.json")
    print("Validation passed.")