"""R28 cut helper (row 3b ONEPATH_R28): per-frame strength / alpha curve on every beam leg of a chain.

fade(sc, ch, windows, low, ramp): windows = [(leg_index, t0, t1), ...] in fractions of the shot (0..1). Inside its
window a leg is at 1.0 (current leg); outside it sits at `low` (a non-current leg, not deleted). The value multiplies
BOTH the emission strength and the transparent-mix factor of the leg materials (and of the landing spots that do not
touch the current leg), so the faded leg's emitted radiance ~ low^2 and its occlusion ~ low.
"""
import bpy


def _ins_mul(N, L, sock, val_out):
    """socket <- socket_input * val_out (inserts a MATH MULTIPLY)."""
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.label = "R28FadeMul"
    if sock.is_linked:
        src = sock.links[0].from_socket
        L.remove(sock.links[0])
        L.new(src, mul.inputs[0])
    else:
        mul.inputs[0].default_value = sock.default_value
    L.new(val_out, mul.inputs[1])
    L.new(mul.outputs[0], sock)


def _fade_node(m):
    """Add (once) a keyed Value node 'R28Fade' to a material and route emission strength + mix fac through it."""
    N, L = m.node_tree.nodes, m.node_tree.links
    v = N.get("R28Fade")
    if v is not None:
        return v
    v = N.new("ShaderNodeValue")
    v.name = "R28Fade"
    v.outputs[0].default_value = 1.0
    for nd in list(N):
        if nd.type == "EMISSION":
            _ins_mul(N, L, nd.inputs["Strength"], v.outputs[0])
        elif nd.type == "MIX_SHADER":
            ins = [l.from_node.type for s in nd.inputs[1:] for l in s.links]
            if "BSDF_TRANSPARENT" in ins:
                fac = nd.inputs[0]
                # Fac weights input 2; if transparent sits in slot 2, fade toward slot-2 instead -> 1 - (1-fac)*v
                if nd.inputs[1].is_linked and nd.inputs[1].links[0].from_node.type == "BSDF_TRANSPARENT":
                    _ins_mul(N, L, fac, v.outputs[0])
                else:
                    inv = N.new("ShaderNodeMath")
                    inv.operation = "SUBTRACT"
                    inv.inputs[0].default_value = 1.0
                    if fac.is_linked:
                        src = fac.links[0].from_socket
                        L.remove(fac.links[0])
                        L.new(src, inv.inputs[1])
                    else:
                        inv.inputs[1].default_value = fac.default_value
                    mul = N.new("ShaderNodeMath")
                    mul.operation = "MULTIPLY"
                    L.new(inv.outputs[0], mul.inputs[0])
                    L.new(v.outputs[0], mul.inputs[1])
                    back = N.new("ShaderNodeMath")
                    back.operation = "SUBTRACT"
                    back.inputs[0].default_value = 1.0
                    L.new(mul.outputs[0], back.inputs[1])
                    L.new(back.outputs[0], fac)
    return v


def _own(ob):
    """Make the object's materials single-user (curves are per-object)."""
    for i, s in enumerate(ob.material_slots):
        if s.material is not None and s.material.users > 1:
            m2 = s.material.copy()
            if s.link == "OBJECT":
                s.material = m2
            else:
                ob.data = ob.data.copy() if ob.data.users > 1 else ob.data
                ob.data.materials[i] = m2


def key_curve(obs, keys):
    """keys = [(frame, value)]; LINEAR interpolation on every material's R28Fade value."""
    for ob in obs:
        if ob is None or ob.type != "MESH":
            continue
        _own(ob)
        for s in ob.material_slots:
            m = s.material
            if m is None or not m.use_nodes:
                continue
            v = _fade_node(m)
            pe = bpy.context.preferences.edit
            prev = pe.keyframe_new_interpolation_type
            pe.keyframe_new_interpolation_type = "LINEAR"
            try:
                for f, val in keys:
                    v.outputs[0].default_value = val
                    v.outputs[0].keyframe_insert("default_value", frame=f)
            finally:
                pe.keyframe_new_interpolation_type = prev


def curve(t0, t1, n, low, ramp):
    """Frame keys for a window [t0, t1] (fractions of n frames): low outside, 1 inside, linear ramps of `ramp` frames."""
    f0, f1 = 1 + (n - 1) * t0, 1 + (n - 1) * t1
    keys = []
    if t0 > 0:
        keys += [(1, low), (max(1, round(f0 - ramp / 2)), low), (round(f0 + ramp / 2), 1.0)]
    else:
        keys += [(1, 1.0)]
    if t1 < 1:
        keys += [(round(f1 - ramp / 2), 1.0), (round(f1 + ramp / 2), low), (n, low)]
    else:
        keys += [(n, 1.0)]
    return keys


def fade(sc, ch, windows, low, ramp=6, spot_keep=True, tag=""):
    n = sc.frame_end
    legs = ch["legs"]
    spots = ch.get("spots") or []
    for i, t0, t1 in windows:
        ks = curve(t0, t1, n, low, ramp)
        obs = list(legs[i]) if isinstance(legs[i], (list, tuple)) else [legs[i]]
        key_curve(obs, ks)
        print(f"[r28u] {tag} leg{i} {[o.name for o in obs]} keys {ks}", flush=True)
    # landing spots: spot j sits at stop j (landing of leg j-1, start of leg j): bright while leg j-1 or leg j is current
    if spot_keep:
        win = {i: (t0, t1) for i, t0, t1 in windows}
        for j, sp in enumerate(spots):
            if sp is None:
                continue
            ts = [win[k] for k in (j - 1, j) if k in win]
            if not ts:
                continue
            t0, t1 = min(a for a, _ in ts), max(b for _, b in ts)
            ks = curve(t0, t1, n, low, ramp)
            key_curve([sp], ks)
            print(f"[r28u] {tag} spot{j} {sp.name} keys {ks}", flush=True)
