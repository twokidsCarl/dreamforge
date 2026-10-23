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
    M["cone"] = (K.beam_column_mat("EUVCone", K.VIOLET, strength=1.3, edge=0.7, core=0.0, vol=0.04)
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
        K.key_path(cam, tgt, [(1, (-3.6, -3.7, 2.9), (-2.5, 0.3, 3.15)), (f1, (-1.9, -3.5, 2.8), (-2.2, 0.3, 3.2))])
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 5.6
        cam.data.dof.focus_object = tgt
    elif variant == "tour":
        cam.data.lens = 30
        K.key_path(cam, tgt, [(1, (-8.4, -4.4, 3.3), (-7.4, 0.0, 2.3)),
                              (round(f1 * 0.25), (-6.6, -4.2, 3.0), (-5.6, 0.1, 2.5)),
                              (round(f1 * 0.55), (-3.4, -4.6, 3.3), (-2.5, 0.2, 3.0)),
                              (round(f1 * 0.85), (-1.0, -3.7, 3.0), (0.38, 0.3, 3.35)),
                              (f1, (-0.85, -3.6, 2.95), (0.5, 0.3, 3.3))])
    elif variant == "collect":
        cam.data.lens = 30
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 4
        cam.data.dof.focus_object = tgt
        cam.data.lens = 24
        cam.data.dof.aperture_fstop = 8
        # R8 (F): keep collector AND intermediate focus in frame the whole shot so the cone visibly converges on IF
        K.key_path(cam, tgt, [(1, (-5.7, -4.9, 3.25), (-6.25, 0.0, 2.4)), (f1, (-6.5, -4.5, 3.05), (-6.45, 0.0, 2.38))])
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
        else:                                # R5 (H13): thin bright core + halo, no wide columns that merged
            pts, rad = B.beam_path(*rng)      # into violet smears in the illuminator / PO bays
            K.beam_columns(mb, pts, [0.05] * len(pts))
            mat = K.beam_column_mat(f"EUVThin{i}", K.VIOLET, strength=5.0, edge=0.75, core=0.3, vol=0.0)
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
    # R5 (H13: the R4 path zig-zagged across itself into a net): one descending zig-zag M1..M6 that never
    # crosses, each bounce a solid mirror on its own mount; restored after this shot is built
    po_keep, por_keep = B.PO, B.PO_R
    B.PO = [Vector(v) for v in PO_ZIGZAG]
    B.PO_R = [0.24, 0.22, 0.26, 0.22, 0.24, 0.2]
    B._projection(M, mbs)
    pts, rad = B.beam_path(5)
    B.PO, B.PO_R = po_keep, por_keep
    pts = [B.MASK + Vector((0, 0, -0.25))] + pts[1:-1] + [B.WAFER + Vector((0, 0, 0.3))]
    # R4: thin k4A beam (no violet fog); the mirrors and their mounts carry the read
    K.beam(mbs["beam"], mbs["halo"], pts, r=0.012, halo=3.0)
    K.beam_columns(mbs["vol"], pts, [0.04] + [0.05] * (len(pts) - 2) + [0.015])
    K.bounce_lights(pts[1:-1], energy=6.0)
    # R4 2A: front cover kept only on the left third, cast ribs, flanges, ports and cables
    cast = mbs["cast"]
    cast.box((0.9, -1.05, 2.52), (0.6, 0.06, 3.1))                          # remaining front cover
    for z in (1.3, 1.9, 2.5, 3.1, 3.7):
        cast.box((0.9, -1.1, z), (0.6, 0.05, 0.06))                          # horizontal ribs
    for x in (0.65, 1.18):
        cast.box((x, -1.1, 2.52), (0.06, 0.05, 3.0))
    mbs["section"].box((1.21, -1.05, 2.52), (0.02, 0.07, 3.1))              # cut face of the cover
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
    mats = {"frame": M["alu"], "bolt": M["steel"], "mirror": M["mirror"], "gold": M["gold"], "copper": M["copper"],
            "mount": M["alu"], "housing": M["paint"], "greeble": M["alu"], "anod": M["anod"], "steel": M["steel"],
            "led": M["led_c"], "cable_b": M["cable_b"], "cable_o": M["cable_o"], "cable_g": M["cable_g"],
            "pipe": M["steel"], "flange_s": M["alu"], "beam": M["beam"], "halo": M["beam_halo"], "stage": M["paint_grey"],
            "alu": M["alu"], "substrate": M["substrate"], "spot": M["spot"], "vol": M["beam_wide"], "skin": M["paint"],
            "section": M["section"], "cast": M["alu"]}
    mats["mirror"] = M["coating"]
    mats["housing"] = M["alu"]
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
    piv.rotation_euler = (0, 0, math.radians(-38))
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(4))
    piv.keyframe_insert("rotation_euler", frame=n)
    K.suit_person("Eng1", (4.4, -1.2, 0), 1.78, "stand", facing=-30)   # R5: clean-room suit (k9B), not a grey dummy
    cam, tgt = K.camera("CamR2", lens=35)
    K.key_path(cam, tgt, [(1, (1.4, -9.2, 3.4), (2.3, 0, 2.2)), (n, (1.6, -8.6, 2.6), (2.3, 0, 2.3))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.5
    sc["vignette"] = 0.3
    sc.camera = cam
    K.anchors("B7_06", {"po": Vector((1.8, 0.05, 2.5)), "eng": Vector((4.4, -1.2, 1.8)), "top": Vector((1.8, 0.05, 4.1))})
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
    MZ, WZ = 2.75, 0.62
    # R7 (H9): EXE (High-NA) data only -> chief ray at the mask 5.4 deg, same machine as the 8x scan ratio
    # R8: the in / out legs drawn at 10 deg so they separate on screen; the label says "angle enlarged, ~5.4 deg"
    th6 = math.tan(math.radians(10.0))
    mask_c, waf_c = Vector((0, 0, MZ)), Vector((0, 0, WZ))
    g2 = Vector((-th6 * 1.25, 0, MZ - 1.25))                 # last illuminator mirror
    # R6 (H13): real illuminator train (field facets -> pupil facets -> G1 -> G2) and six PO mirrors M1-M6 in
    # one non-crossing fold, instead of a single feed leg and three mirrors in an empty grey box
    src = Vector((-1.95, 0, 1.62))
    ff, pf, g1 = Vector((-1.5, 0, 1.3)), Vector((-0.88, 0, 1.72)), Vector((-0.52, 0, 1.3))
    m1 = Vector((th6 * (MZ - 1.75), 0, 1.75))
    m2, m3, m4 = Vector((1.6, 0, 2.08)), Vector((0.66, 0, 1.66)), Vector((1.6, 0, 1.4))
    m5, m6 = Vector((0.98, 0, 1.06)), Vector((0.42, 0, 1.2))
    pts = [src, ff, pf, g1, g2, mask_c + Vector((0, 0, -0.012)), m1, m2, m3, m4, m5, m6,
           waf_c + Vector((0, 0, 0.004))]
    alu, anod, steel = M["alu"], M["anod"], M["steel"]
    M["section"] = K.mat("SectionCutR8", (0.42, 0.17, 0.07), rough=0.62)        # R8: cut faces in a cut colour
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
    for k, m_ in (("bridge", anod), ("rail", steel), ("bolt", steel), ("magnet", K.mat("Magnet", (0.25, 0.26, 0.3),
                  metal=1.0, rough=0.3)), ("led", M["led_c"])):
        fx[k].obj("RBridge_" + k, m_, bevel=0.01 if k == "bridge" else 0.0)
    rp = {k: K.MB() for k in ("car", "chuck", "mask", "absorb", "bolt", "cable")}
    rp["car"].box((0, 0, MZ + 0.17), (1.3, 0.8, 0.16))
    rp["car"].box((-0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
    rp["car"].box((0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
    rp["chuck"].box((0, 0, MZ + 0.06), (0.7, 0.62, 0.07))
    rp["mask"].box((0, 0, MZ + 0.012), (0.56, 0.5, 0.024))
    for k in range(15):                                       # absorber pattern, visible on the front edge too
        rp["absorb"].box((-0.25 + k * 0.036, 0, MZ - 0.001), (0.016, 0.46, 0.003))
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):
        rp["bolt"].cyl((x, -0.401, MZ + 0.2), 0.014, 0.02, rot=(math.radians(90), 0, 0), seg=8)
    K.cable_run(rp["cable"], [(0.55, 0.3, MZ + 0.26), (0.9, 0.38, MZ + 0.3), (1.6, 0.42, MZ + 0.3)], n=4, r=0.01, seed=3)
    rpiv = bpy.data.objects.new("RStage", None)
    sc.collection.objects.link(rpiv)
    for k, m_ in (("car", alu), ("chuck", steel), ("mask", M["coating"]), ("absorb", anod), ("bolt", steel),
                  ("cable", M["cable_b"])):
        ob = rp[k].obj("RStage_" + k, m_, bevel=0.012 if k == "car" else 0.0)
        ob.parent = rpiv

    # ---- wafer stage: granite + guides (fixed), short-stroke stage + chuck + wafer + exposed stripe (moving)
    wf = {k: K.MB() for k in ("granite", "rail", "motor", "cable")}
    wf["granite"].box((0.1, 0.1, 0.27), (3.6, 1.4, 0.54))
    for y in (-0.35, 0.35):
        wf["rail"].box((0.1, y, 0.565), (3.2, 0.06, 0.04))
    wf["motor"].box((-1.55, 0.05, 0.68), (0.3, 1.1, 0.24))
    wf["motor"].box((1.75, 0.05, 0.68), (0.3, 1.1, 0.24))
    K.cable_run(wf["cable"], [(-1.6, 0.45, 0.82), (-1.9, 0.5, 0.6), (-2.0, 0.55, 0.05)], n=5, seed=9)
    for k, m_ in (("granite", M["granite"]), ("rail", steel), ("motor", anod), ("cable", M["cable_g"])):
        wf[k].obj("WBase_" + k, m_, bevel=0.02 if k == "granite" else 0.0)
    wp = {k: K.MB() for k in ("stage", "chuck", "wafer", "bolt")}
    wp["stage"].box((0, 0, 0.6), (0.82, 0.7, 0.05))
    wp["chuck"].cyl((0, 0, WZ - 0.012), 0.2, 0.02, seg=64)
    wp["wafer"].cyl((0, 0, WZ - 0.0015), 0.16, 0.003, seg=96)
    for x in (-0.36, 0.36):
        for y in (-0.3, 0.3):
            wp["bolt"].cyl((x, y, 0.628), 0.012, 0.01, seg=8)
    wpiv = bpy.data.objects.new("WStage", None)
    sc.collection.objects.link(wpiv)
    for k, m_ in (("stage", alu), ("chuck", steel), ("wafer", M["wafer"]), ("bolt", steel)):
        ob = wp[k].obj("WStage_" + k, m_, bevel=0.01 if k == "stage" else 0.0)
        ob.parent = wpiv
    # exposed stripe: wafer-local, grows from where the slit started (+a_w side moves under the slit)
    ex = K.MB()
    ex.box((0.5, 0, 0), (1.0, 0.11, 0.0016))
    exo = ex.obj("Exposed", K.emit_mat("ExposedGlow", K.VIOLET, 1.6, halo=0.35))
    exo.parent = wpiv
    exo.location = (-a_w, 0, WZ + 0.0012)
    _keys_linear(exo, "scale", [(1, 0.001), (n, 2 * a_w)], index=0)

    # ---- illumination module (under-left of the mask): cut-open box, horizontal feed, last mirror G2
    il = {k: K.MB() for k in ("box", "sec", "bolt", "port")}
    il["box"].box((-1.05, 0.27, 1.52), (1.9, 0.12, 0.66))         # R8: 12 cm walls (vacuum housing, not sheet)
    il["box"].box((-1.05, 0.0, 1.87), (1.9, 0.66, 0.11))          # top plate (with exit port)
    il["box"].box((-1.05, 0.0, 1.17), (1.9, 0.66, 0.11))
    il["box"].box((-2.02, 0.0, 1.52), (0.11, 0.66, 0.8))
    il["sec"].box((-1.05, -0.332, 1.87), (1.9, 0.006, 0.112))
    il["sec"].box((-1.05, -0.332, 1.17), (1.9, 0.006, 0.112))
    il["sec"].box((-2.02, -0.332, 1.52), (0.112, 0.006, 0.8))
    for x in (-1.95, -0.15):                                      # edge flanges with bolt rows
        il["port"].box((x, -0.34, 1.52), (0.08, 0.04, 0.8))
    il["port"].ring((g2.x + th6 * 0.35, 0, 1.94), 0.1, 0.06, 0.05, seg=32)
    il["bolt"].bolts((g2.x + th6 * 0.35, 0, 1.965), 0.08, 8, 0.008, 0.012)
    il["port"].ring((-1.95, 0, g2.z), 0.1, 0.06, 0.06, rot=(0, math.radians(90), 0), seg=32)
    for i in range(14):
        il["bolt"].cyl((-1.95 + i * 0.13, -0.3, 1.93), 0.01, 0.02, seg=6)
    il["box"].obj("Illum_box", anod, bevel=0.008)
    il["sec"].obj("Illum_sec", M["section"])
    il["bolt"].obj("Illum_bolt", steel)
    il["port"].obj("Illum_port", alu)

    # ---- projection optics: cut-open cage (back plate, cut side walls, flanges with ports), 3 solid mirrors
    cg, sec, fl = K.MB(), K.MB(), K.MB()
    cg.box((0.95, 0.45, 1.6), (1.9, 0.12, 1.42))                  # R8: 11-12 cm walls + cut faces
    for x in (0.0, 1.9):
        cg.box((x, 0.1, 1.6), (0.11, 0.66, 1.5))
        sec.box((x, -0.232, 1.6), (0.112, 0.006, 1.5))
    for z in (0.88, 2.32):
        cg.box((0.95, 0.1, z), (2.0, 0.66, 0.1))
        sec.box((0.95, -0.232, z), (2.0, 0.006, 0.102))
        for i in range(16):
            K.MB.cyl(fl, (0.1 + i * 0.115, -0.2, z + 0.03), 0.01, 0.02, seg=6)
    cg.obj("POCage", anod, bevel=0.008)
    sec.obj("POCageSection", M["section"])
    fl.obj("POCageBolts", steel)
    lm = K.MB()
    K.cable_run(lm, [(0.12, 0.3, 2.22), (0.12, 0.32, 1.6), (0.14, 0.3, 0.98)], n=4, r=0.009, seed=5)
    K.cable_run(lm, [(1.8, 0.3, 2.22), (1.8, 0.32, 1.5), (1.78, 0.3, 0.98)], n=4, r=0.009, seed=6)
    lm.obj("POCageLoom", M["cable_g"])
    mm = {k: K.MB() for k in ("mirror", "mount", "bolt", "substrate", "spot", "copper", "cable_o", "cable_b")}
    facets = K.MB()
    for i, (p_, r_) in enumerate(((ff, 0.1), (pf, 0.1), (g1, 0.08), (g2, 0.1), (m1, 0.075), (m2, 0.19), (m3, 0.14),
                                  (m4, 0.17), (m5, 0.12), (m6, 0.11))):
        j = pts.index(p_)
        nrm = K.mirror_normal(pts[j - 1], p_, pts[j + 1])
        K.mirror_with_mount(mm["mirror"], mm["mount"], mm["bolt"], p_, nrm, r_,
                            seed=i, mbsub=mm["substrate"], mbspot=mm["spot"], spot=0.55, mbpipe=mm["copper"],
                            mbcable=mm["cable_b" if i % 2 else "cable_o"])
        if i < 2:                                          # field / pupil facet mirrors: a grid of small tiles
            qf = Vector((0, 0, 1)).rotation_difference(nrm)
            Rf = qf.to_matrix()
            for u in range(-3, 4):
                for v in range(-3, 4):
                    o = Vector((u * 0.026, v * 0.026, 0))
                    if o.length < r_ * 0.9:
                        facets.box(p_ + nrm * 0.003 + Rf @ o, (0.022, 0.022, 0.006), rot=qf.to_euler())
    facets.obj("FacetTiles", M["coating"])
    for k, m_ in (("mirror", M["coating"]), ("mount", alu), ("bolt", steel), ("substrate", M["substrate"]),
                  ("spot", M["spot"]), ("copper", M["steel"]), ("cable_o", M["cable_g"]), ("cable_b", M["cable_b"])):
        mm[k].obj("POm_" + k, m_)

    # ---- beam: thin bright core + soft halo + faint column (k4A), one path only
    core, halo = K.MB(), K.MB()
    K.beam(core, halo, pts, r=0.009, halo=3.0)
    core.obj("ScanCore", M["beam"])
    halo.obj("ScanHalo", M["beam_halo"])
    col = K.MB()
    K.beam_columns(col, pts, [0.05, 0.05, 0.055, 0.05, 0.055, 0.05, 0.05, 0.065, 0.06, 0.06, 0.05, 0.04, 0.012])
    col.obj("ScanCol", K.beam_column_mat("EUVColS", K.VIOLET, strength=1.1, edge=0.26, core=0.035, vol=0.16))
    # R7: volumetric sleeve (k4A light-in-air), very faint, wider than the column
    sv = K.MB()
    K.beam_columns(sv, pts, [0.11, 0.11, 0.12, 0.11, 0.12, 0.1, 0.1, 0.13, 0.12, 0.12, 0.1, 0.08, 0.02], seg=32)
    sv.obj("ScanSleeve", K.beam_column_mat("EUVSleeve", K.VIOLET, strength=0.35, edge=0.03, core=0.0, vol=0.05))
    sl = K.MB()
    sl.box((0, 0, WZ + 0.0035), (0.012, 0.11, 0.002))
    sl.obj("SlitW", K.emit_mat("SlitGlow", K.VIOLET, 30.0))
    for i, p_ in enumerate((ff, pf, g1, g2, m1, m2, m3, m4, m5, m6, mask_c + Vector((0, 0, -0.1)),
                            waf_c + Vector((0, 0, 0.12)))):
        K.point(f"Bounce{i}", p_ + Vector((0, -0.22, 0)), 7, K.VIOLET, 0.06)
    # R6 (H13): fill both bays with named mechatronics (frames, trays, manifolds, flanges, drives, terminals)
    # R8 (H13): both bays carry the shared parts kit (pumps, gate valves, gauges, card cages, manifold, chain)
    import parts_kit_r8 as PK
    keep = [(a.lerp(b, k / 6), 0.13) for a, b in zip(pts, pts[1:]) for k in range(7)]
    P = PK.new_parts()
    PK.populate_wall(P, -1.92, -0.18, 1.24, 1.8, 0.21, seed=11, keep=keep, scale=0.62, chain=False)
    PK.populate_wall(P, 0.1, 1.8, 0.95, 2.25, 0.39, seed=13, keep=keep, scale=0.7)
    PK.turbo_pump(P, (-1.55, 0.0, 1.93), (0, 0, 1), 0.1)                    # roof pump on the illuminator
    PK.gate_valve(P, (-2.2, 0.05, 1.5), (1, 0, 0), 0.06)                      # side port valve
    PK.turbo_pump(P, (-2.5, 0.05, 1.5), (-1, 0, 0), 0.09)
    PK.turbo_pump(P, (1.62, 0.12, 2.38), (0, 0, 1), 0.09)                     # roof pump on the PO housing
    PK.gauge(P, (1.96, 0.0, 1.9), (1, 0, 0), 0.035)
    PK.bellows(P, (1.96, 0.0, 1.3), (2.35, 0.0, 1.3), 0.06)
    PK.drag_chain(P, Vector((-1.9, 0.62, 0.56)), 1.3, R=0.07, w=0.12)        # wafer-stage energy chain
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
    yw, zw = -0.62, 0.86
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
    brk.box((0.0, -0.6, 0.72), (0.03, 0.03, 0.28))
    brk.obj("RulerBrk", M["alu_dark"])
    pm = K.emit_mat("PtrCyan", K.CYAN, 7.0)
    pr, pw = K.MB(), K.MB()
    pr.box((0, yr + 0.005, zr - 0.03), (0.022, 0.01, 0.075))
    pr.box((0, (yr - 0.4) / 2 + 0.005, MZ + 0.2), (0.016, 0.24, 0.016))
    pr.box((0, yr + 0.005, MZ + 0.32), (0.016, 0.01, 0.22))
    pw.box((0, yw + 0.005, zw + 0.025), (0.012, 0.01, 0.07))
    pw.box((0, -0.48, 0.63), (0.012, 0.28, 0.012))
    pw.box((0, -0.62, 0.72), (0.012, 0.012, 0.18))
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
    K.area("StageKeyW", (-1.0, -2.8, 1.8), (0, 0, WZ), 2.5, 240, (1.0, 0.98, 0.95))
    K.area("RimTop", (1.5, 1.0, 4.6), (0, 0, MZ), 2.0, 500, (0.8, 0.85, 1.0))
    K.area("POKey", (2.6, -2.8, 2.0), (0.9, 0.2, 1.6), 2.0, 300, (0.95, 0.97, 1.0))
    K.area("IlKey", (-2.5, -2.5, 2.4), (-1.0, 0.2, 1.5), 1.6, 160, (0.95, 0.97, 1.0))
    K.area("BayFillL", (-1.0, -2.2, 1.55), (-1.0, 0.25, 1.5), 1.2, 60, (0.9, 0.93, 1.0))
    K.area("BayFillP", (1.0, -2.6, 1.7), (0.95, 0.4, 1.6), 1.6, 160, (0.9, 0.93, 1.0))
    K.area("BayFillI", (-1.0, -2.4, 2.2), (-1.0, 0.2, 1.5), 1.4, 110, (0.9, 0.93, 1.0))   # R8: light the kit
    K.area("RimPO", (2.8, 1.2, 2.6), (0.95, 0.0, 1.6), 1.2, 160, (0.75, 0.82, 1.0))
    # R7 (H13 depth): high 3/4 camera looking down into both bays, so front section edge / beam / back-plate
    # mechatronics / services wall read as separate layers; slow crane drift for parallax
    _depth_layers(M, MZ, WZ)
    cam, tgt = K.camera("CamR2", lens=28)                                    # R8: tighter on the bays
    K.key_path(cam, tgt, [(1, (-1.75, -4.3, 3.8), (0.05, 0.25, 1.78)), (n, (-1.15, -4.45, 3.6), (0.2, 0.25, 1.76))],
               interp="LINEAR")
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4.0
    cam.data.dof.focus_distance = (Vector((-1.6, -4.8, 3.85)) - Vector((0.1, 0.1, 1.75))).length
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.15
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    sc.camera = cam
    K.anchors(shot, {"rr0": Vector((-a_r, yr, zr)), "rr1": Vector((a_r, yr, zr)),
                     "wr0": Vector((a_w, yw, zw)), "wr1": Vector((-a_w, yw, zw)),
                     "mask": mask_c, "wafer": waf_c, "g2": g2, "src": src, "m2": m2})
    return sc
