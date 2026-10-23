"""Render 6 True-3D Smooth-Shaded Continuous Molecular, Microbial, Retinal & Neural Circuit Sequences:
1. microbe_3d (16f): 3D Chlamydomonas reinhardtii with glowing orange eyespot (stigma) + beating dual flagella + Halobacterium archaea rods swimming toward light (for SF03 & SF16).
2. chr2_3d (16f): Front-cutaway 3D phospholipid bilayer + ChR2 7-TM dimer + all-trans->13-cis retinal isomerization + 470nm blue laser cone + Na+/Ca2+ ion stream through opening pore (for SF06, SF08, SF09, SF15, SF16).
3. br_pump_3d (16f): Front-cutaway 3D Halobacterium purple membrane BR proton pump (uphill single H+ active transport) vs ChR2 downhill high-flux ion channel (for SF15, SF16).
4. nphr_3d (16f): Front-cutaway 3D Halorhodopsin (NpHR) 7-TM chloride pump under 590nm yellow/amber light pumping Cl- ions inward (for SF18).
5. retina_3d (16f): 3D Neuromorphic goggles 595nm projector array + cutaway eyeball (cornea/lens/vitreous) + 595nm amber light beams activating ChrimsonR RGC array & optic nerve spikes (for SF11, SF20, SF21, SF22).
6. hippo_cone_3d (16f): 3D In-situ brain optical fiber ferrule emitting 470nm volumetric blue light cone + ChR2-positive Hippocampus DG / Orexin neurons firing action potentials (for SF01, SF07, SF12, SF13, SF14, SF19).
"""
import bpy, mathutils, math, sys, os, random
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT_DIR = argv[0] if argv else '/workspace/e2work/v8/renders/mol_retina_3d'
SAMPLES = int(argv[1]) if len(argv) > 1 else 10
RES = (int(argv[2]), int(argv[3])) if len(argv) > 3 else (960, 540)
ONLY_SEQ = argv[4] if len(argv) > 4 else 'all'
os.makedirs(OUT_DIR, exist_ok=True)

def smooth_obj(ob):
    if ob and ob.type == 'MESH' and ob.data:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob

def make_mat(name, base_col, rough=0.32, metal=0.0, trans=0.0, sss=0.0, emit_col=None, emit_str=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*base_col, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = trans
    if 'Subsurface Weight' in bsdf.inputs and sss > 0:
        bsdf.inputs['Subsurface Weight'].default_value = sss
        bsdf.inputs['Subsurface Scale'].default_value = 0.05
    if emit_col is not None:
        bsdf.inputs['Emission Color'].default_value = (*emit_col, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emit_str
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
    return m, bsdf

def setup_cycles(sc):
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    sc.cycles.sample_clamp_direct = 4.0
    sc.cycles.sample_clamp_indirect = 2.5
    sc.cycles.max_bounces = 3
    sc.cycles.diffuse_bounces = 1
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 2
    sc.cycles.volume_bounces = 0
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.cycles.samples = SAMPLES
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.008, 0.014, 0.035, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0

def add_lights_and_cam(sc, cam_loc, tgt_loc, lens=50, fstop=4.0):
    bpy.ops.object.light_add(type='AREA', location=(3.5, -3.5, 4.5))
    kl = bpy.context.object; kl.data.energy = 260; kl.data.size = 3.0; kl.data.color = (1.0, 0.95, 0.88)
    bpy.ops.object.light_add(type='AREA', location=(-4.0, 3.0, 2.5))
    rl = bpy.context.object; rl.data.energy = 300; rl.data.size = 2.5; rl.data.color = (0.35, 0.68, 1.0)
    bpy.ops.object.light_add(type='AREA', location=(0.0, -4.5, -2.5))
    fl = bpy.context.object; fl.data.energy = 110; fl.data.size = 3.5; fl.data.color = (0.45, 0.35, 0.75)

    cam = bpy.data.cameras.new('cam')
    cam.lens = lens
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = fstop
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    tgt = bpy.data.objects.new('tgt', None)
    sc.collection.objects.link(tgt)
    tgt.location = tgt_loc
    for L in (kl, rl, fl):
        c = L.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    tc = co.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    cam.dof.focus_object = tgt
    co.location = cam_loc
    return co, tgt, kl, rl

def build_bilayer(sc, nx=13, ny=5, spacing=0.38, hole_radius=0.88):
    """Build smooth-shaded 3D phospholipid bilayer with front cutaway window (`y < -0.10 & |x| < 1.25`) so pore is 100% unobstructed."""
    mat_head, _ = make_mat('lipid_head', (0.90, 0.66, 0.22), rough=0.25, sss=0.35)
    mat_tail, _ = make_mat('lipid_tail', (0.38, 0.30, 0.18), rough=0.50)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.145, location=(0, 0, -100))
    proto_head = smooth_obj(bpy.context.object); proto_head.data.materials.append(mat_head)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.038, depth=0.62, location=(0, 0, -100))
    proto_tail = smooth_obj(bpy.context.object); proto_tail.data.materials.append(mat_tail)

    heads = []
    random.seed(12)
    for ix in range(-nx, nx + 1):
        for iy in range(-ny, ny + 1):
            x = ix * spacing + random.uniform(-0.03, 0.03)
            y = iy * spacing + random.uniform(-0.03, 0.03)
            r = math.hypot(x, y)
            # Front cutaway window so camera at -Y sees directly into the central transmembrane channel!
            if r < hole_radius or (y < -0.05 and abs(x) < 1.20):
                continue
            for sign in (-1, 1):
                z0 = sign * 0.72 + 0.05 * math.sin(x * 1.2 + y * 0.9)
                h_ob = bpy.data.objects.new(f'lh_{ix}_{iy}_{sign}', proto_head.data)
                sc.collection.objects.link(h_ob)
                h_ob.location = (x, y, z0)
                heads.append((h_ob, x, y, z0, sign))
                for tx_off in (-0.055, 0.055):
                    t_ob = bpy.data.objects.new(f'lt_{ix}_{iy}_{sign}_{tx_off}', proto_tail.data)
                    sc.collection.objects.link(t_ob)
                    t_ob.location = (x + tx_off, y, z0 - sign * 0.36)
                    t_ob.rotation_euler = (random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), 0)
    return heads

# ==============================================================================
# SEQ 0: microbe_3d (16 frames) — 3D Chlamydomonas Phototaxis + Eyespot + Beating Flagella + Halobacteria
# ==============================================================================
def render_microbe_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.0, -4.8, 1.0)), Vector((0.0, 0.0, 0.0)), lens=50, fstop=4.0)

    # Right (+0.75): 3D Chlamydomonas cell (translucent green outer wall + chloroplast cup + glowing orange eyespot + 2 flagella)
    mat_wall, _ = make_mat('chlamy_wall', (0.18, 0.78, 0.45), rough=0.15, trans=0.75, sss=0.25, alpha=0.45)
    mat_chloro, _ = make_mat('chloroplast', (0.12, 0.58, 0.28), rough=0.35, sss=0.40, emit_col=(0.10, 0.45, 0.22), emit_str=0.25)
    mat_eyespot, bsdf_eye = make_mat('eyespot', (1.0, 0.38, 0.05), rough=0.15, emit_col=(1.0, 0.42, 0.08), emit_str=5.5)
    mat_flag, _ = make_mat('flagella', (0.35, 0.92, 0.65), rough=0.25, emit_col=(0.25, 0.85, 0.55), emit_str=0.8)

    chlamy = bpy.data.objects.new('chlamy_root', None)
    sc.collection.objects.link(chlamy)
    chlamy.location = (0.75, 0.0, -0.10)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.85, location=(0, 0, 0))
    cell = smooth_obj(bpy.context.object); cell.scale = (0.88, 0.88, 1.08); cell.data.materials.append(mat_wall); cell.parent = chlamy

    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=16, radius=0.68, location=(0, 0, -0.08))
    chl = smooth_obj(bpy.context.object); chl.scale = (0.85, 0.85, 0.95); chl.data.materials.append(mat_chloro); chl.parent = chlamy

    # Glowing orange eyespot (stigma) containing ChR1/ChR2 photoreceptors
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.18, location=(-0.58, -0.35, 0.15))
    esp = smooth_obj(bpy.context.object); esp.scale = (0.55, 0.9, 1.1); esp.data.materials.append(mat_eyespot); esp.parent = chlamy

    # Two 3D beating flagella curves
    flag_curves = []
    for sgn in (-1, 1):
        cu = bpy.data.curves.new(f'flag_{sgn}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.032; cu.bevel_resolution = 4
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(4)
        fob = bpy.data.objects.new(f'flag_{sgn}', cu); sc.collection.objects.link(fob)
        fob.data.materials.append(mat_flag); fob.parent = chlamy
        flag_curves.append((sp, sgn))

    # Left (-1.25): Halobacterium salinarum purple-membrane archaea rods
    mat_halo, _ = make_mat('halobacteria', (0.68, 0.22, 0.82), rough=0.28, sss=0.35, emit_col=(0.58, 0.15, 0.75), emit_str=0.45)
    halos = []
    for i, (hx, hy, hz, rz_ang) in enumerate([(-1.35, 0.1, 0.25, 0.3), (-1.15, -0.2, -0.35, -0.25), (-1.55, 0.3, -0.15, 0.5), (-0.95, 0.25, 0.55, -0.4)]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.16, depth=0.75, location=(hx, hy, hz), rotation=(0.3, 0.5, rz_ang))
        hrod = smooth_obj(bpy.context.object); hrod.data.materials.append(mat_halo)
        halos.append((hrod, hx, hy, hz, i))

    # Top-left Blue-Cyan Light Beam Cone illuminating the eyespot
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.45, radius2=0.25, depth=4.2, location=(-0.3, 0.0, 1.25), rotation=(0, math.radians(-32), 0))
    lcone = smooth_obj(bpy.context.object)
    mat_lcone, _ = make_mat('phototaxis_beam', (0.15, 0.68, 1.0), rough=0.1, trans=0.95, emit_col=(0.15, 0.68, 1.0), emit_str=0.65, alpha=0.14)
    lcone.data.materials.append(mat_lcone)

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        phase = u * math.pi * 4
        # Swim toward light beam (up-left) + rotate slightly
        chlamy.location = (0.85 - 0.30 * u, 0.0, -0.18 + 0.28 * u + 0.04 * math.sin(phase))
        chlamy.rotation_euler = (0.08 * math.sin(phase), -0.18, 0.25 * u)
        bsdf_eye.inputs['Emission Strength'].default_value = 4.5 + 2.5 * math.sin(phase)

        # Animate flagellar breaststroke wave
        for sp, sgn in flag_curves:
            for k, bp in enumerate(sp.bezier_points):
                t = k / 4.0
                wave = math.sin(phase - t * 3.5) * (0.28 * t)
                bp.co = (sgn * (0.08 + 0.55 * t + wave * 0.4), 0.12 * math.cos(phase - t * 2.5) * t, 0.88 + 0.65 * t - 0.25 * (t ** 2) + wave * 0.3)
                bp.handle_left_type = bp.handle_right_type = 'AUTO'

        for hrod, hx, hy, hz, idx in halos:
            hrod.location = (hx + 0.12 * u, hy, hz + 0.06 * math.sin(phase + idx))
            hrod.rotation_euler.z += 0.04

        co.location = Vector((-0.45 + 0.90 * u, -4.75 + 0.35 * u, 0.95 - 0.20 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'microbe_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[microbe_3d] {f}/{n_frames}', flush=True)

# ==============================================================================
# SEQ 1: chr2_3d (16 frames) — Front-Cutaway ChR2 7-TM Dimer + Retinal Isomerization + Na+/Ca2+ Stream
# ==============================================================================
def render_chr2_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.0, -4.4, 1.15)), Vector((0.0, 0.0, -0.05)), lens=52, fstop=4.0)
    heads = build_bilayer(sc, nx=13, ny=5, spacing=0.38, hole_radius=0.92)

    mat_tm, bsdf_tm = make_mat('chr2_tm', (0.08, 0.62, 0.78), rough=0.20, trans=0.35, sss=0.25, emit_col=(0.05, 0.48, 0.90), emit_str=0.35)
    mat_tm2, _ = make_mat('chr2_tm2', (0.06, 0.42, 0.58), rough=0.28, trans=0.25, sss=0.20)
    helices = []
    # Leave front helix slot open (cross-section cutaway) so internal retinal & pore are 100% visible!
    for k in range(7):
        ang = k * (2 * math.pi / 7.0) + 0.35
        hx = 0.44 * math.cos(ang)
        hy = 0.40 * math.sin(ang)
        if hy < -0.25:
            continue  # front cutaway helix omitted so viewer sees inside the pore!
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.135, depth=1.72, location=(hx, hy, 0.0))
        h = smooth_obj(bpy.context.object)
        h.rotation_euler = (0.12 * math.sin(ang), -0.12 * math.cos(ang), ang)
        h.data.materials.append(mat_tm if k in (0, 1, 2, 5, 6) else mat_tm2)
        helices.append((h, ang, hx, hy))

    # All-trans retinal chromophore inside pore pocket
    mat_ret, bsdf_ret = make_mat('retinal', (1.0, 0.48, 0.08), rough=0.15, emit_col=(1.0, 0.52, 0.10), emit_str=4.0)
    ret_pivot = bpy.data.objects.new('ret_pivot', None)
    sc.collection.objects.link(ret_pivot)
    ret_pivot.location = (0.0, -0.05, 0.12)
    for i in range(5):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.072 if i > 0 else 0.115, location=(i * 0.085 - 0.16, 0, (i % 2) * 0.035))
        sp = smooth_obj(bpy.context.object)
        sp.data.materials.append(mat_ret)
        sp.parent = ret_pivot

    # 470nm Volumetric Blue Light Cone
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.15, radius2=0.18, depth=3.6, location=(0.0, 0.0, 1.65))
    cone = smooth_obj(bpy.context.object)
    mat_cone, bsdf_cone = make_mat('blue_cone', (0.10, 0.55, 1.0), rough=0.1, trans=0.95, emit_col=(0.12, 0.58, 1.0), emit_str=0.85, alpha=0.14)
    cone.data.materials.append(mat_cone)

    # Glowing Na+ (cyan) and Ca2+ (gold) ions streaming through the pore
    mat_na, _ = make_mat('ion_na', (0.25, 0.88, 1.0), rough=0.1, emit_col=(0.20, 0.82, 1.0), emit_str=6.0)
    mat_ca, _ = make_mat('ion_ca', (1.0, 0.78, 0.20), rough=0.1, emit_col=(1.0, 0.72, 0.18), emit_str=6.0)
    ions = []
    for i in range(18):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.065 if i % 3 else 0.082, location=(0, 0, 1.5))
        ob = smooth_obj(bpy.context.object)
        ob.data.materials.append(mat_ca if i % 4 == 0 else mat_na)
        ions.append((ob, i / 18.0, random.uniform(-0.14, 0.14), random.uniform(-0.12, 0.12)))

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        open_fac = 0.5 - 0.5 * math.cos(min(1.0, max(0.0, (u - 0.08) / 0.45)) * math.pi)
        pulse = 0.75 + 0.25 * math.sin(u * math.pi * 4)
        bsdf_cone.inputs['Emission Strength'].default_value = (0.25 + 0.85 * open_fac) * pulse
        bsdf_tm.inputs['Emission Strength'].default_value = 0.20 + 0.55 * open_fac
        bsdf_ret.inputs['Emission Strength'].default_value = 2.5 + 3.5 * open_fac

        ret_pivot.rotation_euler = (0.0, 0.48 * open_fac, 0.58 * open_fac)
        for h, ang, hx, hy in helices:
            rad_expand = 1.0 + 0.28 * open_fac
            h.location = (hx * rad_expand, hy * rad_expand, 0.04 * math.sin(u * math.pi * 2 + ang))
            h.rotation_euler = (0.12 * math.sin(ang) + 0.14 * open_fac * math.cos(ang),
                                -0.12 * math.cos(ang) + 0.14 * open_fac * math.sin(ang), ang)

        for h_ob, x, y, z0, sign in heads:
            h_ob.location.z = z0 + 0.035 * math.sin(u * math.pi * 2 + x * 1.5 + y)

        for ob, phase0, ox, oy in ions:
            prog = (phase0 + u * (0.45 + 1.25 * open_fac)) % 1.0
            z_ion = 1.85 - prog * 3.70
            spread = 1.0 + 1.8 * max(0.0, abs(z_ion) - 0.55)
            ob.location = (ox * spread + 0.04 * math.sin(prog * 12), oy * spread, z_ion)

        co.location = Vector((-0.55 + 1.10 * u, -4.35 + 0.45 * u, 1.15 - 0.28 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'chr2_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[chr2_3d] {f}/{n_frames}', flush=True)

# ==============================================================================
# SEQ 2: br_pump_3d (16 frames) — Left: BR Proton Pump (1 H+ uphill) vs Right: ChR2 Channel (High flux downhill)
# ==============================================================================
def render_br_pump_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.0, -5.0, 1.25)), Vector((0.0, 0.0, 0.0)), lens=48, fstop=4.0)

    mat_head, _ = make_mat('lipid_head', (0.88, 0.65, 0.24), rough=0.26, sss=0.30)
    mat_tail, _ = make_mat('lipid_tail', (0.35, 0.28, 0.16), rough=0.50)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10, radius=0.135, location=(0, 0, -100))
    proto_head = smooth_obj(bpy.context.object); proto_head.data.materials.append(mat_head)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.035, depth=0.58, location=(0, 0, -100))
    proto_tail = smooth_obj(bpy.context.object); proto_tail.data.materials.append(mat_tail)

    for ix in range(-15, 16):
        for iy in range(-5, 6):
            x, y = ix * 0.36, iy * 0.36
            if math.hypot(x + 1.35, y) < 0.78 or math.hypot(x - 1.35, y) < 0.78 or (y < -0.05 and (abs(x + 1.35) < 0.95 or abs(x - 1.35) < 0.95)):
                continue
            for sign in (-1, 1):
                z0 = sign * 0.68 + 0.04 * math.sin(x + y)
                h_ob = bpy.data.objects.new(f'bh_{ix}_{iy}_{sign}', proto_head.data)
                sc.collection.objects.link(h_ob); h_ob.location = (x, y, z0)
                t_ob = bpy.data.objects.new(f'bt_{ix}_{iy}_{sign}', proto_tail.data)
                sc.collection.objects.link(t_ob); t_ob.location = (x, y, z0 - sign * 0.34)

    mat_br, _ = make_mat('br_purple', (0.68, 0.18, 0.78), rough=0.22, trans=0.25, sss=0.25, emit_col=(0.65, 0.15, 0.85), emit_str=0.40)
    br_helices = []
    for k in range(7):
        ang = k * (2 * math.pi / 7.0) + 0.3
        if math.sin(ang) < -0.6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.125, depth=1.62, location=(-1.35 + 0.36 * math.cos(ang), 0.34 * math.sin(ang), 0))
        h = smooth_obj(bpy.context.object); h.data.materials.append(mat_br); br_helices.append((h, ang))

    mat_hplus, _ = make_mat('h_plus', (1.0, 0.65, 0.15), rough=0.1, emit_col=(1.0, 0.60, 0.12), emit_str=6.5)
    protons = []
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.088, location=(-1.35, 0, 0))
        p = smooth_obj(bpy.context.object); p.data.materials.append(mat_hplus); protons.append((p, i / 3.0))

    mat_chr, _ = make_mat('chr_cyan', (0.08, 0.68, 0.88), rough=0.20, trans=0.35, sss=0.25, emit_col=(0.08, 0.55, 1.0), emit_str=0.50)
    for k in range(7):
        ang = k * (2 * math.pi / 7.0) + 0.3
        if math.sin(ang) < -0.6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.125, depth=1.62, location=(1.35 + 0.48 * math.cos(ang), 0.44 * math.sin(ang), 0))
        h = smooth_obj(bpy.context.object); h.rotation_euler = (0.15 * math.cos(ang), 0.15 * math.sin(ang), ang); h.data.materials.append(mat_chr)

    mat_na, _ = make_mat('na_ion', (0.20, 0.85, 1.0), rough=0.1, emit_col=(0.18, 0.80, 1.0), emit_str=6.0)
    chan_ions = []
    for i in range(16):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.068, location=(1.35, 0, 0))
        ob = smooth_obj(bpy.context.object); ob.data.materials.append(mat_na)
        chan_ions.append((ob, i / 16.0, random.uniform(-0.15, 0.15), random.uniform(-0.12, 0.12)))

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        rock = math.sin(u * math.pi * 4)
        for h, ang in br_helices:
            squeeze = 0.35 + 0.04 * math.sin(u * math.pi * 4 + ang)
            h.location.x = -1.35 + squeeze * math.cos(ang)
            h.location.z = 0.06 * rock
        for p, ph in protons:
            prog = (ph + u * 0.65) % 1.0
            p.location = (-1.35 + 0.04 * math.sin(prog * 6.28), 0.0, -1.55 + prog * 3.10)
        for ob, ph, ox, oy in chan_ions:
            prog = (ph + u * 1.65) % 1.0
            z_i = 1.75 - prog * 3.50
            sp_f = 1.0 + 1.5 * max(0.0, abs(z_i) - 0.5)
            ob.location = (1.35 + ox * sp_f, oy * sp_f, z_i)
        co.location = Vector((-0.55 + 1.10 * u, -4.95 + 0.35 * u, 1.25 - 0.25 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'br_pump_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[br_pump_3d] {f}/{n_frames}', flush=True)

# ==============================================================================
# SEQ 3: nphr_3d (16 frames) — Halorhodopsin (NpHR) 590nm Yellow Light Cl- Pump & Hyperpolarization
# ==============================================================================
def render_nphr_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.4, -4.4, 1.15)), Vector((0.0, 0.0, -0.05)), lens=52, fstop=4.0)
    rl.data.color = (1.0, 0.72, 0.22)
    heads = build_bilayer(sc, nx=13, ny=5, spacing=0.38, hole_radius=0.88)

    mat_nphr, bsdf_np = make_mat('nphr_tm', (0.95, 0.58, 0.12), rough=0.22, trans=0.30, sss=0.25, emit_col=(1.0, 0.62, 0.12), emit_str=0.45)
    helices = []
    for k in range(7):
        ang = k * (2 * math.pi / 7.0) + 0.35
        if math.sin(ang) < -0.6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.135, depth=1.68, location=(0.38 * math.cos(ang), 0.36 * math.sin(ang), 0))
        h = smooth_obj(bpy.context.object); h.data.materials.append(mat_nphr); helices.append((h, ang))

    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.15, radius2=0.18, depth=3.6, location=(0.0, 0.0, 1.65))
    cone = smooth_obj(bpy.context.object)
    mat_cone, bsdf_cone = make_mat('yellow_cone', (1.0, 0.68, 0.12), rough=0.1, trans=0.95, emit_col=(1.0, 0.68, 0.12), emit_str=0.85, alpha=0.15)
    cone.data.materials.append(mat_cone)

    mat_cl, _ = make_mat('cl_ion', (0.35, 1.0, 0.65), rough=0.1, emit_col=(0.25, 1.0, 0.58), emit_str=6.0)
    cl_ions = []
    for i in range(14):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.075, location=(0, 0, 0))
        ob = smooth_obj(bpy.context.object); ob.data.materials.append(mat_cl)
        cl_ions.append((ob, i / 14.0, random.uniform(-0.18, 0.18), random.uniform(-0.14, 0.14)))

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        pulse = 0.7 + 0.3 * math.sin(u * math.pi * 4)
        bsdf_cone.inputs['Emission Strength'].default_value = 0.85 * pulse
        bsdf_np.inputs['Emission Strength'].default_value = 0.45 * pulse
        for h, ang in helices:
            r_p = 0.38 + 0.04 * math.sin(u * math.pi * 4 - ang)
            h.location = (r_p * math.cos(ang), r_p * math.sin(ang), -0.05 * math.sin(u * math.pi * 4))
        for ob, ph, ox, oy in cl_ions:
            prog = (ph + u * 1.15) % 1.0
            z_i = 1.65 - prog * 3.30
            sp_f = 1.0 + 2.2 * max(0.0, -z_i - 0.35)
            ob.location = (ox * sp_f, oy * sp_f, z_i)
        co.location = Vector((0.55 - 1.10 * u, -4.35 + 0.40 * u, 1.15 - 0.25 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'nphr_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[nphr_3d] {f}/{n_frames}', flush=True)

# ==============================================================================
# SEQ 4: retina_3d (16 frames) — 3D Goggles 595nm Projector + Cutaway Eyeball + ChrimsonR RGC Array
# ==============================================================================
def render_retina_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.0, -4.9, 1.05)), Vector((0.15, 0.0, 0.0)), lens=50, fstop=4.0)

    mat_gog, _ = make_mat('goggles_body', (0.12, 0.15, 0.22), rough=0.25, metal=0.85)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.25, 0.0, 0.0))
    gbox = bpy.context.object; gbox.scale = (0.28, 1.15, 0.95); gbox.data.materials.append(mat_gog)

    mat_led, bsdf_led = make_mat('amber_led', (1.0, 0.62, 0.12), rough=0.1, emit_col=(1.0, 0.58, 0.10), emit_str=6.0)
    for iz in range(-2, 3):
        for iy in range(-2, 3):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.055, depth=0.08, location=(-1.95, iy * 0.22, iz * 0.18), rotation=(0, math.radians(90), 0))
            led = smooth_obj(bpy.context.object); led.data.materials.append(mat_led)

    mat_sclera, _ = make_mat('sclera', (0.75, 0.28, 0.25), rough=0.40, sss=0.45)
    mat_retina, _ = make_mat('retina_cup', (0.92, 0.42, 0.18), rough=0.35, sss=0.35, emit_col=(0.85, 0.32, 0.10), emit_str=0.18)
    mat_lens, _ = make_mat('eye_lens', (0.82, 0.92, 1.0), rough=0.05, trans=0.95, alpha=0.35)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.58, location=(-0.55, 0.0, 0.0))
    elens = smooth_obj(bpy.context.object); elens.scale = (0.42, 1.0, 0.95); elens.data.materials.append(mat_lens)

    rgc_nodes = []
    mat_rgc_off, _ = make_mat('rgc_base', (0.15, 0.55, 0.95), rough=0.2, emit_col=(0.12, 0.48, 0.95), emit_str=1.2)
    mat_rgc_on, bsdf_rgc_on = make_mat('rgc_active', (0.25, 0.88, 1.0), rough=0.1, emit_col=(0.22, 0.85, 1.0), emit_str=7.5)
    for ia in range(-7, 8):
        theta = ia * 0.16
        for ib in range(-3, 4):
            phi = ib * 0.18
            rx = 0.45 + 1.35 * math.cos(theta) * math.cos(phi)
            ry = 1.35 * math.sin(phi)
            rz = 1.35 * math.sin(theta) * math.cos(phi)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.075, location=(rx, ry, rz))
            rc = smooth_obj(bpy.context.object)
            is_central = (abs(ia) <= 4 and abs(ib) <= 2)
            rc.data.materials.append(mat_rgc_on if is_central else mat_rgc_off)
            rgc_nodes.append((rc, rx, ry, rz, is_central, abs(ia) + abs(ib)))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.14, location=(rx + 0.14 * math.cos(theta), ry, rz + 0.14 * math.sin(theta)))
            sc_ob = smooth_obj(bpy.context.object); sc_ob.data.materials.append(mat_sclera if abs(ia) > 5 else mat_retina)

    mat_beam, bsdf_beam = make_mat('amber_beam', (1.0, 0.65, 0.12), rough=0.1, trans=0.9, emit_col=(1.0, 0.62, 0.10), emit_str=2.2, alpha=0.25)
    photons = []
    for k in range(5):
        z_t = (k - 2) * 0.28
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.028, depth=3.65, location=(-0.10, 0.0, z_t * 0.5), rotation=(0, math.radians(90 - k * 2 + 4), 0))
        bm = smooth_obj(bpy.context.object); bm.data.materials.append(mat_beam)
        for p_i in range(4):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=0.052, location=(-1.9, 0, z_t))
            ph = smooth_obj(bpy.context.object); ph.data.materials.append(mat_led)
            photons.append((ph, k, p_i / 4.0, z_t))

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        pulse = 0.65 + 0.35 * math.sin(u * math.pi * 4)
        bsdf_led.inputs['Emission Strength'].default_value = 5.0 * pulse
        bsdf_beam.inputs['Emission Strength'].default_value = 1.8 * pulse
        bsdf_rgc_on.inputs['Emission Strength'].default_value = 4.0 + 5.5 * pulse

        for ph, k, p0, z_t in photons:
            prog = (p0 + u * 1.8) % 1.0
            px_pos = -1.90 + prog * 3.60
            pz_pos = z_t * (0.35 + 0.65 * prog)
            ph.location = (px_pos, 0.0, pz_pos)

        for rc, rx, ry, rz, is_c, dist_k in rgc_nodes:
            if is_c:
                s_p = 1.0 + 0.32 * max(0.0, math.sin(u * math.pi * 4 - dist_k * 0.45))
                rc.scale = (s_p, s_p, s_p)

        co.location = Vector((-0.45 + 0.90 * u, -4.85 + 0.40 * u, 1.05 - 0.25 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'retina_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[retina_3d] {f}/{n_frames}', flush=True)

# ==============================================================================
# SEQ 5: hippo_cone_3d (16 frames) — 3D In-Situ Brain Optical Fiber Cone + DG Engram / Orexin Spikes
# ==============================================================================
def render_hippo_cone_3d(n_frames=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    setup_cycles(sc)
    co, tgt, kl, rl = add_lights_and_cam(sc, Vector((0.0, -4.5, 1.15)), Vector((0.0, 0.0, -0.15)), lens=50, fstop=4.0)

    mat_fer, _ = make_mat('ferrule', (0.90, 0.88, 0.82), rough=0.28)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.18, depth=0.85, location=(0.0, 0.0, 1.55))
    fer = smooth_obj(bpy.context.object); fer.data.materials.append(mat_fer)

    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.35, radius2=0.14, depth=2.85, location=(0.0, 0.0, -0.05))
    cone = smooth_obj(bpy.context.object)
    mat_cone, bsdf_cone = make_mat('fiber_cone', (0.10, 0.55, 1.0), rough=0.1, trans=0.95, emit_col=(0.12, 0.58, 1.0), emit_str=0.95, alpha=0.15)
    cone.data.materials.append(mat_cone)

    mat_on, bsdf_on = make_mat('neuron_chr2', (0.15, 0.78, 1.0), rough=0.18, sss=0.25, emit_col=(0.15, 0.72, 1.0), emit_str=4.5)
    mat_off, _ = make_mat('neuron_untagged', (0.28, 0.22, 0.42), rough=0.45, sss=0.25)
    mat_spike, _ = make_mat('axon_spike', (1.0, 0.82, 0.25), rough=0.1, emit_col=(1.0, 0.78, 0.22), emit_str=7.0)

    random.seed(21)
    active_somas = []
    spikes = []
    for i in range(42):
        nx = random.uniform(-2.1, 2.1)
        ny = random.uniform(-1.1, 1.1)
        nz = random.uniform(-1.35, 0.85)
        in_cone = (math.hypot(nx, ny) < (0.25 + 0.42 * (1.15 - nz))) and (abs(nx) < 1.05)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.13 if in_cone else 0.11, location=(nx, ny, nz))
        soma = smooth_obj(bpy.context.object)
        soma.data.materials.append(mat_on if in_cone else mat_off)
        for b_k in range(3):
            ang = random.uniform(0, 6.28)
            dx, dy, dz = 0.55 * math.cos(ang), 0.55 * math.sin(ang), random.uniform(-0.45, 0.45)
            cu = bpy.data.curves.new(f'ax_{i}_{b_k}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.018
            sp = cu.splines.new('POLY'); sp.points.add(2)
            sp.points[0].co = (nx, ny, nz, 1); sp.points[0].radius = 1.0
            sp.points[1].co = (nx + dx * 0.5, ny + dy * 0.5, nz + dz * 0.5, 1); sp.points[1].radius = 0.6
            sp.points[2].co = (nx + dx, ny + dy, nz + dz, 1); sp.points[2].radius = 0.25
            ax_ob = bpy.data.objects.new(f'ax_{i}_{b_k}', cu); sc.collection.objects.link(ax_ob)
            ax_ob.data.materials.append(mat_on if in_cone else mat_off)
            if in_cone and b_k == 0:
                bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=0.048, location=(nx, ny, nz))
                spk = smooth_obj(bpy.context.object); spk.data.materials.append(mat_spike)
                spikes.append((spk, Vector((nx, ny, nz)), Vector((dx, dy, dz)), random.random()))
        if in_cone:
            active_somas.append((soma, random.random()))

    for f in range(1, n_frames + 1):
        u = (f - 1) / max(n_frames - 1, 1)
        pulse = 0.55 + 0.45 * math.sin(u * math.pi * 4)
        bsdf_cone.inputs['Emission Strength'].default_value = 0.45 + 0.65 * pulse
        bsdf_on.inputs['Emission Strength'].default_value = 2.0 + 4.5 * pulse
        for soma, ph in active_somas:
            sc_v = 1.0 + 0.14 * math.sin(u * math.pi * 4 + ph * 6.28)
            soma.scale = (sc_v, sc_v, sc_v)
        for spk, p0, dvec, ph in spikes:
            prog = (ph + u * 2.0) % 1.0
            spk.location = p0 + dvec * prog
        co.location = Vector((-0.55 + 1.10 * u, -4.40 + 0.40 * u, 1.15 - 0.25 * u))
        sc.render.filepath = os.path.join(OUT_DIR, f'hippo_cone_3d_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[hippo_cone_3d] {f}/{n_frames}', flush=True)

if __name__ == '__main__':
    for name, fn in [
        ('microbe_3d', render_microbe_3d),
        ('chr2_3d', render_chr2_3d),
        ('br_pump_3d', render_br_pump_3d),
        ('nphr_3d', render_nphr_3d),
        ('retina_3d', render_retina_3d),
        ('hippo_cone_3d', render_hippo_cone_3d),
    ]:
        if ONLY_SEQ in ('all', name):
            fn(10)
    print('ALL_6_MOL_RETINA_3D_DONE', flush=True)
