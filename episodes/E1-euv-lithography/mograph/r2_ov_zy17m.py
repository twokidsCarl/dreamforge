"""Round-17 overlays for the r2_misc shots (R17_ROOT_CAUSE #4). Loaded after r2_ov_zx16* (name sorts later);
entries replace earlier overlays for the same shot.
  A2_03  root cause #4 "objects must read": the formula band is ~72 % opaque (55 % lost the k1 term), 20 % lower and sits in the top
         third, so the single V light path + its mirror highlights below stay visible; leaders re-anchored down
         onto the drawn path (lambda -> the core between PO3 / PO4, NA -> the NA cone)
  A0_06  R16 "计数框压住荷兰总装点": the counter moves to the empty lower-right space, the NL node and its tag stay
         clear of it (>= 60 px); footnote wording fixed to the R15-review text
  B6_12  R16 "掩模标签的引线指向底座边缘": the mask leader lands on the pattern seen inside the frame (anchor)
"""
import importlib.util
import os

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r17mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_m = _mod("r2_ov_misc")
L, fade, track, ease, _anchor = _m.L, _m.fade, _m.track, _m.ease, _m._anchor
CYAN, INK, INK2, VIOLET_L = _m.CYAN, _m.INK, _m.INK2, _m.VIOLET_L


def _clip(p, lo=0.04, hi=0.96):
    return (min(hi, max(lo, p[0])), min(hi, max(lo, p[1])))


def ov_A2_03(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    Y0, Y1 = 0.06, 0.285                                   # R17: top third, 0.225 high (R15/16: 0.27..0.55)
    L_.panel((0.14, Y0, 0.86, Y1), fade(t, 0.0), alpha=0.72, radius=18)
    terms = [("CD", INK, "能画多细", 0.0), ("=", INK2, None, 0.06), ("k₁", INK2, "工艺因子", 0.12),
             ("·", INK2, None, 0.16), ("λ", VIOLET_L, "光的波长", 0.22), ("/", INK2, None, 0.3),
             ("NA", CYAN, "数值孔径", 0.36)]
    px = int(0.12 * H)
    f = _m.serif_font(px)
    ws = [_m.text_bbox(L_.d, (0, 0), s, f)[2] + 0.03 * W for s, *_ in terms]
    x = 0.5 * W - sum(ws) / 2
    yb = 0.205 * H
    pos = {}
    for (s, col, name, t0), w in zip(terms, ws):
        a = fade(u * dur, t0 * dur, f=0.5)
        _m.draw_text(L_.d, (x + w / 2, yb), s, f, fill=(*col, int(255 * a)), anchor="ms")
        if col in (VIOLET_L, CYAN):
            _m.draw_text(L_.g, (x + w / 2, yb), s, f, fill=(*col, int(160 * a)), anchor="ms")
        if name:
            L_.text(((x + w / 2) / W, 0.222), name, 0.036, col if col != INK2 else INK, a, anchor="mt")
        pos[s] = ((x + w / 2) / W, Y1)
        x += w
    a1 = fade(t, dur * 0.3)
    bm = _clip(_anchor("A2_03", t, "beam", (0.6, 0.5)), 0.05, 0.92)
    L_.leader(pos["λ"], (bm[0], max(Y1 + 0.06, bm[1])), a1, color=VIOLET_L)
    a2 = fade(t, dur * 0.4, dur * 0.68)          # R15: NA tag first, gone before k1 appears
    mr = _anchor("A2_03", t, "mirror", (0.7, 0.8))
    mp = (min(0.95, max(0.05, mr[0])), max(0.45, min(0.8, mr[1])))
    L_.leader(pos["NA"], mp, a2, color=CYAN)
    L_.tag((min(0.8, mp[0]) + 0.02, mp[1] - 0.02), ["镜子收光的锥角 → NA"], a2, size=0.034, accent=CYAN)
    a3 = fade(t, dur * 0.72)
    kx = pos["k₁"][0]
    L_.leader((kx, Y1), (kx, Y1 + 0.05), a3, color=INK2)
    L_.tag((max(0.04, kx - 0.04), Y1 + 0.05), ["k₁ 的物理极限：0.25"], a3, size=0.042, accent=INK2)
    return L_.compose(img).convert("RGB")


def ov_A0_06(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.1)
    n = int(round(5100 * ease(min(1.0, (u - 0.02) / 0.8))))
    L_.panel((0.775, 0.6, 0.98, 0.83), a)
    L_.text((0.795, 0.615), f"{n:,}", 0.085, CYAN, a, kind="mono", glow=0.5)
    L_.text((0.795, 0.735), "家供应商", 0.04, INK, a)
    pn = _clip(_anchor("A0_06", t, "nl", (0.49, 0.36)))
    a2 = fade(t, dur * 0.45)
    tp = (max(0.2, min(0.6, pn[0] + 0.1)), max(0.4, pn[1] + 0.12))
    L_.leader(tp, pn, a2, color=INK)
    L_.tag(tp, ["荷兰 · 整机总装"], a2, anchor="lt", accent=INK)
    L_.text((0.04, 0.79), "数据来源：ASML 年报；光点位置为示意", 0.026, INK2, fade(t, 0.3))
    return L_.compose(img).convert("RGB")


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    a = fade(t, 0.25, dur * 0.6)
    L_.leader((0.2, 0.3), (0.42, 0.42), a)
    L_.tag((0.2, 0.3), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, anchor="rm")
    a1 = fade(t, 0.5, dur * 0.6)
    pt = _clip(_anchor("B6_12", t, "pattern", (0.55, 0.62)))
    L_.leader((0.2, 0.78), pt, a1)
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


OVERLAYS.update({"A2_03": ov_A2_03, "A0_06": ov_A0_06, "B6_12": ov_B6_12})
NO_STORYBOARD_LABELS |= {"B6_12", "A0_06"}
