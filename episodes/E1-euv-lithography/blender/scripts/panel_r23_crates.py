"""R23 panel agent, A0_03 (root-cause rows 2 + 4).
Row 4: the counts sit on 3D objects in front of the plate: a stencilled wooden crate stack (250+), an aluminium ULD
(43) and a truck-trailer rear (20). Row 2: the ortho camera (no parallax possible on a flat card) becomes a 50 mm
perspective camera that dollies (distance = ortho width * 50/36, so the plate framing is the R22 one) while it trucks;
the 3D foreground at ~10 m vs the plate at ~17 m slides past the plate -> real parallax.
"""
import math

import bpy

import common as C

LENS, SENSOR = 50.0, 36.0
FG_Z = 6.5                       # foreground plane (plate at z = 0, camera z ~ 18.9 -> 16.1)


def _mat(name, col, rough=0.6, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m


def _box(name, ctr, size, mat, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=ctr)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        md = o.modifiers.new("bv", "BEVEL")
        md.width = bevel
        md.segments = 2
    return o


def _cyl(name, ctr, r, depth, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=ctr, rotation=rot, vertices=24)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o


def _text(name, body, ctr, size, mat):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = size
    cu.extrude = 0.004
    try:
        cu.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", check_existing=True)
    except Exception:
        pass
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.location = ctr
    o.data.materials.append(mat)
    return o


CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
TOP = -0.35                      # top of the foreground row (world y); labels sit just under it, above the subtitle band


def _label(tag, num, word, cx, cy, zf, plate_col, w=1.5):
    ink = _mat("R23Ink" + tag, (0.02, 0.02, 0.025), 0.9)
    _box("R23Lab" + tag, (cx, cy, zf), (w, 0.66, 0.012), _mat("R23LabM" + tag, plate_col, 0.7), 0.0)
    _text("R23N" + tag, num, (cx, cy + 0.1, zf + 0.012), 0.4, ink)
    t = _text("R23W" + tag, word, (cx, cy - 0.2, zf + 0.012), min(0.3, (w - 0.12) / len(word)), ink)
    try:
        t.data.font = bpy.data.fonts.load(CJK, check_existing=True)
    except Exception:
        pass


def _crates(z):
    wood = _mat("R23Wood", (0.42, 0.27, 0.14), 0.75)
    batten = _mat("R23Batten", (0.30, 0.19, 0.10), 0.8)
    cw, ch, cd = 0.62, 0.44, 0.7
    x0 = -3.55
    for i in range(4):
        for j in range(6):
            cx, cy = x0 + cw / 2 + i * (cw + 0.02), TOP - ch / 2 - j * (ch + 0.02) - (0.25 if i in (0, 3) else 0)
            zz = z - 0.05 * ((i + j) % 2)
            _box(f"R23Crate{i}{j}", (cx, cy, zz), (cw, ch, cd), wood, 0.012)
            for dy in (-ch / 2 + 0.05, ch / 2 - 0.05):
                _box(f"R23Bat{i}{j}{dy:+.1f}", (cx, cy + dy, zz + cd / 2 + 0.01), (cw, 0.06, 0.02), batten, 0.004)
    _label("250", "250+", "个板条箱", x0 + 1.28, TOP - 0.45, z + cd / 2 + 0.04, (0.86, 0.78, 0.56))


def _uld(z):
    alu = _mat("R23Alu", (0.62, 0.64, 0.66), 0.38, 0.55)
    rib = _mat("R23AluRib", (0.45, 0.47, 0.5), 0.4, 0.6)
    cx, w, h, d = 0.35, 1.7, 2.6, 1.4
    zf = z - 0.3
    _box("R23ULD", (cx, TOP - h / 2 + 0.15, zf), (w, h, d), alu, 0.04)
    for k in range(4):
        _box(f"R23ULDrib{k}", (cx - w / 2 + 0.18 + k * 0.45, TOP - h / 2 + 0.15, zf + d / 2 + 0.01), (0.05, h, 0.03), rib, 0.005)
    _label("43", "43", "个航空集装箱", cx, TOP - 0.45, zf + d / 2 + 0.04, (0.95, 0.66, 0.14), 1.62)


def _trailer(z):
    shell = _mat("R23Trailer", (0.78, 0.80, 0.82), 0.45)
    dark = _mat("R23Tyre", (0.02, 0.02, 0.02), 0.85)
    red = _mat("R23Tail", (0.4, 0.02, 0.01), 0.4, emit=(1.0, 0.05, 0.02), es=6.0)
    cx, w, h = 3.05, 1.4, 2.4
    zf = z + 0.3
    yc = TOP + 0.1 - h / 2
    _box("R23Trl", (cx, yc, zf - 1.5), (w, h, 3.0), shell, 0.03)
    _box("R23TrlSeam", (cx, yc, zf + 0.005), (0.025, h - 0.1, 0.02), dark, 0.0)
    for s in (-1, 1):
        _box(f"R23TrlTail{s}", (cx + s * (w / 2 - 0.12), TOP - 1.0, zf + 0.01), (0.16, 0.12, 0.03), red, 0.005)
        for yy in (TOP - 0.15, TOP - 1.2):                                   # door hinges -> reads as a box-truck rear
            _box(f"R23TrlHinge{s}{yy:.2f}", (cx + s * (w / 2 - 0.05), yy, zf + 0.012), (0.08, 0.05, 0.03), dark, 0.003)
    _box("R23TrlBumper", (cx, TOP - 1.18, zf + 0.06), (w + 0.04, 0.09, 0.08), dark, 0.01)
    _label("20", "20", "辆卡车", cx, TOP - 0.45, zf + 0.04, (0.92, 0.92, 0.9), 1.25)


def _lights(z):
    bpy.ops.object.light_add(type="AREA", location=(1.0, 2.5, z + 6.0))
    k = bpy.context.object
    k.name = "R23KeySodium"
    k.data.energy = 900
    k.data.size = 4.0
    k.data.color = (1.0, 0.72, 0.42)
    k.rotation_euler = (math.radians(-25), 0, 0)                    # mostly toward -Z (onto front faces), from above
    bpy.ops.object.light_add(type="AREA", location=(-3.0, -1.0, z + 5.0))
    f = bpy.context.object
    f.name = "R23FillCool"
    f.data.energy = 160
    f.data.size = 5.0
    f.data.color = (0.55, 0.65, 1.0)
    f.rotation_euler = (0, math.radians(-25), 0)


def _perspective(sc):
    cam = sc.camera
    cam.data.type = "PERSP"
    cam.data.lens = LENS
    cam.data.sensor_width = SENSOR
    cam.data.sensor_fit = "HORIZONTAL"
    dfc = cam.data.animation_data and cam.data.animation_data.action
    ws = {}
    if dfc:
        for fc in C.fcurves(dfc):
            if fc.data_path == "ortho_scale":
                ws = {kp.co[0]: kp.co[1] for kp in fc.keyframe_points}
    for fc in C.fcurves(cam.animation_data.action):
        if fc.data_path == "location" and fc.array_index == 2:
            for kp in fc.keyframe_points:
                w = ws.get(kp.co[0], 13.6)
                v = w * LENS / SENSOR                                  # same plate width as the R22 ortho frame
                dv = v - kp.co[1]
                kp.co[1] = v
                kp.handle_left[1] += dv
                kp.handle_right[1] += dv
            fc.update()
    cam.data.clip_end = 200


def post(sc, variant, shot):
    _perspective(sc)
    _crates(FG_Z)
    _uld(FG_Z)
    _trailer(FG_Z)
    _lights(FG_Z)
