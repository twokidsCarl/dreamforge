"""Round 25 (P1) tin helpers (R25_ROOT_CAUSE row 3: material -> a LIT, STRUCTURED environment for the tin).
Used only by source_r25.py.

  tin_mat_r25    bright, slightly warm silver liquid metal: metallic 1, roughness 0.07 (no transmission / coat).
  film_mat_r25   same + fine capillary ripples (bump: concentric waves + fine noise) for the ultra-thin film.
  struct_bands   reflection 'chamber' made of SHAPED bright parts with dark gaps between them: lit viewport rims
                 (rings + softly lit glass inside), a two-line chamber flange, a port-tube streak and a crisp key -
                 no rectangular cards, no pure black chamber (R24), no white bowl (R23 bright gradient).
  env_r25        one camera-invisible sphere around a tin part that only rays LEAVING the tin see
                 (source_r23_tin._env_mat_r23 mechanism, opaque from the inside).
"""
import math

import bpy
from mathutils import Vector

import kit_r2 as K

TIN_COL = (0.90, 0.885, 0.86)      # bright silver, slightly warm
TIN_ROUGH = 0.07
WARM = (1.0, 0.93, 0.82)
COOL = (0.82, 0.88, 1.0)
BASE = (0.030, 0.029, 0.030)      # dark gaps (not pure black)


def _strip(b):
    for key in ("Transmission Weight", "Transmission", "Coat Weight", "Clearcoat"):
        if key in b.inputs:
            b.inputs[key].default_value = 0.0


def tin_mat_r25(name="TinMetalR25"):
    m = K.mat(name, TIN_COL, metal=1.0, rough=TIN_ROUGH)
    _strip(next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"))
    return m


def film_mat_r25(name="TinFilmR25", ripple=0.07, scale=4.0):
    """Fine liquid ripples on the film: concentric capillary waves (object space, film in the unit YZ plane) +
    a fine noise so the rings are irregular. Bump only (no displacement)."""
    m = K.mat(name, TIN_COL, metal=1.0, rough=TIN_ROUGH)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    _strip(b)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "RINGS"
    wv.rings_direction = "X"           # rings around the film normal (object X)
    wv.inputs["Scale"].default_value = 3.5
    wv.inputs["Distortion"].default_value = 4.0
    wv.inputs["Detail"].default_value = 2.0
    wv.inputs["Detail Scale"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY_ADD"
    nt.links.new(wv.outputs["Fac"], mx.inputs[0])
    mx.inputs[1].default_value = 0.04         # rings only a faint modulation of an irregular low-freq wobble
    nt.links.new(nz.outputs["Fac"], mx.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = ripple
    bp.inputs["Distance"].default_value = 0.02
    nt.links.new(mx.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _n(v):
    return tuple(Vector(v).normalized())


def struct_bands(to_cam, right, up=Vector((0, 0, 1)), mirror_dir=None, gain=1.0, key=8.0, violet=0.0):
    """Bands = (axis, c, w, strength, rgb): |dot(dir, axis) - c| < w (c = 1 -> round cap, c = cos(r) -> ring of
    angular radius r, c = 0 -> great-circle line). Built relative to the camera so the tin's visible half is
    always crossed by shaped bright parts and dark gaps."""
    tc, rt, up = Vector(to_cam).normalized(), Vector(right).normalized(), Vector(up).normalized()
    g = gain
    B = []
    if mirror_dir is None:         # droplet (sphere sees the whole env): chrome-ball read = lit chamber top half,
        B.append(((0, 0, 1), 1.0, 1.02, 0.85 * g, COOL))                     # sharp bright flange at the horizon,
        B.append(((0, 0, 1), 0.02, 0.10, 0.9 * g, WARM))                     # soft bright flange glow, dark below
    else:
        B.append(((0, 0, 1), 1.0, 0.75, 0.16 * g, COOL))
    # lit viewport overhead: bright rim ring + softly lit glass inside
    ov = _n(up * 1.0 + tc * 0.35 - rt * 0.25)
    if mirror_dir is None:
        B.append((ov, math.cos(math.radians(32)), 0.03, 1.2 * g, WARM))
    else:
        B.append((ov, math.cos(math.radians(16)), 0.02, 2.4 * g, WARM))
    # side port behind the camera (camera-left): rim ring
    sp = _n(tc * 1.0 - rt * 0.75 + up * 0.15)
    if mirror_dir is not None:     # (on the small droplets the port ring read as a doodle)
        B.append((sp, math.cos(math.radians(11)), 0.012, 2.6 * g, (1.0, 0.97, 0.92)))
    # crisp key highlight upper-left as seen on screen
    kd = _n(tc + up * 1.0 - rt * 0.5)
    B.append((kd, 1.0, 0.0035, key, (0.97, 0.98, 1.0)))
    if mirror_dir is not None:     # sheet: what the face mirrors = lit chamber wall above, a bright flange line
        md = Vector(mirror_dir).normalized()   # just above the mirror direction, dark gap, a fainter lower flange,
        hz = Vector((md.x, md.y, 0)).normalized() if abs(md.z) < 0.95 else rt  # one small lit port + a tube streak
        el = md.z                              # world-horizontal chamber flanges (the film stands vertical)
        B.append(((0, 0, 1), 1.0, 1.0 - el + 0.08, 0.80 * g, COOL))           # lit wall: bright above -> dark below
        B.append(((0, 0, 1), el + 0.10, 0.07, 1.7 * g, WARM))                  # broad bright flange band
        B.append(((0, 0, 1), el + 0.24, 0.015, 1.2 * g, WARM))                 # its thin upper lip
        B.append(((0, 0, 1), el - 0.22, 0.035, 1.0 * g, WARM))                 # fainter lower flange (dark gap between)
        pa = _n(md + up * 0.40 - rt * 0.35)
        B.append((pa, math.cos(math.radians(11)), 0.018, 2.4 * g, WARM))       # lit port rim
        B.append((pa, 1.0, 0.012, 0.6 * g, COOL))
        B.append((_n(rt + md * 0.25), 0.0, 0.03, 1.1 * g, COOL))              # port-tube streak (near vertical)
    if violet > 0:
        B.append(((-0.4, 0.6, -0.5), 1.0, 0.35, violet, (0.55, 0.45, 0.9)))
    return B


def env_r25(name, centre, radius, bands, parent=None, base=BASE):
    import source_r23_tin as T23
    mb = K.MB()
    mb.sphere((0, 0, 0), radius, 96)
    ob = mb.obj(name, T23._env_mat_r23(name + "Mat", bands, base, 1.0, radius))
    for p in ob.data.polygons:
        p.use_smooth = True
    if parent is not None:
        ob.parent = parent
        ob.location = (0, 0, 0)
    else:
        ob.location = centre
    ob.visible_camera = False
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_volume_scatter = False
    ob.visible_transmission = False
    return ob
