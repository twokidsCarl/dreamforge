"""Round 17 (P1) beam route for blender/shots/r2_misc.py (R17_ROOT_CAUSE #4). Never used by the photons variant
(B9_05 gold control). Installed in-process from r2_misc only; shared beam_r12 / beam_r16 / misc_kit_r16 untouched.

R16 review: taper / end-fade cones (beam_r16) still read as equal-width tubes at 960x540, haze hides the mirrors.
R17 changes ROUTE, not cone knobs:
  * thin_core      - the light between two surfaces is ONLY a thin bright core (no wide haze shell / cone)
  * landing        - where the light hits a surface: a soft elliptical highlight lying ON that surface (radial
                     falloff, no stacked halo discs) + a small violet point light just above it, so the mirror /
                     mount around the spot actually catches light ("each mirror gets one bright spot")
  * columns_factory_r17 - drop-in for K.beam_columns in the A2_03 / A2_08 machine backdrop: one path only, every
                     leg a thin core, landing highlights collected for the caller
  * prune_bounce   - removes the machine's violet bounce lights on mirrors the drawn path does not touch (they lit
                     every mirror disc violet = "a row of spotlights")
"""
import math

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K


def _core_mat(name, color, strength, alpha=0.95, power=0.6, fade0=0.0, fade1=0.0):
    import misc_kit_r16 as MK                      # material builder only (read-only reuse)
    return MK.fade_beam_mat(name, color, strength, alpha, power, fade0=fade0, fade1=fade1)


def thin_core(name, a, b, r, color=None, strength=8.0, alpha=0.95, fade0=0.0, fade1=0.0, seg=12, r_end=None,
              glossy=True):
    """Thin bright light core a -> b (open tube, soft silhouette). fade0 / fade1 fade a FREE end (path start /
    end that does not sit on a surface); ends on a surface stay hard and meet the landing highlight."""
    import misc_kit_r16 as MK
    color = K.VIOLET if color is None else color
    m = _core_mat(name + "M", color, strength, alpha, 0.6, fade0, fade1)
    ob = MK.fade_cone(name, Vector(a), Vector(b), r, r if r_end is None else r_end, m, seg=seg,
                      stations=[k / 24 for k in range(25)], core=0)
    if not glossy:
        ob.visible_glossy = False                 # its mirror image in a polished coating read as an X crossing
    return ob


def _spot_mat(name, color, strength, power=2.2):
    """Radial falloff disc: emission + alpha = (1 - rho) ^ power, rho from the disc's UV (0 centre .. 1 rim)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "SpotUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])

    def op(o, a, b):
        x = N.new("ShaderNodeMath")
        x.operation = o
        for i, s in enumerate((a, b)):
            if isinstance(s, (int, float)):
                x.inputs[i].default_value = s
            else:
                L.new(s, x.inputs[i])
        return x.outputs[0]
    k = op("POWER", op("MAXIMUM", op("SUBTRACT", 1.0, sp.outputs["Y"]), 0.0), power)
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op("MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op("MINIMUM", op("MULTIPLY", k, 1.6), 1.0), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def landing(name, p, nrm, r, color=None, strength=6.0, light=None, light_r=0.03, squash=1.0, major=None, lift=0.003):
    """Soft highlight lying on the surface at p (normal nrm), radius r; squash < 1 makes it an ellipse along
    `major` (in-plane direction, e.g. the projected beam direction). light = point-light energy (W) just above."""
    color = (0.86, 0.78, 1.0) if color is None else color
    n = Vector(nrm).normalized()
    q = Vector((0, 0, 1)).rotation_difference(n)
    ex = q @ Vector((1, 0, 0))
    if major is not None:
        mj = Vector(major) - n * Vector(major).dot(n)
        if mj.length > 1e-6:
            ex = mj.normalized()
    ey = n.cross(ex).normalized()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("SpotUV")
    c = Vector(p) + n * lift
    seg, rings = 40, 6
    ctr = bm.verts.new(c)
    prev = None
    for k in range(1, rings + 1):
        rho = k / rings
        ring = [bm.verts.new(c + ex * (r * rho * math.cos(2 * math.pi * i / seg))
                             + ey * (r * squash * rho * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
        for i in range(seg):
            j = (i + 1) % seg
            if prev is None:
                f = bm.faces.new((ctr, ring[i], ring[j]))
                vals = (0.0, rho, rho)
            else:
                f = bm.faces.new((prev[i], ring[i], ring[j], prev[j]))
                vals = ((k - 1) / rings, rho, rho, (k - 1) / rings)
            for lp, v in zip(f.loops, vals):
                lp[uvl].uv = (0.5, v)
        prev = ring
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(_spot_mat(name + "M", color, strength))
    ob.visible_shadow = False
    try:
        ob.visible_diffuse = False                # the spot itself does not light the scene; the point light does
        ob.visible_glossy = True
    except AttributeError:
        pass
    if light:
        lo = K.point(name + "L", c + n * max(0.04, r * 0.6), light, K.VIOLET, light_r)
        lo.visible_camera = False                 # the light's sphere showed up as a speckled blob on the spot
        lo.visible_glossy = False
    return ob


def columns_factory_r17(spots, keep=None, r_core=0.016, strength=7.0, tag="CoreR17", color=None):
    """Drop-in for K.beam_columns inside build_cutaway_r2.machine: legs lo..hi-1 only (one path), each leg a thin
    core; landing points (p, normal, r) go to `spots` for the caller to build with landing()."""
    built = []

    def cols(mb, pts, radii, seg=40):
        pts = [Vector(p) for p in pts]
        lo, hi = keep if keep else (0, len(pts) - 1)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            if not (lo <= i < hi):
                continue
            built.append(thin_core(f"{tag}_{i}", a, b, r_core, K.VIOLET if color is None else color, strength, 0.95))
        for j in range(max(1, lo), min(len(pts) - 1, hi + 1)):
            spots.append((pts[j], K.mirror_normal(pts[j - 1], pts[j], pts[j + 1]), j))
    return cols, built


def prune_bounce(keep_idx):
    """Delete Bounce{i} point lights (build_cutaway_r2.machine) whose index is not in keep_idx."""
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT" and ob.name.startswith("Bounce"):
            try:
                i = int(ob.name[6:].split(".")[0])
            except ValueError:
                continue
            if i not in keep_idx:
                bpy.data.objects.remove(ob, do_unlink=True)


def golf_ball_r17(name, loc, r, mat, depth=0.035, subdiv=6):
    """B4_10 landing surface: a real golf ball - ~320 regular, near-hexagonal shallow dimples (centres = face
    centres of a 2x subdivided icosahedron, the classic icosahedral layout) pressed into a dense icosphere."""
    from mathutils import kdtree
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    centres = [f.calc_center_median().normalized() for f in bm.faces]
    bm.free()
    kd = kdtree.KDTree(len(centres))
    for i, c in enumerate(centres):
        kd.insert(c, i)
    kd.balance()
    _c, _i, d_nn = kd.find_n(centres[0], 2)[1]
    ang0 = 0.47 * d_nn                                    # dimple radius ~ 47 % of the centre spacing (chord ~ angle)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        u = v.co.normalized()
        c, i, d = kd.find(u)
        x = d / ang0
        h = depth * (1.0 - x * x) if x < 1.0 else 0.0
        v.co = u * r * (1.0 - h)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    me.materials.append(mat)
    return ob
