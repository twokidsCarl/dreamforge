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

# R20 (R20_ROOT_CAUSE rows 1 + 2): per-shot switch. A shot in this set builds with beam_r20 (mirror-to-mirror straight
# cones, end caps on the mirror planes, lit focus tip) + its R20 structural fix; remove a shot id to get its R19 pixels.
# C_03 / B8_03 / B8_03M only pick up beam_r20 (no shot-specific R20 code).
# HARD-STOP REVERT (cut agent, 45 min): no shot reached a 32-spp GO smoke, so every shot renders R19 pixels.
# Candidate set (8-spp smokes looked right for B5_01 / B7_06 / B3_02; see r20smoke/cut/SMOKE.md):
R20_SHOTS_CANDIDATE = {"B5_01", "B7_06", "B3_02", "A0_10", "C_03", "B8_03", "B8_03M"}
R20_SHOTS = {"B5_01", "B3_02"}   # main-process 32-spp smoke: A0_10 (cut agent Q4 no), B7_06 (Q4 no: curved mass inside M5 at 85 %), C_03 (Q4 no: no visible change, crossing segment kept), B8_03 + B8_03M (Q4 no: stray black plates at top) stay R19
_R20 = [None]
# R21 (R21_ROOT_CAUSE rows 3 / 4 / 6): two sub-agents share this module.
#   cut-hero owns R21_HERO + scripts/cut_hero_r21.py (B3_02 / B5_01: hero >= 1/4 frame, one outgoing cone)
#   cut-beam owns R21_2B + scripts/beam_r21.py + scripts/cut_2b_r21.py (flat landing-spot end caps; A0_10 / C_03 / B8_03 / B7_06)
# A shot in R21_SHOTS builds with its R20 code paths ON + beam_r21 (aliased over beam_r19 / beam_r20) + its post() hook.
# Remove a shot id to get its R20 pixels back.
R21_HERO = {"B5_01"}   # cuth R21 smoke: B3_02 Q4 no (cone volume over the dish reflection + floating scaled holder bolts) -> R20 pixels
R21_2B = {"B7_06", "A0_10", "B8_03", "B8_03M"}   # cutb R21 smoke 06:42: C_03 (not built) stays R20; B8_03 + B8_03M re-enabled by main process for its 32-spp smoke; candidates: {"C_03", "B8_03", "B8_03M"}
R21_SHOTS = R21_HERO | R21_2B
# R22 (R22_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process. For a shot in a set,
# build() calls <hook>.pre(variant, shot, module) first (may patch module globals / functions) and
# <hook>.post(sc, variant, shot) last (may add / replace / delete objects, move the camera). Remove a shot id from its
# set -> exact R21 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
#   cuth owns R22_HERO + scripts/cut_hero_r22.py + scripts/kit_r22.py; cutb owns R22_2B + scripts/cut_2b_r22.py.
R22_HERO = {"B5_01"}   # B3_02: main 32-spp smoke Q4 no (cone toward IF gone at 85 %, agent-written risk) -> R21 pixels; # C_03: cuth not built (FFM move needs pre-build patch) -> R21 pixels
R22_2B = {"B7_06"}   # B8_03(+M): main 32-spp smoke Q4 no (mirror wafer: bright blotch reflections hide the field grid) -> R21 pixels; # A0_10: cutb Q4 no (path still breaks mid-bay) -> R21 pixels
R22_HOOKS = [(R22_HERO, "cut_hero_r22"), (R22_2B, "cut_2b_r22")]
# R23 (R23_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R22
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R23 set ->
# exact R22 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R23_HERO = {"C_03"}   # B3_02: agent-written risk (CO2 laser line dropped at the 55° camera) = auto Q4 no -> R22 pixels; B5_01: no change needed -> R22   # cuth agent: cut_hero_r23.py (rows 2 / 3)
R23_2B = {"B7_06", "A0_10", "B8_03", "B8_03M"}   # cutb agent: cut_2b_r23.py (rows 2 / 3 / 5)
R23_HOOKS = [(R23_HERO, "cut_hero_r23"), (R23_2B, "cut_2b_r23")]
# R24 (R24_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R23
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R24 set ->
# exact R23 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R24_BEAM = {"A0_10", "B5_01", "C_03"}                   # cbeam agent: cut_beam_r24.py (row 3: one path per screen, beam_r24)
R24_HERO = {"B7_06", "B8_03", "B8_03M"}   # B3_02: chero agent-written risk (laser line + cone reflection overlap the dish face) = auto Q4 no -> R23 pixels   # chero agent: cut_hero_r24.py (rows 3 / 5: collector geometry, M5/M6 solid rings + 3-leg path, wafer glint)
R24_HOOKS = [(R24_BEAM, "cut_beam_r24"), (R24_HERO, "cut_hero_r24")]
# R25 (R25_ROOT_CAUSE.md): per-agent shot sets + hook modules, pre-wired by the main process, layered AFTER the R24
# hooks (same pre(variant, shot, module) / post(sc, variant, shot) interface). Remove a shot id from its R25 set ->
# exact R24 pixels. Gold shots (A0_02 / D_07 / B9_05 / B1_22) are never in a set.
R25_BEAM = set()   # B5_01: main 32-spp Q4 no (legs = hard-edged flat translucent sheets, "violet glass panels / ribbon" - same new negative read as B2_08 R24) -> R24 pixels; A0_10: cbeam self-flagged risks (roof touches the f184 subtitle, mask turn a small corner, PFM reads as the white back of a dish) = auto Q4 no; C_03: BEAMCHECK25 NOGO f222 (FFM/G1/G2 edge-on) -> R24 pixels   # cbeam agent: cut_beam_r25.py (rows 1 / 2 / 4: turn mirrors via beam_r25, taper, machine density)
R25_HERO = {"B3_02", "B7_06"}   # B8_03(+M): main 32-spp Q4 no (slit cone = hard-edged translucent wedge, same flat-sheet read; mad <0.01) -> R24 pixels   # chero agent: cut_hero_r25.py (rows 2 / 4 / 5: B3_02 dish into the set, taper)
R25_HOOKS = [(R25_BEAM, "cut_beam_r25"), (R25_HERO, "cut_hero_r25")]
_R21 = [None]


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


def _r22_hooks(shot):
    """R22: hook modules for this shot (in set order)."""
    import importlib
    return [importlib.import_module(h) for s_, h in R22_HOOKS + R23_HOOKS + R24_HOOKS + R25_HOOKS if shot in s_]   # R23 hooks after R22, R24 after R23, R25 after R24


def _r22_pre(variant, shot):
    for h in _r22_hooks(shot):
        if hasattr(h, "pre"):
            h.pre(variant, shot, __import__(__name__))


def _r22_post(sc, variant, shot):
    for h in _r22_hooks(shot):
        if hasattr(h, "post"):
            h.post(sc, variant, shot)


def build(variant="illum", shot=None):
    _r22_pre(variant, shot)
    import beam_r12 as BR
    import beam_r16 as R16                    # R16 row 3: diverge -> gather legs, ends fade, line landing on the slit
    R16.install()
    R16.COLL_FADE[0] = (0.06, 0.5) if variant == "collect" else None   # R16 row 4: no violet haze over the collector
    # R17 row 4 (R16: "beam shape changed twice, still an equal-width tube / slab; haze hides the mirrors"): route
    # change - thin cores between mirrors + a bright landing highlight on every mirror + source cones' haze lowered
    import beam_r17 as R17
    R17.install()
    R17.CORE[0] = {"title": 0.03, "illum": 0.02, "tour": 0.013, "collect": 0.02, "scan": 0.012, "po": 0.013}.get(variant, 0.02)
    R17.HOT[0] = {"title": 2.0, "illum": 1.4, "tour": 1.3, "scan": 1.0, "po": 1.0}.get(variant, 1.0)
    # R18 row 2 (R17: all three beam routes read as lines / tubes - "thin lines / laser lines / equal-width
    # tubes"): asset change - beam_r18 solid volumetric light cones whose end radii follow the two mirrors'
    # apertures (soft shell, R17 landing highlights kept, one current segment per screen). No width knob of
    # beam_r16 / beam_r17 is touched; the R17 thin-core legs are no longer built.
    # R19 row 2 (R18 p2: "55-85 % 帧里紫光散成满腔的雾", cones = "soft hoses / fog blobs"): beam_r19 = beam_r18 with
    # the continuity rule - each frustum runs landing -> landing, volume ONLY inside the cone (the outer halo shell
    # that spread the haze is gone), a landing highlight at every bounce and at the path's end. No width knob.
    # (every `import beam_r18 as R18` in this module now loads beam_r19 under the same alias)
    _R21[0] = shot if shot in R21_SHOTS else None
    _R20[0] = shot if (shot in R20_SHOTS or _R21[0]) else None
    if _R21[0]:                               # R21 row 3: every `import beam_r19` / `import beam_r20` loads beam_r21
        import beam_r21 as R21B
        R21B.alias()
    elif _R20[0]:                             # R20 rows 1 + 2: every `import beam_r19` below loads beam_r20
        import beam_r20 as R20B
        R20B.alias()
    import beam_r19 as R18
    R18.install()
    import cut_mirror_r19 as CM
    _WALL19[0] = variant
    _orig_wall = B._wall
    B._wall = _wall19                         # R19 row 3: named-part walls (kit_r19) on the reviewed walls only
    try:
        sc = _build(variant, shot)
    finally:
        B._wall = _orig_wall
    BR.flush()                                # R12: landing spots collected by the soft beam columns (R17 highlights)
    # R19 row 2 (R18 p2: "镜面全部换成真金属反射 … 现在偏哑光，有塑料感 … 镜面能反射出周围结构"): every mirror face
    # of the module -> one high-reflective mirror (roughness 0.05, light tone, no emission / violet), and the hero
    # mirrors get lit REAL structure (kit_r19 assemblies) in their camera-reflection direction (no light cards)
    M = _M19[0]
    CM.apply(M)
    heroes = {"illum": [(B.FFM, K.mirror_normal(B.IF, B.FFM, B.PFM), 1.8)],
              "collect": [(B.COLL + Vector((0.02, 0, 0.18)), Vector((1, 0, 0)), 1.4)],
              "tour": [(B.FFM, K.mirror_normal(B.IF, B.FFM, B.PFM), 1.6)],
              "scan": _HERO19[0]}.get(variant)
    if heroes:
        CM.reflect_env(sc, M, heroes, tag=f"Env19{variant}")
    if _R20[0] == "B3_02":
        _collector_dark_r20()
    if _R20[0] == "B5_01":
        _illum_cleanup_r20()
    if _R21[0] in R21_HERO:                   # R21 rows 4 / 6 (cut-hero)
        import cut_hero_r21 as H21
        H21.post(sc, variant, shot)
    if _R21[0] in R21_2B:                     # R21 row 3 (cut-beam)
        import cut_2b_r21 as T21
        T21.post(sc, variant, shot)
    _r22_post(sc, variant, shot)
    return sc


_WALL19 = [None]
_HERO19 = [None]
_M19 = [None]
# R19 row 3 (R18: "中舱后墙是同一种方格小盒重复铺满" A0_10 / "右侧墙是重复的横管 + 格栅" B3_02): these two walls are
# built with the shared read-only kit_r19.wall_r19 (5-6 big different named assemblies + a diagonal coolant run)
_WALL19_SEEDS = {"title": (12,), "collect": (33,)}


def _illum_r20(n):
    """B5_01 R20 row 1 (R19: "入射光是等宽的实心光柱…看不到从分面镜反射出去的那一束…箭头指向入射光的方向"):
    incoming = ONE cone opening from the IF tip (bright point) and landing as a bright spot on the field facet array;
    outgoing = 6 thin beamlets, each from its own facet on the field facet mirror to the pupil facet mirror (in frame),
    landing spot on the pupil facets. No other leg is lit (each end of every lit segment is on screen)."""
    import beam_r20 as R20B
    nf = K.mirror_normal(B.IF, B.FFM, B.PFM)
    npf = K.mirror_normal(B.FFM, B.PFM, B.G1)
    src = B.IF + (B.FFM - B.IF).normalized() * 0.12      # IF aperture exit (just outside the neck flange: visible)
    os_, ms_ = R20B.segment(src, B.FFM, 0.006, 0.2, "IllumInR20", k=1.3, nb=nf, seg=64)
    R20B.key_vis(os_, ms_, n, 0.0, None)
    R20B.tip(src, (B.FFM - B.IF).normalized(), "IllumIFTipR20", 1, scale=1.3)
    ifm = K.MB()                             # the cone's apex: a bright point at the IF (where the light opens from)
    ifm.sphere(src, 0.03, 16)
    ifm.obj("IFPinchR20", K.emit_mat("IFPinchR20", (0.88, 0.84, 1.0), 30.0)).visible_shadow = False
    R20B._land_timed(B.FFM, nf, "IllumLandFFMR20", 1, scale=1.8)
    d = (B.PFM - B.FFM).normalized()
    u = d.cross(Vector((0, 0, 1))).normalized()
    v = u.cross(d).normalized()
    f_out = 1
    for k_, (a_, b_) in enumerate(((-1, -1), (0, -1), (1, -1), (-1, 1), (0, 1), (1, 1))):
        pa = B.FFM + u * (0.11 * a_) + v * (0.07 * b_)
        pb = B.PFM + u * (0.045 * a_) + v * (0.03 * b_)
        os_, ms_ = R20B.segment(pa, pb, 0.03, 0.02, f"IllumOutR20_{k_}", k=1.0, na=nf, nb=npf, seg=32)
        f_out = R20B.key_vis(os_, ms_, n, 0.1, None)
    R20B._land_timed(B.PFM, npf, "IllumLandPFMR20", f_out, scale=1.5)


def _illum_cleanup_r20():
    """B5_01 R20 row 1 (R19: "右侧那根白色悬空杆读不出用途，删掉"): the bar is part of the R8 wall kit mesh
    (R8Kit2_hose_w: a white hose stub sticking out beside the field facet mirror, z ~3.85) - its faces in that box are
    deleted."""
    for nm, xr, yr, zr in ILLUM_ROD_R20:
        print("[r20] rod faces cut:", nm, _cut_faces(nm, xr, yr, zr))


ILLUM_ROD_R20 = [("R8Kit2_hose_w", (-1.9, -1.25), (-0.45, 0.1), (3.66, 4.05))]


def _collector_dark_r20():
    """B3_02 R20 row 2 (R19: "收集镜现在像带网格的透明玻璃罩。改成金属镜面…深色镜面质感（不要彩虹色），去掉蜂窝格"):
    the collector's reflective face becomes a DARK polished multilayer metal (neutral blue-grey, roughness 0.05, no
    emission, no iridescence); it reads as a dark metal bowl that carries the grazing studio highlights instead of a
    bright see-through dome mirroring the cage grid."""
    dark = K.mat("CollectorDarkML_R20", (0.16, 0.165, 0.185), metal=1.0, rough=0.05, coat=0.6)
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.data.materials:
            continue
        idx = [i for i, m in enumerate(ob.data.materials) if m is not None and
               m.name.startswith(("EUVMirrorHiR19", "CollectorML_R15", "EUVCoatingML_R15"))]
        if not idx:
            continue
        mw = ob.matrix_world
        hit = []
        for pg in ob.data.polygons:          # faces of the collector dish only (the mirror mesh holds every mirror)
            if pg.material_index not in idx:
                continue
            c = mw @ pg.center
            if B.COLL.x - 0.05 < c.x < B.COLL.x + 0.36 and math.hypot(c.y, c.z - B.COLL.z) < 0.72:
                hit.append(pg)
        if hit:
            ob.data.materials.append(dark)
            k_ = len(ob.data.materials) - 1
            for pg in hit:
                pg.material_index = k_
            print("[r20] collector dark:", ob.name, len(hit))


def _wall19():
    import hero_kit_r12 as HK12_

    def disp(*a, **kw):
        if kw.get("seed") in _WALL19_SEEDS.get(_WALL19[0], ()):
            import kit_r19 as KR
            kw.pop("blocks", None)
            if _WALL19[0] == "title":        # the diagonal hose run crossed the mid bay like a second (white) path
                kw["hoses"] = False
            return KR.wall_r19(*a, **kw)
        return HK12_.wall_r12(*a, **kw)
    return disp


def _build(variant="illum", shot=None):
    import beam_r12 as BR
    import hero_kit_r12 as HK12
    B.R12[0] = True                          # R12: bay walls on hero_kit_r12 (14 types, shared no-repeat counter)
    HK12.reset()
    n = K.nframes("B8_03" if shot == "B8_03M" else shot) if shot else 120
    sc = C.reset_scene(n)
    studio = variant in ("title", "po")
    M = K.palette(studio=studio)
    M["wafer"] = K.mat("WaferSi", (0.32, 0.33, 0.42), metal=1.0, rough=0.08)
    # R15 root cause 2 ("mirrors don't read as mirrors": violet glass collector, self-lit facet panel, chrome donuts):
    # every mirror of every channel uses the one shared Mo/Si mirror surface (mirror_r15) - neutral polished metal,
    # no emission, no violet base; blanks / substrates are fine-ground; kit beam footprints are a dim violet glow
    # only (the bright landing spots are beam_r12's, on the legs that are actually lit)
    import mirror_r15 as MR
    M["mirror"] = MR.ml_mirror("EUVMirrorML_R15")
    M["coating"] = MR.ml_mirror("EUVCoatingML_R15")
    M["substrate"] = MR.ground_edge("EUVMirrorBlankR15", tone=0.42)
    M["brushed"] = K.mat("BrushedAluR11", (0.7, 0.71, 0.74), metal=1.0, rough=0.22, brushed=0.35)
    M["facet"] = MR.ml_mirror("FacetML_R15", rough=0.1, tone=0.26, coat=0.15)   # field facets: dark polished, lit only by the beam
    M["facet18"] = MR.ml_mirror("FacetML_R18", rough=0.05, tone=0.78, coat=0.4)  # R18 B5_01: mirror strips
    M["spot"] = K.emit_mat("BeamSpotR15", K.VIOLET, 2.2, halo=0.9)
    _M19[0] = M
    if variant == "title":                   # k1C: near-black backdrop, product-lit machine, white serif title above
        C.set_world(top=(0.004, 0.005, 0.008), horizon=(0.03, 0.033, 0.04), bottom=(0.05, 0.05, 0.055), strength=1.0)
        flo = K.mat("StudioFloor", (0.3, 0.31, 0.33), rough=0.15, coat=0.6)
        K.floor("Floor", flo, z=0.0)
        _lights_studio()
    elif studio:
        K.world_studio(0.9)
        flo = K.mat("StudioFloor", (0.55, 0.56, 0.58), rough=0.18, coat=0.5)
        if _R20[0] == "B7_06":               # R20 row 2 (k2A, R19: "主体和白背景几乎一样亮，光比远不到 8:1"):
            C.set_world(top=(0.07, 0.074, 0.082), horizon=(0.05, 0.052, 0.058), bottom=(0.02, 0.02, 0.022),
                        strength=1.0)        # mid-grey backdrop
            flo = K.mat("StudioFloorR20", (0.09, 0.092, 0.098), rough=0.75, coat=0.0, spec=0.15)   # no rim sheen
        K.floor("Floor", flo, z=0.0)
        _lights_studio()
        if _R20[0] == "B7_06":               # the big top softbox lit the floor as bright as the body: 15 %
            for nm_ in ("Top", "Fill"):
                lo_ = bpy.data.objects.get(nm_)
                if lo_ is not None:
                    lo_.data.energy *= 0.15 if nm_ == "Top" else 0.6
    else:
        K.world_dark(0.55)
        K.floor("Floor", K.mat("FloorDark", (0.05, 0.055, 0.065), rough=0.3, coat=0.3), z=0.0)
        _lights_dark()
    if variant == "collect":                 # R15: shared mirror surface (R14: "translucent violet glass")
        M["coating"] = MR.ml_mirror("CollectorML_R15", rough=0.035)
        M["substrate"] = MR.ground_edge("CollectorBlankR15", tone=0.3)
    M["cone"] = (K.beam_column_mat("EUVCone", K.VIOLET, strength=0.6, edge=0.8, core=0.0, vol=0.02)   # R11: see-through
                 if variant == "collect" else K.beam_column_mat("EUVCone", K.VIOLET, strength=1.4, edge=0.4, core=0.06, vol=0.15))
    # R12 (R11 review: "constant-width noisy tubes"): soft-edged cones with a waist between mirrors + landing spots
    BR.install(K, M)
    if variant == "collect":                 # rim-lit see-through cone: the dish face stays readable behind it
        # R14 (R13: "16 converging rays read as a wire birdcage"): a soft semi-transparent volume cone, bright on its
        # axis and fading to the silhouette; the IF neck is sawn open so the apex shows
        M["cone"] = BR.soft_mat("EUVCollectConeR14", K.VIOLET, strength=1.35, alpha=0.4, power=1.25)
        # R15: a little thinner (0.5 -> 0.4) so the mirror face shows through instead of reading as violet glass
    K.clean_cycles(sc)
    if variant == "po":
        return _po_barrels_r15(sc, M, n)       # R15: disc mirrors + k2B barrel (R14 _po_barrels_r14 kept for reference)
    # R3: the title lights the path up module by module; the scan shot draws its own narrow band
    if variant == "scan":                    # R5: rebuilt (short illumination leg under the mask, 8:1 rulers)
        return _scan_r12(sc, M, n, shot)      # R12: rebuilt around the wafer stage + PIP of the reticle stage
    if variant == "title":                   # R5 (H13): the title's PO bay uses the non-crossing M1..M6 zig-zag
        B.PO = [Vector(v) for v in PO_ZIGZAG]
        B.PO_R = [0.24, 0.22, 0.26, 0.22, 0.24, 0.2]
        if _R20[0] == "A0_10":               # R20 row 2 (R19: "投影箱里的紫光只保留 3–4 段折返，每个拐点都落在看得见的
            B.PO = [B.PO[0], B.PO[3], B.PO[4]]   # 镜面上"): 3 mounted PO mirrors -> mask, M, M, M, wafer = 4 straight
            B.PO_R = [0.24, 0.22, 0.24]          # cones, every turn on a built mirror with its landing highlight
    if variant == "tour":                    # R13 (R12: "in / out overlap into one vertical column"): the fold mirror
        import hero_kit_r10 as HK10          # and PO1 move out so the cones meet the mask at ~20 deg each side
        B.G2 = Vector((-0.2, 0.3, 2.3))      # (label keeps "约 5.4°（角度放大示意）"); fine absorber-line mask
        B.PO = [Vector(v) for v in B.PO]
        B.PO[0] = Vector((1.3, 0.25, 2.3))
        HK10.MASK_STYLE[0] = "r13"
    B.FRONT_FLANGE[0] = variant != "collect"
    B.IF_CUT[0] = variant == "collect"
    B.FRONT_POSTS_SKIP = (-4.0, -0.9) if variant == "tour" else ((-6.0,) if variant == "collect" else ())
    B.LIP_SKIP_X = (0.6,) if variant == "tour" else ()
    # R15 (B5_01: "every facet glows like an LED panel"): only the facets inside the lit footprint get a beam mark
    import hero_kit_r11 as HK11
    import hero_kit_r15 as H15
    _ffm = HK11.field_facet_mirror_r11

    def _ffm15(P, c, n, *a, spot_mb=None, **kw):
        return _ffm(P, c, n, *a, spot_mb=None if spot_mb is None else H15.SpotFilter(spot_mb, c, 0.2), **kw)
    HK11.field_facet_mirror_r11 = _ffm15
    try:
        B.machine(M, studio=studio, cut=True, beam=variant not in ("title", "tour", "illum"), bounce=8.0 if studio else 20.0)
    finally:
        HK11.field_facet_mirror_r11 = _ffm
    if variant == "collect":                 # R15 (R14: "a second beam + pupil mirror top right = two light paths"):
        for nm in ("R2_vol", "R2_spot"):     # B3_02 shows only plasma -> collector -> IF; the downstream path is off
            vo = bpy.data.objects.get(nm)
            if vo is not None:
                bpy.data.objects.remove(vo)
        BR.SPOTS[:] = []
        import beam_r17 as R17
        R17.LAND[:] = []
        import beam_r19 as R18               # R18: machine()'s full-path cones (beam_r18.columns) are off here too
        for o_ in R18.take():
            bpy.data.objects.remove(o_)
    if variant == "illum":                   # R14 (R13: "two beams cross; a white dot where they cross"): the path is
        pts, rad = B.beam_path(0, 6)         # lit leg by leg - only the current leg bright, earlier legs a ghost
        # R16 row 3 (R15: "light stops at the facet mirror, no next station"): the outgoing leg field facet ->
        # pupil facet is lit from 20 %, the onward legs pupil -> condenser -> fold -> mask follow by 45 %
        # R18 row 2 (R17: "two equal-width tubes from the same point, almost parallel - which is in, which out?"):
        # volumetric cones - IF -> field facets arrives NARROW (0.025 -> 0.075), facets -> pupil facet leaves WIDE
        # (0.21 -> 0.27, onto the visible round pupil mirror); the onward legs follow fainter; the incoming leg fades
        # out once the outgoing one carries the screen
        import beam_r19 as R18
        lg = [(pts[0], pts[1], 0.025, 0.075, 0.0, 0.62, 1.3), (pts[1], pts[2], 0.21, 0.27, 0.2, None, 1.0)]
        lg += [(pts[i], pts[i + 1], rad[i] * 0.8, rad[i + 1] * 0.8, t, None, 0.6)
               for i, t in ((2, 0.33), (3, 0.4), (4, 0.45))]
        if _R20[0] == "B5_01":               # R20 row 1: IF cone + facet -> pupil beamlets (R19 legs not built)
            lg = []
            _illum_r20(n)
        for i, (a_, b_, ra_, rb_, t0, t1, kk) in enumerate(lg):
            os_, ms_ = R18.cone(a_, b_, ra_, rb_, f"IllumCone{i}", k=kk)
            f_on = R18.key_vis(os_, ms_, n, t0, t1)
            if i + 1 < len(pts) - 1:
                R18._land_timed(b_, K.mirror_normal(pts[i], pts[i + 1], pts[i + 2]), f"IllumLand{i}", f_on)
        # R18 (R17: "facets are black curved strips, read as vent louvres"): bright polished facet strips + one
        # soft card whose reflection runs along them
        for o in bpy.data.objects:
            for sl in getattr(o, "material_slots", []):
                if sl.material is not None and sl.material.name.startswith("FacetML_R15"):
                    sl.material = M["facet18"]
        fc_ = K.area("FacetCardR18", (-2.4, -2.2, 4.6), B.FFM, 2.0, 140, (0.95, 0.96, 1.0), size_y=0.5)
        try:                                 # R19 row 2: no light card in the mirror - the facets reflect real lit
            fc_.visible_glossy = False       # structure (cut_mirror_r19.reflect_env) + the beam's own landings
        except AttributeError:
            pass
        mb = K.MB()
        K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
        # R17 row 4: the source cone keeps its R16 soft look at ~40 % (M["beam_wide"] is now the thin-core material)
        mb.obj("IllumSrcCone", BR.soft_mat("IllumSrcConeR17", K.VIOLET, 2.2 * 0.4, 0.75 * 0.4))
        K.bounce_lights([B.FFM, B.PFM], energy=20.0)
    if variant == "title":
        _sequential_beam(M, n)
        # R16 row 3 (R15: "the turn between the middle and right bays happens on a thin rod"): the fold mirror G2
        # stands on a solid machined pedestal + mount cell, so the turn lands on a visible mirror block
        gm = K.MB()
        gm.box((B.G2.x, B.G2.y + 0.02, (1.05 + B.G2.z - 0.2) / 2), (0.3, 0.34, B.G2.z - 0.2 - 1.05))
        gm.box((B.G2.x, B.G2.y + 0.02, B.G2.z - 0.17), (0.5, 0.5, 0.1))
        gm.box((B.G2.x, B.G2.y + 0.02, 1.08), (0.6, 0.6, 0.06))
        gm.cyl((B.G2.x, B.G2.y, B.G2.z - 0.08), 0.24, 0.1, seg=48)
        gm.obj("G2PedestalR16", M["alu"], bevel=0.01)
    if variant == "tour":                    # R14 (R13: "floating white dots; crossing beams mid-shot"): story order,
        mi = 6                               # one bright leg at a time; IF cone -> facets -> G2 -> mask -> PO1 (the V)
        pts, rad = B.beam_path(0, mi + 1)
        # R17 row 4 (R16: "at 55 % only pupil <-> field facet shows, reads as the wrong order"): the IF -> field
        # facet leg stays lit with the next leg, so the single path reads in story order (thin cores + landings)
        # R19 row 2 (R18: "入射光收成细锥（照明狭缝形状），落在掩模上形成一条亮弧形照明带，反射光从这条带出去"): legs
        # IF..G2 as before (beam_r19: landing -> landing, zero outside); the G2 -> mask leg closes onto the
        # illumination band (slit-shaped end across the plane of incidence) and the reflected leg leaves from
        # exactly that band toward PO1; the band itself is a bright arc on the mask face
        import beam_r19 as R19
        R19.END_LAND[0] = False              # G2's landing is added below with its true mirror normal
        BR.timed_path(pts[:5], rad[:5], [(0.0, 0.66), (0.45, 0.72), (0.66, 0.76), (0.72, 0.8)], n, "TourLeg")
        R19.END_LAND[0] = True
        band = ((0, 1, 0), 0.15, (1, 0, 0), 0.014)
        for j, (a_, b_, ra_) in enumerate(((pts[4], pts[5], rad[4]), (pts[6], pts[5], rad[6]))):
            os_, ms_ = R19.cone(a_, b_, ra_, 0.01, f"TourLegBand{j}", end=band, seg=64)
            f_band = R19.key_vis(os_, ms_, n, 0.76, None)
        R19._land_timed(pts[4], K.mirror_normal(pts[3], pts[4], pts[5]), "TourLegLandG2", f_band)
        arc, arch = K.MB(), K.MB()
        apts = [Vector((pts[5].x + 1.1 * (y_ * y_), pts[5].y + y_, pts[5].z - 0.006)) for y_ in
                [-0.15 + 0.3 * k / 16 for k in range(17)]]
        for a_, b_ in zip(apts, apts[1:]):          # flat ribbon on the mask face (not a tube / line)
            mid_, d_ = (a_ + b_) / 2, (b_ - a_)
            ang_ = math.atan2(d_.x, d_.y)
            arc.box(mid_, (0.026, d_.length * 1.08, 0.0012), rot=(0, 0, -ang_))
            arch.box(mid_ + Vector((0, 0, 0.0012)), (0.06, d_.length * 1.08, 0.001), rot=(0, 0, -ang_))
        bo1 = arc.obj("MaskBandR19", K.emit_mat("MaskBandHotR19", (0.8, 0.68, 1.0), 9.0))
        bo2 = arch.obj("MaskBandGlowR19", K.emit_mat("MaskBandGlowR19", (0.62, 0.48, 1.0), 2.5, halo=0.8))
        for o_ in (bo1, bo2):
            o_.visible_shadow = False
            o_.hide_render = True
            o_.keyframe_insert("hide_render", frame=1)
            o_.keyframe_insert("hide_render", frame=f_band + 2)
            o_.hide_render = False
            o_.keyframe_insert("hide_render", frame=f_band + 3)
        BR.SPOTS[:] = []
        _cut_faces("R2_housing", (0.42, 0.78), (-1.3, 1.3), (2.0, 4.32))   # R14: the PO wall plate under the mask
        # R18 (R17: "frame 3: a dark post hides the right half of the mask"): the 'post' is the edge of the PO
        # module's top plate (z 4.03-4.08, x 0.6..3) seen from below - that plate is cut so the mask shows whole
        _cut_faces("R2_housing", (0.5, 3.2), (-1.4, 1.4), (3.99, 4.11))
        hw = bpy.data.objects.get("R8Kit2_hose_w")   # R18 (R17: "a glowing bent pipe bottom right reads as a
        if hw is not None:                            # second light path"): the white hose under the mask goes dark
            hw.data.materials.clear()
            hw.data.materials.append(M["cable_g"])

        mb = K.MB()
        K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
        cm = BR.soft_mat("TourSrcCone", K.VIOLET, 2.2, 0.75)
        mb.obj("TourSrcCone", cm)
        BR._anim_mul(cm, [(1, 1.0), (round(n * 0.45), 1.0), (round(n * 0.45) + 6, 0.14)])
        import beam_r17 as R17
        R17.haze(["TourSrcCone"], 0.4)       # R17 row 4: collector + IF read through the source cone
        pg = bpy.data.objects.get("PlasmaGlow")   # (with the haze lowered its glossy reflection read as a white dot)
        if pg is not None:
            pg.visible_glossy = False
        # R18 row 2 (R17: "bottom right an extra light column + a glowing bent pipe, reads as a second path"): the
        # dim PO-onward beam is deleted - one path, the V at the mask is its last lit segment
        K.bounce_lights([B.FFM, B.PFM, B.G1, B.G2, B.MASK + Vector((0, -0.1, -0.15))], energy=20.0)
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.25 if not studio else 0.5
    sc["vignette"] = 0.35
    sc["film_grain"] = 0.12
    cam, tgt = K.camera("CamR2", lens=35, fstop=None)
    f1 = n
    if variant == "title":
        cam.data.lens = 32
        if _R20[0] == "A0_10":               # R20 row 2 (k2A, R19: "给机架加棚拍轮廓光"): cool rim from behind / above
            K.area("RimCoolR20", (-3.0, 4.5, 6.5), (-3.0, 0, 2.8), 3.0, 5200, (0.72, 0.83, 1.0), size_y=14.0)
        K.suit_person("Eng1", (-3.0, -2.3, 0), 1.78, "stand", facing=10)
        K.suit_person("Eng2", (-2.35, -2.5, 0), 1.7, "work", facing=-20)
        _studio_skins(M)
        K.key_path(cam, tgt, [(1, (-5.2, -15.6, 2.2), (-3.6, 0, 3.3)), (f1, (-0.9, -14.0, 2.5), (-2.3, 0, 3.4))],
                   interp="LINEAR")
    elif variant == "illum":
        cam.data.lens = 28
        cam.data.lens = 24
        # R10: open wide on the whole illuminator (IF in, mask out), then push in on the field facet mirror
        # R15 (R14: "facets only 8-10 % of frame at 25 / 55 %"): the push-in starts closer and reaches the facet
        # mirror by mid-shot (>= 1/4 frame at 55 %), then drifts across it
        K.key_path(cam, tgt, [(1, (-2.5, -5.6, 3.35), (-2.05, 0.3, 3.4)),
                              (round(f1 * 0.5), (-2.55, -2.55, 3.75), (-2.15, 0.15, 3.8)),
                              (f1, (-1.7, -1.3, 3.98), (-2.14, 0.12, 3.84))])      # R16 row 4: facets >= 1/4 at 85 %
        if _R20[0] == "B5_01":               # R20 row 1 (R19: "开头 25 % 帧给一个更远的机位，露出 IF → 照明 → 掩模的走向，
            cam.animation_data_clear()
            tgt.animation_data_clear()
            # 再推近"): ~25 % wider at 25 % (IF tip, field facets, pupil facets all in frame), then a push-in that
            # keeps the IF tip and the pupil facet mirror in frame (every lit segment has both ends on screen)
            K.key_path(cam, tgt, [(1, (-2.95, -5.7, 3.05), (-3.0, 0.15, 2.82)),
                                  (round(f1 * 0.25), (-2.85, -4.9, 3.08), (-3.0, 0.15, 2.86)),
                                  (f1, (-2.55, -3.3, 3.15), (-2.95, 0.15, 2.98))])
            cam.data.dof.aperture_fstop = 11.0
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 5.6
        cam.data.dof.focus_object = tgt
    elif variant == "tour":
        cam.data.lens = 30
        K.key_path(cam, tgt, [(1, (-8.4, -4.4, 3.3), (-7.4, 0.0, 2.3)),
                              (round(f1 * 0.25), (-6.6, -4.2, 3.0), (-5.6, 0.1, 2.5)),
                              (round(f1 * 0.55), (-3.4, -4.6, 3.3), (-2.5, 0.2, 3.0)),
                              # R13: under the mask, looking up across the beam plane: the mask face fills
                              # ~1/3 of the frame, the incident cone comes in from lower left, the reflected
                              # cone leaves lower right
                              # R14 (R13: "mask ~1/6; reflected cone cut by the housing wall"): closer, lower-left
                              # R16 row 4 (R15: "mask 8-10 % and cropped by the top edge"): pulled back and
                              # tilted up - the whole patterned mask sits in frame, >= 1/4
                              (round(f1 * 0.85), (0.51, -0.8, 3.6), (0.57, 0.3, 4.3)),
                              (f1, (0.53, -0.78, 3.61), (0.58, 0.3, 4.31))])
        tl = K.MB()                              # short dashed normal under the mask: the angle reads against it
        for k in range(6):
            tl.cyl((B.MASK.x, B.MASK.y, B.MASK.z - 0.12 - k * 0.12), 0.004, 0.06, seg=8)
        tl.obj("MaskNormal", K.emit_mat("MaskNormalR13", (0.85, 0.9, 1.0), 3.0))
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
        # R12 (R11: "mirror face hidden"): closer, more on the dish axis; collector face >= 1/4 frame, IF at the edge
        # R13 (R12 H2: "three frames barely move; IF out of frame; cone not read"): a real 1.6 m dolly-in + truck-left
        # on a curve, focus pulling from the IF / cone mouth onto the dish. Collector, plasma, the converging cone
        # and IF stay in frame the whole move; the dish grows from ~1/4 to ~0.4 of frame height.
        cam.data.lens = 24
        cam.data.dof.aperture_fstop = 5.6
        # R15 (R14: "collector face 6-8 % of frame"): same dolly + truck; first half ~15 % closer onto the dish
        K.key_path(cam, tgt, [(1, (-4.15, -4.35, 3.45), (-6.2, 0.0, 2.42)),
                              (round(f1 * 0.5), (-5.2, -3.1, 3.05), (-6.7, 0.0, 2.41)),
                              (f1, (-6.05, -2.55, 2.9), (-6.95, 0.0, 2.42))])   # R16 row 4: collector >= 1/4
        if _R20[0] == "B3_02":               # R20 row 2 (R19: "「中间焦点 IF」标注在后两帧消失了，应该保留到锥尖…最后一帧
            cam.animation_data_clear()       # 要把『巨大的镜子』交代给观众，可以拉远，让镜子占画面 ≥ 1/3"): the dolly
            tgt.animation_data_clear()       # ends pulled back so the IF tip stays in frame; dish ~0.4 of frame height
            K.key_path(cam, tgt, [(1, (-4.15, -4.35, 3.45), (-6.2, 0.0, 2.42)),
                                  (round(f1 * 0.5), (-4.6, -3.75, 3.2), (-6.25, 0.0, 2.42)),
                                  (f1, (-5.0, -3.0, 2.95), (-6.3, 0.0, 2.42))])
            cam.data.dof.aperture_fstop = 11.0   # the out-of-focus foreground vessel smeared into a white "fog"
        K.area("DishGlint", (-5.6, 2.9, 3.9), B.COLL, 2.2, 520, (0.95, 0.96, 1.0))
        K.area("DishKey", (-5.0, -2.2, 3.6), B.COLL, 1.6, 260, (1.0, 0.98, 0.95))
        # grazing studio strip skimming the coated face from above-front: one long highlight band across the dish
        K.area("DishGraze", (-7.35, -0.9, 3.55), B.COLL + Vector((0.1, 0, 0.1)), 0.7, 520, (1.0, 0.99, 0.97), size_y=2.4)
        K.area("DishGrazeLo", (-7.5, 1.1, 1.2), B.COLL, 0.6, 200, (0.92, 0.95, 1.0), size_y=1.6)
        # the reflected cone, drawn as 16 bright edge rays from the dish rim to IF (the volume alone read as a tube)
        rays = K.MB()
        Rr, ff = 0.62, 0.42
        for a in range(6):                   # R14: six faint helper rays only (16 bright ones read as a birdcage)
            ang = 2 * math.pi * (a + 0.5) / 6
            rim = Vector((B.COLL.x + Rr * Rr / (4 * ff), Rr * math.cos(ang), B.COLL.z + Rr * math.sin(ang)))
            m_, l_ = K._orient(rim, B.IF)
            rays.cyl_m(m_, 0.0022, l_, seg=6, r2=0.001)
        rays.bm.free()                       # R18 row 2 (R17: "6-8 thin lines = a wire cage"): helper rays gone
        # R18 row 2: the reflected light is ONE solid translucent volumetric cone from the whole coated face
        # (rim plane, aperture 0.58) converging onto the IF (beam_r18; soft shell, interior glow). The R16/R17
        # surface cone R2_cone is removed so the two do not stack.
        ro = bpy.data.objects.get("R2_cone")
        if ro is not None:
            bpy.data.objects.remove(ro)
        import beam_r19 as R18
        cc_ = R18.cone(Vector((B.COLL.x + Rr * Rr / (4 * ff) + 0.01, 0, B.COLL.z)), B.IF, 0.58, 0.012,
                       "CollectConeR18", k=0.55, seg=64)
        if _R20[0] == "B3_02":               # R20 row 2 (R19: "85 % 帧白雾太重…把雾密度降一半"): the only volume is
            R18.key_vis(cc_[0], cc_[1], n, 0.0, 0.62, ramp=12, dim=0.5)    # this cone; half by the 85 % frame
        K.clean_cycles(sc, indirect=1.0)                 # R13: fireflies on the cone mouth / posts
        try:
            sc.cycles.blur_glossy = 2.0
            sc.cycles.sample_clamp_direct = 8.0
        except AttributeError:
            pass
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



def _cut_faces(obj_name, xr, yr, zr):
    """R14: delete the faces of one built mesh whose centres fall inside a world box (C_03: the housing plate
    under the mask that cut the reflected cone)."""
    import bmesh
    ob = bpy.data.objects.get(obj_name)
    if ob is None:
        return 0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    dead = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if xr[0] < c.x < xr[1] and yr[0] < c.y < yr[1] and zr[0] < c.z < zr[1]:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    return len(dead)

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
    # R17 row 4 (R16: "mid bay has an upper and a lower leg that cross; more than one path"): ONE left-to-right
    # path - IF -> field facet -> fold G2 -> mask -> PO -> wafer (the pupil-facet / G1 detour that crossed the
    # IF leg is deleted); thin cores + a landing highlight on every mirror, each appearing with its segment
    import beam_r12 as BR
    import beam_r17 as R17
    full, _r = B.beam_path()
    main = [B.IF, B.FFM, B.G2, B.MASK]
    segs = [(None, 1), (main, 0.3), ([B.MASK] + full[6:], 0.6)]
    for i, (rng, start) in enumerate(segs):
        mb = K.MB()
        lands = []
        if rng is None:
            K.cone_beam(mb, B.IF, Vector((B.COLL.x + 0.28, 0, B.COLL.z)), 0.62)
            mat = M["cone"]
        else:
            # R18 row 2 (R17: "light turns in mid-air on a thin post"; thin lines): volumetric cones from the IF
            # onward, each end as wide as the mirror it leaves / lands on (IF focus 0.03 -> field facets 0.24 ->
            # fold G2 0.13 -> mask 0.07 -> PO mirrors -> wafer point); every fold sits on a mounted mirror with
            # its R17 landing highlight
            import beam_r19 as R18
            pts = [Vector(p) for p in rng]
            ap = ([0.03, 0.24, 0.13, 0.07] if i == 1 else [0.07] + [r_ * 0.6 for r_ in B.PO_R] + [0.02])
            if _R21[0] == "A0_10" and i == 2:   # R21 row 3 (R20 smoke: 4 PO cones overlapped into a diagonal mass):
                pts = [pts[0], pts[1], pts[2], pts[-1]]   # mask -> PO1 -> PO2 -> wafer = 3 straight cones in three
                ap = [ap[0], ap[1], ap[2], ap[-1]]        # clearly different directions (right / down-left / down-right)
            for j, (a, b) in enumerate(zip(pts, pts[1:])):
                # R19: k 1.2 -> 1.6 only compensates the removed outer halo shell (beam_r19: zero outside the
                # cone) so the title-scale path keeps its R18 brightness; widths unchanged
                nrm_ = {}
                if _R20[0] == "A0_10":       # R20 row 2: each cone's end caps lie on the two mirror faces it joins
                    ex_ = ([B.G2] if i == 2 else [None]) + pts + ([Vector(full[6])] if i == 1 else [None])
                    nrm_ = {k_: (None if ex_[q_ - 1] is None or ex_[q_ + 1] is None
                                 else K.mirror_normal(ex_[q_ - 1], ex_[q_], ex_[q_ + 1]))
                            for k_, q_ in (("na", j + 1), ("nb", j + 2))}
                os_, ms_ = R18.cone(a, b, ap[j], ap[j + 1], f"TitleCone{i}_{j}", k=1.6, **nrm_)
                R18.key_vis(os_, ms_, n, start, None, ramp=10)
            ext = pts + ([Vector(full[6])] if i == 1 else [])      # segment 1 ends on the mask (bounce -> PO1)
            for j in range(1, len(ext) - 1):
                lands += R17._land_objs(ext[j], K.mirror_normal(ext[j - 1], ext[j], ext[j + 1]), 1.0,
                                        f"TitleLand{i}_{j}")
            mat = R17.core_mat(f"EUVCore{i}", 7.0, 0.95)        # (mb stays empty: the cones are their own objects)
        ob = mb.obj(f"BeamSeg{i}", mat)
        if start == 1:
            R17.haze([ob.name], 0.5)                   # R17: lower source-cone haze, the collector reads
            continue
        f0 = max(2, round(n * start))
        for lo in lands:
            lo.hide_render = True
            lo.keyframe_insert("hide_render", frame=1)
            lo.keyframe_insert("hide_render", frame=f0 + 5)
            lo.hide_render = False
            lo.keyframe_insert("hide_render", frame=f0 + 6)
        f0 = max(2, round(n * start))
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=f0 - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
        mul = [nd for nd in mat.node_tree.nodes if nd.type == "MATH" and nd.operation == "MULTIPLY"]
        hi = [nd.inputs[1].default_value for nd in mul]
        for f, k in ((f0, 0.15), (f0 + 10, 1.0)):
            for nd, h_ in zip(mul, hi):
                nd.inputs[1].default_value = h_ * k
                nd.inputs[1].keyframe_insert("default_value", frame=f)


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
    K.beam_columns(col, [Vector((AX.x, 0, z5 + 0.01)), Vector((AX.x, 0, z6 - 0.01))], [r5 * 0.9, r6 * 0.84], seg=64, waist=False)  # M5 -> M6
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
    # R13 (R12: "still a flat sheet box; M5 / M6 indistinct"): a thick cast housing around the open box - a heavy
    # base flange and roof flange with rounded edges, rounded corner columns, 5 external ribs per side wall and a
    # visible 9 cm shell section on the cut front edges
    cast.box((1.8, 0.05, 1.0), (2.75, 2.35, 0.16))                            # base flange
    cast.box((1.8, 0.05, 4.18), (2.75, 2.35, 0.14))                            # roof flange
    for x in (0.44, 3.16):
        for y in (-1.07, 1.17):
            cast.cyl((x, y, 2.59), 0.11, 3.06, seg=28)                         # rounded corner columns
        for k in range(5):                                                     # external ribs on the side walls
            y = -0.75 + k * 0.42
            cast.box((x + (-0.06 if x < 1 else 0.06), y, 2.59), (0.12, 0.06, 3.0))
    for x in (0.44, 3.16):                                                     # shell section at the cut front
        mbs["section"].box((x, -1.12, 2.59), (0.24, 0.012, 3.04))
    mbs["section"].box((1.8, -1.13, 1.0), (2.75, 0.012, 0.16))
    mbs["section"].box((1.8, -1.13, 4.18), (2.75, 0.012, 0.14))
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
            ob = mb.obj("PO_" + k, mats[k], bevel={"housing": 0.012, "stage": 0.02, "cast": 0.035}.get(k, 0.0))
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
    # R13: anchors on the M5 / M6 rings where the light lands (they turn with the table)
    ring_pts = {}
    for key, loc in (("m5r", (AX.x + r5 * 0.72, 0.0, z5 + 0.02)), ("m6r", (AX.x - r6 * 0.7, 0.0, z6 - 0.02))):
        e_ = bpy.data.objects.new("Anchor_" + key, None)
        sc.collection.objects.link(e_)
        e_.location = Vector(loc) - piv.location
        e_.parent = piv
        ring_pts[key] = e_
    K.anchors("B7_06", {**ring_pts, "po": Vector((1.8, 0.05, 2.5)), "eng": Vector((4.05, -1.7, 1.8)), "top": Vector((1.8, 0.05, 4.1)),
                        "m6": Vector((1.8, 0.05, 2.0)), "m5": Vector((1.8, 0.05, 1.36)), "entry": Vector((0.75, 0.3, 4.3))})
    return sc



def _po_barrels_r14(sc, M, n):
    """B7_06 (R14 rebuild; R13 review: "a solid violet column / vase between M5 and M6, no visible holes, the
    light comes out of the air, still a rectangular cabinet"). Root cause: the M5 -> M6 leg was drawn as a fat
    coaxial cone nested inside the other two, so the three legs merged into one solid body. Now:
      * housing = stacked barrels on a support frame (two cut-open lower barrels for the M5 / M6 bay, a closed
        upper barrel standing for M1-M4), the front ~140 deg sawn away, shell / flange sections light grey;
      * M6 (faces down) and M5 (faces up) are thick annular mirrors with open centre holes, neutral high-reflect
        coating, grazing studio highlights;
      * light path in one plane, three separate legs that never nest or cross: roof port (from the mask, via
        M1-M4) -> landing highlight on the M5 ring -> landing highlight on the M6 ring -> a converging cone
        through the M5 centre hole -> one bright point on the wafer below.
    Local frame: optical axis at x = y = 0 (the turntable pivot)."""
    import beam_r12 as BR
    import hero_kit_r10 as HK
    import hero_kit_r11 as H11
    import hero_kit_r12 as HK12
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    K.area("Key", (-4.5, -6.5, 6.5), (0, 0, 2.3), 6, 2200, (1.0, 0.98, 0.95))
    K.area("Fill", (6, -6, 3), (0, 0, 2), 6, 600, (0.9, 0.95, 1.0))
    K.area("RimL", (-4.5, 4.5, 5), (0, 0, 2.5), 3, 3500, (0.9, 0.93, 1.0))
    K.area("RimR", (4.5, 4.5, 5), (0, 0, 2.5), 3, 3500, (0.9, 0.93, 1.0))
    K.area("Softbox", (0, 0, 9), (0, 0, 0), 6, 2200, (1, 1, 1), size_y=3)
    HK.materials(M)
    M["coating"] = K.mat("MirrorHiR14", (0.86, 0.86, 0.88), metal=1.0, rough=0.05, coat=1.0)   # neutral, no violet
    keys = ("shell", "flange", "bolt", "section", "frame", "steel", "anod", "stage", "paint", "beam", "chuck")
    mb = {k: K.MB() for k in keys}
    HP = HK.new_parts()
    A0, A1 = -20.0, 200.0                     # kept wall: everything except the front 140 deg (centred on -Y)
    z_base, z_mid, z_ceil, z_top = 1.0, 2.15, 3.3, 4.3
    z6, z5, zw = 2.75, 1.62, 1.185
    r6, h6c, r5, h5c = 0.46, 0.13, 0.42, 0.145

    def cut_ring(z0, z1, ri, ro, key="shell", sec=True):
        L = z1 - z0
        mb[key].shell((0, 0, (z0 + z1) / 2), ri, ro, L, A0, A1, seg=96)
        if sec:                               # light-grey section face on both sawn edges (wall thickness reads)
            for a in (A0, A1):
                d = -1 if a == A0 else 1
                ang = math.radians(a)
                rm = (ri + ro) / 2
                c_ = Vector((rm * math.cos(ang), rm * math.sin(ang), (z0 + z1) / 2))
                tang = Vector((-math.sin(ang), math.cos(ang), 0)) * d
                mb["section"].box(c_ + tang * 0.003, (ro - ri + 0.004, 0.004, L + 0.002), rot=(0, 0, ang))

    # ---- barrels + flanges (stacked, two diameters), base plate, support frame
    cut_ring(z_base, z_mid, 0.95, 1.04)
    cut_ring(z_mid, z_ceil, 0.9, 0.98)
    for z, ro in ((z_base + 0.04, 1.16), (z_mid, 1.12), (z_ceil - 0.04, 1.08)):
        cut_ring(z - 0.04, z + 0.04, 0.9, ro, key="flange")
        for k in range(28):                    # bolt circle on the kept part only
            a = A0 + 4 + (A1 - A0 - 8) * k / 27
            ang = math.radians(a)
            rb = ro - 0.05
            mb["bolt"].cyl((rb * math.cos(ang), rb * math.sin(ang), z + 0.05), 0.013, 0.025, seg=6)
    for k in range(9):                         # external ribs on the kept wall
        ang = math.radians(A0 + 12 + (A1 - A0 - 24) * k / 8)
        for z0, z1, r_ in ((z_base + 0.08, z_mid - 0.04, 1.04), (z_mid + 0.04, z_ceil - 0.08, 0.98)):
            c_ = Vector(((r_ + 0.04) * math.cos(ang), (r_ + 0.04) * math.sin(ang), (z0 + z1) / 2))
            mb["flange"].box(c_, (0.08, 0.04, z1 - z0), rot=(0, 0, ang))
    mb["paint"].cyl((0, 0, z_base - 0.04), 1.2, 0.08, seg=96)              # base plate
    mb["paint"].cyl((0, 0, z_ceil + 0.03), 0.98, 0.06, seg=96)             # bay ceiling (holds the roof port)
    mb["shell"].cyl((0, 0, (z_ceil + z_top) / 2 + 0.03), 0.72, z_top - z_ceil - 0.06, seg=96)   # closed upper barrel (M1-M4)
    for z in (z_ceil + 0.08, z_top - 0.02):
        mb["flange"].ring((0, 0, z), 0.82, 0.7, 0.07, seg=96)
        mb["bolt"].bolts((0, 0, z + 0.04), 0.77, 24, 0.012, 0.025)
    for k in range(12):                        # upper barrel ribs
        ang = 2 * math.pi * k / 12
        mb["flange"].box((0.74 * math.cos(ang), 0.74 * math.sin(ang), (z_ceil + z_top) / 2), (0.05, 0.05, 0.85),
                         rot=(0, 0, ang))
    mb["paint"].cyl((0, 0, z_top + 0.04), 0.74, 0.06, seg=96)
    for k in range(4):                         # lifting lugs on the roof
        ang = math.radians(45 + 90 * k)
        mb["steel"].ring((0.55 * math.cos(ang), 0.55 * math.sin(ang), z_top + 0.15), 0.08, 0.045, 0.035,
                         rot=(math.radians(90), 0, ang))
    for ang_d in (45, 135, 225, 315):          # support frame: four square legs + back half-rings
        ang = math.radians(ang_d)
        p_ = (1.3 * math.cos(ang), 1.3 * math.sin(ang))
        mb["frame"].box((p_[0], p_[1], 2.15), (0.1, 0.1, 2.5))
        mb["frame"].box((p_[0] * 0.92, p_[1] * 0.92, z_base + 0.02), (0.36, 0.12, 0.06), rot=(0, 0, ang))
        mb["frame"].box((p_[0] * 0.88, p_[1] * 0.88, z_ceil), (0.3, 0.1, 0.06), rot=(0, 0, ang))
        mb["anod"].cyl((p_[0], p_[1], 0.98), 0.1, 0.1, seg=24)
    for z in (1.55, 2.85):
        mb["frame"].shell((0, 0, z), 1.25, 1.35, 0.06, 20, 160, seg=48)
    # ---- roof port: from the mask (through M1-M4 in the upper barrel) into the M5 / M6 bay
    port = Vector((0.74, 0.0, z_ceil))
    mb["flange"].ring((port.x, 0, z_ceil - 0.02), 0.1, 0.06, 0.06, seg=40)
    mb["bolt"].bolts((port.x, 0, z_ceil - 0.055), 0.085, 8, 0.008, 0.012)
    mb["flange"].ring((0.42, 0, z_top + 0.08), 0.11, 0.065, 0.06, seg=40)    # roof port of the upper barrel
    # ---- M6 (faces down) and M5 (faces up): thick annular mirrors, open centre holes
    HK.annular_mirror(HP, Vector((0, 0, z6)), (0, 0, -1), r6, h6c, spot_mb=None, thick=0.12)
    HK.annular_mirror(HP, Vector((0, 0, z5)), (0, 0, 1), r5, h5c, spot_mb=None, thick=0.12)
    HK.hexapod(HP, Vector((0, 0, z_ceil - 0.02)), Vector((0, 0, z6 + 0.2)), 0.3, 0.28)          # M6 hexapod from the ceiling
    for z in (z6, z5):                          # spider arms tie the mirror cells to the back wall
        for a in (60, 120):
            ang = math.radians(a)
            mb["anod"].box((0.7 * math.cos(ang), 0.7 * math.sin(ang), z + (0.1 if z == z6 else -0.1)), (0.52, 0.06, 0.06),
                           rot=(0, 0, ang))
    for z in (1.95, 2.48):                      # metrology rings with sensor heads (back half only)
        mb["anod"].shell((0, 0, z), 0.8, 0.86, 0.05, 15, 165, seg=64)
        for a in (40, 90, 140):
            d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            HP["brushed"].box(d * 0.78 + Vector((0, 0, z + 0.06)), (0.09, 0.09, 0.07))
            HK._cyl(HP["glass"], d * 0.73 + Vector((0, 0, z + 0.06)), -d, 0.022, 0.008, seg=16)
    for a in (35, 75, 150):                     # coolant bundles up the inner back wall
        ang = math.radians(a)
        p0 = Vector((0.86 * math.cos(ang), 0.86 * math.sin(ang), z_base + 0.1))
        HK.cooling_bundle(HP, [p0, p0 + Vector((0, 0, 2.05))], k=3, r=0.012, clamp_every=0.3,
                          up=(math.cos(ang), math.sin(ang), 0), block=False)
    for a, z in ((-12, 2.7), (192, 1.6), (192, 2.75)):                     # CF viewports on the outer side walls
        ang = math.radians(a)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        HK.flange_viewport(HP, d * 1.06 + Vector((0, 0, z)), d, 0.07, nipple=0.1)
    HK._turbo(HP, Vector((1.12 * math.cos(math.radians(170)), 1.12 * math.sin(math.radians(170)), 2.05)),
              (math.cos(math.radians(170)), math.sin(math.radians(170)), 0), 0.11)
    for a in (-8, 188):                                                       # harnesses down the outside
        ang = math.radians(a)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        HK.cable_harness(HP, [d * 1.1 + Vector((0, 0, 3.25)), d * 1.16 + Vector((0, 0, 2.2)), d * 1.12 + Vector((0, 0, 1.05))],
                         n=5, r=0.008)
    # ---- wafer stage under M5: chuck + dark polished Si wafer with dies, interferometer heads
    mb["chuck"].cyl((0, 0, zw - 0.06), 0.36, 0.1, seg=64)
    mb["chuck"].box((0, 0, zw - 0.13), (0.7, 0.7, 0.05))
    wf = K.MB()
    wf.cyl((0, 0, zw - 0.006), 0.3, 0.004, seg=128)
    for x, y, aim in ((0.55, 0.05, (-1, 0, 0)), (-0.05, 0.55, (0, -1, 0))):
        HK12.interferometer_head(HP, (x, y, z_base), aim, h=zw - 0.08 - z_base)
    # ---- the light: three separate soft legs (never nested, never crossing) + landing highlights
    p5 = Vector((0.30, 0, z5 + 0.012))
    p6 = Vector((-0.30, 0, z6 - 0.012))
    foc = Vector((0, 0, zw + 0.002))
    top_in = Vector((0.42, 0, z_top + 0.9))
    soft = BR.soft_mat("EUVLegR14", K.VIOLET, 2.4, 0.8, power=1.5)
    legs = [(top_in, Vector((0.42, 0, z_top + 0.08)), 0.04, 0.04),           # from the mask into the roof port
            (port + Vector((0, 0, -0.03)), p5, 0.045, 0.06),
            (p5, p6, 0.06, 0.1),
            (p6, foc, 0.11, 0.003)]
    for a, b, ra, rb in legs:
        m_, L_ = K._orient(a, b)
        mb["beam"].cyl_m(m_, ra, L_, seg=48, r2=rb)
    BR.SPOTS.append((p5, K.mirror_normal(port, p5, p6), 0.085))
    BR.SPOTS.append((p6, K.mirror_normal(p5, p6, foc), 0.13))
    fm = K.MB()
    fm.cyl(foc + Vector((0, 0, 0.002)), 0.022, 0.002, seg=32)
    fd = K.MB()
    fd.cyl(foc + Vector((0, 0, 0.003)), 0.07, 0.001, seg=32)
    K.bounce_lights([p5 + Vector((0, -0.15, 0.08)), p6 + Vector((0, -0.15, -0.08)), foc + Vector((0, -0.1, 0.06))], energy=5.0)
    # ---- objects, all on the turntable
    mats = {"shell": M["paint"], "flange": M["brushed"], "bolt": M["steel"], "section": M["section"], "frame": M["alu_dark"],
            "steel": M["steel"], "anod": M["anod"], "stage": M["paint_grey"], "paint": M["paint"], "beam": soft,
            "chuck": M["ceramic"]}
    piv = bpy.data.objects.new("Turntable", None)
    sc.collection.objects.link(piv)
    ped = K.MB()
    ped.cyl((0, 0, 0.45), 1.55, 0.9, seg=96)
    ped.obj("Pedestal", M["paint_grey"], bevel=0.02)
    rim = K.MB()
    rim.ring((0, 0, 0.92), 1.58, 1.45, 0.04, seg=96)
    rim.obj("PedRim", M["steel"])
    for k, m_ in mb.items():
        if len(m_.bm.verts):
            ob = m_.obj("PO14_" + k, mats[k], bevel={"paint": 0.01, "frame": 0.006, "chuck": 0.006}.get(k, 0.0))
            ob.parent = piv
        else:
            m_.bm.free()
    ob = wf.obj("PO14_wafer", _wafer_mat_r14(pitch=0.05, street=0.07))
    ob.parent = piv

    ob = fm.obj("PO14_focus", K.emit_mat("WaferFocusR14", (0.9, 0.85, 1.0), 30.0))
    ob.parent = piv
    ob = fd.obj("PO14_focusHalo", K.emit_mat("WaferFocusHaloR14", K.VIOLET, 3.0, halo=0.8))
    ob.parent = piv
    sp = BR.flush(name="PO14Spots")
    if sp is not None:
        sp.parent = piv
    HK.finish(HP, M, "PO14K", parent=piv)
    for ob in B.flush_kits(M, tag="PO14Kit"):
        ob.parent = piv
    piv.rotation_euler = (0, 0, math.radians(-16))           # turntable swing; the cut side always faces the lens
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(14))
    piv.keyframe_insert("rotation_euler", frame=n)
    K.suit_person("Eng1", (1.55, -1.95, 0), 1.78, "stand", facing=-30)
    K.area("InnerKey", (-0.9, -3.2, 3.4), (0, 0.2, 2.2), 1.6, 420, (1.0, 0.98, 0.95))
    K.area("InnerFill", (1.6, -2.6, 1.4), (0, 0.2, 1.6), 1.2, 260, (0.9, 0.94, 1.0))
    K.area("GrazeM5", (-1.6, -0.8, 1.75), (0, 0, z5), 0.8, 160, (1.0, 0.99, 0.97), size_y=1.6)   # grazing strips
    K.area("GrazeM6", (1.6, -0.8, 2.62), (0, 0, z6), 0.8, 160, (1.0, 0.99, 0.97), size_y=1.6)
    # camera cranes down: high first (looking into the M5 ring and its hole), low last (up at M6's underside / hole)
    cam, tgt = K.camera("CamR2", lens=30)
    K.key_path(cam, tgt, [(1, (0.45, -4.6, 3.55), (0.05, 0, 2.05)), (round(n * 0.55), (0.6, -4.7, 2.75), (0.05, 0, 2.2)),
                          (n, (0.75, -4.5, 1.75), (0.05, 0, 2.4))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.5
    sc["vignette"] = 0.3
    sc.camera = cam
    pts = {}
    for key, loc in (("m5r", p5), ("m6r", p6), ("wfoc", foc), ("entry", port), ("m5h", Vector((0, 0, z5))),
                     ("m6h", Vector((0, 0, z6)))):
        e_ = bpy.data.objects.new("Anchor_" + key, None)
        sc.collection.objects.link(e_)
        e_.location = loc
        e_.parent = piv
        pts[key] = e_
    K.anchors("B7_06", {**pts, "eng": Vector((1.55, -1.95, 1.8)), "top": Vector((0, 0, z_top))})
    return sc


def _po_barrels_r15(sc, M, n):
    """B7_06 (R15 rebuild; R15_ROOT_CAUSE row 1. R14 review: "only ~5 part types in the barrel (H13, A 72); M5 / M6
    read as chrome donuts (torus); the incoming leg and the M6 -> wafer cone cross as an X above M5; the person is
    half out of frame"). Not repeating R14's torus rings or R13's cone radius:
      * M5 / M6 = thick disc aspheric blanks (hero_kit_r15.disc_mirror): polished slightly concave optical face
        (mirror_r15.ml_mirror), 45 deg chamfer, fine-ground side / back / bore (mirror_r15.ground_edge), each
        tilted 12 deg toward the lens so the face reads as a face, held by a 3-point flexure mount in a machined
        cell on a hexapod, with capacitive edge sensors;
      * barrel filled to k2B density in three depth layers: inner ribs + ring stiffeners and harness / coolant
        runs on the back wall (far), metrology rings, sensor heads, mirror cells, hexapods, coolant loops to each
        cell (middle), frame legs, ion pump / gate valve / CF viewports / turbo on the outer barrel (near);
      * the incoming leg drops from a roof port OUTSIDE the M6 cell ring onto the outer M5 face; legs form one
        zig-zag (in -> M5 -> M6 -> through the M5 hole -> wafer point) that never overlaps on screen;
      * the camera cranes less (z 3.2 -> 2.3) on a 26 mm lens so a full-figure engineer stands beside the machine.
    Local frame: optical axis at x = y = 0 (the turntable pivot)."""
    import beam_r12 as BR
    import hero_kit_r10 as HK
    import hero_kit_r12 as HK12
    import hero_kit_r15 as H15
    import mirror_r15 as MR
    import random
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    K.area("Key", (-4.5, -6.5, 6.5), (0, 0, 2.3), 6, 2200, (1.0, 0.98, 0.95))
    K.area("Fill", (6, -6, 3), (0, 0, 2), 6, 600, (0.9, 0.95, 1.0))
    K.area("RimL", (-4.5, 4.5, 5), (0, 0, 2.5), 3, 3500, (0.9, 0.93, 1.0))
    K.area("RimR", (4.5, 4.5, 5), (0, 0, 2.5), 3, 3500, (0.9, 0.93, 1.0))
    K.area("Softbox", (0, 0, 9), (0, 0, 0), 6, 2200, (1, 1, 1), size_y=3)
    HK.materials(M)
    keys = ("shell", "flange", "bolt", "section", "frame", "steel", "anod", "stage", "paint", "beam", "chuck", "mface",
            "medge", "rib")
    mb = {k: K.MB() for k in keys}
    HP = HK.new_parts()
    rnd = random.Random(15)
    A0, A1 = -20.0, 200.0                     # kept wall: everything except the front 140 deg (centred on -Y)
    z_base, z_mid, z_ceil, z_top = 1.0, 2.15, 3.3, 4.3
    z6, z5, zw = 2.78, 1.64, 1.185
    r6, r5, hole, th = 0.5, 0.52, 0.16, 0.14
    tilt = math.radians(18)
    n5 = Vector((0, -math.sin(tilt), math.cos(tilt)))         # M5 faces up, turned toward the lens
    n6 = Vector((0, -math.sin(tilt), -math.cos(tilt)))        # M6 faces down, turned toward the lens

    def cut_ring(z0, z1, ri, ro, key="shell", sec=True):
        L = z1 - z0
        mb[key].shell((0, 0, (z0 + z1) / 2), ri, ro, L, A0, A1, seg=96)
        if sec:                               # light-grey section face on both sawn edges (wall thickness reads)
            for a in (A0, A1):
                d = -1 if a == A0 else 1
                ang = math.radians(a)
                rm = (ri + ro) / 2
                c_ = Vector((rm * math.cos(ang), rm * math.sin(ang), (z0 + z1) / 2))
                tang = Vector((-math.sin(ang), math.cos(ang), 0)) * d
                mb["section"].box(c_ + tang * 0.003, (ro - ri + 0.004, 0.004, L + 0.002), rot=(0, 0, ang))

    # ---- barrels + flanges, base plate, support frame (as R14)
    cut_ring(z_base, z_mid, 0.95, 1.04)
    cut_ring(z_mid, z_ceil, 0.9, 0.98)
    for z, ro in ((z_base + 0.04, 1.16), (z_mid, 1.12), (z_ceil - 0.04, 1.08)):
        cut_ring(z - 0.04, z + 0.04, 0.9, ro, key="flange")
        for k in range(28):
            a = A0 + 4 + (A1 - A0 - 8) * k / 27
            ang = math.radians(a)
            rb = ro - 0.05
            mb["bolt"].cyl((rb * math.cos(ang), rb * math.sin(ang), z + 0.05), 0.013, 0.025, seg=6)
    for k in range(9):
        ang = math.radians(A0 + 12 + (A1 - A0 - 24) * k / 8)
        for z0, z1, r_ in ((z_base + 0.08, z_mid - 0.04, 1.04), (z_mid + 0.04, z_ceil - 0.08, 0.98)):
            c_ = Vector(((r_ + 0.04) * math.cos(ang), (r_ + 0.04) * math.sin(ang), (z0 + z1) / 2))
            mb["flange"].box(c_, (0.08, 0.04, z1 - z0), rot=(0, 0, ang))
    # far layer: inner ribs (radial fins) + ring stiffeners on the inside of the kept wall
    for k in range(13):
        ang = math.radians(A0 + 8 + (A1 - A0 - 16) * k / 12)
        if abs(math.degrees(ang) - 90) < 9:   # no rib straight behind the optical axis (reads as a wire through it)
            continue
        for z0, z1, r_ in ((z_base + 0.06, z_mid - 0.06, 0.95), (z_mid + 0.06, z_ceil - 0.06, 0.9)):
            c_ = Vector(((r_ - 0.03) * math.cos(ang), (r_ - 0.03) * math.sin(ang), (z0 + z1) / 2))
            mb["rib"].box(c_, (0.06, 0.018, z1 - z0), rot=(0, 0, ang))
    for z, ri in ((1.32, 0.9), (1.86, 0.9), (2.42, 0.85), (3.02, 0.85)):
        mb["rib"].shell((0, 0, z), ri, ri + 0.06, 0.035, A0 + 4, A1 - 4, seg=72)
    mb["paint"].cyl((0, 0, z_base - 0.04), 1.2, 0.08, seg=96)
    mb["paint"].cyl((0, 0, z_ceil + 0.03), 0.98, 0.06, seg=96)
    mb["shell"].cyl((0, 0, (z_ceil + z_top) / 2 + 0.03), 0.72, z_top - z_ceil - 0.06, seg=96)
    for z in (z_ceil + 0.08, z_top - 0.02):
        mb["flange"].ring((0, 0, z), 0.82, 0.7, 0.07, seg=96)
        mb["bolt"].bolts((0, 0, z + 0.04), 0.77, 24, 0.012, 0.025)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        mb["flange"].box((0.74 * math.cos(ang), 0.74 * math.sin(ang), (z_ceil + z_top) / 2), (0.05, 0.05, 0.85),
                         rot=(0, 0, ang))
    mb["paint"].cyl((0, 0, z_top + 0.04), 0.74, 0.06, seg=96)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        mb["steel"].ring((0.55 * math.cos(ang), 0.55 * math.sin(ang), z_top + 0.15), 0.08, 0.045, 0.035,
                         rot=(math.radians(90), 0, ang))
    for ang_d in (45, 135, 225, 315):
        ang = math.radians(ang_d)
        p_ = (1.3 * math.cos(ang), 1.3 * math.sin(ang))
        mb["frame"].box((p_[0], p_[1], 2.15), (0.1, 0.1, 2.5))
        mb["frame"].box((p_[0] * 0.92, p_[1] * 0.92, z_base + 0.02), (0.36, 0.12, 0.06), rot=(0, 0, ang))
        mb["frame"].box((p_[0] * 0.88, p_[1] * 0.88, z_ceil), (0.3, 0.1, 0.06), rot=(0, 0, ang))
        mb["anod"].cyl((p_[0], p_[1], 0.98), 0.1, 0.1, seg=24)
    for z in (1.55, 2.85):
        mb["frame"].shell((0, 0, z), 1.25, 1.35, 0.06, 20, 160, seg=48)
    # ---- roof port (outside the M6 cell ring) + upper-barrel port
    port = Vector((0.86, 0.0, z_ceil))
    mb["flange"].ring((port.x, 0, z_ceil - 0.02), 0.09, 0.055, 0.06, seg=40)
    mb["bolt"].bolts((port.x, 0, z_ceil - 0.055), 0.075, 8, 0.008, 0.012)
    mb["flange"].ring((0.42, 0, z_top + 0.08), 0.11, 0.065, 0.06, seg=40)
    # ---- M6 / M5: thick disc aspheric blanks + 3-point mounts + hexapods + edge sensors
    c6 = Vector((0, 0, z6))
    c5 = Vector((0, 0, z5))
    H15.disc_mirror(mb["mface"], mb["medge"], c6, n6, r6, hole, th, sag=0.006)
    H15.disc_mirror(mb["mface"], mb["medge"], c5, n5, r5, hole, th, sag=0.006)
    for c_, n_, r_ in ((c6, n6, r6), (c5, n5, r5)):      # dark retaining ring on the chamfer: the face reads as a
        HK._ring(HP["alu_dark"], c_ - n_ * 0.012, n_, r_ + 0.006, r_ - 0.034, 0.03, seg=96)   # separate optical surface
    cell6, rc6 = H15.three_point_mount(HP, c6, n6, r6, th, phase=90)
    cell5, rc5 = H15.three_point_mount(HP, c5, n5, r5, th, phase=90)
    HK.hexapod(HP, Vector((0, 0, z_ceil - 0.02)), cell6 + Vector((0, 0, 0.04)), 0.34, 0.4)        # M6 from the ceiling
    HK.hexapod(HP, Vector((0, 0.05, z_base + 0.06)), cell5 - Vector((0, 0, 0.04)), 0.66, 0.5)   # M5 from the base
    H15.edge_sensors(HP, c6 - n6 * th * 0.5, n6, r6, k=3, phase=90)
    H15.edge_sensors(HP, c5 - n5 * th * 0.5, n5, r5, k=3, phase=90)
    for c_, z_ in ((cell6, z6 + 0.12), (cell5, z5 - 0.12)):          # cell spider arms to the back wall
        for a in (55, 125):
            ang = math.radians(a)
            mb["anod"].box((0.74 * math.cos(ang), 0.74 * math.sin(ang), z_), (0.36, 0.05, 0.05), rot=(0, 0, ang))
    for z in (1.95, 2.48):                                            # metrology rings with sensor heads (back)
        mb["anod"].shell((0, 0, z), 0.8, 0.86, 0.05, 15, 165, seg=64)
        for a in (40, 90, 140):
            d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            HP["brushed"].box(d * 0.78 + Vector((0, 0, z + 0.06)), (0.09, 0.09, 0.07))
            HK._cyl(HP["glass"], d * 0.73 + Vector((0, 0, z + 0.06)), -d, 0.022, 0.008, seg=16)
    for a in (35, 75, 110, 150):                                      # coolant bundles up the inner back wall
        ang = math.radians(a)
        p0 = Vector((0.82 * math.cos(ang), 0.82 * math.sin(ang), z_base + 0.1))
        HK.cooling_bundle(HP, [p0, p0 + Vector((0, 0, 2.05))], k=3, r=0.011, clamp_every=0.3,
                          up=(math.cos(ang), math.sin(ang), 0), block=False)
    for c_, rc, zz in ((cell6, rc6, z6 + 0.2), (cell5, rc5, z5 - 0.2)):  # coolant loops: cell -> back wall
        for s in (-1, 1):
            a = math.radians(90 + s * 28)
            d = Vector((math.cos(a), math.sin(a), 0))
            p0 = Vector((c_.x, c_.y, c_.z)) + d * rc * 0.98
            HP["hose_b" if s < 0 else "hose_w"].path([p0, p0 + d * 0.12 + Vector((0, 0, (zz - p0.z) * 0.5)),
                                                      d * 0.84 + Vector((0, 0, zz))], 0.014, seg=10)
    for a, z0, z1 in ((65, z_base + 0.15, z_ceil - 0.1), (118, z_base + 0.15, z_ceil - 0.1)):   # cable looms
        ang = math.radians(a)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        HK.cable_harness(HP, [d * 0.86 + Vector((0, 0, z1)), d * 0.84 + Vector((0, 0, (z0 + z1) / 2)),
                              d * 0.86 + Vector((0, 0, z0))], n=6, r=0.007)
    for a, z in ((-12, 2.7), (192, 1.6), (192, 2.75)):               # CF viewports on the outer side walls
        ang = math.radians(a)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        HK.flange_viewport(HP, d * 1.06 + Vector((0, 0, z)), d, 0.07, nipple=0.1)
    HK._turbo(HP, Vector((1.12 * math.cos(math.radians(170)), 1.12 * math.sin(math.radians(170)), 2.05)),
              (math.cos(math.radians(170)), math.sin(math.radians(170)), 0), 0.11)
    HK12.ion_pump(HP, -1.42, 2.72, 0.42, 0.5, 0.05, 1.0, rnd)         # near layer: named vacuum parts outside
    # R17 row 5 (R16: "a valve floats at the person's hand, reads as him holding a pipe"): gate valve removed
    for a in (-8, 188):
        ang = math.radians(a)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        HK.cable_harness(HP, [d * 1.1 + Vector((0, 0, 3.25)), d * 1.16 + Vector((0, 0, 2.2)), d * 1.12 + Vector((0, 0, 1.05))],
                         n=5, r=0.008)
    # R17 row 5 (R16 H13: "cage sparse - two mirrors, three rings and rods"): M1..M4 blanks seen from the back in
    # cells with actuators + flexures, coolant hoses and cable looms - >= 5 nameable part types inside the barrel
    import cut_kit_r17 as CK
    CK.po_fill(HP, mb, z_base, z_ceil, H15, HK)
    # ---- wafer stage under M5
    mb["chuck"].cyl((0, 0, zw - 0.06), 0.36, 0.1, seg=64)
    mb["chuck"].box((0, 0, zw - 0.13), (0.7, 0.7, 0.05))
    wf = K.MB()
    wf.cyl((0, 0, zw - 0.006), 0.3, 0.004, seg=128)
    for x, y, aim in ((0.55, 0.05, (-1, 0, 0)), (-0.05, 0.55, (0, -1, 0))):
        HK12.interferometer_head(HP, (x, y, z_base), aim, h=zw - 0.08 - z_base)
    # ---- the light: one zig-zag, legs only meet at their landing spots
    p5 = c5 + Vector((0.4, 0, 0)) + n5 * 0.004
    p5.z = z5 - 0.006 * (1 - (0.4 / (r5 - 0.03)) ** 2) + 0.004
    p6 = c6 + Vector((-0.38, 0, 0)) + n6 * 0.004
    p6.z = z6 + 0.006 * (1 - (0.38 / (r6 - 0.03)) ** 2) - 0.004
    foc = Vector((0, 0, zw + 0.002))
    top_in = Vector((0.42, 0, z_top + 0.9))
    import beam_r17 as R17
    soft = R17.core_mat("EUVLegR17", 7.0, 0.95)                    # R17 row 4: thin bright cores
    legs = [(top_in, Vector((0.42, 0, z_top + 0.08)), 0.035, 0.035),
            (port + Vector((0, 0, -0.03)), p5, 0.035, 0.05),
            (p5, p6, 0.05, 0.085),
            (p6, foc, 0.13, 0.003)]
    # R16 row 3 (R15: "M6 -> wafer is a constant thin tube, the gathering doesn't read"): R16 legs - the top leg
    # fades in from the mask side, the last leg is gathered from a wide M6 footprint through the M5 hole to one
    # bright wafer point (0.13 at M6 -> 0.037 at the M5 plane, inside the 0.16 hole)
    # R17 row 4: thin cores between the mirrors (+ a faint gathered sheath only on the last, focusing leg) and
    # bright landing highlights on M5 / M6 (beam_r17.flush)
    import beam_r16 as R16
    import beam_r17 as R17
    # R18 row 2 (R17: "3-4 thin lines cross inside the barrel = a wire birdcage; landing = floating white dot";
    # ask: only the current step, a converging cone that visibly passes M5's hole and closes to a point):
    # beam_r18 volumetric cones, ONE step on screen at a time (timed with the overlay's (1)(2)(3) at 0 / 42 / 70 %):
    #   (1) mask -> through the M6 hole -> M5 face, widening 0.04 -> 0.09
    #   (2) M5 -> M6 face, widening onto the big mirror 0.09 -> 0.21
    #   (3) M6 -> converging 0.22 -> 0.004 through the M5 hole (~0.06 at the M5 plane, inside the 0.16 hole) to one
    #       point ON the wafer; the wafer point appears only in step (3); M5 / M6 landing highlights only in their step
    import beam_r19 as R18
    cones18 = []
    if _R20[0] != "B7_06":
        for i, (a, b, ra, rb, t0, t1) in enumerate(((top_in, legs[0][1], 0.04, 0.045, 0.0, 0.46),
                                                    (legs[1][0], p5, 0.045, 0.09, 0.0, 0.46),
                                                    (p5, p6, 0.09, 0.21, 0.42, 0.74),
                                                    (p6, foc, 0.22, 0.004, 0.7, None))):
            os_, ms_ = R18.cone(a, b, ra, rb, f"POCone{i}", k=2.4 if i < 3 else 2.6, seg=64)   # white studio: denser
            R18.key_vis(os_, ms_, n, t0, t1, ramp=5)
            cones18 += os_
        for c_, n_, t0, t1, nm in ((p5, n5, 0.0, 0.46, "POLandM5"), (p6, n6, 0.42, 0.74, "POLandM6")):
            cones18 += R18._land_timed(c_, n_, nm, max(1, round(1 + (n - 1) * t0)), 5,
                                       f_off=round(1 + (n - 1) * t1) + 3)
    else:
        # R20 row 2 (R19: "M5→M6 的光画成了弯曲的 S 形半透明体…改成两段直的锥，拐点只在镜面上"): beam_r20 segments
        # only - top opening -> M5 face (ONE straight cone, no kink at the roof port), M5 -> M6, M6 -> through the
        # M5 hole -> wafer point; each end cap lies on its mirror plane. Every frame shows two straight cones that
        # meet on a mirror face: (1)+(2) turn on M5, (2)+(3) turn on M6. Widths = R19 apertures.
        roof = Vector((top_in.x, top_in.y, z_top + 0.08))        # the roof opening (in frame), lit tip below
        cones18 += R18.tip(roof, (p5 - roof).normalized(), "POTopTipR20", 1, scale=1.2)
        for i, (a, b, ra, rb, t0, t1, na_, nb_) in enumerate(((roof, p5, 0.04, 0.09, 0.0, 0.72, None, n5),
                                                              (p5, p6, 0.09, 0.21, 0.42, None, n5, n6),
                                                              (p6, foc, 0.22, 0.004, 0.7, None, n6, None))):
            os_, ms_ = R18.segment(a, b, ra, rb, f"POConeR20_{i}", k=2.4 if i < 2 else 2.6, na=na_, nb=nb_, seg=64)
            R18.key_vis(os_, ms_, n, t0, t1, ramp=5)
            cones18 += os_
        for c_, n_, t0, t1, nm in ((p5, n5, 0.0, 0.72, "POLandM5"), (p6, n6, 0.42, None, "POLandM6")):
            cones18 += R18._land_timed(c_, n_, nm, max(1, round(1 + (n - 1) * t0)), 5,
                                       f_off=None if t1 is None else round(1 + (n - 1) * t1) + 3)
    sheath = K.MB()
    sheath.bm.free()
    fm = K.MB()
    fm.cyl(foc + Vector((0, 0, 0.002)), 0.022, 0.002, seg=32)
    fd = K.MB()
    fd.cyl(foc + Vector((0, 0, 0.003)), 0.07, 0.001, seg=32)
    K.bounce_lights([p5 + Vector((0, -0.15, 0.08)), p6 + Vector((0, -0.15, -0.08)), foc + Vector((0, -0.1, 0.06))], energy=5.0)
    # ---- objects, all on the turntable
    mats = {"shell": M["paint"], "flange": M["brushed"], "bolt": M["steel"], "section": M["section"], "frame": M["alu_dark"],
            "steel": M["steel"], "anod": M["anod"], "stage": M["paint_grey"], "paint": M["paint"], "beam": soft,
            "chuck": M["ceramic"], "mface": MR.ml_mirror("M56FaceR15", rough=0.12, tone=0.74, coat=0.35),
            "medge": MR.ground_edge("M56EdgeR15", tone=0.24), "rib": M["paint_grey"]}
    piv = bpy.data.objects.new("Turntable", None)
    sc.collection.objects.link(piv)
    ped = K.MB()
    ped.cyl((0, 0, 0.45), 1.55, 0.9, seg=96)
    ped.obj("Pedestal", M["paint_grey"], bevel=0.02)
    rim = K.MB()
    rim.ring((0, 0, 0.92), 1.58, 1.45, 0.04, seg=96)
    rim.obj("PedRim", M["steel"])
    for k, m_ in mb.items():
        if len(m_.bm.verts):
            ob = m_.obj("PO15_" + k, mats[k], bevel={"paint": 0.01, "frame": 0.006, "chuck": 0.006, "rib": 0.004}.get(k, 0.0))
            ob.parent = piv
        else:
            m_.bm.free()
    for o_ in cones18:                       # R18: the cones + timed landings turn with the barrel
        o_.parent = piv
    R18.take()
    ob = wf.obj("PO15_wafer", _wafer_mat_r14(pitch=0.05, street=0.07))
    ob.parent = piv
    ob = fm.obj("PO15_focus", K.emit_mat("WaferFocusR14", (0.9, 0.85, 1.0), 30.0))
    ob.parent = piv
    ob2 = fd.obj("PO15_focusHalo", K.emit_mat("WaferFocusHaloR14", K.VIOLET, 3.0, halo=0.8))
    ob2.parent = piv
    f3 = round(1 + (n - 1) * 0.7) + 3            # R18: the wafer point lights only with step (3)'s cone
    for o_ in (ob, ob2):
        o_.hide_render = True
        o_.keyframe_insert("hide_render", frame=1)
        o_.keyframe_insert("hide_render", frame=f3 - 1)
        o_.hide_render = False
        o_.keyframe_insert("hide_render", frame=f3)
    sp = BR.flush(name="PO15Spots")
    if sp is not None:
        sp.parent = piv
    HK.finish(HP, M, "PO15K", parent=piv)
    for ob in B.flush_kits(M, tag="PO15Kit"):
        ob.parent = piv
    piv.rotation_euler = (0, 0, math.radians(-14))
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(12))
    piv.keyframe_insert("rotation_euler", frame=n)
    eng = (2.3, 1.3, 0)                    # full figure beside the machine (R14: half a head at the frame edge)
    K.suit_person("Eng1", eng, 1.78, "stand", facing=-25)
    K.area("EngRim", (3.6, 3.0, 2.6), (eng[0], eng[1], 1.0), 1.2, 900, (0.92, 0.95, 1.0))
    K.area("InnerKey", (-0.9, -3.2, 3.4), (0, 0.2, 2.2), 1.6, 420, (1.0, 0.98, 0.95))
    K.area("InnerFill", (1.6, -2.6, 1.4), (0, 0.2, 1.6), 1.2, 260, (0.9, 0.94, 1.0))
    K.area("GrazeM5", (-1.7, -1.4, 2.0), c5, 0.8, 220, (1.0, 0.99, 0.97), size_y=1.6)    # one grazing streak per face
    K.area("GrazeM6", (1.7, -1.4, 2.4), c6, 0.8, 220, (1.0, 0.99, 0.97), size_y=1.6)
    if _R20[0] == "B7_06":                    # R20 row 2 (k2A): cool rim on the white body against the grey backdrop
        K.area("RimCoolR20L", (-2.4, 2.6, 3.8), (0, 0, 2.2), 1.4, 1600, (0.72, 0.83, 1.0), size_y=3.0)
        K.area("RimCoolR20R", (2.6, 2.2, 3.4), (0, 0, 2.0), 1.4, 1300, (0.72, 0.83, 1.0), size_y=3.0)
    cam, tgt = K.camera("CamR2", lens=26)
    K.key_path(cam, tgt, [(1, (0.4, -4.3, 3.0), (0.1, 0, 2.15)), (round(n * 0.55), (0.55, -4.2, 2.7), (0.1, 0, 2.18)),
                          (n, (0.7, -4.05, 2.45), (0.1, 0, 2.2))])
    sc["hdri"] = "studio_small_09"
    sc["hdri_strength"] = 0.5
    sc["vignette"] = 0.3
    sc.camera = cam
    pts = {}
    for key, loc in (("m5r", p5), ("m6r", p6), ("wfoc", foc), ("entry", port), ("m5h", c5), ("m6h", c6)):
        e_ = bpy.data.objects.new("Anchor_" + key, None)
        sc.collection.objects.link(e_)
        e_.location = loc
        e_.parent = piv
        pts[key] = e_
    K.anchors("B7_06", {**pts, "eng": Vector((eng[0], eng[1], 1.85)), "eng_ft": Vector(eng), "top": Vector((0, 0, z_top))})
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


def _wafer_mat_r13(pitch=0.073, street=0.07):
    """R13 (R12: "wafer reads as black glass with white lines"): silver-grey polished silicon with a metallic sheen
    (roughness 0.12, catches the sheen card), thin scribe streets, and inside every die field a fine device pattern:
    two banks of dense line / space (x and y), a pad ring and a darker logic block. Object-space, pitch in metres."""
    m = K.mat("WaferSiR13", (0.52, 0.53, 0.57), metal=1.0, rough=0.12)
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
    fx = op("FRACT", op("DIVIDE", sp.outputs["X"], pitch))
    fy = op("FRACT", op("DIVIDE", sp.outputs["Y"], pitch * 1.25))
    streets = op("MAXIMUM", op("LESS_THAN", fx, street), op("LESS_THAN", fy, street))
    lines_x = op("LESS_THAN", op("FRACT", op("DIVIDE", sp.outputs["X"], pitch / 22)), 0.5)
    lines_y = op("LESS_THAN", op("FRACT", op("DIVIDE", sp.outputs["Y"], pitch / 20)), 0.5)
    left = op("LESS_THAN", fx, 0.55)
    top = op("LESS_THAN", fy, 0.5)
    pat = op("ADD", op("MULTIPLY", op("MULTIPLY", left, top), lines_x),
             op("MULTIPLY", op("MULTIPLY", op("SUBTRACT", 1.0, left), top), lines_y))
    logic = op("MULTIPLY", op("SUBTRACT", 1.0, top), op("MULTIPLY", op("GREATER_THAN", fx, 0.2), op("LESS_THAN", fx, 0.8)))
    v = op("ADD", op("MULTIPLY", pat, 0.5), op("MULTIPLY", logic, 0.25))      # 0 bare Si .. 0.75 dense pattern
    v = op("MAXIMUM", op("MULTIPLY", streets, 1.2), v)
    col = nt.nodes.new("ShaderNodeMix"); col.data_type = "RGBA"
    col.inputs["A"].default_value = (*K.lin((0.44, 0.45, 0.5)), 1)
    col.inputs["B"].default_value = (*K.lin((0.2, 0.21, 0.27)), 1)
    nt.links.new(op("MINIMUM", v, 1.0), col.inputs["Factor"])
    nt.links.new(col.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.1
    rr.inputs["To Max"].default_value = 0.32
    nt.links.new(v, rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    return m



def _wafer_mat_r14(pitch=0.073, street=0.07):
    """R14 (R13: "wafer reads as a semi-transparent glass disc with a grid"): dark-grey mirror silicon - same die
    / device pattern as R13 but a dark, low-roughness base so it reflects the room like polished Si (one grazing
    highlight band instead of a white haze over the whole disc)."""
    m = _wafer_mat_r13(pitch, street)
    m.name = "WaferSiR14"
    nt = m.node_tree
    mix = next(n for n in nt.nodes if n.type == "MIX" and n.data_type == "RGBA")
    mix.inputs["A"].default_value = (*K.lin((0.2, 0.205, 0.235)), 1)      # bare Si: dark mirror grey
    mix.inputs["B"].default_value = (*K.lin((0.09, 0.095, 0.125)), 1)     # dense device pattern: darker, bluish
    rr = next(n for n in nt.nodes if n.type == "MAP_RANGE")
    rr.inputs["To Min"].default_value = 0.04
    rr.inputs["To Max"].default_value = 0.2
    return m

def _darken(prefixes, k=0.35):
    """R13: dim the foreground stage materials (B8_03: "foreground grooved grid fights the wafer")."""
    done = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.startswith(prefixes):
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            if m.name not in done:
                d = m.copy()
                d.name = m.name + "_DK"
                bs = next((n for n in d.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if d.use_nodes else None
                if bs is not None and not bs.inputs["Base Color"].is_linked:
                    c = bs.inputs["Base Color"].default_value
                    bs.inputs["Base Color"].default_value = (c[0] * k, c[1] * k, c[2] * k, 1)
                done[m.name] = d
            slot.material = done[m.name]


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
    sl2 = K.MB()                                         # R13: lit field band around the slit
    sl2.box((0, WY, WZ + 0.003), (0.075, 0.3, 0.0015))
    sl2.obj("SlitField", K.emit_mat("SlitFieldR13", (0.72, 0.6, 1.0), 4.0, halo=0.45))
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
    yw0, zw = 0.56, 0.6                                       # R11: on the granite top behind the mover (in frame)
    yw = yw0 + WY
    for i in range(0, 9):
        x = a_w - i * U / 8
        h = 0.06 if i in (0, 8) else 0.025
        tk.box((x, yw, zw - h / 2), (0.004, 0.006, h))
    tk.box((0, yw, zw), (2 * a_w + 0.01, 0.006, 0.005))
    tk.obj("Rulers", ink)
    for i in range(9):
        _txt(f"RD{i}", str(i), (-a_r + i * U, yr, zr - 0.14), 0.1, ink)
    _txt("WD0", "0", (a_w, yw, zw + 0.1), 0.085, ink)
    _txt("WD1", "1", (-a_w, yw, zw + 0.1), 0.085, ink)
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
    pw.box((0, 0.5, 0.66), (0.012, 0.14, 0.012))
    pw.box((0, 0.565, 0.635), (0.012, 0.012, 0.05))
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


def _scan_r12(sc, M, n, shot):
    """B8_03 (R12 rebuild around the wafer stage). R11 review: "wafer ~1/12 frame; flat boxes on a checkerboard
    floor; the x4 label invites a 4x misread". Now:
      * main camera low and close on the wafer stage: a 0.84 m silicon wafer (die fields, polished, sheen card)
        fills >= 1/4 of the frame; the exposure beam converges onto its slit from the projection bay above;
      * floor = granite base carrying planar-motor coil windings (herringbone racetracks, not a magnet checker),
        interferometer heads on posts aimed at the mover's mirror bars, drag chain, umbilical;
      * the reticle stage is a picture-in-picture pass (camera CamR2M, shot B8_03M, same scene / same frames), so
        the mask running 8 units one way and the wafer 1 unit the other way read in one frame;
      * PO mirrors on hexapods + cooling bundles, bay walls on hero_kit_r12 (14 nameable types, no DIN rows).
    EXE (High-NA) data only: 5.4 deg (drawn enlarged, tagged), 8x reduction, 8 : 1 travel on the rulers."""
    import hero_kit_r10 as HK
    import hero_kit_r12 as HK12
    MZ, WZ = 2.75, 0.71
    th6 = math.tan(math.radians(15.0))
    WY = -0.85
    mask_c, waf_c = Vector((0, 0, MZ)), Vector((0, WY, WZ))
    g2 = Vector((-th6 * 1.33, 0, MZ - 1.33))
    src = Vector((-2.0, 0, 1.5))
    ff, pf = Vector((-1.38, 0, 1.24)), Vector((-0.78, 0, 1.76))
    m1 = Vector((th6 * (MZ - 1.75), 0, 1.75))
    m2, m3, m4 = Vector((1.78, 0, 2.12)), Vector((1.2, 0, 1.18)), Vector((0.58, -0.1, 1.5))
    pts = [src, ff, pf, g2, mask_c + Vector((0, 0, -0.012)), m1, m2, m3, m4, waf_c + Vector((0, 0, 0.004))]
    alu, anod, steel = M["alu"], M["anod"], M["steel"]
    M["section"] = K.mat("SectionCutR9", (0.46, 0.47, 0.5), rough=0.6)
    dk = K.mat("WallDark", (0.05, 0.055, 0.065), metal=0.5, rough=0.5)
    U = 0.2
    a_r, a_w = 4 * U, U / 2

    # ---- reticle stage (as R5-R11): bridge, rails, magnet track fixed; carriage, coils, mask moving
    fx = {k: K.MB() for k in ("bridge", "rail", "bolt", "magnet", "led")}
    fx["bridge"].box((0.2, 0.15, MZ + 0.42), (5.6, 1.0, 0.22))
    for y in (-0.32, 0.32):
        fx["rail"].box((0.2, y, MZ + 0.28), (5.2, 0.07, 0.05))
        for k in range(26):
            fx["bolt"].cyl((0.2 - 2.5 + k * 0.2, y, MZ + 0.31), 0.01, 0.02, seg=6)
    for k in range(52):
        fx["magnet"].box((0.2 - 2.55 + k * 0.1, 0.0, MZ + 0.3), (0.085, 0.3, 0.025))
    fx["led"].box((0.2, -0.351, MZ + 0.45), (5.4, 0.006, 0.012))
    for k, m_ in (("bridge", anod), ("rail", M["alu_dark"]), ("bolt", steel), ("magnet", K.mat("Magnet", (0.25, 0.26, 0.3),
                  metal=1.0, rough=0.3)), ("led", M["led_c"])):
        fx[k].obj("RBridge_" + k, m_, bevel=0.01 if k == "bridge" else 0.0)
    rp = {k: K.MB() for k in ("car", "bolt", "cable")}
    rp["car"].box((0, 0, MZ + 0.17), (1.3, 0.8, 0.16))
    rp["car"].box((-0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
    rp["car"].box((0.72, 0, MZ + 0.2), (0.14, 0.7, 0.12))
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
    slit = K.MB()
    slit.box((0, 0, MZ - 0.004), (0.4, 0.07, 0.002))
    slit.obj("MaskSlit", K.emit_mat("MaskSlitGlow", K.VIOLET, 9.0))

    # ---- wafer stage: granite + planar-motor coils + interferometer heads (fixed); mover + chuck + wafer (moving)
    wf = {k: K.MB() for k in ("granite", "cable")}
    wf["granite"].box((0.1, 0.1, 0.27), (3.6, 1.4, 0.54))
    K.cable_run(wf["cable"], [(-1.6, 0.45, 0.62), (-1.9, 0.5, 0.5), (-2.0, 0.55, 0.05)], n=5, seed=9)
    for k, m_ in (("granite", M["granite"]), ("cable", M["cable_g"])):
        wf[k].obj("WBase_" + k, m_, bevel=0.02 if k == "granite" else 0.0)
    zpl = WZ - 0.159
    MW = 1.0
    import hero_kit_r10 as _H10
    _H10.materials(M)
    M["ceramic"] = K.mat("ChuckCeramicR12", (0.42, 0.43, 0.46), rough=0.35, coat=0.2)   # R12: no white slab beside the wafer
    zbar = zpl + 0.015 + 0.11
    PF = HK.new_parts()
    # R19 row 3 (R18: "台面是同一种插座格子重复铺满"): the repeated coil-socket tiles on the stage deck are replaced by
    # the shared kit_r19.deck_r19 (5-6 big named assemblies lying on the deck + a diagonal coolant run) on the
    # dark epoxy deck plate; keep-clear around the mover / wafer, the interferometer heads and the wafer ruler
    import kit_r19 as KR
    PF["coil"].box((0.1, 0.1, zpl - 0.012), (3.3, 1.2, 0.024))
    keep19 = [((0.0, 0.0, zpl), 0.8), ((0.0, 0.62, zpl), 0.32), ((-0.3, -0.59, zpl), 0.14), ((0.3, -0.59, zpl), 0.14),
              ((MW / 2 + 0.25, 0.15, zpl), 0.14), ((MW / 2 + 0.25, -0.2, zpl), 0.14)]
    KR.deck_r19(PF, -1.5, 1.7, -0.55, 0.65, zpl, seed=83, keep=keep19, scale=0.62, depth=0.55)
    for x in (-0.3, 0.3):                                         # Y interferometers aimed at the front mirror bar
        HK12.interferometer_head(PF, (x, -0.5 - 0.09, 0.54), (0, 1, 0), h=zbar - 0.54)
    HK12.interferometer_head(PF, (MW / 2 + 0.25, 0.15, 0.54), (-1, 0, 0), h=zbar - 0.54)   # X interferometer
    HK12.interferometer_head(PF, (MW / 2 + 0.25, -0.2, 0.54), (-1, 0, 0), h=zbar - 0.54)
    HK.finish(PF, M, "WBase_PM")
    wp = {k: K.MB() for k in ("wafer",)}
    WR = 0.42                                                    # R12: wafer is the subject (>= 1/4 frame)
    # R17 row 5 (R16: "wafer = black glass with white lines on a white plate with a hole"): die-map silicon with a
    # bevelled edge (cut_kit_r17), the white ceramic plate + pin-chuck recess are replaced by a dark round chuck
    import cut_kit_r17 as CK
    wedge = K.MB()
    CK.wafer_r17(wp["wafer"], wedge, (0, 0, WZ), WR, thick=0.008, bevel=0.0045)
    PM = HK.new_parts()
    HK.planar_mover(PM, 0.0, 0.0, zpl, mover_w=MW, wafer_r=WR, wafer=False)
    PM["ceramic"].bm.free()
    PM["ceramic"] = K.MB()
    HK._cyl(PM["alu_dark"], (0, 0, zpl + 0.015 + 0.115), (0, 0, 1), WR * 1.035, 0.05, seg=128)
    wpiv = bpy.data.objects.new("WStage", None)
    sc.collection.objects.link(wpiv)
    wpiv.location.y = WY
    for o in bpy.data.objects:
        if o.name.startswith("WBase_"):
            o.location.y += WY
    ob = wp["wafer"].obj("WStage_wafer", CK.wafer_mat_r17(R=WR))                    # R17: die-map Si
    ob.parent = wpiv
    ob = wedge.obj("WStage_waferEdge", K.mat("WaferBevelR17", (0.78, 0.79, 0.82), metal=0.9, rough=0.22))
    ob.parent = wpiv
    HK.finish(PM, M, "WStageK", parent=wpiv)
    fr_ = bpy.data.objects.get("WStageK_alu")                  # R17: the mover frame no longer reads as a white plate
    if fr_ is not None:
        fr_.data.materials[0] = M["anod"]
    ex = K.MB()
    ex.box((0.5, 0, 0), (1.0, 0.26, 0.0016))
    exo = ex.obj("Exposed", K.emit_mat("ExposedGlowR13", K.VIOLET, 1.6, halo=0.35))     # R13: fields under the slit brighter
    exo.parent = wpiv
    exo.location = (-a_w, 0, WZ + 0.0012)
    _keys_linear(exo, "scale", [(1, 0.001), (n, 2 * a_w)], index=0)

    # ---- both bays: thick machined housings (as R9-R11)
    hs = K.mat("HousingGreyR9", (0.2, 0.21, 0.23), metal=0.7, rough=0.42, speck=0.12)
    hb = {k: K.MB() for k in ("box", "sec", "bolt", "port", "rib")}

    def housing(x0, x1, z0, z1, yb, t=0.12, depth=0.7, roof_port=None):
        cx, cz, w, h = (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0
        yf = yb - depth
        hb["box"].box((cx, yb + t / 2, cz), (w, t, h))
        for z in (z0 + t / 2, z1 - t / 2):
            hb["box"].box((cx, (yb + yf) / 2, z), (w, depth, t))
            hb["sec"].box((cx, yf - 0.003, z), (w, 0.006, t + 0.002))
        for x in (x0 + t / 2, x1 - t / 2):
            hb["box"].box((x, (yb + yf) / 2, cz), (t, depth, h))
            hb["sec"].box((x, yf - 0.003, cz), (t + 0.002, 0.006, h))
        for x in (x0 - 0.03, x1 + 0.03):
            hb["rib"].box((x, (yb + yf) / 2, cz), (0.06, depth * 0.9, h + 0.08))
        nb = int(w / 0.11)
        for i in range(nb):
            for z in (z0 + t * 0.5, z1 - t * 0.5):
                hb["bolt"].cyl((x0 + 0.08 + i * (w - 0.16) / max(1, nb - 1), yf - 0.012, z), 0.011, 0.02,
                               rot=(math.radians(90), 0, 0), seg=8)
        if roof_port is not None:
            hb["port"].ring((roof_port, (yb + yf) / 2, z1 + 0.03), 0.13, 0.08, 0.06, seg=32)
            hb["bolt"].bolts((roof_port, (yb + yf) / 2, z1 + 0.062), 0.105, 10, 0.009, 0.012)

    housing(-2.2, -0.05, 0.98, 2.04, 0.36, roof_port=-1.6)
    housing(-0.02, 2.2, 0.96, 2.42, 0.42, roof_port=1.5)
    hb["box"].obj("Bay_box", hs, bevel=0.01)
    hb["sec"].obj("Bay_sec", M["section"])
    hb["bolt"].obj("Bay_bolt", steel)
    hb["port"].obj("Bay_port", alu)
    hb["rib"].obj("Bay_rib", M["alu_dark"], bevel=0.006)
    pp = K.MB()
    for c, r_ in ((g2.lerp(mask_c, 0.33), 0.13), (mask_c.lerp(m1, 0.52), 0.13)):
        pp.ring((c.x, c.y, c.z), r_ * 1.35, r_, 0.05, seg=40)
    pp.obj("BeamPorts", alu)

    # mirrors: facet mirrors + G2 on mounts (illuminator), PO mirrors M1-M4 in machined cells on hexapods
    mm = {k: K.MB() for k in ("mirror", "mount", "bolt", "substrate", "spot", "copper", "cable_o", "cable_b")}
    facets = K.MB()
    HP = HK.new_parts()
    for i, (p_, r_) in enumerate(((ff, 0.17), (pf, 0.17), (g2, 0.15), (m1, 0.14), (m2, 0.23), (m3, 0.22),
                                  (m4, 0.17))):
        j = pts.index(p_)
        nrm = K.mirror_normal(pts[j - 1], p_, pts[j + 1])
        if i >= 3:
            HK.mirror_hexapod(HP, p_, nrm, r_, seed=i, spot_mb=mm["spot"])
            HK.cooling_bundle(HP, [p_ - nrm * 0.12 + Vector((0, 0.15, 0)), p_ + Vector((0, 0.38, 0.25))], k=3, r=0.01,
                              clamp_every=0.5, block=False, up=(0, 1, 0))
            continue
        K.mirror_with_mount(mm["mirror"], mm["mount"], mm["bolt"], p_, nrm, r_, thick=r_ * 0.45,
                            seed=i, mbsub=mm["substrate"], mbspot=mm["spot"], spot=0.62, mbpipe=mm["copper"],
                            mbcable=mm["cable_b" if i % 2 else "cable_o"])
        if i < 2:
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
        if len(mm[k].bm.verts):
            mm[k].obj("POm_" + k, m_)
        else:
            mm[k].bm.free()

    # ---- beam: R12 soft cones (beam_r12 via K.beam_columns), converging onto the wafer slit
    rad = [0.06, 0.1, 0.1, 0.075, 0.028, 0.075, 0.13, 0.12, 0.09, 0.012]
    col = K.MB()
    import beam_r16 as R16                   # R16 row 3: the last leg narrows onto the slit LINE (0.26 m along y)
    R16.END_SHAPE[0] = ((1, 0, 0), 0.007, (0, 1, 0), 0.12)
    import beam_r19 as R19
    R19.END_LAND[0] = False                  # R19: the slit gets its own two end highlights (below), no centre dot
    K.beam_columns(col, pts, rad, seg=40)
    R19.END_LAND[0] = True
    col.obj("ScanCol", M["beam_wide"])
    # R19 row 2 (R18: "让紫光以细锥收束到狭缝，狭缝两端加落点高光"): the wedge cone closes exactly on the slit line
    # (0.24 m along y); a landing highlight sits on each end of the slit, on the wafer surface
    se, sg = K.MB(), K.MB()
    for sy in (-1, 1):
        se.box((0, WY + sy * 0.118, WZ + 0.0042), (0.03, 0.022, 0.0012))
        sg.box((0, WY + sy * 0.118, WZ + 0.0038), (0.07, 0.05, 0.001))
    se.obj("SlitEndsR19", K.emit_mat("SlitEndHotR19", (0.86, 0.76, 1.0), 40.0)).visible_shadow = False
    sg.obj("SlitEndsGlowR19", K.emit_mat("SlitEndGlowR19", K.VIOLET, 6.0, halo=0.6)).visible_shadow = False
    # R19 row 2: the fold / PO mirrors seen in this frame (G2, M1) get lit real structure to reflect
    _HERO19[0] = [(g2, K.mirror_normal(pf, g2, mask_c), 0.9), (m1, K.mirror_normal(mask_c, m1, m2), 0.9)]
    sl = K.MB()
    sl.box((0, WY, WZ + 0.0035), (0.016, 0.26, 0.002))
    sl.obj("SlitW", K.emit_mat("SlitGlow", K.VIOLET, 30.0))
    sl2 = K.MB()                                         # R13: lit field band around the slit
    sl2.box((0, WY, WZ + 0.003), (0.075, 0.3, 0.0015))
    sl2.obj("SlitField", K.emit_mat("SlitFieldR13", (0.72, 0.6, 1.0), 4.0, halo=0.45))
    for i, p_ in enumerate((ff, pf, g2, m1, m2, m3, m4, mask_c + Vector((0, 0, -0.1)))):
        K.point(f"Bounce{i}", p_ + Vector((0, 0.15, 0)), 10, K.VIOLET, 0.03)   # behind the beam: no blobs in the wafer
    # bay walls + stage-services wall under the bays: hero_kit_r12 (no type repeats until all 14 are used)
    import parts_kit_r8 as PK
    keep11 = [(Vector((p_.x, 0.0, p_.z)), 0.25) for p_ in (ff, pf, g2, m1, m2, m3, m4)]
    HK12.wall_r12(HP, -2.08, -0.17, 1.1, 1.92, 0.36, seed=11, keep=keep11, scale=0.8, depth=1.1, front_y=0.15)
    HK12.wall_r12(HP, 0.1, 2.08, 1.08, 2.3, 0.42, seed=13, keep=keep11, scale=0.8, depth=1.1, front_y=0.17)
    HK12.wall_r12(HP, -2.6, 2.6, 0.56, 0.93, 0.62, seed=17, keep=[(waf_c, 0.6)], scale=0.6, depth=0.9, front_y=0.05,
                  blocks=7)
    HK.valve_island(HP, (-1.0, 0.1, 2.2), (0, -1, 0), nval=12, s=1.6, drop=0.12)
    HK.cooling_bundle(HP, [(-2.1, 0.25, 2.12), (-0.15, 0.25, 2.12)], k=4, r=0.014, up=(0, 1, 0))
    HK.cooling_bundle(HP, [(0.1, 0.3, 2.5), (2.1, 0.3, 2.5)], k=4, r=0.014, up=(0, 1, 0))
    HK.flange_viewport(HP, (2.22, -0.1, 1.9), (1, 0, 0), 0.06)
    HK.finish(HP, M, "B8HK")
    P = PK.new_parts()
    PK.turbo_pump(P, (-1.6, 0.0, 2.25), (0, 0, 1), 0.12)
    PK.turbo_pump(P, (1.5, 0.0, 2.62), (0, 0, 1), 0.12)
    PK.gate_valve(P, (-2.38, 0.0, 1.5), (1, 0, 0), 0.08)
    PK.turbo_pump(P, (-2.7, 0.0, 1.5), (-1, 0, 0), 0.11)
    PK.bellows(P, (2.26, -0.1, 1.3), (2.6, -0.1, 1.3), 0.07)
    PK.drag_chain(P, Vector((-1.95, 0.45 + WY, 0.56)), 1.2, R=0.07, w=0.12)       # wafer-stage energy chain
    PK.drag_chain(P, Vector((-2.4, 0.32, MZ + 0.54)), 1.5, R=0.06, w=0.1)
    PK.finish(P, M, "B8Kit")

    # ---- rulers (same unit U): reticle 0..8 under the bridge (PIP view), wafer 0..1 on the granite front edge
    ink = K.emit_mat("RulerInk", (0.86, 0.9, 0.96), 3.0)
    tk = K.MB()
    yr, zr = -0.62, MZ + 0.47
    for i in range(0, 33):
        x = -a_r + i * U / 4
        h = 0.07 if i % 4 == 0 else 0.03
        tk.box((x, yr, zr - h / 2), (0.007, 0.006, h))
    tk.box((0, yr, zr), (2 * a_r + 0.02, 0.006, 0.006))
    yw0, zw = 0.6, 0.62                                       # on the granite behind the mover (in frame)
    yw = yw0 + WY
    for i in range(0, 9):                                     # R13: taller ticks, thicker bar
        x = a_w - i * U / 8
        h = 0.07 if i in (0, 8) else (0.05 if i == 4 else 0.03)
        tk.box((x, yw, zw - h / 2), (0.006, 0.008, h))
    tk.box((0, yw, zw), (2 * a_w + 0.012, 0.008, 0.008))
    tk.box((0, yw + 0.03, 0.55), (2 * a_w + 0.08, 0.07, 0.02))                # ruler foot on the granite
    for x in (-a_w - 0.035, a_w + 0.035):
        tk.box((x, yw + 0.02, 0.585), (0.006, 0.006, 0.07))
    tk.obj("Rulers", ink)
    # R18 row 5 (R17: "the 0-8 ruler reads as '8x'; '格' has no unit"): ruler in millimetres (1 division = 10 mm,
    # schematic), unit printed at its end
    for i in range(9):
        _txt(f"RD{i}", str(i * 10), (-a_r + i * U, yr, zr - 0.14), 0.085, ink)
    _txt("RDmm", "mm", (a_r + U * 0.62, yr, zr - 0.14), 0.075, ink)
    # R13 (R12: "1 0 reads backwards"): the wafer ruler is a signed coordinate increasing to the right like the
    # mask ruler (0 .. 8 ->); the wafer runs the other way, from 0 down to -1
    # R15 (R14: "-0.5 tiny, squeezed into the ticks; misread risk; too many label layers"): no digits on the wafer
    # ruler - the magnifier prints the current reading
    brk = K.MB()
    for x in (-a_r - 0.08, a_r + 0.08):
        brk.box((x, (yr - 0.25) / 2 + 0.05, zr + 0.05), (0.03, 0.42, 0.02))
    brk.obj("RulerBrk", M["alu_dark"])
    pm = K.emit_mat("PtrCyan", K.CYAN, 7.0)
    pr, pw = K.MB(), K.MB()
    pr.box((0, yr + 0.005, zr - 0.03), (0.022, 0.01, 0.075))
    pr.box((0, (yr - 0.4) / 2 + 0.005, MZ + 0.2), (0.016, 0.24, 0.016))
    pr.box((0, yr + 0.005, MZ + 0.32), (0.016, 0.01, 0.22))
    pw.box((0, yw0 - 0.006, zw + 0.012), (0.007, 0.008, 0.045))
    pw.box((0, (yw0 + MW / 2) / 2, zw + 0.04), (0.01, abs(yw0 - MW / 2) + 0.02, 0.01))
    pw.box((0, MW / 2 + 0.005, (zw + 0.04 + zpl + 0.06) / 2), (0.01, 0.01, abs(zw + 0.04 - zpl - 0.06) + 0.01))
    pr.obj("PtrR", pm).parent = rpiv
    pw.obj("PtrW", pm).parent = wpiv
    gm = K.MB()
    gm.box((-a_r, yr - 0.002, zr - 0.03), (0.02, 0.004, 0.075))
    gm.box((a_w, yw - 0.002, zw - 0.012), (0.008, 0.004, 0.045))
    gm.obj("StartMarks", K.emit_mat("StartInk", (0.35, 0.55, 0.6), 1.5))
    knots = scan_knots(n)
    _keys_linear(rpiv, "location", [(f, -a_r + 2 * a_r * u) for f, u in knots], index=0)
    _keys_linear(wpiv, "location", [(f, a_w - 2 * a_w * u) for f, u in knots], index=0)

    # ---- far services wall (dark, defocused)
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

    # ---- lights
    _lights_dark(0.35)
    for o in bpy.data.objects:
        if o.name in ("PlasmaGlow", "IFGlow", "MaskGlow"):
            bpy.data.objects.remove(o)
    K.area("StageKeyR", (-1.0, -3.0, 4.3), (0, 0, MZ + 0.2), 2.5, 300, (1.0, 0.98, 0.95))
    K.area("StageKeyW", (-1.6, -2.0, 1.3), (0, WY, WZ), 1.2, 55, (1.0, 0.98, 0.95))
    K.area("StageRimW", (1.8, -1.2, 1.0), (0.3, WY, WZ), 0.8, 35, (0.85, 0.9, 1.0))
    K.area("RimTop", (1.5, 1.0, 4.6), (0, 0, MZ), 2.0, 500, (0.8, 0.85, 1.0))
    K.area("POKey", (2.6, -2.8, 2.0), (0.9, 0.2, 1.6), 2.0, 300, (0.95, 0.97, 1.0))
    K.area("IlKey", (-2.5, -2.5, 2.4), (-1.0, 0.2, 1.5), 1.6, 160, (0.95, 0.97, 1.0))
    K.area("BayFillP", (1.0, -2.6, 1.7), (0.95, 0.4, 1.6), 1.6, 200, (0.9, 0.93, 1.0))
    K.area("BayFillI", (-1.0, -2.4, 1.9), (-1.0, 0.2, 1.5), 1.4, 160, (0.9, 0.93, 1.0))
    K.area("UnderFill", (0.0, -1.9, 0.95), (0.0, 0.6, 0.75), 2.4, 25, (0.9, 0.93, 1.0), size_y=0.4)
    # the polished wafer mirrors this soft card toward the main camera (silicon sheen across half the disc)
    pass                                                       # R14: R12 sheen card removed (white haze)
    # R13: a broad overhead card in the wafer's mirror direction (metallic sheen over most of the disc) and darker
    # foreground stage parts so the wafer is the brightest object
    # R14: no broad overhead card (it laid a white haze on the wafer); a narrow grazing strip in the mirror
    # direction gives one highlight band across the dark polished disc
    K.area("WaferGrazeR14", (0.35, -0.2, 1.05), (0.0, WY, WZ), 0.12, 30, (0.95, 0.96, 1.0), size_y=1.4)
    _depth_layers(M, MZ, WZ)
    _darken(("WBase_", "FG_"), 0.4)
    # main camera: low 3/4 onto the wafer stage, slow truck for parallax
    cam, tgt = K.camera("CamR2", lens=30)
    # R15 (R14: "wafer ~1/5 of frame"): ~15 % closer, same slow truck
    K.key_path(cam, tgt, [(1, (-0.3, -1.98, 1.52), (0.02, -0.66, 0.84)), (n, (0.08, -2.0, 1.5), (0.06, -0.66, 0.84))],
               interp="LINEAR")
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 8.0
    cam.data.dof.focus_distance = 1.5
    # picture-in-picture camera on the reticle stage (rendered as shot B8_03M, pasted by the overlay)
    camm, tgtm = K.camera("CamR2M", lens=30)
    K.key_path(camm, tgtm, [(1, (0.0, -3.3, 2.15), (0.0, 0.0, 2.78)), (n, (0.0, -3.3, 2.15), (0.0, 0.0, 2.78))],
               interp="LINEAR")
    sc["hdri"] = "hangar_interior"
    sc["hdri_strength"] = 0.15
    sc["vignette"] = 0.3
    sc["film_grain"] = 0.08
    sc.camera = cam
    K.anchors(shot, {"rr0": Vector((-a_r, yr, zr)), "rr1": Vector((a_r, yr, zr)),
                     "wr0": Vector((a_w, yw, zw)), "wr1": Vector((-a_w, yw, zw)),
                     "mask": mask_c, "wafer": waf_c, "g2": g2, "src": src, "m2": m2, "m4": m4})
    return sc
