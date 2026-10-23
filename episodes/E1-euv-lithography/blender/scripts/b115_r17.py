"""Round 17 (P1) helper for r2_source variant "contrast" (B1_15) - and the shared solid collector for B2_08 / B1_18.

R17 root cause #1 (B1_15 capped H1 + H2 three rounds running on the same inside-bowl / rim / off-axis camera family):
CHANGE ASSET ROUTE. The collector is the B3_02 collector (r2_cutaway variant "collect", which reviewers read as "a
mirror that looks like a mirror"): build_cutaway_r2._collector is imported READ-ONLY and its geometry (thick shell,
ground substrate back, cooling channels, bolted flange, central hole + laser entry tube, support spokes) is moved so
the B3_02 plasma site (first focus) sits at the r2_source origin; the face uses the same mirror_r15 Mo/Si surface
B3_02 uses (CollectorML_R15 rough 0.035 / CollectorBlankR15 tone 0.3). For B1_15 the dish is HALF-CUT on the camera
side and seen from OUTSIDE at 3/4: the cut-open bowl fills >= 1/3 of the frame, the violet plasma hangs at its first
focus, the plasma's glow is mirrored in the polished face; over 1.5 s the camera pushes in ~9 % and the focus pulls
from the plasma onto the mirror face (H2). No rim highlight / neon flange, no ghost glow volume, one leader on the
face. Not repeating: inside-bowl / rim / off-axis cameras, rim highlights.

R17 root cause #2 (B2_08 collector = translucent violet ghost disc): collector_b302(M, cut=False) gives B2_08 /
B1_18 the same SOLID ellipsoidal mirror (same family as B3_02).
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K
import build_cutaway_r2 as B          # READ-ONLY reuse of the B3_02 collector builder (never modified)
import mirror_r15 as MR

KEYS = ("mirror", "substrate", "copper", "flange", "bolt", "gold", "anod", "mount")
# B3_02 collector constants (build_cutaway_r2._collector): R 0.68, hole 0.12, f 0.42, shell 0.09
B_R, B_HOLE, B_F, B_SHELL = 0.68, 0.12, 0.42, 0.09
OFFSET = -B.PLASMA                     # B3_02 plasma site -> origin; the collector vertex lands at x = -0.9
VERTEX_X = B.COLL.x + OFFSET.x


def face_x(r, shift=0.0):
    """x of the collector face at radius r in r2_source coordinates (plasma at the origin)."""
    return VERTEX_X + shift + r * r / (4 * B_F)


B115_SHIFT = 0.3          # B1_15: dish 0.3 m nearer, so the plasma (first focus) hangs inside the bowl's mouth


def glossy_glow_at(name, cam_pos, face_pt, nrm, dist, radius, strength, S, color=(0.8, 0.68, 1.0)):
    """A reflection-only violet glow placed on the mirrored camera ray of face_pt: the dish shows the plasma's
    light as a soft violet patch there (camera / diffuse never see it)."""
    d = (face_pt - cam_pos).normalized()
    r = d - 2 * d.dot(nrm) * nrm
    c = face_pt + r * dist
    ob = S.single(name, S.vol_glow_soft(name + "M", color, strength, radius, centre=tuple(c)),
                  lambda mb: mb.sphere(tuple(c), radius, 24))
    S.camera_only(ob, glossy=True)
    ob.visible_camera = False
    return ob


def face_normal(y, z):
    return Vector((1, -y / (2 * B_F), -z / (2 * B_F))).normalized()


def collector_mats(M):
    M.setdefault("coll_b302", MR.ml_mirror("CollectorML_R15", rough=0.035))      # = B3_02 collect variant
    M.setdefault("coll_blank", MR.ground_edge("CollectorBlankR15", tone=0.3))
    return {"mirror": M["coll_b302"], "substrate": M["coll_blank"], "copper": M["copper"], "flange": M["alu_dark"],
            "bolt": M["steel"], "gold": M["gold"], "anod": M["anod"], "mount": M["alu"]}


def collector_b302(M, cut=False, name="CollB302", keep=KEYS, shift=0.0):
    """The B3_02 collector at the r2_source plasma origin. cut=True: half-cut, the y < 0 half (camera side) is
    removed and the section through the thick shell is capped with the ground substrate material."""
    mats = collector_mats(M)
    mbs = {k: K.MB() for k in KEYS}
    B._collector(M, mbs)
    objs = []
    for k in KEYS:
        mb = mbs[k]
        if k not in keep or not mb.bm.verts:
            mb.bm.free()
            continue
        if cut:
            # cut-away wedge on the camera side (B3_02 world space): the front-lower quadrant y < 0, z < axis is
            # removed - the bowl stays readable as a bowl, the two section planes show the thick shell
            mb._resolve()
            mb.bm.faces.ensure_lookup_table()
            dead = [f for f in mb.bm.faces
                    if (lambda c: c.y < -1e-4 and c.z < B.COLL.z - 1e-4)(f.calc_center_median())]
            bmesh.ops.delete(mb.bm, geom=dead, context="FACES")
        if cut and k == "substrate":                 # section caps through the shell (face -> back skin)
            for ay, az in ((-1, 0), (0, -1)):       # plane z = axis (y = -r) and plane y = 0 (z = -r)
                prev = None
                for i in range(15):
                    r = B_HOLE + (B_R - B_HOLE) * i / 14
                    x = B.COLL.x + r * r / (4 * B_F)
                    yy, zz = ay * r, B.COLL.z + az * r
                    pair = (mb.bm.verts.new((x - 0.002, yy, zz)), mb.bm.verts.new((x - B_SHELL, yy, zz)))
                    if prev is not None:
                        mb.bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
                    prev = pair
        ob = mb.obj(f"{name}_{k}", mats[k], bevel=0.003 if k in ("flange", "anod") else 0.0)
        ob.location = OFFSET + Vector((shift, 0, 0))
        objs.append(ob)
    return objs


def face_with_sheen(name, haze=0.025, haze_rough=0.3):
    m = MR.ml_mirror(name, rough=0.035)
    nt = m.node_tree
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    h = nt.nodes.new("ShaderNodeBsdfPrincipled")
    h.inputs["Base Color"].default_value = b.inputs["Base Color"].default_value[:]
    h.inputs["Metallic"].default_value = 1.0
    h.inputs["Roughness"].default_value = haze_rough
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = haze
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(h.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- B1_15 scene
def build_contrast(sc, M, cam, tgt, n, S):
    """S = the r2_source module (for plasma_r10 / single / camera_only / vol_glow_soft / _debris_r16 / key_*).
    Returns a post-hook that adds the B1_15 lights after the module's shared relight."""
    import hero_kit_r10 as H
    import common as C
    # a dim cool vessel-grey surround: the polished face mirrors a soft gradient (a mirror of a black void reads
    # as a black hole - R15 / R16)
    C.set_world(top=(0.075, 0.085, 0.12), horizon=(0.04, 0.045, 0.07), bottom=(0.012, 0.014, 0.024))
    S._metals_r15(M, coll_rough=0.035)
    # the polished face: the shared B3_02 Mo/Si surface plus a faint broad polish haze (15 %), so the plasma's own
    # light spreads over the face as a violet sheen around it (R16 used separate glow volumes -> "violet ghost")
    M["coll_b302"] = face_with_sheen("CollectorML_R17s")
    coll = collector_b302(M, cut=True, name="CollB115", shift=B115_SHIFT)
    wn = bpy.context.scene.world.node_tree           # reflections see a brighter cool surround than the camera
    bg = next(nd for nd in wn.nodes if nd.type == "BACKGROUND")
    out = next(nd for nd in wn.nodes if nd.type == "OUTPUT_WORLD")
    ramp = next(nd for nd in wn.nodes if nd.type == "VALTORGB")
    bg2 = wn.nodes.new("ShaderNodeBackground")
    bg2.inputs["Strength"].default_value = 1.2
    wn.links.new(ramp.outputs["Color"], bg2.inputs["Color"])
    lp = wn.nodes.new("ShaderNodeLightPath")
    mx = wn.nodes.new("ShaderNodeMixShader")
    wn.links.new(lp.outputs["Is Glossy Ray"], mx.inputs["Fac"])
    wn.links.new(bg.outputs[0], mx.inputs[1])
    wn.links.new(bg2.outputs[0], mx.inputs[2])
    wn.links.new(mx.outputs[0], out.inputs["Surface"])
    # the droplet generator above the plasma and the catcher below (real chamber parts, no wall: external view)
    P = H.new_parts()
    H.droplet_generator(P, (0, 0, 0.42), (0, 0, -1), s=1.0, flange_at=0.3)
    H.finish(P, M, "B115Kit")
    cat = K.MB()
    cat.tube((0, 0, -1.2), (0, 0, -0.55), 0.06, seg=32)
    cat.tube((0, 0, -0.55), (0, 0, -0.47), 0.06, seg=32, r2=0.11)
    cat.obj("B115Catcher", M["steel"], bevel=0.002)
    # plasma at the first focus (the B3_02 / r2_source plasma site = origin)
    pl, li = S.plasma_r10(M, (0, 0, 0), 0.045, energy=0.0, gas=1.0, li_color=(0.74, 0.6, 1.0), mirror_core=True)
    S.key_energy(li, [(1, 190), (n, 220)])
    li.visible_glossy = True                         # its light spreads over the face through the polish haze
    for ob in pl:
        ob.visible_glossy = False
    # the plasma as the mirror sees it: one compact violet-white glow, visible ONLY in reflections (the camera sees
    # the volumetric core); no separate off-centre glow volume (R16: "upper-left violet ghost")
    for ob in S._debris_r16(M):
        S.key_scale(ob, [(1, 0.6), (n, 1.15)], interp="LINEAR")
    # leader target: the middle of the lit mirror face of the remaining half (upper back quadrant)
    rr, aa = 0.42, math.radians(55)
    face_pt = Vector((face_x(rr, B115_SHIFT), rr * math.cos(aa), rr * math.sin(aa)))
    K.anchors("B1_15", {"coll": face_pt, "plasma": Vector((0, 0, 0))})
    # camera: OUTSIDE the dish, 3/4 from the cut side; 1.5 s push-in ~9 % + focus pull plasma -> mirror face
    cam.data.lens = 32
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.0
    foc = bpy.data.objects.new("FocusR17", None)
    sc.collection.objects.link(foc)
    cam.data.dof.focus_object = foc
    S.key_loc(foc, [(1, (0.0, 0.0, 0.0)), (n, tuple(face_pt))], interp="BEZIER")
    # ~34 deg off the dish axis, seen from beyond the plasma's real image (x ~ -0.11): the ray through the image
    # lands on the remaining half's face, so the dish shows the plasma's glow (a camera outside that cone sees a
    # black mirror - R15)
    look = Vector((-0.24, 0.1, 0.07))
    c0 = Vector((1.3, -1.12, 0.4))
    c1 = look + (c0 - look) * 0.91
    K.key_path(cam, tgt, [(1, tuple(c0), tuple(look)), (n, tuple(c1), tuple(look))], interp="BEZIER")
    def post(sc_):
        # shapeless soft fills (spherical point lights): the polished face shows round soft gradients, the ground
        # section / flange read as solid metal; nothing on the rim
        K.point("B115FillKey", (0.9, -1.4, 1.1), 90.0, (0.95, 0.96, 1.0), 0.6)
        K.point("B115FillBack", (0.5, 1.6, 0.8), 60.0, (0.7, 0.76, 1.0), 0.6)
    return post
