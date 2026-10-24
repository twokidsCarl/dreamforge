"""Round 27 hook (owned by the 'tin' sub-agent; shots in r2_source.R27_TIN = A0_01 / B1_08 / B1_10). Layered AFTER the
R22..R26 hooks (A0_01 / B1_08: R26 pixels = source_r26 camera push + landing rim + dash-to-lock are kept; B1_10: R25).

R27_ROOT_CAUSE row 1 (material - tin asset UNFROZEN). One switch per sub-fix:

  MAT_R27     (row 1, all three) the R25 banded structured env (source_r25_tin.struct_bands: flange bands / port rings /
              dark gaps = the 「条纹星球」/「半黑球」) is removed from every tin part and replaced by ONE soft, uniformly
              bright env per tin part (no bands, no black: grey-blue base + broad overhead soft light + a bright cap
              BEHIND the tin = rim light around every droplet / the sheet edge + one soft key highlight); tin material =
              bright silver liquid metal, roughness 0.05, NO ripple / smear bump. Sheet (A0_01 / B1_10): edge bead
              thicker (source_r24_tin.HE -> HE_R27) and the sheet turned about Z so the camera sees it SHEET_VIEW deg
              from edge-on (= thin disc with a visible thickness edge; the R24 ring of breakup satellites is kept).
  PULSE2_R27  (row 1, A0_01) the main pulse (2nd shot, frames hit2-4..boom) rebuilt thicker + brighter than the
              pre-pulse (r0 0.025 -> P2_R0, emission x P2_GAIN) so the two shots read as 「连打两次」.
  AIM_R27     (row 1, B1_08) the pending-laser aim dashes are cyan HUD ink (orange is reserved for the laser firing).

Remove a shot from r2_source.R27_TIN -> exact R26 pixels; set a switch False -> that sub-fix off.
"""
import math

import bpy
from mathutils import Vector

MAT_R27 = True
PULSE2_R27 = True
AIM_R27 = True

SHEETS = {"A0_01", "B1_10"}
HE_R27 = 0.024                  # unit-radius sheet: edge-bead half thickness (R26 A0_01 0.005, R24 0.006)
SHEET_VIEW = 30.0               # camera sees the sheet this many degrees off its plane (edge-on = 0)
ENV_FRAME = {"A0_01": (72, 160), "B1_10": (69, 69), "B1_08": (51, 51)}   # (droplet frame, sheet frame)
DROP_GONE = {"A0_01": 94, "B1_10": 32}
TIN_ROUGH = 0.03
LIQUID_WOBBLE = 0.12            # sheet: low-freq liquid wobble bump strength (0 = flat)
P2_R0, P2_GAIN = 0.05, 2.2
BASE = (0.05, 0.053, 0.062)       # env base: lit grey-blue chamber, never black
SHEET_BASE = (0.04, 0.045, 0.055)   # sheet env base (dim, the soft light gives the brightness)
WHITE = (1.0, 0.98, 0.95)
COOL = (0.86, 0.91, 1.0)


def pre(variant, shot, mod):
    if MAT_R27 and shot in SHEETS:
        import source_r24_tin as T24
        T24.HE = HE_R27


def _ob(n):
    return bpy.data.objects.get(n)


def _n(v):
    return tuple(Vector(v).normalized())


def _drop_bands(tc, rt, up):
    return [((0, 0, 1), 1.0, 0.95, 1.0, COOL),                       # broad overhead soft light, fades below horizon
            (_n(-tc), 1.0, 0.40, 1.8, WHITE),                        # bright cap behind = rim light round the ball
            (_n(tc), 1.0, 0.7, 0.12, WHITE),                         # soft frontal fill (no dark middle band)
            (_n(tc + up * 1.0 - rt * 0.5), 1.0, 0.004, 14.0, WHITE)]  # one soft key highlight upper-left


def _sheet_bands(tc, rt, up, nrm, mdir):
    """flat mirror sees only a ~40 deg window round mdir: ONE soft horizon inside it (bright above -> dim below, no
    band lines) + a fill so the lower part is never black + one soft specular spot + edge light + rim."""
    md = Vector(mdir).normalized()
    return [(_n(md + up * 0.30), 1.0, 0.10, 1.10, COOL),              # big soft light above the mirror direction
            (_n(md), 1.0, 1.2, 0.12, COOL),                           # fill (lower face dim, not black)
            (_n(md + up * 0.12 - rt * 0.18), 1.0, 0.003, 14.0, WHITE),  # soft specular spot on the face
            (_n(nrm), 0.0, 0.22, 3.0, WHITE),                         # light in the sheet plane -> bright thickness edge
            (_n(-tc), 1.0, 0.5, 1.4, WHITE)]                          # rim light from behind


def _yaw_for_view(tc):
    """yaw so that the sheet normal (+X rotated about Z) is SHEET_VIEW deg off the camera's horizontal direction
    complement: angle(normal, to_cam_horizontal) = 90 - SHEET_VIEW."""
    az = math.atan2(tc.y, tc.x)
    off = math.radians(90.0 - SHEET_VIEW)
    cands = [az + off, az - off]
    return min(cands, key=lambda a: abs(math.atan2(math.sin(a), math.cos(a))))   # smallest turn away from +X


def _wobble_mat(base, strength):
    """liquid surface: ONE low-frequency smooth wobble (no rings / no fine noise = no R25 smear)."""
    m = base.copy()
    m.name = "TinFilmR27"
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.3
    nz.inputs["Detail"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = 0.05
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _material(sc, shot):
    import source_r24 as H24
    import source_r25_tin as T25
    for o in list(bpy.data.objects):
        if o.name.startswith(("TinEnvR25", "TinSheetEnvR25")):
            bpy.data.objects.remove(o, do_unlink=True)
    tin = [o for o in bpy.data.objects if o.type == "MESH" and o.active_material is not None
           and o.active_material.name.startswith(("TinMetalR25", "TinFilmR25", "LiquidTin", "TinMetalR24"))]
    m = T25.tin_mat_r25("TinMetalR27")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = TIN_ROUGH
    for o in tin:
        o.data.materials.clear()
        o.data.materials.append(m)
    sheet = _ob("Pancake")
    if sheet is not None and shot in SHEETS and LIQUID_WOBBLE > 0:
        sheet.data.materials.clear()
        sheet.data.materials.append(_wobble_mat(m, LIQUID_WOBBLE))
    f_drop, f_sheet = ENV_FRAME[shot]
    root = _ob("PancakeRoot")
    if shot in SHEETS and root is not None:
        tc, rt, up = H24._cam_dirs(sc, f_sheet, (0, 0, 0))
        yaw = _yaw_for_view(tc)
        root.rotation_euler = (0, 0, yaw)
        nrm = Vector((math.cos(yaw), math.sin(yaw), 0))
        if nrm.dot(tc) < 0:
            nrm = -nrm
        v = -tc
        mdir = v - 2 * v.dot(nrm) * nrm
        root["r27_view_deg"] = math.degrees(math.asin(max(-1, min(1, abs(nrm.dot(tc))))))
        print("R27TIN sheet yaw %.1f deg, view off plane %.1f deg" % (math.degrees(yaw), root["r27_view_deg"]))
        T25.env_r25("TinSheetEnvR27", (0, 0, 0), 0.27, _sheet_bands(tc, rt, up, nrm, mdir), base=SHEET_BASE)
    drops = [o for o in tin if o.name in ("Droplet", "DropletNext") or (o.name.startswith("Drop") and o.name[4:].isdigit())]
    for d in drops:
        p = d.matrix_world.translation.copy()
        tc, rt, up = H24._cam_dirs(sc, f_drop, p)
        e = T25.env_r25("TinEnvR27_" + d.name, (0, 0, 0), 0.05, _drop_bands(tc, rt, up), parent=d, base=BASE)
        if d.name == "Droplet" and shot in DROP_GONE:
            for f, s_ in ((DROP_GONE[shot], 1.0), (DROP_GONE[shot] + 1, 0.001)):
                e.scale = (s_, s_, s_)
                e.keyframe_insert("scale", frame=f)
            H24._const(e)


def _pulse2():
    import sys
    mod = sys.modules.get("r2_source")
    old = _ob("MainPulse")
    if mod is None or old is None:
        return
    hide = [(kp.co[0], kp.co[1]) for fc in __import__("source_r26_tin")._fcs(old) if fc.data_path == "hide_render"
            for kp in fc.keyframe_points]
    vis = (old.visible_shadow, old.visible_glossy, old.visible_diffuse)
    bpy.data.objects.remove(old, do_unlink=True)
    r = 0.016
    mp = mod.main_pulse_cone_r15((mod.COLL_X - 0.2, 0, 0), (-0.012, 0, 0), P2_R0, r * 10.0, "MainPulse")
    (mp.visible_shadow, mp.visible_glossy, mp.visible_diffuse) = vis
    for nd in mp.active_material.node_tree.nodes:      # strength is driven by the soft-edge map range (To Min 3.2)
        if nd.type == "MAP_RANGE" and abs(nd.inputs["To Min"].default_value - 3.2) < 1e-6:
            nd.inputs["To Min"].default_value *= P2_GAIN
    shown = sorted(f for f, h in hide if h < 0.5)
    gone = sorted(f for f, h in hide if h > 0.5 and shown and f > shown[0])
    if shown:
        mod.show_between(mp, int(shown[0]), int(gone[0]) - 1 if gone else None)
    li = _ob("LaserLight")
    if li is not None:             # brighter orange spill from the 2nd shot on the tin
        import kit_r2 as K
        ad = li.data.animation_data
        if ad and ad.action:
            for fc in __import__("source_r26_tin")._fcs(li.data):
                for kp in fc.keyframe_points:
                    if 150 <= kp.co[0] <= 166:
                        kp.co[1] *= 1.6


def _aim_cyan():
    import kit_r2 as K
    ob = _ob("PendingLaser")
    if ob is None or ob.active_material is None:
        return
    m = ob.active_material.copy()
    m.name = "PendingAimCyanR27"
    for nd in m.node_tree.nodes:
        if nd.type == "EMISSION":
            nd.inputs["Color"].default_value = (*K.lin(K.CYAN), 1)
    ob.data.materials.clear()
    ob.data.materials.append(m)


def post(sc, variant, shot):
    if MAT_R27:
        _material(sc, shot)
    if PULSE2_R27 and shot == "A0_01":
        _pulse2()
    if AIM_R27 and shot == "B1_08":
        _aim_cyan()
    sc.frame_set(1)
    return sc
