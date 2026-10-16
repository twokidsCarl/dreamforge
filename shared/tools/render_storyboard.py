"""Render storyboard shots from the shot registry.

  blender -b --factory-startup -P tools/render_storyboard.py -- --shot B1_10 [--quality preview|sample|final]
      [--frames 1,60] [--engine eevee|cycles]

episodes/<episode>/blender/shots/registry.yaml maps a storyboard id to a scene module, a camera and the
simulation frame where the shot starts:

  B1_10: {scene: b1_source, camera: CamB1_10, start: 65, style: photoreal, engine: cycles}
  B1_11: {scene: b1_source, camera: CamB1_11, start: 150, hold: true, style: sem}

The shot length comes from storyboard.timed.yaml (real VO timing). `hold: true` renders one frame
for a freeze. Frames go to $DREAMFORGE_RENDER_DIR/shots/<id>/<quality>/####.png (numbered from 1),
timings to renders/times.csv; tools/encode_shots.py turns them into clips the story reel picks up.
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
                os.path.join(EP, "blender/shots"),
                os.path.join(REPO, ".blender_pylib")]  # PyYAML for Blender's Python (see .gitignore)

import bpy  # noqa: E402
import yaml  # noqa: E402

import common as C  # noqa: E402
import styles  # noqa: E402

FPS = 24


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--quality", choices=list(C.PRESETS), default="preview")
    ap.add_argument("--engine", choices=["eevee", "cycles"])
    ap.add_argument("--frames", help="comma-separated shot-relative frames (1-based) to render")
    return ap.parse_args(argv)


def main():
    a = args()
    reg = yaml.safe_load(open(os.path.join(EP, "blender/shots/registry.yaml"), encoding="utf-8"))
    spec = reg[a.shot]
    timed = yaml.safe_load(open(os.path.join(EP, "storyboard/storyboard.timed.yaml"),
                                encoding="utf-8"))
    shot = next(s for s in timed["shots"] if s["id"] == a.shot)
    n = 1 if spec.get("hold") else max(1, round(shot["duration"] * FPS))

    module = importlib.import_module(spec["scene"])
    sc = module.build(**spec.get("args", {}))
    sc.camera = bpy.data.objects[spec["camera"]]
    engine = a.engine or spec.get("engine", "eevee")
    C.setup_render(engine, a.quality)
    style = spec.get("style", shot["style"])
    if style in styles.STYLES and style != "photoreal":
        styles.apply_style(style, line_px=1.3 * C.PRESETS[a.quality][1] / 540)
    elif style == "photoreal":
        styles.apply_style("photoreal")
    if hasattr(module, "after_style"):
        module.after_style(style, a.shot)
    C.setup_compositor()
    if any(o.particle_systems for o in bpy.data.objects if o.type == "MESH"):
        bpy.ops.ptcache.bake_all(bake=True)

    out = os.path.join(C.render_root(), "shots", a.shot, a.quality)
    os.makedirs(out, exist_ok=True)
    rel = [int(f) for f in a.frames.split(",")] if a.frames else range(1, n + 1)
    log = os.path.join(C.render_root(), "times.csv")
    new = not os.path.exists(log)
    with open(log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "shot", "engine", "preset", "frame", "seconds"])
        for f in rel:
            fr = spec["start"] + (f - 1) * spec.get("step", 1)      # step: every Nth sim frame (<1 = slow motion)
            sc.frame_set(int(fr), subframe=fr - int(fr))
            sc.render.filepath = os.path.join(out, f"{f:04d}.png")
            t0 = time.time()
            if f > n - spec.get("black_tail", 0):                  # hard cut to black on the last frames
                blk = bpy.data.images.new("Black", sc.render.resolution_x * sc.render.resolution_percentage // 100,
                                          sc.render.resolution_y * sc.render.resolution_percentage // 100)
                blk.pixels = [0.0, 0.0, 0.0, 1.0] * (blk.size[0] * blk.size[1])
                blk.filepath_raw = sc.render.filepath
                blk.file_format = "PNG"
                blk.save()
            else:
                bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), a.shot, engine, a.quality,
                        f, f"{dt:.2f}"])
            fh.flush()
            print(f"[render_storyboard] {a.shot} {engine} frame {f}/{n} {dt:.2f}s", flush=True)


main()
