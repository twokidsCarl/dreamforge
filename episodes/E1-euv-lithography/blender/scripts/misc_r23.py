"""R23 hook module for the misc group (B6_12 / B4_10 / B8_17), owned by the misc sub-agent.
Dispatches per shot to misc_r23_<shot>.py helpers. Remove a shot from r2_misc.R23_MISC -> exact R22 pixels.
Rows (R23_ROOT_CAUSE.md): B6_12 rows 1 + 2, B4_10 row 6, B8_17 row 5."""
import importlib

_MODS = {"B6_12": "misc_r23_b612", "B4_10": "misc_r23_b410", "B8_17": "misc_r23_b817"}


def _m(shot):
    nm = _MODS.get(shot)
    if nm is None:
        return None
    try:
        return importlib.import_module(nm)
    except ModuleNotFoundError:
        return None


def pre(variant, shot, mod):
    m = _m(shot)
    if m is not None and hasattr(m, "pre"):
        m.pre(mod)


def post(sc, variant, shot):
    m = _m(shot)
    if m is not None and hasattr(m, "post"):
        m.post(sc)
