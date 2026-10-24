"""R23 hook module, panel agent (R23_ROOT_CAUSE.md rows 2 / 4). Called from THREE scene modules:
r2_plates (A0_03), r2_source (B1_18), r2_misc (A0_06) -> dispatch on shot. Shots outside these ids: no-op."""
import importlib


def _helper(shot):
    name = {"A0_03": "panel_r23_crates", "B1_18": "panel_r23_spectrum", "A0_06": "panel_r23_globe"}.get(shot)
    if not name:
        return None
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name == name:
            return None
        raise


def pre(variant, shot, mod):
    h = _helper(shot)
    if h is not None and hasattr(h, "pre"):
        h.pre(variant, shot, mod)


def post(sc, variant, shot):
    h = _helper(shot)
    if h is not None and hasattr(h, "post"):
        h.post(sc, variant, shot)
