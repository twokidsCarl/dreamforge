"""R15 root cause #2 ("mirrors don't read as mirrors"): ONE shared EUV mirror surface for every mirror in the
cutaway (collector, field / pupil facets, M1..M6, fold mirrors) and the source chamber collector.

R14 reads: B3_02 collector = "translucent violet glass", B5_01 facets = "self-lit LED panel", B7_06 = "chrome
donuts", B1_15 = "a bowl of violet fog", B2_08 = "matte dark-blue plate".
Rule: neutral silver-grey Mo/Si multilayer look, polished, NO emission, NO violet base colour, no rainbow. Violet on
a mirror may only come from the beam's own landing spot / the plasma's reflection. Unlit facets stay dark metal.

  import mirror_r15 as MR
  m = MR.ml_mirror("CollectorML")          # optical face
  e = MR.ground_edge("MirrorEdgeR15")      # ground / chamfered side of a thick mirror blank
"""
import kit_r2 as K


def ml_mirror(name="EUVMirrorML_R15", rough=0.03, tone=0.86, coat=0.35):
    """Optical face: polished metal, faint warm-neutral tint (the Mo/Si stack is very slightly gold-grey, never
    violet). A fine radial polish noise in roughness keeps it from reading as glass or chrome plastic."""
    m = K.mat(name, (tone, tone * 0.985, tone * 0.96), metal=1.0, rough=rough, coat=coat)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 60.0
    nz.inputs["Detail"].default_value = 2.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough * 0.6
    mr.inputs["To Max"].default_value = rough * 1.6
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m


def ground_edge(name="EUVMirrorEdge_R15", tone=0.62):
    """Side / chamfer / back of a thick mirror blank: fine-ground (satin) substrate, so the polished face reads as a
    separate optical surface on a solid disc."""
    return K.mat(name, (tone, tone, tone * 0.98), metal=0.0, rough=0.42)


def dark_unlit(name="EUVMirrorUnlit_R15"):
    """Facets / mirror areas that the beam does not hit at this moment: dark polished metal (reflects the bay, does
    not glow)."""
    return K.mat(name, (0.32, 0.33, 0.35), metal=1.0, rough=0.06, coat=0.2)
