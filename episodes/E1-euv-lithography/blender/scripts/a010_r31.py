"""Round 31 A0_10 (R31_ROOT_CAUSE row 1; MAIN process, wired via r2_cutaway.R31_A010; layered after a010_r30 and BEFORE
beam_hook_r29, which converts every leg built here to a beam_r29 volume).

R30 p2: 「『照明系统』引线指向的是一个悬空发光球点，球点向外甩出扇形光；掩模附近也是光团+扇形…光路被切成 4–5 段」
「把所有光团换成实心镜 + 镜座，光只在镜面落点拐弯，IF→照明→掩模→物镜→晶圆连成一条锥形收放的紫光」.
Root cause (sketch31/probe_kit.txt, a010_grid119.txt): the R30 FFM landing spot was 0.78 x 0.36 m (larger than the
0.62 x 0.46 m facet plate) at emission 25.6 -> a white glow covering the mirror = 「悬空发光球点」; the plate was ~37 px
wide; ~60 px of the IF -> FFM leg ran behind the R27 left-column parts (hexapod + metrology ring, y -1.64 .. -0.05).
One switch, PATH_R31:
  * every landing in the shot = a flat spot ON the face at mirror-highlight level (size x SPOT_SIZE, emission x
    SPOT_GAIN); the illuminator chain is rebuilt with small spots (no spot wider than ~0.45 x the leg aperture);
  * field-facet plate 0.90 x 0.66 m (parts_r30.facet_plate, the one B5_01 / C_03 model) + pupil-facet disc x1.35 with
    its support post, both inside the visible bay (grid: x -2.75 .. -1.25, z 3.0 .. 3.9);
  * the two upper left-column R27 parts (hexapod row, metrology-ring row) are scaled x PART_S into the upper-left
    corner above the beam line; the power cabinet stays -> the IF -> FFM leg passes ABOVE the R27 cabinet;
  * the 照明系统 leader points at the plate's top edge, not at a landing.
"""
import bpy
from mathutils import Matrix, Vector

PATH_R31 = True
PEOPLE_R31 = True       # row 1b (material): p2 「白人偶改逆光剪影/灰阶洁净服（BRIEF 约定人物只出逆光剪影）」 -> grey suits

JOB = (54, 119, 184)
FFM_P = Vector((-2.25, 0.42, 3.80))
PFM_P = Vector((-1.55, 0.48, 3.22))
FFM_WH = (0.90, 0.66)
PFM_SCALE = 0.48 * 1.35
SPOT_SIZE = 0.45
SPOT_GAIN = 0.12
PART_S = 0.55
PIVOT = Vector((-3.87, 0.0, 4.25))      # upper-left corner of the left column (x, -, z)
ROWS_Z = (2.50, 4.25)                   # hexapod + metrology rows (power cabinet below 2.5 stays)
COL_X = -2.80
CARD = 2.0                              # reflection card radiance (soft highlight on the facets)


def pre(variant, shot, mod):
    return None


def _spot_scale(ob, size, gain):
    """flat spot: shrink about its centre on its own plane, emission x gain."""
    me = ob.data
    if not me.vertices:
        return
    mw = ob.matrix_world
    c = sum((mw @ v.co for v in me.vertices), Vector()) / len(me.vertices)
    inv = mw.inverted()
    for v in me.vertices:
        w = mw @ v.co
        v.co = inv @ (c + (w - c) * size)
    for s_ in ob.material_slots:
        m = s_.material
        if not (m and m.use_nodes):
            continue
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                lk = n.inputs["Strength"].links
                if lk and lk[0].from_node.type == "MATH":
                    lk[0].from_node.inputs[1].default_value *= gain
                else:
                    n.inputs["Strength"].default_value *= gain


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


def _move_upper_parts():
    """hexapod + metrology ring (left column, z 2.5 .. 4.25) scaled x PART_S about the column's upper-left corner."""
    import bmesh
    n = 0
    for ob in [o for o in bpy.data.objects if o.name.startswith("A0R27Kit") and o.type == "MESH"]:
        mw = ob.matrix_world
        inv = mw.inverted()
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        for isl in _islands(bm):
            ws = [mw @ v.co for v in isl]
            c = sum(ws, Vector()) / len(ws)
            if not (c.x < COL_X and ROWS_Z[0] < c.z < ROWS_Z[1] and c.y < 0.2):
                continue
            for v, w in zip(isl, ws):
                q = Vector((PIVOT.x + (w.x - PIVOT.x) * PART_S, -1.15 + (w.y + 1.15) * PART_S,
                            PIVOT.z + (w.z - PIVOT.z) * PART_S))
                v.co = inv @ q
            n += 1
        bm.to_mesh(ob.data)
        bm.free()
    return n


def _anchor_house(point):
    import json
    import os
    import common as C
    from bpy_extras.object_utils import world_to_camera_view
    out = os.path.join(C.render_root(), "shots", "A0_10", "anchors")

    def h31(sc, *_):
        if sc.camera is None:
            return
        fp = os.path.join(out, f"{sc.frame_current:04d}.json")
        try:
            res = json.load(open(fp))
        except Exception:
            res = {}
        v = world_to_camera_view(sc, sc.camera, point)
        res["r26_house"] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(fp, "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h31)     # after a010_r30's handler -> overwrites r26_house


def _refl_card(name, P, n, cam, dist=1.0, size=0.9, strength=2.5):
    """soft emissive card where the camera ray reflects off the face at P (seen only by glossy rays, never by the
    camera): the facet strips show a nameable soft highlight = mirrors, not a dark grille."""
    import kit_r2 as K
    v = (P - cam).normalized()
    r = (v - 2 * v.dot(n) * n).normalized()
    c = P + r * dist
    me = bpy.data.meshes.new(name)
    h = size / 2
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = c
    ob.rotation_euler = (-r).to_track_quat("Z", "Y").to_euler()
    m = K.mat(name + "M", (1, 1, 1))
    m.use_nodes = True
    N = m.node_tree.nodes
    for x in list(N):
        if x.type != "OUTPUT_MATERIAL":
            N.remove(x)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.92, 0.94, 1.0, 1)
    em.inputs["Strength"].default_value = strength
    m.node_tree.links.new(em.outputs[0], next(x for x in N if x.type == "OUTPUT_MATERIAL").inputs["Surface"])
    me.materials.append(m)
    for attr in ("visible_camera", "visible_diffuse", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(ob, attr, False)
    ob.visible_glossy = True
    return ob


def _grey_people(col=(0.13, 0.135, 0.15)):
    """the two scale figures: white suits -> dark grey (copies of their materials; only Eng* objects)."""
    n = 0
    for ob in [o for o in bpy.data.objects if o.name.startswith("Eng") and o.type == "MESH"]:
        for s_ in ob.material_slots:
            m = s_.material
            if not (m and m.use_nodes):
                continue
            b = next((x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
            if b is None or b.inputs["Base Color"].is_linked:
                continue
            c = b.inputs["Base Color"].default_value
            if min(c[0], c[1], c[2]) < 0.45:          # visor / dark parts stay
                continue
            m2 = m.copy()
            b2 = next(x for x in m2.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
            b2.inputs["Base Color"].default_value = (*col, 1)
            s_.material = m2
            n += 1
    return n


def post(sc, variant, shot):
    if not PATH_R31 or shot != "A0_10":
        return sc
    import a010_r26 as A
    import beam_r26 as BR
    import kit_r2 as K
    import parts_r30 as P
    for nm in [o.name for o in bpy.data.objects if o.name.startswith(("A0R30Ffm", "A0R30Pfm", "A0R30Ill"))]:
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    n_mv = _move_upper_parts()
    import a010_r30 as A30
    # the dark lining's front face behind the left column (bottom edge z 1.43 < a010_r30.Z_MIN, so R30 kept it; it hid
    # the leg once the parts moved) -> cut, the interior back wall shows through
    n_cut = A30._cut_front(["A0R26HouseDark", "A0R26Housing"], z_min=-9.0, box=(-4.05, -2.70, -9.0, 9.0))
    hs = bpy.data.objects.get("A0R26Housing")
    if hs is not None and hs.material_slots:       # front panel kept only behind the power cabinet (below the leg)
        lp = K.MB()
        lp.box((-3.35, -0.75, (A.HOUSE[2][0] + 2.46) / 2), (1.20, 0.02, 2.46 - A.HOUSE[2][0]))
        lp.obj("A0R31LowPanel", hs.material_slots[0].material)
    sc.frame_set(JOB[1])
    cam = sc.camera.matrix_world.translation
    ent, ex = A.ENTRY, A.EXIT
    n_f0 = ((ent - FFM_P).normalized() + (PFM_P - FFM_P).normalized()).normalized()
    n_f = (n_f0 + (cam - FFM_P).normalized() * 0.9).normalized()
    n_p0 = ((FFM_P - PFM_P).normalized() + (ex - PFM_P).normalized()).normalized()
    n_p = (n_p0 + (cam - PFM_P).normalized() * 0.9).normalized()
    P.facet_plate("A0R31Ffm", FFM_P, n_f, *FFM_WH)
    P.pupil_disc("A0R31Pfm", PFM_P, n_p, scale=PFM_SCALE, post=True)
    _refl_card("A0R31FfmCard", FFM_P, n_f, cam, dist=0.9, size=0.6, strength=CARD)
    _refl_card("A0R31PfmCard", PFM_P, n_p, cam, dist=0.8, size=0.8, strength=CARD)
    # FFM support: two posts from the plate's back to the housing floor shelf + a cross bar (visible mount)
    mt = K.MB()
    u = Vector((0, 0, 1)).cross(n_f).normalized()
    back = FFM_P - n_f * 0.09
    for s_ in (-0.3, 0.3):
        top = back + u * s_ * FFM_WH[0]
        mt.tube(top, top - n_f * 0.12 + Vector((0, 0.10, -0.32)), 0.022)
    mt.box(tuple(back - n_f * 0.03), (FFM_WH[0] * 0.8, 0.05, 0.05),
           rot=Matrix((u, n_f.cross(u).normalized(), n_f)).transposed().to_euler())
    mt.obj("A0R31FfmMount", K.mat("A0R31FfmMountM", (0.55, 0.56, 0.6), metal=1.0, rough=0.25))
    ch = BR.chain("A0R31Ill", [(ent, None), (FFM_P, n_f), (PFM_P, n_p), (ex, None)], [0.06, 0.13, 0.045, 0.10],
                  strength=7.0, spot_strength=16.0 * SPOT_GAIN, spot_scale=SPOT_SIZE, land_final=False, mirrors=False)
    # every other landing in the shot: flat, small, mirror-highlight level
    n_sp = 0
    for ob in list(bpy.data.objects):
        if ob.type == "MESH" and ob.data.uv_layers.get("SpotUV") is not None and not ob.name.startswith("A0R31Ill"):
            _spot_scale(ob, SPOT_SIZE, SPOT_GAIN)
            n_sp += 1
    _anchor_house(FFM_P + n_f.cross(u).normalized() * FFM_WH[1] * 0.5)
    n_pp = _grey_people() if PEOPLE_R31 else 0
    bad = BR.check(sc, ch, JOB, tag="A0_10 ill31") or []
    print(f"[a010r31] moved {n_mv} upper left-column part islands; cut {n_cut} lining faces; {n_sp} landing spots flattened; {n_pp} people slots grey; FFM n.cam "
          f"{n_f.dot((cam - FFM_P).normalized()):.2f} PFM n.cam {n_p.dot((cam - PFM_P).normalized()):.2f}; "
          f"BEAMCHECK26 A0_10 R31 {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    sc.frame_set(1)
    return sc
