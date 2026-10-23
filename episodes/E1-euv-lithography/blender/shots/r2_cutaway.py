"""P1 round 2 cutaway shots built on build_cutaway_r2.machine (2B + 4A + 2A studio light).

variants (registry args: {variant: ..., shot: ...}):
  title   A0_10  1C: white-studio panorama of the de-cased machine, two clean-room silhouettes for scale
  illum   B5_01  illuminator in context: facet mirrors, violet beam bouncing to the mask
  tour    C_03   long take: collector -> intermediate focus -> illuminator -> mask
  collect B3_02  3/4 reveal of the ellipsoidal collector with central hole inside the cut-open vessel
  scan    B8_03  reflective mask on the reticle stage, PO, wafer stage; stages move opposite at 8:1
Every variant puts its camera in "CamR2".
"""
import math

import bpy
from mathutils import Vector

import build_cutaway_r2 as B
import common as C
import kit_r2 as K


# R5: one descending zig-zag through the PO housing that never crosses itself (B7_06, A0_10)
PO_ZIGZAG = ((2.55, 0.15, 3.72), (1.05, 0.2, 3.28), (2.6, 0.1, 2.62), (1.0, 0.15, 2.1), (2.45, 0.05, 1.6),
             (1.35, 0.0, 1.28))


def _lights_dark(scale=1.0):
    K.area("Key", (-6, -8, 8), (-2, 0, 2), 5, 2400 * scale, (0.95, 0.96, 1.0))
    K.area("Rim", (-3, 6, 7), (-3, 0, 2), 10, 1800 * scale, (0.7, 0.75, 1.0))
    K.area("FillL", (-12, -4, 3), (-6, 0, 2), 4, 500 * scale, (0.6, 0.7, 1.0))
    K.area("FillR", (7, -5, 3), (2, 0, 2), 4, 500 * scale, (0.6, 0.7, 1.0))
    K.area("Top", (-3, 0, 12), (-3, 0, 0), 14, 600 * scale, (0.9, 0.92, 1.0), size_y=4)
    K.area("Kick", (6, -3, 6), (-2, 0.5, 2.5), 3, 1600 * scale, (1.0, 0.95, 0.9))
    K.point("PlasmaGlow", B.PLASMA, 300 * scale, K.VIOLET, 0.08)
    K.point("IFGlow", B.IF, 30 * scale, K.VIOLET, 0.05)
    K.point("MaskGlow", B.MASK + Vector((0, -0.2, -0.3)), 40 * scale, K.VIOLET, 0.1)


def _lights_studio():
    K.area("Key", (-4, -14, 10), (-3, 0, 2), 12, 9000, (1.0, 0.98, 0.95))
    K.area("Fill", (8, -10, 4), (-2, 0, 2), 10, 3500, (0.9, 0.95, 1.0))
    K.area("Rim", (-3, 10, 8), (-3, 0, 2.5), 14, 6000, (0.9, 0.93, 1.0))
    K.area("Top", (-3, 0, 14), (-3, 0, 0), 20, 5000, (1, 1, 1), size_y=8)


def build(variant="illum", shot=None):
    n = K.nframes(shot) if shot else 120
    sc = C.reset_scene(n)
    studio = variant in ("title", "po")
    M = K.palette(studio=studio)
    M["wafer"] = K.mat("WaferSi", (0.32, 0.33, 0.42), metal=1.0, rough=0.08)
    if variant == "title":                   # k1C: near-black backdrop, product-lit machine, white serif title above
        C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.03, 0.033, 0.04), bottom=(0.05, 0.05, 0.055), strength=1.0)
        flo = K.mat("StudioFloor", (0.3, 0.31, 0.33), rough=0.15, coat=0.6)
        K.floor("Floor", flo, z=0.0)
        _lights_studio()
    elif studio:
        K.world_studio(0.9)
        flo = K.mat("StudioFloor", (0.55, 0.56, 0.58), rough=0.18, coat=0.5)
        K.floor("Floor", flo, z=0.0)
        _lights_studio()
    else:
        K.world_dark(0.55)
        K.floor("Floor", K.mat("FloorDark", (0.05, 0.055, 0.065), rough=0.3, coat=0.3), z=0.0)
        _lights_dark()
    if variant == "collect":                 # R8: solid, dark polished multilayer dish (R7: read as a glass dome)
        M["coating"] = K.mat("CollectorSolidR8", (0.3, 0.29, 0.36), metal=1.0, rough=0.035, coat=1.0)
        M["substrate"] = K.mat("CollectorBodyR8", (0.2, 0.2, 0.23), metal=1.0, rough=0.3, speck=0.2)
    M["cone"] = (K.beam_column_mat("EUVCone", K.VIOLET, strength=0.6, edge=0.8, core=0.0, vol=0.02)   # R11: see-through
                 if variant == "collect" else K.beam_column_mat("EUVCone", K.VIOLET, strength=1.4, edge=0.4, core=0.06, vol=0.15))
    K.clean_cycles(sc)
    if variant == "po":
        return _po_turntable(sc, M, n)
    # R3: the title lights the path up module by module; the scan shot draws its own narrow band
    if variant == "scan":                    # R5: rebuilt (short illumination leg under the mask, 8:1 rulers)
        return _scan_r5(sc, M, n, shot)
    if variant == "title":                   # R5 (H13): the title's PO bay uses the non-crossing M1..M6 zig-zag
        B.PO = [Vector(v) for v in PO_ZIGZAG]
        B.PO_R = [0.24, 0.22, 0.26, 0.22, 0.24, 0.2]
    B.FRONT_POSTS_SKIP = (-4.0, -0.9) if variant == "tour" else ()
    B.LIP_SKIP_X = (0.6,) if variant == "tour" else ()
    B.machine(M, studio=studio, cut=True, beam=variant not in ("title", "tour"), bounce=8.0 if studio else 20.0)
    if variant == "title":
        _sequential_beam(M, n)
    if variant == "tour":                    # R4: one segment at a time; the PO path after the mask stays dim
        mi = 6                               # MASK is index 5; keep its reflected leg to PO1 bright (the V)
        pts, rad = B.beam_path(0, mi + 1)
        mb = K.MB()
        K.beam_columns(mb, pts, rad)
        K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
        mb.obj("TourBeam", M["beam_wide"])
        pts, rad = B.beam_path(mi)
        mb = K.MB()
        K.beam_columns(mb, pts, rad)
        mb.obj("TourBeamPO", K.beam_column_mat("EUVColumnDim", K.VIOLET, strength=0.35, edge=0.15, core=0.02, vol=0.03))
        K.bounce_lights([B.FFM, B.PFM, B.G1, B.G2, B.MASK + Vector((0, -0.1, -0.15))], energy=20.0)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.25 if not studio else 0.5
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.12
    cam, tgt = K.camera("CamR2", lens=35, fstop=None)
    f1 = n
    if variant == "title":
        cam.data.lens = 32
        K.suit_person("Eng1", (-3.0, -2.3, 0), 1.78, "stand", facing=10)
        K.suit_person("Eng2", (-2.35, -2.5, 0), 1.7, "work", facing=-20)
        _studio_skins(M)
        K.key_path(cam, tgt, [(1, (-5.2, -15.6, 2.2), (-3.6, 0, 3.3)), (f1, (-0.9, -14.0, 2.5), (-2.3, 0, 3.4))],
                   interp="LINEAR")
    elif variant == "illum":
        cam.data.lens = 28
        cam.data.lens = 24
        # R10: open wide on the whole illuminator (IF in, mask out), then push in on the field facet mirror
        K.key_path(cam, tgt, [(1, (-2.2, -7.4, 3.1), (-1.9, 0.3, 3.1)),
                              (round(f1 * 0.5), (-2.9, -5.0, 3.0), (-2.2, 0.3, 3.3)),
                              (f1, (-2.75, -2.0, 3.3), (-2.15, 0.15, 3.8))])
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 5.6
        cam.data.dof.focus_object = tgt
    elif variant == "tour":
        cam.data.lens = 30
        K.key_path(cam, tgt, [(1, (-8.4, -4.4, 3.3), (-7.4, 0.0, 2.3)),
                              (round(f1 * 0.25), (-6.6, -4.2, 3.0), (-5.6, 0.1, 2.5)),
                              (round(f1 * 0.55), (-3.4, -4.6, 3.3), (-2.5, 0.2, 3.0)),
                              (round(f1 * 0.85), (-0.05, -2.0, 3.3), (0.5, 0.3, 4.02)),     # R11: mask >= 1/4 frame
                              (f1, (0.0, -1.95, 3.32), (0.51, 0.3, 4.03))])
    elif variant == "collect":
        cam.data.lens = 30
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 4
        cam.data.dof.focus_object = tgt
        cam.data.lens = 24
        cam.data.dof.aperture_fstop = 8
        # R8 (F): keep collector AND intermediate focus in frame the whole shot so the cone visibly converges on IF
        # R11 (R10: "the cone hides the mirror, which doesn't look huge"): camera swings onto the dish axis side so
        # the collector face (>= 1/4 frame) looks at the lens, IF stays at the right edge; thinner cone; glint card
        cam.data.lens = 26
        K.key_path(cam, tgt, [(1, (-5.6, -4.7, 3.2), (-7.0, 0.0, 2.35)), (f1, (-5.9, -4.1, 2.95), (-7.15, 0.0, 2.33))])
        K.area("DishGlint", (-5.6, 2.9, 3.9), B.COLL, 2.2, 520, (0.95, 0.96, 1.0))
        K.area("DishKey", (-5.0, -2.2, 3.6), B.COLL, 1.6, 260, (1.0, 0.98, 0.95))
        pl = K.MB()                                     # plasma at the first focus (small violet-white glow)
        pl.sphere(B.PLASMA, 0.035, 20)
        pl.obj("PlasmaCore", K.emit_mat("PlasmaCoreR8", (0.92, 0.88, 1.0), 40.0))
        ph = K.MB()
        ph.sphere(B.PLASMA, 0.12, 24)
        ph.obj("PlasmaHalo", K.emit_mat("PlasmaHaloR8", K.VIOLET, 4.0, halo=0.8))
        ifm = K.MB()                                    # the cone's apex: a bright pinch point at IF
        ifm.sphere(B.IF, 0.03, 16)
        ifm.obj("IFPinch", K.emit_mat("IFPinchR8", (0.85, 0.8, 1.0), 25.0))
        # tin droplet stream through the plasma point
        dm = K.MB()
        for k in range(14):
            dm.sphere((-7.35, 0, 3.6 - k * 0.09), 0.012, 10)
        dm.obj("Droplets", K.mat("Tin", (0.8, 0.8, 0.82), metal=1.0, rough=0.12))
        lz = K.MB()                                     # CO2 laser enters through the collector's central hole
        lh = K.MB()
        K.beam(lz, lh, [Vector((-8.6, 0, 2.3)), B.PLASMA], r=0.005, halo=2.4)
        lz.obj("LaserCore", M["laser"])
        for o in bpy.data.objects:                       # no plasma yet in this shot: drop the point lights that
            if o.name in ("PlasmaGlow", "IFGlow"):       # made glossy fireflies around the focus
                o.data.energy *= 0.35
        lh.obj("LaserHalo", M["laser_halo"])
    sc.camera = cam
    K.anchors(shot, {"plasma": B.PLASMA, "coll": B.COLL + Vector((0.12, 0, 0.35)), "hole": B.COLL + Vector((0.02, 0, 0)),
                     "if": B.IF, "ffm": B.FFM, "pfm": B.PFM, "g1": B.G1, "mask": B.MASK, "rstage": B.MASK + Vector((0, -0.9, 0.35)),
                     "po": B.PO[2], "wafer": B.WAFER, "wstage": B.WAFER + Vector((-0.5, -0.6, -0.05)),
                     "eng": Vector((-3.0, -2.3, 1.84)), "eng_ft": Vector((-3.0, -2.3, 0.0)),
                     "eng_dim": Vector((-3.32, -2.3, 1.78)), "eng_dim0": Vector((-3.32, -2.3, 0.0))})
    return sc


def _scan_closeup(sc, M, n, shot):
    """B8_03 (R3): the two stages as the subject. The reticle stage and the wafer stage from the machine kit are
    re-stacked 2.1 m apart around a closed projection-optics housing (schematic spacing), in front of a dense
    services wall. The beam comes off a fold mirror at ~6 deg onto the mask, enters the housing, and leaves its
    bottom as a narrow band onto the wafer slit. Reticle stage travels 8x the wafer stage, opposite directions,
    read off fixed rulers; camera trucks across for parallax."""
    MZ, WZ = 2.7, 0.62
    mask_c, waf_c = Vector((0, 0, MZ)), Vector((0, 0, WZ))

    def kit_part(fn, offset, keys, name):
        mbs = {k: K.MB() for k in keys}
        fn(M, mbs)
        piv = bpy.data.objects.new(name, None)
        sc.collection.objects.link(piv)
        mats = {"rstage": M["alu"], "flange_s": M["alu"], "bolt": M["steel"], "steel": M["steel"], "mask": M["coating"],
                "anod": M["anod"], "led": M["led_c"], "cable_b": M["cable_b"], "cable_g": M["cable_g"], "stage": M["paint"],
                "granite": M["granite"], "wafer": M["wafer"]}
        mats["stage"] = M["alu"]
        for k, mb in mbs.items():
            if len(mb.bm.verts):
                ob = mb.obj(f"{name}_{k}", mats[k], bevel={"rstage": 0.015, "stage": 0.015, "granite": 0.02}.get(k, 0.0))
                ob.location = offset
                ob.parent = piv
            else:
                mb.bm.free()
        return piv

    rpiv = kit_part(B._reticle_stage, mask_c - B.MASK, ("rstage", "flange_s", "bolt", "steel", "mask", "anod", "led", "cable_b"),
                    "RStage")
    # the granite block and both guides stay; only the stage + wafer move -> build them in two passes
    wpiv = kit_part(B._wafer_stage, waf_c - B.WAFER, ("stage", "granite", "steel", "wafer", "anod", "cable_g"), "WStage")
    for ob in list(wpiv.children):
        if ob.name.endswith(("_granite", "_anod", "_cable_g")):
            ob.parent = None
    for ob in list(rpiv.children):                    # R4: the loom ran off to the top-left corner of the frame
        if ob.name.endswith("_cable_b"):
            bpy.data.objects.remove(ob)
    # R4: open projection-optics cage (cut-away front, section faces) with 3 solid mirrors on hexapod mounts;
    # the path is the real topology: illumination in at ~6 deg onto the face-down mask -> reflected down at ~6 deg
    # -> PO mirrors fold it -> narrow band onto the wafer. Every bounce point lights its mount (violet points).
    th6 = math.radians(6.0)
    g2 = mask_c + Vector((-math.tan(th6) * 1.5, -0.0, -1.5))
    m1 = mask_c + Vector((math.tan(th6) * 0.85, 0.0, -0.85))
    m2 = Vector((1.05, 0.0, 1.35))
    m3 = Vector((0.42, 0.0, 0.98))
    src = Vector((-3.6, 0.0, 3.35))
    pts = [src, g2, mask_c, m1, m2, m3, waf_c + Vector((0, 0, 0.004))]
    mm = {k: K.MB() for k in ("mirror", "mount", "bolt", "substrate", "spot", "copper", "cable_o", "cable_b")}
    for i, (p_, r_) in enumerate(((g2, 0.14), (m1, 0.15), (m2, 0.27), (m3, 0.2))):
        j = pts.index(p_)
        K.mirror_with_mount(mm["mirror"], mm["mount"], mm["bolt"], p_, K.mirror_normal(pts[j - 1], p_, pts[j + 1]), r_,
                            seed=i, mbsub=mm["substrate"], mbspot=mm["spot"], spot=0.6, mbpipe=mm["copper"],
                            mbcable=mm["cable_b" if i % 2 else "cable_o"])
    for k, m_ in (("mirror", M["coating"]), ("mount", M["alu"]), ("bolt", M["steel"]), ("substrate", M["substrate"]),
                  ("spot", M["spot"]), ("copper", M["copper"]), ("cable_o", M["cable_o"]), ("cable_b", M["cable_b"])):
        if len(mm[k].bm.verts):
            mm[k].obj("POm_" + k, m_)
        else:
            mm[k].bm.free()
    cg, sec, fl = K.MB(), K.MB(), K.MB()
    cg.box((0.45, 0.62, 1.62), (2.3, 0.06, 1.5))                  # back plate of the PO cage
    for x in (-0.68, 1.58):                                       # cut side walls (shell thickness shows)
        cg.box((x, 0.2, 1.62), (0.06, 0.85, 1.5))
        sec.box((x, -0.23, 1.62), (0.065, 0.012, 1.5))
    for z in (0.86, 2.38):                                        # top / bottom flanges with beam ports
        cg.box((0.45, 0.2, z), (2.3, 0.85, 0.05))
        sec.box((0.45, -0.23, z), (2.3, 0.012, 0.055))
        for i in range(18):
            K.MB.cyl(fl, (-0.62 + i * 0.125, -0.19, z + 0.03), 0.011, 0.02, seg=6)
    for x, z in ((-0.4, 1.2), (1.3, 2.0), (1.3, 1.1), (-0.45, 2.1)):  # sensor / actuator boxes on the back plate
        cg.box((x, 0.5, z), (0.2, 0.18, 0.24))
        fl.box((x, 0.4, z + 0.08), (0.04, 0.01, 0.03))
    cg.obj("POCage", M["anod"], bevel=0.008)
    sec.obj("POCageSection", M["section"])
    fl.obj("POCageBolts", M["steel"])
    lm = K.MB()
    K.cable_run(lm, [(-0.6, 0.45, 2.3), (-0.62, 0.45, 1.5), (-0.6, 0.45, 0.9)], n=4, r=0.01, seed=5)
    K.cable_run(lm, [(1.5, 0.45, 2.3), (1.52, 0.45, 1.6), (1.5, 0.45, 0.9)], n=4, r=0.01, seed=6)
    lm.obj("POCageLoom", M["cable_g"])
    # back services wall: pushed back, darker, out of focus (linear-motor racks, guides, coolant)
    wall = {k: K.MB() for k in ("housing", "bolt", "flange_s", "greeble", "anod", "frame", "led", "pipe", "copper",
                                "steel", "alu", "gold", "cable_b", "cable_o", "cable_g")}
    wall["housing"].box((0, 2.3, 1.9), (8.0, 0.05, 3.8))
    B._interior_fill(wall, -4.0, 4.0, 0.1, 3.7, y_back=2.3, seed=31)
    dk = K.mat("WallDark", (0.07, 0.075, 0.085), metal=0.6, rough=0.45)
    wm = {"housing": dk, "bolt": M["alu_dark"], "flange_s": M["alu_dark"], "greeble": dk, "anod": M["anod"],
          "frame": dk, "led": M["led_c"], "pipe": M["alu_dark"], "copper": M["copper"], "steel": M["alu_dark"],
          "alu": dk, "gold": dk, "cable_b": M["cable_g"], "cable_o": M["cable_g"], "cable_g": M["cable_g"]}
    for k, mb in wall.items():
        if len(mb.bm.verts):
            mb.obj("Wall_" + k, wm[k])
        else:
            mb.bm.free()
    bm = K.MB()
    K.beam_columns(bm, pts, [0.05, 0.045, 0.035, 0.04, 0.06, 0.045, 0.012])
    bm.obj("ScanBand", M["beam_wide"])
    sl = K.MB()                                      # exposure slit footprints on mask and wafer (fixed)
    sl.box((0, 0, MZ - 0.004), (0.36, 0.05, 0.004))
    sl.box((0, 0, WZ + 0.003), (0.11, 0.014, 0.003))
    sl.obj("Slit", K.emit_mat("SlitGlow", K.VIOLET, 25.0))
    K.point("SlitLightM", mask_c + Vector((0, -0.3, -0.25)), 40, K.VIOLET, 0.1)
    K.point("SlitLightW", waf_c + Vector((0, -0.3, 0.2)), 20, K.VIOLET, 0.05)
    for i, p_ in enumerate((g2, m1, m2, m3)):
        K.point(f"POBounce{i}", p_ + Vector((0, -0.25, 0)), 12, K.VIOLET, 0.08)
    # rulers: 0.15 m ticks under the reticle stage, 1/8 of that beside the wafer (same 8 divisions, 8x shorter)
    tk = K.MB()
    for i in range(-10, 11):
        h = 0.1 if i % 4 == 0 else 0.05
        tk.box((i * 0.075, -1.2, MZ - 0.24 + h / 2), (0.008, 0.01, h))
    for i in range(-10, 11):
        h = 0.05 if i % 4 == 0 else 0.025
        tk.box((i * 0.075 / 8, -0.62, WZ + 0.08 + h / 2), (0.002, 0.006, h))
    tk.box((0, -1.2, MZ - 0.24), (1.52, 0.01, 0.006))
    tk.box((0, -0.62, WZ + 0.08), (0.19, 0.006, 0.003))
    tk.obj("Rulers", K.emit_mat("RulerInk", (0.85, 0.88, 0.95), 2.5))
    pm = K.emit_mat("PtrCyan", K.CYAN, 6.0)
    pr, pw = K.MB(), K.MB()
    pr.box((0, -1.21, MZ - 0.1), (0.03, 0.012, 0.07))
    pr.box((0, -1.16, MZ + 0.05), (0.02, 0.1, 0.3))                  # pointer arm hanging from the stage front
    pw.box((0, -0.625, WZ + 0.065), (0.006, 0.008, 0.02))
    po_, pwo = pr.obj("RulerPtr", pm), pw.obj("RulerPtrW", pm)
    po_.parent, pwo.parent = rpiv, wpiv
    d = 0.075
    for piv, a0, a1 in ((rpiv, -9 * d, 9 * d), (wpiv, 9 * d / 8, -9 * d / 8)):
        piv.location.x = a0
        piv.keyframe_insert("location", frame=1)
        piv.location.x = a1
        piv.keyframe_insert("location", frame=n)
        for fc in C.fcurves(piv.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    # lights: dark machine-interior look with product key + rims
    _lights_dark(0.5)
    for o in bpy.data.objects:
        if o.name in ("PlasmaGlow", "IFGlow", "MaskGlow"):
            bpy.data.objects.remove(o)
    K.area("StageKeyR", (-1.2, -3.2, 4.6), (0, 0, MZ + 0.3), 2.5, 260, (1.0, 0.98, 0.95))
    K.area("StageKeyW", (-1.2, -3.0, 2.0), (0, 0, WZ), 2.5, 200, (1.0, 0.98, 0.95))
    K.area("RimTop", (1.5, 1.0, 4.8), (0, 0, MZ), 2.0, 600, (0.8, 0.85, 1.0))
    K.area("POKey", (2.5, -3.0, 2.2), (0.45, 0.2, 1.6), 2.0, 380, (0.95, 0.97, 1.0))
    cam, tgt = K.camera("CamR2", lens=33)
    K.key_path(cam, tgt, [(1, (0.3, -7.1, 2.45), (0.3, 0.2, 2.06)), (n, (0.3, -6.5, 2.38), (0.3, 0.2, 2.03))],
               interp="LINEAR")
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 1.4
    cam.data.dof.focus_distance = 6.6
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.2
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    sc.camera = cam
    K.anchors(shot, {"rstage": Vector((0.6, -1.2, MZ - 0.24)), "mask": mask_c, "wafer": waf_c,
                     "wstage": Vector((0.08, -0.62, WZ + 0.1)), "fold": g2, "po": m2})
    return sc


def _sequential_beam(M, n):
    """A0_10: the violet path lights up module by module (source cone -> illuminator -> mask + PO -> wafer)."""
    segs = [(None, 1), ((0, 6), 0.3), ((5, None), 0.6)]
    for i, (rng, start) in enumerate(segs):
        mb = K.MB()
        if rng is None:
            K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
            mat = M["cone"]
        else:                                # R9: solid k4A shafts (mirror-sized) on the non-crossing path
            pts, rad = B.beam_path(*rng)
            K.beam_columns(mb, pts, rad)
            mat = K.beam_column_mat(f"EUVShaft{i}", K.VIOLET, strength=2.6, edge=0.85, core=0.2, vol=0.3)
        ob = mb.obj(f"BeamSeg{i}", mat)
        if start == 1:
            continue
        f0 = max(2, round(n * start))
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=f0 - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
        mr = next(nd for nd in mat.node_tree.nodes if nd.type == "MAP_RANGE" and nd.inputs["To Max"].default_value > 1.0)
        hi = (mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value)
        for f, k in ((f0, 0.15), (f0 + 10, 1.0)):
            mr.inputs["To Min"].default_value = hi[0] * k
            mr.inputs["To Max"].default_value = hi[1] * k
            mr.inputs["To Min"].keyframe_insert("default_value", frame=f)
            mr.inputs["To Max"].keyframe_insert("default_value", frame=f)


def _studio_skins(M):
    """2A: closed white product cabinets at both ends and a roof skin, so the open middle reads as a cutaway of a
    finished product (panel seams, vents, status strip). Generic shapes, no vendor styling or marks."""
    mb, seam, vent = K.MB(), K.MB(), K.MB()
    for x0, x1, h in ((-11.2, -9.5, 4.6), (3.5, 5.6, 4.2), (5.6, 6.9, 3.2)):
        cx = (x0 + x1) / 2
        mb.box((cx, 0, h / 2 + 0.05), (x1 - x0, 2.9, h))
        for k in range(1, int((x1 - x0) / 0.42) + 1):                       # vertical panel seams
            seam.box((x0 + k * 0.42, -1.452, h / 2 + 0.05), (0.012, 0.01, h - 0.1))
        seam.box((cx, -1.452, 0.35), (x1 - x0 - 0.04, 0.01, 0.012))
        for k in range(8):                                                    # vent slots
            vent.box((cx, -1.455, 0.6 + k * 0.06), ((x1 - x0) * 0.5, 0.01, 0.02))
    mb.box((-3.0, 0.1, 5.05), (12.8, 2.7, 0.18))                              # roof skin
    mb.obj("SkinPanels", M["paint"], bevel=0.02)
    seam.obj("SkinSeams", K.mat("Seam", (0.25, 0.26, 0.28), rough=0.6))
    vent.obj("SkinVents", K.mat("Vent", (0.08, 0.08, 0.09), rough=0.5))
    led = K.MB()
    led.box((-10.35, -1.46, 3.9), (1.0, 0.01, 0.02))
    led.obj("SkinLED", K.emit_mat("SkinLEDc", K.CYAN, 4.0))


def _po_turntable(sc, M, n):
    """B7_06: the projection-optics module alone as a 2A studio product on a turntable, front cover removed
    (mirrors + violet path visible), a suited silhouette for scale."""
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    K.area("Key", (-5, -7, 7), (1.8, 0, 2.2), 6, 4200, (1.0, 0.98, 0.95))
    K.area("Fill", (7, -6, 3), (1.8, 0, 2), 6, 1200, (0.9, 0.95, 1.0))
    K.area("RimL", (-3, 5, 5), (1.8, 0, 2.5), 3, 6500, (0.9, 0.93, 1.0))
    K.area("RimR", (7, 5, 5), (1.8, 0, 2.5), 3, 6500, (0.9, 0.93, 1.0))
    K.area("Softbox", (1.8, 0, 9), (1.8, 0, 0), 6, 5000, (1, 1, 1), size_y=3)
    mbs = {k: K.MB() for k in ("frame", "bolt", "mirror", "gold", "copper", "mount", "housing", "greeble", "anod",
                                "steel", "led", "cable_b", "cable_o", "cable_g", "pipe", "flange_s", "beam", "halo",
                                "stage", "alu", "substrate", "spot", "vol", "skin", "section", "cast")}
    # R10 (R9 review: "M5/M6 centre holes missing; no entry / exit"): M1-M4 fold down the housing without crossing,
    # M4 sends the beam straight down through the hole of M6 onto M5 (faces up, centre hole), M5 throws it back up
    # onto M6 (faces down, centre hole), M6 focuses it down through the hole of M5 and out of the floor port.
    # Entry: a beam cone coming in through a roof port from the mask above.
    import hero_kit_r10 as HK
    AX = Vector((1.8, 0.0, 0))
    m1, m2, m3, m4 = (Vector(v) for v in ((2.55, 0.15, 3.65), (1.0, 0.18, 3.3), (2.6, 0.1, 2.95), (1.8, 0.0, 2.7)))
    z6, z5, zf = 2.05, 1.32, 0.96
    r6, h6, r5, h5 = 0.46, 0.1, 0.3, 0.12
    po_keep, por_keep, w_keep = B.PO, B.PO_R, B.WAFER
    B.PO = [m1, m2, m3, m4]
    B.PO_R = [0.22, 0.2, 0.22, 0.15]
    B.WAFER = Vector((AX.x, 0.0, z6))                     # M4's normal points straight down the axis
    # R11: the back-wall blocks stay clear of the M6 -> M5 column and its mounts
    B.EXTRA_KEEP[:] = [(Vector((AX.x, 0, z6)), 0.62), (Vector((AX.x, 0, z5)), 0.5), (Vector((AX.x, 0, 1.7)), 0.45),
                       (Vector((AX.x, 0, zf)), 0.3)]
    B.WALL_TONE[0] = "dark"
    B._projection(M, mbs)
    B.WALL_TONE[0] = "mixed"
    B.EXTRA_KEEP[:] = []
    B.PO, B.PO_R, B.WAFER = po_keep, por_keep, w_keep
    HP = B._hk()
    HK.annular_mirror(HP, Vector((AX.x, 0, z6)), (0, 0, -1), r6, h6, spot_mb=mbs["spot"], spot=(0.5, 0.86))   # M6
    HK.annular_mirror(HP, Vector((AX.x, 0, z5)), (0, 0, 1), r5, h5, spot_mb=mbs["spot"], spot=(0.55, 0.9))    # M5
    for z in (z6, z5):                                    # mirror cells tied to the housing back wall
        mbs["mount"].tube(Vector((AX.x, 0.35, z)), Vector((AX.x, 1.08, z)), 0.04)
        mbs["anod"].box(Vector((AX.x, 1.0, z)), (0.26, 0.12, 0.22))
    # R11 (H13, R10 review: "a few disc mirrors and sparse supports in a flat aluminium box"): dense, nameable
    # interior - hexapods carry M5 (from below) and M6 (from above) with their legs outside the beam, coolant
    # hose bundles with P-clamps up both side walls, CF viewports + a turbo pump on the side walls, a metrology
    # ring frame with sensor heads, a valve island + harness on the floor; brushed, chamfered housing plates
    import hero_kit_r11 as H11
    HK.materials(M)
    HK.hexapod(HP, Vector((AX.x, 0, 1.03)), Vector((AX.x, 0, z5 - h5 * 0.5 - 0.035)), 0.36, 0.3)          # M5 hexapod
    HK.hexapod(HP, Vector((AX.x, 0, 2.62)), Vector((AX.x, 0, z6 + h6 * 0.5 + 0.045)), 0.42, 0.44)          # M6 hexapod
    for z in (1.18, 2.38):                                                                                  # metrology rings
        HK._ring(HP["anod"], Vector((AX.x, 0.05, z)), (0, 0, 1), 0.98, 0.9, 0.05, seg=72)
        for a in (30, 150, 270):
            d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            p_ = Vector((AX.x, 0.05, z)) + d * 0.88
            HP["brushed"].box(p_ + Vector((0, 0, 0.06)), (0.09, 0.09, 0.07))                           # sensor head
            HK._cyl(HP["glass"], p_ - d * 0.05 + Vector((0, 0, 0.06)), -d, 0.022, 0.008, seg=16)
    for x, sg in ((0.68, 1), (2.92, -1)):                                                                   # side walls
        HK.cooling_bundle(HP, [Vector((x, 0.75, 1.1)), Vector((x, 0.75, 3.85)), Vector((x + sg * 0.25, 0.85, 4.0))],
                          k=4, r=0.014, clamp_every=0.3, up=(1, 0, 0))
        HK.flange_viewport(HP, Vector((x - sg * 0.05, 0.55, 3.1 if sg > 0 else 1.75)), (sg, 0, 0), 0.08, nipple=0.1)
        HK.flange_viewport(HP, Vector((x - sg * 0.05, 0.45, 1.55 if sg > 0 else 3.35)), (sg, 0, 0), 0.055, nipple=0.08,
                           side_port=False)
        HK.cable_harness(HP, [Vector((x + sg * 0.06, 0.95, 1.05)), Vector((x + sg * 0.08, 0.6, 2.3)),
                              Vector((x + sg * 0.06, 0.95, 3.9))], n=6, r=0.008)
    HK._turbo(HP, Vector((2.62, 0.7, 2.75)), (-1, 0, 0), 0.1)
    HP["steel"].tube(Vector((2.95, 0.7, 2.75)), Vector((2.75, 0.7, 2.75)), 0.08, seg=24)
    H11.valve_island(HP, 1.0, 1.25, 0.5, 0.3, 0.95, 0.8, None)
    H11.card_cage(HP, 2.55, 1.32, 0.5, 0.42, 1.0, 0.8, __import__("random").Random(4), 0.8)
    entry = Vector((0.75, 0.3, 4.75))
    pts = [entry, m1, m2, m3, m4]
    K.beam_columns(mbs["vol"], pts, [0.07, 0.13, 0.12, 0.13, 0.08])
    col = mbs["vol"]
    K.beam_columns(col, [Vector((AX.x, 0, m4.z)), Vector((AX.x, 0, z6))], [0.075, 0.045], seg=40)          # M4 -> M6 hole
    K.beam_columns(col, [Vector((AX.x, 0, z6)), Vector((AX.x, 0, z5 + 0.01))], [0.045, r5 * 0.88], seg=48)    # -> M5 ring
    K.beam_columns(col, [Vector((AX.x, 0, z5 + 0.01)), Vector((AX.x, 0, z6 - 0.01))], [r5 * 0.9, r6 * 0.84], seg=64)  # M5 -> M6
    K.beam_columns(col, [Vector((AX.x, 0, z6 - 0.01)), Vector((AX.x, 0, zf))], [r6 * 0.8, 0.008], seg=64)    # M6 -> through M5 hole
    K.bounce_lights([m1, m2, m3, m4, Vector((AX.x, -0.2, z5 + 0.1)), Vector((AX.x, -0.2, z6 - 0.1))], energy=6.0)
    # roof entry port + floor exit port
    for z in (4.07, 1.0):
        c_ = entry.lerp(m1, 0.06) if z > 2 else Vector((AX.x, 0, z))
        mbs["flange_s"].ring((c_.x, c_.y, z), 0.17, 0.1, 0.05, seg=40)
        mbs["bolt"].bolts((c_.x, c_.y, z + 0.03), 0.14, 10, 0.01, 0.02)
    pts = [entry, m1, m2, m3, m4]
    # R4 2A: front cover kept only on the left third, cast ribs, flanges, ports and cables
    # R11: the remaining front cover hid a third of the interior -> only a sawn-off lip with its cut face
    cast = mbs["cast"]
    cast.box((0.68, -1.05, 2.52), (0.16, 0.06, 3.1))
    mbs["section"].box((0.765, -1.05, 2.52), (0.012, 0.07, 3.1))
    for x in (0.75, 2.85):                                                   # isolation feet on the turntable
        for y in (-0.8, 0.9):
            mbs["anod"].cyl((x, y, 0.98), 0.09, 0.12, seg=24)
            mbs["steel"].cyl((x, y, 1.06), 0.06, 0.05, seg=24)
    for z in (1.6, 2.8):
        mbs["flange_s"].ring((0.6, 0.0, z), 0.16, 0.07, 0.05, rot=(0, math.radians(90), 0))
        mbs["bolt"].bolts((0.57, 0.0, z), 0.13, 8, 0.01, 0.02, rot=(0, math.radians(90), 0))
        mbs["steel"].tube((0.58, 0, z), (0.25, 0, z), 0.07, seg=20)
    for k, col in enumerate(("cable_b", "cable_o", "cable_g")):
        K.cable_run(mbs[col], [(0.62, -0.4 + k * 0.1, 3.9), (0.3, -0.5 + k * 0.1, 3.0), (0.25, -0.6 + k * 0.1, 0.95)],
                    n=4, r=0.012, seed=k)
    for x in (0.75, 2.85):
        for z in (1.15, 3.9):
            mbs["anod"].box((x, -1.0, z), (0.18, 0.12, 0.14))
    # pedestal + turntable + lifting lugs, outer cover strips with seams
    mbs["stage"].cyl((1.8, 0.05, 0.45), 1.75, 0.9, seg=96)
    mbs["steel"].ring((1.8, 0.05, 0.92), 1.78, 1.6, 0.04, seg=96)
    for x in (0.65, 2.95):
        mbs["housing"].box((x, 0.05, 2.5), (0.1, 2.2, 3.1))
        for z in (1.4, 2.5, 3.6):
            mbs["steel"].cyl((x, -1.0, z), 0.06, 0.12, rot=(math.radians(90), 0, 0), seg=6)
    for x in (1.0, 2.6):
        mbs["steel"].ring((x, 0.05, 4.2), 0.16, 0.09, 0.05, rot=(math.radians(90), 0, 0))
    for x, sg in ((0.565, -1), (3.035, 1)):                  # R11: outer side walls = thick brushed chamfered plates
        for (yc, zc, w_, h_) in ((0.75, 1.55, 0.7, 1.0), (0.75, 2.75, 0.7, 1.3), (0.75, 3.75, 0.7, 0.62),
                                 (0.12, 2.2, 0.46, 2.3), (0.12, 3.75, 0.46, 0.62)):
            H11.housing_plate(HP, Vector((x, yc, zc)), (w_ - 0.03, 0.035, h_ - 0.03), (sg, 0, 0), key="brushed")
    mats = {"frame": M["alu"], "bolt": M["steel"], "mirror": M["mirror"], "gold": M["gold"], "copper": M["copper"],
            "mount": M["alu"], "housing": M["paint"], "greeble": M["alu"], "anod": M["anod"], "steel": M["steel"],
            "led": M["led_c"], "cable_b": M["cable_b"], "cable_o": M["cable_o"], "cable_g": M["cable_g"],
            "pipe": M["steel"], "flange_s": M["alu"], "beam": M["beam"], "halo": M["beam_halo"], "stage": M["paint_grey"],
            "alu": M["alu"], "substrate": M["substrate"], "spot": M["spot"], "vol": M["beam_wide"], "skin": M["paint"],
            "section": M["section"], "cast": M["alu"]}
    mats["mirror"] = M["coating"]
    mats["housing"] = M["brushed"]
    mats["cast"] = M["brushed"]
    piv = bpy.data.objects.new("Turntable", None)
    sc.collection.objects.link(piv)
    piv.location = (1.8, 0.05, 0)
    for k, mb in mbs.items():
        if len(mb.bm.verts):
            ob = mb.obj("PO_" + k, mats[k], bevel={"housing": 0.012, "stage": 0.02, "cast": 0.015}.get(k, 0.0))
            ob.parent = piv
            ob.location -= piv.location
        else:
            mb.bm.free()
    for ob in B.flush_kits(M, tag="POKit"):          # R8: parts kit inside the PO cage turns with it
        ob.parent = piv
        ob.location -= piv.location
    piv.rotation_euler = (0, 0, math.radians(-42))           # R11: 42 -> 76 deg swing so the path visibly turns
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(34))
    piv.keyframe_insert("rotation_euler", frame=n)
    K.suit_person("Eng1", (4.05, -1.7, 0), 1.78, "stand", facing=-30)   # R5: clean-room suit (k9B), not a grey dummy
    # R11: product key into the open housing so the back-wall assemblies and hexapods read (R10: dark interior)
    K.area("InnerKey", (1.2, -3.2, 3.6), (1.8, 0.8, 2.4), 1.6, 900, (1.0, 0.98, 0.95))
    K.area("InnerFill", (3.2, -2.6, 1.6), (1.8, 0.8, 1.6), 1.2, 300, (0.9, 0.94, 1.0))
    cam, tgt = K.camera("CamR2", lens=35)
    K.key_path(cam, tgt, [(1, (1.3, -8.0, 3.3), (2.15, 0, 2.5)), (n, (1.75, -7.3, 2.8), (2.2, 0, 2.5))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.5
    sc["vignette"] = 0.3
    sc.camera = cam
    K.anchors("B7_06", {"po": Vector((1.8, 0.05, 2.5)), "eng": Vector((4.05, -1.7, 1.8)), "top": Vector((1.8, 0.05, 4.1)),
                        "m6": Vector((2.25, -0.1, 2.05)), "m5": Vector((2.1, -0.1, 1.32)), "entry": Vector((0.75, 0.3, 4.3))})
    return sc


def _txt(name, s, loc, size, mat, align="CENTER"):
    """Flat text facing the camera (-Y), for ruler digits."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(mat)
    return ob


def _keys_linear(ob, prop, frames_vals, index=-1):
    for f, v in frames_vals:
        if index >= 0:
            getattr(ob, prop)[index] = v
        else:
            setattr(ob, prop, v)
        ob.keyframe_insert(prop, frame=f, index=index)
    for fc in C.fcurves(ob.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


def _bay_fill(M, x0, x1, z0, z1, yb, seed=0, tag="B"):
    """R6 (H13, B8_03): dense, nameable machine parts on a bay's back plate (front face at y = yb), all behind the
    beam plane (y = 0): a metrology frame of bolted bars, a cable tray with looms, a coolant manifold with
    branch lines and valves, CF flanges with sensor heads, finned drive amplifiers and terminal-block rows."""
    import random as _r
    rnd = _r.Random(seed)
    P = {k: K.MB() for k in ("frame", "bolt", "tray", "loom", "cu", "valve", "flange", "sensor", "lens", "drive",
                             "fin", "term", "wire_o", "wire_b", "led")}
    y = yb - 0.012
    w, h = x1 - x0, z1 - z0
    # metrology frame: two horizontals + verticals every ~0.4 m, bolted at the joints
    for z in (z0 + 0.06, z1 - 0.06):
        P["frame"].box(((x0 + x1) / 2, y - 0.02, z), (w, 0.04, 0.035))
    nx = max(2, int(w / 0.4))
    for i in range(nx + 1):
        x = x0 + 0.03 + (w - 0.06) * i / nx
        P["frame"].box((x, y - 0.02, (z0 + z1) / 2), (0.035, 0.04, h - 0.04))
        for z in (z0 + 0.06, z1 - 0.06):
            P["bolt"].cyl((x, y - 0.045, z), 0.009, 0.012, rot=(math.radians(90), 0, 0), seg=8)
    # cable tray (open channel) along the top with a loom inside, drops to each drive
    zt = z1 - 0.13
    P["tray"].box(((x0 + x1) / 2, y - 0.05, zt - 0.03), (w - 0.1, 0.07, 0.008))
    P["tray"].box(((x0 + x1) / 2, y - 0.085, zt), (w - 0.1, 0.006, 0.06))
    K.cable_run(P["loom"], [(x0 + 0.06, y - 0.05, zt - 0.01), (x1 - 0.06, y - 0.05, zt - 0.01)], n=6, r=0.007,
                spread=0.018, seed=seed)
    # coolant manifold: horizontal header low on the plate, branch lines up with valves
    zm = z0 + 0.16
    P["cu"].tube((x0 + 0.05, y - 0.06, zm), (x1 - 0.05, y - 0.06, zm), 0.016, seg=12)
    P["cu"].tube((x0 + 0.05, y - 0.1, zm + 0.05), (x1 - 0.05, y - 0.1, zm + 0.05), 0.012, seg=12)
    for i in range(int(w / 0.22)):
        x = x0 + 0.12 + i * 0.22
        P["cu"].path([(x, y - 0.06, zm), (x, y - 0.06, zm + 0.12), (x + 0.04, y - 0.09, zm + 0.2)], 0.007, seg=8)
        P["valve"].box((x, y - 0.075, zm + 0.08), (0.03, 0.03, 0.03))
        P["valve"].cyl((x, y - 0.1, zm + 0.08), 0.012, 0.02, rot=(math.radians(90), 0, 0), seg=10)
    # CF flanges with sensor heads / feedthroughs
    nfl = max(2, int(w / 0.5))
    for i in range(nfl):
        x = x0 + (i + 0.5) * w / nfl + rnd.uniform(-0.05, 0.05)
        z = z0 + h * rnd.uniform(0.45, 0.62)
        r = rnd.choice((0.045, 0.06, 0.075))
        rot = (math.radians(90), 0, 0)
        P["flange"].ring((x, y - 0.005, z), r * 1.6, r * 0.6, 0.02, rot=rot, seg=32)
        P["bolt"].bolts((x, y - 0.018, z), r * 1.3, 8, 0.006, 0.01, rot=rot)
        P["sensor"].cyl((x, y - 0.06, z), r * 0.55, 0.09, rot=rot, seg=20)
        P["lens"].cyl((x, y - 0.107, z), r * 0.35, 0.006, rot=rot, seg=20)
        P["led"].box((x + r * 0.7, y - 0.03, z + r * 0.9), (0.012, 0.004, 0.008))
    # drive amplifiers with cooling fins + terminal rows with wires
    nd = max(1, int(w / 0.6))
    for i in range(nd):
        x = x0 + (i + 0.5) * w / nd + 0.12
        z = z0 + h * 0.36
        P["drive"].box((x, y - 0.04, z), (0.16, 0.08, 0.12))
        for k in range(7):
            P["fin"].box((x - 0.06 + k * 0.02, y - 0.09, z), (0.006, 0.03, 0.11))
        P["led"].box((x + 0.06, y - 0.081, z + 0.045), (0.01, 0.003, 0.008))
        P["loom"].path([(x, y - 0.05, z + 0.06), (x, y - 0.05, zt - 0.03)], 0.006, seg=8)
    zr = z0 + h * 0.78 if h > 0.8 else z0 + h * 0.5
    nt = int((w - 0.2) / 0.035)
    for k in range(nt):
        x = x0 + 0.1 + k * 0.035
        if h <= 0.8 and abs(x - (x0 + x1) / 2) < 0.25:
            continue
        P["term"].box((x, y - 0.025, zr), (0.03, 0.05, 0.05))
        (P["wire_o"] if k % 3 == 0 else P["wire_b"]).path(
            [(x, y - 0.05, zr + 0.025), (x, y - 0.06, zr + 0.06), (x + 0.01, y - 0.06, zt - 0.03)], 0.003, seg=6)
    mats = {"frame": M["alu"], "bolt": M["steel"], "tray": M["alu_dark"], "loom": M["cable_g"], "cu": M["copper"],
            "valve": M["steel"], "flange": M["alu"], "sensor": M["anod"], "lens": M["glass"], "drive": M["anod"],
            "fin": M["alu"], "term": M["paint_grey"], "wire_o": M["cable_o"], "wire_b": M["cable_b"],
            "led": M["led_c"]}
    for k, mb in P.items():
        mb.obj(f"{tag}Fill_{k}", mats[k], bevel=0.004 if k in ("frame", "drive", "tray") else 0.0)


def _depth_layers(M, MZ, WZ):
    """R7 (B8_03 H13): foreground layer for the oblique camera - a cut frame post and the near edge of the
    metrology deck between the two stages, with cable chains, so the shot has >= 3 depth planes."""
    fg = {k: K.MB() for k in ("post", "sec")}
    for x in (-2.75, 2.7):
        fg["post"].box((x, -1.05, 1.75), (0.14, 0.14, 3.5))
        fg["sec"].box((x, -1.121, 1.75), (0.142, 0.004, 3.5))
    for k, m_ in (("post", M["alu_dark"]), ("sec", M["alu_dark"])):
        fg[k].obj("FG_" + k, m_, bevel=0.006 if k == "post" else 0.0)


def _wafer_mat(pitch=0.034, street=0.1):
    """R9: polished silicon with a die grid: mirror-like dark blue-grey face, scribe streets slightly rougher and
    darker (object-space grid, pitch in metres)."""
    m = K.mat("WaferDiesR9", (0.3, 0.32, 0.4), metal=1.0, rough=0.05)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sp.inputs[0])
    fac = None
    for ax, p_ in (("X", pitch), ("Y", pitch * 1.25)):
        dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = p_
        nt.links.new(sp.outputs[ax], dv.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(dv.outputs[0], fr.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = street
        nt.links.new(fr.outputs[0], lt.inputs[0])
        if fac is None:
            fac = lt
        else:
            mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
            nt.links.new(fac.outputs[0], mx.inputs[0]); nt.links.new(lt.outputs[0], mx.inputs[1])
            fac = mx
    mc = nt.nodes.new("ShaderNodeMix"); mc.data_type = "RGBA"
    mc.inputs["A"].default_value = (*K.lin((0.3, 0.32, 0.42)), 1)
    mc.inputs["B"].default_value = (*K.lin((0.62, 0.63, 0.66)), 1)
    nt.links.new(fac.outputs[0], mc.inputs["Factor"])
    nt.links.new(mc.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.05
    rr.inputs["To Max"].default_value = 0.3
    nt.links.new(fac.outputs[0], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m


def scan_knots(n):
    """(frame, u) knots of the B8_03 scan; u = 0..1 of the full stroke."""
    fr = [1 + round((n - 1) * p) for p in (0.245, 0.545, 0.85)]
    return [(1, 0.0)] + list(zip(fr, (0.25, 0.55, 0.85))) + [(n, 1.0)]


def _scan_r5(sc, M, n, shot):
    """B8_03 (R5 rebuild). R4 review: the long upper-left illumination leg read as hitting a PO mirror and the
    stage travel could not be read (D 55). Now:
      * the illumination module sits under-left of the mask; its last mirror sends a SHORT leg up at ~6 deg onto the
        face-down mask, which reflects down at ~6 deg (narrow V) into the projection optics;
      * PO = 3 solid mirrors on hexapod mounts in a W fold, then one narrow band onto the wafer directly below;
      * reticle stage travels 8 units (1.6 m), wafer stage 1 unit (0.2 m) the opposite way, on numbered rulers
        with the same unit; the exposed stripe grows on the wafer; calm, dark, defocused services wall."""
    MZ, WZ = 2.75, 0.71                                       # R10: wafer on the planar-motor mover's chuck
    # R7 (H9): EXE (High-NA) data only -> chief ray at the mask 5.4 deg, same machine as the 8x scan ratio
    # R8: the in / out legs drawn at 10 deg so they separate on screen; the label says "angle enlarged, ~5.4 deg"
    th6 = math.tan(math.radians(15.0))                       # R11: legs drawn 15 deg apart (R10: in / out merged)
    WY = -0.85                                               # R11: wafer stage further toward the camera
    mask_c, waf_c = Vector((0, 0, MZ)), Vector((0, WY, WZ))
    # R6 (H13): real illuminator train (field facets -> pupil facets -> G1 -> G2) and six PO mirrors M1-M6 in
    # one non-crossing fold, instead of a single feed leg and three mirrors in an empty grey box
    # R9 (H13): one clean line, no crossing anywhere: illuminator zig-zag (source -> field facets -> pupil facets
    # -> G2) -> up onto the mask -> down into a four-mirror "N" through the PO bay -> wafer. Bigger, thicker mirrors.
    g2 = Vector((-th6 * 1.33, 0, MZ - 1.33))
    src = Vector((-2.0, 0, 1.5))
    ff, pf = Vector((-1.38, 0, 1.24)), Vector((-0.78, 0, 1.76))
    m1 = Vector((th6 * (MZ - 1.75), 0, 1.75))
    m2, m3, m4 = Vector((1.78, 0, 2.12)), Vector((1.2, 0, 1.18)), Vector((0.58, 0, 1.5))
    pts = [src, ff, pf, g2, mask_c + Vector((0, 0, -0.012)), m1, m2, m3, m4, waf_c + Vector((0, 0, 0.004))]
    alu, anod, steel = M["alu"], M["anod"], M["steel"]
    M["section"] = K.mat("SectionCutR9", (0.46, 0.47, 0.5), rough=0.6)         # R9: neutral grey cut faces
    dk = K.mat("WallDark", (0.05, 0.055, 0.065), metal=0.5, rough=0.5)
    U = 0.2                                                    # one ruler unit
    a_r, a_w = 4 * U, U / 2                                    # stage travel half-ranges (8 : 1)

    # ---- reticle stage: bridge + rails + magnet track (fixed), carriage + chuck + mask (moving)
    fx = {k: K.MB() for k in ("bridge", "rail", "bolt", "magnet", "led")}
    fx["bridge"].box((0.2, 0.15, MZ + 0.42), (5.6, 1.0, 0.22))
    for y in (-0.32, 0.32):
        fx["rail"].box((0.2, y, MZ + 0.28), (5.2, 0.07, 0.05))
        for k in range(26):
            fx["bolt"].cyl((0.2 - 2.5 + k * 0.2, y, MZ + 0.31), 0.01, 0.02, seg=6)
    for k in range(52):                                       # linear-motor magnet track, alternating
        fx["magnet"].box((0.2 - 2.55 + k * 0.1, 0.0, MZ + 0.3), (0.085, 0.3, 0.025))
    fx["led"].box((0.2, -0.351, MZ + 0.45), (5.4, 0.006, 0.012))
    for k, m_ in (("bridge", anod), ("rail", M["alu_dark"]), ("bolt", steel), ("magnet", K.mat("Magnet", (0.25, 0.26, 0.3),
                  metal=1.0, rough=0.3)), ("led", M["led_c"])):
        fx[k].obj("RBridge_" + k, m_, bevel=0.01 if k == "bridge" else 0.0)
    rp = {k: K.MB() for k in ("car", "bolt", "cable")}
    rp["car"].box((0, 0, MZ + 0.17), (1.3, 0.8, 0.16))
    rp["car"].box((-0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
    rp["car"].box((0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
    # R10: the coil mover of the maglev on the magnet track (coil blocks + hoses), and the patterned reflective
    # mask (die fields, absorber lines, fiducials) in a ceramic chuck with clamps, face down
    import hero_kit_r10 as HK
    PR = HK.new_parts()
    for x in (-0.45, 0.0, 0.45):
        PR["coil"].box((x, 0.0, MZ + 0.27), (0.36, 0.34, 0.06))
    HK.cooling_bundle(PR, [Vector((0.5, 0.2, MZ + 0.27)), Vector((0.75, 0.25, MZ + 0.34)), Vector((1.4, 0.35, MZ + 0.36))],
                      k=3, r=0.01, clamp_every=0.3, block=False)
    HK.reticle(PR, (0, 0, MZ), size=0.52, face=(0, 0, -1))
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):
        rp["bolt"].cyl((x, -0.401, MZ + 0.2), 0.014, 0.02, rot=(math.radians(90), 0, 0), seg=8)
    K.cable_run(rp["cable"], [(0.55, 0.3, MZ + 0.26), (0.9, 0.38, MZ + 0.3), (1.6, 0.42, MZ + 0.3)], n=4, r=0.01, seed=3)
    rpiv = bpy.data.objects.new("RStage", None)
    sc.collection.objects.link(rpiv)
    for k, m_ in (("car", alu), ("bolt", steel), ("cable", M["cable_b"])):
        ob = rp[k].obj("RStage_" + k, m_, bevel=0.012 if k == "car" else 0.0)
        ob.parent = rpiv
    HK.finish(PR, M, "RStageK", parent=rpiv)
    slit = K.MB()                                             # the illuminated slit stays put; the mask runs through it
    slit.box((0, 0, MZ - 0.004), (0.4, 0.07, 0.002))
    slit.obj("MaskSlit", K.emit_mat("MaskSlitGlow", K.VIOLET, 9.0))

    # ---- wafer stage: granite + guides (fixed), short-stroke stage + chuck + wafer + exposed stripe (moving)
    # R10: planar motor - Halbach checkerboard magnet plate on the granite; the coil mover carries the chuck
    wf = {k: K.MB() for k in ("granite", "cable")}
    wf["granite"].box((0.1, 0.1, 0.27), (3.6, 1.4, 0.54))
    K.cable_run(wf["cable"], [(-1.6, 0.45, 0.62), (-1.9, 0.5, 0.5), (-2.0, 0.55, 0.05)], n=5, seed=9)
    for k, m_ in (("granite", M["granite"]), ("cable", M["cable_g"])):
        wf[k].obj("WBase_" + k, m_, bevel=0.02 if k == "granite" else 0.0)
    zpl = WZ - 0.159
    PF = HK.new_parts()
    HK.planar_motor(PF, 0.1, 0.1, zpl, 3.3, 1.25, mover=False, base=False)
    HK.finish(PF, M, "WBase_PM")
    wp = {k: K.MB() for k in ("wafer",)}
    WR = 0.34                                                           # R11: wafer >= 1/4 frame (R10: "small white square")
    wp["wafer"].cyl((0, 0, WZ - 0.0015), WR, 0.003, seg=160)
    PM = HK.new_parts()
    HK.planar_mover(PM, 0.0, 0.0, zpl, mover_w=0.86, wafer_r=WR, wafer=False)
    wpiv = bpy.data.objects.new("WStage", None)
    sc.collection.objects.link(wpiv)
    wpiv.location.y = WY
    for o in bpy.data.objects:
        if o.name.startswith("WBase_"):
            o.location.y += WY
    for k, m_ in (("wafer", _wafer_mat()),):
        ob = wp[k].obj("WStage_" + k, m_)
        ob.parent = wpiv
    HK.finish(PM, M, "WStageK", parent=wpiv)
    # exposed stripe: wafer-local, grows from where the slit started (+a_w side moves under the slit)
    ex = K.MB()
    ex.box((0.5, 0, 0), (1.0, 0.2, 0.0016))
    exo = ex.obj("Exposed", K.emit_mat("ExposedGlow", K.VIOLET, 1.6, halo=0.35))
    exo.parent = wpiv
    exo.location = (-a_w, 0, WZ + 0.0012)
    _keys_linear(exo, "scale", [(1, 0.001), (n, 2 * a_w)], index=0)

    # ---- R9 (H13, k2B): both bays are thick machined housings in neutral grey (cut faces light grey, never
    # orange), packed with large nameable parts; the beam is a wide k4A column; mirrors are big and thick
    hs = K.mat("HousingGreyR9", (0.2, 0.21, 0.23), metal=0.7, rough=0.42, speck=0.12)
    hb = {k: K.MB() for k in ("box", "sec", "bolt", "port", "rib")}

    def housing(x0, x1, z0, z1, yb, t=0.12, depth=0.7, roof_port=None):
        cx, cz, w, h = (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0
        yf = yb - depth                                               # cut plane (front)
        hb["box"].box((cx, yb + t / 2, cz), (w, t, h))                # back wall
        for z in (z0 + t / 2, z1 - t / 2):                            # floor / roof
            hb["box"].box((cx, (yb + yf) / 2, z), (w, depth, t))
            hb["sec"].box((cx, yf - 0.003, z), (w, 0.006, t + 0.002))
        for x in (x0 + t / 2, x1 - t / 2):                            # side walls
            hb["box"].box((x, (yb + yf) / 2, cz), (t, depth, h))
            hb["sec"].box((x, yf - 0.003, cz), (t + 0.002, 0.006, h))
        for x in (x0 - 0.03, x1 + 0.03):                              # outer ribs + bolt rows on the cut edge
            hb["rib"].box((x, (yb + yf) / 2, cz), (0.06, depth * 0.9, h + 0.08))
        nb = int(w / 0.11)
        for i in range(nb):
            for z in (z0 + t * 0.5, z1 - t * 0.5):
                hb["bolt"].cyl((x0 + 0.08 + i * (w - 0.16) / max(1, nb - 1), yf - 0.012, z), 0.011, 0.02,
                               rot=(math.radians(90), 0, 0), seg=8)
        if roof_port is not None:
            hb["port"].ring((roof_port, (yb + yf) / 2, z1 + 0.03), 0.13, 0.08, 0.06, seg=32)
            hb["bolt"].bolts((roof_port, (yb + yf) / 2, z1 + 0.062), 0.105, 10, 0.009, 0.012)

    housing(-2.2, -0.05, 0.98, 2.04, 0.36, roof_port=-1.6)            # illuminator bay
    housing(-0.02, 2.2, 0.96, 2.42, 0.42, roof_port=1.5)              # projection-optics bay
    hb["box"].obj("Bay_box", hs, bevel=0.01)
    hb["sec"].obj("Bay_sec", M["section"])
    hb["bolt"].obj("Bay_bolt", steel)
    hb["port"].obj("Bay_port", alu)
    hb["rib"].obj("Bay_rib", M["alu_dark"], bevel=0.006)
    # ports where the beam passes the housings (illuminator roof -> mask, PO roof <- mask, PO floor -> wafer)
    pp = K.MB()
    for c, r_ in ((g2.lerp(mask_c, 0.33), 0.13), (mask_c.lerp(m1, 0.52), 0.13), (m4.lerp(waf_c, 0.55), 0.1)):
        pp.ring((c.x, c.y, c.z), r_ * 1.35, r_, 0.05, seg=40)
    pp.obj("BeamPorts", alu)

    mm = {k: K.MB() for k in ("mirror", "mount", "bolt", "substrate", "spot", "copper", "cable_o", "cable_b")}
    facets = K.MB()
    for i, (p_, r_) in enumerate(((ff, 0.17), (pf, 0.17), (g2, 0.15), (m1, 0.14), (m2, 0.23), (m3, 0.22),
                                  (m4, 0.16))):
        j = pts.index(p_)
        nrm = K.mirror_normal(pts[j - 1], p_, pts[j + 1])
        K.mirror_with_mount(mm["mirror"], mm["mount"], mm["bolt"], p_, nrm, r_, thick=r_ * 0.45,
                            seed=i, mbsub=mm["substrate"], mbspot=mm["spot"], spot=0.62, mbpipe=mm["copper"],
                            mbcable=mm["cable_b" if i % 2 else "cable_o"])
        if i < 2:                                          # field / pupil facet mirrors: a grid of small tiles
            qf = Vector((0, 0, 1)).rotation_difference(nrm)
            Rf = qf.to_matrix()
            for u in range(-6, 7):
                for v in range(-6, 7):
                    o = Vector((u * 0.026, v * 0.026, 0))
                    if o.length < r_ * 0.9:
                        facets.box(p_ + nrm * 0.003 + Rf @ o, (0.022, 0.022, 0.006), rot=qf.to_euler())
    facets.obj("FacetTiles", M["coating"])
    for k, m_ in (("mirror", M["coating"]), ("mount", alu), ("bolt", steel), ("substrate", M["substrate"]),
                  ("spot", M["spot"]), ("copper", M["steel"]), ("cable_o", M["cable_g"]), ("cable_b", M["cable_b"])):
        mm[k].obj("POm_" + k, m_)

    # ---- beam: k4A wide column (as wide as the mirror footprint), faint volumetric sleeve; no thin core line
    rad = [0.06, 0.1, 0.1, 0.075, 0.028, 0.075, 0.13, 0.12, 0.09, 0.02]   # R11: thin at the mask -> dark gap between in / out
    col = K.MB()
    K.beam_columns(col, pts, rad, seg=40)
    col.obj("ScanCol", K.beam_column_mat("EUVColS", K.VIOLET, strength=1.8, edge=0.85, core=0.16, vol=0.3))
    sv = K.MB()
    K.beam_columns(sv, pts, [r_ * 1.5 + 0.01 for r_ in rad], seg=32)
    sv.obj("ScanSleeve", K.beam_column_mat("EUVSleeve", K.VIOLET, strength=0.4, edge=0.05, core=0.0, vol=0.05))
    sl = K.MB()
    sl.box((0, WY, WZ + 0.0035), (0.014, 0.2, 0.002))
    sl.obj("SlitW", K.emit_mat("SlitGlow", K.VIOLET, 30.0))
    for i, p_ in enumerate((ff, pf, g2, m1, m2, m3, m4, mask_c + Vector((0, 0, -0.1)), waf_c + Vector((0, 0, 0.12)))):
        K.point(f"Bounce{i}", p_ + Vector((0, -0.25, 0)), 12, K.VIOLET, 0.08)
    # dense parts kit on both back walls + top-of-bay electronics (k2B: no bare wall left)
    # R10: nameable parts only on both back walls (profile frame, CF viewports, valve islands, turbo pumps, hose
    # bundles, hexapod mounts, harnesses); roof: turbo pumps on the ports, valve islands, hose bundles
    import parts_kit_r8 as PK
    keep = [(Vector((p_.x, 0.3, p_.z)), 0.3) for p_ in (ff, pf, g2, m1, m2, m3, m4)]
    keep11 = [(Vector((p_.x, 0.0, p_.z)), 0.25) for p_ in (ff, pf, g2, m1, m2, m3, m4)]   # R11: on the mirrors
    HP = HK.new_parts()
    import hero_kit_r11 as HK11                  # R11: non-repeating blocks (R10: one tiled panel + flange cell)
    HK11.wall_r11(HP, -2.08, -0.17, 1.1, 1.92, 0.36, seed=11, keep=keep11, scale=0.95, depth=1.1, front_y=0.15, blocks=6)
    HK11.wall_r11(HP, 0.1, 2.08, 1.08, 2.3, 0.42, seed=13, keep=keep11, scale=0.95, depth=1.1, front_y=0.17, blocks=6)
    HK.valve_island(HP, (-1.0, 0.1, 2.2), (0, -1, 0), nval=12, s=1.6, drop=0.12)
    HK.valve_island(HP, (0.95, 0.1, 2.6), (0, -1, 0), nval=10, s=1.6, drop=0.12)
    HK.cooling_bundle(HP, [(-2.1, 0.25, 2.12), (-0.15, 0.25, 2.12)], k=4, r=0.014, up=(0, 1, 0))
    HK.cooling_bundle(HP, [(0.1, 0.3, 2.5), (2.1, 0.3, 2.5)], k=4, r=0.014, up=(0, 1, 0))
    HK.flange_viewport(HP, (2.22, -0.1, 1.9), (1, 0, 0), 0.06)
    HK.finish(HP, M, "B8HK")
    P = PK.new_parts()
    PK.turbo_pump(P, (-1.6, 0.0, 2.25), (0, 0, 1), 0.12)                    # roof pumps on the two ports
    PK.turbo_pump(P, (1.5, 0.0, 2.62), (0, 0, 1), 0.12)
    PK.gate_valve(P, (-2.38, 0.0, 1.5), (1, 0, 0), 0.08)                      # side port valve + pump
    PK.turbo_pump(P, (-2.7, 0.0, 1.5), (-1, 0, 0), 0.11)
    PK.bellows(P, (2.26, -0.1, 1.3), (2.6, -0.1, 1.3), 0.07)
    PK.drag_chain(P, Vector((-1.9, 0.62 + WY, 0.56)), 1.3, R=0.07, w=0.12)        # wafer-stage energy chain
    PK.drag_chain(P, Vector((-2.4, 0.32, MZ + 0.54)), 1.5, R=0.06, w=0.1)    # reticle-stage energy chain
    PK.finish(P, M, "B8Kit")

    # ---- rulers (same unit U for both stages): reticle 0..8 under the bridge, wafer 0..1 on the granite front
    ink = K.emit_mat("RulerInk", (0.86, 0.9, 0.96), 3.0)
    tk = K.MB()
    yr, zr = -0.62, MZ + 0.47
    for i in range(0, 33):
        x = -a_r + i * U / 4
        h = 0.07 if i % 4 == 0 else 0.03
        tk.box((x, yr, zr - h / 2), (0.007, 0.006, h))
    tk.box((0, yr, zr), (2 * a_r + 0.02, 0.006, 0.006))
    yw0, zw = -0.62, 0.47
    yw = yw0 + WY
    for i in range(0, 9):
        x = a_w - i * U / 8
        h = 0.06 if i in (0, 8) else 0.025
        tk.box((x, yw, zw - h / 2), (0.004, 0.006, h))
    tk.box((0, yw, zw), (2 * a_w + 0.01, 0.006, 0.005))
    tk.obj("Rulers", ink)
    for i in range(9):
        _txt(f"RD{i}", str(i), (-a_r + i * U, yr, zr - 0.14), 0.1, ink)
    _txt("WD0", "0", (a_w, yw, zw - 0.12), 0.085, ink)
    _txt("WD1", "1", (-a_w, yw, zw - 0.12), 0.085, ink)
    brk = K.MB()                                              # ruler brackets tie the rulers to the bridge / granite
    for x in (-a_r - 0.08, a_r + 0.08):
        brk.box((x, (yr - 0.25) / 2 + 0.05, zr + 0.05), (0.03, 0.42, 0.02))
    brk.obj("RulerBrk", M["alu_dark"])
    pm = K.emit_mat("PtrCyan", K.CYAN, 7.0)
    pr, pw = K.MB(), K.MB()
    pr.box((0, yr + 0.005, zr - 0.03), (0.022, 0.01, 0.075))
    pr.box((0, (yr - 0.4) / 2 + 0.005, MZ + 0.2), (0.016, 0.24, 0.016))
    pr.box((0, yr + 0.005, MZ + 0.32), (0.016, 0.01, 0.22))
    pw.box((0, yw0 + 0.005, zw + 0.025), (0.012, 0.01, 0.07))
    pw.box((0, -0.48, 0.63), (0.012, 0.28, 0.012))
    pw.box((0, -0.62, 0.575), (0.012, 0.012, 0.11))
    pr.obj("PtrR", pm).parent = rpiv
    pw.obj("PtrW", pm).parent = wpiv
    # ghost marks of where both stages started (thin dashed outline on the rulers)
    gm = K.MB()
    gm.box((-a_r, yr - 0.002, zr - 0.03), (0.02, 0.004, 0.075))
    gm.box((a_w, yw - 0.002, zw + 0.025), (0.012, 0.004, 0.07))
    gm.obj("StartMarks", K.emit_mat("StartInk", (0.35, 0.55, 0.6), 1.5))
    # R8: the three review frames (25 / 55 / 85 %) land exactly on u = 0.25 / 0.55 / 0.85, so the read-outs are
    # 2.00 / 0.25, 4.40 / 0.55, 6.80 / 0.85 grid units - a steady 8 : 1 (mograph/r2_ov_zr8.py uses the same knots)
    knots = scan_knots(n)
    _keys_linear(rpiv, "location", [(f, -a_r + 2 * a_r * u) for f, u in knots], index=0)
    _keys_linear(wpiv, "location", [(f, a_w - 2 * a_w * u) for f, u in knots], index=0)

    # ---- calm services wall: far, dark panels with seams, two columns, a tray; out of focus
    wl = {k: K.MB() for k in ("panel", "seam", "col", "tray", "pipe")}
    wl["panel"].box((0.2, 1.9, 1.7), (9.0, 0.05, 4.2))
    for k in range(-8, 10):
        wl["seam"].box((0.2 + k * 0.55, 1.87, 1.7), (0.012, 0.01, 4.2))
    wl["seam"].box((0.2, 1.87, 2.6), (9.0, 0.01, 0.012))
    for x in (-2.6, 3.0):
        wl["col"].box((x, 1.4, 1.7), (0.16, 0.16, 4.2))
    wl["tray"].box((0.2, 1.6, 3.55), (8.0, 0.3, 0.06))
    for y in (1.75, 1.68):
        wl["pipe"].tube((-4.0, y, 3.75 if y > 1.7 else 3.85), (4.5, y, 3.75 if y > 1.7 else 3.85), 0.035)
    for k, m_ in (("panel", dk), ("seam", K.mat("SeamD", (0.02, 0.022, 0.026), rough=0.6)), ("col", M["alu_dark"]),
                  ("tray", M["alu_dark"]), ("pipe", M["steel"])):
        wl[k].obj("Wall_" + k, m_)

    # ---- lights: dark interior, product key on both stages, rims
    _lights_dark(0.35)
    for o in bpy.data.objects:
        if o.name in ("PlasmaGlow", "IFGlow", "MaskGlow"):
            bpy.data.objects.remove(o)
    K.area("StageKeyR", (-1.0, -3.0, 4.3), (0, 0, MZ + 0.2), 2.5, 300, (1.0, 0.98, 0.95))
    K.area("StageKeyW", (-1.0, -2.8, 1.8), (0, WY, WZ), 2.5, 120, (1.0, 0.98, 0.95))
    K.area("RimTop", (1.5, 1.0, 4.6), (0, 0, MZ), 2.0, 500, (0.8, 0.85, 1.0))
    K.area("POKey", (2.6, -2.8, 2.0), (0.9, 0.2, 1.6), 2.0, 300, (0.95, 0.97, 1.0))
    K.area("IlKey", (-2.5, -2.5, 2.4), (-1.0, 0.2, 1.5), 1.6, 160, (0.95, 0.97, 1.0))
    K.area("BayFillL", (-1.0, -2.2, 1.55), (-1.0, 0.25, 1.5), 1.2, 60, (0.9, 0.93, 1.0))
    K.area("BayFillP", (1.0, -2.6, 1.7), (0.95, 0.4, 1.6), 1.6, 160, (0.9, 0.93, 1.0))
    K.area("BayFillI", (-1.0, -2.4, 2.2), (-1.0, 0.2, 1.5), 1.4, 110, (0.9, 0.93, 1.0))   # R8: light the kit
    K.area("RimPO", (2.8, 1.2, 2.6), (0.95, 0.0, 1.6), 1.2, 160, (0.75, 0.82, 1.0))
    # R9: a soft card behind / above the wafer that the polished silicon mirrors toward the camera (sheen)
    K.area("WaferSheen", (0.25, WY + 0.75, 0.92), (0.0, WY, WZ), 0.9, 14, (0.85, 0.88, 1.0), size_y=0.3)
    # R7 (H13 depth): high 3/4 camera looking down into both bays, so front section edge / beam / back-plate
    # mechatronics / services wall read as separate layers; slow crane drift for parallax
    _depth_layers(M, MZ, WZ)
    cam, tgt = K.camera("CamR2", lens=19)
    # R11: low and close over the wafer stage (wafer big in the foreground), mask + both bays still above
    K.key_path(cam, tgt, [(1, (-0.85, -3.4, 2.4), (0.05, -0.1, 1.62)), (n, (-0.3, -3.5, 2.33), (0.12, -0.1, 1.6))],
               interp="LINEAR")
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    cam.data.dof.focus_distance = 3.2
    cam.data.dof.aperture_fstop = 8.0
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.15
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    sc.camera = cam
    K.anchors(shot, {"rr0": Vector((-a_r, yr, zr)), "rr1": Vector((a_r, yr, zr)),
                     "wr0": Vector((a_w, yw, zw)), "wr1": Vector((-a_w, yw, zw)),
                     "mask": mask_c, "wafer": waf_c, "g2": g2, "src": src, "m2": m2})
    return sc
