"""Round-6 overlays (P1, R5 review fixes). Loaded after r2_ov_zr5 (name sorts last), so an entry here replaces
earlier overlays for the same shot. Layout rules unchanged: <= 3 blocks, bottom 15 % free for subtitles."""
from r2_ov_common import CYAN, INK, INK2, VIOLET, FPS, Layer, anchor, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


def _base(module, fn_name):
    import importlib.util
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), module + ".py")
    spec = importlib.util.spec_from_file_location(module + "_r6base", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, fn_name)


_B2_08 = _base("r2_ov_source", "ov_B2_08")


@ov("B2_08", no_labels=True)
def clean(img, t, dur, W, H):
    """R6: the magnifier hangs on a deposit patch of the (now whole, recognisable) collector dish; the SnH4
    streamlines in the render end at the pump port, which gets one tag."""
    d = anchor("B2_08", t, "dep", (0.5, 0.3))
    img = _B2_08(img, t, dur, W, H, anchor_pt=d, center=(0.2, 0.36), panel_xy=(0.05, 0.66))
    L = Layer(W, H)
    p = anchor("B2_08", t, "pump", (0.85, 0.25))
    p = (min(0.96, max(0.55, p[0])), min(0.6, max(0.08, p[1])))
    L.label(p, (0.66, 0.05), ["SnH₄ 气体 → 抽气泵口", "深色斑点 = 镜面上的锡沉积"], fade(t, 0.8), accent=CYAN, size=0.036)
    return L.compose(img)
