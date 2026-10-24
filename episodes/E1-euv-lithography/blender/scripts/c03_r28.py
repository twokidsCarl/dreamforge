"""Round 28 C_03 scene-level restructure (R28_ROOT_CAUSE row 3; MAIN process, wired via r2_cutaway.R28_C03).

R27 review p2 C_03: 「55% 帧的紫光是等宽的『霓虹灯管』折线，每个拐点处看不到镜面落点，有『光在空中拐弯』的风险…85% 帧掩模上的
落点画成白色弧形高光，像一根弯管，不像反射…掩模落点改成一条狭缝形照明区（弧形照明场），删掉白色弯管高光」; p2 #5 「C_03 机柜…
同一种格子铺满」. R24..R27 kept the R24 tour path IF -> FFM -> PFM -> G1 -> G2 -> MASK = four ADJACENT open turns in a side-on
cutaway (R26 sketch: two consecutive turn mirrors can never both face a side-on camera). Same structural answer as the
approved A0_10 (a010_r26): fewer open turns.

  HOUSE_R28  the illuminator module (x -4.25..0.45, z 1.55..3.15) is closed by a FRONT wall at y = Y0 dressed with
             kit_r27 named parts (left / right of the window) and a roof; one FRONT WINDOW frames the field-facet landing
             only; the IF -> FFM leg enters through a port in the left wall (seen landing on the FFM through the window);
             FFM -> PFM -> G1 -> G2 legs (+ spots, bounce / landing lights) are deleted - they are inside the box;
             a roof exit port on the G2 -> mask line; the ONE open leg = port -> MASK (pattern face down, f343 look-up)
             -> PO; beams = beam_r26 soft shells (collector -> IF converging, IF -> port, port -> mask, mask -> PO).
  SLIT_R28   the mask landing = a violet ARC-SHAPED slit (ring sector across the plane of incidence) on the pattern face;
             the R19 white band (MaskBandR19 / MaskBandGlowR19) is deleted.

Remove C_03 from r2_cutaway.R28_C03 -> exact R27 pixels; a switch False -> that row off.
"""
import math
import os

import bpy
from mathutils import Vector

HOUSE_R28 = True
SLIT_R28 = True

_E = os.environ
JOB = (101, 222, 343)
X0, X1 = -4.25, 0.45              # illuminator module x range
Y0, Y1 = -0.98, 0.95              # front wall (camera side) / back
Z0, Z1 = 1.55, 3.15
WIN = ((-3.55, -2.35), (2.2, 3.0))   # window around the field-facet landing (x, z)
G2E = Vector((-0.2, 0.3, 2.3))       # R24 tour G2 stop (TourPathR24Spot5)
PATH_DEL = ("TourPathR24Leg1", "TourPathR24Leg2", "TourPathR24Leg3", "TourPathR24Leg4", "TourPathR24Leg5",
            "TourPathR24Spot2", "TourPathR24Spot3", "TourPathR24Spot4", "TourPathR24Spot5", "TourPathR24Leg0",
            "TourPathR24Leg6", "TourPathR24Spot6", "TourLegLand1Lt", "TourLegLand2Lt", "TourLegLandG2Lt",
            "Bounce1", "Bounce2", "Bounce3")


def _mats():
    import kit_r2 as K
    return dict(
        shell=K.mat("C03R28Shell", (0.80, 0.81, 0.83), metal=0.6, rough=0.3, brushed=0.08),
        dark=K.mat("C03R28Dark", (0.05, 0.055, 0.065), metal=0.4, rough=0.45),
        flange=K.mat("C03R28Flange", (0.62, 0.63, 0.66), metal=1.0, rough=0.2),
        bolt=K.mat("C03R28Bolt", (0.55, 0.56, 0.6), metal=1.0, rough=0.25),
        glass=K.mat("C03R28Glass", (0.9, 0.93, 1.0), metal=0.0, rough=0.02),
    )


def _rot_to(d):
    return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler()


def _port_exit():
    """roof exit port: where the G2 -> mask line crosses the roof plane z = Z1."""
    import build_cutaway_r2 as B
    d = (B.MASK - G2E)
    return G2E + d * ((Z1 - G2E.z) / d.z)


def _housing(M, entry, exitp):
    import kit_r2 as K
    sh, dk, fl, bo, gl = K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    t = 0.06
    (wx0, wx1), (wz0, wz1) = WIN
    cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
    sx, sz = X1 - X0, Z1 - Z0
    # front wall around the window, roof (with the exit-port hole region left solid around it), left / right walls
    for cc, ss in ((((X0 + wx0) / 2, Y0 + t / 2, cz), (wx0 - X0, t, sz)),
                   (((wx1 + X1) / 2, Y0 + t / 2, cz), (X1 - wx1, t, sz)),
                   (((wx0 + wx1) / 2, Y0 + t / 2, (Z0 + wz0) / 2), (wx1 - wx0, t, wz0 - Z0)),
                   (((wx0 + wx1) / 2, Y0 + t / 2, (wz1 + Z1) / 2), (wx1 - wx0, t, Z1 - wz1)),
                   ((X0 + t / 2, (Y0 + Y1) / 2, cz), (t, Y1 - Y0, sz)),
                   ((X1 - t / 2, (Y0 + Y1) / 2, cz), (t, Y1 - Y0, sz))):
        sh.box(cc, ss)
    # roof in two parts leaving a square hole round the exit port
    hx0, hx1 = exitp.x - 0.16, exitp.x + 0.16
    for cc, ss in ((((X0 + hx0) / 2, (Y0 + Y1) / 2, Z1 - t / 2), (hx0 - X0, Y1 - Y0, t)),
                   (((hx1 + X1) / 2, (Y0 + Y1) / 2, Z1 - t / 2), (X1 - hx1, Y1 - Y0, t)),
                   ((exitp.x, (Y0 + exitp.y - 0.16) / 2, Z1 - t / 2), (hx1 - hx0, exitp.y - 0.16 - Y0, t)),
                   ((exitp.x, (Y1 + exitp.y + 0.16) / 2, Z1 - t / 2), (hx1 - hx0, Y1 - exitp.y - 0.16, t))):
        sh.box(cc, ss)
    # machined window bezel + bolts, dark lining behind the wall so the window reads as a lit cavity
    wc = Vector(((wx0 + wx1) / 2, Y0 - 0.01, (wz0 + wz1) / 2))
    for cc, ss in (((wc.x, wc.y, wz0 - 0.04), (wx1 - wx0 + 0.16, 0.05, 0.08)),
                   ((wc.x, wc.y, wz1 + 0.04), (wx1 - wx0 + 0.16, 0.05, 0.08)),
                   ((wx0 - 0.04, wc.y, wc.z), (0.08, 0.05, wz1 - wz0)), ((wx1 + 0.04, wc.y, wc.z), (0.08, 0.05, wz1 - wz0))):
        fl.box(cc, ss)
    for k in range(10):
        bo.cyl((wx0 - 0.04 + (wx1 - wx0 + 0.08) * (k % 5) / 4, Y0 - 0.04, wz0 - 0.04 if k < 5 else wz1 + 0.04), 0.012,
               0.02, rot=(math.pi / 2, 0, 0), seg=10)
    gl.box((wc.x, Y0 + 0.02, wc.z), (wx1 - wx0, 0.004, wz1 - wz0))
    # plinth + service rail + port flanges
    dk.box((cx, (Y0 + Y1) / 2, Z0 - 0.05), (sx + 0.1, Y1 - Y0 + 0.1, 0.1))
    fl.box((cx, (Y0 + Y1) / 2, Z1 + 0.025), (sx + 0.05, 0.08, 0.05))
    for p, d in ((entry, Vector((1, 0, 0))), (exitp, Vector((0, 0, 1)))):
        e = _rot_to(d)
        fl.ring(p, 0.2, 0.1, 0.05, rot=e, seg=48)
        fl.cyl(p - d * 0.06, 0.17, 0.1, rot=e, seg=40)
        bo.bolts(p + d * 0.03, 0.155, 8, 0.012, 0.02, rot=e)
    obs = [sh.obj("C03R28Housing", M["shell"], bevel=0.015), dk.obj("C03R28Dark", M["dark"]),
           fl.obj("C03R28Flange", M["flange"], bevel=0.004), bo.obj("C03R28Bolts", M["bolt"])]
    g = gl.obj("C03R28Window", M["glass"])
    g.visible_shadow = False
    try:
        bsdf = next(n for n in g.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        bsdf.inputs["Alpha"].default_value = 0.12
    except (StopIteration, KeyError):
        pass
    obs.append(g)
    return obs


def _dress(M):
    """kit_r27 named parts on the front wall, left and right of the window (few / big / different)."""
    import hero_kit_r10 as H
    import kit_r27 as KT
    P = H.new_parts()
    (wx0, wx1), _ = WIN
    log = []
    KT.named_row(P, X0 + 0.08, wx0 - 0.14, Z0 + 0.1, Z1 - 0.1, Y0, kinds=("power_supply", "valve_island"), seed=28,
                 depth=1.2, log=log)
    KT.named_row(P, wx1 + 0.14, X1 - 0.1, Z0 + 0.1, Z1 - 0.12, Y0,
                 kinds=("ion_pump", "hexapod_mount", "metrology_ring", "turbo_gate", "gas_panel", "card_cage"), seed=29,
                 depth=1.2, log=log)
    KT.finish(P, "C03R28Kit")
    print(f"[c03r28] front-wall kinds {KT.count(log)}: {log}", flush=True)
    return log


def _slit_mat():
    """translucent violet glow (the pattern stays readable through it), soft across the width (UV-free: object-space
    distance from the arc centre line is not available on a flat strip -> use the strip's generated Y coordinate)."""
    import kit_r2 as K
    m = bpy.data.materials.new("C03R28SlitM")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for nd in list(N):
        if nd.type != "OUTPUT_MATERIAL":
            N.remove(nd)
    out = next(nd for nd in N if nd.type == "OUTPUT_MATERIAL")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin((0.62, 0.42, 1.0)), 1)
    em.inputs["Strength"].default_value = float(_E.get("C28_SS", "2.2"))
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = float(_E.get("C28_SA2", "0.55"))
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _arc_slit(mask_pt, d_in):
    """violet ring sector on the pattern face (pattern faces down, z = mask_pt.z - 0.004): arc centre offset against
    the incidence direction so the arc bows across the plane of incidence (x-z), long along y."""
    import bmesh
    import kit_r2 as K
    rc = float(_E.get("C28_RC", "0.5"))
    w = float(_E.get("C28_SW", "0.06"))
    half = math.radians(float(_E.get("C28_SA", "26")))
    ax = Vector((d_in.x, d_in.y, 0)).normalized()
    side = Vector((-ax.y, ax.x, 0))
    c = mask_pt - ax * rc
    z = mask_pt.z - 0.004
    bm = bmesh.new()
    n = 48
    rows = []
    for r in (rc - w / 2, rc + w / 2):
        row = []
        for i in range(n + 1):
            a = -half + 2 * half * i / n
            p = c + ax * (r * math.cos(a)) + side * (r * math.sin(a))
            row.append(bm.verts.new((p.x, p.y, z)))
        rows.append(row)
    for i in range(n):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new("C03R28Slit")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("C03R28Slit", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(_slit_mat())
    ob.visible_shadow = False
    return ob


def post(sc, variant, shot):
    if shot != "C_03" or variant != "tour":
        return sc
    import beam_r26 as BR
    import build_cutaway_r2 as B
    import kit_r2 as K
    exitp = _port_exit()
    d_in = (B.MASK - G2E).normalized()
    d_out = Vector((d_in.x, d_in.y, -d_in.z))
    po_end = B.MASK + d_out * ((B.MASK.z - 2.27) / -d_out.z)
    if HOUSE_R28:
        gone = [nm for nm in PATH_DEL if nm in bpy.data.objects]
        for nm in gone:
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
        for ob in list(bpy.data.objects):
            if ob.name.startswith(("TourPathR24Leg0In", "TourPathR24Leg1In", "TourPathR24Leg2In", "TourPathR24Leg3In",
                                   "TourPathR24Leg4In", "TourPathR24Leg5In", "TourPathR24Leg6In")):
                bpy.data.objects.remove(ob, do_unlink=True)
        print(f"[c03r28] removed {len(gone)} R24 tour path objects", flush=True)
        M = _mats()
        ax = (B.IF - B.COLL).normalized()
        entry = B.IF + ax * ((X0 - B.IF.x) / ax.x)
        _housing(M, entry, exitp)
        _dress(M)
        S = float(_E.get("C28_S", "7.0"))
        src = Vector((B.COLL.x + 0.68 ** 2 / (4 * 0.42), 0, B.COLL.z))   # collector rim plane (R 0.68, f 0.42): the
        # cone base = the dish mouth (R27 B1_15 lesson: a base in mid-air reads 「光凭空出现」); 0.5 x widen 1.35 = R
        chA = BR.chain("C03R28Src", [(src, None), (B.IF, None), (entry, None)], [0.5, 0.03, 0.09], strength=S,
                       spot_strength=0.0, land_final=False, mirrors=False)
        chI = BR.chain("C03R28In", [(entry, None), (B.FFM, (entry - B.FFM).normalized())], [0.09, 0.05], strength=S,
                       spot_strength=16.0, mirrors=False)
        mobj = bpy.data.objects.get("R8Kit2_mask")
        chB = BR.chain("C03R28Ill", [(exitp + Vector((0, 0, 0.02)), None), (B.MASK, Vector((0, 0, -1))), (po_end, None)],
                       [0.10, 0.035, 0.07], strength=S, spot_strength=0.0, land_final=False, mirrors=False,
                       existing={1: mobj} if mobj is not None else None)
        bad = []
        for tag, ch, frs, ex in (("C_03 src", chA, JOB[:2], (0,)), ("C_03 in", chI, JOB[1:2], ()),
                                 ("C_03 ill", chB, JOB[1:], (0, 2))):
            bad += BR.check(sc, ch, frs, exits=ex, tag=tag) or []
        print(f"BEAMCHECK26 C_03 SUMMARY {'OK' if not bad else 'NOGO ' + str(len(bad))}", flush=True)
    if SLIT_R28:
        for nm in ("MaskBandR19", "MaskBandGlowR19"):
            if nm in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
        _arc_slit(B.MASK, d_in)
    from bpy_extras.object_utils import world_to_camera_view as w2c
    for f in JOB:
        sc.frame_set(f)
        pr = {}
        for k, p in (("IF", B.IF), ("FFM", B.FFM), ("port", exitp), ("MASK", B.MASK), ("po_end", po_end)):
            v = w2c(sc, sc.camera, p)
            pr[k] = (round(v.x * sc.render.resolution_x), round((1 - v.y) * sc.render.resolution_y))
        print(f"[c03r28] f{f} {pr}", flush=True)
    sc.frame_set(1)
    return sc
