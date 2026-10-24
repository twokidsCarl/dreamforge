"""R22 row 6 (B8_03 / B8_03M material): R21 review 「晶圆是白亮底加灰方格，偏『平涂网格』，看不出硅片的镜面和场内图形」.
The wafer becomes dark-grey mirror silicon (metallic, low roughness) whose die fields keep the R17 device micro
pattern (lines / logic block / pads, now dark-on-dark with a faint blue), plus a stronger grazing card in the wafer's
mirror direction so a highlight band runs across the polished disc. Beam / slit / readouts untouched (R21 wins)."""
import bpy


def _lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def post(sc, shot):
    ob = bpy.data.objects.get("WStage_wafer")
    if ob is None or not ob.data.materials:
        return
    m = ob.data.materials[0].copy()
    m.name = "WaferSiR22"
    ob.data.materials[0] = m
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Metallic"].default_value = 1.0
    mixes = [n for n in nt.nodes if n.type == "MIX" and getattr(n, "data_type", "") == "RGBA"]
    cols = {(0.56, 0.57, 0.61): (0.2, 0.205, 0.22),     # bare Si: dark grey mirror
            (0.24, 0.25, 0.33): (0.07, 0.075, 0.12),    # device areas: near-black, faint blue
            (0.7, 0.71, 0.74): (0.34, 0.35, 0.37)}      # scribe streets: thin lighter lines
    for mx in mixes:
        for key in ("A", "B"):
            s_ = mx.inputs[key]
            if s_.is_linked:
                continue
            v = tuple(round(x, 2) for x in s_.default_value[:3])
            for k_, new in cols.items():
                if all(abs(a - b_) < 0.02 for a, b_ in zip(v, _lin(k_))):
                    s_.default_value = (*_lin(new), 1)
    for n in nt.nodes:
        if n.type == "MAP_RANGE":
            n.inputs["To Min"].default_value = 0.04
            n.inputs["To Max"].default_value = 0.16
    g = bpy.data.objects.get("WaferGrazeR14")
    if g is not None:
        g.data.energy *= 4.0
    # the mirror wafer now reflected the violet bounce point lights as a flare (8-spp f143): not in glossy rays
    for o in bpy.data.objects:
        if o.type == "LIGHT" and (o.name.startswith("Bounce") or o.data.type == "POINT"):
            try:
                o.visible_glossy = False
            except AttributeError:
                pass
    # exposed fields: on the dark wafer the R13 glow read as a flat violet slab -> half strength, pattern shows
    ex = bpy.data.objects.get("Exposed")
    if ex is not None and ex.data.materials:
        em = ex.data.materials[0]
        for nd in em.node_tree.nodes:
            if nd.type == "EMISSION":
                nd.inputs["Strength"].default_value *= 0.45
            elif nd.type == "BSDF_PRINCIPLED" and "Emission Strength" in nd.inputs:
                nd.inputs["Emission Strength"].default_value *= 0.45
    # violet beam volumes / glows are not mirrored by the polished wafer (8-spp: violet blobs on the disc)
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name in ("Exposed", "WStage_wafer"):
            continue
        mn = " ".join(m.name for m in o.data.materials if m)
        if any(k in mn for k in ("EUV", "Beam", "Cone", "Spot", "Glow", "Violet", "Land")):
            try:
                o.visible_glossy = False
            except AttributeError:
                pass
