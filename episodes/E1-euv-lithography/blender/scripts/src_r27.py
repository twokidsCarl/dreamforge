"""Round 27 hook (owned by the 'srcb' sub-agent; shots in r2_source.R27_SRC = B1_15 / B2_08). Remove a shot from
R27_SRC -> exact R26 pixels (B1_15 = src_r26 cone, B2_08 = R23 pixels). Layered AFTER the R22..R26 hooks.
One module-level switch per R27_ROOT_CAUSE row (False -> that row's R26 pixels):

  CONE_R27   (row 2, B1_15): the src_r26 cone B115ExitR26* (starts in mid-air at 0.62 rim->IF, fades in) is deleted
             and rebuilt with beam_r26.chain from the bowl MOUTH (cone base = rim circle R at x = fx(R), no fade-in)
             to the SAME IF (label / anchor unchanged); the post-IF exit leg is cut to S27_EL (0.3, sketch NOGO at 1.2);
             shell edge 1.6 / core 0.06 / alpha 0.5 / strength 9 (fill 0.52, hardness 0.13 = BEAMCHECK26 soft);
             front_dim: the NEAR wall (the only wall between camera and mirror face) x0.06 where face-on, the far
             wall x0.08 where face-on, both full toward the silhouette (rendered rims 143-148 > centre 136-144);
             a soft violet landing-glow annulus on the mirror face at the mouth
             (B115LandR27, r 0.78R..R, brightest at the rim) = where the light leaves the mirror. R24 push + focus pull,
             plasma, laser untouched.
  MIRROR_R27 (row 2b, B2_08): collector face material -> the high-reflectance polished mirror used by B1_15.
  SPOTS_R27  (row 2b, B2_08): tin deposit spots = dark stains ON the face that disappear over the shot
             (per-island removal time, frame-driven front: ~3 % gone f60, ~39 % f133, ~74 % f206 = the 85 % frame).
"""
import math
import os

CONE_R27 = True
MIRROR_R27 = False   # main 32-spp Q4 (R27): the reflection-room panels read as abstract white blobs on a dark disc, not a mirror -> row returned; SPOTS_R27 kept
SPOTS_R27 = True

_E = os.environ
_MOD = [None]


def pre(variant, shot, mod):
    _MOD[0] = mod


def post(sc, variant, shot):
    if shot == "B1_15" and variant == "contrast" and CONE_R27:
        _b115(sc)
    elif shot == "B2_08" and variant == "clean":
        import src_r27_b208 as G
        G.build(sc, _MOD[0], mirror=MIRROR_R27, spots=SPOTS_R27)
    return sc


def _glow_mat(name, color, strength, r_in, r_out, alpha):
    """Emission + transparent mix; radial ramp 0 at r_in -> 1 at r_out (object-space radius from the X axis)."""
    import bpy
    import kit_r2 as K
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tc = N.new("ShaderNodeTexCoord")
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sp.inputs[0])
    def op(o, a, b):
        n = N.new("ShaderNodeMath")
        n.operation = o
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]
    r = op("SQRT", op("ADD", op("MULTIPLY", sp.outputs["Y"], sp.outputs["Y"]),
                      op("MULTIPLY", sp.outputs["Z"], sp.outputs["Z"])), 0.0)
    mr = N.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    L.new(r, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = r_in
    mr.inputs["From Max"].default_value = r_out
    w = op("POWER", mr.outputs["Result"], 1.6)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op("MULTIPLY", w, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op("MULTIPLY", w, alpha), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def front_dim(ob, k, flip=False):
    """Scale the shell's emission + opacity on the camera-facing (near) surface by k, far surface unchanged: through
    the bowl mouth only the near surface lies in front of the mirror face (the far surface projects outside the rim
    ellipse), so the face stays a clean mirror while the cone below the bowl keeps its far wall + silhouettes."""
    for slot in ob.material_slots:
        m = slot.material
        N, L = m.node_tree.nodes, m.node_tree.links
        em = next(n for n in N if n.type == "EMISSION")
        mx = next(n for n in N if n.type == "MIX_SHADER")
        geo = N.new("ShaderNodeNewGeometry")
        bf = geo.outputs["Backfacing"]
        if flip:
            inv = N.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            L.new(bf, inv.inputs[1])
            bf = inv.outputs[0]
        # near surface: k face-on, back to full toward its silhouette (Facing 0.55 -> 0.9) so the cone outline keeps
        # both walls (rim brighter than centre) while the face-on part over the mirror stays clear
        lw = N.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        kfr = N.new("ShaderNodeMapRange")
        kfr.interpolation_type = "SMOOTHSTEP"
        L.new(lw.outputs["Facing"], kfr.inputs["Value"])
        kfr.inputs["From Min"].default_value = float(_E.get("S27_SF0", "0.3"))
        kfr.inputs["From Max"].default_value = float(_E.get("S27_SF1", "0.7"))
        kfr.inputs["To Min"].default_value = k
        kfr.inputs["To Max"].default_value = 1.0
        # far wall: also thinned where face-on (kb), full toward the silhouette -> rim brighter than centre on screen
        kbr = N.new("ShaderNodeMapRange")
        kbr.interpolation_type = "SMOOTHSTEP"
        L.new(lw.outputs["Facing"], kbr.inputs["Value"])
        kbr.inputs["From Min"].default_value = float(_E.get("S27_BF0", "0.15"))
        kbr.inputs["From Max"].default_value = float(_E.get("S27_BF1", "0.55"))
        kbr.inputs["To Min"].default_value = float(_E.get("S27_BACK", "0.08"))
        kbr.inputs["To Max"].default_value = 1.0
        mxn = N.new("ShaderNodeMix")             # backfacing 0 -> near-wall factor, 1 -> far-wall factor
        mxn.data_type = "FLOAT"
        L.new(bf, mxn.inputs["Factor"])
        L.new(kfr.outputs["Result"], mxn.inputs["A"])
        L.new(kbr.outputs["Result"], mxn.inputs["B"])
        fac = mxn
        for sock in (em.inputs["Strength"], mx.inputs["Fac"]):
            src = sock.links[0].from_socket
            mul = N.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            L.new(src, mul.inputs[0])
            L.new(fac.outputs["Result"], mul.inputs[1])
            L.new(mul.outputs[0], sock)


def _land_ring(sc, B, color):
    """Annulus hugging the paraboloid face (x = fx(r)) just inside the mouth, offset along the face normal."""
    import bpy
    import bmesh
    r0, r1 = float(_E.get("S27_LR0", "0.78")) * B.R, B.R * 0.995
    na, nr = 144, 10
    bm = bmesh.new()
    grid = []
    for i in range(nr + 1):
        r = r0 + (r1 - r0) * i / nr
        row = []
        for j in range(na):
            a = 2 * math.pi * j / na
            y, z = r * math.cos(a), r * math.sin(a)
            p = B.face_normal(y, z) * 0.006
            row.append(bm.verts.new((B.fx(r) + p.x, y + p.y, z + p.z)))
        grid.append(row)
    for i in range(nr):
        for j in range(na):
            k = (j + 1) % na
            bm.faces.new((grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j])).smooth = True
    me = bpy.data.meshes.new("B115LandR27")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("B115LandR27", me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(_glow_mat("B115LandR27M", color, float(_E.get("S27_LS", "2.2")), r0, r1,
                                       float(_E.get("S27_LA", "0.55"))))
    ob.visible_glossy = False
    ob.visible_shadow = False
    return ob


def _b115(sc):
    import bpy
    from mathutils import Vector
    import kit_r2 as K
    import b115_r21 as B
    import b115_r22_build as BB
    import beam_r26 as BM
    for ob in list(bpy.data.objects):
        if ob.name.startswith("B115ExitR26") or ob.name.startswith("B115ExitR25"):
            bpy.data.objects.remove(ob, do_unlink=True)
    # same IF as src_r25 / src_r26 (the zz25s label and the R24 anchor point at it)
    xr, xi0 = B.fx(B.R), BB.image_x()
    xi = xr + float(_E.get("S25_IFF", "0.62")) * (xi0 - xr)
    xa = xr + float(_E.get("S27_K", "0.0")) * (xi - xr)       # cone base = the bowl mouth
    ra = B.R * (xi - xa) / (xi - xr)
    ri = float(_E.get("S25_RI", "0.012"))
    xe = xi + (xi - xa) * float(_E.get("S27_EL", "0.3"))       # sketch: 1.2 -> 92-114 % of frame, NOGO
    re = ra * (xe - xi) / (xi - xa)
    edge, core, alpha = (float(_E.get("S27_EDGE", "1.6")), float(_E.get("S27_CORE", "0.06")),
                         float(_E.get("S27_CA", "0.5")))
    ch = BM.chain("B115ExitR27", [((xa, 0, 0), None), ((xi, 0, 0), None), ((xe, 0, 0), None)],
                  [ra, ri, re], color=K.VIOLET, strength=float(_E.get("S27_CS", "9.0")), alpha=alpha, edge=edge,
                  core=core, gain=float(_E.get("S27_GAIN", "1.6")), widen=1.0, land_final=False, mirrors=False)
    for leg in ch["legs"]:
        for ob in leg:
            ob.visible_glossy = False      # mirror-hero: the cone never shows in the face
    kf = float(_E.get("S27_FRONT", "0.06"))
    if kf < 1:
        front_dim(ch["legs"][0][0], kf, flip=_E.get("S27_FLIP") == "1")
    import src_r25 as R25
    fe = float(_E.get("S27_EFADE", "0.0"))
    if fe > 0:
        R25.fade_start(ch["legs"][1][0], fe)
    _land_ring(sc, B, K.VIOLET)
    from bpy_extras.object_utils import world_to_camera_view as w2c

    def px(p):
        v = w2c(sc, sc.camera, Vector(p))
        return round(v.x * 960), round((1 - v.y) * 540)
    for f in (9, 20, 31):
        sc.frame_set(f)
        rim = [px((xr, B.R * math.cos(t), B.R * math.sin(t))) for t in [i * math.pi / 36 for i in range(72)]]
        pl = px(tuple(B.PC))
        print(f"B115PROJ27 f{f} IF {px((xi, 0, 0))} exit-end {px((xe, 0, 0))} plasma {pl} "
              f"rim x {min(p[0] for p in rim)}..{max(p[0] for p in rim)} y {min(p[1] for p in rim)}..{max(p[1] for p in rim)}",
              flush=True)
    BM.check(sc, ch, (9, 20, 31), exits=(2,), tag="B1_15")
    if _E.get("S27_DUMP") == "1":
        for ob in bpy.data.objects:
            if ob.type in ("MESH", "CURVE"):
                print("B115OBJ", ob.name, tuple(round(v, 2) for v in ob.matrix_world.translation),
                      tuple(round(v, 2) for v in ob.dimensions), flush=True)
    sc.frame_set(1)
