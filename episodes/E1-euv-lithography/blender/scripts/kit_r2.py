"""P1 round 2 kit: product-grade materials, batched hard-surface geometry and lighting for the E1 cutaway look
(SCALE_E1 v2: 2A studio light + 2B dense cutaway, Carl 2026-10-23 "B做极细致和还原").

Geometry is accumulated in bmesh batches (one object per material) so a scene can carry thousands of parts
(ribs, bolts, flanges, pipes, cables) without thousands of bpy objects.

  mb = MB(); mb.box(c, size); mb.cyl(c, r, h, rot); mb.tube(a, b, r); mb.bolts(...); mb.obj("Frame", M["alu"])
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import common as C

VIOLET = (0.54, 0.36, 1.0)          # #8A5CFF
ORANGE = (1.0, 0.54, 0.24)          # #FF8A3D
CYAN = (0.25, 0.84, 0.88)           # #3FD6E0


def lin(c):
    """sRGB 0-1 tuple -> linear (Blender colour inputs are linear)."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# ---------------------------------------------------------------- materials
def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mat(name, color, metal=0.0, rough=0.4, emit=None, strength=0.0, transmission=0.0, ior=1.45, coat=0.0,
        brushed=0.0, speck=0.0, alpha=1.0, spec=0.5):
    """Principled material. brushed > 0 adds an anisotropic-looking streak in roughness + a tiny bump;
    speck > 0 adds a fine noise to the base colour (sand-blast / cast metal)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*lin(color), 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(emit), 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    if brushed or speck:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0, 1.0, 40.0) if brushed else (1, 1, 1)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 60.0 if brushed else 180.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        if brushed:
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = max(0.0, rough - brushed)
            mr.inputs["To Max"].default_value = rough + brushed
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.04
            bump.inputs["Distance"].default_value = 0.002
            nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        if speck:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = speck
            mix.inputs["A"].default_value = (*lin(color), 1)
            nt.links.new(nz.outputs["Color"], mix.inputs["B"])
            nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def emit_mat(name, color, strength, halo=0.0):
    """Pure emission; halo > 0 makes it a soft transparent glow (alpha = halo)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin(color), 1)
    em.inputs["Strength"].default_value = strength
    if halo:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        lw = nt.nodes.new("ShaderNodeLayerWeight")       # brighter in the middle of a tube, fading at the edge
        lw.inputs["Blend"].default_value = 0.35
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "MULTIPLY"
        inv.inputs[1].default_value = halo
        one = nt.nodes.new("ShaderNodeMath")
        one.operation = "SUBTRACT"
        one.inputs[0].default_value = 1.0
        nt.links.new(lw.outputs["Facing"], one.inputs[1])
        nt.links.new(one.outputs[0], inv.inputs[0])
        nt.links.new(inv.outputs[0], mx.inputs["Fac"])
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def vol_mat(name, color, density=1.0, emit=None):
    """Volume-light beam: transparent surface + emissive / scattering volume, so the beam reads as lit air
    (soft, brighter along its axis) instead of a solid glowing rod (R2 review, 2B gap 3)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs[0], out.inputs["Surface"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (*lin(color), 1)
    pv.inputs["Density"].default_value = 0.15 * density
    pv.inputs["Emission Color"].default_value = (*lin(color), 1)
    pv.inputs["Emission Strength"].default_value = emit if emit is not None else 2.0 * density
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    return m


def beam_column_mat(name, color, strength=1.5, edge=0.6, core=0.1, vol=0.18):
    """k4A-style wide beam column: translucent violet shell, more opaque towards the silhouette, faint
    streaks along the beam, and a thin emissive volume inside so it reads as light filling air."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin(color), 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (60.0, 60.0, 0.6)          # streaks along the local beam axis (generated Z)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeMapRange")
    st.inputs["To Min"].default_value = strength * 0.65
    st.inputs["To Max"].default_value = strength * 1.5
    nt.links.new(nz.outputs["Fac"], st.inputs["Value"])
    nt.links.new(st.outputs["Result"], em.inputs["Strength"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")                        # facing 1 (centre) -> core alpha, 0 (edge) -> edge alpha
    mr.inputs["To Min"].default_value = edge
    mr.inputs["To Max"].default_value = core
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    if vol:
        ve = nt.nodes.new("ShaderNodeEmission")
        ve.inputs["Color"].default_value = (*lin(color), 1)
        ve.inputs["Strength"].default_value = vol
        nt.links.new(ve.outputs[0], out.inputs["Volume"])
    return m


def clean_cycles(sc, indirect=4.0):
    """Clamp indirect light: kills the black / white firefly blocks the R2 review flagged (B6_12, B4_07)."""
    try:
        sc.cycles.sample_clamp_indirect = indirect
        sc.cycles.sample_clamp_direct = 0.0
        sc.cycles.blur_glossy = 1.0
        sc.cycles.caustics_reflective = False
        sc.cycles.caustics_refractive = False
    except AttributeError:
        pass


def palette(studio=False):
    """The shared material set. studio=True: 2A white-product panels are brighter."""
    return {
        "alu": mat("Alu", (0.78, 0.79, 0.81), metal=1.0, rough=0.28, brushed=0.08),
        "alu_dark": mat("AluDark", (0.42, 0.44, 0.48), metal=1.0, rough=0.35, brushed=0.1),
        "steel": mat("Steel", (0.62, 0.63, 0.66), metal=1.0, rough=0.2, brushed=0.05),
        "blast": mat("Blasted", (0.55, 0.56, 0.6), metal=1.0, rough=0.55, speck=0.25),
        "anod": mat("Anodized", (0.13, 0.14, 0.17), metal=0.8, rough=0.4, speck=0.15),
        "paint": mat("PaintWhite", (0.86, 0.87, 0.88) if studio else (0.72, 0.74, 0.77), rough=0.32, coat=0.4),
        "paint_grey": mat("PaintGrey", (0.32, 0.34, 0.38), rough=0.45),
        "granite": mat("Granite", (0.1, 0.1, 0.11), rough=0.35, speck=0.6),
        "copper": mat("Copper", (0.95, 0.6, 0.42), metal=1.0, rough=0.3),
        "gold": mat("GoldFoil", (1.0, 0.78, 0.36), metal=1.0, rough=0.38, speck=0.3),
        "rubber": mat("Rubber", (0.04, 0.04, 0.045), rough=0.7),
        "cable_b": mat("CableBlue", (0.12, 0.32, 0.75), rough=0.45),
        "cable_o": mat("CableOrange", (0.9, 0.45, 0.12), rough=0.45),
        "cable_g": mat("CableGrey", (0.5, 0.52, 0.55), rough=0.5),
        "mirror": mat("EUVMirror", (0.86, 0.84, 0.92), metal=1.0, rough=0.02, coat=0.3),
        # R3: a solid mirror = coated face that catches the studio lights (not a black hole) on a thick
        # pale glass-ceramic substrate, with the beam's footprint as a soft violet spot
        "coating": mat("MoSiCoating", (0.74, 0.7, 0.86), metal=1.0, rough=0.13, coat=0.8),
        "substrate": mat("MirrorBody", (0.82, 0.82, 0.85), metal=1.0, rough=0.16, brushed=0.06),
        "spot": emit_mat("BeamSpot", VIOLET, 6.0, halo=0.9),
        "beam_wide": beam_column_mat("EUVColumn", VIOLET),
        "section": mat("SectionFace", (0.46, 0.47, 0.5), rough=0.55),
        "beam_vol": vol_mat("EUVVolume", VIOLET, 2.2),
        "glass": mat("ViewGlass", (0.9, 0.95, 1.0), rough=0.02, transmission=1.0, ior=1.5),
        "led_c": emit_mat("LEDCyan", CYAN, 6.0),
        "led_o": emit_mat("LEDAmber", (1.0, 0.6, 0.2), 5.0),
        "beam": emit_mat("EUVBeam", VIOLET, 14.0),
        "beam_halo": emit_mat("EUVHalo", VIOLET, 3.0, halo=0.55),
        "laser": emit_mat("Laser", ORANGE, 18.0),
        "laser_halo": emit_mat("LaserHalo", ORANGE, 3.0, halo=0.5),
    }


# ---------------------------------------------------------------- batched geometry
def _orient(a, b):
    """Matrix placing a Z-aligned unit primitive between a and b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4(), d.length


class MB:
    def __init__(self):
        self.bm = bmesh.new()

    def _smooth_new(self, before, flat_caps=True):
        for f in self.bm.faces[before:]:
            f.smooth = not (flat_caps and len(f.verts) > 4)

    def box(self, c, s, rot=(0, 0, 0)):
        m = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*s, 1.0))
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self.bm.faces.ensure_lookup_table()

    def cyl(self, c, r, h, rot=(0, 0, 0), seg=32, r2=None):
        n0 = len(self.bm.faces)
        m = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2,
                              depth=h, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._smooth_new(n0)

    def cyl_m(self, m, r, h, seg=32, r2=None):
        n0 = len(self.bm.faces)
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2,
                              depth=h, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._smooth_new(n0)

    def tube(self, a, b, r, seg=12, r2=None):
        m, L = _orient(a, b)
        if L < 1e-5:
            return
        self.cyl_m(m, r, L, seg, r2)

    def path(self, pts, r, seg=10, joints=True):
        for a, b in zip(pts, pts[1:]):
            self.tube(a, b, r, seg)
        if joints:
            for p in pts[1:-1]:
                self.sphere(p, r * 1.02, 8)

    def sphere(self, c, r, seg=16):
        n0 = len(self.bm.faces)
        bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(4, seg // 2), radius=r,
                                  matrix=Matrix.Translation(Vector(c)))
        self.bm.faces.ensure_lookup_table()
        self._smooth_new(n0, flat_caps=False)

    def ring(self, c, r_out, r_in, h, rot=(0, 0, 0), seg=48):
        """Flat annulus (flange) with thickness h, axis = local Z."""
        n0 = len(self.bm.faces)
        M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4()
        vs = []
        for z in (-h / 2, h / 2):
            for r in (r_out, r_in):
                vs.append([self.bm.verts.new(M @ Vector((r * math.cos(2 * math.pi * i / seg),
                                                         r * math.sin(2 * math.pi * i / seg), z)))
                           for i in range(seg)])
        bo, bi, to, ti = vs
        for i in range(seg):
            j = (i + 1) % seg
            self.bm.faces.new((bo[i], bo[j], to[j], to[i]))
            self.bm.faces.new((bi[j], bi[i], ti[i], ti[j]))
            self.bm.faces.new((to[i], to[j], ti[j], ti[i]))
            self.bm.faces.new((bo[j], bo[i], bi[i], bi[j]))
        self.bm.faces.ensure_lookup_table()
        for f in self.bm.faces[n0:]:
            f.smooth = True

    def bolts(self, c, R, n, r, h, rot=(0, 0, 0), phase=0.0):
        M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4()
        for i in range(n):
            a = phase + 2 * math.pi * i / n
            p = M @ Vector((R * math.cos(a), R * math.sin(a), 0))
            self.cyl_m(Matrix.Translation(p) @ Euler(rot).to_matrix().to_4x4(), r, h, seg=6)

    def shell(self, c, r_in, r_out, length, a0, a1, rot=(0, 0, 0), seg=48):
        """Partial cylinder wall (cut-open vessel), axis local Z, angles in degrees."""
        n0 = len(self.bm.faces)
        M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4()
        k = max(2, int(seg * (a1 - a0) / 360) + 1)
        grid = {}
        for zi, z in enumerate((-length / 2, length / 2)):
            for ri, r in enumerate((r_out, r_in)):
                for i in range(k):
                    a = math.radians(a0 + (a1 - a0) * i / (k - 1))
                    grid[zi, ri, i] = self.bm.verts.new(M @ Vector((r * math.cos(a), r * math.sin(a), z)))
        for i in range(k - 1):
            for ri in (0, 1):
                q = (grid[0, ri, i], grid[0, ri, i + 1], grid[1, ri, i + 1], grid[1, ri, i])
                self.bm.faces.new(q if ri == 0 else q[::-1])
            self.bm.faces.new((grid[1, 0, i], grid[1, 0, i + 1], grid[1, 1, i + 1], grid[1, 1, i]))
            self.bm.faces.new((grid[0, 1, i], grid[0, 1, i + 1], grid[0, 0, i + 1], grid[0, 0, i]))
        for i in (0, k - 1):
            q = (grid[0, 0, i], grid[1, 0, i], grid[1, 1, i], grid[0, 1, i])
            self.bm.faces.new(q if i == 0 else q[::-1])
        self.bm.faces.ensure_lookup_table()
        for f in self.bm.faces[n0:]:
            f.smooth = len(f.verts) == 4 and abs(f.normal.z) < 0.99
        return M

    def obj(self, name, material, bevel=0.0, coll=None):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        me.materials.append(material)
        if bevel:
            bv = ob.modifiers.new("Bevel", "BEVEL")
            bv.width = bevel
            bv.segments = 2
            bv.limit_method = "ANGLE"
            bv.angle_limit = math.radians(40)
            bv.harden_normals = False
        return ob


def greeble(mb, origin, u, v, nrm, w, h, n, smin, smax, dmin, dmax, seed=0):
    """Random panels / boxes on a rectangle origin + s*u + t*v (s in [0,w], t in [0,h]), sticking out along nrm."""
    rnd = random.Random(seed)
    u, v, nrm = Vector(u).normalized(), Vector(v).normalized(), Vector(nrm).normalized()
    rot = Matrix((u, v, nrm)).transposed().to_euler()
    for _ in range(n):
        sx, sy, d = rnd.uniform(smin, smax), rnd.uniform(smin, smax) * rnd.choice((0.5, 1, 1.6)), rnd.uniform(dmin, dmax)
        s, t = rnd.uniform(0, w - sx), rnd.uniform(0, h - sy)
        c = Vector(origin) + u * (s + sx / 2) + v * (t + sy / 2) + nrm * (d / 2)
        mb.box(c, (sx, sy, d), rot)


def cable_run(mb, pts, n=5, r=0.012, spread=0.035, seed=0):
    """A loose bundle of n cables following pts (each with small offsets)."""
    rnd = random.Random(seed)
    for k in range(n):
        off = Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)))
        mb.path([Vector(p) + off for p in pts], r, seg=8)


# ---------------------------------------------------------------- optics helpers
def mirror_normal(prev, p, nxt):
    return ((Vector(prev) - Vector(p)).normalized() + (Vector(nxt) - Vector(p)).normalized()).normalized()


def mirror_with_mount(mbm, mbmount, mbbolt, p, n, r, thick=0.05, struts=True, seed=0, mbsub=None, mbspot=None,
                      mbpipe=None, mbcable=None, spot=0.32):
    """Solid mirror at p facing n (front face sits on p): coated face disc on a thick substrate (mbsub), mount
    ring + bolt circle, back plate, hexapod; R3 adds the beam footprint spot (mbspot), two cooling lines and a
    cable loom from the back plate (mbpipe / mbcable) so every bounce point reads as a real, serviced mirror."""
    p, n = Vector(p), Vector(n).normalized()
    q = Vector((0, 0, 1)).rotation_difference(n)
    R = q.to_matrix().to_4x4()
    if mbsub is not None:
        thick = max(thick, r * 0.32)
        mbm.cyl_m(Matrix.Translation(p - n * 0.004) @ R, r * 0.985, 0.008, seg=64)       # coated face
        back = p - n * (thick / 2 + 0.008)
        mbsub.cyl_m(Matrix.Translation(back) @ R, r, thick, seg=64)                       # solid substrate
    else:
        back = p - n * (thick / 2 + 0.002)
        mbm.cyl_m(Matrix.Translation(back) @ R, r, thick, seg=48)
    if mbspot is not None and spot:
        mbspot.cyl_m(Matrix.Translation(p + n * 0.002) @ R, r * spot, 0.002, seg=32)
    mbmount.ring(back - n * 0.01, r * 1.12, r * 0.98, thick * 1.3, rot=q.to_euler(), seg=48)
    mbbolt.bolts(back - n * 0.01 + n * thick * 0.7, r * 1.05, 12, r * 0.025, 0.02, rot=q.to_euler())
    plate = p - n * (thick + r * 0.55)
    mbmount.cyl_m(Matrix.Translation(plate) @ R, r * 0.9, 0.04, seg=6)
    if struts:
        for i in range(6):                       # hexapod: pairs of struts crossing between back ring and plate
            a = math.radians(60 * i)
            a2 = math.radians(60 * i + (40 if i % 2 else -40))
            top = back - n * 0.03 + R @ Vector((r * 0.85 * math.cos(a), r * 0.85 * math.sin(a), 0))
            bot = plate + R @ Vector((r * 0.75 * math.cos(a2), r * 0.75 * math.sin(a2), 0))
            mbmount.tube(top, bot, r * 0.035, seg=8)
            mbbolt.sphere(top, r * 0.05, 8)
            mbbolt.sphere(bot, r * 0.05, 8)
            mbmount.cyl_m(Matrix.Translation(top.lerp(bot, 0.5)) @ R, r * 0.06, r * 0.09, seg=10)   # actuator can
    side = R @ Vector((1, 0, 0))
    up = R @ Vector((0, 1, 0))
    if mbpipe is not None:                       # cooling in / out from the substrate back, bent away from the beam
        for s_ in (-1, 1):
            a = back - n * (thick * 0.5) + side * (s_ * r * 0.35)
            b = a - n * r * 0.5
            c = b + side * (s_ * r * 1.4) - n * r * 0.3
            mbpipe.path([a, b, c, c - n * r * 0.9], r * 0.04, seg=10)
            mbbolt.cyl_m(Matrix.Translation(a) @ R, r * 0.07, r * 0.08, seg=8)
    if mbcable is not None:
        rnd = random.Random(seed)
        for k in range(4):
            o = up * (r * (0.2 + 0.08 * k)) + side * (rnd.uniform(-0.1, 0.1) * r)
            mbcable.path([plate + o, plate + o - n * r * 0.6 - up * r * 0.4, plate + o - n * r * 1.4 - up * r * 1.1],
                         r * 0.018, seg=6)
    return plate


def beam(mbcore, mbhalo, pts, r=0.03, halo=3.2, mbvol=None, vol=6.0):
    """Beam polyline: thin emissive core + soft halo; with mbvol, also a wide volume-light sleeve (R3)."""
    for a, b in zip(pts, pts[1:]):
        mbcore.tube(a, b, r, seg=12)
        mbhalo.tube(a, b, r * halo, seg=16)
        if mbvol is not None:
            mbvol.tube(a, b, r * vol, seg=20)
    for p in pts[1:-1]:
        mbcore.sphere(p, r * 1.4, 10)
        if mbvol is not None:
            mbvol.sphere(p, r * vol, 16)


def beam_columns(mb, pts, radii, seg=40):
    """Wide tapered beam columns between consecutive optical points (radius radii[i] at pts[i])."""
    for (a, b), (ra, rb) in zip(zip(pts, pts[1:]), zip(radii, radii[1:])):
        m, L = _orient(a, b)
        if L > 1e-4:
            mb.cyl_m(m, max(ra, 0.004), L, seg=seg, r2=max(rb, 0.004))


def bounce_lights(pts, energy=25.0, radius=0.15, offset=None):
    """Violet point lights at the bounce points, so the beam actually lights the mirror mounts around it."""
    for i, p in enumerate(pts):
        point(f"Bounce{i}", Vector(p) + (Vector(offset) if offset else Vector((0, -0.15, 0))), energy, VIOLET, radius)


def cone_beam(mbhalo, apex, base_c, base_r, seg=48):
    """A light cone from apex to a disc of radius base_r centred at base_c (soft halo material)."""
    m, L = _orient(base_c, apex)
    mbhalo.cyl_m(m, base_r, L, seg=seg, r2=0.002)


# ---------------------------------------------------------------- scene helpers
def area(name, loc, target, size, energy, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    l = bpy.data.lights.new(name, "AREA")
    l.energy = energy
    l.color = color
    l.shape = shape
    l.size = size
    if size_y:
        l.size_y = size_y
    ob = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def point(name, loc, energy, color=(1, 1, 1), radius=0.05):
    l = bpy.data.lights.new(name, "POINT")
    l.energy = energy
    l.color = color
    l.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, l)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def camera(name, lens=35, fstop=None, focus=None, sensor=36):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.01
    cd.clip_end = 400
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    tgt = bpy.data.objects.new(name + "_tgt", None)
    bpy.context.scene.collection.objects.link(tgt)
    tc = cam.constraints.new("TRACK_TO")
    tc.target = tgt
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_object = focus or tgt
    return cam, tgt


def key_path(cam, tgt, keys, interp="BEZIER"):
    """keys: [(frame, cam_loc, tgt_loc)]."""
    for f, cl, tl in keys:
        cam.location = cl
        cam.keyframe_insert("location", frame=f)
        tgt.location = tl
        tgt.keyframe_insert("location", frame=f)
    for ob in (cam, tgt):
        for fc in C.fcurves(ob.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = interp
                k.easing = "EASE_IN_OUT"


def world_dark(strength=1.0):
    C.set_world(top=(0.05, 0.065, 0.11), horizon=(0.02, 0.027, 0.048), bottom=(0.006, 0.008, 0.014),
                strength=strength)


def world_studio(strength=1.0):
    C.set_world(top=(0.55, 0.57, 0.6), horizon=(0.32, 0.33, 0.35), bottom=(0.1, 0.1, 0.11), strength=strength)


def floor(name, material, size=80, z=0.0):
    mb = MB()
    mb.box((0, 0, z - 0.05), (size, size, 0.1))
    return mb.obj(name, material)


def nframes(sid):
    import sys
    sys.path.insert(0, os.path.join(C.REPO_ROOT, "shared", "tools"))
    from paths import timed_shots
    s = next(s for s in timed_shots() if s["id"] == sid)
    return max(1, round(s["duration"] * 24))


def person(name, loc, height=1.75, pose="stand", facing=0.0, color=(0.03, 0.035, 0.045)):
    import figures
    m = mat(name + "Suit", color, rough=0.75)
    return figures.person(name, loc, height=height, pose=pose, facing=facing, mat=m, role="env")


def _cloth_mat(name, color):
    """R8: bunny-suit fabric: cloth sheen + soft wrinkle bump (two noise scales), not a smooth plastic shell."""
    m = mat(name, color, rough=0.72, spec=0.25)
    nt = m.node_tree
    b = _bsdf(m)
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 0.6
        b.inputs["Sheen Roughness"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 3.2)            # wrinkles run mostly around the limbs
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 9.0
    n1.inputs["Detail"].default_value = 3.0
    n1.inputs["Distortion"].default_value = 1.2
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 60.0
    n2.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b1 = nt.nodes.new("ShaderNodeBump")
    b1.inputs["Strength"].default_value = 0.55
    b1.inputs["Distance"].default_value = 0.02
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.12
    b2.inputs["Distance"].default_value = 0.003
    nt.links.new(n1.outputs["Fac"], b1.inputs["Height"])
    nt.links.new(n2.outputs["Fac"], b2.inputs["Height"])
    nt.links.new(b1.outputs["Normal"], b2.inputs["Normal"])
    nt.links.new(b2.outputs["Normal"], b.inputs["Normal"])
    return m


def suit_person(name, loc, height=1.75, pose="stand", facing=0.0):
    """9A/9B clean-room figure, no face. R8 (R7 review: "smooth white dummy, toy-like"): wrinkled fabric with
    sheen, hood opening framing a dark goggle visor + white face mask, front zip, blue nitrile gloves with cuff
    seams, pale-blue boot covers with soles."""
    import figures
    m = _cloth_mat(name + "Suit", (0.86, 0.87, 0.9))
    ob = figures.person(name, loc, height=height, pose=pose, facing=facing, mat=m, role="env")
    k = height / 1.75
    a = math.radians(facing)
    L = Vector(loc)

    def P(x, y, z):
        v = Vector((x, y, z)) * k
        return L + Vector((v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a), v.z))
    rot = (0, 0, a)
    parts = {key: MB() for key in ("visor", "mask", "hood", "zip", "glove", "boot", "sole")}
    parts["hood"].ring(P(0, -0.112, 1.615), 0.092 * k, 0.07 * k, 0.03 * k, rot=(math.radians(90), 0, a), seg=32)
    parts["mask"].sphere(P(0, -0.1, 1.555), 0.058 * k, 16)
    parts["zip"].box(P(0, -0.142, 1.16), (0.012 * k, 0.01 * k, 0.5 * k), rot=rot)
    for z in (1.0, 1.15, 1.3):                                                    # snap closures
        parts["zip"].sphere(P(0.03, -0.14, z), 0.008 * k, 8)
    stride = 0.16 if pose == "walk" else 0.0
    for sgn in (-1, 1):
        if pose == "work" and sgn == 1:
            hand, wrist = P(0.2, -0.38, 1.12), P(0.215, -0.31, 1.115)
        else:
            sw = -stride * sgn * 0.8
            hand, wrist = P(0.25 * sgn, sw, 0.8), P(0.25 * sgn, sw * 0.88, 0.86)
        parts["glove"].sphere(hand, 0.052 * k, 16)
        parts["glove"].tube(wrist, hand, 0.045 * k, seg=14)
        parts["hood"].ring(wrist, 0.062 * k, 0.04 * k, 0.025 * k,
                           rot=Vector((0, 0, 1)).rotation_difference(hand - wrist).to_euler(), seg=20)
        foot = P(0.1 * sgn, stride * sgn, 0.1)
        toe = P(0.1 * sgn, stride * sgn - 0.12, 0.07)
        parts["boot"].tube(foot + Vector((0, 0, 0.12 * k)), foot, 0.1 * k, seg=16)
        parts["boot"].tube(foot, toe, 0.082 * k, seg=16)
        parts["sole"].box((foot + toe) / 2 - Vector((0, 0, 0.065 * k)), (0.12 * k, 0.26 * k, 0.025 * k), rot=rot)
    v = parts.pop("visor")
    v.sphere(P(0, -0.105, 1.63), 0.075 * k, 20)
    vo = v.obj(name + "Visor", mat(name + "VisorM", (0.02, 0.022, 0.03), metal=0.3, rough=0.08, coat=1.0))
    c = P(0, -0.105, 1.63)
    vo.data.transform(Matrix.Translation(-c))
    vo.location = c
    vo.scale = (1.25, 0.55, 0.5)
    vo.rotation_euler = rot
    mats = {"mask": mat(name + "MaskM", (0.93, 0.94, 0.95), rough=0.8),
            "hood": _cloth_mat(name + "SeamM", (0.74, 0.76, 0.8)),
            "zip": mat(name + "ZipM", (0.45, 0.47, 0.52), metal=0.6, rough=0.35),
            "glove": mat(name + "GloveM", (0.22, 0.36, 0.78), rough=0.35, coat=0.3),
            "boot": _cloth_mat(name + "BootM", (0.62, 0.7, 0.82)),
            "sole": mat(name + "SoleM", (0.12, 0.13, 0.15), rough=0.6)}
    for key, mb in parts.items():
        mb.obj(name + "_" + key, mats[key])
    return ob


def anchors(shot, points):
    """Write the screen position (0-1, y down) of named world points for every frame that gets set, to
    <renders>/shots/<shot>/anchors/####.json (shot-relative frame = scene frame - start + 1 for start=1, step=1).
    2D overlays (mograph/r2_ov_*.py) read these so leader lines land on the 3D parts."""
    import json
    from bpy_extras.object_utils import world_to_camera_view
    if not shot:
        return
    out = os.path.join(C.render_root(), "shots", shot, "anchors")
    pts = {k: Vector(v) for k, v in points.items()}

    def h(sc, *_):
        cam = sc.camera
        if cam is None:
            return
        res = {}
        for k, p in pts.items():
            v = world_to_camera_view(sc, cam, p)
            res[k] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"{sc.frame_current:04d}.json"), "w") as fh:
            json.dump(res, fh)
    bpy.app.handlers.frame_change_post.append(h)
