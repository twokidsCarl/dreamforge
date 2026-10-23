"""Round 17 (P1, R17_ROOT_CAUSE row 5: "hero bay / hero part sparse or fake") - parts for r2_cutaway only.

  po_fill(HP, mb, ...)   B7_06 (H13 "cage sparse: only two mirrors, three rings and some rods"): fills the barrel
                         between M5 and M6 with >= 5 nameable part types - M1..M4 mirror blanks seen from the BACK
                         (lightweighting ribs, ground substrate) in machined cells, three actuator cans + flexure
                         blades per cell, coolant supply / return hoses from every cell to the back wall, a cable
                         loom from every cell to the ceiling. All kept off the screen-space path of the beam.
  wafer_r17(...)         B8_03 ("wafer reads as black glass with white lines, on a white plate with a hole"): a
                         silicon wafer with a visible die map (small dies, partial edge dies left bare, device
                         texture inside every die, light metallic grey - not a black mirror) and a bevelled edge.
"""
import math

from mathutils import Vector

import kit_r2 as K

# (centre, radius) of M1..M4 in the B7_06 barrel frame (optical axis x = y = 0); see r2_cutaway._po_barrels_r15
PO_FILL = [((-0.6, 0.24, 2.36), 0.2), ((-0.4, 0.52, 1.98), 0.17), ((0.36, 0.58, 2.44), 0.17), ((0.71, 0.3, 1.97), 0.14)]


def _basis(n):
    n = Vector(n).normalized()
    up = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = up.cross(n).normalized()
    v = n.cross(u).normalized()
    return u, v, n


def po_fill(HP, mb, z_base, z_ceil, H15, HK):
    """mb: the _po_barrels_r15 batch dict (mface / medge / anod / steel / flange ...); HP: hero_kit parts."""
    for i, (c, r) in enumerate(PO_FILL):
        c = Vector(c)
        # the blank faces away from the lens (toward the axis / back wall): the camera sees its ribbed back
        n = Vector((-c.x * 1.5, 1.0, 0.12)).normalized()
        th = r * 0.42
        H15.disc_mirror(mb["mface"], mb["medge"], c, n, r, 0.0001 + r * 0.05, th, sag=0.004, chamfer=0.012, seg=64)
        u, v, _ = _basis(n)
        back = c - n * th
        # back: a raised rim ring + a hub boss (ground substrate), seen obliquely so the blank reads as a thick disc
        HK._ring(mb["medge"], back - n * 0.012, n, r * 0.98, r * 0.86, 0.024, seg=48)
        HK._cyl(mb["medge"], back - n * 0.012, n, r * 0.2, 0.024, seg=24)
        # machined cell ring behind the blank, bolt circle
        cell = back - n * 0.05
        HK._ring(HP["anod"], cell, n, r * 1.18, r * 1.02, 0.05, seg=64)
        HK._ring(HP["brushed"], c - n * th * 0.5, n, r * 1.08, r * 1.0, th * 0.7, seg=64)
        # three actuator cans + flexure blades at 120 deg
        for k in range(3):
            a = math.radians(90 + 120 * k)
            d = u * math.cos(a) + v * math.sin(a)
            p0 = cell + d * r * 1.1
            HK._cyl(HP["brushed"], p0 - n * 0.05, n, 0.028, 0.09, seg=16)                 # actuator can
            HK._cyl(HP["coil"], p0 - n * 0.11, n, 0.021, 0.04, seg=12)                    # motor
            HP["steel"].box(p0 + n * 0.03, (0.006, 0.006, 0.05), rot=(0, 0, 0))             # flexure blade
            HP["solenoid"].box(p0 - n * 0.06 + d * 0.035, (0.03, 0.02, 0.025))              # connector
        # coolant in / out (blue supply, white return) from the cell to the back wall
        wall = Vector((c.x * 1.25, 0.82, 0)).normalized() * 0.84
        for s, key in ((-1, "hose_b"), (1, "hose_w")):
            p0 = cell + u * s * r * 0.55
            HP[key].path([p0, p0 - n * 0.12 + Vector((0, 0, s * 0.03)),
                          Vector((wall.x, wall.y, c.z + s * 0.12))], 0.011, seg=10)
        # cable loom from the cell up to the ceiling
        top = Vector((wall.x * 0.95, wall.y * 0.95, z_ceil - 0.08))
        p0 = cell + v * r * 0.9
        HK.cable_harness(HP, [p0, p0 - n * 0.1 + Vector((0, 0, 0.12)), top], n=4, r=0.006)
        # strut from the cell to the barrel wall (the mount it hangs on)
        mb["anod"].tube(cell - n * 0.02, Vector((wall.x, wall.y, c.z)) * 1.0, 0.022, seg=12)


def wafer_mat_r17(name="WaferSiR17", R=0.42, pitch=0.042, street=0.09, edge=0.035):
    """Light metallic-grey polished silicon with a die map: small dies (pitch x 1.25 pitch), scribe streets, a
    device texture in every die (dense lines + pads + darker logic block), partial dies near the edge left bare
    (edge exclusion) - object space, wafer centre at the object origin."""
    m = K.mat(name, (0.5, 0.51, 0.55), metal=0.85, rough=0.16)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])

    def op(o, a, b_=None):
        nd = nt.nodes.new("ShaderNodeMath"); nd.operation = o
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                nt.links.new(v, nd.inputs[i])
        return nd.outputs[0]
    X, Y = sp.outputs["X"], sp.outputs["Y"]
    py = pitch * 1.25
    gx, gy = op("DIVIDE", X, pitch), op("DIVIDE", Y, py)
    fx, fy = op("FRACT", gx), op("FRACT", gy)
    # die centre radius -> inside (full die) or edge-excluded
    cx = op("MULTIPLY", op("ADD", op("FLOOR", gx), 0.5), pitch)
    cy = op("MULTIPLY", op("ADD", op("FLOOR", gy), 0.5), py)
    rc = op("SQRT", op("ADD", op("MULTIPLY", cx, cx), op("MULTIPLY", cy, cy)))
    inside = op("LESS_THAN", rc, R - edge - pitch * 0.6)
    streets = op("MAXIMUM", op("LESS_THAN", fx, street), op("LESS_THAN", fy, street))
    lines_x = op("LESS_THAN", op("FRACT", op("DIVIDE", X, pitch / 16)), 0.5)
    left = op("LESS_THAN", fx, 0.55)
    top = op("LESS_THAN", fy, 0.45)
    pat = op("MULTIPLY", op("MULTIPLY", left, top), lines_x)
    logic = op("MULTIPLY", op("SUBTRACT", 1.0, top), op("MULTIPLY", op("GREATER_THAN", fx, 0.22), op("LESS_THAN", fx, 0.78)))
    pads = op("MULTIPLY", op("SUBTRACT", 1.0, left), op("MULTIPLY", top, op("LESS_THAN", op("FRACT", op("DIVIDE", Y, py / 6)), 0.45)))
    dev = op("MINIMUM", op("ADD", op("ADD", op("MULTIPLY", pat, 0.55), op("MULTIPLY", logic, 0.8)), op("MULTIPLY", pads, 0.35)), 1.0)
    dev = op("MULTIPLY", op("MULTIPLY", dev, op("SUBTRACT", 1.0, streets)), inside)
    st = op("MULTIPLY", streets, inside)
    col = nt.nodes.new("ShaderNodeMix"); col.data_type = "RGBA"
    col.inputs["A"].default_value = (*K.lin((0.56, 0.57, 0.61)), 1)       # bare / edge Si: light metallic grey
    col.inputs["B"].default_value = (*K.lin((0.24, 0.25, 0.33)), 1)       # device areas: darker, faintly blue
    nt.links.new(dev, col.inputs["Factor"])
    col2 = nt.nodes.new("ShaderNodeMix"); col2.data_type = "RGBA"
    nt.links.new(col.outputs["Result"], col2.inputs["A"])
    col2.inputs["B"].default_value = (*K.lin((0.7, 0.71, 0.74)), 1)       # scribe streets: brighter lines
    nt.links.new(op("MULTIPLY", st, 0.85), col2.inputs["Factor"])
    nt.links.new(col2.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.12
    rr.inputs["To Max"].default_value = 0.34
    nt.links.new(op("ADD", dev, op("MULTIPLY", st, 0.6)), rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m


def wafer_r17(mb_face, mb_edge, c, R, thick=0.012, bevel=0.006, notch=True):
    """Wafer disc with a bevelled (chamfered) edge: flat polished face (mb_face), the bevel ring + side (mb_edge),
    and an orientation notch. c = centre of the top face."""
    import hero_kit_r15 as H15
    c = Vector(c)
    n = Vector((0, 0, 1))
    face = [(0.0, 0.0), (R - bevel, 0.0)]
    H15.lathe(mb_face, c, n, face, 192)
    edge = [(R - bevel, 0.0), (R, -bevel * 0.8), (R, -thick + bevel * 0.8), (R - bevel, -thick)]
    H15.lathe(mb_edge, c, n, edge, 192)
