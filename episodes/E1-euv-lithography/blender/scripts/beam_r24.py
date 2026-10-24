"""Round 24 (P1, R24_ROOT_CAUSE row 3 "beam unification", owned by the MAIN process - agents import it, never edit it).

R23 review (p2 #1 / p3 #2): "一屏一条光路，光束锥形收放、软边，每个拐点落在可见的镜面高光上" - the failures were
not the cone SHAPE (R13 waist beads, R16 taper / end fade, R17 thin core, R18-R21 volume density were all tried) but
the PATH CONTRACT: each scene drew its legs ad hoc, so several legs were lit at once and crossed on screen (B5_01 X,
A0_10 right-bay Z), a leg ended in mid-air (C_03 55 % frame), a volume leg filled the bay with fog (B7_06), a landing
was a halo instead of a spot on the face (B4_07 / A2_03), the cone vanished on the last frame (B8_17).

One contract for every importer (r2_cutaway / r2_misc / r2_source hooks):
  * chain(stops)   - ONE ordered path per screen: source/focus -> mirror -> mirror -> target. Each leg is a straight
                     SURFACE-emission soft cone (facing falloff = soft edge, brighter inner core, zero outside the
                     silhouette; no volume shader -> no bay fog) whose two end radii are the two apertures, so it
                     visibly tapers. Every interior stop and the final stop with a face normal gets a flat elliptical
                     landing highlight lying ON the face (beam footprint), i.e. every turn sits on a visible highlight.
  * key_chain()    - optional timed reveal (leg i lights at its frame and STAYS lit: the chain grows, never jumps).
  * check()        - screen-space validator on the job frames (prints BEAMCHECK lines): both ends of every leg in
                     frame (or flagged exit), no two non-adjacent legs crossing on screen, cone axis vs line of sight
                     >= 45 deg (no cone pointing at the camera), cone screen width <= 60 % of the frame, camera
                     distance to the cone surface >= 2x the cone mouth radius (R23 RETRO: B3_02 camera beside the cone).
"""
import math

import bmesh
import bpy
from mathutils import Vector

import kit_r2 as K
import misc_beam_r18 as MB   # cone_mat / _cone_mesh / _vis reused unchanged (surface soft cone recipe)

VIOLET = K.VIOLET


def _v(p):
    return Vector(p)


def soft_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=0.6, edge=1.8, inner=0.45, inner_gain=1.6,
              fade0=0.0, fade1=0.0, gain=0.4, xdir=None, seg=48):
    """Surface soft cone a -> b (ra / rb = end radii or (rx, ry) ellipses). Returns [outer, inner] objects."""
    return MB.vol_cone(name, tuple(a), tuple(b), ra, rb, color=VIOLET if color is None else color, strength=strength,
                       alpha=alpha, edge=edge, inner=inner, inner_gain=inner_gain, fade0=fade0, fade1=fade1, gain=gain,
                       xdir=xdir, seg=seg)


def _spot_mat(name, color, strength, alpha):
    """Radial falloff disc: bright centre, soft rim (SpotUV: centre (0.5, 0.5), rim radius 0.5)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "SpotUV"
    sub = N.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    L.new(uv.outputs["UV"], sub.inputs[0])
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L.new(sub.outputs[0], ln.inputs[0])
    rr = N.new("ShaderNodeMath")          # 1 - 2|uv - c|  (1 at the centre, 0 on the rim)
    rr.operation = "MULTIPLY_ADD"
    L.new(ln.outputs["Value"], rr.inputs[0])
    rr.inputs[1].default_value = -2.0
    rr.inputs[2].default_value = 1.0
    rr.use_clamp = True
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    L.new(rr.outputs[0], pw.inputs[0])
    pw.inputs[1].default_value = 1.6
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    ms = N.new("ShaderNodeMath")
    ms.operation = "MULTIPLY"
    L.new(pw.outputs[0], ms.inputs[0])
    ms.inputs[1].default_value = strength
    L.new(ms.outputs[0], em.inputs["Strength"])
    ma = N.new("ShaderNodeMath")
    ma.operation = "MULTIPLY"
    L.new(pw.outputs[0], ma.inputs[0])
    ma.inputs[1].default_value = alpha
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(ma.outputs[0], mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def landing(name, c, d, nrm, r, color=None, strength=12.0, alpha=1.0, lift=0.003, cap=2.2):
    """Flat elliptical landing highlight ON the face at c (normal nrm) for a beam of radius r arriving along d."""
    color = (1.0, 0.93, 1.0) if color is None else color
    d = _v(d).normalized()
    n_ = _v(nrm).normalized()
    if n_.dot(d) > 0:
        n_ = -n_
    c_ = max(abs(d.dot(n_)), 0.2)
    u = d - n_ * d.dot(n_)
    if u.length < 1e-6:
        u = n_.orthogonal()
    u.normalize()
    v = n_.cross(u).normalized()
    a_u, a_v = min(r / c_, cap * r), r
    bm = bmesh.new()
    o = _v(c) + n_ * lift
    cen = bm.verts.new(o)
    ring = [bm.verts.new(o + u * a_u * math.cos(2 * math.pi * i / 48) + v * a_v * math.sin(2 * math.pi * i / 48))
            for i in range(48)]
    uvl = bm.loops.layers.uv.new("SpotUV")
    for i in range(48):
        f = bm.faces.new((cen, ring[i], ring[(i + 1) % 48]))
        for lp, k in zip(f.loops, (None, i, (i + 1) % 48)):
            lp[uvl].uv = (0.5, 0.5) if k is None else (0.5 + 0.5 * math.cos(2 * math.pi * k / 48),
                                                       0.5 + 0.5 * math.sin(2 * math.pi * k / 48))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(_spot_mat(name + "M", color, strength, alpha))
    MB._vis(ob)
    return ob


def chain(name, stops, radii, color=None, strength=4.0, alpha=0.6, edge=1.8, inner=0.45, spot_strength=12.0,
          spot_scale=1.0, land_final=True, **kw):
    """ONE path: stops = [(point, face_normal_or_None), ...] in light order, radii = aperture radius at each stop
    (float or (rx, ry)). Returns {"legs": [[outer, inner], ...], "spots": [obj or None per stop], "stops": [...]}."""
    assert len(stops) >= 2 and len(radii) == len(stops)
    legs, spots = [], [None]
    for i in range(len(stops) - 1):
        a, b = _v(stops[i][0]), _v(stops[i + 1][0])
        legs.append(soft_cone(f"{name}Leg{i}", a, b, radii[i], radii[i + 1], color, strength, alpha, edge, inner, **kw))
    for i in range(1, len(stops)):
        p, nrm = stops[i]
        if nrm is None or (i == len(stops) - 1 and not land_final):
            spots.append(None)
            continue
        r = radii[i] if isinstance(radii[i], (int, float)) else max(radii[i])
        d = _v(p) - _v(stops[i - 1][0])
        spots.append(landing(f"{name}Spot{i}", p, d, nrm, max(r, 0.004) * spot_scale, strength=spot_strength))
    return {"legs": legs, "spots": spots, "stops": [(_v(p), n) for p, n in stops], "radii": list(radii)}


def _key_alpha(ob, frames_vals):
    """Animate visibility by keying hide_render (hard) - simple, renders identically on CPU / GPU."""
    for f, on in frames_vals:
        ob.hide_render = not on
        ob.keyframe_insert("hide_render", frame=f)
        ob.hide_viewport = not on
        ob.keyframe_insert("hide_viewport", frame=f)


def key_chain(ch, leg_frames):
    """Timed reveal: leg i (and its landing spot) appears at leg_frames[i] and stays (the chain grows)."""
    for i, f in enumerate(leg_frames):
        objs = list(ch["legs"][i]) + ([ch["spots"][i + 1]] if ch["spots"][i + 1] is not None else [])
        for ob in objs:
            _key_alpha(ob, [(1, f <= 1), (max(1, f), True)] if f > 1 else [(1, True)])


# ---------------------------------------------------------------- screen-space validator (sketch + smoke tool)
def _proj(sc, cam, p):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    v = w2c(sc, cam, _v(p))
    W, H = sc.render.resolution_x, sc.render.resolution_y
    return Vector((v.x * W, (1 - v.y) * H)), v.z


def _seg_x(p1, p2, q1, q2):
    def cr(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
    d1, d2, d3, d4 = cr(q1, q2, p1), cr(q1, q2, p2), cr(p1, p2, q1), cr(p1, p2, q2)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def check(sc, ch, frames, exits=(), tag="", cam=None):
    """Print BEAMCHECK lines for each frame; returns list of NOGO strings. exits = stop indices allowed off-frame
    (a named off-frame target, e.g. IF leaving the frame)."""
    cam = cam or sc.camera
    W, H = sc.render.resolution_x, sc.render.resolution_y
    bad = []
    stops, radii = ch["stops"], ch["radii"]
    for f in frames:
        sc.frame_set(int(f))
        cl = cam.matrix_world.translation
        pts = [_proj(sc, cam, p) for p, _n in stops]
        for i, (s, z) in enumerate(pts):
            inn = 0 <= s.x <= W and 0 <= s.y <= H and z > 0
            if not inn and i not in exits:
                bad.append(f"f{f} stop{i} out of frame ({s.x:.0f},{s.y:.0f})")
        for i in range(len(stops) - 1):
            a, b = stops[i][0], stops[i + 1][0]
            ax = (b - a).normalized()
            mid = (a + b) * 0.5
            los = (mid - cl).normalized()
            ang = math.degrees(math.acos(min(1.0, abs(ax.dot(los)))))
            if ang < 45:
                bad.append(f"f{f} leg{i} axis {ang:.0f} deg to line of sight (<45: cone points at camera)")
            r_max = max(max(r) if not isinstance(r, (int, float)) else r for r in (radii[i], radii[i + 1]))
            # camera distance to the cone surface (approx: distance to axis segment minus local radius)
            t = max(0.0, min(1.0, (cl - a).dot(b - a) / max((b - a).length_squared, 1e-9)))
            ra = radii[i] if isinstance(radii[i], (int, float)) else max(radii[i])
            rb = radii[i + 1] if isinstance(radii[i + 1], (int, float)) else max(radii[i + 1])
            d_surf = (cl - a.lerp(b, t)).length - (ra + (rb - ra) * t)
            if d_surf < 2 * r_max:
                bad.append(f"f{f} leg{i} camera {d_surf:.2f} m from cone surface (< 2x mouth radius {r_max:.2f})")
            # screen width of the cone: project the wide end's two rim points perpendicular to the view
            wide = b if rb >= ra else a
            side = ax.cross(los).normalized() * r_max
            s1, _ = _proj(sc, cam, wide + side)
            s2, _ = _proj(sc, cam, wide - side)
            wf = (s1 - s2).length / W
            if wf > 0.6:
                bad.append(f"f{f} leg{i} cone width {wf:.0%} of frame (> 60 %)")
            print(f"BEAMCHECK {tag} f{f} leg{i} {pts[i][0].x:.0f},{pts[i][0].y:.0f} -> {pts[i+1][0].x:.0f},"
                  f"{pts[i+1][0].y:.0f} axis/los {ang:.0f}deg width {wf:.0%} cam-surface {d_surf:.2f}m", flush=True)
        for i in range(len(stops) - 1):
            for j in range(i + 2, len(stops) - 1):
                if _seg_x(pts[i][0], pts[i + 1][0], pts[j][0], pts[j + 1][0]):
                    bad.append(f"f{f} legs {i} and {j} cross on screen")
    for b_ in bad:
        print(f"BEAMCHECK {tag} NOGO {b_}", flush=True)
    if not bad:
        print(f"BEAMCHECK {tag} OK frames {list(frames)}", flush=True)
    return bad
