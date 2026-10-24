"""Round 24 hook (owned by the 'mbeam' sub-agent; shots in r2_misc.R24_BEAM = B4_07 / A2_03 / B8_17).

R24_ROOT_CAUSE row #3 (light path, shared beam_r24): R23 review p3 #2 「光束统一成锥形收放 + 软边 + 镜面椭圆落点（B4_07、A2_03、
B8_17）：把剩下的等宽管和光在空中折返的读法去掉」. Per shot the old beam objects of that screen (R16-R21 cores / cones / halos /
spots) are deleted and ONE ordered path is built with beam_r24.chain (soft surface cones whose end radii are the apertures,
flat elliptical landing highlights ON the faces); beam_r24.check runs on the 3 job frames (BEAMCHECK lines in the log).
- B4_07: incoming cone converges onto the coating, reflected cone opens out of the same elliptical spot.
- A2_03: the single fold PO4 -> PO5 -> wafer (NA cone, lit at the NA beat) with a landing ellipse on PO5's face.
- B8_17: exit slot -> fixed slit cone; at the end the exposed (all-grey) wafer is carried to the cassette, a fresh dark
  wafer slides onto the chuck and the cone lights again (R23 review: 「保留已曝光的晶圆移到片架，换新片时让光锥重新亮起」).
Remove a shot from r2_misc.R24_BEAM -> exact R23 pixels.
"""
import math

import bpy
from mathutils import Vector

JOB = {"B4_07": (36, 79, 122), "A2_03": (74, 163, 252), "B8_17": (56, 122, 189)}


def pre(variant, shot, mod):
    pass


def _kill(prefixes=(), names=()):
    gone = []
    for ob in list(bpy.data.objects):
        if ob.name in names or (prefixes and ob.name.startswith(tuple(prefixes))):
            gone.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    print(f"[R24 mbeam] removed old beam objects: {gone}", flush=True)


def _vis_keys(ob, spans, n):
    """spans = list of (f0, f1) frames where ob is visible (inclusive); hidden elsewhere."""
    if ob.animation_data:
        ob.animation_data_clear()
    on = set()
    for f0, f1 in spans:
        on.update(range(max(1, f0), f1 + 1))
    prev = None
    for f in range(1, n + 2):
        v = f in on
        if v != prev:
            ob.hide_render = not v
            ob.keyframe_insert("hide_render", frame=f)
            ob.hide_viewport = not v
            ob.keyframe_insert("hide_viewport", frame=f)
            prev = v


def _chain_objs(ch):
    out = []
    for leg in ch["legs"]:
        out += list(leg)
    out += [s for s in ch["spots"] if s is not None]
    return out


# ------------------------------------------------------------------------------------------------ B4_07
def _b407(sc):
    import beam_r24 as BR
    _kill(prefixes=("BeamInR19", "BeamOutR19", "BeamHaloR19", "BeamSpotR17", "BeamR17", "BeamOutR17"),
          names=())
    hit = Vector((0.15, 0.25, 0.006))
    # the V (in / out) lies in the vertical plane ACROSS the push-in line of sight (R23's V leaned toward the camera
    # on the push: incoming leg 32 deg to the line of sight at 79 %): legs splay left / right of the landing spot
    sc.frame_set(JOB["B4_07"][1])
    v = sc.camera.matrix_world.translation - hit
    h = Vector((v.x, v.y, 0.0)).normalized()
    perp = Vector((-h.y, h.x, 0.0))
    import os
    sp, bk, Lg = (float(x) for x in os.environ.get("B407_GEOM", "1.0,0.5,2.5").split(","))
    din = (perp * sp + Vector((0, 0, 1.0)) - h * bk).normalized()
    rout = (-perp * sp + Vector((0, 0, 1.0)) - h * bk).normalized()
    ch = BR.chain("B407R24", [(hit + din * Lg, None), (hit, (0, 0, 1)), (hit + rout * Lg, None)],
                  radii=[0.36, 0.06, 0.26], strength=3.0, alpha=0.6, edge=1.8, inner=0.45, spot_strength=16.0,
                  spot_scale=1.9, gain=0.4)
    for ob in _chain_objs(ch):
        if ob.name.startswith("B407R24Spot"):
            ob.visible_glossy = False
    # on the push-in to the cut edge the whole path leaves the frame: from the first frame after which no point of
    # either leg projects inside the frame, the path is keyed off (no pop: it is already off screen)
    from bpy_extras.object_utils import world_to_camera_view as w2c
    n = sc.frame_end
    stops = [p for p, _n in ch["stops"]]
    samples = [stops[i].lerp(stops[i + 1], t / 24) for i in range(2) for t in range(25)]

    def inside(fr):
        sc.frame_set(fr)
        for p in samples:
            q = w2c(sc, sc.camera, p)
            if q.z > 0 and -0.02 <= q.x <= 1.02 and -0.02 <= q.y <= 1.02:
                return True
        return False
    f_off = n + 1
    for fr in range(n, 1, -1):
        if inside(fr):
            break
        f_off = fr
    if f_off <= n:
        _vis_and = _chain_objs(ch)
        for ob in _vis_and:
            _vis_keys(ob, [(1, f_off - 1)], n)
    print(f"[R24 B4_07] V across the line of sight; path fully off screen from f{f_off} -> keyed off there", flush=True)
    f = JOB["B4_07"]
    BR.check(sc, ch, [x for x in f if x < f_off], exits=(0, 2), tag="B4_07")
    print(f"BEAMCHECK B4_07 frames {[x for x in f if x >= f_off]}: path keyed off (entirely off screen on the push-in)",
          flush=True)


# ------------------------------------------------------------------------------------------------ A2_03
def _a203(sc):
    import beam_r24 as BR
    import build_cutaway_r2 as B
    import kit_r2 as K
    n = sc.frame_end
    _kill(prefixes=("FoldR18", "NAConeR18", "MirrorSpotR19_", "MirrorSpotR21_", "LandR17_", "WaferSpotR18",
                    "LandingSpotsR14", "CoreR17_"))
    pts = [Vector(B.MASK)] + [Vector(v) for v in B.PO] + [Vector(B.WAFER)]
    nrm = [K.mirror_normal(pts[i], Vector(p), pts[i + 2]) for i, p in enumerate(B.PO)]
    po4, po5 = Vector(B.PO[4]), Vector(B.PO[5])
    wf = Vector((B.WAFER.x, 0.0, 1.065))
    ch = BR.chain("A203R24", [(po4, nrm[4]), (po5, nrm[5]), (wf, (0, 0, 1))],
                  radii=[B.PO_R[4] * 0.6, B.PO_R[5] * 0.62, 0.006], strength=3.0, alpha=0.55, edge=1.7,
                  inner=0.45, spot_strength=14.0, gain=0.4)
    # the start of the fold also lands ON PO4's face (it is the turn from the previous mirror)
    s4 = BR.landing("A203R24Spot0", po4, po4 - po5, nrm[4], B.PO_R[4] * 0.6, strength=10.0)
    ws = BR.landing("A203R24WaferSpot", wf, wf - po5, (0, 0, 1), 0.05, strength=10.0)
    # PO5's face points DOWN (camera sees it edge-on from above): its landing ellipse is hidden by the blank, so the
    # footprint shows where it meets the camera-side lip of the coated face: a short bright arc on the face edge
    # (= the landing ellipse seen edge-on), centred on the side facing the camera
    sc.frame_set(JOB["A2_03"][2])
    n5 = Vector(nrm[5]).normalized()
    cdir = sc.camera.matrix_world.translation - po5
    e1 = (cdir - n5 * cdir.dot(n5)).normalized()
    e2 = n5.cross(e1).normalized()
    r5 = B.PO_R[5] * 1.24
    arc = [po5 - n5 * 0.004 + (e1 * math.cos(math.radians(t)) + e2 * math.sin(math.radians(t))) * r5 * 1.025
           for t in range(-12, 13, 2)]
    gmb = K.MB()
    gmb.path(arc, 0.011, seg=10)
    glint = gmb.obj("A203R24LipGlint", K.emit_mat("A203R24LipGlintM", (0.9, 0.84, 1.0), 16.0))
    glint.visible_shadow = False
    f_on = round(n * 0.48)
    BR.key_chain(ch, [1, f_on])
    _vis_keys(ws, [(f_on, n + 1)], n)
    print(f"[R24 A2_03] PO4 {tuple(round(x, 3) for x in po4)} PO5 {tuple(round(x, 3) for x in po5)} wafer "
          f"{tuple(round(x, 3) for x in wf)}; NA leg on at f{f_on}; spot0 {s4.name}", flush=True)
    BR.check(sc, ch, JOB["A2_03"], tag="A2_03")


# ------------------------------------------------------------------------------------------------ B8_17
def _b817(sc):
    import beam_r24 as BR
    import misc_b817_r22 as W22
    n = sc.frame_end
    dur = n / 24
    _kill(prefixes=("SlitConeR18", "SlitConeR20", "SlitConeR21"))
    slit = bpy.data.objects["Slit"]
    PX, PY, PZ = 0.45 - 1.2, 1.3, 1.72
    S = Vector(slit.location)
    ch = BR.chain("B817R24", [(Vector((PX, PY, PZ - 0.006)), None), (Vector((S.x, S.y, 0.0106)), (0, 0, 1))],
                  radii=[(0.43, 0.16), (0.07, 0.006)], strength=0.8, alpha=0.15, edge=3.0, inner=0.4, fade0=0.25,
                  spot_strength=4.0, spot_scale=0.45, gain=2.5, xdir=(1, 0, 0))
    done = next(f for f in range(1, n + 2) if W22.counter(f, dur) >= W22.COUNT)
    T0 = done + 3                  # last field exposed -> light off, exposed wafer leaves for the cassette
    T_new, T_seat, T_on = T0 + 5, T0 + 10, T0 + 11
    rig = bpy.data.objects.get("WaferStageR21")
    kids = [o for o in rig.children if not o.name.startswith("Chuck") and not o.hide_render and o.type == "MESH"]
    print(f"[R24 B8_17] done f{done}; T0 {T0}; wafer parts: {[o.name for o in kids]}", flush=True)
    # 1) exposed wafer: copies at the world pose of T0, carried in an arc into the cassette's top slot
    sc.frame_set(T0)
    carrier = bpy.data.objects.new("ExposedCarrierR24", None)
    sc.collection.objects.link(carrier)
    exp = []
    for o in kids:
        c = o.copy()
        c.animation_data_clear()
        sc.collection.objects.link(c)
        c.parent = carrier
        c.matrix_parent_inverse.identity()
        c.matrix_world = o.matrix_world.copy()
        c.name = "Exposed" + o.name + "R24"
        exp.append(c)
        _vis_keys(c, [(T0, n + 1)], n)
        _vis_keys(o, [(1, T0 - 1)], n)
    wc = next((o.matrix_world.translation.copy() for o in kids if o.name == "Wafer"), Vector((0, 0, 0)))
    # it goes into a cassette slot BELOW the counter panel (slot 12, z 0.85; that slot's stack wafer is left out) so the
    # grey 188-field wafer is seen sliding into the rack, not lost under the panel
    k_slot = 12
    st = bpy.data.objects.get(f"Stack{k_slot}")
    if st is not None:
        st.animation_data_clear()
        st.hide_render = True
    slot = Vector((3.4 + 0.8, 0.0, -0.05 + k_slot * 0.075 + 0.004))
    entry = Vector((slot.x - 3.2, slot.y, slot.z))
    T_up, T1 = T0 + 6, T0 + 18
    for f in range(T0, T1 + 1):
        if f <= T_up:
            u = (f - T0) / (T_up - T0)
            e = u * u * (3 - 2 * u)
            p = wc.lerp(entry, e)
        else:
            u = (f - T_up) / (T1 - T_up)
            e = u * u * (3 - 2 * u)
            p = entry.lerp(slot, e)
        carrier.location = p - wc
        carrier.keyframe_insert("location", frame=f)
    # 2) fresh wafer (all fields unexposed) slides onto the chuck, riding the stage
    newc = bpy.data.objects.new("FreshCarrierR24", None)
    sc.collection.objects.link(newc)
    newc.parent = rig
    newc.matrix_parent_inverse.identity()
    for o in kids:
        c = o.copy()
        c.animation_data_clear()
        if o.name.startswith("FieldsR20"):
            c.data = o.data.copy()
            m = o.data.materials[0].copy()
            m.name = "FieldR24Fresh"
            nt = m.node_tree
            if nt.animation_data:
                nt.animation_data_clear()
            val = next(x for x in nt.nodes if x.type == "VALUE")
            val.outputs[0].default_value = 0.0
            c.data.materials[0] = m
        sc.collection.objects.link(c)
        c.parent = newc
        c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        c.matrix_basis = o.matrix_basis.copy()
        c.name = "Fresh" + o.name + "R24"
        _vis_keys(c, [(T_new, n + 1)], n)
    for f, off in ((T_new, Vector((-3.2, 0.0, 0.25))), (T_seat - 1, Vector((0, 0, 0.04))), (T_seat, Vector((0, 0, 0)))):
        newc.location = off
        newc.keyframe_insert("location", frame=f)
    # 3) light: on while exposing, off during the swap, on again over the fresh wafer
    for ob in _chain_objs(ch) + [slit]:
        _vis_keys(ob, [(1, T0 - 1), (T_on, n + 1)], n)
    print(f"[R24 B8_17] light off f{T0}-{T_on - 1}; fresh wafer in f{T_new}-{T_seat}; exposed wafer in cassette f{T1}",
          flush=True)
    BR.check(sc, ch, JOB["B8_17"], tag="B8_17")


def post(sc, variant, shot):
    import os
    if os.environ.get("MBEAM_R24_OFF"):          # diagnostics only (smoke A/B against the R23 build)
        return
    fn = {"B4_07": _b407, "A2_03": _a203, "B8_17": _b817}.get(shot)
    if fn is not None:
        fn(sc)
