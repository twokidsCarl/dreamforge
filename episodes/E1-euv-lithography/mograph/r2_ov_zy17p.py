"""Round-17 overlay for A0_03 (root cause 6: counts must match the narration). Loads after r2_ov_zx16p (name sorts
last), so it replaces earlier A0_03 overlays.

R16 review: the wide plate showed far more than 250 crates, ~10 ULDs and 1-2 trucks, so the leader numbers did not
match what was on screen; labels jumped around the frame. R17: the R15 close documentary plate stays as the "real
thing" and a flat infographic counter panel, fixed top-right, stacks the chain layer by layer with countable
pictograms (BRIEF: 数量链条用扁平信息图层层堆叠):
  250 crates  = 10 x 25 grid in 5 cyan group boxes of 50
  43 ULDs     = 4 boxed groups of 10 + 3
  freighters  = 3 jets ("几架货机")
  20 trucks   = one row of 20
Each layer fills in icon by icon while its number counts up, and stays on screen (earlier steps remain visible).
No leaders: the numbers live only in the panel (review R15: information shown twice)."""
from PIL import ImageDraw

from r2_ov_common import Layer, ease, fade, CYAN, INK, INK2, PANEL

OVERLAYS = {}
NO_STORYBOARD_LABELS = {"A0_03"}

# (t_start, t_full) per layer, synced to the narration (250 箱 … 43 个集装箱 … 几架货机 … 20 辆卡车)
T_CRATE, T_ULD, T_JET, T_TRUCK = (0.5, 2.4), (3.3, 5.0), (6.3, 7.0), (7.9, 9.0)


def _prog(t, span):
    return ease((t - span[0]) / (span[1] - span[0]))


def _crate(d, x, y, c, a):
    d.rectangle((x, y, x + c - 2, y + c - 2), fill=(214, 220, 230, int(235 * a)), outline=(120, 130, 148, int(255 * a)))
    d.line((x + 1, y + 1, x + c - 3, y + c - 3), fill=(150, 158, 172, int(160 * a)))


def _uld(d, x, y, w, h, a):
    # LD3-style contour: flat top, one slanted lower corner
    pts = [(x, y), (x + w, y), (x + w, y + h * 0.55), (x + w * 0.72, y + h), (x, y + h)]
    d.polygon(pts, fill=(176, 186, 200, int(235 * a)), outline=(96, 108, 126, int(255 * a)))
    for k in (0.33, 0.66):
        d.line((x + w * k, y + 2, x + w * k, y + h - 2), fill=(110, 120, 138, int(200 * a)))


def _jet(d, cx, cy, s, a):
    col = (226, 230, 238, int(240 * a))
    d.polygon([(cx - 1.6 * s, cy - 0.16 * s), (cx + 1.5 * s, cy - 0.16 * s), (cx + 1.75 * s, cy),
               (cx + 1.5 * s, cy + 0.16 * s), (cx - 1.6 * s, cy + 0.16 * s)], fill=col)          # fuselage
    d.polygon([(cx - 0.1 * s, cy), (cx + 0.5 * s, cy), (cx - 0.3 * s, cy - 1.0 * s), (cx - 0.65 * s, cy - 1.0 * s)], fill=col)
    d.polygon([(cx - 0.1 * s, cy), (cx + 0.5 * s, cy), (cx - 0.3 * s, cy + 1.0 * s), (cx - 0.65 * s, cy + 1.0 * s)], fill=col)
    d.polygon([(cx - 1.35 * s, cy), (cx - 1.1 * s, cy), (cx - 1.45 * s, cy - 0.45 * s), (cx - 1.6 * s, cy - 0.45 * s)], fill=col)
    d.polygon([(cx - 1.35 * s, cy), (cx - 1.1 * s, cy), (cx - 1.45 * s, cy + 0.45 * s), (cx - 1.6 * s, cy + 0.45 * s)], fill=col)


def _truck(d, x, y, w, h, a):
    d.rectangle((x, y, x + w * 0.72, y + h), fill=(222, 226, 234, int(240 * a)), outline=(110, 120, 138, int(255 * a)))
    d.rectangle((x + w * 0.76, y + h * 0.3, x + w, y + h), fill=(170, 180, 196, int(240 * a)))
    d.rectangle((x + w * 0.80, y + h * 0.38, x + w * 0.95, y + h * 0.6), fill=(60, 70, 90, int(240 * a)))


def crates(img, t, dur, W, H):
    L = Layer(W, H)
    a0 = fade(t, 0.3, None, 0.4)
    if a0 <= 0:
        return img
    d = L.d
    s = H / 540.0
    c = int(round(11 * s))                       # crate cell
    gw = 5 * c                                   # group width (5 cols x 10 rows = 50)
    gap = int(round(7 * s))
    pw = 5 * gw + 4 * gap + int(30 * s)          # panel width
    x0 = W - pw - int(0.018 * W)
    y0 = int(0.035 * H)
    rows = []                                    # (height, draw fn)
    hdr = int(round(0.040 * H * 1.5))

    def head(y, num, unit, a):
        L.text(((x0 + 15 * s) / W, y / H), num, 0.040, CYAN, a, shadow=False)
        b = L.bbox(((x0 + 15 * s) / W, y / H), num, 0.040)
        L.text(((b[2] + 6 * s) / W, (y + 3 * s) / H), unit, 0.032, INK, a, shadow=False)

    # layer heights
    h_crate = hdr + 10 * c + int(10 * s)
    h_uld = hdr + int(2 * 19 * s) + int(12 * s)
    h_jet = hdr + int(40 * s)
    h_truck = hdr + int(26 * s)
    vis = [(h_crate, T_CRATE), (h_uld, T_ULD), (h_jet, T_JET), (h_truck, T_TRUCK)]
    arrow_h = int(14 * s)
    total = 0
    for h_, span in vis:
        if t >= span[0] - 0.3:
            total += h_ + (arrow_h if total else 0)
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + total + int(10 * s)), radius=int(6 * s), fill=(*PANEL, int(195 * a0)))
    y = y0 + int(8 * s)

    def arrow(yy, a):
        cx = x0 + pw / 2
        d.polygon([(cx - 6 * s, yy + 2 * s), (cx + 6 * s, yy + 2 * s), (cx, yy + arrow_h - 2 * s)], fill=(*CYAN, int(200 * a)))

    # 1) crates: 10 x 25 in 5 cyan groups of 50
    p = _prog(t, T_CRATE)
    n = int(round(250 * p))
    head(y, f"{n}", "个板条箱 · 10 × 25", a0)
    gy = y + hdr
    for g in range(5):
        gx = x0 + int(15 * s) + g * (gw + gap)
        d.rectangle((gx - 2, gy - 2, gx + gw + 1, gy + 10 * c + 1), outline=(*CYAN, int(230 * a0)), width=max(1, int(1.4 * s)))
        for k in range(50):
            idx = g * 50 + k
            if idx >= n:
                break
            r_, c_ = divmod(k, 5)
            _crate(d, gx + c_ * c, gy + r_ * c, c, a0)
    y += h_crate
    # 2) ULDs: 4 boxed groups 10 / 10 / 10 / 10 + 3
    if t >= T_ULD[0] - 0.3:
        a = fade(t, T_ULD[0] - 0.3, None, 0.3) * a0
        arrow(y, a); y += arrow_h
        n = int(round(43 * _prog(t, T_ULD)))
        head(y, f"{n}", "个航空集装箱", a)
        uw, uh = int(10 * s), int(16 * s)        # each group = 2 rows x 5 ULDs (the last group: 3)
        gy = y + hdr
        gx = x0 + int(15 * s)
        cnt = 0
        for gn in (10, 10, 10, 10, 3):
            cols = min(5, gn)
            bw = cols * (uw + 2) + 1
            bh = (2 if gn > 5 else 1) * (uh + 3) + 1
            d.rectangle((gx - 2, gy - 2, gx + bw, gy + bh), outline=(*CYAN, int(230 * a)), width=max(1, int(1.4 * s)))
            for k in range(gn):
                if cnt >= n:
                    break
                r_, c_ = divmod(k, 5)
                _uld(d, gx + 1 + c_ * (uw + 2), gy + 1 + r_ * (uh + 3), uw, uh, a)
                cnt += 1
            gx += bw + gap
        y += h_uld
    # 3) freighters
    if t >= T_JET[0] - 0.3:
        a = fade(t, T_JET[0] - 0.3, None, 0.3) * a0
        arrow(y, a); y += arrow_h
        head(y, "几架", "货机", a)
        k = int(round(3 * _prog(t, T_JET) + 0.49))
        for i in range(min(3, max(1, k))):
            _jet(d, x0 + int(45 * s) + i * int(90 * s), y + hdr + int(12 * s), 18 * s, a)
        y += h_jet
    # 4) trucks: one row of 20
    if t >= T_TRUCK[0] - 0.3:
        a = fade(t, T_TRUCK[0] - 0.3, None, 0.3) * a0
        arrow(y, a); y += arrow_h
        n = int(round(20 * _prog(t, T_TRUCK)))
        head(y, f"{n}", "辆卡车", a)
        tw = (pw - int(30 * s)) / 20.0
        d.rectangle((x0 + int(15 * s) - 2, y + hdr - 2, x0 + pw - int(15 * s) + 1, y + hdr + int(16 * s) + 2),
                    outline=(*CYAN, int(230 * a)), width=max(1, int(1.4 * s)))
        for k in range(n):
            _truck(d, x0 + int(15 * s) + k * tw + 1, y + hdr, tw - 3, int(16 * s), a)
        y += h_truck
    return L.compose(img)


OVERLAYS["A0_03"] = crates
