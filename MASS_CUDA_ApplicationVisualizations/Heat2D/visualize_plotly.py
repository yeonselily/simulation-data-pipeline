import numpy as np
import plotly.graph_objects as go

data = np.load("heat2d_grids.npz")

timesteps = data["timesteps"]
grids = data["grids"]   # shape (T,H,W)

# Downsample frames for faster visualization.
stride = 5
if stride > 1:
    timesteps = timesteps[::stride]
    grids = grids[::stride]

# Create frames
frames = []

for i in range(len(timesteps)):
    frames.append(
        go.Frame(
            data=[go.Heatmap(z=grids[i])],
            name=str(timesteps[i])
        )
    )

# Initial figure
fig = go.Figure(
    data=[go.Heatmap(z=grids[0])],
    frames=frames
)

# Add slider
fig.update_layout(
    sliders=[{
        "steps":[
            {"args":[[str(t)],{"frame":{"duration":0,"redraw":True}}],
             "label":str(t),
             "method":"animate"} 
            for t in timesteps
        ]
    }]
)

fig.show()
