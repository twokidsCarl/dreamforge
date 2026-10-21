"""Render storyboard shots from the shot registry.

  blender -b --factory-startup -P tools/render_storyboard.py -- --shot B1_10 [--quality preview|sample|final]
      [--frames 1,60 | 1,mid,last] [--engine eevee|cycles]

episodes/<episode>/blender/shots/registry.yaml maps a storyboard id to a scene module, a camera and the
simulation frame where the shot starts:

  B1_10: {scene: b1_source, camera: CamB1_10, start: 65, style: photoreal, engine: cycles}
  B1_11: {scene: b1_source, camera: CamB1_11, start: 150, hold: true, style: sem}

The shot length comes from storyboard.timed.yaml (real VO timing); until that exists, from storyboard.yaml. `hold: true` renders one frame
for a freeze. Frames go to $DREAMFORGE_RENDER_DIR/shots/<id>/<quality>/####.png (numbered from 1),
timings to renders/times.csv; tools/encode_shots.py turns them into clips the story reel picks up.
"""
import argparse
import csv
import datetime
import importlib
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # Blender -P does not add it
from paths import AUDIO, EP, REPO, RENDERS, SHARED, timed_shots  # noqa: E402,F401
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
    ap.add_argument("--frames", help="comma-separated shot-relative frames (1-based), or mid / last")
    return ap.parse_args(argv)


def main():
    a = args()
    reg = yaml.safe_load(open(os.path.join(EP, "blender/shots/registry.yaml"), encoding="utf-8"))
    spec = reg[a.shot]
    if "scene" not in spec:                                       # 2D 镜头：registry 只登记 mograph 模块
        sys.exit(f"[render_storyboard] {a.shot} 是 2D 镜头（mograph: {spec.get('mograph')}）："
                 f"用 python3 shared/tools/mograph.py --shot {a.shot}")
    shot = next(s for s in timed_shots() if s["id"] == a.shot)     # 没有 timed 文件时回退到分镜 duration
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

    # raw: true 的镜头先写到 <quality>_raw，由 mograph 里同 id 的后处理（叠字等）再写 <quality>
    out = os.path.join(C.render_root(), "shots", a.shot, a.quality + ("_raw" if spec.get("raw") else ""))
    os.makedirs(out, exist_ok=True)
    # --frames 1,60 或 1,mid,last（mid = 中帧，last = 尾帧，按本镜帧数算）
    named = {"mid": (n + 1) // 2, "last": n}
    rel = [named[f] if f in named else int(f) for f in a.frames.split(",")] if a.frames else range(1, n + 1)
    log = os.path.join(C.render_root(), "times.csv")
    new = not os.path.exists(log)
    with open(log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "shot", "engine", "preset", "frame", "seconds"])
        for f in rel:
            fr = spec["start"] + (f - 1) * spec.get("step", 1)      # step: every Nth sim frame (<1 = slow motion)
            sc.frame_set(math.floor(fr), subframe=fr - math.floor(fr))   # start may be < 1 (hold before the action)
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
                try:
                    bpy.ops.render.render(write_still=True)
                except RuntimeError as e:                        # e.g. Metal out of memory: retry on the CPU
                    if sc.render.engine != "CYCLES" or sc.cycles.device == "CPU":
                        raise
                    print(f"[render_storyboard] GPU failed ({e}); retrying {a.shot} frame {f} on CPU", flush=True)
                    sc.cycles.device = "CPU"
                    bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), a.shot, engine, a.quality,
                        f, f"{dt:.2f}"])
            fh.flush()
            print(f"[render_storyboard] {a.shot} {engine} frame {f}/{n} {dt:.2f}s", flush=True)


main()
