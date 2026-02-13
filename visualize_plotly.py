import numpy as np
import plotly.graph_objects as go

data = np.load("heat2d_grids.npz")

timesteps = data["timesteps"]
grids = data["grids"]   # shape (T,H,W)

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
