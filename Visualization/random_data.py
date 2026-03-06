'''
Below is a Python script that generates:

1. *_TIMESTEPCONSTANTS.csv (from your existing META/GRID/AGENT,
 with placeholders where impossible)

2. visualization_parameters.csv (default values)

It also ignores macOS metadata files like ._serial_000010_GRID.csv.

agent existence 

TB 
'''
import csv
import re
import math
import random
from pathlib import Path

# ---------- Config ----------
INPUT_DIR = "input_files"   # folder containing SugarScape CSV files
USE_RANDOM_PLACEHOLDERS = True  # for conflictCount / meanVision / meanMetabolism
RANDOM_SEED = 42

# Default visualization params if missing
DEFAULT_VIZ_PARAMS = {
    "gradientStartHex": "#F5F5DC",   # beige
    "gradientEndHex":   "#8B4513",   # brown
    "showGridLine": 1,
    "gridLineHex": "#333333",
    "gridLineThickness": 1.0
}

# ---------- Filename patterns ----------
# Supports BOTH:
#   serial_META.csv
#   CILK_000001_META.csv
# and similarly for GRID/AGENT files.
META_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_META\.csv$")
GRID_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_(?P<timestep>\d{6})_GRID\.csv$")
AGENT_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_(?P<timestep>\d{6})_AGENT\.csv$")
TIMESTEP_CONST_RE = re.compile(r"^(?P<prefix>.+?)(?:_(?P<run>\d{6}))?_TIMESTEPCONSTANTS\.csv$")
rng = random.Random(RANDOM_SEED)


def list_real_csvs(folder: Path):
    # Ignore macOS sidecar files (._*)
    return [p for p in folder.glob("*.csv") if not p.name.startswith("._")]


def read_single_row_csv(path: Path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No data rows in {path}")
    return rows[0]


def read_grid_total_sugar(grid_csv: Path):
    total = 0.0
    with open(grid_csv, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total += float(row["sugarCount"])
    return total


def read_agent_stats(agent_csv: Path):
    """
    Returns stats from one AGENT file:
      - liveAgentCount
      - totalWealth
      - averageWealth
      - sexRatio
      - fertileCount
      - giniWealth
      - ids (set)
    """
    wealths = []
    male_count = 0
    fertile_count = 0
    ids = set()

    with open(agent_csv, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            aid = int(row["agentID"])
            ids.add(aid)

            w = float(row["wealth"])
            wealths.append(w)

            is_male = int(row["isMale"])
            is_fertile = int(row["isFertile"])
            male_count += 1 if is_male == 1 else 0
            fertile_count += 1 if is_fertile == 1 else 0

    live = len(wealths)
    total_wealth = sum(wealths)
    avg_wealth = (total_wealth / live) if live > 0 else 0.0
    sex_ratio = (male_count / live) if live > 0 else 0.0
    gini = gini_coefficient(wealths)

    return {
        "liveAgentCount": live,
        "totalWealth": total_wealth,
        "averageWealth": avg_wealth,
        "sexRatio": sex_ratio,
        "fertileCount": fertile_count,
        "giniWealth": gini,
        "ids": ids,
    }


def gini_coefficient(values):
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return 0.0
    vals.sort()
    total = sum(vals)
    if total == 0:
        return 0.0
    cum = 0.0
    for i, x in enumerate(vals, start=1):
        cum += i * x
    return (2 * cum) / (n * total) - (n + 1) / n


def detect_run_files(folder: Path):
    files = list_real_csvs(folder)
    meta = None
    grid_by_t = {}
    agent_by_t = {}
    prefix = None
    run = None

    for p in files:
        m = META_RE.match(p.name)
        if m:
            meta = p
            prefix = m.group("prefix")
            run = m.group("run")
            continue

    if meta is None:
        raise FileNotFoundError("Could not find *_META.csv (excluding ._* files)")

    for p in files:
        mg = GRID_RE.match(p.name)
        if mg and mg.group("prefix") == prefix and mg.group("run") == run:
            t = int(mg.group("timestep"))
            grid_by_t[t] = p
            continue

        ma = AGENT_RE.match(p.name)
        if ma and ma.group("prefix") == prefix and ma.group("run") == run:
            t = int(ma.group("timestep"))
            agent_by_t[t] = p
            continue

    if not grid_by_t:
        raise FileNotFoundError("No *_GRID.csv files found for detected run.")
    if not agent_by_t:
        raise FileNotFoundError("No *_AGENT.csv files found for detected run.")

    common_ts = sorted(set(grid_by_t.keys()) & set(agent_by_t.keys()))
    if not common_ts:
        raise ValueError("No overlapping timesteps between GRID and AGENT files.")

    return prefix, run, meta, grid_by_t, agent_by_t, common_ts


def generate_timestepconstants(folder: Path):
    prefix, run, meta_csv, grid_by_t, agent_by_t, timesteps = detect_run_files(folder)

    meta = read_single_row_csv(meta_csv)

    if run:
        out_name = f"{prefix}_{run}_TIMESTEPCONSTANTS.csv"
    else:
        out_name = f"{prefix}_TIMESTEPCONSTANTS.csv"

    out_path = folder / out_name

    # Optional: use meta ranges to generate plausible placeholders
    vision_min = int(float(meta.get("visionMin", 1)))
    vision_max = int(float(meta.get("visionMax", max(vision_min, 1))))
    metabolism_min = int(float(meta.get("metabolismMin", 1)))
    metabolism_max = int(float(meta.get("metabolismMax", max(metabolism_min, 1))))

    fieldnames = [
        "timestep",
        "liveAgentCount",
        "birthCount",
        "deathCount",
        "totalWealth",
        "averageWealth",
        "totalSugarOnGrid",
        "conflictCount",
        "meanVision",
        "meanMetabolism",
        "sexRatio",
        "fertileCount",
        "giniWealth",
    ]

    prev_ids = None
    rows_out = []

    for t in timesteps:
        grid_csv = grid_by_t[t]
        agent_csv = agent_by_t[t]

        total_sugar = read_grid_total_sugar(grid_csv)
        a = read_agent_stats(agent_csv)
        curr_ids = a["ids"]

        if prev_ids is None:
            birth_count = 0
            death_count = 0
        else:
            birth_count = len(curr_ids - prev_ids)
            death_count = len(prev_ids - curr_ids)

        # Placeholders for fields that cannot be recovered exactly from provided files
        if USE_RANDOM_PLACEHOLDERS:
            conflict_count = rng.randint(0, max(0, a["liveAgentCount"] // 8))
            mean_vision = rng.uniform(vision_min, vision_max)
            mean_metabolism = rng.uniform(metabolism_min, metabolism_max)
        else:
            conflict_count = 0
            mean_vision = 0.0
            mean_metabolism = 0.0

        row = {
            "timestep": t,
            "liveAgentCount": a["liveAgentCount"],
            "birthCount": birth_count,
            "deathCount": death_count,
            "totalWealth": round(a["totalWealth"], 6),
            "averageWealth": round(a["averageWealth"], 6),
            "totalSugarOnGrid": round(total_sugar, 6),
            "conflictCount": conflict_count,
            "meanVision": round(mean_vision, 6),
            "meanMetabolism": round(mean_metabolism, 6),
            "sexRatio": round(a["sexRatio"], 6),
            "fertileCount": a["fertileCount"],
            "giniWealth": round(a["giniWealth"], 6),
        }
        rows_out.append(row)
        prev_ids = curr_ids

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    print(f"Wrote timestep constants: {out_path.name}")
    return out_path


def generate_visualization_parameters(folder: Path):
    out_path = folder / "visualization_parameters.csv"
    if out_path.exists():
        print(f"Already exists, skipping: {out_path.name}")
        return out_path

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(DEFAULT_VIZ_PARAMS.keys()))
        w.writeheader()
        w.writerow(DEFAULT_VIZ_PARAMS)

    print(f"Wrote visualization params: {out_path.name}")
    return out_path


def main():
    folder = Path(INPUT_DIR)

    # Generate visualization params first (always safe)
    generate_visualization_parameters(folder)

    # Generate timestep constants if missing
    try:
        prefix, run, *_ = detect_run_files(folder)
        expected_ts_constants = folder / f"{prefix}_{run}_TIMESTEPCONSTANTS.csv"
        if expected_ts_constants.exists():
            print(f"Already exists, skipping: {expected_ts_constants.name}")
        else:
            generate_timestepconstants(folder)
    except Exception as e:
        print(f"Could not generate TIMESTEPCONSTANTS: {e}")


if __name__ == "__main__":
    main()