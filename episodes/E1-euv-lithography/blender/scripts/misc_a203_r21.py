"""R21 A2_03 (R21_ROOT_CAUSE row #3, R20 review A2_03 #1 "紫光在右侧镜座附近拐弯，拐点没有清楚落在镜面上…把拐点对准镜面中心，
加一个镜面落点高光，入射段和反射段都做成锥形收放"): light turns only ON the mirror faces.

The R18/R19 cones (fold PO4 -> PO5, NA cone PO5 -> wafer) end in discs perpendicular to the cone axis; at an oblique mirror
half of that disc stands in front of the face, so the V-turn reads as happening in mid-air next to the mount. Here every
cone end that meets a mirror is cut by that mirror's face plane: each vertex of the end ring (and any vertex behind the
face) is slid along the cone axis onto the plane through the face centre. The cone stays a straight converging /
diverging cone, its end cap becomes a flat ellipse lying ON the mirror face, both cones of a turn share the face centre,
and a flat landing highlight spot (larger than R19's) sits on the face there. Own code (no beam_r21 import).
Called from r2_misc._bokeh only when A2_03 is in R21_SHOTS.
"""
import bpy
from mathutils import Vector


def clip_to_plane(ob, a, b, ends):
    """ends: list of (which, P, n) with which in {"a", "b"}; P = face centre, n = face normal (front side)."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    L = (b - a).length
    mw, mi = ob.matrix_world, ob.matrix_world.inverted()
    me = ob.data
    moved = 0
    for v in me.vertices:
        w = mw @ v.co
        s = (w - a).dot(u) / L
        for which, P, n in ends:
            P, n = Vector(P), Vector(n).normalized()
            un = u.dot(n)
            if abs(un) < 1e-4:
                continue
            d = (w - P).dot(n)
            near_end = (s > 0.97) if which == "b" else (s < 0.03)
            # the front side of the face is where the cone's far end lies
            far = a if which == "b" else b
            front = 1.0 if (far - P).dot(n) > 0 else -1.0
            if near_end or d * front < 0:
                w = w - u * (d / un)
                moved += 1
        v.co = mi @ w
    me.update()
    return moved


def apply(B, nrm, wf, n_frames=None):
    import misc_mirror_r19 as MM
    po4, po5 = Vector(B.PO[4]), Vector(B.PO[5])
    for nm in ("FoldR18", "FoldR18In"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            k = clip_to_plane(ob, po4, po5, [("a", po4, nrm[4]), ("b", po5, nrm[5])])
            print(f"[R21 A2_03] {nm}: {k} vertices put on the PO4 / PO5 faces")
    for nm in ("NAConeR18", "NAConeR18In"):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            k = clip_to_plane(ob, po5, wf, [("a", po5, nrm[5])])
            print(f"[R21 A2_03] {nm}: {k} vertices put on the PO5 face")
    # flat landing highlight on each turning face, centred exactly on the face centre
    for i in (4, 5):
        MM.landing(f"MirrorSpotR21_{i}", Vector(B.PO[i]) + Vector(nrm[i]).normalized() * 0.002, nrm[i],
                   B.PO_R[i] * 0.42, strength=10.0, light=3.0)
