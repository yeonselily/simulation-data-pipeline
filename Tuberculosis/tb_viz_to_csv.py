import os
import csv
import struct
'''
tuberculosis.viz contains raw RGB frames; tb_viz_to_csv.py can decode the colors back into per-cell numeric state and
write META.csv + GRID_*.csv.
The per-cell encoding is a 2×2 pixel block (4 quadrants) in outputSimSpace():
'''
SIG = 0xCC10ADDE
HEADER_BYTES = 4 + 8 + 8  # u32 sig + u64 w + u64 h

# Color decoding from main/Tuberculosis/src/Tuberculosis.cu
RGB_BACTERIA = (0, 0, 128)
RGB_TCELL = (0, 0, 255)

RGB_MACRO_STATE = {
    (0, 255, 0): 0,         # RESTING
    (255, 255, 0): 1,       # INFECTED
    (0, 255, 255): 2,       # ACTIVATED
    (128, 0, 128): 3,       # CHRONICALLY_INFECTED
}

RGB_CHEMOKINE = {
    (255, 140, 0): 1,
    (255, 0, 0): 2,
}

def read_header(f):
    sig = struct.unpack("<I", f.read(4))[0]
    if sig != SIG:
        raise ValueError(f"Bad signature: got {hex(sig)} expected {hex(SIG)}")
    w = struct.unpack("<Q", f.read(8))[0]
    h = struct.unpack("<Q", f.read(8))[0]
    if w % 2 != 0 or h % 2 != 0:
        raise ValueError(f"Expected even width/height (got {w}x{h})")
    return int(w), int(h)

def decode_cell(frame_rgb, r, c):
    # 2x2 block:
    # TL bacteria, TR macrophage+state, BL tcell, BR chemokine
    tl = tuple(frame_rgb[(2*r)*3 + (2*c)*3 : (2*r)*3 + (2*c)*3 + 3])  # not used (see below)
    # The above indexing is messy in 1D; we’ll do explicit indexing with (y,x).
    raise RuntimeError("Use the 2D decoder below")

def main(viz_path, out_dir, output_interval, max_chemokine=2, tcell_entrance=10):
    os.makedirs(out_dir, exist_ok=True)

    with open(viz_path, "rb") as f:
        w, h = read_header(f)
        frame_bytes = w * h * 3

        # Determine number of frames
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        payload = file_size - HEADER_BYTES
        if payload < 0 or payload % frame_bytes != 0:
            raise ValueError("File size is not a whole number of frames")
        T = payload // frame_bytes

        # Write META.csv
        meta_path = os.path.join(out_dir, "META.csv")
        with open(meta_path, "w", newline="") as mf:
            writer = csv.writer(mf)
            writer.writerow(["height","width","timesteps","outputInterval","maxChemokine","tcellEntrance"])
            writer.writerow([h//2, w//2, T, output_interval, max_chemokine, tcell_entrance])

        # Go to first frame
        f.seek(HEADER_BYTES, os.SEEK_SET)

        for t in range(T):
            buf = f.read(frame_bytes)
            if len(buf) != frame_bytes:
                raise ValueError(f"Short read at frame {t}")

            # Frame as (h,w,3) using plain indexing (avoid numpy dependency)
            # pixel(y,x) starts at (y*w + x)*3
            def pixel(y, x):
                i = (y * w + x) * 3
                return (buf[i], buf[i+1], buf[i+2])

            grid_path = os.path.join(out_dir, f"GRID_{t:05d}.csv")
            with open(grid_path, "w", newline="") as gf:
                writer = csv.writer(gf)
                writer.writerow(["row","col","bacteria","macrophage","macrophageState","tcell","chemokine"])

                H = h // 2
                W = w // 2
                for row in range(H):
                    for col in range(W):
                        # 2x2 block coords in pixel-space
                        tl = pixel(2*row,   2*col)     # bacteria
                        tr = pixel(2*row,   2*col + 1) # macrophage + state
                        bl = pixel(2*row+1, 2*col)     # tcell
                        br = pixel(2*row+1, 2*col + 1) # chemokine

                        bacteria = 1 if tl == RGB_BACTERIA else 0

                        if tr in RGB_MACRO_STATE:
                            macrophage = 1
                            macrophage_state = RGB_MACRO_STATE[tr]
                        else:
                            macrophage = 0
                            macrophage_state = -1

                        tcell = 1 if bl == RGB_TCELL else 0
                        chemokine = RGB_CHEMOKINE.get(br, 0)

                        writer.writerow([row, col, bacteria, macrophage, macrophage_state, tcell, chemokine])

    print(f"Wrote {out_dir}/META.csv and {T} grid files (GRID_*.csv)")

if __name__ == "__main__":
    import sys
    viz_path = sys.argv[1] if len(sys.argv) > 1 else "tuberculosis.viz"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "tb_csv"
    output_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    main(viz_path, out_dir, output_interval)