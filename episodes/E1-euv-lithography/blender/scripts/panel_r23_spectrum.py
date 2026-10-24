"""R23 panel agent, B1_18 (root-cause row 4): the spectrum becomes a 3D bar array standing in front of the source
chamber (camera-parented, ~half the frame width, in the focal plane; chamber + plasma fall out of focus behind it).
Bars = stacked Sn8+..Sn14+ lines in 0.1 nm bins, cool blue -> violet by charge state (violet = EUV), grown one by one
(ion by ion); the +-1 % mirror window is a cyan 3D gate. Text (title / ticks / legend) comes from r2_ov_zz23p at the
screen positions given by GEOM below (shared constants, the overlay re-derives them from this file's numbers)."""
import random

try:
    import bpy
except ImportError:          # the overlay (r2_ov_zz23p) imports this file for its geometry constants only
    bpy = None

D = 0.5                    # chart plane distance in front of the camera (m)
LENS, SENSOR = 26.0, 36.0
X0, X1 = -0.315, 0.03      # chart x range at D (camera space, m)
YB, HMAX = -0.075, 0.19    # baseline y and max stack height
LO, HI, BIN = 11.0, 17.0, 0.075
ICOL = [(0.04, 0.22, 1.0), (0.09, 0.18, 1.0), (0.15, 0.14, 1.0), (0.22, 0.11, 1.0), (0.30, 0.09, 1.0),
        (0.38, 0.07, 1.0), (0.46, 0.05, 1.0)]
TICKS = (11, 12, 13.5, 15, 17)
F0, FK, FR, FD = 8, 21, 12, 8      # growth: start, frames per ion, random spread within an ion, grow duration


def X(nm):
    return X0 + (nm - LO) / (HI - LO) * (X1 - X0)


def _emis(name, col, s):
    m = bpy.data.materials.new(name)          # pure emission: no lit specular washing the ion colours to white
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = s
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def _bar(name, x, y0, w, h, z, mat, parent):
    me = bpy.data.meshes.new(name)
    hw = w / 2
    v = [(-hw, 0, -0.001), (hw, 0, -0.001), (hw, h, -0.001), (-hw, h, -0.001),
         (-hw, 0, 0.001), (hw, 0, 0.001), (hw, h, 0.001), (-hw, h, 0.001)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.parent = parent
    o.location = (x, y0, z)
    return o


def counts():
    rnd = random.Random(7)
    bins = {}
    for i in range(3000):                       # "thousands of lines": 3000 lines, 82 % piled around 13.5 nm
        nm = rnd.gauss(13.5, 0.28) if rnd.random() < 0.82 else rnd.uniform(11.05, 16.95)
        if LO < nm < HI:
            b = int((nm - LO) / BIN)
            bins.setdefault(b, [0] * 7)[i % 7] += 1
    return bins


def post(sc, variant, shot):
    cam = sc.camera
    rig = bpy.data.objects.new("R23SpecRig", None)
    sc.collection.objects.link(rig)
    rig.parent = cam
    rig.location = (0, 0, -D)
    cam.data.dof.focus_object = rig
    cam.data.dof.aperture_fstop = 2.0
    mats = [_emis(f"R23Ion{k}", c, 1.0) for k, c in enumerate(ICOL)]
    cyan = _emis("R23Win", (0.1, 0.85, 0.95), 2.0)
    gate = _emis("R23WinFill", (0.02, 0.2, 0.25), 0.12)
    white = _emis("R23Axis", (0.8, 0.82, 0.88), 1.5)
    bins = counts()
    top = max(sum(c) for c in bins.values())
    rnd = random.Random(118)
    w = BIN / (HI - LO) * (X1 - X0) * 0.78
    for b, cs in sorted(bins.items()):
        x = X(LO + (b + 0.5) * BIN)
        y = YB
        for k, c in enumerate(cs):
            if not c:
                continue
            h = HMAX * c / top
            o = _bar(f"R23Line{b:03d}_{k}", x, y, w, h, 0.0, mats[k], rig)
            f0 = int(F0 + k * FK + rnd.random() * FR)
            o.scale = (1, 0.0, 1)                     # not started: zero height AND hidden (no floating dash)
            o.keyframe_insert("scale", frame=f0)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f0)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f0 + 1)
            o.scale = (1, 1, 1)
            o.keyframe_insert("scale", frame=f0 + FD)
            # stacked: rides on the lower ions' growth -> the base of this segment is static (lower ions finish first)
            y += h
    # +-1 % mirror window: cyan gate (two posts + faint fill behind the bars) and the axis
    xa, xb = X(13.5 * 0.99), X(13.5 * 1.01)
    for nm_x in (xa, xb):
        _bar(f"R23WinPost{nm_x:.3f}", nm_x, YB, 0.0022, HMAX * 1.08, 0.002, cyan, rig)   # two thin gate lines, no fill
    _bar("R23Axis", (X0 + X1) / 2, YB - 0.0022, X1 - X0 + 0.01, 0.0022, 0.0, white, rig)
    for nm in TICKS:
        _bar(f"R23Tick{nm}", X(nm), YB - 0.008, 0.0022, 0.006, 0.0, cyan if nm == 13.5 else white, rig)
