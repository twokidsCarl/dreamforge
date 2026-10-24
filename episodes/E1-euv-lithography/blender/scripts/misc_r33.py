"""Round 33 hook (misc sub-agent; shots in r2_misc.R33_MISC = B8_17). Layered AFTER the R22..R31 hooks, BEFORE beam_hook_r29.

One module-level switch (False -> exact R32 pixels):
- FIELDS_R33 (row 5, B8_17) R32 p3 「场格数和 188 对不上…改成长方形格」「曝光进度和计数器矛盾：143 帧里只有右侧约 1/4 是白格。按蛇形扫描
  逐格变亮，亮格比例跟随计数器」. The 188 cells of misc_b817_r20.layout (26 x 16.5 mm half-fields, exactly 188 reaching
  >= 3 mm into the 300 mm wafer, count printed) are kept as the ONLY grid, but:
  (a) exposure order = ROW serpentine (near row first, alternating x direction) instead of the R20 column serpentine;
      the per-polygon scan index (UVMap.x) is rewritten, the stage is re-keyed so the field being exposed (C(f) - 1, the
      R22 counter curve) sits under the fixed slit/cone;
  (b) semantics flipped: EXPOSED = bright warm-white resist, UNEXPOSED = dark silicon -> lit cells == counter;
  (c) scribe lanes widened (rows were sub-pixel -> cells read as squares/stripes), parity tone contrast reduced;
  (d) the R24 wafer swap (exposed wafer flies to the cassette = the motion-blur smear on the top cassette wafer, fresh
      unexposed wafer onto the chuck) starts SWAP_DELAY frames later, so the finished all-lit wafer is still on the chuck
      at the last job frame (counter 188).
"""
import math

import bpy

FIELDS_R33 = True

UNEXP = ((0.17, 0.18, 0.22), (0.21, 0.22, 0.26))      # dark silicon (parity pair, sRGB)
EXPO = ((0.76, 0.74, 0.68), (0.82, 0.80, 0.74))       # lit / exposed resist: warm white (parity pair, sRGB)
EXPO_GLOW = 0.08                                      # faint warm self-glow on exposed cells ("lit")
LANE_X, LANE_Y = 0.011, 0.024                         # half-lane widths (scene units, 0.26 = 26 mm)
SWAP_DELAY = 15


def pre(variant, shot, mod):
    return None


def post(sc, variant, shot):
    try:
        if shot == "B8_17" and FIELDS_R33:
            _b817(sc)
    except Exception as e:   # never break the build; the log shows it
        import traceback
        traceback.print_exc()
        print(f"[R33 misc] {shot} post FAILED: {e}", flush=True)
    return sc


def _lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _fcs(ob):
    import common as C
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    return list(C.fcurves(ad.action))


def _row_serpentine(cells):
    rows = sorted({c[1] for c in cells})                         # near (-y) row first
    order = []
    for ri, j in enumerate(rows):
        order += sorted([c for c in cells if c[1] == j], key=lambda c: c[0], reverse=(ri % 2 == 1))
    return order


def _b817(sc):
    import misc_b817_r20 as W20
    import misc_b817_r22 as W22
    n = sc.frame_end
    dur = n / W22.FPS
    R = 1.5
    old = W20.layout(R)                                           # polygon k of FieldsR20 == old[k]
    new = _row_serpentine(old)
    rank = {(c[0], c[1]): k for k, c in enumerate(new)}
    full = sum(1 for (_, _, cx, cy) in new if all(math.hypot(cx + sx * W20.FX / 2, cy + sy * W20.FY / 2) <= R
                                                 for sx in (-1, 1) for sy in (-1, 1)))
    print(f"[R33 B8_17] FIELDS_R33: {len(new)} cells 26 x 16.5 mm ({full} whole + {len(new) - full} edge), "
          f"{len({c[1] for c in new})} rows, row serpentine", flush=True)
    # (a) scan index per polygon
    fo = bpy.data.objects.get("FieldsR20")
    me = fo.data
    uvl = me.uv_layers["UVMap"]
    for p in me.polygons:
        i, j = old[p.index][0], old[p.index][1]
        u = (rank[(i, j)] + 0.5) / W20.COUNT
        for li in p.loop_indices:
            uvl.data[li].uv = (u, 0.0)
    cv = {f: W22.counter(f, dur) for f in range(1, n + 2)}
    done = next(f for f in range(1, n + 2) if cv[f] >= W22.COUNT)
    for f in (56, 122, 189):
        if f in cv:
            print(f"[R33 B8_17] frame {f}: counter {cv[f]} -> lit cells {sum(1 for k in range(W20.COUNT) if (k + 0.5) / W20.COUNT < cv[f] / W20.COUNT + 1e-4)}",
                  flush=True)
    # (a') stage: field C(f) - 1 under the fixed slit (R22 keys 1..done+3 rewritten, later keys kept)
    rig = bpy.data.objects.get("WaferStageR21")
    if rig is not None:
        fl = [fc for fc in _fcs(rig) if fc.data_path == "location"]
        sx0 = fl[0].evaluate(1) + old[0][2]
        sy0 = fl[1].evaluate(1) + old[0][3]
        for fc in fl:
            for kp in list(fc.keyframe_points)[::-1]:
                if kp.co.x <= done + 3.5:
                    fc.keyframe_points.remove(kp)
        for f in range(1, done + 4):
            k = min(max(cv[f] - 1, 0), W20.COUNT - 1)
            rig.location = (sx0 - new[k][2], sy0 - new[k][3], 0.0)
            rig.keyframe_insert("location", frame=f)
        for fc in _fcs(rig):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        # row serpentine = fast screen-horizontal stage steps -> no motion-blur smear on the stage (cells stay countable)
        nb = 0
        for ob in [rig] + list(rig.children_recursive):
            try:
                ob.cycles.use_motion_blur = False
                nb += 1
            except AttributeError:
                pass
        print(f"[R33 B8_17] motion blur off on {nb} stage objects", flush=True)
    # (b) + (c) colours / lanes on the exposing wafer (+ its cassette copy) and the fresh wafer
    done_m = []
    for m in bpy.data.materials:
        if not m.node_tree or not (m.name.startswith("FieldR20") or m.name.startswith("FieldR24Fresh")):
            continue
        N = m.node_tree.nodes
        mix = next((x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA"
                    and x.inputs["A"].is_linked and x.inputs["B"].is_linked
                    and x.inputs["A"].links[0].from_node.type == "MIX"), None)
        if mix is not None:
            for sock, (c0, c1) in (("A", UNEXP), ("B", EXPO)):
                cm = mix.inputs[sock].links[0].from_node
                cm.inputs["A"].default_value = (*_lin(c0), 1)
                cm.inputs["B"].default_value = (*_lin(c1), 1)
        else:
            mix = next((x for x in N if x.type == "MIX" and getattr(x, "data_type", "") == "RGBA"
                        and x.inputs["Factor"].is_linked and not x.inputs["A"].is_linked), None)
            if mix is None:
                continue
            mix.inputs["A"].default_value = (*_lin(UNEXP[0]), 1)
            if not mix.inputs["B"].is_linked:
                mix.inputs["B"].default_value = (*_lin(EXPO[0]), 1)
        for x in N:                                            # R27 lane thresholds
            if x.type == "MATH" and x.operation == "LESS_THAN" and x.inputs[0].is_linked and not x.inputs[1].is_linked:
                v = x.inputs[1].default_value
                if abs(v - 0.008) < 1e-6:
                    x.inputs[1].default_value = LANE_X
                elif abs(v - 0.013) < 1e-6:
                    x.inputs[1].default_value = LANE_Y
        # faint warm glow on exposed cells: emission colour stays violet for the hot cell; add a separate emission
        bs = next((x for x in N if x.type == "BSDF_PRINCIPLED"), None)
        if bs is not None and EXPO_GLOW > 0 and bs.inputs["Emission Strength"].is_linked:
            exposed = mix.inputs["Factor"].links[0].from_socket
            em = N.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (*_lin(EXPO[1]), 1)
            gm = N.new("ShaderNodeMath")
            gm.operation = "MULTIPLY"
            m.node_tree.links.new(exposed, gm.inputs[0])
            gm.inputs[1].default_value = EXPO_GLOW
            m.node_tree.links.new(gm.outputs[0], em.inputs["Strength"])
            add = N.new("ShaderNodeAddShader")
            sock = bs.outputs[0].links[0].to_socket if bs.outputs[0].links else None
            if sock is not None:
                m.node_tree.links.new(bs.outputs[0], add.inputs[0])
                m.node_tree.links.new(em.outputs[0], add.inputs[1])
                m.node_tree.links.new(add.outputs[0], sock)
        done_m.append(m.name)
    print(f"[R33 B8_17] exposed = warm white, unexposed = dark, lanes x {LANE_X} y {LANE_Y} in {done_m}", flush=True)
    # (d) delay the R24 wafer swap (and the light-off around it) by SWAP_DELAY frames
    T0 = done + 3
    names = []
    for ob in sc.objects:
        nm = ob.name
        if not (nm.startswith(("Exposed", "Fresh", "B817R24")) or nm in ("Slit", "Wafer", "FieldsR20", "WaferNotch")):
            continue
        hit = False
        for fc in _fcs(ob):
            for kp in sorted(fc.keyframe_points, key=lambda k: -k.co.x):
                if kp.co.x >= T0 - 1.5:
                    kp.co.x += SWAP_DELAY
                    kp.handle_left.x += SWAP_DELAY
                    kp.handle_right.x += SWAP_DELAY
                    hit = True
            fc.update()
        if hit:
            names.append(nm)
    print(f"[R33 B8_17] n={n} done f{done}: swap keys >= f{T0 - 1} shifted +{SWAP_DELAY} on {names}", flush=True)
