"""R29 row 6, B4_07 (misc_r29.B407_R29): sand-blasted glass-ceramic body + 3 flexure hinges + cooling line + a
defocused vacuum-chamber wall corner behind. Never touches beams, landing spot, coating, anchors or the inset."""
import math

import bpy
from mathutils import Vector

import kit_r2 as K

R, TH = 1.2, 0.4
CER_COL = (0.42, 0.41, 0.39)      # sRGB, light warm grey glass-ceramic (not white plaster, not dark plastic)
CER_ROUGH = 0.5
GRAIN = 140.0                     # sand-blast grain scale (object units)
GRAIN_BUMP = 0.5
BEVEL_R = 0.022                   # shader bevel -> thin edge highlight on every body edge
HINGE_ANG = (55.0, 175.0, -65.0)  # degrees (wedge gap is -35..25 at +x, cameras look from +x)
WALL_X, SIDE_Y = -2.7, -3.2       # chamber corner (back wall faces +x, side wall faces +y)
WALL_LIGHT = 5.0


def _grain_normal(nt, b, target_bump=None):
    nn, l = nt.nodes, nt.links
    tc = nn.new("ShaderNodeTexCoord")
    nz = nn.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = GRAIN
    nz.inputs["Detail"].default_value = 2.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    bev = nn.new("ShaderNodeBevel")
    bev.samples = 8
    bev.inputs["Radius"].default_value = BEVEL_R
    bp = target_bump
    if bp is None:
        bp = nn.new("ShaderNodeBump")
        l.new(bp.outputs["Normal"], b.inputs["Normal"])
    bp.inputs["Strength"].default_value = GRAIN_BUMP
    for lk in list(bp.inputs["Height"].links):
        l.remove(lk)
    l.new(nz.outputs["Fac"], bp.inputs["Height"])
    l.new(bev.outputs["Normal"], bp.inputs["Normal"])
    # micro-rough: roughness varies a little with the grain (sparkle, not a flat matte)
    mr = nn.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = CER_ROUGH - 0.12
    mr.inputs["To Max"].default_value = CER_ROUGH + 0.08
    l.new(nz.outputs["Fac"], mr.inputs["Value"])
    l.new(mr.outputs["Result"], b.inputs["Roughness"])
    return nz


def _ceramic_side():
    m = K.mat("SandCeramicR29", CER_COL, rough=CER_ROUGH, speck=0.35)
    b = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    lk = b.inputs["Normal"].links
    bump = lk[0].from_node if lk and lk[0].from_node.type == "BUMP" else None
    _grain_normal(m.node_tree, b, bump)
    for k, v in (("Subsurface Weight", 0.12), ("Subsurface Scale", 0.03), ("Coat Weight", 0.0)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def _ceramic_cut(cut):
    nt = cut.node_tree
    b = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED")
    mix = next(x for x in nt.nodes if x.type == "MIX" and x.data_type == "RGBA")
    mix.inputs["A"].default_value = (*K.lin(CER_COL), 1)
    lk = b.inputs["Normal"].links
    bump = lk[0].from_node if lk and lk[0].from_node.type == "BUMP" else None
    _grain_normal(nt, b, bump)
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.12


def _flexures(M):
    fx, fb = K.MB(), K.MB()
    mt = K.mat("FlexureTiR29", (0.66, 0.67, 0.7), metal=1.0, rough=0.32, brushed=0.06)
    for ad in HINGE_ANG:
        a = math.radians(ad)
        u = Vector((math.cos(a), math.sin(a), 0))
        rot = (0, 0, a)
        base_c = u * (R + 0.07)
        fx.box(base_c + Vector((0, 0, -0.38)), (0.14, 0.2, 0.07), rot)          # foot on the mount ring
        fx.box(base_c + Vector((0, 0, -0.325)), (0.018, 0.16, 0.04), rot)      # lower blade neck
        fx.box(base_c + Vector((0, 0, -0.27)), (0.1, 0.17, 0.07), rot)          # middle link
        fx.box(base_c + Vector((0, 0, -0.215)), (0.018, 0.16, 0.04), rot)      # upper blade neck
        fx.box(u * (R + 0.04) + Vector((0, 0, -0.16)), (0.1, 0.19, 0.07), rot)  # pad clamped to the blank
        for s in (-1, 1):                                                         # two screws on the foot
            t = Vector((-math.sin(a), math.cos(a), 0)) * 0.065 * s
            fb.cyl(base_c + t + Vector((0, 0, -0.343)), 0.016, 0.012, seg=12)
    o1 = fx.obj("FlexureHingesR29", mt, bevel=0.006)
    o2 = fb.obj("FlexureScrewsR29", M["steel"])
    return [o1, o2]


def _cooling(M):
    cl, ft = K.MB(), K.MB()
    pts = []
    a0, a1, zc, rc = -150.0, 150.0, -0.47, R + 0.27
    for i in range(37):
        a = math.radians(a0 + (a1 - a0) * i / 36)
        pts.append(Vector((rc * math.cos(a), rc * math.sin(a), zc)))
    cl.path(pts, 0.028, seg=12)
    for a_ in (a0, a1):                                       # supply / return leave downward out of frame
        a = math.radians(a_)
        p = Vector((rc * math.cos(a), rc * math.sin(a), zc))
        cl.path([p, p + Vector((0.15 * math.cos(a), 0.15 * math.sin(a), -0.15)),
                 p + Vector((0.25 * math.cos(a), 0.25 * math.sin(a), -0.8))], 0.028, seg=12)
    for ad in HINGE_ANG:                                      # one branch + fitting into each flexure foot
        a = math.radians(ad)
        u = Vector((math.cos(a), math.sin(a), 0))
        p0 = u * rc + Vector((0, 0, zc))
        p1 = u * (R + 0.15) + Vector((0, 0, -0.38))
        cl.tube(p0, p1, 0.016, seg=10)
        ft.tube(p0 - u * 0.03, p0 + u * 0.03, 0.042, seg=16)  # tee fitting on the loop
        ft.tube(p1 - u * 0.02, p1 + u * 0.03, 0.026, seg=12)  # fitting at the foot
    o1 = cl.obj("CoolingLineR29", K.mat("CoolTubeR29", (0.7, 0.71, 0.74), metal=1.0, rough=0.18))
    o2 = ft.obj("CoolFittingsR29", M["steel"], bevel=0.003)
    return [o1, o2]


_DIM = {}


def _dim(m):
    if m.name not in _DIM:
        d = m.copy()
        b = next((x for x in d.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
        if b is not None:
            c = b.inputs["Base Color"].default_value
            if not b.inputs["Base Color"].links:
                b.inputs["Base Color"].default_value = (c[0] * 0.45, c[1] * 0.45, c[2] * 0.45, 1)
            if not b.inputs["Roughness"].links:
                b.inputs["Roughness"].default_value = max(0.45, b.inputs["Roughness"].default_value)
        _DIM[m.name] = d
    return _DIM[m.name]


def _wall(sc):
    import kit_r27 as KR
    import hero_kit_r10 as H
    out = []
    # back wall (faces +x) and side wall (faces +y) of the vacuum chamber, built in the kit's x-z frame facing -y
    for tag, kinds, rotz, loc, x0, x1 in (
            ("ChamberBackR29", ("viewport_stack", "gate_valve", "turbo_gate"), math.radians(90), (WALL_X, 0.0, 0.0), -3.2, 3.2),
            ("ChamberSideR29", ("ion_pump", "viewport_stack"), math.radians(180), (0.0, SIDE_Y, 0.0), -2.7, 2.0)):
        P = H.new_parts()
        P["paint_grey"].box(((x0 + x1) / 2, 0.06, 0.8), (x1 - x0 + 0.3, 0.12, 4.2))      # wall skin
        for zr in (-1.05, 2.6):                                                          # flange ribs top / bottom
            P["brushed"].box(((x0 + x1) / 2, -0.04, zr), (x1 - x0 + 0.3, 0.1, 0.18))
        KR.named_row(P, x0 + 0.3, x1 - 0.3, -0.9, 1.7, 0.0, kinds=kinds, seed=29, scale=1.3, depth=1.2)
        emp = bpy.data.objects.new(tag, None)
        sc.collection.objects.link(emp)
        emp.location = loc
        emp.rotation_euler = (0, 0, rotz)
        for ob in KR.finish(P, tag):
            ob.parent = emp
            out.append(ob)
            if ob.name.endswith("paint_grey"):
                ob.data.materials[0] = K.mat("ChamberSkinR29", (0.16, 0.17, 0.19), metal=0.6, rough=0.45, brushed=0.1)
            else:                  # satin, dim: background parts must not glint brighter than the hero
                ob.data.materials[0] = _dim(ob.data.materials[0])
    # corner column where the two walls meet
    cc = K.MB()
    cc.box((WALL_X + 0.15, SIDE_Y + 0.15, 0.8), (0.5, 0.5, 4.2))
    out.append(cc.obj("ChamberCornerR29", K.mat("ChamberSteelR29", (0.42, 0.43, 0.45), metal=1.0, rough=0.35, brushed=0.1),
                      bevel=0.02))
    lt = K.area("ChamberWashR29", (WALL_X + 0.9, SIDE_Y + 0.9, 2.2), (WALL_X, SIDE_Y + 2.5, -0.5), 2.0, WALL_LIGHT,
                (0.8, 0.85, 1.0))
    lt.visible_camera = False
    lt.visible_glossy = False
    for ob in out:                 # the coating keeps its R28 reflection (no new shapes on the mirror face)
        ob.visible_glossy = False
    return out


def apply(sc):
    mir = bpy.data.objects.get("MirrorCap")
    if mir is None:
        print("[R29 B4_07] MirrorCap missing", flush=True)
        return
    mats = mir.data.materials
    mats[1] = _ceramic_side()
    _ceramic_cut(mats[2])
    M = K.palette()
    n = len(_flexures(M)) + len(_cooling(M)) + len(_wall(sc))
    print(f"[R29 B4_07] B407_R29: sand-blasted ceramic body, 3 flexures, cooling line, chamber corner ({n} objs)",
          flush=True)
