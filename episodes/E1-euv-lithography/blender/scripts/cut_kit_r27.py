"""Round 27 hook (kit sub-agent; shots in r2_cutaway.R27_KIT = A0_10 / B5_01). R27_ROOT_CAUSE row 4 (nameable parts
instead of repeated grids / plain boxes; B5_01 field-facet hero). Runs AFTER the R22..R26 hooks (A0_10: a010_r26 stays
active underneath; B5_01: cut_beam_r26 beam_r26 legs stay). One module-level switch per row:

  KIT_R27   (row 4)  A0_10: the plain R26 illuminator housing gets BIG named parts on its front wall (left column:
                     hexapod / power cabinet / metrology ring stacked; below the window: valve island + ion pump) and a
                     turbo pump + gate valve on its roof (kit_r27.named_row / dress_box, depth x DEPTH so parts stand
                     >= 0.25 m proud). The window (field-facet view) and every light leg stay clear.
                     B5_01: the repeated grid back wall on the left (R8Kit3 / R2_steel at y ~1.2, x -6.6..-4.3) is
                     covered by one kit_r27.named_row (6 kinds, one each).
  FACET_R27 (row 4)  B5_01: field-facet mirror (R8Kit2_facet) scaled x FACET_SCALE about the FFM landing point (beam
                     landing unchanged) so it fills >= 1/4 frame; every facet strip shrunk to STRIP_GAP about its own
                     centre (visible gaps) and given its own dark mount block on its back (camera) side; the landing
                     spot (IllumPathR24Spot1) emission x SPOT_GAIN (highlight halved).
Shot removed from R27_KIT -> exact R26 pixels; a switch False -> that row's R26 pixels.
"""
import bpy
from mathutils import Matrix, Vector

KIT_R27 = True
FACET_R27 = True

DEPTH = 2.0            # A0_10 part protrusion multiplier
FACET_SCALE = 1.3
STRIP_GAP = 0.86
SPOT_GAIN = 0.5


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    if shot == "A0_10" and KIT_R27:
        _a010_kit()
    if shot == "B5_01":
        if FACET_R27:
            _b501_facet()
        if KIT_R27:
            _b501_wall()
    return sc


# ---------------------------------------------------------------------------------------------------------- A0_10
def _a010_kit():
    import a010_r26 as A
    import hero_kit_r10 as HK
    import kit_r27 as K27
    P = HK.new_parts()
    (x0, x1), (y0, y1), (z0, z1) = A.HOUSE
    (wx0, wx1), (wz0, wz1) = A.WINDOW
    yf = y0 - 0.03
    ks = []
    # left column (x0..wx0): three parts stacked, one per row, each ~1.0 x 0.85 m
    lx0, lx1 = x0 + 0.08, wx0 - 0.12
    col = ("power_supply", "hexapod_mount", "metrology_ring")
    zs = [z0 + 0.1 + (z1 - 0.1 - (z0 + 0.1)) * i / 3 for i in range(4)]
    for i, k in enumerate(col):
        ks += K27.named_row(P, lx0, lx1, zs[i] + 0.03, zs[i + 1] - 0.03, yf, kinds=(k,), seed=11 + i, scale=1.3,
                            depth=DEPTH)
    # below the window: valve island + ion pump side by side
    ks += K27.named_row(P, wx0 + 0.02, wx1 - 0.02, z0 + 0.1, wz0 - 0.16, yf, kinds=("valve_island", "ion_pump"),
                        seed=2, scale=1.3, depth=DEPTH)
    # roof: turbo pump + gate valve
    ks += K27.dress_box(P, (x0, y0, z0), (x1, y1, z1), faces=("+z",), seed=3, scale=1.3, depth=DEPTH * 0.8)
    K27.finish(P, "A0R27Kit")
    print(f"[r27k] A0_10 KIT kinds {K27.count(ks)} {ks}", flush=True)


# ---------------------------------------------------------------------------------------------------------- B5_01
def _islands(bm):
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        isl, st = [], [v]
        while st:
            x = st.pop()
            if x.index in seen:
                continue
            seen.add(x.index)
            isl.append(x)
            st += [e.other_vert(x) for e in x.link_edges]
        out.append(isl)
    return out


def _b501_facet():
    import bmesh
    import build_cutaway_r2 as B
    import kit_r2 as K
    ob = bpy.data.objects.get("R8Kit2_facet")
    if ob is None:
        print("[r27k] B5_01 R8Kit2_facet missing", flush=True)
        return
    piv = Vector(B.FFM)
    mw = ob.matrix_world.copy()
    S = Matrix.Translation(piv) @ Matrix.Scale(FACET_SCALE, 4) @ Matrix.Translation(-piv)
    ob.matrix_world = S @ mw
    mw = ob.matrix_world.copy()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    isl = _islands(bm)
    cam = sc_cam_pos()
    mounts = K.MB()
    n_m = 0
    for vs in isl:
        if len(vs) < 4:
            continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        for v in vs:
            v.co = c + (v.co - c) * STRIP_GAP
        # strip extent + normal (world)
        ids = {v.index for v in vs}
        faces = [f for f in bm.faces if f.verts[0].index in ids]
        if not faces:
            continue
        big = max(faces, key=lambda f: f.calc_area())
        nw = (mw.to_3x3() @ big.normal).normalized()
        cw = mw @ c
        if cam is not None and nw.dot(cam - cw) < 0:
            nw = -nw                                     # mount on the camera-visible back side
        far = max(vs, key=lambda v: (v.co - c).length)
        L = (mw.to_3x3() @ (far.co - c)).length * 2
        if L < 0.04:
            continue
        mounts.cyl(tuple(cw + nw * 0.035), max(0.012, min(0.03, L * 0.12)), 0.05,
                   rot=Vector((0, 0, 1)).rotation_difference(nw).to_euler(), seg=12)
        n_m += 1
    bm.to_mesh(ob.data)
    bm.free()
    mat = K.mat("B5R27FacetMount", (0.32, 0.33, 0.36), metal=0.9, rough=0.3)
    if n_m:
        mounts.obj("B5R27FacetMounts", mat)
    # landing highlight halved (own material copy so Spot2 / Spot3 keep R26 strength)
    sp = bpy.data.objects.get("IllumPathR24Spot1")
    n_e = 0
    if sp is not None:
        for i, m in enumerate(sp.data.materials):
            if m is None or not m.use_nodes:
                continue
            m2 = m.copy()
            m2.name = "B5R27Spot1"
            for n in m2.node_tree.nodes:
                if n.type != "EMISSION":
                    continue
                st = n.inputs["Strength"]
                if not st.is_linked:
                    st.default_value *= SPOT_GAIN
                    n_e += 1
                    continue
                src = st.links[0].from_node          # beam_r24._spot_mat: falloff x strength (MATH MULTIPLY)
                if src.type == "MATH" and not src.inputs[1].is_linked:
                    src.inputs[1].default_value *= SPOT_GAIN
                    n_e += 1
            sp.data.materials[i] = m2
    print(f"[r27k] B5_01 FACET scale {FACET_SCALE} about FFM, {len(isl)} strips gap {STRIP_GAP}, {n_m} mounts, "
          f"spot1 {n_e} strengths x{SPOT_GAIN}", flush=True)


def sc_cam_pos():
    sc = bpy.context.scene
    if sc.camera is None:
        return None
    sc.frame_set(64)
    return sc.camera.matrix_world.translation.copy()


def _b501_wall():
    import hero_kit_r10 as HK
    import kit_r27 as K27
    P = HK.new_parts()
    ks = K27.named_row(P, -6.7, -4.3, 2.0, 4.65, 1.12,
                       kinds=("valve_island", "turbo_gate", "power_supply", "gas_panel", "ion_pump", "hexapod_mount"),
                       seed=5, scale=1.2, depth=1.6)
    K27.finish(P, "B5R27Wall")
    print(f"[r27k] B5_01 KIT wall kinds {K27.count(ks)} {ks}", flush=True)
