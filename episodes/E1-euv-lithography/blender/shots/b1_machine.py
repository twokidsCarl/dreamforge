"""B1_25 (fab hall with the drive-laser beam tube) and B1_28/B1_29 (light leaving the source and
heading into the scanner) — uses build_machine's stylised layout."""
import math

import bpy

import build_machine as BM
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 240
ORANGE = (1.0, 0.42, 0.12)
SLAB_TOP, SLAB_T, SUB_FLOOR = -2.2, 0.6, -8.0       # fab floor (fab_hall), waffle slab, sub-fab floor
CUT_Y = -4.0                                          # section plane: everything nearer the camera is cut away


def _box(name, loc, size, mat, role="env"):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    ob.data.materials.append(mat)
    styles.tag(ob, role)
    return ob


def _tube(name, a, b, r, mat):
    from mathutils import Vector
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=(b - a).length, vertices=32, location=(a + b) / 2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    for pl in ob.data.polygons:
        pl.use_smooth = True
    ob.data.materials.append(mat)
    styles.tag(ob, "structure")
    return ob


def subfab_section():
    """B1_25: a cut-away of two floors. The drive laser stands in the sub-fab "along with its RF generators and
    water-to-water heat exchangers"; "turning mirrors" send the beam "from the sub-fab to the fab through the
    waffle-slab floor" (FOM17 p.176, Fig. 1 "Fab Floor" over "Sub-Fab Floor"; F62). Up to ~30 m of beam path (F6).
    Layout of the boxes, heights and the hall are stylised (示意); people are silhouettes for scale."""
    import figures
    BM.fab_hall(people=0)
    BM.machine(with_path=False)
    for ob in list(bpy.data.objects):                  # open the dollhouse: the hall floor and front columns go
        if ob.name == "HallFloor" or (ob.name.startswith("Col") and ob.name.endswith("-14")):   # mesh-baked
            bpy.data.objects.remove(ob, do_unlink=True)
    concrete = M.principled("SlabConcrete", (0.42, 0.42, 0.43), roughness=0.85)
    cutface = M.principled("SectionCut", (0.62, 0.62, 0.63), roughness=0.9)
    # waffle slab: a grid of ribs with square through-holes, cut at CUT_Y
    zc = SLAB_TOP - SLAB_T / 2
    for k, x in enumerate(range(-30, 31, 1)):
        _box(f"RibX{k}", (x * 1.2, (CUT_Y + 16) / 2, zc), (0.25, 16 - CUT_Y, SLAB_T), concrete)
    for k in range(int((16 - CUT_Y) / 1.2)):                     # the cut runs through a row of holes, so the
        y = CUT_Y + 0.6 + k * 1.2                                    # section shows ribs with open squares between
        _box(f"RibY{k}", (0, y, zc), (72, 0.25, SLAB_T), concrete)
    _box("RaisedFloor", (0, (CUT_Y + 16) / 2, SLAB_TOP + 0.02), (72, 16 - CUT_Y, 0.04),
         M.principled("FabFloorTile", (0.55, 0.56, 0.58), roughness=0.35))
    _box("SubFloor", (0, (CUT_Y + 16) / 2, SUB_FLOOR - 0.3), (72, 16 - CUT_Y, 0.6), cutface)
    _box("Foundation", (0, (CUT_Y + 16) / 2, SUB_FLOOR - 3.6), (72, 16 - CUT_Y, 6.0),
         M.principled("Ground", (0.07, 0.07, 0.075), roughness=0.95))
    _box("SubBackWall", (0, 16, (SUB_FLOOR + SLAB_TOP) / 2), (72, 0.3, SLAB_TOP - SUB_FLOOR),
         M.principled("SubWall", (0.12, 0.125, 0.135), roughness=0.7))
    lamp = M.emission("SubLamp", (0.9, 0.93, 1.0), 4.0)
    for k, x in enumerate(range(-30, 31, 5)):
        _box(f"SubLamp{k}", (x, 2.0, SLAB_TOP - SLAB_T - 0.08), (0.18, 9.0, 0.06), lamp)
    # the beam path rises at the source unit's optical platform (build_machine: beside the vessel, +x)
    xr = BM.PLASMA[0] + 2.6
    # laser chain on the sub-fab floor: seed module, pre-amplifier, four power amplifiers (F6, TRUMPF)
    cab = M.principled("LaserCabinet", (0.78, 0.8, 0.82), roughness=0.4)
    seam = M.principled("LaserSeam", (0.1, 0.1, 0.11), roughness=0.6)
    units = [("Seed", -27.0, 1.6, 1.6), ("PreAmp", -24.6, 2.2, 1.9)] + \
            [(f"PA{k + 1}", -20.6 + 4.4 * k, 3.6, 2.6) for k in range(4)]
    tube_z = SUB_FLOOR + 3.0
    for name, x, ln, h in units:
        _box(f"Laser{name}", (x, 0.6, SUB_FLOOR + h / 2), (ln, 2.2, h), cab, role="structure")
        for sx in (-0.3, 0.3):
            _box(f"Laser{name}Seam{sx}", (x + sx * ln, -0.505, SUB_FLOOR + h / 2), (0.02, 0.01, h * 0.9), seam)
        _tube(f"Laser{name}Feed", (x, 0.6, SUB_FLOOR + h), (x, 0.6, tube_z), 0.12,
              M.principled("FeedSteel", (0.6, 0.62, 0.65), metallic=0.9, roughness=0.3))
    # RF generators and heat exchangers stand beside the laser (FOM17 p.176)
    _box("RFGen", (-17.0, 4.5, SUB_FLOOR + 1.0), (2.4, 1.4, 2.0), cab, role="structure")
    _box("HeatExch", (-11.0, 4.5, SUB_FLOOR + 0.8), (2.0, 1.4, 1.6), cab, role="structure")
    steel = M.principled("BTSteel", (0.62, 0.64, 0.67), metallic=0.9, roughness=0.28)
    x0 = units[0][1]
    _tube("BTHorizontal", (x0, 0.6, tube_z), (xr, 0.6, tube_z), 0.28, steel)
    _box("TurnMirrorLow", (xr, 0.6, tube_z), (0.9, 0.9, 0.9), steel, role="structure")
    _tube("BTVertical", (xr, 0.6, tube_z), (xr, 0.6, 0.85), 0.28, steel)
    _box("TurnMirrorHigh", (xr, 0.6, 0.85), (0.8, 0.8, 0.8), steel, role="structure")
    # an orange light dot racing along the tube (示意: the 10.6 um beam is invisible and enclosed)
    dot = M.emission("TubeDot", ORANGE, 40.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x0, 0.6 - 0.32, tube_z))
    d = bpy.context.object
    d.name = "TubeDot"
    d.data.materials.append(dot)
    styles.tag(d, "emitter")
    run_h, run_v = xr - x0, 0.85 - tube_z
    for f in range(1, FRAMES + 1):                                   # one pass every 60 frames
        u = ((f - 1) % 60) / 60 * (run_h + run_v)
        d.location = (x0 + min(u, run_h), 0.6 - 0.32, tube_z + max(0.0, u - run_h))
        d.keyframe_insert("location", frame=f)
        d.scale = (2.5, 1, 1) if u < run_h else (1, 1, 2.5)
        d.keyframe_insert("scale", frame=f)
    for fc in C.fcurves(d.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    sil = bpy.data.materials.get("Silhouette") or M.principled("Silhouette", (0.01, 0.01, 0.012), roughness=0.9)
    for k, (x, y, z, pose, fa) in enumerate(((-22.4, -1.4, SUB_FLOOR, "work", 180), (-15.0, -1.8, SUB_FLOOR, "stand", 160),
                                             (-6.0, -1.2, SUB_FLOOR, "walk", 90), (1.5, -2.6, SLAB_TOP, "stand", 200),
                                             (-4.5, -2.9, SLAB_TOP, "work", 180))):
        figures.person(f"Scale{k}", (x, y, z), pose=pose, facing=fa, mat=sil)
    B._area("SubKey", (-10, -14, -3.5), (1.25, 0, 0), 30, 5000, (0.8, 0.85, 1.0), size_y=6)
    B._area("FabKey", (0, -12, 6), (1.0, 0, 0), 30, 4000, (0.8, 0.85, 1.0))
    # front section view, slow drift along the beam from the laser toward the machine
    B._camera("CamB1_25", [(1, (-9.0, 0, -2.4), (-11.0, -30.0, -2.0), 26, 8.0),
                           (160, (-5.5, 0, -2.3), (-6.5, -29.0, -1.9), 26, 8.0)])


def build(variant="machine"):
    sc = C.reset_scene(FRAMES)
    C.set_color_management(exposure=0.4)
    if variant == "hall":
        C.set_world(top=(0.02, 0.022, 0.03), horizon=(0.01, 0.011, 0.015), bottom=(0.002, 0.002, 0.003))
        subfab_section()
        return sc
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    path, pmat = BM.machine()
    path.data.bevel_factor_end = 0.0
    path.data.keyframe_insert("bevel_factor_end", frame=1)
    path.data.bevel_factor_end = 1.0
    path.data.keyframe_insert("bevel_factor_end", frame=100)
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    B._area("MRim", (-6, 8, 4), (1.2, 0, 3.0), 10, 1500, (0.5, 0.7, 1.0))
    # High-NA layout (build_machine): source unit on +x, IF between it and the illuminator, scanner at x ~ 0
    px, ifp = BM.PLASMA, BM.IF
    B._camera("CamB1_28", [(1, ((px[0] + ifp[0]) / 2, 0, 1.0), (px[0] + 2.0, -8.5, 2.4), 28, 8.0),
                           (113, (1.6, 0, 1.2), (2.8, -11.0, 3.0), 28, 8.0)])
    B._camera("CamB1_29", [(100, ifp, (ifp[0] - 1.7, -2.4, ifp[2] + 0.45), 35, 4.0),
                           (160, ifp, (ifp[0] - 0.95, -1.8, ifp[2] + 0.3), 35, 4.0)])     # a slow push, never still
    return sc


def after_style(style, shot_id):
    """B1_29 "一束细细的紫光": seen from ~3 units the 0.025 light-path bevel filled the frame as a thick bar; here the
    beam is a thin line (the energy style already keeps it saturated violet)."""
    if shot_id == "B1_29":
        path = bpy.data.objects.get("LightPath")
        if path:
            path.data.bevel_depth = 0.008
