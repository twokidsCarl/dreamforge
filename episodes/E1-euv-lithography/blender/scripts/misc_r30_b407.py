"""R30 row 6c, B4_07 (misc_r30.B407_R30). R29 p3 「镜体像一块奶酪轮，底座只有一圈螺栓。镜底加冷却管束和三点柔性支撑，
切面做出抛光基底和膜层的分界」:
- three bipod flexure mounts (two struts with necked notch hinges, foot bolted on the mount ring, pad clamped to the
  blank rim) at 120 deg;
- a cooling-tube bundle: manifold under the blank, 5 parallel tubes with clamps running out under the wedge gap and
  dropping through the mount ring;
- cut face: polished substrate below, a dark interface line, the coating as a thin proud lip on top (real geometry).
Beams, landing spot, anchors, the R28 body material and the Mo/Si inset are untouched (R29 sandblast NOT used)."""
import math

import bpy
import bmesh
from mathutils import Vector

import kit_r2 as K

R, SAG_R, TH = 1.2, 6.0, 0.4
A_CUT0, A_CUT1 = math.radians(-35), math.radians(25)
FLEX_ANG = (-52.0, 68.0, 188.0)
COAT_T = 0.016            # coating band thickness on the cut face (= r2_misc band threshold)
IFACE_T = 0.016           # dark interface line below the coating
LIP = 0.006               # coating lip stands proud of the cut plane
SUB_COL, SUB_ROUGH = (0.30, 0.295, 0.29), 0.1


def _ztop(r):
    return SAG_R - math.sqrt(SAG_R * SAG_R - r * r)


def _flexures(M):
    st, nk, ft = K.MB(), K.MB(), K.MB()
    for ad in FLEX_ANG:
        a = math.radians(ad)
        u = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-math.sin(a), math.cos(a), 0))
        foot = u * (R + 0.11) + Vector((0, 0, -0.35))
        pad = u * (R + 0.04) + Vector((0, 0, -0.16))
        ft.box(foot, (0.14, 0.36, 0.05), (0, 0, a))                          # foot plate on the mount ring
        ft.box(pad, (0.07, 0.16, 0.13), (0, 0, a))                           # pad clamped to the blank rim
        for s in (-1, 1):
            p0 = foot + t * 0.13 * s + Vector((0, 0, 0.025))
            p1 = pad + t * 0.045 * s + u * 0.02 + Vector((0, 0, -0.06))
            d = p1 - p0
            q = [p0, p0 + d * 0.14, p0 + d * 0.22, p0 + d * 0.78, p0 + d * 0.86, p1]
            st.tube(q[0], q[1], 0.02, seg=14)
            nk.tube(q[1], q[2], 0.008, seg=12)                               # notch hinge (necked)
            st.tube(q[2], q[3], 0.02, seg=14)
            nk.tube(q[3], q[4], 0.008, seg=12)
            st.tube(q[4], q[5], 0.02, seg=14)
            ft.cyl(foot + t * 0.13 * s + u * 0.04 + Vector((0, 0, 0.03)), 0.018, 0.014, seg=12)   # foot screws
        ft.cyl(pad + u * 0.04, 0.02, 0.02, rot=(0, math.radians(90), a), seg=12)                 # clamp screw
    ti = K.mat("FlexTiR30", (0.62, 0.63, 0.66), metal=1.0, rough=0.28, brushed=0.06)
    return [st.obj("FlexStrutsR30", ti, bevel=0.002), nk.obj("FlexNotchR30", K.mat("FlexNotchR30M", (0.2, 0.2, 0.22),
            metal=1.0, rough=0.35)), ft.obj("FlexFeetR30", ti, bevel=0.004)]


def _bundle(M):
    cu, ss, cl = K.MB(), K.MB(), K.MB()
    am = math.radians(-5.0)                                    # runs out under the wedge gap (camera side)
    u = Vector((math.cos(am), math.sin(am), 0))
    t = Vector((-math.sin(am), math.cos(am), 0))
    cl.cyl(Vector((0, 0, -0.44)), 0.2, 0.06, seg=40)            # manifold under the blank
    for k in range(5):
        off = t * (0.04 * (k - 2))
        z = -0.47 - 0.004 * abs(k - 2)
        pts = [off + u * 0.12 + Vector((0, 0, -0.44)), off + u * 0.3 + Vector((0, 0, z)),
               off + u * 0.78 + Vector((0, 0, z)), off + u * 0.9 + Vector((0, 0, z - 0.08)),
               off + u * 0.94 + Vector((0, 0, z - 0.3)), off + u * 0.95 + Vector((0, 0, -1.15))]
        (cu if k % 2 == 0 else ss).path(pts, 0.015, seg=12)
    for r_ in (0.42, 0.68):                                     # bundle clamps
        cl.box(u * r_ + Vector((0, 0, -0.475)), (0.04, 0.24, 0.05), (0, 0, am))
    cl.box(u * 0.94 + Vector((0, 0, -0.75)), (0.06, 0.24, 0.04), (0, 0, am))
    return [cu.obj("CoolBundleCuR30", M["copper"]), ss.obj("CoolBundleSsR30", K.mat("CoolSsR30", (0.72, 0.73, 0.76),
            metal=1.0, rough=0.2)), cl.obj("CoolClampsR30", M["steel"], bevel=0.004)]


def _lip(sc):
    """Coating lip on both cut faces: a thin strip COAT_T high, LIP proud of the cut plane, following the top sag."""
    bm = bmesh.new()
    for a, sgn in ((A_CUT0, 1), (A_CUT1, -1)):
        u = Vector((math.cos(a), math.sin(a), 0))
        nrm = Vector((-math.sin(a), math.cos(a), 0)) * sgn      # face normal into the gap
        rows = []
        N = 40
        for i in range(N + 1):
            r = 0.04 + (R - 0.04) * i / N
            zt = _ztop(r)
            base = u * r
            rows.append([bm.verts.new(base + Vector((0, 0, zt + 0.001))),
                         bm.verts.new(base + nrm * LIP + Vector((0, 0, zt + 0.001))),
                         bm.verts.new(base + nrm * LIP + Vector((0, 0, zt - COAT_T))),
                         bm.verts.new(base + Vector((0, 0, zt - COAT_T)))])
        for i in range(N):
            for k in range(3):
                bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]))
        bm.faces.new(rows[N])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("CoatLipR30")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("CoatLipR30", me)
    sc.collection.objects.link(ob)
    m = K.mat("CoatLipR30M", (0.86, 0.84, 0.95), metal=1.0, rough=0.12)
    b = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Emission Color"].default_value = (0.85, 0.85, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 1.6
    me.materials.append(m)
    return ob


def _cut_face(cut):
    """Substrate polished (glossy, clear-coated), dark interface line between substrate and coating band."""
    nt = cut.node_tree
    nn, l = nt.nodes, nt.links
    b = next(x for x in nn if x.type == "BSDF_PRINCIPLED")
    band = next(x for x in nn if x.type == "MATH" and x.operation == "LESS_THAN")
    mix = next(x for x in nn if x.type == "MIX" and x.data_type == "RGBA")
    mix.inputs["A"].default_value = (*K.lin(SUB_COL), 1)
    b.inputs["Roughness"].default_value = SUB_ROUGH
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.8
        b.inputs["Coat Roughness"].default_value = 0.03
    for x in nn:
        if x.type == "BUMP":
            x.inputs["Strength"].default_value = 0.02
    dz = band.inputs[0].links[0].from_socket
    lo = nn.new("ShaderNodeMath")
    lo.operation = "LESS_THAN"
    lo.inputs[1].default_value = COAT_T + IFACE_T
    l.new(dz, lo.inputs[0])
    ln = nn.new("ShaderNodeMath")
    ln.operation = "SUBTRACT"
    l.new(lo.outputs[0], ln.inputs[0])
    l.new(band.outputs[0], ln.inputs[1])
    dk = nn.new("ShaderNodeMix")
    dk.data_type = "RGBA"
    dk.inputs["B"].default_value = (0.012, 0.012, 0.016, 1)
    l.new(ln.outputs[0], dk.inputs["Factor"])
    l.new(mix.outputs["Result"], dk.inputs["A"])
    l.new(dk.outputs["Result"], b.inputs["Base Color"])


def apply(sc):
    mir = bpy.data.objects.get("MirrorCap")
    if mir is None:
        print("[R30 B4_07] MirrorCap missing", flush=True)
        return
    M = K.palette()
    _cut_face(mir.data.materials[2])
    obs = _flexures(M) + _bundle(M) + [_lip(sc)]
    for ob in obs:
        ob.visible_glossy = ob.name.startswith("CoatLip")      # new parts do not add shapes to the coating reflection
    print(f"[R30 B4_07] B407_R30: 3 bipod flexures, 5-tube cooling bundle, cut-face substrate/coating boundary "
          f"({len(obs)} objs)", flush=True)
