"""R22 row 1 (B7_06, projection optics clay turntable).

R21 review: 「入射光是一根等宽、发光的实心圆柱」「M6 反射处是一团泛光」「白模加灰棚，主体和背景接近 3:1」
「都是 clay 白，叫不出名字的件多」(repeated small round mirrors).
  * dark cool backdrop (deep cool-blue world, near-black floor) + ONE cool rim light (grey studio lights removed);
  * incoming = soft cone from ABOVE (mask side, through the roof port) converging onto the M5 ring spot;
    M5 -> M6 diverging, M6 -> through the M5 hole converging to the wafer; k decreasing per segment;
  * M5 / M6 faces = a real high-reflective mirror material, structure stays clay;
  * cut_kit_r17.po_fill (4 repeated small round mirror blanks) -> hexapod strut sets + metrology ring + coolant pipes.
Geometry matches r2_cutaway._po_barrels_r15 (local frame of the 'Turntable' pivot).
"""
import math
import bpy
from mathutils import Vector

Z_BASE, Z_CEIL, Z_TOP = 1.0, 3.3, 4.3
Z6, Z5, ZW = 2.78, 1.64, 1.185
TILT = math.radians(18)


def _po_fill_r22(HP, mb, z_base, z_ceil, H15, HK):
    """Replaces the R17 M1..M4 back-blanks: two hexapod strut sets, a metrology ring with sensor heads, coolant pipes."""
    # hexapod strut sets standing on the mid ring shelf (back left / back right), each carrying a cell plate
    for (x, y), rb, rt in (((-0.56, 0.36), 0.2, 0.15), ((0.58, 0.42), 0.17, 0.13)):
        HK.hexapod(HP, Vector((x, y, 1.9)), Vector((x, y, 2.42)), rb, rt)
        mb["anod"].cyl((x, y, 2.47), rt + 0.04, 0.04, seg=40)
        mb["steel"].cyl((x, y, 1.87), rb + 0.05, 0.03, seg=40)
    # metrology ring (back half) with capacitive / interferometric sensor heads looking at the axis
    mb["steel"].shell((0, 0, 2.2), 0.64, 0.7, 0.045, 25, 155, seg=64)
    for a in (35, 70, 110, 145):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        HP["brushed"].box(d * 0.62 + Vector((0, 0, 2.2)), (0.07, 0.07, 0.08))
        HK._cyl(HP["glass"], d * 0.58 + Vector((0, 0, 2.2)), -d, 0.018, 0.01, seg=16)
    # coolant pipes: a supply / return manifold pair around the back wall + drops to the mirror cells
    for z, key in ((2.06, "hose_b"), (2.12, "hose_w")):
        pts = [Vector((0.8 * math.cos(math.radians(a)), 0.8 * math.sin(math.radians(a)), z)) for a in range(20, 165, 12)]
        HP[key].path(pts, 0.016, seg=12)
    for a in (30, 150):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        HP["hose_b"].path([d * 0.8 + Vector((0, 0, 2.06)), d * 0.74 + Vector((0, 0, 1.9)), d * 0.66 + Vector((0, 0, 1.72))],
                          0.014, seg=10)
        HP["hose_w"].path([d * 0.82 + Vector((0, 0, 2.12)), d * 0.74 + Vector((0, 0, 2.4)), d * 0.62 + Vector((0, 0, 2.62))],
                          0.014, seg=10)


def pre(mod):
    import cut_kit_r17 as CK
    CK.po_fill = _po_fill_r22


def _mirror_mat():
    m = bpy.data.materials.new("M56MirrorR22")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.92, 0.93, 0.96, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.025
    return m


def post(sc):
    import common as C
    import kit_r2 as K
    import beam_r19 as R18          # aliased to beam_r21 for this shot (R21_2B)
    piv = bpy.data.objects.get("Turntable")
    n = sc.frame_end
    # ---- (a) dark cool backdrop + one rim light
    C.set_world(top=(0.006, 0.011, 0.024), horizon=(0.004, 0.007, 0.016), bottom=(0.002, 0.003, 0.006), strength=1.0)
    sc["hdri_strength"] = 0.25      # glossy-only env for the mirrors
    flo = bpy.data.objects.get("Floor")
    if flo is not None:
        flo.data.materials.clear()
        flo.data.materials.append(K.mat("FloorDarkR22", (0.012, 0.014, 0.02), rough=0.6, coat=0.0, spec=0.2))
    for nm in ("Softbox", "RimL", "RimR", "RimCoolR20L", "RimCoolR20R", "Fill", "Top"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            bpy.data.objects.remove(o)
    K.area("RimR22", (-2.2, 3.4, 4.6), (0, 0, 2.3), 1.2, 2600, (0.66, 0.8, 1.0), size_y=3.2)
    # ---- (c) M5 / M6 optical faces = mirror (structure stays clay)
    mf = bpy.data.objects.get("PO15_mface")
    if mf is not None:
        mf.data.materials.clear()
        mf.data.materials.append(_mirror_mat())
    # ---- (b) light path: replace the R21 cones
    for o in [o for o in bpy.data.objects if o.name.startswith(("POConeR20_", "POTopTipR20", "POLandM5", "POLandM6"))]:
        bpy.data.objects.remove(o)
    n5 = Vector((0, -math.sin(TILT), math.cos(TILT)))
    n6 = Vector((0, -math.sin(TILT), -math.cos(TILT)))
    c5, c6 = Vector((0, 0, Z5)), Vector((0, 0, Z6))
    # the path is mirrored to the LEFT half (x -> -x): the incoming cone enters at the upper left, away from the
    # top-right title block, through a new roof port at x = -0.86
    p5 = c5 + Vector((-0.4, 0, 0)) + n5 * 0.004
    p5.z = Z5 - 0.006 * (1 - (0.4 / 0.49) ** 2) + 0.004
    p6 = c6 + Vector((0.38, 0, 0)) + n6 * 0.004
    p6.z = Z6 + 0.006 * (1 - (0.38 / 0.47) ** 2) - 0.004
    foc = Vector((0, 0, ZW + 0.002))
    port = Vector((-0.86, 0.0, Z_CEIL))
    pm = K.MB()
    pm.ring((port.x, 0, Z_CEIL - 0.02), 0.13, 0.1, 0.07, seg=40)
    pm.ring((port.x, 0, Z_CEIL + 0.08), 0.13, 0.1, 0.04, seg=40)
    po = pm.obj("PO22_roofport", bpy.data.materials.get("BrushedAluR11") or K.mat("PortR22", (0.7, 0.71, 0.74), metal=1.0, rough=0.25))
    po.parent = piv
    d_in = (port - p5).normalized()
    src = port + d_in * 1.25                      # above the roof, toward the mask (off frame top)
    objs = []
    for i, (a, b, ra, rb, k, t0, t1, na, nb) in enumerate((
            (src, p5, 0.16, 0.04, 2.4, 0.0, 0.72, None, n5),      # mask side -> M5 ring: slowly converging
            (p5, p6, 0.045, 0.2, 1.7, 0.42, None, n5, n6),       # M5 -> M6: diverging
            (p6, foc, 0.2, 0.004, 1.3, 0.7, None, n6, None))):   # M6 -> through the M5 hole -> wafer
        os_, ms_ = R18.segment(a, b, ra, rb, f"POConeR22_{i}", k=k, na=na, nb=nb, seg=64)
        R18.key_vis(os_, ms_, n, t0, t1, ramp=5)
        objs += os_
    for c_, n_, t0, t1, nm in ((p5, n5, 0.0, 0.72, "POLandM5R22"), (p6, n6, 0.42, None, "POLandM6R22")):
        objs += R18._land_timed(c_, n_, nm, max(1, round(1 + (n - 1) * t0)), 5,
                                f_off=None if t1 is None else round(1 + (n - 1) * t1) + 3)
    for nm, loc in (("Anchor_m5r", p5), ("Anchor_m6r", p6)):   # the overlay's step markers follow the new spots
        e_ = bpy.data.objects.get(nm)
        if e_ is not None:
            e_.location = loc
    R18.take()
    for o in objs:
        o.parent = piv
