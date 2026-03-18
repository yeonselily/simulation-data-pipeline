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

Tuberculosis-specific visualization semantics:
    - Background heatmap:
        - chemokine level 0 -> light gray
        - chemokine level 1 -> orange (255, 140, 0)
        - chemokine level 2 -> red (255, 0, 0)
    - Overlays:
        - Bacteria: dark navy (0, 0, 128)
        - Macrophage state:
            0 (RESTING)              -> green
            1 (INFECTED)             -> yellow
            2 (ACTIVATED)            -> cyan
            3 (CHRONICALLY_INFECTED) -> purple
        - T-cell: blue
        - Blood vessel (if exported): purple markers on grid cells

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

def make_grid_overlay_trace(channel_grid, name, color, t_index):
    """
    For Tuberculosis:
    - channel_grid: (T,H,W) int/bool array
    - name: legend name (e.g. "Bacteria")
    - color: marker color
    - t_index: index into T
    Creates a scatter of all cells where channel_grid[t_index] != 0.
    """
    layer = channel_grid[t_index]
    ys, xs = np.nonzero(layer)  # note: y=row, x=col

    if xs.size == 0:
        # No points this frame; return an empty trace so Plotly layout is stable
        return go.Scatter(
            x=[],
            y=[],
            mode="markers",
            name=name,
            marker=dict(size=6, color=color),
            showlegend=False,
        )

    return go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=name,
        marker=dict(size=6, color=color, line=dict(width=0)),
        showlegend=True,
        hoverinfo="skip",
    )

def make_macrophage_state_traces(mstate_grid, t_index):
    """
    Create one scatter trace per macrophage state (0–3), skipping cells with -1.

    State semantics per specification:
        0 = RESTING
        1 = INFECTED
        2 = ACTIVATED
        3 = CHRONICALLY_INFECTED
    """
    layer = mstate_grid[t_index]

    state_info = [
        (0, "Macrophage RESTING", "green"),
        (1, "Macrophage INFECTED", "yellow"),
        (2, "Macrophage ACTIVATED", "cyan"),
        (3, "Macrophage CHRONIC", "purple"),
    ]

    traces = []
    for value, name, color in state_info:
        ys, xs = np.where(layer == value)
        if xs.size == 0:
            # Empty trace to keep legend stable if needed
            traces.append(
                go.Scatter(
                    x=[],
                    y=[],
                    mode="markers",
                    name=name,
                    marker=dict(size=6, color=color),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            continue

        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name=name,
                marker=dict(size=6, color=color, line=dict(width=0)),
                showlegend=True,
                hoverinfo="skip",
            )
        )

    return traces

def get_default_layout(has_heatmap=True, has_overlay_legend=False):
    """
    Generic layout policy:
    - If a heatmap and overlay legend coexist, move legend to the top
      so it does not overlap the colorbar.
    - Otherwise use normal margins.
    """
    layout = {
        "xaxis": dict(title="x"),
        "yaxis": dict(title="y", autorange="reversed"),
    }

    if has_heatmap and has_overlay_legend:
        layout["legend"] = dict(
            orientation="h",
            y=1.08,
            x=0.0,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.8)"
        )
        layout["margin"] = dict(t=90, r=100)
    else:
        layout["margin"] = dict(t=60, r=60)

    return layout

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

    # Detect application type
    app_name = cfg["run"].get("app_name", "").lower()
    is_tb = app_name.startswith("tuberculosis")
    is_heat2d = app_name.startswith("heat2d")
    chemokine = data["chemokine"] if ("chemokine" in data and is_tb) else None
    bacteria = data["bacteria"] if ("bacteria" in data and is_tb) else None
    macrophage = data["macrophage"] if ("macrophage" in data and is_tb) else None
    macrophage_state = data["macrophageState"] if ("macrophageState" in data and is_tb) else None
    tcell = data["tcell"] if ("tcell" in data and is_tb) else None
    blood = data["bloodVessel"] if ("bloodVessel" in data and is_tb) else None

    if stride > 1:
        timesteps = timesteps[::stride]
        grids = grids[::stride]
        if chemokine is not None:
            chemokine = chemokine[::stride]
            bacteria = bacteria[::stride]
            macrophage = macrophage[::stride]
            macrophage_state = macrophage_state[::stride] if macrophage_state is not None else None
            tcell = tcell[::stride]
            if blood is not None:
                blood = blood[::stride]
    
    entities_by_t = load_entities_csv(entities_path) if use_entities else {}
    print(f"Loaded entities for {len(entities_by_t)} timesteps")

    zmin = float(cfg["run"].get("value_range", {}).get("min", np.nanmin(grids)))
    zmax = float(cfg["run"].get("value_range", {}).get("max", np.nanmax(grids)))

    # Label for scalar field in hover (e.g., "Temperature", "Chemokine level")
    value_label = cfg["run"].get("state_semantics", "value")

    frames = []
    for i, t in enumerate(timesteps):
        # Choose heatmap styling:
        # - For Tuberculosis, use discrete 0/1/2 -> gray/orange/red with fixed range
        # - For Heat2D, let Plotly auto-scale per frame (match original Heat2D viz)
        # - For other apps, use a generic continuous colorscale with global zmin/zmax
        heatmap_kwargs = {
            "z": grids[i],
            "hovertemplate": f"x: %{{x}}<br>y: %{{y}}<br>{value_label}: %{{z}}<extra></extra>",
        }

        if is_tb and chemokine is not None:
            heatmap_kwargs.update(
                colorscale=[
                    [0.0, "rgb(230,230,230)"],
                    [0.4999, "rgb(230,230,230)"],
                    [0.5, "rgb(255,140,0)"],
                    [0.8333, "rgb(255,140,0)"],
                    [0.8334, "rgb(255,0,0)"],
                    [1.0, "rgb(255,0,0)"],
                ],
                colorbar=dict(
                    title=cfg["run"].get("state_semantics", "Value"),
                    tickmode="array",
                    tickvals=[0, 1, 2],
                ),
                zmin=zmin,
                zmax=zmax,
                showscale=True,
            )
        elif is_heat2d:
            # Per-frame autoscale, no fixed zmin/zmax
            heatmap_kwargs.update(
                colorbar=dict(title=cfg["run"].get("state_semantics", "Value")),
                showscale=True,
            )
        else:
            heatmap_kwargs.update(
                colorscale="Viridis",
                colorbar=dict(title=cfg["run"].get("state_semantics", "Value")),
                zmin=zmin,
                zmax=zmax,
                showscale=True,
            )

        traces = [go.Heatmap(**heatmap_kwargs)]

        if use_entities:
            traces.append(make_agent_trace(entities_by_t.get(int(t), [])))

        # Tuberculosis: grid-based overlays, if channels exist
        if is_tb and chemokine is not None:
            if bacteria is not None:
                traces.append(make_grid_overlay_trace(bacteria, "Bacteria", "rgb(0,0,128)", i))
            # Macrophage state overlay (categorical), if available
            if macrophage_state is not None:
                traces.extend(make_macrophage_state_traces(macrophage_state, i))
            elif macrophage is not None:
                # Fallback: simple macrophage presence overlay
                traces.append(make_grid_overlay_trace(macrophage, "Macrophage", "orange", i))
            if tcell is not None:
                traces.append(make_grid_overlay_trace(tcell, "T-cell", "blue", i))
            if blood is not None:
                traces.append(make_grid_overlay_trace(blood, "Blood vessel", "purple", i))

        frames.append(go.Frame(data=traces, name=str(int(t))))
    print(f"Constructed {len(frames)} frames for animation")

    # Same heatmap styling for the initial frame as in the animation frames
    init_heatmap_kwargs = {
        "z": grids[0],
        "hovertemplate": f"x: %{{x}}<br>y: %{{y}}<br>{value_label}: %{{z}}<extra></extra>",
    }

    if is_tb and chemokine is not None:
        init_heatmap_kwargs.update(
            colorscale=[
                [0.0, "rgb(230,230,230)"],
                [0.4999, "rgb(230,230,230)"],
                [0.5, "rgb(255,140,0)"],
                [0.8333, "rgb(255,140,0)"],
                [0.8334, "rgb(255,0,0)"],
                [1.0, "rgb(255,0,0)"],
            ],
            colorbar=dict(
                title=cfg["run"].get("state_semantics", "Value"),
                tickmode="array",
                tickvals=[0, 1, 2],
            ),
            zmin=zmin,
            zmax=zmax,
        )
    elif is_heat2d:
        init_heatmap_kwargs.update(
            colorbar=dict(title=cfg["run"].get("state_semantics", "Value")),
        )
    else:
        init_heatmap_kwargs.update(
            colorscale="Viridis",
            colorbar=dict(title=cfg["run"].get("state_semantics", "Value")),
            zmin=zmin,
            zmax=zmax,
        )

    initial_traces = [go.Heatmap(**init_heatmap_kwargs)]

    if use_entities:
        initial_traces.append(make_agent_trace(entities_by_t.get(int(timesteps[0]), [])))

    if is_tb and chemokine is not None:
        if bacteria is not None:
            initial_traces.append(make_grid_overlay_trace(bacteria, "Bacteria", "rgb(0,0,128)", 0))
        if macrophage_state is not None:
            initial_traces.extend(make_macrophage_state_traces(macrophage_state, 0))
        elif macrophage is not None:
            initial_traces.append(make_grid_overlay_trace(macrophage, "Macrophage", "orange", 0))
        if tcell is not None:
            initial_traces.append(make_grid_overlay_trace(tcell, "T-cell", "blue", 0))
        if blood is not None:
            initial_traces.append(make_grid_overlay_trace(blood, "Blood vessel", "purple", 0))

    has_overlay_legend = len(initial_traces) > 1

    fig = go.Figure(data=initial_traces, frames=frames)

    layout_cfg = get_default_layout(
        has_heatmap=True,
        has_overlay_legend=has_overlay_legend
    )

    fig.update_layout(
        title=cfg["run"].get("app_name", "Visualization"),
        xaxis=layout_cfg["xaxis"],
        yaxis=layout_cfg["yaxis"],
        margin=layout_cfg["margin"],
        legend=layout_cfg.get("legend"),
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