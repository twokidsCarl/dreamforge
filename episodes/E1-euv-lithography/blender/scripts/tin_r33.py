"""Round 33 tin = OPAQUE LIQUID METAL, still a regular near-round thin disc (R33_ROOT_CAUSE row 3; MAIN process recipe -
looked at 8 + 32 spp before use).

R32 p1: 「薄饼像一块凸透镜 / 玻璃片」「仍像玻璃透镜 / 化妆镜：中间是镜面反射斑块，边缘橙色像镜框」「锡滴读成深色玻璃弹珠」;
asks: 「不透明的液态锡：低粗糙度银灰金属，边缘卷起、有厚度，表面带一点褶皱」「橙色只留在被激光照到的那一侧」.
Why R32 read as a lens: a smooth, perfectly mirror-like face that showed ONE big white key box (tin_r29 sheet env sphere
TinSheetEnvR29, key strength 3.0) on a near-black base, closed by a thin edge glowing orange ALL ROUND = a lens /
compact mirror in a frame. R33 keeps Carl's regular round disc (tin_r32 outline) and changes what reads as glass:
  * the edge is a thick ROLLED BEAD (round cross-section, ~2.8x the sheet thickness at the rim, rolled slightly toward
    the downstream side) - the thickness shows from the side, it is not a thin frame line;
  * a few gentle concentric surface wrinkles (liquid surface waves) + the R32 low-frequency wobble;
  * satin liquid metal (silver-grey, roughness 0.18); its reflection env keeps the soft horizon, warm box and grazing
    rims of tin_r29 but drops the white key box, so no single white blob (hiding the env entirely = dark glass);
  * the warm glow sits only on the bead arc facing the laser on screen (screen-left for both shots), not a ring;
  * B1_08 droplets: the same satin liquid-tin material (one model per part); their drop env keeps the tin_r29 soft
    bands but on a lit-chamber base instead of near-black (the dark half of the 「深色玻璃弹珠」; env hidden = darker).
"""
import math

import bpy
from mathutils import Vector

NS = 128
NR = 26
SAG = 0.10
T0 = 0.055                 # centre half-thickness (units of the radius)
T_RIM = 0.016              # sheet half-thickness where it meets the bead
BEAD = 0.050               # bead cross-section radius (units of the radius)
BEAD_X = 0.025             # bead rolled toward +x (downstream of the laser)
WOB = 0.050
WRINKLE = (0.008, 2.8)     # concentric wrinkles: amplitude (units of the radius), waves across the radius
ROUGH = 0.18
ROUGH_SHOT = {"B1_10": 0.09}   # 32 spp at 0.18: the small B1_10 disc 90/10 3.73 < 4 (flat satin grey)
SILVER = (0.82, 0.83, 0.86)
RIPPLE = (2.0, 0.4, 0.10)
HOT = 3.2
HOT_COL = (1.0, 0.30, 0.05)
SIDE = (-0.15, 0.75)       # smoothstep of cos(angle to the laser side on screen) -> glow arc
ENV_HIDE = ("TinSheetEnvR27", "TinSheetEnvR28", "TinSheetEnvR25")
ENV_KEEP = (0, 2, 3, 4, 5)  # tin_r29.sheet_bands minus band 1 (the white key box = the R32 big white blob); 8 spp with the
                           # env hidden altogether = a dark smooth disc with a clear rim (dark-glass read)
DROP_BASE = (0.20, 0.21, 0.24)   # tin_r29 drop env base 0.03 = the dark lower half of the 「深色玻璃弹珠」
DROP_FRAME = {"B1_08": 51}
RIDERS = ("TinAfterglow", "PancakeHot", "PancakeRim", "PancakeEdge", "TinLanding", "PancakeDrops")


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _rings():
    rc = 1.0 - BEAD
    out = [i / NR * (rc - BEAD * 0.4) for i in range(1, NR + 1)]
    out += [rc - BEAD * 0.4 + (BEAD * 1.4) * (k / 10.0) for k in range(1, 10)]
    return out


def _half(r):
    """half-thickness at normalised radius r: thin sheet, then a round bead (circle of radius BEAD centred at 1-BEAD)."""
    rc = 1.0 - BEAD
    body = T_RIM + (T0 - T_RIM) * max(0.0, 1 - r * r) ** 1.5
    if r <= rc - BEAD:
        return body, 0.0
    d = min(BEAD, abs(r - rc)) if r > rc else min(BEAD, rc - r)
    bead = math.sqrt(max(0.0, BEAD * BEAD - d * d))
    w = _smooth(rc - BEAD, rc, r)
    return max(body, bead), BEAD_X * w


def _mid(r, t):
    wob = WOB * r * r * (math.sin(2 * t + 0.7) * 0.5 + math.sin(3 * t + 2.1) * 0.3 + math.sin(5 * t + 4.0) * 0.2)
    wr = WRINKLE[0] * math.sin(2 * math.pi * WRINKLE[1] * r + 1.1 * math.sin(2 * t + 0.5) + 0.6 * math.sin(5 * t)) * _smooth(0.12, 0.45, r) * (1 - _smooth(0.88, 0.95, r))
    return SAG * r * r + wob + wr


def _rebuild(me, R, cx, side_dir):
    verts, faces, hot = [], [], []
    rings = _rings()
    rows_by_side = {}
    for side in (1, -1):
        h0, _ = _half(0.0)
        verts.append((cx + (_mid(0, 0) + side * h0) * R, 0.0, 0.0))
        hot.append(0.0)
        c = len(verts) - 1
        rows = []
        for r in rings:
            row = []
            h, xo = _half(r)
            for j in range(NS):
                t = 2 * math.pi * j / NS
                verts.append((cx + (_mid(r, t) + xo + side * h) * R, R * r * math.cos(t), R * r * math.sin(t)))
                hot.append((t, r))
                row.append(len(verts) - 1)
            rows.append(row)
        rows_by_side[side] = (c, rows)
    rim = []
    for j in range(NS):
        t = 2 * math.pi * j / NS
        verts.append((cx + (_mid(1.0, t) + BEAD_X) * R, R * math.cos(t), R * math.sin(t)))
        hot.append((t, 1.0))
        rim.append(len(verts) - 1)
    for side, flip in ((1, False), (-1, True)):
        c, rows = rows_by_side[side]
        r0 = rows[0]
        for j in range(NS):
            f = (c, r0[j], r0[(j + 1) % NS])
            faces.append(f[::-1] if flip else f)
        for a, b in zip(rows[:-1], rows[1:]):
            for j in range(NS):
                f = (a[j], b[j], b[(j + 1) % NS], a[(j + 1) % NS])
                faces.append(f[::-1] if flip else f)
        last = rows[-1]
        for j in range(NS):
            f = (last[j], rim[j], rim[(j + 1) % NS], last[(j + 1) % NS])
            faces.append(f[::-1] if flip else f)
    mats = [p.material_index for p in me.polygons[:1]] or [0]
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
        p.material_index = mats[0]
    me.update()
    at = me.attributes.get("r31hot") or me.attributes.new("r31hot", "FLOAT", "POINT")
    ly, lz = side_dir
    for i, hv in enumerate(hot):
        if not hv:
            at.data[i].value = 0.0
            continue
        t, r = hv
        arc = _smooth(SIDE[0], SIDE[1], math.cos(t) * ly + math.sin(t) * lz)
        at.data[i].value = 0.9 * arc * _smooth(1.0 - 2.2 * BEAD, 1.0 - BEAD * 0.6, r)
    me.update()


def _env(sc, frame):
    """rebuild the sheet env sphere (tin_r29.apply geometry) without its white key box."""
    import math as _m
    import source_r24 as H24
    import source_r25_tin as T25
    import tin_r29
    old = bpy.data.objects.get("TinSheetEnvR29")
    root = bpy.data.objects.get("PancakeRoot")
    if old is None or root is None:
        return False
    rad = max(old.dimensions) * 0.5 if old.dimensions.length > 0 else 0.27
    bpy.data.objects.remove(old, do_unlink=True)
    tc, rt, up = H24._cam_dirs(sc, frame, (0, 0, 0))
    yaw = root.rotation_euler.z
    nrm = Vector((_m.cos(yaw), _m.sin(yaw), 0))
    if nrm.dot(tc) < 0:
        nrm = -nrm
    v = -tc
    md = v - 2 * v.dot(nrm) * nrm
    bands = tin_r29.sheet_bands(tc, rt, up, nrm, md)
    T25.env_r25("TinSheetEnvR33", (0, 0, 0), rad, [bands[i] for i in ENV_KEEP], base=tin_r29.SHEET_BASE)
    return True


def _side_dir(sc, sh, frame):
    """unit (y, z) in the sheet's local disc plane that points to screen-left (where the laser comes in) at frame."""
    sc.frame_set(frame)
    cam = sc.camera
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    loc = sh.matrix_world.to_3x3().inverted() @ (-right)
    v = Vector((loc.y, loc.z))
    if v.length < 1e-6:
        return (0.0, 1.0)
    v.normalize()
    return (v.x, v.y)


def material(ob, ripple=RIPPLE, glow=True, rough=None):
    """tin_r31 node recipe (metal 1, no transmission, r31hot glow) at the R33 satin silver; HOT_BACK 1 = the glow arc
    is set by the r31hot attribute alone."""
    import tin_r31 as T31
    rough = ROUGH if rough is None else rough
    T31.ROUGH, T31.HOT, T31.HOT_BACK, T31.HOT_COL, T31.SILVER = rough, (HOT if glow else 0.0), 1.0, HOT_COL, SILVER
    for s in ob.material_slots:
        m = s.material
        if m is not None and m.get("r31disc"):
            base = bpy.data.materials.get(m.name.replace("_R31disc", ""))
            if base is not None:
                s.material = base
    T31._material(ob, ripple)
    for s in ob.material_slots:
        m = s.material
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m and m.use_nodes else None
        if b is not None and not b.inputs["Base Color"].is_linked:
            b.inputs["Base Color"].default_value = (*SILVER, 1)
        if b is not None:
            b.inputs["Roughness"].default_value = rough


def disc(sc, shot, frame, name="Pancake"):
    sh = bpy.data.objects.get(name)
    if sh is None:
        print(f"[tin_r33] {shot}: no {name}", flush=True)
        return None
    me = sh.data
    co = [v.co.copy() for v in me.vertices]
    R = max(math.hypot(c.y, c.z) for c in co) * 0.97
    cx = sum(c.x for c in co) / len(co)
    sd = _side_dir(sc, sh, frame)
    _rebuild(me, R, cx, sd)
    n_h = 0
    for o in bpy.data.objects:
        if o is not sh and (o.name.startswith(RIDERS) or o.name.startswith(ENV_HIDE)):
            o.hide_render = True
            n_h += 1
    env = _env(sc, frame)
    material(sh, rough=ROUGH_SHOT.get(shot))
    print(f"[tin_r33] {shot} {name}: round disc R {R:.4f}, bead {BEAD} (x {BEAD_X}), wrinkles {WRINKLE}, rough {ROUGH}, "
          f"glow arc toward local {tuple(round(x, 2) for x in sd)}, {n_h} riders hidden, env without key box {env}", flush=True)
    return sh


def drops(sc, shot):
    """B1_08: every tin droplet gets the same satin liquid-tin material (no glow) and its env sphere is hidden."""
    n, n_e = 0, 0
    for o in bpy.data.objects:
        if o.type != "MESH":                # (drops key their visibility per frame: do not skip hidden ones)
            continue
        if o.name.startswith("TinEnvR27_") and o.parent is not None:   # drop env rebuilt on a lit-chamber base
            import source_r23_tin as T23
            import source_r24 as H24
            import tin_r29
            tc, rt, up = H24._cam_dirs(sc, DROP_FRAME.get(shot, 1), o.parent.matrix_world.translation.copy())
            mm = T23._env_mat_r23("TinEnvR33Mat_" + o.parent.name, tin_r29.drop_bands(tc, rt, up), DROP_BASE, 1.0, 0.05)
            o.data.materials.clear()
            o.data.materials.append(mm)
            n_e += 1
            continue
        am = o.active_material
        if am is not None and am.name.startswith("TinSilverR29"):
            for s in o.material_slots:
                if s.material is not None and s.material.name.startswith("TinSilverR29"):
                    s.material = _drop_mat()
            n += 1
    print(f"[tin_r33] {shot} droplets: {n} objects -> TinLiquidR33 (rough {ROUGH}), {n_e} drop env spheres on base {DROP_BASE}",
          flush=True)
    return n


def _drop_mat():
    m = bpy.data.materials.get("TinLiquidR33")
    if m is not None:
        return m
    import tin_r29
    m = tin_r29.silver_mat("TinLiquidR33")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*SILVER, 1)
    b.inputs["Roughness"].default_value = ROUGH
    b.inputs["Metallic"].default_value = 1.0
    for k in ("Transmission Weight", "Coat Weight"):
        if k in b.inputs:
            for lk in list(b.inputs[k].links):
                m.node_tree.links.remove(lk)
            b.inputs[k].default_value = 0.0
    return m
