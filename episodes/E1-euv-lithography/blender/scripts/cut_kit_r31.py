"""Round 31 hook (kit sub-agent; r2_cutaway.R31_KIT = {"B8_03", "B8_03M"}). Layered AFTER the R22..R30 hooks (cut_kit_r30
RULER_R30 alignment cross stays; cut_kit_r29 GRID_R29 188 half-fields stays) and BEFORE beam_hook_r29 / r30 / r31.
Beams untouched (B8_03 keeps the R29 beam). Remove a shot from R31_KIT -> exact R30 pixels.

R31_ROOT_CAUSE row 5 (B8_03), R30 p2: 「晶圆台反向移动看不出来（−8.5 mm 在画面上几乎不动）…画中画里掩模没有图形，读不出是
掩模」「①晶圆台加一条同款细标尺（0–10 mm），三帧指针明显向左走，跟上方指针反向、同框可读；②画中画里露出掩模图形面 +
狭缝光斑，标尺标题写『掩模台行程』」. One switch per part of the row (main process can return either at 32 spp):

  RULER_R31  (B8_03) a FIXED 0-10 mm reference ruler (PIP ruler style: dark bar, white ticks + digits, cyan travel bar)
             on a metrology bar with two posts on the deck, just behind the wafer's upper-left edge (out of the PIP band,
             out of the slit haze); a cyan needle parented to WStage rides on it (= the R30 cross's x, 1 mm = 0.02 m as
             PtrW / the read-out), going LEFT 2.5 -> 5.5 -> 8.5 mm while the PIP pointer goes right. The R28 white tick
             bar + WaferRefLineR28 + PtrW L-pointer (the old, unreadable wafer scale under the PIP edge) are hidden - replaced, not dropped.
             The R30 alignment cross stays. Extra anchors (k31_*) are merged into the shot's anchors json for the
             「晶圆台行程」 title in mograph/r2_ov_zz31k.py.
  PIP_R31    (B8_03M) the PIP camera CamR2M drops / tilts up so the mask's patterned face (EUVMaskR10 die fields) and
             the violet slit footprint on it are seen face-on enough to read; zz31k re-crops the PIP to ruler + mask face
             and titles the ruler 「掩模台行程」.
"""
import json
import os

RULER_R31 = True
PIP_R31 = True

_E = os.environ
K_MM = 0.02          # world m per mm on the wafer stage (PtrW / R30 cross measured: -2.5 / -5.5 / -8.5 mm)


def _f(k, d):
    return float(_E.get(k, str(d)))


def _merge_anchors(sc, shot, pts):
    """frame_change_post handler appended AFTER kit_r2.anchors' handler: merge extra keys into the same json."""
    import bpy
    from bpy_extras.object_utils import world_to_camera_view as w2c
    import common as C
    out = os.path.join(C.render_root(), "shots", shot, "anchors")

    def h(sc_, *_):
        cam = sc_.camera
        if cam is None:
            return
        p = os.path.join(out, f"{sc_.frame_current:04d}.json")
        try:
            with open(p) as fh:
                res = json.load(fh)
        except Exception:
            res = {}
        for k, v in pts.items():
            if isinstance(v, bpy.types.Object):
                v = v.matrix_world.translation
            q = w2c(sc_, cam, v)
            res[k] = [round(q.x, 4), round(1 - q.y, 4), round(q.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(p, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


def _ruler(sc):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils import Matrix, Vector
    import cut_kit_r29_b803 as H
    ptr, st = bpy.data.objects.get("PtrW"), bpy.data.objects.get("WStage")
    cross = bpy.data.objects.get("WAlignCrossR30")
    if ptr is None or st is None:
        print("[r31k] PtrW / WStage missing - no ruler", flush=True)
        return
    f0 = sc.frame_current
    xs = {}
    for f in (42, 143):
        sc.frame_set(f)
        xs[f] = sum((ptr.matrix_world @ Vector(c) for c in ptr.bound_box), Vector()).x / 8
    k = (xs[143] - xs[42]) / (-8.5 + 2.5)             # world m per mm (mm negative -> -x)
    xp0 = xs[42] - k * -2.5                            # PtrW x at 0 mm
    # ruler origin (0 mm) = the R30 cross's x at 0 mm, so the needle runs straight above the cross
    sc.frame_set(42)
    xc42 = cross.matrix_world.translation.x if cross else -0.17
    x0 = xc42 - k * -2.5 + _f("R31K_DX", 0.0)
    yb, zb = _f("R31K_Y", -0.52), _f("R31K_Z", 0.735)
    sc.frame_set(92)
    org = Vector((x0, yb, zb))
    to_cam = (sc.camera.matrix_world.translation - org).normalized()
    u = Vector((1, 0, 0))
    n = (to_cam - u * to_cam.dot(u)).normalized()
    v = n.cross(u).normalized()
    M = Matrix((u, v, n)).transposed().to_4x4()
    M.translation = org
    coll = sc.collection
    piv = bpy.data.objects.new("WRulerR31", None)
    coll.objects.link(piv)
    piv.matrix_world = M
    cy = H._emit("WRulerCyanR31M", (0.1, 0.85, 0.95), 4.0)
    wh = H._emit("WRulerWhiteR31M", (0.92, 0.93, 0.95), 2.2)
    dark = H._plain("WRulerPlateR31M", (0.012, 0.014, 0.018), 0.85)
    _bs = next(n_ for n_ in dark.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
    for nm_ in ("Specular IOR Level", "Specular"):             # dark bar like the PIP ruler (no grey sheen)
        if nm_ in _bs.inputs:
            _bs.inputs[nm_].default_value = 0.05
    L = -k * 10.0                                      # 10 mm span: the stage runs -x, so 10 mm is on the LEFT
    lab = _f("R31K_LAB", 0.046)
    ph = _f("R31K_PH", 0.085)
    lo, hi = min(L, 0.0), max(L, 0.0)
    xl = lo - _f("R31K_XL", 0.05)                       # plate runs left past 10 mm (unit + title + the post)
    objs = []
    objs.append(H._quads("WRulerPlateR31", [(xl, -0.016, hi + 0.075, ph)], dark, piv, coll, dz=-0.002))
    ticks = [(lo - 0.002, -0.0025, hi + 0.002, 0.0025)]  # base line at the bottom, ticks UP, digits above
    for mm in range(0, 11):
        uu = -k * mm
        major = mm % 5 == 0
        w_ = 0.0032 if major else 0.002
        ticks.append((uu - w_, 0.0, uu + w_, 0.03 if major else 0.016))
    objs.append(H._quads("WRulerTickR31", ticks, wh, piv, coll))
    fl = bpy.data.fonts.load(H.FONT_L, check_existing=True)
    yl = 0.036
    for mm in (0, 5, 10):
        objs.append(H._text(f"WRulerLab{mm}R31", str(mm), fl, lab, (-k * mm, yl), piv, coll, wh))
    objs.append(H._text("WRulerUnitR31", "mm", fl, lab * 0.75, (hi + 0.016, yl), piv, coll, wh, align="LEFT"))
    # cyan travel bar 0 -> needle, keyed per frame from the stage
    bar = H._quads("WRulerTravelR31", [(-1.0, -0.011, 0.0, -0.004)], cy, piv, coll, dz=0.002)
    objs.append(bar)
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
        px = sum((ptr.matrix_world @ Vector(c) for c in ptr.bound_box), Vector()).x / 8
        bar.scale.x = max(1e-4, -(px - xp0))
        bar.keyframe_insert("scale", index=0, frame=f)
    # one post at the far-left end down to the deck (fixed metrology bar, clear of the moving chuck), bar cantilevered
    zpl = _f("R31K_DECK", 0.551)
    pm = H._plain("WRulerPostR31M", (0.05, 0.055, 0.065), 0.45)
    for ux in (xl + 0.015,):
        bm = bpy.data.meshes.new("WRulerPostR31")
        pw_ = 0.012
        top = M @ Vector((ux, 0.0, -0.004))
        vs = [(top.x - pw_, top.y - pw_, zpl), (top.x + pw_, top.y - pw_, zpl), (top.x + pw_, top.y + pw_, zpl),
              (top.x - pw_, top.y + pw_, zpl)]
        vs += [(a, b, top.z) for a, b, _ in vs]
        bm.from_pydata(vs, [], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
        bm.update()
        po = bpy.data.objects.new("WRulerPostR31", bm)
        coll.objects.link(po)
        bm.materials.append(pm)
    # needle (triangle on the base line + stem down over the ticks) parented to the stage
    sc.frame_set(42)
    pu = -k * 2.5
    pq = [(pu - 0.0055, -_f("R31K_NL", 0.03), pu + 0.0055, 0.032),
          ("tri", (pu, 0.0), (pu - 0.02, -0.028), (pu + 0.02, -0.028))]
    pt = H._quads("WRulerPtrR31", pq, cy, None, coll, dz=0.005)
    objs.append(pt)
    for o in objs:                                      # no mirrored digits in the polished wafer
        o.visible_glossy = False
    pt.data.transform(M)
    pt.parent = st
    pt.matrix_parent_inverse = st.matrix_world.inverted()
    # the old R28 white tick bar + PtrW L-pointer (under the PIP edge, in the slit haze) are replaced by this ruler
    for o in bpy.data.objects:
        if o.name.startswith(("WScaleBarR28", "WScaleTickR28", "WaferRefLineR28")) or o.name == "PtrW":
            o.hide_render = True
    # anchors for the overlay title (left end of the bar, above the plate)
    e0 = bpy.data.objects.new("WRulerAnchorTitleR31", None)
    coll.objects.link(e0)
    e0.matrix_world = M @ Matrix.Translation(Vector((xl - 0.012, ph * 0.45, 0.0)))
    e1 = bpy.data.objects.new("WRulerAnchorEndR31", None)
    coll.objects.link(e1)
    e1.matrix_world = M @ Matrix.Translation(Vector((hi + 0.075, ph * 0.45, 0.0)))
    _merge_anchors(sc, "B8_03", {"k31_t0": e0, "k31_t1": e1})
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in (42, 92, 143):
        sc.frame_set(f)
        P = lambda p: w2c(sc, sc.camera, M @ Vector(p))
        t0, t10 = P((0, 0, 0)), P((L, 0, 0))
        a, b = P((0, yl, 0)), P((0, yl + lab * 0.74, 0))
        pl0, pl1 = P((xl, ph, 0)), P((hi + 0.075, -0.016, 0))
        q = w2c(sc, sc.camera, sum((pt.matrix_world @ Vector(c) for c in pt.bound_box), Vector()) / 8)
        cc = w2c(sc, sc.camera, cross.matrix_world.translation) if cross else q
        print(f"[r31k] f{f} tick0 ({t0.x * 960:.0f},{(1 - t0.y) * 540:.0f}) tick10 ({t10.x * 960:.0f},"
              f"{(1 - t10.y) * 540:.0f}) cap {(a.y - b.y) * 540:.1f}px needle x {q.x * 960:.0f} -> "
              f"{(q.x - t0.x) / (t10.x - t0.x) * 10:.2f} mm plate x {pl0.x * 960:.0f}-{pl1.x * 960:.0f} y {(1 - pl0.y) * 540:.0f}-{(1 - pl1.y) * 540:.0f} cross ({cc.x * 960:.0f},{(1 - cc.y) * 540:.0f})", flush=True)
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
    print(f"[r31k] ruler k {k * 1000:.1f} mm-world/mm x0 {x0:.3f} y {yb} z {zb}", flush=True)


def _long_mask(sc, s):
    """The fixed slit footprint (x = 0) must stay ON the patterned face for the whole scan (8-spp f42: with the 0.52 m
    plate the slit glow hung in the air beside the mask). The plate (+ blank, chuck) is lengthened s x along the scan
    axis; clamps / fiducials shift outward; the die-field pattern is re-tiled (3 s fields, line pitch kept), so the dies
    keep their R10 proportions instead of stretching."""
    import bpy
    if s <= 1.001:
        return
    ms = bpy.data.objects.get("RStageK_mask")
    if ms is None:
        return
    xs = [v.co.x for v in ms.data.vertices]
    cx, half = (min(xs) + max(xs)) / 2, (max(xs) - min(xs)) / 2
    d = (s - 1) * half
    for nm in ("RStageK_mask", "RStageK_subs", "RStageK_ceramic"):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        k_ = _f("R31K_CS", s) if nm == "RStageK_ceramic" else s
        for v in o.data.vertices:
            v.co.x = cx + (v.co.x - cx) * k_
        o.data.update()
    for nm in ("RStageK_alu_dark", "RStageK_label"):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        for v in o.data.vertices:
            v.co.x += d if v.co.x > cx else -d
        o.data.update()
    m0 = ms.data.materials[0] if ms.data.materials else None
    if m0 is None or m0.node_tree is None:
        return
    m = m0.copy()
    m.name = "EUVMaskLongR31"
    ms.data.materials[0] = m
    nt = m.node_tree
    sx = next((n for n in nt.nodes if n.type == "SEPXYZ"), None)
    nf = round(3 * s)
    for n in nt.nodes:
        if n.type == "MATH" and n.inputs[0].is_linked and sx is not None \
                and n.inputs[0].links[0].from_node == sx and n.inputs[0].links[0].from_socket.name == "X":
            v = n.inputs[1].default_value
            if n.operation == "GREATER_THAN" and abs(v - 0.09) < 1e-4:
                n.inputs[1].default_value = 0.09 / s
            elif n.operation == "LESS_THAN" and abs(v - 0.91) < 1e-4:
                n.inputs[1].default_value = 1 - 0.09 / s
            elif n.operation == "SUBTRACT" and abs(v - 0.09) < 1e-4:
                n.inputs[1].default_value = 0.09 / s
                for l_ in n.outputs[0].links:
                    dv = l_.to_node
                    if dv.type == "MATH" and dv.operation == "DIVIDE":
                        dv.inputs[1].default_value = (1 - 0.18 / s) / nf
        if n.type == "TEX_WAVE":
            n.inputs["Scale"].default_value *= s
    print(f"[r31k pip] mask lengthened x{s} ({2 * half * s:.2f} m), {nf} die columns", flush=True)


def _pip(sc):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view as w2c
    from mathutils import Vector
    cam, tgt = bpy.data.objects.get("CamR2M"), bpy.data.objects.get("CamR2M_tgt")
    if cam is None or tgt is None:
        print("[r31k] CamR2M missing", flush=True)
        return
    for o in (cam, tgt):
        o.animation_data_clear()
    cam.location = (0.0, _f("R31K_CY", -3.3), _f("R31K_CZ", 0.85))
    tgt.location = (0.0, 0.0, _f("R31K_TZ", 2.95))
    cam.data.lens = _f("R31K_LENS", 30.0)
    _long_mask(sc, _f("R31K_MS", 3.0))
    # the lower PIP view catches the under-lights' specular on the carriage's front (Alu, speckle-textured) -> 8-spp
    # f42 black / colour speck field; ray-picked object RStage_car only: own copy, speckle unlinked, a bit rougher
    car = bpy.data.objects.get("RStage_car")
    if car is not None and car.data.materials and car.data.materials[0] is not None:
        m = car.data.materials[0].copy()
        m.name = "AluCarPipR31"
        b_ = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b_ is not None:
            for nm in ("Roughness", "Base Color", "Normal", "Coat Weight"):
                if nm in b_.inputs:
                    for l_ in list(b_.inputs[nm].links):
                        m.node_tree.links.remove(l_)
            b_.inputs["Roughness"].default_value = _f("R31K_CR", 0.5)
        car.data.materials[0] = m
    old = sc.camera
    sc.camera = cam
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    for f in (42, 92, 143):
        sc.frame_set(f)
        out = []
        for nm in ("RStageK_mask", "RD0", "RD8", "MaskSlit", "RulerBrk"):
            o = bpy.data.objects.get(nm)
            if o is None:
                continue
            bb = [w2c(sc, cam, o.matrix_world @ Vector(c)) for c in o.bound_box]
            out.append(f"{nm} x {min(p.x for p in bb) * 960:.0f}-{max(p.x for p in bb) * 960:.0f} "
                       f"y {min(1 - p.y for p in bb) * 540:.0f}-{max(1 - p.y for p in bb) * 540:.0f}")
        print(f"[r31k pip] f{f} " + " | ".join(out), flush=True)
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.camera = old


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "B8_03" and RULER_R31:
        _ruler(sc)
    if shot == "B8_03M" and PIP_R31:
        _pip(sc)
    return sc
