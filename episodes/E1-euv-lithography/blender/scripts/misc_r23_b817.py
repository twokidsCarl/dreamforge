"""R23 B8_17 (R23_ROOT_CAUSE row 5, material: wafer read). Owned by the misc sub-agent. Layered on misc_b817_r22.

R22 review: 「晶圆像浅灰瓷砖，没有硅片镜面感…改法：晶圆换深色镜面+彩虹衍射以外的冷灰反射」. Not repeating the R22 mirror silicon +
full environment reflection (blotches) nor the R21 flat light-grey grid.
- FieldR20 (the 188 counter-synced fields, R22 logic kept: field k exposed iff k < counter(f), slit fixed / stage moves):
  unexposed = dark polished silicon; exposed = dark silicon carrying an in-field micro pattern (4 x 3 dies per field,
  each with fine cool-grey line structure) -> exposed fields read as "printed chips" instead of light tiles.
  Dielectric specular (metallic 0, rough 0.16-0.24) -> the environment only gives a faint cool sheen, no blotches.
- ONE grazing highlight band: a single long thin area light, light-linked to the wafer + fields only, placed by mirror
  geometry so its reflection is one cool-white strip across the wafer for the camera (re-solved per frame).
- plain wafer under/between the fields: dark silicon (no metallic env mirror).
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

BAND_W, BAND_L, BAND_E = 0.03, 7.0, 220.0   # spec 0.25: env reflections ~2.4x dimmer (R23 smoke f56 mirrored the cabinets)


def _op(N, L, op, a, b):
    m = N.new("ShaderNodeMath")
    m.operation = op
    for k, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            m.inputs[k].default_value = x
        else:
            L.new(x, m.inputs[k])
    return m.outputs[0]


def _material():
    import kit_r2 as K
    m = bpy.data.materials.get("FieldR20")
    if m is None:
        return False
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    mix = next(x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA")
    bs = next(x for x in N if x.type == "BSDF_PRINCIPLED")
    exposed = mix.inputs["Factor"].links[0].from_socket
    cs = next(x for x in N if x.bl_idname == "ShaderNodeSeparateXYZ" and x.inputs[0].links
              and getattr(x.inputs[0].links[0].from_node, "uv_map", "") == "Cell")
    # in-field micro pattern: 4 x 3 dies (scribe gaps) + fine horizontal / vertical line structure inside each die
    dx = _op(N, L, "FRACT", _op(N, L, "MULTIPLY", cs.outputs["X"], 4.0), 0.0)
    dy = _op(N, L, "FRACT", _op(N, L, "MULTIPLY", cs.outputs["Y"], 3.0), 0.0)
    gx = _op(N, L, "LESS_THAN", _op(N, L, "MINIMUM", dx, _op(N, L, "SUBTRACT", 1.0, dx)), 0.04)
    gy = _op(N, L, "LESS_THAN", _op(N, L, "MINIMUM", dy, _op(N, L, "SUBTRACT", 1.0, dy)), 0.05)
    scribe = _op(N, L, "MAXIMUM", gx, gy)
    lx = _op(N, L, "GREATER_THAN", _op(N, L, "SINE", _op(N, L, "MULTIPLY", dx, 2 * math.pi * 9.0), 0.0), 0.55)
    ly = _op(N, L, "GREATER_THAN", _op(N, L, "SINE", _op(N, L, "MULTIPLY", dy, 2 * math.pi * 14.0), 0.0), 0.7)
    blk = _op(N, L, "GREATER_THAN", _op(N, L, "SINE", _op(N, L, "ADD", _op(N, L, "MULTIPLY", dx, 2 * math.pi * 2.0),
                                                                     _op(N, L, "MULTIPLY", dy, 2 * math.pi * 1.0)), 0.0), 0.2)
    lines = _op(N, L, "MAXIMUM", _op(N, L, "MULTIPLY", lx, 0.6), _op(N, L, "MULTIPLY", ly, blk))
    patt = _op(N, L, "MULTIPLY", _op(N, L, "SUBTRACT", 1.0, scribe), _op(N, L, "ADD", 0.7, _op(N, L, "MULTIPLY", lines, 0.3)))
    pm = N.new("ShaderNodeMix")
    pm.data_type = "RGBA"
    pm.inputs["A"].default_value = (*K.lin((0.035, 0.038, 0.048)), 1)       # scribe / substrate
    pm.inputs["B"].default_value = (*K.lin((0.24, 0.25, 0.31)), 1)          # printed structure (cool grey)
    L.new(patt, pm.inputs["Factor"])
    mix.inputs["A"].default_value = (*K.lin((0.045, 0.048, 0.058)), 1)      # unexposed: dark polished silicon
    L.new(pm.outputs["Result"], mix.inputs["B"])
    bs.inputs["Metallic"].default_value = 0.0
    try:
        bs.inputs["Specular IOR Level"].default_value = 0.25
    except KeyError:
        pass
    rr = next((x for x in N if x.type == "MAP_RANGE" and abs(x.inputs["To Max"].default_value - 0.55) < 1e-6), None)
    if rr is not None:
        rr.inputs["To Min"].default_value = 0.05
        rr.inputs["To Max"].default_value = 0.08
    return True


def _band(sc, cam, objs):
    fo = bpy.data.objects.get("FieldsR20")
    n = sc.frame_end
    ld = bpy.data.lights.new("WaferBandR23", "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y, ld.energy = BAND_W, BAND_L, BAND_E
    ld.color = (0.88, 0.93, 1.0)
    lo = bpy.data.objects.new("WaferBandR23", ld)
    sc.collection.objects.link(lo)
    lo.visible_camera = False
    lo.visible_diffuse = False
    try:
        rc = bpy.data.collections.new("WaferBandRecvR23")
        for o in objs:
            rc.objects.link(o)
        lo.light_linking.receiver_collection = rc
    except Exception as e:
        print("[R23 B8_17] band light link failed", e)
    nrm = Vector((0, 0, 1))
    step = max(1, n // 24)
    for f in list(range(1, n + 1, step)) + [n]:
        sc.frame_set(f)
        wz = (fo.matrix_world @ Vector((0, 0, 0.0096))).z
        C = cam.matrix_world.translation.copy()
        X = Vector((WC[0], WC[1], wz))
        d = (X - C).normalized()
        r = d - 2 * d.dot(nrm) * nrm
        E = X + r * 3.0
        lo.location = E
        z = r.normalized()                               # area light emits along local -Z -> local +Z points away from X
        y = nrm.cross(r).normalized()                    # long axis across the plane of incidence
        y = (y - y.dot(z) * z).normalized()
        x = y.cross(z)
        lo.rotation_euler = Matrix((x, y, z)).transposed().to_quaternion().to_euler()
        lo.keyframe_insert("location", frame=f)
        lo.keyframe_insert("rotation_euler", frame=f)
    sc.frame_set(1)
    return lo


WC = (0.0, 0.0)


def post(sc):
    global WC
    ok = _material()
    wo = bpy.data.objects.get("Wafer")
    import kit_r2 as K
    if wo is not None:
        wo.data.materials[0] = K.mat("WaferDarkR23", (0.045, 0.048, 0.058), metal=0.0, rough=0.05, spec=0.25)
    cam = sc.camera
    fo = bpy.data.objects.get("FieldsR20")
    if fo is None:
        print("[R23 B8_17] FieldsR20 missing - band skipped")
        return
    # band centre: the wafer centre at the 55 % frame, shifted toward the camera half (reads as a grazing streak)
    sc.frame_set(round(sc.frame_end * 0.55))
    c = fo.matrix_world @ Vector((0, 0, 0.0096))
    WC = (c.x, c.y)
    objs = [o for o in (fo, wo) if o is not None]
    lo = _band(sc, cam, objs)
    from bpy_extras.object_utils import world_to_camera_view as w2c
    for f in (56, 122, 189):
        sc.frame_set(min(f, sc.frame_end))
        v = w2c(sc, cam, Vector((WC[0], WC[1], c.z)))
        print(f"[R23 B8_17] f{f} band point screen ({v.x * 960:.0f},{(1 - v.y) * 540:.0f}) material={ok}")
    sc.frame_set(1)
