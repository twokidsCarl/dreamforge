"""Round-18 overlays for the r2_misc shots. Loaded after r2_ov_zy17m (name sorts later); entries replace earlier
overlays for the same shot.
  A0_06  root cause #3 / #5: the counter + source become ONE block in the top-right corner (<= 3 lines); the
         bottom-left footnote is merged into it; NL tag kept
  A2_03  root cause #2: the NA leader now lands on the cone angle theta at the wafer (the new soft NA cone);
         the lambda leader follows the moved "beam" anchor (the single PO4 -> PO5 fold)
  B4_10  root cause #5: subtitle on a visible dark bar (the 55 % house bar vanished on the star field); the
         storyboard label spanning 75 % of the top is replaced by a top-right block <= 40 % wide:
         big "< 0.1 nrad" + one small line (+ source)
  B4_07  root cause #5: labels top right (mirror name, then the 40-pair tag), magnifier unchanged
  B6_12  root cause #5: <= 2 labels per beat, top right; "膜厚 13 nm" leader ends on the film cross-section at
         the cut frame edge (gap_top anchor)
"""
import importlib.util
import os
import sys

OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(module):
    spec = importlib.util.spec_from_file_location(module + "_r18mbase", os.path.join(_HERE, module + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_m = _mod("r2_ov_misc")
_z17 = _mod("r2_ov_zy17m")
L, fade, track, ease, _anchor = _m.L, _m.fade, _m.track, _m.ease, _m._anchor
CYAN, INK, INK2, VIOLET_L = _m.CYAN, _m.INK, _m.INK2, _m.VIOLET_L


def _clip(p, lo=0.04, hi=0.96):
    return (min(hi, max(lo, p[0])), min(hi, max(lo, p[1])))


def _tl(L_, p, lines, a, target, prog=1.0, **kw):
    """Top-right tag + a leader that starts on the tag's left edge and ends on the 3D target."""
    if a <= 0:
        return
    box = L_.tag(p, lines, a, anchor="rt", **kw)
    if box:
        L_.leader((box[0] / L_.W, (box[1] + box[3]) / 2 / L_.H), target, a, prog=prog)


def ov_A0_06(img, t, dur, W, H):
    L_ = L(W, H)
    u = t / dur
    a = fade(t, 0.1)
    n = int(round(5100 * ease(min(1.0, (u - 0.02) / 0.8))))
    L_.panel((0.745, 0.045, 0.975, 0.285), a)
    L_.text((0.765, 0.06), f"{n:,}", 0.085, CYAN, a, kind="mono", glow=0.5)
    L_.text((0.765, 0.165), "家供应商", 0.04, INK, a)
    L_.text((0.765, 0.235), "来源：ASML 年报 · 光点为示意", 0.024, INK2, a)
    pn = _clip(_anchor("A0_06", t, "nl", (0.49, 0.36)))
    a2 = fade(t, dur * 0.45)
    tp = (max(0.2, min(0.6, pn[0] + 0.1)), max(0.4, pn[1] + 0.12))
    L_.leader(tp, pn, a2, color=INK)
    L_.tag(tp, ["荷兰 · 整机总装"], a2, anchor="lt", accent=INK)
    return L_.compose(img).convert("RGB")


_anchor_orig = _z17._anchor


def ov_A2_03(img, t, dur, W, H):
    """R17 layout; only the NA leader target changes: the 'mirror' anchor is answered with the cone angle theta."""
    def _a(shot, t_, name, fb):
        if shot == "A2_03" and name == "mirror":
            return _anchor_orig(shot, t_, "theta", fb)
        return _anchor_orig(shot, t_, name, fb)
    _z17._anchor = _a
    try:
        img = _z17.ov_A2_03(img, t, dur, W, H)
    finally:
        _z17._anchor = _anchor_orig
    return _sub_bar(img, t, "A2_03", W, H)


def _sub_bar(img, t, sid, W, H):
    """A visible dark bar behind the subtitle (drawn before compose's own subtitle + 55 % bar)."""
    try:
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "shared", "tools"))
        from paths import timed_shots
        import edit_film as EF
        s = next(s for s in timed_shots() if s["id"] == sid)
        cue = next((c for c in s.get("subs") or [] if c["start"] <= t < c["end"]), None)
        if not cue:
            return img
        from PIL import Image, ImageDraw
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        size = int(H * 0.043)
        f = EF.font(size)
        cx, cy = W / 2, H * 0.905
        l, tp, r, b = EF.text_bbox(d, (cx, cy), cue["text"], f, anchor="mm")
        px, py = 0.6 * size, 0.28 * size
        d.rounded_rectangle((l - px, min(tp, cy - size / 2) - py, r + px, max(b, cy + size / 2) + py),
                            radius=max(1, round(4 * H / 1080)), fill=(18, 24, 38, 235),
                            outline=(78, 90, 116, 200), width=max(1, round(H / 540)))
        return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    except Exception:
        return img


_b410_base = None


def _b410_no_golf(img, t, dur, W, H, _golf=False):
    """r2_ov_zw15m.ov_B4_10 (Earth + Moon tags) without its golf-ball tag (redrawn top right)."""
    L_ = L(W, H)
    a = fade(t, 0.2, dur * 0.42)
    L_.leader((0.30, 0.68), (0.16, 0.55), a)
    L_.tag((0.30, 0.68), ["地球"], a, anchor="lm")
    pm = track(t, dur, [(0.0, (0.79, 0.33)), (0.28, (0.79, 0.33)), (0.55, (0.5, 0.51)), (0.7, (0.5, 0.51))])
    a2 = fade(t, dur * 0.12, dur * 0.66)
    L_.leader((pm[0] - 0.06, pm[1] + 0.2), (pm[0] - 0.012, pm[1] + 0.03), a2)
    L_.tag((pm[0] - 0.06, pm[1] + 0.2), ["月球", "距地球约 38 万 km"], a2, anchor="rt")
    return L_.compose(img).convert("RGB")


def ov_B4_10(img, t, dur, W, H):
    global _b410_base
    if _b410_base is None:
        _b410_base = _b410_no_golf
    img = _b410_base(img, t, dur, W, H, _golf=False)
    L_ = L(W, H)
    u = t / dur
    a3 = fade(t, dur * 0.7)                       # golf-ball tag in the top-right corner (house rule), leader to the ball
    _tl(L_, (0.975, 0.035), ["高尔夫球", "直径约 4 cm · 尺寸示意"], a3, (0.52, 0.45), prog=ease((u - 0.7) / 0.1))
    a = fade(t, 10 / 24, dur * 0.68)
    if a > 0:
        L_.panel((0.6, 0.045, 0.975, 0.235), a)
        L_.text((0.62, 0.06), "< 0.1 nrad", 0.075, CYAN, a, kind="mono", glow=0.3)
        L_.text((0.62, 0.155), "蔡司比喻：从地球打中月球上的一颗高尔夫球", 0.026, INK, a)
        L_.text((0.62, 0.198), "来源：EUVL 研讨会", 0.021, INK2, a)
    img = L_.compose(img).convert("RGB")
    return _sub_bar(img, t, "B4_10", W, H)


def ov_B4_07(img, t, dur, W, H):
    u = t / dur
    a = ease((u - 0.42) / 0.14)
    r = 0.15 + 0.17 * ease((u - 0.42) / 0.3)
    import r2_ov_common as RC
    fb = track(t, dur, [(0.42, (0.3, 0.6)), (0.55, (0.3, 0.58)), (1.0, (0.3, 0.2))])
    cand = [RC.anchor("B4_07", t, f"coat{k}", None) for k in (2, 1, 3, 0)]
    cand = [c for c in cand if c and 0.06 < c[0] < 0.6 and 0.08 < c[1] < 0.8]
    an = cand[0] if cand else fb
    if a > 0:
        size = int(2 * r * H)
        img = _m.magnifier(img, (0.66, 0.47), r, _m._tem_panel(max(64, size)), a, anchor=an)
    L_ = L(W, H)
    a2 = fade(t, dur * 0.72)
    L_.tag((0.975, 0.035), ["钼 / 硅 × 40 对 · 每对约 7 nm", "只在镜面最顶层 · 总厚约 0.3 μm"], a2, size=0.04, anchor="rt")
    a0 = fade(t, 0.2, dur * 0.45)
    _tl(L_, (0.975, 0.035), ["多层膜反射镜"], a0, (0.34, 0.56), size=0.042)
    return L_.compose(img).convert("RGB")


def ov_B6_12(img, t, dur, W, H):
    L_ = L(W, H)
    # beat 1 (to 60 %): film + mask, stacked in the top-right corner
    a = fade(t, 0.25, dur * 0.6)
    _tl(L_, (0.975, 0.035), ["保护膜 pellicle", "张在金属框上，几乎透明"], a, _clip(_anchor("B6_12", t, "film", (0.42, 0.42))))
    a1 = fade(t, 0.5, dur * 0.6)
    _tl(L_, (0.975, 0.2), ["掩模（图形面朝上）"], a1, _clip(_anchor("B6_12", t, "pattern", (0.55, 0.62))))
    # beat 2: film thickness (leader onto the film cross-section at the cut frame edge) + gap
    a2 = fade(t, dur * 0.6)
    if a2 > 0:
        ft = _clip(_anchor("B6_12", t, "gap_top", (0.6, 0.5)))
        _tl(L_, (0.975, 0.035), ["膜厚 13 nm"], a2, ft)
        g = _clip(_anchor("B6_12", t, "gap_mid", (0.6, 0.53)))
        _tl(L_, (0.975, 0.2), ["间距：膜面 ↔ 图形面", "框边剖开示意"], a2, (g[0] + 0.006, g[1]))
    return L_.compose(img).convert("RGB")


OVERLAYS.update({"A0_06": ov_A0_06, "A2_03": ov_A2_03, "B4_10": ov_B4_10, "B4_07": ov_B4_07, "B6_12": ov_B6_12})
NO_STORYBOARD_LABELS |= {"A0_06", "B4_10", "B4_07", "B6_12"}
