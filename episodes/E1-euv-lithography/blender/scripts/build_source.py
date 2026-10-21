"""EUV light source: droplet generator, tin droplets, drive-laser pulses, plasma, collector, IF.

Coordinate frame: optical axis = +X. Plasma site (collector primary focus) at the origin,
intermediate focus (IF) on +X. Droplets fly along +Y across the focus.

Scale: near the droplet, 1 unit = 125 um, so droplet and pancake sizes are true relative to
each other. The collector and IF are NOT to scale (real collector is ~0.6 m across); the
shot must carry the "示意 / 非比例" tag.
"""
import math
import bmesh
import bpy
from mathutils import Matrix

import materials as M
import styles

UNIT_UM = 125.0                      # micrometres per Blender unit near the droplet
DROPLET_DIAMETER_UM = 25.0           # F3
DROPLET_SPEED_MS = 70.0              # F3 (shown as a label; motion is slow-motion)
PANCAKE_DIAMETER_UM = 300.0          # F4b
DROPLET_R = DROPLET_DIAMETER_UM / 2 / UNIT_UM      # 0.1
PANCAKE_R = PANCAKE_DIAMETER_UM / 2 / UNIT_UM      # 1.2

# Collector: ellipsoid with foci F1 = origin, F2 = IF. Stylised dimensions.
IF_X = 14.0
COLLECTOR_VERTEX_X = -4.0            # mirror apex behind the plasma
COLLECTOR_RIM_X = -0.35              # rim just behind the droplet path
COLLECTOR_HOLE_R = 0.7               # central aperture for the drive laser


def _link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def _mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _link(bpy.data.objects.new(name, me))


def _shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def droplet(name="Droplet", segments=48):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=DROPLET_R)
    obj = _mesh_obj(name, bm)
    _shade_smooth(obj)
    obj.data.materials.append(M.tin())
    return obj


def pancake(name="Pancake", rings=48, segments=128):
    """Thin tin sheet left by the pre-pulse, facing the laser (+X): radius PANCAKE_R at scale 1,
    thin centre and a thicker rim, with low-frequency ripples. Shape is illustrative."""
    bm = bmesh.new()
    prof = []
    for i in range(rings + 1):
        r = PANCAKE_R * i / rings
        t = 0.0004 + 0.012 * (i / rings) ** 10      # half-thickness: ~50 nm sheet, ~3 um beaded rim (ARCNL)
        prof.append((r, t))
    prof.append((PANCAKE_R * 1.02, 0.0))
    top, bot = [], []
    for r, t in prof:
        rt, rb = [], []
        for j in range(segments):
            th = 2 * math.pi * j / segments
            y, z = r * math.cos(th), r * math.sin(th)
            rt.append(bm.verts.new((t, y, z)))
            rb.append(bm.verts.new((-t, y, z)))
        top.append(rt)
        bot.append(rb)
    for rows, flip in ((top, False), (bot, True)):
        for i in range(len(rows) - 1):
            for j in range(segments):
                k = (j + 1) % segments
                q = (rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j])
                bm.faces.new(q[::-1] if flip else q)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_obj(name, bm)
    _shade_smooth(obj)
    tex = bpy.data.textures.new(name + "Ripple", "CLOUDS")
    tex.noise_scale = 0.8
    disp = obj.modifiers.new("Ripple", "DISPLACE")
    disp.texture = tex
    disp.direction = "X"
    disp.texture_coords = "LOCAL"
    disp.strength = 0.08
    disp.mid_level = 0.5
    obj.data.materials.append(M.tin("TinSheet", roughness=0.22))
    return obj


def droplet_stream(count, spacing, name="DropletStream"):
    """A row of droplets trailing behind the object's origin along -Y (array modifier)."""
    obj = droplet(name)
    arr = obj.modifiers.new("Array", "ARRAY")
    arr.count = count
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = (0, -spacing, 0)
    return obj


def nozzle(tip_y, name="DropletGenerator"):
    """Stylised droplet-generator nozzle pointing +Y. Real nozzle geometry is not public."""
    bm = bmesh.new()
    # tapered tip
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.9, radius2=0.12, depth=2.4)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, tip_y - 1.2, 0))
    tip = _mesh_obj(name, bm)
    _shade_smooth(tip)
    tip.data.materials.append(M.polished_steel("NozzleSteel", 0.12))
    bev = tip.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 3
    # body
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=1.6, radius2=1.6, depth=6.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, tip_y - 2.4 - 3.0, 0))
    body = _mesh_obj(name + "Body", bm)
    _shade_smooth(body)
    body.data.materials.append(M.dark_anodized("NozzleBody"))
    return tip, body


def _ellipse_r(x):
    """Radius of the collector ellipsoid of revolution at axial position x."""
    c = IF_X / 2
    a = c - COLLECTOR_VERTEX_X
    b = math.sqrt(a * a - c * c)
    t = (x - c) / a
    return b * math.sqrt(max(0.0, 1 - t * t))


def collector(rings=64, segments=128, thickness=0.18):
    """Ellipsoidal normal-incidence collector: surface of revolution between the central hole
    and the rim, solidified, with the Mo/Si iridescent material."""
    # find x where radius == hole radius (near the apex)
    lo, hi = COLLECTOR_VERTEX_X, COLLECTOR_RIM_X
    for _ in range(60):
        mid = (lo + hi) / 2
        if _ellipse_r(mid) < COLLECTOR_HOLE_R:
            lo = mid
        else:
            hi = mid
    x0 = hi
    bm = bmesh.new()
    grid = []
    for i in range(rings + 1):
        # denser rings near the apex where curvature is high
        u = (i / rings) ** 1.6
        x = x0 + (COLLECTOR_RIM_X - x0) * u
        r = _ellipse_r(x)
        row = []
        for j in range(segments):
            th = 2 * math.pi * j / segments
            row.append(bm.verts.new((x, r * math.cos(th), r * math.sin(th))))
        grid.append(row)
    for i in range(rings):
        for j in range(segments):
            k = (j + 1) % segments
            bm.faces.new((grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_obj("Collector", bm)
    _shade_smooth(obj)
    sol = obj.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = 1.0
    # ASML's photographs show the collector as a plain mirror: no rainbow bands (the multilayer is invisible)
    obj.data.materials.append(M.principled("CollectorMirror", (0.86, 0.85, 0.82), metallic=1.0, roughness=0.03))
    obj.data.materials.append(M.dark_anodized("CollectorBack"))
    sol.material_offset = 1
    sol.material_offset_rim = 1
    return obj


def collector_housing():
    """Dark ring frame around the collector rim (stylised)."""
    r = _ellipse_r(COLLECTOR_RIM_X)
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.25, minor_radius=0.28,
                                     major_segments=128, minor_segments=24,
                                     location=(COLLECTOR_RIM_X - 0.1, 0, 0),
                                     rotation=(0, math.pi / 2, 0))
    ring = bpy.context.object
    ring.name = "CollectorRing"
    _shade_smooth(ring)
    ring.data.materials.append(M.polished_steel("RingSteel", 0.25))
    return ring


def laser_beam(name, radius, color, x_from=-40.0, x_to=0.0):
    """Drive-laser pulse along +X ending at the plasma site. CO2 light is infrared and
    invisible; the beam is a visual stand-in. Returns (object, material, length); animate
    with materials.set_beam (front runs from -length/2 to +length/2 = the target)."""
    length = x_to - x_from
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=48,
                                        location=((x_from + x_to) / 2, 0, 0),
                                        rotation=(0, math.pi / 2, 0))
    beam = bpy.context.object
    beam.name = name
    _shade_smooth(beam)
    mat = M.beam(name + "Mat", color, radius, length)
    beam.data.materials.append(mat)
    return beam, mat, length


def debris(frame, location, count=500, speed=2.6, lifetime=110, seed=3):
    """Burst of glowing tin fragments flung out by the main pulse (no gravity: vacuum)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.25, location=location)
    emitter = bpy.context.object
    emitter.name = "DebrisEmitter"
    emitter.show_instancer_for_render = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, segments=8, ring_count=4,
                                         location=(0, 0, -200))
    frag = bpy.context.object
    frag.name = "DebrisFragment"
    frag.data.materials.append(M.debris())
    ps = emitter.modifiers.new("Debris", "PARTICLE_SYSTEM").particle_system
    ps.seed = seed
    st = ps.settings
    st.count = count
    st.frame_start = frame
    st.frame_end = frame + 3
    st.lifetime = lifetime
    st.lifetime_random = 0.5
    st.normal_factor = speed
    st.factor_random = speed * 0.6
    st.effector_weights.gravity = 0.0
    st.render_type = "OBJECT"
    st.instance_object = frag
    st.particle_size = 1.0
    st.size_random = 0.7
    return emitter


def plasma(name="Plasma"):
    """Emissive turbulent volume (radius 1 in object space) plus a hot core."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0))
    shell = bpy.context.object
    shell.name = name
    vol = M.volume_glow(name + "Vol", (0.45, 0.28, 1.0), density=4.0, emission_strength=0.0,
                        noise_scale=2.2, falloff=True, core_color=(1.0, 0.88, 0.95))
    shell.data.materials.append(vol)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=48, ring_count=24, location=(0, 0, 0))
    core = bpy.context.object
    core.name = name + "Core"
    _shade_smooth(core)
    core_mat = M.emission(name + "CoreMat", (0.92, 0.88, 1.0), 0.0)
    core.data.materials.append(core_mat)
    bpy.ops.object.light_add(type="POINT", location=(0.3, 0, 0))
    light = bpy.context.object
    light.name = name + "Light"
    light.data.color = (0.78, 0.62, 1.0)
    light.data.energy = 0.0
    light.data.shadow_soft_size = 0.4
    light["keep_light"] = True
    return shell, vol, core, core_mat, light


def euv_cone(name="EUVCone"):
    """Converging EUV bundle from the collector rim to IF. EUV is invisible: stand-in only."""
    r = _ellipse_r(COLLECTOR_RIM_X)
    length = IF_X - COLLECTOR_RIM_X
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=r * 0.98, radius2=0.02, depth=length,
                                    location=(COLLECTOR_RIM_X + length / 2, 0, 0),
                                    rotation=(0, math.pi / 2, 0))
    cone = bpy.context.object
    cone.name = name
    mat = M.volume_glow(name + "Mat", (0.55, 0.45, 1.0), density=0.0, emission_strength=0.0)
    cone.data.materials.append(mat)
    return cone, mat


def light_rays(n=64, seed=5, name="EUVRay", radius=0.018):
    """Ray-traced EUV paths F1 -> collector -> F2: any ray leaving one focus of an ellipsoid
    reflects through the other. Tagged `rays` (shown in the energy and xray styles)."""
    import random
    from mathutils import Vector
    c = IF_X / 2
    a = c - COLLECTOR_VERTEX_X
    b2 = a * a - c * c
    rnd = random.Random(seed)
    mat = M.emission(name + "Mat", (0.62, 0.48, 1.0), 6.0)
    f2 = Vector((IF_X, 0, 0))
    rays, tries = [], 0
    while len(rays) < n and tries < 20000:
        tries += 1
        d = Vector((rnd.uniform(-1, 0), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
        if d.length < 1e-3:
            continue
        d.normalize()
        cos_t = d.x                                   # angle measured from +X (toward F2)
        r = b2 / (a - c * cos_t)
        p = d * r
        radial = (p.y ** 2 + p.z ** 2) ** 0.5
        if p.x > COLLECTOR_RIM_X or radial < COLLECTOR_HOLE_R * 1.3:
            continue
        cu = bpy.data.curves.new(f"{name}{len(rays)}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = radius
        sp = cu.splines.new("POLY")
        sp.points.add(2)
        for k, q in enumerate((Vector((0, 0, 0)), p, f2)):
            sp.points[k].co = (*q, 1)
        ob = bpy.data.objects.new(cu.name, cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
        styles.tag(ob, "rays")
        rays.append(ob)
    return rays, mat


def intermediate_focus(name="IF"):
    """Aperture plate at IF with a small glow point."""
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.25, vertices=96,
                                        location=(IF_X + 0.15, 0, 0), rotation=(0, math.pi / 2, 0))
    plate = bpy.context.object
    plate.name = name + "Plate"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.0, vertices=48,
                                        location=(IF_X + 0.15, 0, 0), rotation=(0, math.pi / 2, 0))
    hole = bpy.context.object
    hole.hide_render = hole.hide_viewport = True
    b = plate.modifiers.new("Hole", "BOOLEAN")
    b.object = hole
    b.operation = "DIFFERENCE"
    plate.data.materials.append(M.dark_anodized("IFPlate"))
    plate.visible_glossy = False   # its mirror image in the collector reads as a stray dark blob
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(IF_X, 0, 0))
    dot = bpy.context.object
    dot.name = name + "Glow"
    dot_mat = M.emission(name + "GlowMat", (0.7, 0.6, 1.0), 0.0)
    dot.data.materials.append(dot_mat)
    return plate, dot, dot_mat
