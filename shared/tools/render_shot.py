"""Build and render one shot headlessly.

  blender -b --factory-startup -P tools/render_shot.py -- --shot sample_b1 --engine cycles \
      --preset sample [--cut CamPlasma] [--frames 48,150,260] [--save-blend]

Without --cut, frames go to $DREAMFORGE_RENDER_DIR (default renders/)/<shot>/<engine>/frames/;
with --cut (a camera listed in the shot's CUTS) they go to .../<engine>/<cut>/ and the frame
range defaults to that cut's range. Per-frame timings are appended to renders/times.csv.
"""
import argparse
import csv
import datetime
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender -P does not add it
from paths import AUDIO, EP, REPO, RENDERS, SHARED  # noqa: E402,F401
sys.path[:0] = [os.path.join(SHARED, "blender"),
                os.path.join(EP, "blender/scripts"),
                os.path.join(EP, "blender/shots")]

import bpy  # noqa: E402
import common as C  # noqa: E402


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--engine", choices=["eevee", "cycles"], default="eevee")
    ap.add_argument("--preset", choices=list(C.PRESETS), default="sample")
    ap.add_argument("--cut", help="camera name from the shot's CUTS")
    ap.add_argument("--style", choices=["photoreal", "xray", "blueprint", "energy", "clay", "sem"],
                    help="re-render the shot in one of the visual languages (styles.py)")
    ap.add_argument("--frames", help="comma-separated frame list; default renders the full range")
    ap.add_argument("--save-blend", action="store_true")
    return ap.parse_args(argv)


def main():
    a = parse()
    shot = importlib.import_module(a.shot)
    sc = shot.build()
    if a.cut:
        bpy.context.scene.camera = bpy.data.objects[next(c for c in shot.CUTS if c[0] == a.cut)[0]]
    C.setup_render(a.engine, a.preset)
    if a.style:
        import styles
        styles.apply_style(a.style, line_px=1.3 * C.PRESETS[a.preset][1] / 540)
    C.setup_compositor()
    # simulate particle systems up front so any frame can be rendered out of order
    bpy.ops.ptcache.bake_all(bake=True)
    sub = (a.cut or "frames") + (f"_{a.style}" if a.style else "")
    out = C.set_output(a.shot, a.engine, sub=sub)
    rng = range(sc.frame_start, sc.frame_end + 1)
    if a.cut:
        cam, f0, f1 = next(c for c in shot.CUTS if c[0] == a.cut)
        sc.camera = bpy.data.objects[cam]
        rng = range(f0, f1 + 1)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.render_root(), a.shot, f"{a.shot}.blend"))

    frames = [int(f) for f in a.frames.split(",")] if a.frames else rng
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
                        a.cut or a.shot, a.engine, a.preset, f, f"{dt:.2f}"])
            fh.flush()
            print(f"[render_shot] {a.shot} {a.engine} frame {f} {dt:.2f}s", flush=True)


main()
