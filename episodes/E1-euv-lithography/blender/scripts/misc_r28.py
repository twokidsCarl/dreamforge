"""Round 28 hook (misc sub-agent; shots in r2_misc.R28_MISC = B6_12 / A2_03). Layered AFTER the R20..R27 hooks.

One module-level switch per root-cause row (False -> that row's R27 pixels for the shot):
- FILM_R28    (row 4, B6_12)  R27 p3 「放大框里的『13 nm 膜』画成和掩模一样厚的白板…膜画成一根发丝细线，框架另画成实体…
  用破断线表示」. The magnifier is a 3D camera-parented inset (misc_b612_r21 MagnifierR21) that sits ~6 px out of focus in
  the last beat (a 3D hair-line smears to a 7 px plate; pushing the inset into the focal plane buries it in the chuck), so:
  3D: frame bar -> a lit solid grey block (cut by a dark break band), mask -> one thick DARK block (dark substrate + dark
  blue multilayer + black absorber teeth; the light multilayer slab is gone), gap rule split at mid-gap, inset key dimmed;
  the 3D membrane slab is hidden. 2D: mograph/r2_ov_zz28m.py draws the membrane as a crisp 1.5 px hair-line + two break
  strokes across the gap rule from anchors exported here (mag_hair_l / _r, mag_brk_*) -> that overlay IS the structural
  fix for the film thickness (gated on R28_MISC + FILM_R28). Overlay label 「间距不按比例」 kept.
- FACE_R28    (row 4, B6_12)  R27 p3 「掩模图形面看起来像 CAD 线稿…图形面做深色镜面加规则的吸收层线阵，带一点掠射反光」.
  MaskTop material -> procedural: deep blue-black Mo/Si multilayer mirror (constant-tint glossy, rough 0.05) + absorber line
  arrays (dark matte TaN lines, 3 x 2 dies, each die = 4 x 4 blocks of horizontal / vertical line arrays or bare mirror,
  bare scribe lanes) and a grazing highlight: an area strip light-linked to MaskTop only, re-solved per frame by
  mirror geometry so its reflection crosses the face. The R19 die-photo texture (CAD look) is no longer used.
- HOSE_R28    (row 4, B6_12)  R27 p3 「浅蓝色气管又亮又饱和…降成灰蓝或不锈钢编织管」: GasHosesR20 -> stainless braided
  hose (metallic grey, crossed-wave braid bump). Cyan stays only on leaders / magnifier.
- NAVIOLET_R28 (row 5, A2_03) R27 p3 「顶镜→晶圆那段画成紫色会聚光锥，青色只留 θ 角标和中轴虚线」: the R27 NA cone
  (NAConeR27, geometry + theta growth kept) gets a clearly violet shell, the two cyan cone-edge lines are removed
  (they made the 「青色线框锥」), theta arc + glyph + dashed axis stay cyan, and a violet landing spot sits on the wafer
  at the apex.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

FILM_R28 = True
FACE_R28 = True
HOSE_R28 = True
NAVIOLET_R28 = True


def pre(variant, shot, mod):
    pass


def post(sc, variant, shot):
    for sw, sh, fn in (("FILM_R28", "B6_12", _b612_film), ("FACE_R28", "B6_12", _b612_face),
                       ("HOSE_R28", "B6_12", _b612_hose), ("NAVIOLET_R28", "A2_03", _a203_violet)):
        if shot != sh or not globals()[sw]:
            continue
        try:
            fn(sc)
        except Exception as e:   # never break the build; the log shows it
            import traceback
            traceback.print_exc()
            print(f"[R28 misc] {shot} {sw} FAILED: {e}", flush=True)
    return sc


# ------------------------------------------------------------------------------------------------ helpers
def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def _op(nt, op, a, b=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for k, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m.inputs[k].default_value = x
        else:
            nt.links.new(x, m.inputs[k])
    return m.outputs[0]


def _swap_mesh(ob, mb, mat):
    """Replace ob's mesh with the MB geometry (keeps ob, its parent, keys, name)."""
    tmp = mb.obj(ob.name + "_tmp28", mat)
    old = ob.data
    ob.data = tmp.data
    bpy.data.objects.remove(tmp, do_unlink=True)
    if old.users == 0:
        bpy.data.meshes.remove(old)


# ------------------------------------------------------------------------------------------------ B6_12 FILM
MAG_KEY = 1.8
MAG_DEPTH = 0.0    # inset depth as a fraction of the last-beat focus distance (0 = R21 depth)


def _b612_film(sc):
    import kit_r2 as K
    rim = bpy.data.objects.get("MagRimR21")
    mem = bpy.data.objects.get("MagMembraneR21")
    if rim is None or mem is None:
        print("[R28 B6_12] FILM_R28: magnifier missing", flush=True)
        return
    r = max(math.hypot(v.co.x, v.co.y) for v in rim.data.vertices)
    # 0) inset into the focal plane: R21 put it at 0.6 x the target distance -> DOF CoC ~6 px at f124, so any thin line
    #    (the hair-line!) smeared to a 7 px plate. Push it back along the view ray + scale up (same screen size).
    rig = bpy.data.objects.get("MagnifierR21")
    k = 1.0
    if rig is not None and MAG_DEPTH:
        cam = sc.camera
        sc.frame_set(sc.frame_end)
        fd = cam.data.dof.focus_distance
        sc.frame_set(1)
        d = -rig.location.z
        k = max(1.0, MAG_DEPTH * fd / d)
        rig.location = rig.location * k
        rig.scale = (k, k, k)
        kl0 = bpy.data.objects.get("MagKeyR21")
        if kl0 is not None:
            kl0.data.size *= 1.0                   # object scale already scales the area
    # geometry as built in misc_b612_r21 (block-local units)
    W, D = r * 1.25, r * 0.5
    y_pf, y_mem = r * 0.30, -r * 0.46
    fz = D / 2 + r * 0.01                          # front plane (toward the camera)
    hair = r * 0.0045                              # ~0.9 px core at 960x540 (r ~ 103 px); DOF softens it to ~2 px
    # 1) membrane = hair-line along the front edge, no depth face
    mb = K.MB()
    mb.tube(Vector((-W / 2 + r * 0.15, y_mem, fz)), Vector((W / 2 - r * 0.02, y_mem, fz)), hair, seg=8)
    _swap_mesh(mem, mb, K.emit_mat("MagHairR28", (0.92, 0.94, 0.98), 5.0))
    # 2) frame bar = a lit solid block (grey anodised), carrying the hair-line
    fb = bpy.data.objects.get("MagFrameBarR21")
    if fb is not None:
        fb.data.materials[0] = K.mat("MagFrameR28M", (0.42, 0.43, 0.47), metal=0.2, rough=0.5,
                                     emit=(0.42, 0.43, 0.47), strength=0.5)
    # 3) mask = one thick DARK block: dark substrate + dark blue multilayer, black absorber teeth
    for nm, col, em in (("MagSubstrateR21", (0.012, 0.013, 0.018), 0.0), ("MagMultilayerR21", (0.06, 0.08, 0.22), 0.6)):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.data.materials[0] = K.mat(nm + "R28M", col, metal=0.0, rough=0.95 if em == 0 else 0.6, emit=col,
                                        strength=em, spec=0.05 if em == 0 else 0.5)
            print(f"[R28 B6_12] {nm} mats {[m.name for m in o.data.materials]} polys {len(o.data.polygons)}", flush=True)
    kl = bpy.data.objects.get("MagKeyR21")           # R21 key washed the inset to light grey (R27 「白板」)
    if kl is not None:
        kl.data.energy = MAG_KEY * k * k
    ab = bpy.data.objects.get("MagAbsorberR21")
    if ab is not None:
        ab.data.materials[0] = K.mat("MagAbsR28M", (0.012, 0.012, 0.015), rough=0.7)
    # 4) gap rule broken + double zig-zag break line across the section (gap not to scale)
    gr = bpy.data.objects.get("MagGapRuleR21")
    if gr is not None:
        gx = r * 0.44
        ym = (y_pf + y_mem) / 2 - r * 0.03
        sp = r * 0.05                               # spacing of the two break lines
        y_top, y_bot = y_pf - r * 0.06, y_mem + hair
        rule = K.MB()
        rule.tube(Vector((gx, y_bot, fz)), Vector((gx, ym - sp, fz)), r * 0.012, seg=10)
        rule.tube(Vector((gx, ym + sp, fz)), Vector((gx, y_top, fz)), r * 0.012, seg=10)
        for yy in (y_bot, y_top):
            rule.tube(Vector((gx - r * 0.06, yy, fz)), Vector((gx + r * 0.06, yy, fz)), r * 0.01, seg=8)
        _swap_mesh(gr, rule, gr.data.materials[0])
        brk = K.MB()
        band = K.MB()
        xb, wb = -W / 2 + r * 0.09, r * 0.18          # frame bar (misc_b612_r21)
        z = r * 0.03
        for dy in (-sp / 2, sp / 2):                  # two parallel slanted strokes across the rule (cyan, like the rule)
            brk.tube(Vector((gx - r * 0.07, ym + dy - z, fz + r * 0.006)), Vector((gx + r * 0.07, ym + dy + z, fz + r * 0.006)),
                     r * 0.008, seg=6)
        band.box((xb, ym, fz - r * 0.002), (wb + r * 0.05, sp * 1.6, r * 0.004))   # the bar is cut between the marks
        blk = gr.parent
        made = []
        for m_, nm, mat in ((brk, "MagBreakR28", gr.data.materials[0]),
                            (band, "MagBreakBandR28", K.mat("MagBreakBandR28M", (0.035, 0.038, 0.045), rough=0.8,
                                                             emit=(0.035, 0.038, 0.045), strength=0.6))):
            o = m_.obj(nm, mat)
            o.parent = blk
            made.append(o)
        # same visibility keys as the magnifier (appears with it)
        n = sc.frame_end
        f_on = round(n * 0.58)
        for o in made:
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=1)
            o.keyframe_insert("hide_render", frame=f_on - 1)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f_on)
            try:
                rc = bpy.data.collections.get("MagReceiversR21")
                if rc is not None:
                    rc.objects.link(o)
            except Exception:
                pass
    # 5) crisp hair-line + break strokes are drawn by mograph/r2_ov_zz28m.py (the inset sits ~6 px out of focus at
    #    f124, so a 3D hair-line smears to a 7 px plate): hide the 3D hair-line + strokes, export their anchors
    for nm in ("MagMembraneR21", "MagBreakR28"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.animation_data_clear()
            o.hide_render = True
    blk = mem.parent
    ym = (y_pf + y_mem) / 2 - r * 0.03
    _extra_anchors(sc, "B6_12", blk, {"mag_hair_l": (-W / 2 + r * 0.09, y_mem, fz), "mag_hair_r": (W / 2 + r * 0.02, y_mem, fz),
                                      "mag_brk_c": (r * 0.44, ym, fz), "mag_brk_x": (r * 0.44 + r * 0.1, ym, fz),
                                      "mag_brk_y": (r * 0.44, ym + r * 0.1, fz)})
    print(f"[R28 B6_12] FILM_R28: inset depth x{k:.2f}, r={r:.4f} hair d={2 * hair / r * 102.6:.2f} px, break lines + dark mask block", flush=True)


def _extra_anchors(sc, shot, parent, pts):
    """Merge extra anchor keys into kit_r2.anchors' per-frame json (runs after its handler; never drops its keys)."""
    import json
    import os
    import common as C0
    out = os.path.join(C0.render_root(), "shots", shot, "anchors")
    emp = {}
    for k, v in pts.items():
        e = bpy.data.objects.new("Anchor28_" + k, None)
        sc.collection.objects.link(e)
        e.parent = parent
        e.location = v
        emp[k] = e
    from bpy_extras.object_utils import world_to_camera_view

    def h(sc_, *_):
        cam = sc_.camera
        if cam is None:
            return
        fp = os.path.join(out, f"{sc_.frame_current:04d}.json")
        try:
            with open(fp) as fh:
                res = json.load(fh)
        except Exception:
            res = {}
        for k, e in emp.items():
            v = world_to_camera_view(sc_, cam, e.matrix_world.translation)
            res[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fp, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)


# ------------------------------------------------------------------------------------------------ B6_12 FACE
PITCH = 0.018          # absorber line pitch (scene units, mask 1.44 wide ~ 80 lines per die width)
DUTY = 0.45
GLINT_W, GLINT_L, GLINT_E = 0.05, 4.0, 380.0
MIRROR_COL = (0.30, 0.34, 0.48)   # glossy tint (sRGB) -> linear ~0.07-0.2: dark blue mirror


def _face_mat():
    m = bpy.data.materials.new("MaskFaceR28")
    m.use_nodes = True
    nt = m.node_tree
    nn, l = nt.nodes, nt.links
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    tc = nn.new("ShaderNodeTexCoord")
    sep = nn.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    X, Y = sep.outputs["X"], sep.outputs["Y"]
    # dies 3 x 2 over [-0.72, 0.72]: die index + local position, scribe lanes bare
    dw, dh = 1.44 / 3, 1.44 / 2
    ux = _op(nt, "DIVIDE", _op(nt, "ADD", X, 0.72), dw)
    uy = _op(nt, "DIVIDE", _op(nt, "ADD", Y, 0.72), dh)
    fx, fy = _op(nt, "FRACT", ux), _op(nt, "FRACT", uy)
    lane = _op(nt, "MAXIMUM",
               _op(nt, "MAXIMUM", _op(nt, "LESS_THAN", fx, 0.05), _op(nt, "GREATER_THAN", fx, 0.95)),
               _op(nt, "MAXIMUM", _op(nt, "LESS_THAN", fy, 0.04), _op(nt, "GREATER_THAN", fy, 0.96)))
    # blocks: 4 x 4 per die, each block picks horizontal lines / vertical lines / pads / bare (white noise per block)
    bx = _op(nt, "FLOOR", _op(nt, "MULTIPLY", ux, 4.0))
    by = _op(nt, "FLOOR", _op(nt, "MULTIPLY", uy, 4.0))
    cmb = nn.new("ShaderNodeCombineXYZ")
    l.new(bx, cmb.inputs["X"])
    l.new(by, cmb.inputs["Y"])
    wn = nn.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    l.new(cmb.outputs[0], wn.inputs["Vector"])
    sel = wn.outputs["Value"]
    # block margin (bare mirror between blocks)
    gx_ = _op(nt, "FRACT", _op(nt, "MULTIPLY", ux, 4.0))
    gy_ = _op(nt, "FRACT", _op(nt, "MULTIPLY", uy, 4.0))
    marg = _op(nt, "MAXIMUM",
               _op(nt, "MAXIMUM", _op(nt, "LESS_THAN", gx_, 0.08), _op(nt, "GREATER_THAN", gx_, 0.92)),
               _op(nt, "MAXIMUM", _op(nt, "LESS_THAN", gy_, 0.08), _op(nt, "GREATER_THAN", gy_, 0.92)))
    lv = _op(nt, "LESS_THAN", _op(nt, "FRACT", _op(nt, "DIVIDE", X, PITCH)), DUTY)
    lh = _op(nt, "LESS_THAN", _op(nt, "FRACT", _op(nt, "DIVIDE", Y, PITCH)), DUTY)
    pad = _op(nt, "MULTIPLY", _op(nt, "LESS_THAN", _op(nt, "FRACT", _op(nt, "DIVIDE", X, PITCH * 2.5)), 0.6),
              _op(nt, "LESS_THAN", _op(nt, "FRACT", _op(nt, "DIVIDE", Y, PITCH * 2.5)), 0.6))
    s_v = _op(nt, "LESS_THAN", sel, 0.42)
    s_h = _op(nt, "MULTIPLY", _op(nt, "GREATER_THAN", sel, 0.42), _op(nt, "LESS_THAN", sel, 0.80))
    s_p = _op(nt, "MULTIPLY", _op(nt, "GREATER_THAN", sel, 0.80), _op(nt, "LESS_THAN", sel, 0.92))
    absb = _op(nt, "ADD", _op(nt, "ADD", _op(nt, "MULTIPLY", s_v, lv), _op(nt, "MULTIPLY", s_h, lh)),
               _op(nt, "MULTIPLY", s_p, pad))
    keep = _op(nt, "SUBTRACT", 1.0, _op(nt, "MAXIMUM", lane, marg))
    A = _op(nt, "MINIMUM", _op(nt, "MULTIPLY", absb, keep), 1.0)          # 1 = absorber, 0 = multilayer mirror
    # no Principled: at this grazing view its metallic Fresnel goes to white and the face mirrored the grey studio floor
    # (= light-grey sheet with white stripes). Constant-colour glossy = a DARK mirror that still shows bright things
    # (the glint strip) clearly; absorber = black matte.
    out = next(x for x in nn if x.type == "OUTPUT_MATERIAL")
    nn.remove(b)
    gl = nn.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (*_lin(MIRROR_COL), 1)
    gl.inputs["Roughness"].default_value = 0.05
    df = nn.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (*_lin((0.10, 0.12, 0.20)), 1)
    ml = nn.new("ShaderNodeMixShader")                 # multilayer: dark blue mirror + a little blue body colour
    ml.inputs["Fac"].default_value = 0.08
    nt.links.new(gl.outputs[0], ml.inputs[1])
    nt.links.new(df.outputs[0], ml.inputs[2])
    ad = nn.new("ShaderNodeBsdfDiffuse")
    ad.inputs["Color"].default_value = (*_lin((0.02, 0.02, 0.022)), 1)
    ag = nn.new("ShaderNodeBsdfGlossy")
    ag.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1)
    ag.inputs["Roughness"].default_value = 0.5
    am = nn.new("ShaderNodeAddShader")
    nt.links.new(ad.outputs[0], am.inputs[0])
    nt.links.new(ag.outputs[0], am.inputs[1])
    fm = nn.new("ShaderNodeMixShader")
    nt.links.new(A, fm.inputs["Fac"])
    nt.links.new(ml.outputs[0], fm.inputs[1])
    nt.links.new(am.outputs[0], fm.inputs[2])
    bp = nn.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.3
    bp.inputs["Distance"].default_value = 0.001
    nt.links.new(A, bp.inputs["Height"])
    for x in (gl, ad):
        nt.links.new(bp.outputs["Normal"], x.inputs["Normal"])
    nt.links.new(fm.outputs[0], out.inputs["Surface"])
    return m


def _b612_face(sc):
    mt = bpy.data.objects.get("MaskTop")
    if mt is None:
        print("[R28 B6_12] FACE_R28: MaskTop missing", flush=True)
        return
    mt.data.materials.clear()
    mt.data.materials.append(_face_mat())
    # grazing highlight: strip light linked to MaskTop only, mirror-solved per frame
    mw = mt.matrix_world
    vs = [mw @ v.co for v in mt.data.vertices]
    ctr = sum(vs, Vector()) / len(vs)
    nrm = (mw.to_3x3() @ Vector((0, 0, 1))).normalized()
    cam = sc.camera
    if (cam.matrix_world.translation - ctr).dot(nrm) < 0:
        nrm = -nrm                                   # face normal toward the camera (pattern face down)
    zmin = min(v.z for v in vs) if nrm.z < 0 else max(v.z for v in vs)
    ld = bpy.data.lights.new("MaskGlintR28", "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y, ld.energy = GLINT_W, GLINT_L, GLINT_E
    ld.color = (0.85, 0.9, 1.0)
    lo = bpy.data.objects.new("MaskGlintR28", ld)
    sc.collection.objects.link(lo)
    lo.visible_camera = False
    try:
        rc = bpy.data.collections.new("MaskGlintRecvR28")
        rc.objects.link(mt)
        lo.light_linking.receiver_collection = rc
    except Exception as e:
        print("[R28 B6_12] glint light link failed", e, flush=True)
    n = sc.frame_end
    ax = Vector((1, 0, 0))
    ay = nrm.cross(ax).normalized()
    step = max(1, n // 30)
    for f in list(range(1, n + 1, step)) + [n]:
        u = (f - 1) / max(1, n - 1)
        sc.frame_set(f)
        C = cam.matrix_world.translation.copy()
        X = Vector((ctr.x + 0.30 - 0.45 * u, ctr.y - 0.15, zmin))       # reflection point drifts across the face
        d = (X - C).normalized()
        rr = d - 2 * d.dot(nrm) * nrm
        lo.location = X + rr * 2.4
        z = rr.normalized()                         # area light emits along local -Z -> +Z points away from X
        acr = nrm.cross(rr).normalized()
        y = (acr - acr.dot(z) * z).normalized()
        x = y.cross(z)
        lo.rotation_euler = (Matrix((x, y, z)).transposed().to_quaternion()
                             @ Quaternion((0, 0, 1), math.radians(20))).to_euler()
        lo.keyframe_insert("location", frame=f)
        lo.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(1)
    print(f"[R28 B6_12] FACE_R28: MaskTop ctr {tuple(round(c, 3) for c in ctr)} nrm {tuple(round(c, 2) for c in nrm)}; "
          f"multilayer mirror + absorber line arrays, glint {GLINT_W}x{GLINT_L} {GLINT_E} W", flush=True)


# ------------------------------------------------------------------------------------------------ B6_12 HOSE
def _b612_hose(sc):
    ho = bpy.data.objects.get("GasHosesR20")
    if ho is None:
        print("[R28 B6_12] HOSE_R28: GasHosesR20 missing", flush=True)
        return
    m = bpy.data.materials.new("HoseBraidR28")
    m.use_nodes = True
    nt = m.node_tree
    nn, l = nt.nodes, nt.links
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*_lin((0.50, 0.52, 0.55)), 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.38
    tc = nn.new("ShaderNodeTexCoord")
    h = None
    for rot in (math.radians(35), math.radians(-35)):
        mp = nn.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (rot, rot * 0.5, rot)
        l.new(tc.outputs["Object"], mp.inputs["Vector"])
        wv = nn.new("ShaderNodeTexWave")
        wv.inputs["Scale"].default_value = 160.0
        wv.inputs["Distortion"].default_value = 0.0
        l.new(mp.outputs["Vector"], wv.inputs["Vector"])
        h = wv.outputs["Fac"] if h is None else _op(nt, "MULTIPLY", h, wv.outputs["Fac"])
    bp = nn.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.45
    l.new(h, bp.inputs["Height"])
    l.new(bp.outputs["Normal"], b.inputs["Normal"])
    cr = nn.new("ShaderNodeMapRange")                # braid grooves slightly darker
    cr.inputs["To Min"].default_value = 0.55
    cr.inputs["To Max"].default_value = 0.30
    l.new(h, cr.inputs["Value"])
    l.new(cr.outputs["Result"], b.inputs["Roughness"])
    ho.data.materials.clear()
    ho.data.materials.append(m)
    print("[R28 B6_12] HOSE_R28: GasHosesR20 -> stainless braided", flush=True)


# ------------------------------------------------------------------------------------------------ A2_03
NA_STRENGTH, NA_ALPHA, NA_GAIN, NA_EDGE, NA_CORE = 3.0, 0.42, 1.6, 1.8, 0.14
NA_COL = (0.50, 0.30, 1.0)


def _a203_violet(sc):
    import beam_r26 as B26
    import kit_r2 as K
    cone = bpy.data.objects.get("NAConeR27")
    ink = bpy.data.objects.get("NAThetaR27")
    if cone is None:
        print("[R28 A2_03] NAVIOLET_R28: NAConeR27 missing (NA_R27 off?)", flush=True)
        return
    # 1) violet shell (same soft-shell profile family, brighter + more violet)
    old = cone.data.materials[0]
    cone.data.materials[0] = B26.shell_mat("NAConeR28M", NA_COL, NA_STRENGTH, NA_ALPHA, NA_EDGE, NA_CORE, NA_GAIN,
                                           narrow_at_end=True)
    print(f"[R28 A2_03] cone mat {old.name if old else None} -> NAConeR28M", flush=True)
    # 2) ink: drop the two cyan cone-edge lines (keep theta arc + dashed axis). Rebuild from the R27 recipe in cone space.
    if ink is not None:
        me = ink.data
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        # cone local frame: apex origin, +Z axis; edge lines are long straight tubes leaving the apex off-axis.
        # islands = linked groups; an island is an edge line if it touches the apex (|v| small) and is off-axis.
        islands = []
        seen = set()
        for v in bm.verts:
            if v.index in seen:
                continue
            stack, isl = [v], []
            seen.add(v.index)
            while stack:
                a = stack.pop()
                isl.append(a)
                for e in a.link_edges:
                    o = e.other_vert(a)
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
            islands.append(isl)
        kill = []
        for isl in islands:
            ps = [ink.matrix_world @ x.co for x in isl]
            ls = [cone.matrix_world.inverted() @ p for p in ps]
            near = min(p.length for p in ls)
            far = max(ls, key=lambda p: p.length)
            off = math.hypot(far.x, far.y) / max(1e-6, far.z)
            if near < 0.02 and off > 0.08 and far.length > 0.3:
                kill += isl
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(me)
        bm.free()
        print(f"[R28 A2_03] ink islands {len(islands)}, removed {len(kill)} edge-line verts", flush=True)
    # 3) violet landing spot on the wafer at the apex (appears with the cone)
    import misc_beam_r17 as BR17
    apex = cone.matrix_world.translation.copy()
    sp = BR17.landing("NALandR28", apex + Vector((0, 0, 0.001)), Vector((0, 0, 1)), 0.07, color=(0.78, 0.66, 1.0),
                      strength=3.0, lift=0.001)
    sp.visible_glossy = False
    n = sc.frame_end
    f_on = round(n * 0.48)
    sp.hide_render = True
    sp.keyframe_insert("hide_render", frame=1)
    sp.keyframe_insert("hide_render", frame=f_on - 1)
    sp.hide_render = False
    sp.keyframe_insert("hide_render", frame=f_on)
    # diagnostics: what else is near the cone (R27 frames show a teal fill)
    for o in bpy.data.objects:
        if o.type != "MESH" or o in (cone, ink):
            continue
        p = cone.matrix_world.inverted() @ o.matrix_world.translation
        if abs(p.x) < 0.4 and abs(p.y) < 0.4 and -0.05 < p.z < 2.5 and o.data.materials and o.data.materials[0]:
            print(f"[R28 A2_03] near cone: {o.name} mat {o.data.materials[0].name} hide {o.hide_render}", flush=True)
    print(f"[R28 A2_03] NAVIOLET_R28: shell {NA_COL} s{NA_STRENGTH} a{NA_ALPHA}, landing at {tuple(round(c, 3) for c in apex)}",
          flush=True)
