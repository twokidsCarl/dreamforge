"""Round-15 overlays for the r2_misc shots (R15_ROOT_CAUSE #4 / #5). Loaded after r2_ov_zv14 (name sorts last), so
entries here replace earlier overlays for the same shot.
  B6_12  gap rule now lives in 3D (membrane plane <-> pattern face, in a cut-open notch); the tag follows its anchor
  A2_03  formula band ~85 % opaque on top; NA and k1 tags never on screen together
  B4_10  golf-ball tag in metrology cyan (orange is the CO2 laser only) + "尺寸示意"
  A0_06  NL tag follows the NL node anchor (the globe view now turns west)"""
import importlib.util
import os

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r15mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_m = _mod("r2_ov_misc")
L, fade, track, ease, _anchor = _m.L, _m.fade, _m.track, _m.ease, _m._anchor
CYAN, INK, INK2, VIOLET_L = _m.CYAN, _m.INK, _m.INK2, _m.VIOLET_L


def _clip(p, lo=0.04, hi=0.96):
    return (min(hi, max(lo, p[0])), min(hi, max(lo, p[1])))


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    a = fade(t, 0.25, dur * 0.6)
    L_.leader((0.2, 0.3), (0.42, 0.42), a)
    L_.tag((0.2, 0.3), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, anchor="rm")
    a1 = fade(t, 0.5, dur * 0.6)
    L_.leader((0.2, 0.78), (0.6, 0.7), a1)
    L_.tag((0.2, 0.78), ["掩模（图形面朝上）"], a1, anchor="rm")
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        g = _clip(_anchor("B6_12", t, "gap_mid", (0.6, 0.53)))
        tp = (min(0.9, g[0] + 0.12), min(0.8, g[1] + 0.16))
        L_.leader(tp, g, a2)
        L_.tag(tp, ["间距：膜面 ↔ 图形面", "框边剖开示意"], a2, anchor="lt")
        L_.leader((0.3, 0.3), (0.45, 0.47), a2)
        L_.tag((0.3, 0.3), ["膜厚 13 nm"], a2, anchor="rm")
    return L_.compose(img).convert("RGB")


def ov_A2_03(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    L_.panel((0.14, 0.27, 0.86, 0.55), fade(t, 0.0), alpha=0.86, radius=18)    # R15: opaque band, on top
    terms = [("CD", INK, "能画多细", 0.0), ("=", INK2, None, 0.06), ("k₁", INK2, "工艺因子", 0.12),
             ("·", INK2, None, 0.16), ("λ", VIOLET_L, "光的波长", 0.22), ("/", INK2, None, 0.3),
             ("NA", CYAN, "数值孔径", 0.36)]
    px = int(0.13 * H)
    f = _m.serif_font(px)
    ws = [_m.text_bbox(L_.d, (0, 0), s, f)[2] + 0.03 * W for s, *_ in terms]
    x = 0.5 * W - sum(ws) / 2
    yb = 0.44 * H
    pos = {}
    for (s, col, name, t0), w in zip(terms, ws):
        a = fade(u * dur, t0 * dur, f=0.5)
        _m.draw_text(L_.d, (x + w / 2, yb), s, f, fill=(*col, int(255 * a)), anchor="ms")
        if col in (VIOLET_L, CYAN):
            _m.draw_text(L_.g, (x + w / 2, yb), s, f, fill=(*col, int(160 * a)), anchor="ms")
        if name:
            L_.text(((x + w / 2) / W, 0.49), name, 0.038, col if col != INK2 else INK, a, anchor="mt")
        pos[s] = ((x + w / 2) / W, 0.29)
        x += w
    a1 = fade(t, dur * 0.3)
    bm = _anchor("A2_03", t, "beam", (0.4, 0.2))
    L_.leader(pos["λ"], (min(0.95, max(0.05, bm[0])), max(0.06, min(0.2, bm[1]))), a1, color=VIOLET_L)
    a2 = fade(t, dur * 0.4, dur * 0.68)          # R15: NA tag first, gone before k1 appears
    mr = _anchor("A2_03", t, "mirror", (0.7, 0.8))
    L_.leader((pos["NA"][0], 0.55), (min(0.95, max(0.05, mr[0])), max(0.6, min(0.8, mr[1]))), a2, color=CYAN)
    L_.tag((min(0.8, max(0.05, mr[0])) + 0.02, max(0.6, min(0.8, mr[1])) - 0.02), ["镜子收光的锥角 → NA"], a2,
           size=0.034, accent=CYAN)
    a3 = fade(t, dur * 0.72)
    kx = pos["k₁"][0]
    L_.leader((kx, 0.55), (kx, 0.6), a3, color=INK2)
    L_.tag((max(0.04, kx - 0.04), 0.6), ["k₁ 的物理极限：0.25"], a3, size=0.045, accent=INK2)
    return L_.compose(img).convert("RGB")


def ov_B4_10(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.2, dur * 0.42)
    L_.leader((0.30, 0.68), (0.16, 0.55), a)
    L_.tag((0.30, 0.68), ["地球"], a, anchor="lm")
    pm = track(t, dur, [(0.0, (0.79, 0.33)), (0.28, (0.79, 0.33)), (0.55, (0.5, 0.51)), (0.7, (0.5, 0.51))])
    a2 = fade(t, dur * 0.12, dur * 0.66)
    L_.leader((pm[0] - 0.06, pm[1] + 0.2), (pm[0] - 0.012, pm[1] + 0.03), a2)
    L_.tag((pm[0] - 0.06, pm[1] + 0.2), ["月球", "距地球约 38 万 km"], a2, anchor="rt")
    a3 = fade(t, dur * 0.7)
    L_.leader((0.68, 0.24), (0.52, 0.45), a3, prog=ease((u - 0.7) / 0.1))
    L_.tag((0.68, 0.2), ["高尔夫球", "直径约 4 cm · 尺寸示意"], a3, anchor="la", accent=CYAN)
    return L_.compose(img).convert("RGB")


def ov_A0_06(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.1)
    n = int(round(5100 * ease(min(1.0, (u - 0.02) / 0.8))))
    L_.panel((0.66, 0.05, 0.95, 0.31), a)
    L_.text((0.69, 0.07), f"{n:,}", 0.11, CYAN, a, kind="mono", glow=0.5)
    L_.text((0.69, 0.22), "家供应商", 0.045, INK, a)
    pn = _clip(_anchor("A0_06", t, "nl", (0.49, 0.36)))
    a2 = fade(t, dur * 0.45)
    tp = (max(0.2, min(0.6, pn[0] + 0.1)), max(0.4, pn[1] + 0.12))     # east of the node, open water / land
    L_.leader(tp, pn, a2, color=INK)
    L_.tag(tp, ["荷兰 · 整机总装"], a2, anchor="lt", accent=INK)
    L_.text((0.04, 0.79), "各地区数量据 ASML 年报；光点位置为示意", 0.026, INK2, fade(t, 0.3))
    return L_.compose(img).convert("RGB")


OVERLAYS.update({"B6_12": ov_B6_12, "A2_03": ov_A2_03, "B4_10": ov_B4_10, "A0_06": ov_A0_06})
NO_STORYBOARD_LABELS |= {"B6_12", "A0_06"}
