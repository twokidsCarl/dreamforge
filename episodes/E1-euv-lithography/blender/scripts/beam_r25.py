"""Round 25 (P1, R25_ROOT_CAUSE rows 1 + 2, owned by the MAIN process - agents import it, never edit it).

R24 review: A0_10 (new lowest) "光束在顶部和右上拐弯，拐点只有一根细白条或小筒，外行会读成『光在空中拐弯』…各放一面能看见
反射面的实心镜和镜座"; all three lanes: beams still read as "等宽实心柱 / 等宽的半透明管". beam_r24 fixed the path
CONTRACT (one ordered path, no crossing) but (a) its surface cone had a bright inner cone (inner_gain 1.6) that fills
the silhouette -> solid column, (b) agents passed near-equal end radii (0.20 -> 0.16), (c) nothing guaranteed a
physical mirror at a turn.

Superset of beam_r24 (same call shapes; key_chain / landing reused):
  * soft_cone()  - SHELL cone: emission k = facing^edge (bright silhouette shell; Blender Facing = 0 face-on) + a very faint core
                   (core * strength, NO inner cone), brighter toward the narrow end (the focus); the two end radii are
                   forced to >= taper:1 (default 3:1) by shrinking the narrow end. Not R18-R21 volume fog (no volume
                   shader), not R16 end fade (no fade), not R17 thin core (no inner object).
  * mirror_at()  - a solid disc mirror (coated face + substrate) on a machined mount (kit_r2.mirror_with_mount: ring,
                   bolt circle, cell, hexapod struts, back plate) whose FRONT FACE passes through the stop point, so
                   the landing highlight lies ON the mirror.
  * chain()      - beam_r24.chain + taper + a mirror_at() at every interior stop that has a face normal (unless the
                   caller passes an existing scene mirror object for that stop in existing={i: obj}); mirror radius
                   = max(mirror_r, 3 x the beam radius at the stop) so the landing is <= 1/3 of the mirror aperture.
  * check()      - beam_r24.check (ends in frame / no crossing / axis >= 45 deg / width <= 60 % / camera >= 2x mouth
                   radius) PLUS (R24 RETRO) taper: each leg's two ends >= 2:1 in SCREEN width, and turn mirrors: every
                   interior stop with a face normal has a mirror object that is >= 30 deg out of edge-on
                   (|n . to_cam| >= 0.5; seen from the BACK = WARN, Q3 must say how it reads), and every interior
                   stop WITHOUT a mirror (a focus such as the IF) is passed straight through (bend <= 8 deg).
                   R25 sketch (r25smoke/sketch25): in a side-on cutaway every bisector of an in-plane path is
                   perpendicular to the line of sight (A0_10 |n.to_cam| 0.06-0.45 = the R24 "thin white strip");
                   depth-staggering the turn stops (+-0.5-1.5 m) and / or orbiting the camera is what opens the faces.
"""
import math

import bpy
from mathutils import Vector

import beam_r24 as B24
import kit_r2 as K
import misc_beam_r18 as MB

VIOLET = K.VIOLET
TAPER = 3.0            # build-time end-radius ratio per leg
TAPER_SCREEN = 2.0     # check-time screen-width ratio per leg
MIRROR_FACE_MIN = 0.5  # |n . to_camera| (sin 30 deg) -> the disc is >= 30 deg out of edge-on (front or back)
BEND_MAX = 8.0         # a stop without a mirror (focus) may bend the path by at most this (straight through)

key_chain = B24.key_chain
landing = B24.landing
_proj = B24._proj


def _rmax(r):
    return r if isinstance(r, (int, float)) else max(r)


def _scale(r, s):
    return r * s if isinstance(r, (int, float)) else tuple(x * s for x in r)


def tapered(ra, rb, taper=TAPER):
    """Return (ra, rb) with max/min >= taper (the narrow end shrinks; the wide end = the aperture stays)."""
    a, b = _rmax(ra), _rmax(rb)
    if min(a, b) <= 1e-6 or max(a, b) / min(a, b) >= taper:
        return ra, rb
    if a >= b:
        return ra, _scale(rb, (a / taper) / b)
    return _scale(ra, (b / taper) / a), rb


def shell_mat(name, color, strength, alpha=0.6, edge=2.4, core=0.08, gain=1.2, narrow_at_end=True):
    """Shell emission: k = (facing^edge + core) * (1 + gain * w), w = 0 at the wide end, 1 at the narrow end."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    op = MB._op
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    # LayerWeight Facing = 0 where the surface faces the camera (the cone's core), -> 1 at the silhouette: Facing^edge
    # is the bright SHELL / dark core (R25 mbeam caught the first draft using 1 - Facing = bright core = solid column)
    shell = op(N, L, "POWER", lw.outputs["Facing"], edge)
    k = op(N, L, "ADD", shell, core)
    uv = N.new("ShaderNodeUVMap")
    uv.uv_map = "ConeUV"
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sp.inputs[0])
    v = sp.outputs["Y"]
    w = v if narrow_at_end else op(N, L, "SUBTRACT", 1.0, v)
    if gain:
        k = op(N, L, "MULTIPLY", k, op(N, L, "ADD", 1.0, op(N, L, "MULTIPLY", w, gain)))
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*K.lin(color), 1)
    L.new(op(N, L, "MULTIPLY", k, strength), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(op(N, L, "MINIMUM", op(N, L, "MULTIPLY", k, alpha), 1.0), mx.inputs["Fac"])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def soft_cone(name, a, b, ra, rb, color=None, strength=4.0, alpha=0.6, edge=2.4, core=0.08, gain=1.2, taper=TAPER,
              xdir=None, seg=48, **_ignored):
    """Shell soft cone a -> b, end radii forced to >= taper:1. Returns [obj] (list, like beam_r24.soft_cone).
    Extra beam_r24 kwargs (inner, inner_gain, fade0, fade1) are ignored on purpose (no inner cone, no end fade)."""
    ra, rb = tapered(ra, rb, taper)
    me, _s = MB._cone_mesh(name, tuple(a), tuple(b), ra, rb, xdir, seg)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(shell_mat(name + "M", VIOLET if color is None else color, strength, alpha, edge, core, gain,
                                  narrow_at_end=_rmax(rb) <= _rmax(ra)))
    MB._vis(ob)
    ob["r25_radii"] = (float(_rmax(ra)), float(_rmax(rb)))
    return [ob]


_MATS = {}


def _mirror_mats():
    if not _MATS or any(m.name not in bpy.data.materials for m in _MATS.values()):
        _MATS.clear()
        _MATS.update(
            coating=K.mat("R25MirrorCoat", (0.80, 0.78, 0.90), metal=1.0, rough=0.08, coat=0.8),
            substrate=K.mat("R25MirrorBody", (0.82, 0.82, 0.85), metal=1.0, rough=0.18, brushed=0.06),
            mount=K.mat("R25MirrorMount", (0.42, 0.44, 0.48), metal=1.0, rough=0.35, brushed=0.1),
            bolt=K.mat("R25MirrorBolt", (0.62, 0.63, 0.66), metal=1.0, rough=0.2),
        )
    return _MATS


def mirror_at(name, p, nrm, r, mount=True, struts=True, mats=None):
    """Solid disc mirror whose front face passes through p (normal nrm) + machined mount. Returns [objects]."""
    M = mats or _mirror_mats()
    mbm, mbsub, mbmount, mbbolt = K.MB(), K.MB(), K.MB(), K.MB()
    K.mirror_with_mount(mbm, mbmount, mbbolt, Vector(p), Vector(nrm), r, thick=max(0.02, r * 0.3),
                        struts=struts and mount, mbsub=mbsub)
    obs = [mbm.obj(name + "Face", M["coating"]), mbsub.obj(name + "Body", M["substrate"])]
    if mount:
        obs += [mbmount.obj(name + "Mount", M["mount"]), mbbolt.obj(name + "Bolts", M["bolt"])]
    for o in obs:
        o["r25_mirror"] = name
    return obs


def chain(name, stops, radii, color=None, strength=4.0, alpha=0.6, edge=2.4, core=0.08, gain=1.2, spot_strength=12.0,
          spot_scale=1.0, land_final=True, taper=TAPER, mirrors=True, mirror_r=None, existing=None, mount=True,
          **_ignored):
    """ONE path with tapered shell legs + a solid mounted mirror at every interior stop with a face normal.
    stops = [(point, normal_or_None)], radii = beam radius at each stop. mirror_r = float or {stop: r};
    existing = {stop index: scene object} (an existing mirror counts, nothing is built there).
    Returns beam_r24-style dict + "mirrors": {stop index: [objects]} + "leg_radii": [(ra, rb)]."""
    assert len(stops) >= 2 and len(radii) == len(stops)
    existing = existing or {}
    legs, leg_r, spots, mir = [], [], [None], {}
    for i in range(len(stops) - 1):
        a, b = Vector(stops[i][0]), Vector(stops[i + 1][0])
        ra, rb = tapered(radii[i], radii[i + 1], taper)
        legs.append(soft_cone(f"{name}Leg{i}", a, b, ra, rb, color, strength, alpha, edge, core, gain, taper))
        leg_r.append((_rmax(ra), _rmax(rb)))
    for i in range(1, len(stops)):
        p, nrm = stops[i]
        last = i == len(stops) - 1
        # landing footprint = the narrower of the two leg ends meeting here (<= 1/3 of the mirror aperture)
        r_in = leg_r[i - 1][1]
        r_here = min(r_in, leg_r[i][0]) if not last else r_in
        if nrm is None or (last and not land_final):
            spots.append(None)
        else:
            d = Vector(p) - Vector(stops[i - 1][0])
            spots.append(landing(f"{name}Spot{i}", p, d, nrm, max(r_here, 0.004) * spot_scale,
                                 strength=spot_strength))
        if last or nrm is None:
            continue
        if i in existing:
            mir[i] = [existing[i]]
            existing[i]["r25_mirror"] = existing[i].name
        elif mirrors:
            mr = mirror_r.get(i) if isinstance(mirror_r, dict) else mirror_r
            mr = max(mr or 0.0, 3.0 * max(r_in, leg_r[i][0]) * 1.05)
            mir[i] = mirror_at(f"{name}Mir{i}", p, nrm, mr, mount=mount)
    return {"legs": legs, "spots": spots, "stops": [(Vector(p), n) for p, n in stops], "radii": list(radii),
            "leg_radii": leg_r, "mirrors": mir}


def _screen_w(sc, cam, p, ax, r):
    cl = cam.matrix_world.translation
    los = (Vector(p) - cl).normalized()
    side = ax.cross(los)
    if side.length < 1e-9:
        return 0.0
    side = side.normalized() * r
    s1, z1 = _proj(sc, cam, Vector(p) + side)
    s2, z2 = _proj(sc, cam, Vector(p) - side)
    return (s1 - s2).length if z1 > 0 and z2 > 0 else 0.0


def check(sc, ch, frames, exits=(), tag="", cam=None, mirror_stops=None):
    """beam_r24.check + taper (screen width ratio >= 2:1 per leg) + turn mirrors (each interior stop: a mirror object,
    face toward the camera n . to_cam >= 0.5). mirror_stops = interior stop indices that must carry a mirror
    (default: every interior stop). Prints BEAMCHECK lines; returns the NOGO list."""
    cam = cam or sc.camera
    bad = B24.check(sc, ch, frames, exits=exits, tag=tag, cam=cam)
    stops = ch["stops"]
    leg_r = ch.get("leg_radii") or [(_rmax(ch["radii"][i]), _rmax(ch["radii"][i + 1])) for i in range(len(stops) - 1)]
    interior = list(range(1, len(stops) - 1)) if mirror_stops is None else list(mirror_stops)
    mirrors = ch.get("mirrors", {})
    extra = []
    for f in frames:
        sc.frame_set(int(f))
        cl = cam.matrix_world.translation
        for i in range(len(stops) - 1):
            a, b = stops[i][0], stops[i + 1][0]
            ax = (b - a).normalized()
            wa, wb = _screen_w(sc, cam, a, ax, leg_r[i][0]), _screen_w(sc, cam, b, ax, leg_r[i][1])
            ratio = max(wa, wb) / max(min(wa, wb), 1e-6)
            print(f"BEAMCHECK25 {tag} f{f} leg{i} end widths {wa:.1f}px / {wb:.1f}px taper {ratio:.1f}:1", flush=True)
            if ratio < TAPER_SCREEN:
                extra.append(f"f{f} leg{i} taper {ratio:.1f}:1 on screen (< {TAPER_SCREEN:.0f}:1: equal-width tube)")
        for i in interior:
            p, n = stops[i]
            obs = mirrors.get(i)
            if n is None:
                # a focus (IF) or pass-through point: light may only go STRAIGHT through it
                d0 = (Vector(p) - Vector(stops[i - 1][0])).normalized()
                d1 = (Vector(stops[i + 1][0]) - Vector(p)).normalized()
                bend = math.degrees(math.acos(max(-1.0, min(1.0, d0.dot(d1)))))
                print(f"BEAMCHECK25 {tag} f{f} stop{i} focus (no mirror) bend {bend:.0f} deg", flush=True)
                if bend > BEND_MAX:
                    extra.append(f"f{f} stop{i} path bends {bend:.0f} deg at a stop with NO mirror (light turns "
                                 f"in mid-air)")
                continue
            if not obs:
                extra.append(f"f{f} stop{i} turn has NO mirror object (light turns in mid-air)")
                continue
            to_cam = (cl - Vector(p)).normalized()
            dot = Vector(n).normalized().dot(to_cam)
            side = "FRONT" if dot >= 0 else "BACK"
            print(f"BEAMCHECK25 {tag} f{f} stop{i} mirror {obs[0].name} n.to_cam {dot:+.2f} "
                  f"({math.degrees(math.asin(min(1.0, abs(dot)))):.0f} deg out of edge-on, {side})", flush=True)
            if abs(dot) < MIRROR_FACE_MIN:
                extra.append(f"f{f} stop{i} mirror edge-on (|n.to_cam| {abs(dot):.2f} < {MIRROR_FACE_MIN}: reads as a "
                             f"thin strip)")
            elif dot < 0:
                print(f"BEAMCHECK25 {tag} WARN f{f} stop{i} mirror seen from the BACK (landing hidden) - Q3 must say "
                      f"how it reads", flush=True)
    for b_ in extra:
        print(f"BEAMCHECK25 {tag} NOGO {b_}", flush=True)
    bad = bad + extra
    print(f"BEAMCHECK25 {tag} {'OK' if not bad else 'NOGO ' + str(len(bad))} frames {list(frames)}", flush=True)
    return bad
