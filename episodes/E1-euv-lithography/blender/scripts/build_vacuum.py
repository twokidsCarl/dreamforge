"""Vacuum vessel surroundings: a large dark chamber with ribs, flanged ports and status LEDs.

Purely stylised context (real vessel internals are not public). It gives the macro shots
out-of-focus structure and bokeh, and gives the collector something to reflect besides black.
"""
import math
import random

import bpy

import materials as M
import styles

CHAMBER_R = 30.0
CHAMBER_H = 50.0


def _smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def wall_material():
    """Dark brushed metal with horizontal panel seams (bump from a wave texture)."""
    m = M.principled("ChamberWall", (0.06, 0.07, 0.085), metallic=0.85, roughness=0.42)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 0.08
    wave.inputs["Distortion"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.9
    ramp.color_ramp.elements[1].position = 1.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    return m


def chamber(seed=7):
    before = set(bpy.data.objects)
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_cylinder_add(radius=CHAMBER_R, depth=CHAMBER_H, vertices=192,
                                        location=(0, 0, 0))
    wall = bpy.context.object
    wall.name = "ChamberWall"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    _smooth(wall)
    wall.data.materials.append(wall_material())

    ring_mat = M.polished_steel("RibSteel", 0.3)
    for z in range(-20, 21, 8):
        bpy.ops.mesh.primitive_torus_add(major_radius=CHAMBER_R - 0.3, minor_radius=0.35,
                                         major_segments=192, minor_segments=12, location=(0, 0, z))
        rib = bpy.context.object
        rib.name = f"Rib{z}"
        _smooth(rib)
        rib.data.materials.append(ring_mat)

    flange = M.polished_steel("FlangeSteel", 0.2)
    glass = M.principled("PortGlass", (0.02, 0.05, 0.08), metallic=0.0, roughness=0.05,
                         emission=(0.25, 0.6, 1.0), emission_strength=0.6)
    led_cyan = M.emission("LedCyan", (0.2, 0.75, 1.0), 40.0)
    led_amber = M.emission("LedAmber", (1.0, 0.55, 0.15), 30.0)
    for i in range(14):
        th = rnd.uniform(0, 2 * math.pi)
        z = rnd.uniform(-12, 14)
        r = rnd.uniform(1.4, 3.2)
        cx, cy = (CHAMBER_R - 0.5) * math.cos(th), (CHAMBER_R - 0.5) * math.sin(th)
        rot = (0, math.pi / 2, th)
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.22, major_segments=96,
                                         minor_segments=12, location=(cx, cy, z), rotation=rot)
        rim = bpy.context.object
        _smooth(rim)
        rim.data.materials.append(flange)
        bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.86, depth=0.1, vertices=64,
                                            location=(cx * 1.005, cy * 1.005, z), rotation=rot)
        win = bpy.context.object
        win.data.materials.append(glass if i % 3 == 0 else M.dark_anodized(f"PortCap{i}"))
        # a few status LEDs next to every port: they become bokeh in the macro shots
        for k in range(rnd.randint(2, 5)):
            a = th + (r + 0.6 + 0.35 * k) / CHAMBER_R
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=12, ring_count=6,
                                                 location=((CHAMBER_R - 0.6) * math.cos(a),
                                                           (CHAMBER_R - 0.6) * math.sin(a),
                                                           z - r * 0.6))
            led = bpy.context.object
            led.data.materials.append(led_amber if (i + k) % 4 == 0 else led_cyan)
    styles.tag_new(before, "env")
    return wall


def source_vessel(r=15.0, x_back=-6.5, x_shoulder=2.0, x_neck=12.6, r_neck=1.6, x_end=14.4):
    """Stylised source vessel: a drum around collector and plasma that narrows into a cone
    toward the intermediate focus. Tagged `shell` (ghost glass in xray, linework in blueprint)."""
    import bmesh
    from mathutils import Matrix
    before = set(bpy.data.objects)
    prof = [(x_back, 0.0), (x_back, r), (x_shoulder, r), (x_neck, r_neck), (x_end, r_neck)]
    bm = bmesh.new()
    verts = [bm.verts.new((x, 0.0, rr)) for x, rr in prof]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(1, 0, 0), angle=2 * math.pi,
                   steps=128, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("SourceVessel")
    bm.to_mesh(me)
    bm.free()
    shell = bpy.data.objects.new("SourceVessel", me)
    bpy.context.scene.collection.objects.link(shell)
    _smooth(shell)
    shell.data.materials.append(M.polished_steel("VesselSteel", 0.35))
    styles.tag(shell, "shell")
    steel = M.polished_steel("VesselFlange", 0.25)
    for x, rr in ((x_back + 0.3, r), (x_shoulder, r), (x_neck, r_neck)):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr + 0.15, minor_radius=0.22 if rr > 3 else 0.12,
                                         major_segments=128, minor_segments=12, location=(x, 0, 0),
                                         rotation=(0, math.pi / 2, 0))
        ring = bpy.context.object
        _smooth(ring)
        ring.data.materials.append(steel)
        styles.tag(ring, "structure")
    # ports: drive-laser entry at the back, droplet generator at -Y and the droplet catcher opposite it at +Y
    # (one horizontal line through the plasma, research/visual/euv_source.md), diagnostics around
    for loc, rot, rad in (((x_back - 0.6, 0, 0), (0, math.pi / 2, 0), 1.2),
                          ((0.0, -r - 0.5, 0), (math.pi / 2, 0, 0), 1.8),
                          ((0.0, r + 0.5, 0), (math.pi / 2, 0, 0), 1.5),
                          ((-2.0, 0, r + 0.5), (0, 0, 0), 1.4),
                          ((-1.0, r * 0.7 + 0.4, r * 0.7 + 0.4), (-math.pi / 4, 0, 0), 1.1)):
        bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=1.2, vertices=64, location=loc,
                                            rotation=rot)
        port = bpy.context.object
        port.data.materials.append(steel)
        styles.tag(port, "structure")
    return shell
