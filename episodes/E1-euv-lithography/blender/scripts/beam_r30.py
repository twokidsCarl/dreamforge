"""Round 30 (P1, R30_ROOT_CAUSE row 2 - beam TAPER + on-screen FLOOR; MAIN process, agents never edit it).

R29 review: beam_r29 volumes are right in kind (centre-bright, soft, background visible) but
  * the legs are still read as 「等宽的圆管」 (B5_01: 3:1 end radii), 「一片扁平楔子…IF 标在墙上，离锥尖还有一段距离」
    (B3_02), 「水平宽管，没有往 IF 锥尖收拢」 (C_03, where IF -> entry -> FFM even NARROWED towards the FFM), 「狭缝光现在是
    一团雾」 (B8_03), 「会聚到点的光锥…和『狭缝扫描』对不上」 (B8_17);
  * in the wide title shot the thin legs are 3-5 px wide on screen and fade into the bay (A0_10 H13 「光路断」).
beam_r30 changes the cone each leg is BUILT with (beam_r29.cone is wrapped while beam_hook_r29 converts - that hook
stays the only converter and stays LAST):
  TAPER: per shot, named FOCUS ends (IF / wafer / slit / mask landing / PFM) get an aperture <= wide end / RATIO
      (4.5 -> on screen <= 1/4); legs whose geometry runs the wrong way (C_03 entry -> FFM) get explicit radii; a slit
      end is an ellipse (long axis kept, thin axis = SLIT_THIN).
  FLOOR: every leg is projected on the shot's three job frames; if the mid-leg on-screen width is < FLOOR_PX (6 px at
      960x540) both apertures are scaled up until it is not, and a narrow end below END_PX (3 px) is widened (ratio kept
      >= RATIO by widening the wide end with it).
Radiance on the axis stays beam_r29's B * (R0 / R)^GAMMA (independent of the absolute width), so widening does not dim
a leg and the focus end stays the brighter end. No shell parameter, no fade, no level below 0.6.
"""
import bpy
from mathutils import Vector

RATIO = 4.5
FLOOR_PX = 6.0
END_PX = 3.0
SLIT_THIN = 0.1     # slit thin axis = this x the long axis at the focus end

JOBS = {}           # shot -> job frames (filled from handoff/p1/round29_jobs.txt)
LOG = []


def _jobs(shot):
    if not JOBS:
        import os
        p = os.path.join(os.path.dirname(__file__), "..", "..", "handoff", "p1", "round29_jobs.txt")
        for ln in open(p):
            f = ln.split()
            if len(f) == 2 and not ln.startswith("#"):
                JOBS[f[0]] = [int(x) for x in f[1].split(",")]
    return JOBS.get(shot, [])


def _px_width(sc, cam, p, r, d):
    """on-screen width (960 px frame) of a disc of radius r at world point p, perpendicular to direction d."""
    from bpy_extras.object_utils import world_to_camera_view as w2c
    view = (p - cam.matrix_world.translation).normalized()
    u = d.cross(view)
    if u.length < 1e-6:
        return None
    u.normalize()
    q0, q1 = w2c(sc, cam, p), w2c(sc, cam, p + u * r)
    if q0.z <= 0:
        return None
    if not (-0.2 <= q0.x <= 1.2 and -0.2 <= q0.y <= 1.2):
        return None
    return 2 * ((Vector((q1.x, q1.y)) - Vector((q0.x, q0.y))) * Vector((960, 540))).length


def _taper(spec, ra, rb):
    """spec: {'a': True} / {'b': True} focus end(s); {'ra': .., 'rb': ..} overrides; {'slit': 'b'} slit focus end."""
    ra, rb = list(ra), list(rb)
    if "ra" in spec:
        ra = list(spec["ra"]) if isinstance(spec["ra"], (tuple, list)) else [spec["ra"]] * 2
    if "rb" in spec:
        rb = list(spec["rb"]) if isinstance(spec["rb"], (tuple, list)) else [spec["rb"]] * 2
    for end, me, other in (("a", ra, rb), ("b", rb, ra)):
        if spec.get(end):
            wide = max(other)
            for i in (0, 1):
                me[i] = min(me[i], wide / RATIO)
        if spec.get("slit") == end:
            i_long = 0 if me[0] >= me[1] else 1
            long_ = spec.get("slit_long", me[i_long])
            me[i_long] = long_
            me[1 - i_long] = min(me[1 - i_long], long_ * SLIT_THIN, max(other) / RATIO)
    return tuple(ra), tuple(rb)


def _floor(name, a, b, ra, rb, parent, frames, floor_px=FLOOR_PX):
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None or not frames:
        return ra, rb, None
    keep = sc.frame_current
    k_mid, k_end, worst = 1.0, 1.0, None
    sa = parent.matrix_world.to_scale().x if parent is not None else 1.0
    for f in frames:
        sc.frame_set(f)
        M = parent.matrix_world if parent is not None else None
        wa = (M @ Vector(a)) if M is not None else Vector(a)
        wb = (M @ Vector(b)) if M is not None else Vector(b)
        d = (wb - wa).normalized()
        rm = 0.5 * (max(ra) + max(rb)) * sa
        w_mid = _px_width(sc, cam, wa.lerp(wb, 0.5), rm, d)
        if w_mid is not None and w_mid > 0:
            k_mid = max(k_mid, floor_px / w_mid)
            worst = w_mid if worst is None else min(worst, w_mid)
        for p, r in ((wa, max(ra) * sa), (wb, max(rb) * sa)):
            w = _px_width(sc, cam, p, r, d)
            if w is not None and w > 0:
                k_end = max(k_end, END_PX / w)
    sc.frame_set(keep)
    if k_mid > 1.0:
        ra, rb = tuple(x * k_mid for x in ra), tuple(x * k_mid for x in rb)
        k_end = max(1.0, k_end / k_mid)
    if k_end > 1.0:
        na, nb = max(ra), max(rb)
        if na <= nb:
            ra = tuple(x * k_end for x in ra)
            rb = tuple(max(x, max(ra) * RATIO * (x / nb)) for x in rb)
        else:
            rb = tuple(x * k_end for x in rb)
            ra = tuple(max(x, max(rb) * RATIO * (x / na)) for x in ra)
    return ra, rb, (worst, k_mid, k_end)


SLIT_GAIN = 6.0      # landing line radiance (scene linear) - the slit end of a fan is a clear bright line on the face


def spot_disc(name, ctr, ex, ey, nz, color, gain=None):
    """a soft-edged bright ellipse: centre ctr, semi-axes ex / ey (world vectors), normal nz. Camera-only."""
    import math
    import kit_r2 as K
    from mathutils import Matrix
    me = bpy.data.meshes.new(name)
    n = 48
    vs = [(0.0, 0.0, 0.0)] + [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    fs = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    me.from_pydata(vs, [], fs)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    R = Matrix((Vector(ex), Vector(ey), Vector(nz).normalized())).transposed().to_4x4()
    R.translation = Vector(ctr)
    ob.matrix_world = R
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    for x in list(N):
        if x.type != "OUTPUT_MATERIAL":
            N.remove(x)
    out = next(x for x in N if x.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    Lk.new(tc.outputs["Object"], ln.inputs[0])
    rmp = N.new("ShaderNodeMapRange")
    rmp.inputs["From Min"].default_value = 0.45
    rmp.inputs["From Max"].default_value = 1.0
    rmp.inputs["To Min"].default_value = SLIT_GAIN if gain is None else gain
    rmp.inputs["To Max"].default_value = 0.0
    Lk.new(ln.outputs["Value"], rmp.inputs["Value"])
    em = N.new("ShaderNodeEmission")
    c = K.lin(K.VIOLET if color is None else color)
    em.inputs["Color"].default_value = (0.5 + 0.5 * c[0], 0.5 + 0.5 * c[1], 0.5 + 0.5 * c[2], 1)
    Lk.new(rmp.outputs["Result"], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeAddShader")
    Lk.new(em.outputs[0], mx.inputs[0])
    Lk.new(tr.outputs[0], mx.inputs[1])
    Lk.new(mx.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    for a_ in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        try:
            setattr(ob, a_, False)
        except AttributeError:
            pass
    return ob


def _slit_line(cone_ob, r, at_end, color, face=(0, 0, 1)):
    """the slit at the focus end of a fan leg, laid flat ON the landing face (normal `face`), long axis = the cone's x
    axis projected on the face."""
    bpy.context.view_layer.update()
    L = cone_ob["r29_beam"][0]
    Mc = cone_ob.matrix_world
    sc_ = Mc.to_scale().x
    ctr = Mc @ Vector((0.0, 0.0, L if at_end else 0.0))
    nz = Vector(face).normalized()
    ex = Mc.to_3x3() @ Vector((1, 0, 0))
    ex = (ex - nz * ex.dot(nz)).normalized()
    ey = nz.cross(ex).normalized()
    ob = spot_disc(cone_ob.name + "Slit", ctr + nz * 0.002, ex * r[0] * sc_ * 1.05, ey * r[1] * sc_ * 1.0, nz, color)
    print(f"[beam_r30] slit line {ob.name} r {tuple(round(x, 3) for x in r)}", flush=True)
    return ob


def install(shot, focus, taper=True, floor=True, gain=None):
    """wrap beam_r29.cone for this build: focus = {leg-name prefix: spec}; gain = {leg-name prefix: strength x}."""
    import beam_r29 as B29
    orig = getattr(B29.cone, "_r30_orig", B29.cone)
    frames = _jobs(shot)

    def cone(name, a, b, ra, rb, color=None, strength=B29.B_DEFAULT, xdir=None, parent=None):
        ra = (ra, ra) if isinstance(ra, (int, float)) else tuple(ra)
        rb = (rb, rb) if isinstance(rb, (int, float)) else tuple(rb)
        leg = name[:-3] if name.endswith("V29") else name
        r0 = (ra, rb)
        spec = next((v for k, v in focus.items() if leg.startswith(k)), None)
        if taper and spec:
            ra, rb = _taper(spec, ra, rb)
        info = None
        if floor:
            ra, rb, info = _floor(name, a, b, ra, rb, parent, frames)
        g = next((v for k, v in (gain or {}).items() if leg.startswith(k)), 1.0)
        msg = (f"[beam_r30] {shot} {leg} r {tuple(round(x, 3) for x in r0[0])}->{tuple(round(x, 3) for x in r0[1])}"
               f" => {tuple(round(x, 3) for x in ra)}->{tuple(round(x, 3) for x in rb)} focus {spec} gain {g}"
               f" floor {None if info is None else tuple(None if x is None else round(x, 2) for x in info)}")
        print(msg, flush=True)
        LOG.append(msg)
        if spec and spec.get("slit_dir") is not None:
            xd = Vector(spec["slit_dir"])
            if parent is not None:
                xd = parent.matrix_world.to_3x3().inverted() @ xd
            xdir = xd
        ob = orig(name, a, b, ra, rb, color, strength * g, xdir=xdir, parent=parent)
        if taper and spec and spec.get("slit") in ("a", "b"):
            _slit_line(ob, ra if spec["slit"] == "a" else rb, spec["slit"] == "b", color, spec.get("face", (0, 0, 1)))
        return ob
    cone._r30_orig = orig
    B29.cone = cone
