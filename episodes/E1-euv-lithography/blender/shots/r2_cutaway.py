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
    M["cone"] = (K.beam_column_mat("EUVCone", K.VIOLET, strength=1.0, edge=0.22, core=0.03, vol=0.06)
                 if variant == "collect" else K.beam_column_mat("EUVCone", K.VIOLET, strength=1.4, edge=0.4, core=0.06, vol=0.15))
    K.clean_cycles(sc)
    if variant == "po":
        return _po_turntable(sc, M, n)
    # R3: the title lights the path up module by module; the scan shot draws its own narrow band
    if variant == "scan":
        return _scan_closeup(sc, M, n, shot)
    B.machine(M, studio=studio, cut=True, beam=variant != "title", bounce=8.0 if studio else 20.0)
    if variant == "title":
        _sequential_beam(M, n)
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
                              (round(f1 * 0.85), (0.0, -3.8, 3.5), (0.7, 0.3, 3.7)),
                              (f1, (0.5, -3.6, 3.4), (1.0, 0.3, 3.4))])
    elif variant == "collect":
        cam.data.lens = 30
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 4
        cam.data.dof.focus_object = tgt
        cam.data.lens = 24
        cam.data.dof.aperture_fstop = 8
        K.key_path(cam, tgt, [(1, (-5.6, -4.3, 3.3), (-6.5, 0.0, 2.35)), (f1, (-6.6, -2.9, 3.0), (-7.6, 0.0, 2.3))])
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
                o.data.energy *= 0.15
        lh.obj("LaserHalo", M["laser_halo"])
    sc.camera = cam
    K.anchors(shot, {"plasma": B.PLASMA, "coll": B.COLL + Vector((0.12, 0, 0.35)), "hole": B.COLL + Vector((0.02, 0, 0)),
                     "if": B.IF, "ffm": B.FFM, "pfm": B.PFM, "g1": B.G1, "mask": B.MASK, "rstage": B.MASK + Vector((0, -0.9, 0.35)),
                     "po": B.PO[2], "wafer": B.WAFER, "wstage": B.WAFER + Vector((-0.5, -0.6, -0.05)),
                     "eng": Vector((-2.7, -2.4, 1.9))})
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
        mats = {"rstage": M["paint"], "flange_s": M["alu"], "bolt": M["steel"], "steel": M["steel"], "mask": M["coating"],
                "anod": M["anod"], "led": M["led_c"], "cable_b": M["cable_b"], "cable_g": M["cable_g"], "stage": M["paint"],
                "granite": M["granite"], "wafer": M["wafer"]}
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
    # closed PO housing between them: dark anodized box with ribs, flange rings, lifting lugs, ports
    hs, rib, fl = K.MB(), K.MB(), K.MB()
    hs.box((0, 0.33, 1.62), (1.7, 0.76, 1.24))
    for z in (1.1, 1.45, 1.8, 2.14):
        rib.box((0, -0.06, z), (1.74, 0.03, 0.05))
    for x in (-0.6, -0.2, 0.2, 0.6):
        rib.box((x, -0.06, 1.62), (0.05, 0.03, 1.2))
    for z in (0.98, 2.27):
        fl.box((0, 0.33, z), (1.9, 0.9, 0.06))
        for i in range(16):
            K.MB.cyl(fl, (-0.88 + i * 0.117, -0.13, z + 0.04), 0.012, 0.02, seg=6)
    for x in (-0.86, 0.86):
        fl.cyl((x, 0.33, 1.6), 0.09, 0.08, rot=(0, math.radians(90), 0), seg=24)
    hs.obj("POHousing", M["anod"], bevel=0.012)
    rib.obj("POHousingRibs", M["alu_dark"], bevel=0.005)
    fl.obj("POHousingFlanges", M["alu"])
    # back services wall for depth (dense: greebles, motors, looms, coolant lines)
    wall = {k: K.MB() for k in ("housing", "bolt", "flange_s", "greeble", "anod", "frame", "led", "pipe", "copper",
                                "steel", "alu", "gold", "cable_b", "cable_o", "cable_g")}
    wall["housing"].box((0, 1.45, 1.9), (6.0, 0.05, 3.8))
    B._interior_fill(wall, -3.0, 3.0, 0.1, 3.7, y_back=1.45, seed=31)
    wm = {"housing": M["paint_grey"], "bolt": M["steel"], "flange_s": M["alu"], "greeble": M["alu_dark"], "anod": M["anod"],
          "frame": M["alu_dark"], "led": M["led_c"], "pipe": M["steel"], "copper": M["copper"], "steel": M["steel"],
          "alu": M["alu"], "gold": M["gold"], "cable_b": M["cable_b"], "cable_o": M["cable_o"], "cable_g": M["cable_g"]}
    for k, mb in wall.items():
        if len(mb.bm.verts):
            mb.obj("Wall_" + k, wm[k])
        else:
            mb.bm.free()
    # fold mirror + beam
    g2 = Vector((0, -0.15, 1.3))
    mm = {k: K.MB() for k in ("mirror", "mount", "bolt", "substrate", "spot", "copper", "cable_o")}
    K.mirror_with_mount(mm["mirror"], mm["mount"], mm["bolt"], g2, K.mirror_normal(Vector((-3.0, -0.15, 1.3)), g2, mask_c),
                        0.12, mbsub=mm["substrate"], mbspot=mm["spot"], spot=0.8, mbpipe=mm["copper"], mbcable=mm["cable_o"])
    for k, m_ in (("mirror", M["coating"]), ("mount", M["alu"]), ("bolt", M["steel"]), ("substrate", M["substrate"]),
                  ("spot", M["spot"]), ("copper", M["copper"]), ("cable_o", M["cable_o"])):
        mm[k].obj("G2_" + k, m_)
    bm = K.MB()
    refl = mask_c + Vector((0, 0.15 / 1.4, -1.0)) * 0.45
    K.beam_columns(bm, [Vector((-3.5, -0.15, 1.3)), g2, mask_c, refl], [0.07, 0.07, 0.05, 0.06])
    K.beam_columns(bm, [Vector((0, 0.0, 0.95)), waf_c + Vector((0, 0, 0.005))], [0.05, 0.012])
    bm.obj("ScanBand", M["beam_wide"])
    sl = K.MB()                                      # exposure slit footprints on mask and wafer (fixed)
    sl.box((0, 0, MZ - 0.004), (0.5, 0.06, 0.004))
    sl.box((0, 0, WZ + 0.003), (0.13, 0.016, 0.003))
    sl.obj("Slit", K.emit_mat("SlitGlow", K.VIOLET, 25.0))
    K.point("SlitLightM", mask_c + Vector((0, -0.3, -0.25)), 50, K.VIOLET, 0.1)
    K.point("SlitLightW", waf_c + Vector((0, -0.3, 0.2)), 20, K.VIOLET, 0.05)
    K.point("FoldLight", g2 + Vector((0, -0.2, 0.1)), 15, K.VIOLET, 0.05)
    # rulers: 0.1 m ticks under the reticle stage, 0.0125 m beside the wafer (8 divisions each, 8x shorter)
    tk = K.MB()
    for i in range(-5, 6):
        h = 0.1 if i % 5 == 0 else 0.055
        tk.box((i * 0.1, -1.0, MZ + 0.12 + h / 2), (0.008, 0.01, h))
        tk.box((i * 0.0125, -0.62, WZ + 0.06 + h * 0.4 / 2), (0.003, 0.006, h * 0.4))
    tk.box((0, -1.0, MZ + 0.12), (1.02, 0.01, 0.006))
    tk.box((0, -0.62, WZ + 0.06), (0.13, 0.006, 0.003))
    tk.obj("Rulers", K.emit_mat("RulerInk", (0.85, 0.88, 0.95), 2.5))
    pm = K.emit_mat("PtrCyan", K.CYAN, 6.0)
    pr, pw = K.MB(), K.MB()
    pr.box((0, -1.01, MZ + 0.26), (0.03, 0.012, 0.06))
    pw.box((0, -0.625, WZ + 0.1), (0.006, 0.008, 0.02))
    po_, pwo = pr.obj("RulerPtr", pm), pw.obj("RulerPtrW", pm)
    po_.parent, pwo.parent = rpiv, wpiv
    d = 0.1
    for piv, a0, a1 in ((rpiv, -4 * d, 4 * d), (wpiv, d / 2, -d / 2)):
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
    K.area("StageKeyR", (-1.2, -3.2, 4.6), (0, 0, MZ + 0.3), 2.5, 700, (1.0, 0.98, 0.95))
    K.area("StageKeyW", (-1.2, -3.0, 2.0), (0, 0, WZ), 2.5, 450, (1.0, 0.98, 0.95))
    K.area("RimTop", (1.5, 1.0, 4.8), (0, 0, MZ), 2.0, 600, (0.8, 0.85, 1.0))
    cam, tgt = K.camera("CamR2", lens=27)
    K.key_path(cam, tgt, [(1, (-1.5, -6.0, 2.3), (0.0, 0.2, 1.85)), (n, (1.6, -5.7, 2.0), (0.15, 0.2, 1.8))],
               interp="LINEAR")
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.2
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.1
    sc.camera = cam
    K.anchors(shot, {"rstage": Vector((0.9, -0.6, MZ + 0.35)), "mask": mask_c, "wafer": waf_c,
                     "wstage": Vector((0.45, -0.5, WZ - 0.02)), "fold": g2})
    return sc


def _sequential_beam(M, n):
    """A0_10: the violet path lights up module by module (source cone -> illuminator -> mask + PO -> wafer)."""
    segs = [(None, 1), ((0, 6), 0.3), ((5, None), 0.6)]
    for i, (rng, start) in enumerate(segs):
        mb = K.MB()
        if rng is None:
            K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
            mat = M["cone"]
        else:
            pts, rad = B.beam_path(*rng)
            K.beam_columns(mb, pts, rad)
            mat = M["beam_wide"].copy()
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
    B._projection(M, mbs)
    pts, rad = B.beam_path(5)
    pts = [B.MASK + Vector((0, 0, -0.25))] + pts[1:-1] + [B.WAFER + Vector((0, 0, 0.3))]
    K.beam_columns(mbs["vol"], pts, rad)
    # R3 2A: front cover kept on the left 55 % (only 2-3 mirrors show), cast ribs, flanges, ports and cables
    cast = mbs["cast"]
    cast.box((1.25, -1.05, 2.52), (1.3, 0.06, 3.1))                         # remaining front cover
    for z in (1.3, 1.9, 2.5, 3.1, 3.7):
        cast.box((1.25, -1.1, z), (1.3, 0.05, 0.06))                         # horizontal ribs
    for x in (0.7, 1.25, 1.85):
        cast.box((x, -1.1, 2.52), (0.06, 0.05, 3.0))
    mbs["section"].box((1.9, -1.05, 2.52), (0.02, 0.07, 3.1))               # cut face of the cover
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
            "section": M["section"], "cast": M["paint"]}
    mats["mirror"] = M["coating"]
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
    piv.rotation_euler = (0, 0, math.radians(-38))
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(4))
    piv.keyframe_insert("rotation_euler", frame=n)
    K.suit_person("Eng1", (4.4, -1.2, 0), 1.78, "stand", facing=-30)
    cam, tgt = K.camera("CamR2", lens=35)
    K.key_path(cam, tgt, [(1, (1.4, -9.2, 3.4), (2.3, 0, 2.2)), (n, (1.6, -8.6, 2.6), (2.3, 0, 2.3))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.5
    sc["vignette"] = 0.3
    sc.camera = cam
    K.anchors("B7_06", {"po": Vector((1.8, 0.05, 2.5)), "eng": Vector((4.4, -1.2, 1.8)), "top": Vector((1.8, 0.05, 4.1))})
    return sc
