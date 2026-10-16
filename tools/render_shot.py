"""Build and render one shot headlessly.

  blender -b --factory-startup -P tools/render_shot.py -- --shot sample_b1 --engine eevee \
      --preset sample [--frames 48,150,260] [--save-blend]

Frames go to $DREAMFORGE_RENDER_DIR (default renders/)/<shot>/<engine>/frames/####.png;
per-frame timings are appended to renders/times.csv.
"""
import argparse
import csv
import datetime
import importlib
import os
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path[:0] = [os.path.join(REPO, "projects/euv/blender/scripts"),
                os.path.join(REPO, "projects/euv/blender/shots")]

import bpy  # noqa: E402
import common as C  # noqa: E402


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--engine", choices=["eevee", "cycles"], default="eevee")
    ap.add_argument("--preset", choices=list(C.PRESETS), default="sample")
    ap.add_argument("--frames", help="comma-separated frame list; default renders the full range")
    ap.add_argument("--save-blend", action="store_true")
    return ap.parse_args(argv)


def main():
    a = parse()
    shot = importlib.import_module(a.shot)
    sc = shot.build()
    C.setup_render(a.engine, a.preset)
    C.setup_compositor()
    out = C.set_output(a.shot, a.engine)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.render_root(), a.shot, f"{a.shot}.blend"))

    frames = [int(f) for f in a.frames.split(",")] if a.frames else range(sc.frame_start, sc.frame_end + 1)
    log = os.path.join(C.render_root(), "times.csv")
    new = not os.path.exists(log)
    with open(log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "shot", "engine", "preset", "frame", "seconds"])
        for f in frames:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, f"{f:04d}.png")
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                        a.shot, a.engine, a.preset, f, f"{dt:.2f}"])
            fh.flush()
            print(f"[render_shot] {a.shot} {a.engine} frame {f} {dt:.2f}s", flush=True)


main()
