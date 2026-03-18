import json
import numpy as np

"""
Tuberculosis validator

Input:
- state.npz  (from Tuberculosis/parse_sugarscape.py)
- run.json   (metadata)

Checks:
- Basic NPZ/run.json consistency (T,H,W)
- Presence and shapes of core channels: chemokine, bacteria, macrophage, macrophageState, tcell
- grids == chemokine alias
- Value ranges respect specification.md
"""

def load_run_config(path="run.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_tb_npz(config_path="run.json"):
    cfg = load_run_config(config_path)

    npz_path = cfg["outputs"]["grid_npz"]
    dims = cfg["run"]["dimensions"]
    H = int(dims["height"])
    W = int(dims["width"])

    run = cfg["run"]
    max_chemokine = int(run.get("chemokine_max", run.get("value_range", {}).get("max", 2)))

    data = np.load(npz_path)

    # Required arrays
    required_keys = ["timesteps", "grids", "chemokine", "bacteria", "macrophage", "macrophageState", "tcell"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"NPZ must contain '{k}' array for Tuberculosis")

    timesteps = data["timesteps"]
    grids = data["grids"]
    chemokine = data["chemokine"]
    bacteria = data["bacteria"]
    macrophage = data["macrophage"]
    mstate = data["macrophageState"]
    tcell = data["tcell"]
    blood = data["bloodVessel"] if "bloodVessel" in data else None

    if timesteps.ndim != 1:
        raise ValueError(f"timesteps must be 1D, got shape {timesteps.shape}")

    T = len(timesteps)

    def check_shape(name, arr):
        if arr.ndim != 3:
            raise ValueError(f"{name} must be 3D (T,H,W), got shape {arr.shape}")
        if arr.shape[0] != T or arr.shape[1] != H or arr.shape[2] != W:
            raise ValueError(f"{name} shape mismatch. Expected (T,{H},{W}), got {arr.shape}")

    check_shape("grids", grids)
    check_shape("chemokine", chemokine)
    check_shape("bacteria", bacteria)
    check_shape("macrophage", macrophage)
    check_shape("macrophageState", mstate)
    check_shape("tcell", tcell)
    if blood is not None:
        check_shape("bloodVessel", blood)

    # grids must be the chemokine alias
    if not np.array_equal(grids, chemokine):
        raise ValueError("Expected 'grids' to be identical to 'chemokine' for Tuberculosis")

    # Value range checks (from specification.md)
    if np.any((bacteria < 0) | (bacteria > 1)):
        raise ValueError("bacteria must be in {0,1}")

    if np.any((macrophage < 0) | (macrophage > 1)):
        raise ValueError("macrophage must be in {0,1}")

    allowed_mstate = np.array([-1, 0, 1, 2, 3], dtype=mstate.dtype)
    if not np.isin(mstate, allowed_mstate).all():
        raise ValueError("macrophageState must be in {-1,0,1,2,3}")

    if np.any((tcell < 0) | (tcell > 1)):
        raise ValueError("tcell must be in {0,1}")

    if np.any((chemokine < 0) | (chemokine > max_chemokine)):
        gmin = int(chemokine.min())
        gmax = int(chemokine.max())
        raise ValueError(
            f"chemokine out of range [0,{max_chemokine}]: observed [{gmin},{gmax}]"
        )

    if blood is not None:
        if np.any((blood < 0) | (blood > 1)):
            raise ValueError("bloodVessel must be in {0,1}")

    return True


if __name__ == "__main__":
    validate_tb_npz("run.json")
    print("Tuberculosis validation passed.")