"""R25 chero B7_06 (R25_ROOT_CAUSE rows 1 + 2 + 4). Layered on cut_hero_r24_b706 (solid ring mirrors M5/M6 + one path).

  * row 2: while the R24 hook runs, beam_r24.chain is patched (cut_hero_r25.pre) to chain24(): the same stops / radii
    built by beam_r25.chain = tapered SHELL legs (ends >= 3:1, no inner cone); the R24 solid ring mirrors (PO24_mface,
    one object carrying both faces) are passed as existing={1: face, 2: face}, so no extra mirror is built;
  * row 1: every turn (M5 ring landing, M6 landing) sits on a visible mirror face; BEAMCHECK25 is run here with the
    stops AND normals transformed by the turntable per job frame. M5 / M6 faces opened toward the camera: tilt TILT5 / TILT6
    instead of 18 deg (R24 M6 |n.to_cam| 0.26-0.38 = ~20 deg from edge-on -> a strip);
  * row 4: three depth layers of real parts inside / in front of the tower (turntable frame): back = non-repeating
    valve blocks / pump bodies / manifold on the back wall, mid = second metrology ring + sensor heads, hexapod struts
    under the M6 cell, coolant manifold risers and cable trays, front = a defocused hose / cable bundle at the
    front-left post. No fog, no texture wall. Turntable / truck camera / no-fog V path untouched.
"""
import math
import random

import bpy
from mathutils import Vector

CH = {}
WIDEN, EDGE, CORE, STRENGTH, ALPHA = 1.35, 1.3, 0.28, 2.4, 0.45
TILT5, TILT6 = 21.0, 36.0   # deg toward the camera side (R24 18/18: M6 |n.to_cam| 0.26-0.38 = edge-on strip; M5 36 hid the wafer point)


def _swap(fn_mod, fn_name, reps, tag):
    import inspect
    import textwrap
    fn = getattr(fn_mod, fn_name)
    src = textwrap.dedent(inspect.getsource(fn))
    n = 0
    for a, b in reps:
        if a in src:
            src = src.replace(a, b)
            n += 1
    if n:
        exec(compile(src, fn_mod.__file__, "exec"), fn_mod.__dict__)
    print(f"[r25h b706] {tag}: {n}/{len(reps)} tilt lines patched", flush=True)


def pre(mod=None):
    """M5 tilt 18 -> TILT5, M6 tilt 18 -> TILT6 in the R15 cells / flexure mounts (r2_cutaway._po_barrels_r15, local
    `tilt`) and in the R24 solid faces + path (cut_hero_r24_b706.post): runtime copies of those two functions with the
    new normals replace them for this build only (files untouched)."""
    import cut_hero_r24_b706 as H24
    t5, t6 = f"math.radians({TILT5})", f"math.radians({TILT6})"
    reps15 = [("n5 = Vector((0, -math.sin(tilt), math.cos(tilt)))", f"n5 = Vector((0, -math.sin({t5}), math.cos({t5})))"),
              ("n6 = Vector((0, -math.sin(tilt), -math.cos(tilt)))", f"n6 = Vector((0, -math.sin({t6}), -math.cos({t6})))")]
    reps24 = [("n5 = Vector((0, -math.sin(TILT), math.cos(TILT)))", f"n5 = Vector((0, -math.sin({t5}), math.cos({t5})))"),
              ("n6 = Vector((0, -math.sin(TILT), -math.cos(TILT)))", f"n6 = Vector((0, -math.sin({t6}), -math.cos({t6})))")]
    if mod is not None and hasattr(mod, "_po_barrels_r15"):
        _swap(mod, "_po_barrels_r15", reps15, "R15 cells")
    _swap(H24, "post", reps24, "R24 faces")


def chain24(name, stops, radii, **kw):
    import beam_r25 as BR
    face = bpy.data.objects.get("PO24_mface")
    ex = {1: face, 2: face} if face is not None else {}
    kw.pop("existing", None)
    # main 32 spp after the shell_mat fix (Facing^edge): thin legs read as wire pairs -> wider mouths (x1.35, focus
    # end kept), soft edge 1.3, filled core 0.28, a bit less strength / alpha so the body is soft, not solid
    radii = [r * WIDEN for r in radii[:-1]] + [radii[-1]]
    kw.update(edge=EDGE, core=CORE, strength=STRENGTH, alpha=ALPHA)
    ch = BR.chain(name, stops, radii, existing=ex, **kw)
    CH["ch"] = ch
    return ch


def check24(*_a, **_k):
    return []


def _mats():
    import kit_r2 as K
    return dict(
        clay=K.mat("ClayR25B7", (0.80, 0.80, 0.78), rough=0.5),
        steel=K.mat("SteelR25B7", (0.62, 0.63, 0.66), metal=1.0, rough=0.28),
        dark=K.mat("DarkR25B7", (0.07, 0.075, 0.085), metal=0.3, rough=0.45),
        hose=K.mat("HoseR25B7", (0.10, 0.22, 0.62), rough=0.4),
        hosew=K.mat("HoseWR25B7", (0.75, 0.76, 0.78), rough=0.45),
        cable=K.mat("CableR25B7", (0.03, 0.03, 0.035), rough=0.55),
    )


def _cyl_dir(mb, c, d, r, h, seg=24):
    c, d = Vector(c), Vector(d).normalized()
    mb.tube(tuple(c - d * h / 2), tuple(c + d * h / 2), r, seg=seg)


def density(piv):
    import kit_r2 as K
    M = _mats()
    rnd = random.Random(25)
    P = {k: K.MB() for k in M}
    # ---- BACK layer: back wall (y ~ +0.80) - valve blocks, pump bodies, manifold block, all different sizes
    K.greeble(P["dark"], (-0.62, 0.86, 1.25), (1, 0, 0), (0, 0, 1), (0, -1, 0), 1.24, 1.9, 22, 0.06, 0.2, 0.03, 0.12,
              seed=251)
    for x, z, r, h in ((-0.42, 1.42, 0.07, 0.26), (0.36, 1.48, 0.06, 0.22), (-0.12, 2.92, 0.055, 0.3),
                       (0.46, 2.98, 0.05, 0.24)):
        P["steel"].cyl((x, 0.72, z), r, h, seg=28)                        # pump bodies (vertical)
        P["steel"].ring((x, 0.72, z + h / 2 + 0.01), r + 0.025, r - 0.01, 0.02, seg=28)
        P["steel"].ring((x, 0.72, z - h / 2 - 0.01), r + 0.025, r - 0.01, 0.02, seg=28)
    for x in (-0.3, -0.1, 0.1, 0.3):                                       # manifold risers on the back wall
        P["hosew" if x < 0 else "hose"].tube((x, 0.66, 1.3), (x, 0.66, 3.15), 0.018, seg=12)
    for z in (1.55, 2.0, 2.55, 3.0):                                       # riser clamps
        P["clay"].box((0, 0.68, z), (0.72, 0.05, 0.035))
    # ---- MID layer: second metrology ring (back half) + sensor heads, hexapod struts under M6, cable trays
    P["steel"].shell((0, 0, 2.48), 0.6, 0.66, 0.04, 20, 160, seg=64)
    for a in (30, 62, 95, 128, 155):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        c = d * 0.57 + Vector((0, 0, 2.48))
        P["dark"].box(tuple(c), (0.06, 0.06, 0.07))
        _cyl_dir(P["steel"], c - d * 0.05, d, 0.016, 0.06, seg=12)
    for k in range(6):                                                    # hexapod: M6 cell -> top ring
        a0 = math.radians(60 * k + 30 + (12 if k % 2 else -12))
        a1 = math.radians(60 * (k + (1 if k % 2 else 0)) + 30)
        p0 = Vector((0.58 * math.cos(a0), 0.58 * math.sin(a0), 2.95))
        p1 = Vector((0.74 * math.cos(a1), 0.74 * math.sin(a1), 3.2))
        if p0.y < -0.2 and p1.y < -0.2:
            continue                                                      # keep the front clear (M6 face)
        P["steel"].tube(tuple(p0), tuple(p1), 0.016, seg=10)
        P["dark"].cyl(tuple(p0.lerp(p1, 0.5)), 0.026, 0.07, seg=14)
    for z, seed in ((1.82, 3), (2.66, 4)):                                # cable trays (back arc)
        pts = [Vector((0.76 * math.cos(math.radians(a)), 0.76 * math.sin(math.radians(a)), z)) for a in range(15, 170, 10)]
        K.cable_run(P["cable"], pts, n=4, r=0.008, spread=0.02, seed=seed)
    for a in (8, 172):                                                    # side bellows + flanges (left / right walls)
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        for i in range(9):
            z = 1.9 + i * 0.045
            P["steel"].ring(tuple(d * 0.8 + Vector((0, 0, z))), 0.07 if i % 2 else 0.06, 0.04, 0.03,
                            rot=(0, math.pi / 2, math.radians(a)), seg=24)
        P["clay"].ring(tuple(d * 0.8 + Vector((0, 0, 1.86))), 0.1, 0.04, 0.03, rot=(0, math.pi / 2, math.radians(a)))
    # ---- FRONT layer: defocused hose / cable bundle at the front-left post (outside the beam / mirror region)
    pts = [Vector((-0.98, -0.98, 0.95)), Vector((-1.0, -1.02, 1.6)), Vector((-0.97, -0.99, 2.2)),
           Vector((-0.9, -0.95, 2.45))]
    # 8-spp try 1: a 3-hose blue bundle read as a flat blue board along the post -> dark cables + one steel hose
    K.cable_run(P["cable"], pts, n=4, r=0.012, spread=0.06, seed=8)
    P["steel"].path([p + Vector((-0.08, -0.04, 0)) for p in pts], 0.02, seg=12)
    obs = []
    for k, mb in P.items():
        try:
            o = mb.obj(f"PODensR25_{k}", M[k])
        except Exception as e:      # empty builder
            print("[r25h b706] skip", k, e)
            continue
        if o is not None:
            o.parent = piv
            obs.append(o)
    print(f"[r25h b706] density layers: {len(obs)} objects", flush=True)
    return obs


def post(sc):
    import beam_r25 as BR
    ch = CH.get("ch")
    piv = bpy.data.objects.get("Turntable")
    density(piv)
    if ch is None:
        print("[r25h b706] no R25 chain (R24 hook did not run?)", flush=True)
        return
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in (36, 79, 122):
        sc.frame_set(f)
        Mw = piv.matrix_world if piv is not None else None
        R = Mw.to_3x3() if Mw is not None else None
        st = [((Mw @ Vector(p)) if Mw is not None else Vector(p),
               None if nn is None else ((R @ Vector(nn)).normalized() if R is not None else Vector(nn)))
              for p, nn in ch["stops"]]
        BR.check(sc, {"stops": st, "radii": ch["radii"], "leg_radii": ch["leg_radii"], "mirrors": ch["mirrors"]},
                 [f], exits=(0,), tag="B7_06", mirror_stops=[1, 2])
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
