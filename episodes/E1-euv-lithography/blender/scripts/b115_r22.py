"""Round 22 (P1) hook for B1_15 (R22_ROOT_CAUSE row 2). Owned by the src-a sub-agent.

pre(): r2_source._contrast is replaced by b115_r22_build.build_contrast (plasma on axis at the near focus, reflected
converging cone toward the far IF, elevated camera, whole rim in frame). Remove B1_15 from r2_source.R22_SRC -> R21.
"""


def pre(variant, shot, mod):
    if shot != "B1_15" or variant != "contrast":
        return
    import b115_r22_build as BB

    def _contrast_r22(sc, M, cam, tgt, n):
        return BB.build_contrast(sc, M, cam, tgt, n, mod)
    mod._contrast = _contrast_r22


def post(sc, variant, shot):
    pass
