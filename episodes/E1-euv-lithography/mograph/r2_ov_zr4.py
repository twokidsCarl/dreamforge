"""Round-4 overlays (P1, R3 review fixes). Loaded after the other r2_ov_* modules (name sorts last), so an entry
here replaces the R2/R3 overlay for the same shot. Same layout rules: tags upper right where possible, <= 3
blocks, bottom 15 % free for subtitles."""
from r2_ov_common import CYAN, INK, INK2, VIOLET, Layer, anchor, ease, fade

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()


def ov(sid, no_labels=False):
    def wrap(fn):
        OVERLAYS[sid] = fn
        if no_labels:
            NO_STORYBOARD_LABELS.add(sid)
        return fn
    return wrap


@ov("B1_15")
def contrast(img, t, dur, W, H):
    """H1 fix: name the polished collector next to the plasma (cold mirror vs hot plasma)."""
    L = Layer(W, H)
    c = anchor("B1_15", t, "coll", (0.2, 0.55))
    p = anchor("B1_15", t, "plasma", (0.67, 0.55))
    L.label(c, (0.06, 0.36), ["收集镜", "原子级光滑的多层膜镜面"], fade(t, 0.3), accent=CYAN, size=0.042)
    L.label(p, (min(0.9, p[0] + 0.1), 0.72), ["锡等离子体", "炽热 · 就在镜面跟前"], fade(t, 0.5), accent=VIOLET, size=0.038)
    return L.compose(img)


@ov("B8_03", no_labels=True)
def scan(img, t, dur, W, H):
    """R4: the stages are read off the rulers; arrows sit on the rulers, opposite directions; one 6-degree tag."""
    L = Layer(W, H)
    m = anchor("B8_03", t, "rstage", (0.5, 0.3))
    w = anchor("B8_03", t, "wstage", (0.5, 0.8))
    a = fade(t, 0.5)
    L.arrow((m[0] - 0.1, m[1] - 0.035), (m[0] + 0.12, m[1] - 0.035), a, CYAN, 0.006, 0.026)
    L.label((m[0] + 0.12, m[1]), (0.8, 0.2), ["掩模台 → 行程 8 份", "比晶圆台快 8 倍"], a, size=0.04)
    L.arrow((w[0] + 0.03, w[1] - 0.04), (w[0] - 0.03, w[1] - 0.04), a, CYAN, 0.006, 0.02)
    L.label((w[0] + 0.03, w[1]), (0.8, 0.7), ["← 晶圆台 1 份", "反向移动"], a, size=0.04)
    mk = anchor("B8_03", t, "mask", (0.5, 0.25))
    L.label((mk[0] - 0.012, mk[1] + 0.04), (0.08, 0.2), ["约 6° 斜射掩模", "反射后进入投影物镜"], fade(t, 1.2),
            accent=VIOLET, size=0.038)
    return L.compose(img)


def _base(module, fn_name):
    """Load an earlier overlay function by module file name (for wrappers that add one layer on top)."""
    import importlib.util
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), module + ".py")
    spec = importlib.util.spec_from_file_location(module + "_r4base", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, fn_name)


_B2_08 = _base("r2_ov_source", "ov_B2_08")


@ov("B2_08", no_labels=True)
def clean(img, t, dur, W, H):
    """H6 fix: the grey specks on the dish are named (tin debris deposited on the collector)."""
    img = _B2_08(img, t, dur, W, H)
    L = Layer(W, H)
    d = anchor("B2_08", t, "dep", (0.75, 0.25))
    L.label(d, (0.82, 0.12), ["灰点 = 落在镜面上的锡碎屑", "要被氢清掉"], fade(t, 0.6), accent=CYAN, size=0.036)
    return L.compose(img)
