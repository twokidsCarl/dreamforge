"""B4 — multilayer optics and atom-flat mirrors. Variants:

  silver   B4_01  a plain silvered mirror swallows EUV: no reflection, a faint warm edge
  stack    B4_02  SEM cross-section of the Mo/Si stack (same framing as B2_05)
  mirror   B4_04  a large freeform EUV mirror on a stand in a clean room, light sweeping across
           B4_05  same, with a metrology scan band
  atoms    B4_07  zoom from the polished surface down to the atomic lattice
           B4_08  the lattice with one tiny bump next to the silicon-atom ruler (F29, F60)
  space    B4_10  a laser leaving Earth toward the Moon;  B4_11  the golf ball on the Moon (F9b, F30)
  hall     B4_13  the 150 t measuring machine's vacuum chamber, a mirror lowered in (F32)
  explode  B4_14  High-NA projection-optics module exploding and reassembling (F18)
  bounce   B4_15  one mirror: ~70% reflected, the rest a heat halo;  B4_16  ten mirrors, dimming
All shapes illustrative; sizes not to scale.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 300
VIOLET = (0.62, 0.45, 1.0)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


def _cyl(name, r, depth, loc, mat, rot=(0, 0, 0), role="structure", verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    es = ob.modifiers.new("Edges", "EDGE_SPLIT")       # crisp caps, smooth sides
    es.split_angle = math.radians(40)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _beam(name, a, b, radius, color, strength):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=d.length, vertices=24, location=(a + b) / 2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    mat = M.emission(name + "Mat", color, strength)
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob, mat


# ---- B4_01 ---------------------------------------------------------------------------------
def silver(sc, rnd):
    glass = M.principled("Silvered", (0.85, 0.86, 0.88), metallic=1.0, roughness=0.05)
    m = _cyl("PlainMirror", 2.0, 0.15, (0, 0, 0), glass, rot=(0, math.pi / 2, 0))
    beam, bm = _beam("EUV", (12, 6, 0), (0.08, 0, 0), 0.06, VIOLET, 0.0)
    for f, v in ((1, 0), (10, 0), (16, 10), (FRAMES, 10)):
        M.set_emission_strength(bm, f, v)
    heat = M.emission("Heat", (1.0, 0.45, 0.15), 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.02, minor_radius=0.03, location=(0.08, 0, 0),
                                     rotation=(0, math.pi / 2, 0))
    ring = bpy.context.object
    ring.data.materials.append(heat)
    styles.tag(ring, "emitter")
    for f, v in ((1, 0), (24, 0), (70, 1.5)):
        M.set_emission_strength(heat, f, v)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.0, minor_radius=0.012, location=(-0.06, 0, 0),
                                     rotation=(0, math.pi / 2, 0))
    edge = bpy.context.object
    edge.data.materials.append(M.emission("MirrorEdge", (0.7, 0.75, 0.85), 0.6))
    styles.tag(edge, "emitter")
    B._camera("CamB4_01", [(1, (0, 1.0, 0), (9.0, 7.5, 3.0), 35, 11.0), (100, (0, 0.5, 0), (8.0, 6.0, 2.6), 35, 11.0)])


# ---- B4_02 ---------------------------------------------------------------------------------
def stack(sc, rnd):
    import b2_scenes
    b2_scenes.multilayer(sc, n_pairs=20, t=0.11)
    B._camera("CamB4_02", [(1, (0, 0, -1.2), (0.0, -6.0, -0.2), 100, 11.0),
                           (180, (0, 0, -2.2), (0.0, -7.5, -1.2), 100, 11.0)])


# ---- B4_04 / B4_05 -------------------------------------------------------------------------
def _cap(name, radius=1.6, curv_r=9.0, segs=96, rings=32):
    bm = bmesh.new()
    verts = [[None] * segs for _ in range(rings + 1)]
    centre = bm.verts.new((0, 0, 0))
    for i in range(1, rings + 1):
        r = radius * i / rings
        z = r * r / (2 * curv_r)
        for j in range(segs):
            th = 2 * math.pi * j / segs
            verts[i][j] = bm.verts.new((r * math.cos(th), r * math.sin(th), z))
    for j in range(segs):
        bm.faces.new((centre, verts[1][j], verts[1][(j + 1) % segs]))
    for i in range(1, rings):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][k], verts[i][k]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.25
    return ob


def mirror(sc, rnd, scan=False):
    BM.fab_hall(people=0)
    cap = _cap("FreeformMirror")
    cap.location = (0, 0, 0.9)
    cap.rotation_euler = (math.radians(-35), 0, 0)
    cap.data.materials.append(M.multilayer_mirror("BigMirror", r_max=1.6))
    styles.tag(cap, "structure")
    steel = M.polished_steel("Stand", 0.3)
    for x in (-0.9, 0.9):
        _cyl(f"Leg{x}", 0.08, 2.6, (x, 0.5, -0.9), steel)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0.4, -2.0))
    base = bpy.context.object
    base.scale = (1.6, 1.0, 0.15)
    base.data.materials.append(steel)
    styles.tag(base, "structure")
    sweep = B._area("Sweep", (-6, -4, 5), (0.9, 0, -0.6), 3.0, 1500, (0.8, 0.88, 1.0))
    _key(sweep, 1, location=(-6, -4, 5))
    _key(sweep, 110, location=(6, -4, 5))
    if scan:
        mat = styles.dark_rim("ScanBand", color=(0.2, 0.85, 0.95), strength=3.0)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-2.2, 0, 1.1))
        band = bpy.context.object
        band.scale = (0.06, 2.0, 2.0)
        band.rotation_euler = (0, math.radians(90), 0)
        band.data.materials.append(M.emission("Band", (0.2, 0.85, 0.95), 6.0))
        styles.tag(band, "emitter")
        _key(band, 1, location=(-2.2, 0, 1.1))
        _key(band, 100, location=(2.2, 0, 1.1))
    B._camera("CamB4_04", [(1, (0, 0, 0.8), (3.8, -4.6, 2.2), 40, 4.0), (96, (0, 0, 0.8), (2.6, -5.2, 1.8), 40, 4.0)])
    B._camera("CamB4_05", [(1, (0, 0, 0.9), (0.4, -4.0, 3.4), 45, 5.6), (103, (0, 0, 0.9), (-0.4, -4.1, 3.3), 45, 5.6)])


# ---- B4_07 / B4_08 -------------------------------------------------------------------------
def atoms(sc, rnd, n=80, spacing=0.235):
    """Atomic lattice as vertex-instanced spheres (cheap), with one tiny bump near the centre."""
    me = bpy.data.meshes.new("LatticePts")
    pts = []
    for i in range(n):
        for j in range(n):
            x = (i - n / 2) * spacing + (j % 2) * spacing / 2
            y = (j - n / 2) * spacing * 0.866
            bump = 0.02 * math.exp(-((x - 0.3) ** 2 + (y + 0.2) ** 2) / 0.4)    # ~1/10 of an atom
            pts.append((x, y, bump))
    me.from_pydata(pts, [], [])
    host = bpy.data.objects.new("Lattice", me)
    sc.collection.objects.link(host)
    host.instance_type = "VERTS"
    styles.tag(host, "structure")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, segments=20, ring_count=10, location=(0, 0, -50))
    atom = bpy.context.object
    atom.name = "Atom"
    atom.parent = host
    atom.location = (0, 0, 0)
    atom.data.materials.append(M.principled("AtomMat", (0.8, 0.8, 0.8)))
    styles.tag(atom, "structure")
    # the polished surface seen from afar (fades out as the camera dives in)
    bpy.ops.mesh.primitive_plane_add(size=n * spacing, location=(0, 0, -0.02))
    surf = bpy.context.object
    surf.name = "Surface"
    surf.data.materials.append(M.principled("SurfMat", (0.6, 0.6, 0.6), roughness=0.4))
    styles.tag(surf, "structure")
    # silicon-atom ruler (shown only in B4_08 via after_style)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1175, segments=32, ring_count=16, location=(0.95, -1.15, 0.32))
    ruler = bpy.context.object
    ruler.name = "SiRuler"
    ruler["ruler"] = True
    styles.tag(ruler, "rays")
    bpy.ops.mesh.primitive_cube_add(location=(0.95 + 0.2, -1.15, 0.32))
    bar = bpy.context.object
    bar.name = "TenthBar"
    bar.scale = (0.03, 0.03, 0.01175)            # 1/10 of an atom: the mirror's error
    bar["ruler"] = True
    styles.tag(bar, "rays")
    B._camera("CamB4_07", [(1, (0.3, -0.2, 0), (0.3, -0.25, 40.0), 50, 11.0),
                           (144, (0.3, -0.2, 0), (0.6, -1.4, 1.1), 50, 11.0)])
    B._camera("CamB4_08", [(1, (0.6, -0.4, 0.05), (1.2, -2.6, 0.55), 50, 11.0),
                           (185, (0.7, -0.4, 0.05), (1.6, -2.4, 0.6), 50, 11.0)])


# ---- B4_10 / B4_11 -------------------------------------------------------------------------
def _earth(loc, r):
    m = bpy.data.materials.new("Earth")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.1
    noise.inputs["Detail"].default_value = 5.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.52, (0.01, 0.04, 0.16, 1)
    e[1].position, e[1].color = 0.56, (0.12, 0.2, 0.08, 1)
    e2 = ramp.color_ramp.elements.new(0.66)
    e2.color = (0.32, 0.26, 0.14, 1)
    clouds = nt.nodes.new("ShaderNodeTexNoise")
    clouds.inputs["Scale"].default_value = 3.0
    clouds.inputs["Detail"].default_value = 6.0
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.62
    cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.82
    cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], clouds.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(clouds.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color1"])
    mix.inputs["Color2"].default_value = (0.9, 0.92, 0.95, 1)
    nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=96, ring_count=48, location=loc)
    ob = bpy.context.object
    ob.name = "EarthBody"
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(m)
    styles.tag(ob, "structure")
    atm = styles.dark_rim("Atmosphere", color=(0.3, 0.55, 1.0), strength=2.5)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.025, segments=96, ring_count=48, location=loc)
    a = bpy.context.object
    for p in a.data.polygons:
        p.use_smooth = True
    a.data.materials.append(atm)
    styles.tag(a, "emitter")
    return ob


def _moon_terrain(rnd, loc=(0, 0, -500)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=260, size=24, location=loc)
    t = bpy.context.object
    t.name = "MoonTerrain"
    tex = bpy.data.textures.new("Craters", "VORONOI")
    tex.noise_scale = 1.6
    d = t.modifiers.new("Craters", "DISPLACE")
    d.texture = tex
    d.strength = -0.35
    tex2 = bpy.data.textures.new("Regolith", "CLOUDS")
    tex2.noise_scale = 0.3
    d2 = t.modifiers.new("Regolith", "DISPLACE")
    d2.texture = tex2
    d2.strength = 0.08
    for p in t.data.polygons:
        p.use_smooth = True
    t.data.materials.append(M.principled("Regolith", (0.16, 0.155, 0.15), roughness=0.95))
    styles.tag(t, "structure")
    # golf ball with dimples (voronoi bump)
    gm = bpy.data.materials.new("Golf")
    gm.use_nodes = True
    nt = gm.node_tree
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 22.0
    vor.feature = "F1"
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.invert = True
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    nt.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.7, 0.7, 0.68, 1)
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.21, segments=64, ring_count=32,
                                         location=(loc[0], loc[1], loc[2] + 0.12))
    ball = bpy.context.object
    ball.name = "GolfBall"
    for p in ball.data.polygons:
        p.use_smooth = True
    ball.data.materials.append(gm)
    styles.tag(ball, "structure")
    spot = bpy.data.lights.new("LaserSpot", "SPOT")              # the laser's faint footprint
    spot.energy = 40.0
    spot.color = (0.75, 0.85, 1.0)
    spot.spot_size = math.radians(14)
    spot.spot_blend = 0.6
    sp = bpy.data.objects.new("LaserSpot", spot)
    bpy.context.scene.collection.objects.link(sp)
    sp.location = (loc[0], loc[1], loc[2] + 3.0)
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 1.4
    sun.angle = math.radians(0.6)
    so = bpy.data.objects.new("Sun", sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(82), 0, math.radians(30))
    return ball


def space(sc, rnd):
    _earth((0, 0, 0), 6.0)
    moon = M.principled("MoonMat", (0.4, 0.39, 0.38), roughness=0.95)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.64, segments=64, ring_count=32, location=(360, 0, 0))
    mo = bpy.context.object
    mo.data.materials.append(moon)
    styles.tag(mo, "structure")
    beam, bm = _beam("Laser", (6.05, 0, 0), (358.4, 0, 0), 0.015, (0.95, 0.95, 1.0), 20.0)
    beam.data.materials[0] = bm
    _moon_terrain(rnd)
    _earth((-60, 220, -470), 2.0)                      # small Earth in the lunar sky
    sun = bpy.data.lights.new("SpaceSun", "SUN")
    sun.energy = 2.0
    so = bpy.data.objects.new("SpaceSun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (0, math.radians(-70), math.radians(20))
    B._camera("CamB4_10", [(1, (6.0, 0, 0), (14.0, -9.0, 4.0), 35, 16.0),
                           (60, (120.0, 0, 0), (40.0, -3.0, 1.2), 35, 16.0),
                           (163, (360.0, 0, 0), (352.0, -2.0, 0.8), 35, 16.0)])
    B._camera("CamB4_11", [(1, (0, 0, -499.85), (1.6, -3.4, -499.45), 70, 5.6),
                           (108, (0, 0, -499.85), (1.0, -3.0, -499.55), 70, 5.6)])


# ---- B4_13 ---------------------------------------------------------------------------------
def hall(sc, rnd):
    BM.fab_hall(people=5)
    steel = M.polished_steel("ChamberSteel", 0.35)
    ch = _cyl("MetroChamber", 2.6, 10.0, (2.0, 4.0, 0.4), steel, rot=(0, math.pi / 2, 0))
    door = _cyl("ChamberDoor", 2.4, 0.3, (7.2, 4.0, 0.4), M.dark_anodized("Door"), rot=(0, math.pi / 2, 0))
    for x in (-3.5, 7.5):                               # crane gantry
        _cyl(f"Post{x}", 0.18, 9.0, (x, 4.0, 2.3), steel, rot=(0, 0, 0))
    bpy.ops.mesh.primitive_cube_add(location=(2.0, 2.6, 6.8))
    beam = bpy.context.object
    beam.scale = (6.5, 1.6, 0.2)
    beam.data.materials.append(steel)
    styles.tag(beam, "structure")
    m = _cyl("HungMirror", 1.0, 0.18, (8.0, 1.2, 4.6), M.multilayer_mirror("HungMirrorMat", r_max=1.0),
             rot=(0, math.pi / 2, 0))
    _key(m, 1, location=(8.0, 1.2, 4.6))
    _key(m, 127, location=(8.0, 1.2, 1.6))
    cable = _cyl("Cable", 0.02, 4.0, (0, 0, 2.0), steel, verts=8)
    cable.parent = m
    cable.rotation_euler = (0, -math.pi / 2, 0)
    cable.location = (-2.0, 0, 0)
    B._area("HallFill", (0, -10, 7), (1.1, 0, 0), 18, 2500, (0.85, 0.9, 1.0))
    B._camera("CamB4_13", [(1, (3.0, 4.0, 1.4), (-9.0, -9.0, 0.2), 24, 8.0),
                           (127, (3.5, 4.0, 1.2), (-7.0, -10.0, 0.4), 24, 8.0)])


# ---- B4_14 ---------------------------------------------------------------------------------
def explode(sc, rnd):
    """A stacked barrel of 6 sections: it separates along its axis, mirrors slide out sideways,
    struts move radially, then everything returns home in reverse order. Calm, readable order."""
    mat = M.principled("PO", (0.7, 0.7, 0.7))
    n = 6
    groups = []                                    # (objects, home z, section index)
    for k in range(n):
        z = -1.5 + 0.6 * k
        bpy.ops.mesh.primitive_cylinder_add(radius=1.25, depth=0.56, vertices=96, end_fill_type="NOTHING",
                                            location=(0, 0, z))
        ring = bpy.context.object
        ring.name = f"Section{k}"
        sol = ring.modifiers.new("Wall", "SOLIDIFY")
        sol.thickness = 0.12
        for p in ring.data.polygons:
            p.use_smooth = True
        ring.data.materials.append(mat)
        styles.tag(ring, "structure")
        bpy.ops.mesh.primitive_torus_add(major_radius=1.33, minor_radius=0.05, location=(0, 0, z + 0.28))
        fl = bpy.context.object
        fl.data.materials.append(mat)
        styles.tag(fl, "structure")
        fl.parent = ring
        fl.location = (0, 0, 0.28)
        for j in range(12):                        # bolts ride on their flange
            th = 2 * math.pi * (j + 0.5 * (k % 2)) / 12
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.1, vertices=8)
            bo = bpy.context.object
            bo.data.materials.append(mat)
            styles.tag(bo, "structure")
            bo.parent = ring
            bo.location = (1.33 * math.cos(th), 1.33 * math.sin(th), 0.34)
        mir = _cyl(f"Mir{k}", 0.8, 0.1, (0, 0, z), mat, rot=(0.35 * (-1) ** k, 0, 0))
        groups.append((ring, mir, z, k))
    struts = []
    for j in range(8):
        th = 2 * math.pi * j / 8 + math.pi / 8
        struts.append((_cyl(f"Strut{j}", 0.045, 3.8, (1.55 * math.cos(th), 1.55 * math.sin(th), 0.0), mat, verts=12),
                       th))
    spread = 2.1
    for ring, mir, z, k in groups:
        d = abs(k - (n - 1) / 2)                   # centre sections open first
        f0, f1 = 18 + int(4 * d), 46 + int(4 * d)
        zo = z * spread
        side = 1 if k % 2 == 0 else -1
        _key(ring, f0, location=(0, 0, z))
        _key(ring, f1, location=(0, 0, zo))
        _key(mir, f0, location=(0, 0, z))
        _key(mir, f1, location=(0, 0, zo))
        lat = Vector((0.81, 0.59, 0)) * side * 2.4       # screen-lateral for this camera
        _key(mir, f1 + 10, location=(lat.x, lat.y, zo))
        _key(mir, 92, location=(lat.x, lat.y, zo))
        _key(mir, 102, location=(0, 0, zo))
        r0 = 100 + int(3 * (2.5 - d))
        _key(ring, r0, location=(0, 0, zo))
        _key(ring, r0 + 18, location=(0, 0, z))
        _key(mir, r0, location=(0, 0, zo))
        _key(mir, r0 + 18, location=(0, 0, z))
    for s_, th in struts:
        home = s_.location.copy()
        out = home + Vector((math.cos(th), math.sin(th), 0)) * 1.4
        _key(s_, 12, location=home)
        _key(s_, 30, location=out)
        _key(s_, 112, location=out)
        _key(s_, 126, location=home)
    B._area("ClayKey", (5, -6, 7), (0.9, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._camera("CamB4_14", [(1, (0, 0, 0.0), (8.0, -11.0, 3.2), 35, 11.0), (136, (0, 0, 0.0), (10.0, -9.0, 3.8), 35, 11.0)])


# ---- B4_15 / B4_16 -------------------------------------------------------------------------
def bounce(sc, rnd):
    mir = M.principled("M", (0.6, 0.6, 0.65), metallic=1.0)
    heat = M.emission("Heat", (1.0, 0.42, 0.12), 0.0)
    pts = [Vector((-14, 0, 2.5))]
    for k in range(10):
        pts.append(Vector((-11 + 2.6 * k, 0, 0.0 if k % 2 == 0 else 2.6)))
    pts.append(Vector((16, 0, 0.8)))
    for k in range(1, 11):
        m = _cyl(f"Mirror{k}", 0.55, 0.08, tuple(pts[k]), mir)
        a_ = (pts[k - 1] - pts[k]).normalized()
        b_ = (pts[k + 1] - pts[k]).normalized()
        m.rotation_euler = (a_ + b_).normalized().to_track_quat("Z", "Y").to_euler()
        h = _cyl(f"Halo{k}", 0.62, 0.02, tuple(pts[k]), heat)
        h.rotation_euler = m.rotation_euler
        styles.tag(h, "emitter")
    level = 10.0
    for k in range(11):
        beam, bm = _beam(f"Leg{k}", pts[k], pts[k + 1], 0.06 * max(0.35, 0.7 ** k) + 0.02, VIOLET, 0.0)
        f0 = 8 + 9 * k
        M.set_emission_strength(bm, f0 - 1, 0.0)
        M.set_emission_strength(bm, f0 + 3, level)
        level *= 0.7
    s = heat.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 0.0), (18, 0.0), (40, 1.2)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    B._camera("CamB4_15", [(1, tuple(pts[1]), (-9.0, -4.0, 1.4), 45, 11.0), (134, tuple(pts[1]), (-8.0, -4.4, 1.6), 45, 11.0)])
    B._camera("CamB4_16", [(1, (-6.0, 0, 1.2), (-8.0, -14.0, 3.0), 30, 11.0), (120, (1.0, 0, 1.2), (1.0, -36.0, 6.0), 30, 11.0)])


def build(variant="silver", seed=41):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.01, 0.012, 0.02), horizon=(0.004, 0.005, 0.008), bottom=(0.001, 0.001, 0.002))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"silver": silver, "stack": stack, "mirror": mirror, "scan": lambda s, r: mirror(s, r, scan=True),
     "atoms": atoms, "space": space, "hall": hall, "explode": explode, "bounce": bounce}[variant](sc, rnd)
    return sc


def after_style(style, shot_id):
    import b2_scenes
    b2_scenes.after_style(style, shot_id)
    if shot_id == "B4_08":                  # show the cyan silicon-atom ruler in the SEM look
        cyan = M.emission("RulerCyan", (0.2, 0.85, 0.95), 4.0)
        for ob in bpy.data.objects:
            if ob.get("ruler"):
                ob.hide_render = False
                ob.data.materials.clear()
                ob.data.materials.append(cyan)
    if shot_id == "B4_07":                  # the smooth surface fades as atoms resolve
        surf = bpy.data.objects.get("Surface")
        if surf:
            _key(surf, 1, hide_render=False)
            _key(surf, 100, hide_render=True)
