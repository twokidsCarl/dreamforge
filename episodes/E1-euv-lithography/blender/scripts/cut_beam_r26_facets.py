"""R26 cbeam helper, R26_ROOT_CAUSE row 4 (B5_01): field facet mirror = each facet strip individually lit.
R25 review (B5_01 p2 #1): 「场分面镜读起来像百叶窗或散热片，小镜之间没有反光差异。给每条弧形小镜单独的倾角和高光，让人看得出是一面面
小镜」. post(): every facet strip island of R8Kit2_facet gets
  * its own small tilt (+-TILT deg about its long axis, seeded) -> each strip catches a different reflection,
  * one of three polished-mirror tone / roughness variants (still hi_mirror metal, never violet),
  * its own landing: a 3 mm-raised copy of the strip's front face with a violet emission that falls off with the distance
    from the FFM landing point (footprint radius R) - strips outside the footprint stay dark, the gaps between strips stay
    dark, so the one round R24 landing disc becomes a row of separately lit strips. The R24 single disc (Spot1) is hidden.
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

TILT = 7.0          # deg, per strip
R_FOOT = 0.5        # m, footprint radius on the facet mirror (leg0 end 0.27 m, x1.35 mouth + spill)
EMIT = 9.0
OFF = 0.003
LANDINGS = False


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


def _land_mat(center, color):
    import kit_r2 as K
    m = bpy.data.materials.new("B5R26FacetLandM")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    geo = N.new("ShaderNodeNewGeometry")
    dist = N.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.inputs[1].default_value = tuple(center)
    L.new(geo.outputs["Position"], dist.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHERSTEP"
    mr.inputs["From Min"].default_value = R_FOOT
    mr.inputs["From Max"].default_value = 0.0
    L.new(dist.outputs["Value"], mr.inputs["Value"])
    att = N.new("ShaderNodeAttribute")          # per-strip gain (face attribute)
    att.attribute_name = "r26_gain"
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L.new(mr.outputs["Result"], mul.inputs[0])
    L.new(att.outputs["Fac"], mul.inputs[1])
    s = N.new("ShaderNodeMath")
    s.operation = "MULTIPLY"
    L.new(mul.outputs[0], s.inputs[0])
    s.inputs[1].default_value = EMIT
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(s.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(mul.outputs[0], mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m


def post(sc, center, n_face):
    """n_face = a world point on the incoming side (the IF): each strip's lit face is the one turned toward it."""
    import kit_r2 as K
    import cut_mirror_r19 as CM
    ob = bpy.data.objects.get("R8Kit2_facet")
    if ob is None:
        print("[r26c] B5_01 facets: R8Kit2_facet missing", flush=True)
        return
    rnd = random.Random(26)
    mw = ob.matrix_world
    mwi = mw.inverted()
    base = ob.data.materials[0]
    vari = [CM.hi_mirror("B5R26FacetA", rough=0.03, tone=0.95), CM.hi_mirror("B5R26FacetB", rough=0.09, tone=0.8),
            CM.hi_mirror("B5R26FacetC", rough=0.16, tone=0.66)]
    for m in vari:
        ob.data.materials.append(m)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    isl = _islands(bm)
    land = bmesh.new()
    gain_l = land.faces.layers.float.new("r26_gain")
    lit = 0
    center_l = mwi @ Vector(center)
    for k, vs in enumerate(isl):
        ids = {v.index for v in vs}
        faces = [f for f in bm.faces if f.verts[0].index in ids]
        if not faces:
            continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        # long axis: farthest vertex pair direction (strips are long and thin)
        far = max(vs, key=lambda v: (v.co - c).length)
        ax = (far.co - c).normalized()
        big = max(faces, key=lambda f: f.calc_area())
        nf = big.normal.copy()
        if (mw.to_3x3() @ nf).dot(Vector(n_face) - (mw @ c)) < 0:      # lit face = the one facing the IF (incoming)
            nf = -nf
        ang = math.radians(rnd.uniform(-TILT, TILT))
        R = Matrix.Translation(c) @ Matrix.Rotation(ang, 4, ax) @ Matrix.Translation(-c)
        for v in vs:
            v.co = R @ v.co
        nf = (R.to_3x3() @ nf).normalized()
        mi = 1 + rnd.randrange(3)
        for f in faces:
            f.material_index = mi
        # own landing on the IF-facing face inside the footprint (LANDINGS False: those faces are turned AWAY from the
        # B5_01 camera - measured n.to_IF / n.to_cam opposite on every lit strip at f64 - so a per-strip landing is hidden)
        if not LANDINGS or (mw @ c - Vector(center)).length > R_FOOT + 0.25:
            continue
        g = rnd.uniform(0.55, 1.0)
        front = [f for f in faces if f.normal.dot(nf) > 0.8]
        vmap = {}
        for f in front:
            nv = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = land.verts.new(v.co + nf * OFF)
                nv.append(vmap[v.index])
            try:
                nfc = land.faces.new(nv)
                nfc[gain_l] = g
            except ValueError:
                pass
        lit += 1
    bm.to_mesh(ob.data)
    bm.free()
    me = bpy.data.meshes.new("B5R26FacetLand")
    land.to_mesh(me)
    land.free()
    # face float layer -> attribute name r26_gain is kept by to_mesh
    if not LANDINGS:
        bpy.data.meshes.remove(me)
        print(f"[r26c] B5_01 facets: {len(isl)} strips tilted +-{TILT} deg, 3 tone variants (no per-strip landings)", flush=True)
        return
    lo = bpy.data.objects.new("B5R26FacetLand", me)
    sc.collection.objects.link(lo)
    lo.matrix_world = mw.copy()
    me.materials.append(_land_mat(center, K.VIOLET))
    for nm in ("IllumPathR24Spot1",):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = True
    print(f"[r26c] B5_01 facets: {len(isl)} strips tilted +-{TILT} deg, 3 tone variants, {lit} strips with own landing",
          flush=True)
