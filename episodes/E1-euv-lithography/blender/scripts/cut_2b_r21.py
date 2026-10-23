"""Round 21 (P1, R21_ROOT_CAUSE rows 3): post-build hook for cut-beam (B7_06 / A0_10 / C_03 / B8_03 / B8_03M), called from r2_cutaway.build after the
R20 build when the shot is in its R21 set. Owned by that sub-agent.

B8_03 / B8_03M (row 3, R20 review: "入射紫光从右上落在晶圆边缘外…读成『光落在空处』… 入射光改成一个会聚锥，锥尖精确落在狭缝上，
狭缝处加落点辉光"; R20 smoke: "two stray black plates at top of frame"):
  * the black plates = the near post of the bay frame (Bay_sec section-cut caps + Bay_bolt + Bay_rib at x ~ 0,
    y ~ -0.3, z ~ 1.0-1.2, raycast-identified) - its faces in that box are deleted;
  * the last leg (M4 -> slit) gets its converging TIP drawn: one more straight beam_r21 cone over the last 45 % of the
    leg, closing to 6 mm exactly on the slit centre, + a landing glow on the wafer at the slit.
B7_06 / A0_10 / C_03: nothing here (B7_06 = beam_r21 flat landing spots; A0_10 = 3-cone PO path in r2_cutaway).
"""
import bpy
from mathutils import Vector

POST_BOX = ((-0.2, 0.16), (-0.5, -0.2), (0.8, 2.2))


def _cut_any(ob, xr, yr, zr):
    """delete every face of ob lying wholly inside the world box (only the near vertical post, not the long beam)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    dead = [f for f in bm.faces if all(xr[0] < c.x < xr[1] and yr[0] < c.y < yr[1] and zr[0] < c.z < zr[1]
                                       for c in (mw @ v.co for v in f.verts))]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    return len(dead)


def _b803(sc):
    for ob in list(bpy.data.objects):
        if ob.type == "MESH" and ob.name.startswith("Bay_"):
            print("[cut_2b_r21] cut", ob.name, _cut_any(ob, *POST_BOX))
    sec = bpy.data.objects.get("Bay_sec")         # the post's section cap is one tall face (centre test, any height)
    if sec is not None:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(sec.data)
        mw = sec.matrix_world
        dead = [f for f in bm.faces if (lambda c: -0.2 < c.x < 0.16 and -0.5 < c.y < -0.2 and 0.8 < c.z < 4.0)(
            mw @ f.calc_center_median())]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(sec.data)
        bm.free()
        print("[cut_2b_r21] cut Bay_sec tall", len(dead))
    import beam_r21 as R21B
    bo, sl = bpy.data.objects.get("Bounce6"), bpy.data.objects.get("SlitW")
    if bo is None or sl is None:
        return
    a = bo.location - Vector((0, 0.15, 0))                       # M4 landing (Bounce6 sits 0.15 behind it)
    vs = [sl.matrix_world @ v.co for v in sl.data.vertices]
    b = sum(vs, Vector()) / len(vs)
    b = Vector((b.x, b.y, b.z + 0.001))
    s = a + (b - a) * 0.55
    os_, ms_ = R21B.cone(s, b, 0.09 + (0.012 - 0.09) * 0.55, 0.006, "ScanTipR21", k=2.6, seg=48)
    R21B.tip(b, Vector((0, 0, 1)), "ScanSlitLandR21", 1, scale=0.55)


def post(sc, variant, shot):
    if shot in ("B8_03", "B8_03M"):
        _b803(sc)
    return sc
