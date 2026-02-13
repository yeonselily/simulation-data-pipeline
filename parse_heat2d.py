import re
import csv
import numpy as np

TIME_RE = re.compile(r"\btime\s*=\s*(\d+)\b")

def parse_heat2d(path, grid_h=100, grid_w=100, max_steps=None):
    """
    Parses a Heat2D-style output file that contains:
      - 'time = N' headers
      - followed by grid_h lines each with grid_w ints
      - interleaved with arbitrary debug/CUDA logs

    Returns:
      timesteps: list[int]
      grids: np.ndarray shape (T, grid_h, grid_w) dtype=int
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

            # Read the next grid_h lines that look like a row of integers
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
                if len(parts) == grid_w and all(p.lstrip("-").isdigit() for p in parts):
                    grid_rows.append([int(p) for p in parts])
                # else: it's likely a debug/log line; skip it

            if len(grid_rows) == grid_h:
                timesteps.append(t)
                grids.append(np.array(grid_rows, dtype=int))

                if max_steps is not None and len(grids) >= max_steps:
                    break

    if not grids:
        raise ValueError("No grids found. Check that your file contains 'time = N' and 100x100 integer grids.")

    grids = np.stack(grids, axis=0)  # (T,H,W)
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
                    writer.writerow([t, x, y, int(g[y, x])])


def main():
    in_file = "log.txt"  # change to your filename
    timesteps, grids = parse_heat2d(in_file, grid_h=100, grid_w=100)

    # Save structured data
    export_long_csv(timesteps, grids, "heat2d_long.csv")
    np.savez_compressed(
        "heat2d_grids.npz",
        timesteps=np.array(timesteps, dtype=int),
        grids=grids
    )

    print(f"Parsed {len(timesteps)} timesteps.")
    print("Wrote: heat2d_long.csv and heat2d_grids.npz")

if __name__ == "__main__":
    main()
