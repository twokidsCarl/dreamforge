"""不开 GPU 的镜头冒烟：按 registry 逐镜 build、套风格、切到首帧 / 中帧 / 尾帧，检查相机和画面里的东西，不渲染。

  DREAMFORGE_EPISODE=E2-optogenetics blender -b --factory-startup -P shared/tools/build_check.py -- \
      [--shots A_01a,B_08a | --segment B] [--render A0_91 --quality preview]

每镜一行：OK / FAIL、物体数、三角面数、各检查帧里相机视野内可见的物体数。
- registry 里没有 scene 的条目（2D 镜头，`mograph:` 指向 mograph/*.py）跳过，只核对 id 在 timed.yaml 里。
- 另外核对 timed.yaml 的每个 id 都在 registry 里（覆盖率），缺的列出来并让退出码为 1。
- `--render` 只给列出的镜头渲 1 帧（中帧），写到 $DREAMFORGE_RENDER_DIR/build_check/<id>.png；默认不渲。
退出码：有 FAIL 或覆盖不全为 1。
"""
import argparse
import importlib
import math
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import EP, REPO, SHARED, timed_shots  # noqa: E402
sys.path[:0] = [os.path.join(SHARED, "blender"), os.path.join(EP, "blender/scripts"),
                os.path.join(EP, "blender/shots"), os.path.join(REPO, ".blender_pylib")]

import bpy  # noqa: E402
import yaml  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

import common as C  # noqa: E402
import styles  # noqa: E402

FPS = 24


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", help="逗号分隔的镜头 id")
    ap.add_argument("--segment", help="只查这一段（A0 / A / B / C / D）")
    ap.add_argument("--render", default="", help="逗号分隔：这些镜头渲 1 帧（中帧）")
    ap.add_argument("--quality", default="preview", choices=list(C.PRESETS))
    ap.add_argument("--extra-registry", default="", help="逗号分隔：额外的 registry 片段（同格式），合并进来（写新模块时自测用）")
    return ap.parse_args(argv)


def visible_in_camera(sc, cam):
    """相机视野内（含部分进入）的可渲染物体数。"""
    deps = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in sc.objects:
        if o.type not in ("MESH", "CURVE", "FONT", "SURFACE", "META") or o.hide_render:
            continue
        ev = o.evaluated_get(deps)
        try:
            corners = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        except Exception:
            continue
        pts = [world_to_camera_view(sc, cam, p) for p in corners]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        if max(p.z for p in pts) > 0 and max(xs) >= 0 and min(xs) <= 1 and max(ys) >= 0 and min(ys) <= 1:
            n += 1
    return n


def tri_count(sc):
    deps = bpy.context.evaluated_depsgraph_get()
    t = 0
    for o in sc.objects:
        if o.type == "MESH" and not o.hide_render:
            t += sum(len(p.vertices) - 2 for p in o.evaluated_get(deps).data.polygons)
    return t


def check(sid, spec, shot, quality, render):
    t0 = time.time()
    module = importlib.import_module(spec["scene"])
    sc = module.build(**spec.get("args", {}))
    cam = bpy.data.objects.get(spec["camera"])
    if cam is None or cam.type != "CAMERA":
        raise RuntimeError(f"相机 {spec['camera']} 不存在")
    sc.camera = cam
    engine = spec.get("engine", "eevee")
    C.setup_render(engine, quality)
    style = spec.get("style", shot["style"])
    if style in styles.STYLES:
        styles.apply_style(style, line_px=1.3 * C.PRESETS[quality][1] / 540)
    if hasattr(module, "after_style"):
        module.after_style(style, sid)
    C.setup_compositor(no_glare=bool(spec.get("no_glare")))   # registry 逐镜 no_glare: true
    n = 1 if spec.get("hold") else max(1, round(shot["duration"] * FPS))
    seen = []
    for rel in sorted({1, (n + 1) // 2, n}):
        fr = spec["start"] + (rel - 1) * spec.get("step", 1)
        sc.frame_set(math.floor(fr), subframe=fr - math.floor(fr))
        seen.append(visible_in_camera(sc, cam))
    if min(seen) == 0:
        raise RuntimeError(f"相机视野里没有可见物体（各检查帧 {seen}）")
    out = None
    if render:
        fr = spec["start"] + ((n + 1) // 2 - 1) * spec.get("step", 1)
        sc.frame_set(math.floor(fr))
        out = os.path.join(C.render_root(), "build_check", f"{sid}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
    return len(sc.objects), tri_count(sc), seen, time.time() - t0, out


def main():
    a = parse()
    reg = yaml.safe_load(open(os.path.join(EP, "blender/shots/registry.yaml"), encoding="utf-8"))
    for extra_path in filter(None, a.extra_registry.split(",")):
        reg.update(yaml.safe_load(open(extra_path, encoding="utf-8")) or {})
    shots = {s["id"]: s for s in timed_shots(quiet=True)}
    missing = [i for i in shots if i not in reg]
    extra = [i for i in reg if i not in shots]
    want = a.shots.split(",") if a.shots else [i for i in reg if not a.segment or shots.get(i, {}).get("segment") == a.segment]
    render = set(filter(None, a.render.split(",")))
    fails = 0
    for sid in want:
        spec = reg[sid]
        if "scene" not in spec:
            print(f"[build_check] SKIP {sid}: 2D（mograph: {spec.get('mograph')}）", flush=True)
            continue
        try:
            n_obj, tris, seen, dt, out = check(sid, spec, shots[sid], a.quality, sid in render)
            print(f"[build_check] OK   {sid}: {spec['scene']} {spec.get('args', {})} objects={n_obj} tris={tris} "
                  f"in_view={seen} {dt:.1f}s" + (f" rendered={out}" if out else ""), flush=True)
        except Exception as e:                                # noqa: BLE001
            fails += 1
            print(f"[build_check] FAIL {sid}: {e}", flush=True)
            traceback.print_exc()
    print(f"[build_check] timed.yaml {len(shots)} 镜，registry {len(reg)} 条；缺 {missing or '无'}；多出 {extra or '无'}；"
          f"FAIL {fails}", flush=True)
    sys.exit(1 if fails or missing or extra else 0)


main()
