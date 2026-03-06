import json
import numpy as np
import plotly.graph_objects as go

'''
Current script needs: state.npz

Future cleaner version should use: state.npz + run.json

If you later overlay agents, it may also use: entities_long.csv

visualize_plotly loads processed data and renders the animated heatmap. 

Note: This script needs to be updated to visualize agents, hearts, side metrics, and grid lines from visualization parameters. 
Now, it only visualizes sugar grid values over time. 
'''

def load_run_config(path="run.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_run_config("run.json")

    npz_path = cfg["outputs"]["grid_npz"]
    stride = int(cfg.get("visualization", {}).get("frame_stride", 1))

    data = np.load(npz_path)

    if "timesteps" not in data or "grids" not in data:
        raise ValueError(f"{npz_path} must contain 'timesteps' and 'grids' arrays")

    timesteps = data["timesteps"]
    grids = data["grids"]   # expected shape (T,H,W)

    if stride > 1:
        timesteps = timesteps[::stride]
        grids = grids[::stride]

    frames = []
    for i in range(len(timesteps)):
        frames.append(
            go.Frame(
                data=[go.Heatmap(z=grids[i])],
                name=str(int(timesteps[i]))
            )
        )

    fig = go.Figure(
        data=[go.Heatmap(z=grids[0])],
        frames=frames
    )

    fig.update_layout(
        title=cfg["run"].get("app_name", "Visualization"),
        sliders=[{
            "steps": [
                {
                    "args": [[str(int(t))], {"frame": {"duration": 0, "redraw": True}}],
                    "label": str(int(t)),
                    "method": "animate"
                }
                for t in timesteps
            ]
        }]
    )

    fig.show()


if __name__ == "__main__":
    main()