# Steps to run Heat2D MASS simulation

## 1) Build once
```
make develop LLVM_PREBUILD_DOWNLOAD_URL=https://github.com/llvm/llvm-project/releases/download/llvmorg-14.0.6/clang+llvm-14.0.6-x86_64-linux-gnu-rhel-8.4.tar.xz
make build
```

## 2) Run the simulation (manual)
Use `--help` to see parameters. You must use `--verbose` to print the grid.
Example:
```
./bin/Heat2D_PlaceV2 --interval 1 --verbose
```

Max size as of MASS v0.7.2, this implementation as of 5/10/2024, is 3083.

## 3) Visualize using run.sh (recommended)
`run.sh` runs the full pipeline:
1. Run the simulation and write `log.txt`.
2. Parse `log.txt` into `heat2d_long.csv` and `heat2d_grids.npz`.
3. Install Plotly if needed.
4. Launch `visualize_plotly.py`.

Run it like this:
```
sh run.sh
```

## 4) Visualize manually (optional)
If you want to run each step yourself:
```
./bin/Heat2D_PlaceV2 --interval 1 --verbose > log.txt
python3 parse_heat2d.py
python3 -m pip install --user plotly
python3 visualize_plotly.py
```

## 5) Optional: simviz build
```
make build-simviz
./bin/simviz heat2d.viz
```

## Python virtual environment (UB)
If you are on UB, you can create a Python virtual environment to isolate packages:
```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install plotly
```