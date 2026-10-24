"""Round 27 hook stub (cut_kit_r27; pre-wired by the main process). Shots in the scene module's R27 set call pre(variant, shot,
mod) at the START of build() and post(sc, variant, shot) at the END, after the R22..R26 hooks. No-op = R26 pixels.
The owning sub-agent replaces this docstring with its root-cause rows and exposes ONE module-level switch per row."""


def pre(variant, shot, mod):
    pass


def post(sc, variant, shot):
    return sc
