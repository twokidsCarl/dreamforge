"""Round 26 (P1) tin helpers (R26_ROOT_CAUSE row 3: camera push + laser landing + thinner film; material frozen).
Used only by source_r26.py.

  push_camera   every CamR2 location key moved toward the target's location at the same frame (distance x k);
                handles move with their key, so the R25 camera motion keeps its shape (D-row motion kept).
  landing_rim   orange emissive arc on the camera-side rim of the sheet (parented to PancakeRoot), keyed on only
                while the main pulse hits = where the laser lands is visible (the face it hits is turned away).
  dash_to_lock  B1_08: the pending-laser dashes run on to the lock point (they used to stop short of the droplet).
"""
import math

import bpy
from mathutils import Vector

import kit_r2 as K


def _fcs(ob):
    ad = ob.animation_data
    if not (ad and ad.action):
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:
        return [fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves]


def _target(cam):
    for c in cam.constraints:
        t = getattr(c, "target", None)
        if t is not None:
            return t
    return bpy.data.objects.get(cam.name + "Target") or bpy.data.objects.get("CamR2Tgt")


def push_camera(sc, k):
    """k: a factor for every key, or {frame: factor}: existing keys not listed keep factor 1, listed frames that
    are not keys get a NEW key (original path position pulled toward the target) - all positions are evaluated on
    the original R25 path before anything is changed."""
    cam = sc.camera or bpy.data.objects.get("CamR2")
    tgt = _target(cam)
    loc = {fc.array_index: fc for fc in _fcs(cam) if fc.data_path == "location"}
    tl = {fc.array_index: fc for fc in _fcs(tgt) if fc.data_path == "location"} if tgt else {}
    if len(loc) != 3:
        return
    keys = sorted({int(round(kp.co[0])) for fc in loc.values() for kp in fc.keyframe_points})
    frames = sorted(set(keys) | (set(k) if isinstance(k, dict) else set()))
    plan = []
    for f in frames:
        c = Vector([loc[i].evaluate(f) for i in range(3)])
        t = Vector([tl[i].evaluate(f) for i in range(3)]) if len(tl) == 3 else Vector((0, 0, 0))
        kk = k.get(f, 1.0) if isinstance(k, dict) else k
        plan.append((f, t + (c - t) * kk))
    for f, new in plan:
        for i in range(3):
            hit = [kp for kp in loc[i].keyframe_points if abs(kp.co[0] - f) < 1e-3]
            if hit:
                kp = hit[0]
                d = new[i] - kp.co[1]
                kp.co[1] += d
                kp.handle_left[1] += d
                kp.handle_right[1] += d
            else:
                kp = loc[i].keyframe_points.insert(f, new[i])
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_IN_OUT"
    for fc in loc.values():
        fc.update()
    cam["r26_push"] = str(k)


def landing_rim(f0, f1, a0=math.radians(95), a1=math.radians(265), strength=10.0, name="TinLandingR26"):
    root = bpy.data.objects.get("PancakeRoot")
    if root is None:
        return None
    import source_r24_tin as T24
    rims = root.get("r24_rim")
    mb = K.MB()
    n = 48
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        rr = rims[int(round(a / (2 * math.pi) * 64)) % 64] if rims else 1.0
        rho = rr + T24.HE * 0.5
        pts.append(Vector((-T24.CUP * 0.0, rho * math.cos(a), rho * math.sin(a))))
    for i in range(n):
        w = math.sin(math.pi * (i + 0.5) / n)
        mb.tube(tuple(pts[i]), tuple(pts[i + 1]), 0.010 + 0.022 * w, seg=8)
    m = K.emit_mat(name + "Mat", (1.0, 0.45, 0.10), strength)
    ob = mb.obj(name, m)
    ob.parent = root
    ob.visible_shadow = False
    ob.visible_glossy = False
    for f, h in ((1, True), (f0 - 1, False), (f1 + 1, True)):     # geometry only exists in the pulse window
        ob.hide_render = h
        ob.keyframe_insert("hide_render", frame=f)
    for fc in _fcs(ob):
        for kp_ in fc.keyframe_points:
            kp_.interpolation = "CONSTANT"
    em = next(nd for nd in m.node_tree.nodes if nd.type == "EMISSION")
    for f, s in ((f0 - 1, 0.0), (f0 + 2, strength), (f1 - 4, strength * 0.7), (f1, 0.0)):
        em.inputs["Strength"].default_value = s
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    return ob


def dash_to_lock(mod_coll_x=-0.9, r_drop=0.016):
    old = bpy.data.objects.get("PendingLaser")
    if old is None:
        return None
    mat = old.active_material
    vis = (old.visible_diffuse, old.visible_glossy, old.visible_shadow, old.visible_transmission,
           old.visible_volume_scatter)
    bpy.data.objects.remove(old, do_unlink=True)
    dsh = K.MB()
    x_end = -r_drop * 1.15
    x0 = mod_coll_x + 0.05
    while x0 + 0.03 < x_end:
        dsh.tube((x0, 0.0, 0.0), (x0 + 0.03, 0.0, 0.0), 0.0018, seg=8)
        x0 += 0.06
    dsh.tube((x_end - 0.03, 0.0, 0.0), (x_end, 0.0, 0.0), 0.0018, seg=8, r2=0.0009)   # last dash ends on the lock point
    ob = dsh.obj("PendingLaser", mat)
    (ob.visible_diffuse, ob.visible_glossy, ob.visible_shadow, ob.visible_transmission,
     ob.visible_volume_scatter) = vis
    return ob


def dash_follow(n, lock_z=0.0, past=0.04):
    """B1_08: the pending-laser dashes ride at the height of the droplet nearest the lock line (a droplet more than
    `past` below the lock line is done: the dashes snap to the next one) - the dashed aim line always ends on a droplet (review: 虚线终点随锡滴移动)."""
    ob = bpy.data.objects.get("PendingLaser")
    if ob is None:
        return None
    drops = []
    for i in range(16):
        d = bpy.data.objects.get(f"Drop{i}")
        if d is None or d.hide_render and not (d.animation_data and d.animation_data.action):
            continue
        fz = [fc for fc in _fcs(d) if fc.data_path == "location" and fc.array_index == 2]
        fh = [fc for fc in _fcs(d) if fc.data_path == "hide_render"]
        if fz:
            drops.append((fz[0], fh[0] if fh else None, d))
    if not drops:
        return None
    for f in range(1, n + 1):
        best = None
        for fz, fh, d in drops:
            if (fh is not None and fh.evaluate(f) > 0.5) or (fh is None and d.hide_render):
                continue
            z = fz.evaluate(f)
            if z < lock_z - past:            # already through the lock line: aim at the next droplet
                continue
            if best is None or abs(z - lock_z) < abs(best - lock_z):
                best = z
        if best is None:
            continue
        ob.location = (0.0, 0.0, best - lock_z)
        ob.keyframe_insert("location", index=2, frame=f)
    for fc in _fcs(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return ob
