"""R24 chero B8_03 / B8_03M (R24_ROOT_CAUSE rows 3 + 5). Layered on R22 (scan) + R23 (dark Si wafer, push + focus pull).

R23 review: 「晶圆上那条横贯全片的白色高光带读起来像第二道光/狭缝…去掉或压暗这条反射。狭缝内的白色圆点/圆环（像标签图钉）
也删掉，狭缝做成纯紫亮条」「光束是等宽长条：改成从狭缝向上张开的窄锥，软边」
  * WaferEnvStripR23 (the full-width glossy band) -> a short, dim strip offset to one side: a weak local glint next to
    the slit, never across the disc;
  * slit landing dot / ring / end caps deleted (ScanSlitLandR21*, SlitEnds*); SlitField + SlitW = pure violet;
  * equal-width bar ScanTipR21 -> ONE beam_r24 narrow soft cone, narrow at the slit, opening upward toward the reticle
    (same top point as the R21 bar so the PIP / reticle side is unchanged).
"""
import bpy
from mathutils import Vector

GLINT_LEN, GLINT_OFF, GLINT_STR = 0.12, 0.17, 0.0
VIOLET_SLIT = (0.42, 0.12, 1.0)


def _world_verts(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]


def _set_emit(o, col, mult=None):
    for m in o.data.materials:
        if m is None or not m.use_nodes:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "EMISSION":
                nd.inputs["Color"].default_value = (*col, 1)
                if mult is not None:
                    nd.inputs["Strength"].default_value *= mult
            elif nd.type == "BSDF_PRINCIPLED":
                if "Emission Color" in nd.inputs:
                    nd.inputs["Emission Color"].default_value = (*col, 1)
                nd.inputs["Base Color"].default_value = (col[0] * 0.3, col[1] * 0.3, col[2] * 0.3, 1)


def post(sc, shot):
    import beam_r24 as BR
    # ---- slit: pure violet bar, no white dot / ring / end caps
    for nm in ("ScanSlitLandR21Glow", "ScanSlitLandR21Hot", "ScanSlitLandR21Lt", "SlitEndsGlowR19", "SlitEndsR19"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            bpy.data.objects.remove(o)
    # SlitGlow strength 30 clipped the violet bar to a white core -> x0.17; field x0.5 (pure violet, no white)
    for nm, mult in (("SlitW", 0.07), ("SlitField", 0.4)):
        o = bpy.data.objects.get(nm)
        if o is not None and o.type == "MESH":
            _set_emit(o, VIOLET_SLIT, mult)
    sw = bpy.data.objects.get("SlitW")
    tip = bpy.data.objects.get("ScanTipR21")
    if sw is None or tip is None:
        print("[cut_hero_r24_b803] slit / tip missing", sw, tip)
        return
    vs = _world_verts(sw)
    sc_ = sum(vs, Vector()) / len(vs)
    xs = [v.x for v in vs]
    ys = [v.y for v in vs]
    hw, hl = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    tv = _world_verts(tip)
    zt = max(v.z for v in tv)
    top_pts = [v for v in tv if v.z > zt - 0.03]
    top = sum(top_pts, Vector()) / len(top_pts)
    tip.hide_render = True
    tip.hide_viewport = True
    # ---- ONE narrow cone: from the reticle side (top) down to the slit; narrow at the slit, opening upward
    ch = BR.chain("ScanBeamR24", [(top, None), (sc_, (0, 0, 1))],
                  [(hl * 2.6, 0.09), (hl * 0.95, hw * 1.6)],   # try 2: top x1.45 still read as an equal-width slab
                  strength=3.0, alpha=0.5, land_final=False, xdir=(0, 1, 0), inner=0.7, inner_gain=1.15)
    print("[cut_hero_r24_b803] slit", tuple(round(c, 3) for c in sc_), "half", round(hw, 3), round(hl, 3),
          "top", tuple(round(c, 3) for c in top))
    if shot == "B8_03M":
        return
    # ---- wafer band -> weak local glint beside the slit
    st = bpy.data.objects.get("WaferEnvStripR23")
    if st is not None and GLINT_STR <= 0:
        st.hide_render = True      # 8-spp try 2: even a short dim strip read as a grey tab beside the slit -> removed
    elif st is not None:
        st.scale.x = GLINT_LEN / (2.4 * 0.9)
        st.location.x += GLINT_OFF
        for m in st.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == "EMISSION":
                    nd.inputs["Strength"].default_value = GLINT_STR
    f0 = sc.frame_current
    rx = (sc.render.resolution_x, sc.render.resolution_y)
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    BR.check(sc, ch, (42, 92, 143), tag="B8_03")
    sc.render.resolution_x, sc.render.resolution_y = rx
    sc.frame_set(f0)
