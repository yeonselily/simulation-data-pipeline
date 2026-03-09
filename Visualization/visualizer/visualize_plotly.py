import json
import csv
import numpy as np
import plotly.graph_objects as go

'''
Current script uses:
    - run.json
    - state.npz
    - entities_long.csv (optional, only when agent overlay is enabled)

visualize_plotly loads processed data and renders an animated Plotly heatmap.

What it currently supports:
    - grid-based animation from state.npz
    - conditional agent overlay from entities_long.csv
    - timestep slider and play/pause controls
    - configuration-driven loading through run.json

How agent overlay works:
    - Agents are only rendered if:
        1. visualization.show_entities == true in run.json
        2. outputs.entities_csv is present and non-empty in run.json

This allows the same script to support:
    - grid-only simulations (e.g., Heat2D)
    - grid + agents simulations (e.g., SugarScape)

What it does not yet support:
    - fertility heart icons as separate symbols
    - side metrics from TIMESTEPCONSTANTS
    - grid line styling / color gradients from visualization_parameters.csv
    - richer legend / styling rules beyond the current built-in agent coloring
'''

def load_run_config(path="run.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_entities_csv(path):
    entities_by_t = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = int(row["timestep"])
            entities_by_t.setdefault(t, []).append({
                "id": int(row["id"]),
                "x": int(row["x"]),
                "y": int(row["y"]),
                "wealth": float(row["wealth"]),
                "age": int(row["age"]),
                "deathAge": int(row["deathAge"]),
                "isMale": int(row["isMale"]),
                "isFertile": int(row["isFertile"]),
            })
    return entities_by_t

def make_agent_trace(agent_rows):
    xs = [a["x"] for a in agent_rows]
    ys = [a["y"] for a in agent_rows]

    colors = []
    for a in agent_rows:
        '''
        - Blue dot → male that can reproduce
        - Red dot → female that can reproduce
        - Light blue dot → male too young/old to reproduce
        - Pink dot → female too young/old to reproduce
        '''
        if a["isFertile"] == 1 and a["isMale"] == 1:
            colors.append("blue")
        elif a["isFertile"] == 1 and a["isMale"] == 0:
            colors.append("red")
        elif a["isFertile"] == 0 and a["isMale"] == 1:
            colors.append("lightblue")
        else:
            colors.append("pink")

    hover_text = [
        f"<b>Agent {a['id']}</b><br>"
        f"Wealth: {a['wealth']}<br>"
        f"Age: {a['age']} / {a['deathAge']}<br>"
        f"Sex: {'Male' if a['isMale'] == 1 else 'Female'}<br>"
        f"Fertile: {'Yes' if a['isFertile'] == 1 else 'No'}"
        for a in agent_rows
    ]

    return go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name="Agents",
        marker=dict(size=8, color=colors, line=dict(width=1, color="black")),
        text=hover_text,
        hoverinfo="text",
        showlegend=False
    )


def main():
    cfg = load_run_config("run.json")
    print("Loaded config:", json.dumps(cfg, indent=2))

    npz_path = cfg["outputs"]["grid_npz"]
    stride = int(cfg.get("visualization", {}).get("frame_stride", 1))

    show_entities = bool(cfg.get("visualization", {}).get("show_entities", False))
    entities_path = cfg["outputs"].get("entities_csv", "")
    use_entities = show_entities and bool(entities_path)

    data = np.load(npz_path)
    timesteps = data["timesteps"]
    grids = data["grids"]
    print(f"Loaded NPZ with timesteps {timesteps.shape} and grids {grids.shape}")

    if stride > 1:
        timesteps = timesteps[::stride]
        grids = grids[::stride]

    entities_by_t = load_entities_csv(entities_path) if use_entities else {}
    print(f"Loaded entities for {len(entities_by_t)} timesteps")

    zmin = float(cfg["run"].get("value_range", {}).get("min", np.nanmin(grids)))
    zmax = float(cfg["run"].get("value_range", {}).get("max", np.nanmax(grids)))

    frames = []
    for i, t in enumerate(timesteps):
        traces = [
            go.Heatmap(
                z=grids[i],
                zmin=zmin,
                zmax=zmax,
                colorbar=dict(title=cfg["run"].get("state_semantics", "Value"))
            )
        ]

        if use_entities:
            traces.append(make_agent_trace(entities_by_t.get(int(t), [])))

        frames.append(go.Frame(data=traces, name=str(int(t))))
    print(f"Constructed {len(frames)} frames for animation")

    initial_traces = [
        go.Heatmap(
            z=grids[0],
            zmin=zmin,
            zmax=zmax,
            colorbar=dict(title=cfg["run"].get("state_semantics", "Value"))
        )
    ]

    if use_entities:
        initial_traces.append(make_agent_trace(entities_by_t.get(int(timesteps[0]), [])))

    fig = go.Figure(data=initial_traces, frames=frames)

    fig.update_layout(
        title=cfg["run"].get("app_name", "Visualization"),
        xaxis=dict(title="x"),
        yaxis=dict(title="y", autorange="reversed"),
        sliders=[{
            "steps": [
                {
                    "args": [[str(int(t))], {"frame": {"duration": 0, "redraw": True}}],
                    "label": str(int(t)),
                    "method": "animate"
                }
                for t in timesteps
            ]
        }],

        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {
                        "mode": "immediate",
                        "transition": {"duration": 0},
                        "frame": {"duration": 300, "redraw": True}
                    }]
                },
                {
                    "label": "Pause",
                    "method": "animate",
                    "args": [[None], {
                        "mode": "immediate",
                        "transition": {"duration": 0},
                        "frame": {"duration": 0, "redraw": False}
                    }]
                }
            ]
        }]
    )

    # fig.show()
    print("About to show figure. If running in a non-interactive environment, this may not work. Instead, we will save to HTML.")
    out_html = "visualization.html"
    fig.write_html(out_html, auto_open=False, auto_play=False)
    print(f"Wrote {out_html}")


if __name__ == "__main__":
    main()