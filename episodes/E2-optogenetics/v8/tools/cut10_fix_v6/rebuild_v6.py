#!/usr/bin/env python3
"""E2 Cut10 fix_v6 — re-render film 0:00 → 4:27.875 as one VO-locked timeline, keep old tail.

Every overlay is keyed to captions.ass cue times (film time). Plates are Goodsell gens; procedural
work is ONLY overlay (ions / charges / glows / cards) tracked through the same clamped camera.
Old fix_v5 `render_spike_animated` (flat lipid dots + square channel + Vm bar) is NOT used.

usage: rebuild_v6.py [render [names..]] [mux]
"""
from __future__ import annotations
import json, math, subprocess, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from v6lib import *  # noqa

HERE = Path(__file__).parent
OUT = HERE.parent
SEGS_OLD = OUT / 'segs'
SEG6 = HERE / 'segs'
PL = HERE / 'plates'
WORK = HERE / 'work'
BASE = Path('/workspace/e2work/lowres_cut/E2_lowres_full.mp4')
FILM_DUR = 865.04
plan = json.loads((OUT / 'plan.json').read_text())
SEG = {s['name']: (s['t0'], s['t1']) for s in plan['segments']}

# old chain: sB started at old frame 4412; its pure-oocyte frame 2017 is where we hand back
OLD_SB_START_F = 4412
OLD_SB_HANDOFF = 2017
END_F = OLD_SB_START_F + OLD_SB_HANDOFF          # 6429 frames = 267.875 s
B0 = 183.76

# ------------------------------------------------------------------ lazy plates
_P = {}


def P(key):
    if key in _P:
        return _P[key]
    spec = {
        'open': (GEN / 'sf01c_open_bg.png', (0, 0.025, 1, 1), 1.3),
        'crowd': (GEN / 'sf02c_crowd.png', None, 1.35),
        'microbe': (GEN / 'sf03e_microbes.png', None, 1.5),
        'crick': (PL / 'crick_v6.png', None, 1.0),
        'laur': (PL / 'laureates_v6.png', None, 1.0),
        'neuron': (GEN / 'sf06t_neuron.png', None, 1.35),
        'brain': (GEN / 'sf07j_brain.png', None, 1.35),
        'spike': (GEN / 'sf08e_relay.png', (0.44, 0.12, 1.0, 0.88), 1.35),
        'relay': (GEN / 'sf08e_relay.png', None, 1.6),
        'relayd': (GEN / 'sf08d_relay.png', None, 1.6),
        'chr2': (GEN / 'sf09e_chr2.png', None, 1.4),
        'orexin': (GEN / 'sf10_orexin.png', None, 1.3),
        'msleep': (GEN / 'c9_msleep.png', None, 1.25),
        'mwake': (GEN / 'c9_mouseA2_still.png', None, 1.25),
    }[key]
    _P[key] = Plate(spec[0], spec[1], spec[2])
    return _P[key]


_M = {}


def MASK(key):
    if key in _M:
        return _M[key]
    if key == 'crowd_or':
        m = hue_mask(P('crowd'), 5, 24, smin=120, vmin=150, blur=7)
    elif key == 'microbe_rods':
        m = hue_mask(P('microbe'), 125, 160, smin=70, vmin=60, blur=7, region=(0.05, 0.25, 0.40, 0.70))
    elif key == 'orexin_cy':
        m = hue_mask(P('orexin'), 82, 102, smin=70, vmin=150, blur=9, region=(0.22, 0.05, 0.80, 0.85))
    elif key == 'relay_squig':
        m = hue_mask(P('relay'), 85, 110, smin=40, vmin=200, blur=5, region=(0.0, 0.05, 0.16, 0.33))
    elif key == 'relay_pump':
        m = hue_mask(P('relay'), 120, 150, smin=60, vmin=90, blur=7, region=(0.06, 0.28, 0.17, 0.57))
    elif key == 'chr2_beam':
        m = hue_mask(P('chr2'), 95, 115, smin=60, vmin=140, blur=21, region=(0.0, 0.0, 0.55, 0.36))
    elif key == 'chr2_pore':
        m = hue_mask(P('chr2'), 85, 105, smin=80, vmin=170, blur=5, region=(0.40, 0.33, 0.60, 0.64))
        pc = disc_mask(P('chr2'), [(0.435, 0.49), (0.555, 0.49)], 0.03, 0.9)
        m = m * np.clip(pc * 2, 0, 1)
    _M[key] = m
    return m


_S = {}


def SPR(key):
    if key in _S:
        return _S[key]
    if key.startswith('card_') or key in ('br_patch', 'lockup_1280'):
        s = pil_rgba(Image.open(PL / f'{key}.png'))
    elif key == 'oocyte':
        im = cv2.cvtColor(cv2.imread(str(PL / 'oocyte_f2017.png')), cv2.COLOR_BGR2RGB)
        s = np.dstack([im.astype(np.float32) / 255, np.ones(im.shape[:2], np.float32)])
    _S[key] = s
    return s


def scaled(spr, k):
    h, w = spr.shape[:2]
    return cv2.resize(spr, (max(1, int(w * k)), max(1, int(h * k))), interpolation=cv2.INTER_AREA)


def circle_crop(img_rgb, cx, cy, r, out_r, ring=GOLD):
    """circular PIP from a plate image (fractions)."""
    h, w = img_rgb.shape[:2]
    x0, y0 = int(cx * w - r), int(cy * h - r)
    sub = img_rgb[max(0, y0):y0 + 2 * r, max(0, x0):x0 + 2 * r]
    sub = cv2.resize(sub, (2 * out_r, 2 * out_r), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:2 * out_r, 0:2 * out_r].astype(np.float32)
    d = np.sqrt((xx - out_r) ** 2 + (yy - out_r) ** 2)
    a = np.clip(out_r - 1 - d, 0, 1)
    spr = np.dstack([sub, a])
    ringm = np.clip(1 - np.abs(d - (out_r - 3)) / 2.2, 0, 1)
    c = np.asarray(ring, np.float32) / 255
    spr[..., :3] = spr[..., :3] * (1 - ringm[..., None]) + c * ringm[..., None]
    spr[..., 3] = np.maximum(spr[..., 3], ringm)
    return spr


@lru_cache(maxsize=64)
def tag_sprite(text, color=CREAM, size=20, accent=MINT):
    f = font(size, True)
    tw = int(f.getlength(text.replace('^{', '').replace('_{', '').replace('}', ''))) + 26
    im = Image.new('RGBA', (tw, size + 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, size + 17), radius=6, fill=(11, 16, 34, 205), outline=tuple(accent) + (220,), width=2)
    draw_rich(d, (13, 5), text, size, tuple(color) + (255,), bold=True)
    return pil_rgba(im)


def tag(rgb, text, x, y, al, accent=MINT, size=20):
    if al > 0:
        paste(rgb, tag_sprite(text, CREAM, size, tuple(accent)), x, y, al)
    return rgb


def leader(rgb, a, b, color, al, width=2, dashed=False, arrow=False):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    c = col(color, al)
    if dashed:
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 14)
        for i in range(0, n, 2):
            p0 = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            p1 = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
            cv2.line(ov, tuple(map(int, p0)), tuple(map(int, p1)), c, width, cv2.LINE_AA)
    else:
        cv2.line(ov, tuple(map(int, a)), tuple(map(int, b)), c, width, cv2.LINE_AA)
    if arrow:
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        L = 16
        p1 = (b[0] - L * math.cos(ang - 0.45), b[1] - L * math.sin(ang - 0.45))
        p2 = (b[0] - L * math.cos(ang + 0.45), b[1] - L * math.sin(ang + 0.45))
        cv2.fillConvexPoly(ov, np.array([b, p1, p2], np.int32), c, cv2.LINE_AA)
    return comp(rgb, ov)


def ring(rgb, x, y, r, color, al, width=3):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    cv2.circle(ov, (int(x), int(y)), int(r), col(color, al), width, cv2.LINE_AA)
    return comp(rgb, ov)


def charge_glyph(rgb, x, y, sign, al, color, size=26):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    c = col(color, al)
    s = size // 2
    cv2.line(ov, (int(x - s), int(y)), (int(x + s), int(y)), c, 4, cv2.LINE_AA)
    if sign > 0:
        cv2.line(ov, (int(x), int(y - s)), (int(x), int(y + s)), c, 4, cv2.LINE_AA)
    return comp(rgb, ov)


def charges_row(rgb, view, xs, fy, sign, al, color):
    for fx in xs:
        x, y = view.pt(fx, fy)
        rgb = charge_glyph(rgb, x, y, sign, al, color)
    return rgb


def mix(a, b, k):
    return a * (1 - k) + b * k


def dim_all(rgb, amt):
    return rgb * (1 - amt) + np.array([0.04, 0.06, 0.13], np.float32) * amt


# ------------------------------------------------------------------ HUD panels
def panel_bg(rgb, x0, y0, x1, y1, al, accent=GOLD):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    cv2.rectangle(ov, (x0, y0), (x1, y1), col(INK, 0.86 * al), -1, cv2.LINE_AA)
    cv2.rectangle(ov, (x0, y0), (x1, y1), col(accent, 0.9 * al), 2, cv2.LINE_AA)
    return comp(rgb, ov)


def ap_shape(u):
    """membrane potential in mV for one spike, u in [0,1] (slowed display)."""
    if u < 0.15:
        return -70 + 15 * (u / 0.15)
    if u < 0.32:
        return -55 + 85 * ease((u - 0.15) / 0.17)
    if u < 0.62:
        return 30 - 110 * ease((u - 0.32) / 0.30)
    return -80 + 10 * ease((u - 0.62) / 0.38)


def vm_panel(rgb, t, al, spike_t0, spike_dur, x0=880, y0=34, w=360, h=210):
    """锋电位 knowledge panel: trace drawn in sync with the ions below."""
    if al <= 0:
        return rgb
    rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, al, AMBER)
    paste(rgb, text_sprite('锋电位', 30, AMBER), x0 + 18, y0 + 4, al, center=False)
    paste(rgb, text_sprite('膜电位 V_m（mV）', 16, CREAM, False), x0 + 128, y0 + 16, al, center=False)
    ov = overlay_layer()
    gx0, gx1, gy0, gy1 = x0 + 50, x0 + w - 16, y0 + 62, y0 + h - 34

    def Y(mv):
        return gy1 - (mv + 90) / 130 * (gy1 - gy0)
    for mv, lab in ((30, '+30'), (0, '0'), (-70, '−70')):
        cv2.line(ov, (gx0, int(Y(mv))), (gx1, int(Y(mv))), col((90, 110, 150), 0.5 * al), 1, cv2.LINE_AA)
    # time window: 3 s ending at now; trace = rest except during spike
    span = 3.0
    pts = []
    for i in range(160):
        tt = t - span + span * i / 159
        u = (tt - spike_t0) / spike_dur
        mv = ap_shape(u) if 0 <= u <= 1 else -70
        pts.append((gx0 + (gx1 - gx0) * i / 159, Y(mv)))
    for i in range(159):
        cv2.line(ov, tuple(map(int, pts[i])), tuple(map(int, pts[i + 1])), col(AMBER, al), 3, cv2.LINE_AA)
    cv2.circle(ov, tuple(map(int, pts[-1])), 5, col(YELLOW, al), -1, cv2.LINE_AA)
    rgb = comp(rgb, ov)
    for mv, lab in ((30, '+30'), (0, '0'), (-70, '−70')):
        paste(rgb, text_sprite(lab, 13, (170, 185, 210), False, False), x0 + 8, Y(mv) - 12, al, center=False)
    paste(rgb, text_sprite('放慢显示 · 实际约 1 毫秒', 14, MINT, False, False), x0 + 50, y0 + h - 30, al, center=False)
    return rgb


# ------------------------------------------------------------------ ion paths
def through_pore(view, px, top, bot, u, k, spread=0.06, seed=0, upward=False):
    """ion path: drift in from outside (above), funnel to pore centre px, pass, disperse inside."""
    rng = (math.sin(k * 12.9898 + seed) * 43758.5453) % 1.0
    rng2 = (math.sin(k * 78.233 + seed) * 12345.678) % 1.0
    sx = px + (rng - 0.5) * 2 * spread
    ex = px + (rng2 - 0.5) * 2 * spread
    y_out, y_in = top - 0.16, bot + 0.16
    if upward:
        y_out, y_in = y_in, y_out
        top, bot = bot, top
    if u < 0.4:
        v = ease(u / 0.4)
        fx, fy = sx + (px - sx) * v, y_out + (top - y_out) * v
    elif u < 0.7:
        v = (u - 0.4) / 0.3
        fx, fy = px, top + (bot - top) * v
    else:
        v = ease((u - 0.7) / 0.3)
        fx, fy = px + (ex - px) * v, bot + (y_in - bot) * v
    a = min(1, u * 8) * min(1, (1 - u) * 6)
    x, y = view.pt(fx, fy)
    return x, y, a


def draw_ions(rgb, view, t, n, rate, px, top, bot, color, r_frac, al, seed=0, upward=False, label='+', spread=0.06):
    if al <= 0:
        return rgb
    r = max(5, int(view.px(r_frac)))
    spr = ion_sprite(r, tuple(color), label)
    for k in range(n):
        u = (t * rate + ((k * 0.61803) % 1.0)) % 1.0
        x, y, a = through_pore(view, px, top, bot, u, k, spread, seed, upward)
        paste(rgb, spr, x, y, a * al)
    return rgb


# ================================================================== SEGMENTS (film time t)
def f_sting(t):
    lk = SPR('lockup_1280')
    a = ramp(t, 0.15, 1.0)
    k = 0.955 + 0.045 * ease(t / 3.4)
    spr = scaled(lk, k)
    rgb = np.zeros((H, W, 3), np.float32) + np.array([0.02, 0.025, 0.05], np.float32)
    paste(rgb, spr, W / 2, H / 2, a)
    # glint sweeps across the mark (once), no top streaks
    gx = W * (0.30 + 0.45 * ramp(t, 0.9, 2.2))
    add_radial(rgb, gx, H * 0.40, 60, (255, 220, 150), 0.22 * win(t, 0.9, 2.3, 0.3, 0.3))
    if t > 2.35:
        rgb = mix(rgb, f_open(t), ramp(t, 2.35, 3.0))
    return rgb


def f_open(t):
    p = P('open')
    u = (t - 2.3) / 6.2        # slow constant push across sting tail → s02
    z = 1.04 + 0.10 * u
    rgb, v = p.cam(z, 0.56 + 0.02 * u, 0.50 - 0.02 * u)
    al = win(t, 3.25, 7.35, 0.6, 0.6)
    if al > 0:
        rgb = mix(rgb, rgb * np.linspace(0.45, 1.0, W, dtype=np.float32)[None, :, None], 0.75 * al)
        paste(rgb, text_sprite('光遗传学', 92, CREAM), 330, 278, al)
        paste(rgb, text_sprite('OPTOGENETICS', 24, GOLD, True, True, 9), 330, 352, al)
        ov = overlay_layer()
        cv2.line(ov, (190, 382), (470, 382), col(GOLD, 0.8 * al), 2, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('一束光，只拨动一类神经元', 26, (190, 225, 215), False), 330, 414, al)
        paste(rgb, text_sprite('EigenLens · 主观知识', 18, (210, 200, 170), False), 330, 470, 0.85 * al)
    if t > 7.7:
        rgb = mix(rgb, f_1979(t), ramp(t, 7.7, 8.3))
    return rgb


CROWD_SOMA = [(0.22, 0.19), (0.70, 0.19), (0.12, 0.47), (0.47, 0.44), (0.89, 0.40), (0.31, 0.73), (0.79, 0.68)]


def crowd_frame(t, z, cx, cy, glow=0.0, dimv=0.0, ripple=0.0, ripple_rate=1.2):
    p = P('crowd')
    rgb, v = p.cam(z, cx, cy)
    m = p.warp_mask(MASK('crowd_or'), v)
    if dimv > 0:
        rgb = dim(rgb, m, dimv, 0.7)
    if glow > 0:
        rgb = tint(rgb, m, (255, 214, 140), min(1.0, 0.9 * glow))
        rgb = add_glow(rgb, m, (255, 170, 80), 0.35 * glow)
    if ripple > 0:
        for i, (fx, fy) in enumerate(CROWD_SOMA):
            x, y = v.pt(fx, fy)
            ph = (t * ripple_rate + i * 0.37) % 1.0
            rgb = ring(rgb, x, y, 20 + 70 * ph, (255, 200, 110), ripple * (1 - ph) * 0.9, 3)
    return rgb, v


def f_1979(t):
    u = (t - 7.7) / 4.8
    on = win(t, 8.4, 11.6, 0.6, 0.6)
    rgb, v = crowd_frame(t, 1.08 + 0.06 * u, 0.5, 0.5, glow=0.28 * on * (0.75 + 0.25 * math.sin(t * 3)))
    chip(rgb, '1979 · 一个要求', t, 8.1, 12.4, GOLD, '只动某一类神经元，其余大体不动')
    if t > 11.7:
        rgb = mix(rgb, f_microbe(t), ramp(t, 11.7, 12.3))
    return rgb


def microbe_frame(t, z, cx, cy, rods=0.0, light=0.0):
    p = P('microbe')
    rgb, v = p.cam(z, cx, cy)
    if rods > 0:
        m = p.warp_mask(MASK('microbe_rods'), v)
        rgb = add_glow(rgb, m, (200, 120, 255), rods)
    if light > 0:
        x, y = v.pt(0.56, 0.0)
        add_radial(rgb, x, y + 40, 200, (120, 200, 255), light)
    return rgb, v


def f_microbe(t):
    u = (t - 11.7) / 8.4
    lt = ramp(t, 14.8, 16.2)
    rgb, v = microbe_frame(t, 1.03 + 0.08 * u, 0.48, 0.5, rods=0.25 * lt * (0.7 + 0.3 * math.sin(t * 2.5)), light=0.18 * lt)
    # 线索越来越多：markers appear one by one on photoreceptive spots
    for i, (fx, fy, tt) in enumerate([(0.14, 0.42, 17.7), (0.30, 0.34, 18.0), (0.30, 0.57, 18.3), (0.733, 0.48, 18.6)]):
        a = ramp(t, tt, tt + 0.3)
        if a > 0:
            x, y = v.pt(fx, fy)
            rgb = ring(rgb, x, y, 18 + 4 * math.sin(t * 4 + i), YELLOW, 0.9 * a, 2)
    chip(rgb, '微生物 · 会被光推动的膜蛋白', t, 14.7, 19.9, PURPLE)
    if t > 19.5:
        rgb = mix(rgb, f_crick(t), ramp(t, 19.5, 20.1))
    return rgb


def f_crick(t):
    p = P('crick')
    u = (t - 19.5) / 11.6
    rgb, v = p.cam(1.0 + 0.05 * ease(u), 0.57, 0.40)
    card(rgb, SPR('card_crick'), 44, 196, t, 20.1, 30.4)
    chip(rgb, '设想：可以用光', t, 20.2, 23.2, CYAN)
    chip(rgb, '1999 · 写进文章', t, 23.3, 28.3, GOLD, '「理想的信号会是光」')
    chip(rgb, '他也承认：相当牵强', t, 28.4, 31.0, (200, 170, 140))
    if t > 30.45:
        rgb = mix(rgb, f_select(t), ramp(t, 30.45, 31.0))
    return rgb


def f_select(t):
    u = (t - 30.45) / 10.3
    on = win(t, 32.6, 34.95, 0.4, 0.25)
    off = win(t, 34.95, 36.5, 0.25, 0.4)
    fast = 0.0
    if 36.9 < t < 38.1:
        fast = 1.0 if ((t - 36.9) % 0.4) < 0.2 else 0.0
    glow = 0.6 * on + 0.6 * fast
    rgb, v = crowd_frame(t, 1.24 + 0.08 * u, 0.46, 0.46, glow=glow, dimv=0.8 * off, ripple=max(on, fast), ripple_rate=1.6)
    chip(rgb, '只让这一类打开（放电）', t, 32.5, 34.95, AMBER, '橙色 = 目标那一类神经元')
    chip(rgb, '或者关掉', t, 34.95, 36.5, (150, 160, 190), '这一类静默')
    chip(rgb, '旁边的细胞大体不动 · 而且要快', t, 36.5, 40.6, MINT)
    if t > 40.2:
        rgb = mix(rgb, f_nobel(t), ramp(t, 40.2, 40.8))
    return rgb


LAUR = [((0.162, 0.73), '格奥尔格·纳格尔', 'Georg Nagel', 42.9),
        ((0.500, 0.73), '彼得·黑格曼', 'Peter Hegemann', 43.6),
        ((0.838, 0.73), '卡尔·戴瑟罗斯', 'Karl Deisseroth', 44.3)]


def f_nobel(t):
    p = P('laur')
    u = (t - 40.2) / 11.2
    rgb, v = p.cam(1.0 + 0.04 * ease(u), 0.5, 0.46)
    for (fx, fy), zh, en, tt in LAUR:
        a = ramp(t, tt, tt + 0.6)
        x, y = v.pt(fx, fy)
        tw = v.px(0.325) / 2
        reg = (slice(max(0, int(y - 2 * tw - 20)), int(y)), slice(max(0, int(x - tw)), min(W, int(x + tw))))
        rgb[reg] = rgb[reg] * (0.12 + 0.88 * a)
        paste(rgb, text_sprite(zh, 24, CREAM), x, y + 22, a)
        paste(rgb, text_sprite(en, 16, (190, 200, 220), False), x, y + 52, a)
    ha = win(t, 40.7, 51.4, 0.5, 0.4)
    paste(rgb, text_sprite('2026 · 诺贝尔生理学或医学奖', 34, GOLD), W / 2, 58, ha)
    paste(rgb, text_sprite('10 月 5 日公布 · 三位研究者', 18, (200, 205, 220), False), W / 2, 100, ha * (1 - ramp(t, 45.4, 45.8)))
    qa = win(t, 45.7, 51.4, 0.5, 0.4)
    paste(rgb, text_sprite('理由：发现光控离子通道，并由此建立光遗传学', 22, MINT), W / 2, 104, qa)
    if t > 50.85:
        rgb = mix(rgb, f_switch(t), ramp(t, 50.85, 51.4))
    return rgb


def f_switch(t):
    p = P('neuron')
    u = (t - 50.85) / 10.2
    rgb, v = p.cam(1.08 + 0.12 * ease(u), 0.60 + 0.05 * u, 0.48)
    x, y = v.pt(0.655, 0.485)
    a = ramp(t, 55.7, 56.2)
    if a > 0:
        lit = ramp(t, 57.4, 58.2)
        rgb = ring(rgb, x, y, 34, (230, 230, 255) if lit < 0.5 else CYAN, a * (1 - lit) * 0.9 + 0.0, 2)
        if lit > 0:
            add_radial(rgb, x, y, 26, CYAN, 0.85 * lit)
            # beam arriving from upper-left
            ov = overlay_layer()
            src = (x - 380, y - 420)
            pts = np.array([src, (x - 12, y - 6), (x + 12, y + 6), (src[0] + 60, src[1] - 20)], np.int32)
            cv2.fillConvexPoly(ov, pts, col(CYAN, 0.18 * lit), cv2.LINE_AA)
            ov = cv2.GaussianBlur(ov, (0, 0), 6)
            rgb = comp(rgb, ov)
        paste(rgb, text_sprite('?', 34, CREAM), x + 44, y - 40, a * (1 - lit))
    chip(rgb, '从设想到方法', t, 51.6, 55.5, GOLD)
    chip(rgb, '缺一枚：能用光拨动的开关', t, 55.6, 61.2, CYAN)
    if t > 60.5:
        rgb = mix(rgb, f_title(t), ramp(t, 60.5, 61.0))
    return rgb


def f_title(t):
    p = P('brain')
    u = (t - 60.5) / 8.0
    rgb, v = p.cam(1.04 + 0.08 * u, 0.46, 0.44)
    x, y = v.pt(0.425, 0.285)
    add_radial(rgb, x, y, 22, CYAN, 0.5 + 0.25 * math.sin(t * 3))
    al = win(t, 63.4, 67.9, 0.6, 0.6)
    if al > 0:
        rgb = dim_all(rgb, 0.55 * al)
        paste(rgb, text_sprite('光遗传学', 86, CREAM), W / 2, 300, al)
        paste(rgb, text_sprite('OPTOGENETICS', 22, GOLD, True, True, 9), W / 2, 368, al)
        paste(rgb, text_sprite('这一期：这枚开关', 22, (190, 225, 215), False), W / 2, 412, al)
    if t > 68.0:
        rgb = mix(rgb, f_spike(t), ramp(t, 68.0, 68.6))
    return rgb


# ---------------- s13 spike — Goodsell membrane + ion overlay (note #7)
def spk(fx, fy):
    """sf08e fraction → spike-crop fraction"""
    return (fx - 0.44) / 0.56, (fy - 0.12) / 0.76


CH1 = spk(0.575, 0.0)[0]; CH2 = spk(0.817, 0.0)[0]
M_TOP = spk(0, 0.385)[1]; M_BOT = spk(0, 0.59)[1]
SPIKE_T0, SPIKE_DUR = 80.15, 1.9


def f_spike_membrane(t):
    p = P('spike')
    u = (t - 68.0) / 15.6
    rgb, v = p.cam(1.02 + 0.10 * ease(u), 0.47, 0.50)
    # charges: outside + / inside − ; flip during spike
    xs = [0.06 + 0.11 * i for i in range(9)]
    ca = win(t, 72.8, 83.6, 0.6, 0.4)
    flip = ramp(t, SPIKE_T0 + 0.25, SPIKE_T0 + 0.6) * (1 - ramp(t, SPIKE_T0 + 1.2, SPIKE_T0 + 1.7))
    out_y, in_y = M_TOP - 0.07, M_BOT + 0.07
    rgb = charges_row(rgb, v, xs, out_y, +1, ca * (1 - flip), (255, 120, 110))
    rgb = charges_row(rgb, v, xs, in_y, -1, ca * (1 - flip), (120, 170, 255))
    rgb = charges_row(rgb, v, xs, out_y, -1, ca * flip, (120, 170, 255))
    rgb = charges_row(rgb, v, xs, in_y, +1, ca * flip, (255, 120, 110))
    if ca > 0:
        x, y = v.pt(0.015, out_y); paste(rgb, text_sprite('膜外', 20, CREAM), x + 8, y - 44, ca, center=False)
        x, y = v.pt(0.015, in_y); paste(rgb, text_sprite('膜内', 20, CREAM), x + 8, y + 12, ca, center=False)
    # channels open: pore glow; Na+ in (ch1) then K+ out (ch2)
    op1 = win(t, 76.4, SPIKE_T0 + 0.8, 0.5, 0.4)
    op2 = win(t, SPIKE_T0 + 0.5, 83.4, 0.3, 0.6)
    for cx_, op, c in ((CH1, op1, NA), (CH2, op2, KION)):
        if op > 0:
            x0, y0 = v.pt(cx_, M_TOP); x1, y1 = v.pt(cx_, M_BOT)
            for k in range(6):
                add_radial(rgb, x0, y0 + (y1 - y0) * k / 5, 16, c, 0.35 * op)
    rgb = draw_ions(rgb, v, t, 9, 0.55, CH1, M_TOP, M_BOT, NA, 0.016, op1, seed=1, spread=0.10)
    rgb = draw_ions(rgb, v, t, 7, 0.55, CH2, M_TOP, M_BOT, KION, 0.016, op2, seed=2, upward=True, spread=0.10)
    # legends near pores
    la = win(t, 77.0, SPIKE_T0 + 0.6, 0.4, 0.3)
    x, y = v.pt(CH1 + 0.16, M_TOP - 0.09); tag(rgb, 'Na^{+} 涌入', x, y, la, NA)
    lb = win(t, SPIKE_T0 + 0.7, 83.4, 0.3, 0.4)
    x, y = v.pt(CH2 - 0.19, M_TOP - 0.09); tag(rgb, 'K^{+} 流出 → 恢复', x, y, lb, KION)
    chip(rgb, '细胞膜 · 离子通道', t, 68.8, 75.6, MINT, '膜两侧有电压')
    chip(rgb, '一次锋电位 = 离子极快穿膜', t, 75.7, 79.9, AMBER)
    chip(rgb, '电压翻过去 → 再恢复', t, 79.95, 83.7, AMBER, '膜内由负变正，又回到负')
    rgb = vm_panel(rgb, t, win(t, 73.2, 83.6, 0.5, 0.4), SPIKE_T0, SPIKE_DUR)
    return rgb


def f_spike_tools(t):
    p = P('brain')
    u = (t - 83.0) / 13.6
    rgb, v = p.cam(1.15 + 0.10 * ease(u), 0.40, 0.46)
    tip = v.pt(0.425, 0.29)
    # 记录：tip + active sites blink, mini trace attached
    ra = win(t, 83.5, 91.0, 0.4, 0.5)
    if ra > 0:
        sites = [(0.33, 0.27), (0.38, 0.35), (0.46, 0.31), (0.50, 0.25), (0.40, 0.42)]
        for i, (fx, fy) in enumerate(sites):
            ph = (t * 1.3 + i * 0.29) % 1.0
            x, y = v.pt(fx, fy)
            add_radial(rgb, x, y, 14, CYAN, ra * 0.9 * math.exp(-((ph - 0.1) / 0.08) ** 2))
        add_radial(rgb, tip[0], tip[1], 20, CYAN, 0.6 * ra)
        x0, y0 = int(tip[0] + 60), int(tip[1] - 150)
        rgb = panel_bg(rgb, x0, y0, x0 + 230, y0 + 86, ra, CYAN)
        ov = overlay_layer()
        for i in range(140):
            xx = x0 + 10 + i * 1.5
            tt = t - 2 + i / 70
            spike = 1 if (tt * 3.1) % 1 < 0.04 else 0
            yy = y0 + 58 - spike * 34 + 2 * math.sin(i * 1.7)
            if i:
                cv2.line(ov, (int(px_), int(py_)), (int(xx), int(yy)), col(CYAN, ra), 2, cv2.LINE_AA)
            px_, py_ = xx, yy
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('电极记录', 15, CYAN, True, False), x0 + 10, y0 + 2, ra, center=False)
        rgb = leader(rgb, (tip[0] + 4, tip[1] - 4), (x0, y0 + 60), CYAN, ra)
    # 损毁：a region darkens with dashed outline
    la = win(t, 87.9, 95.9, 0.6, 0.5)
    if la > 0:
        m = disc_mask(p, [(0.40, 0.68)], 0.075, 0.45)
        rgb = dim(rgb, p.warp_mask(m, v), 0.85 * la, 0.9)
        x, y = v.pt(0.40, 0.68)
        r = v.px(0.075)
        ov = overlay_layer()
        for a0 in range(0, 360, 20):
            cv2.ellipse(ov, (int(x), int(y)), (int(r), int(r)), 0, a0, a0 + 11, col(AMBER, la), 3, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        tag(rgb, '损毁一块', x + r + 70, y - r * 0.6, la, AMBER)
    chip(rgb, '记录：哪里在活动', t, 83.6, 87.9, CYAN)
    chip(rgb, '损毁：看行为缺了什么', t, 87.9, 91.4, AMBER)
    qa = win(t, 91.6, 96.4, 0.5, 0.5)
    if qa > 0:
        rgb = dim_all(rgb, 0.6 * qa)
        paste(rgb, text_sprite('相关 ≠ 因果', 70, CREAM), W / 2, 300, qa)
        paste(rgb, text_sprite('记录与损毁都证明不了因果 —— 诺奖新闻稿', 22, (200, 210, 225), False), W / 2, 372, qa)
    return rgb


MOUSE_PIP = None


def mouse_pip(out_r=96):
    global MOUSE_PIP
    if MOUSE_PIP is None:
        MOUSE_PIP = circle_crop(P('mwake').img, 0.44, 0.50, int(P('mwake').w * 0.24), out_r, GOLD)
    return MOUSE_PIP


def f_spike_cause(t):
    u = (t - 95.9) / 26.0
    z, cx, cy = 1.16 + 0.10 * ease(u), 0.42, 0.50
    # C: correlation vs causation
    corr = win(t, 97.1, 109.3, 0.5, 0.6)
    drive = 0.0; hold = 0.0
    beam_col = None
    if 109.8 < t < 113.35:
        ph = ((t - 109.8) * 4.0) % 1.0
        drive = 1.0 if ph < 0.3 else 0.0
        beam_col = CYAN
    hold = win(t, 113.35, 116.0, 0.3, 0.6)
    glow = 0.45 * corr * (0.8 + 0.2 * math.sin(t * 2.6)) + 0.75 * drive
    rgb, v = crowd_frame(t, z, cx, cy, glow=glow, dimv=0.85 * hold, ripple=max(drive, 0.0), ripple_rate=2.0)
    # mouse PIP (top-right) — 动物醒了/怕了
    pa = win(t, 98.6, 109.3, 0.5, 0.5)
    pip_xy = (W - 150, 160)
    if pa > 0:
        paste(rgb, mouse_pip(), pip_xy[0], pip_xy[1], pa)
        paste(rgb, text_sprite('动物醒了 / 怕了', 18, CREAM), pip_xy[0], pip_xy[1] + 118, pa)
    soma = v.pt(*CROWD_SOMA[3])
    a1 = win(t, 102.9, 109.3, 0.4, 0.5)
    rgb = leader(rgb, (soma[0] + 30, soma[1] - 20), (pip_xy[0] - 100, pip_xy[1] + 20), (20, 20, 30), 0.7 * a1, 9)
    rgb = leader(rgb, (soma[0] + 30, soma[1] - 20), (pip_xy[0] - 100, pip_xy[1] + 20), CREAM, a1, 4, arrow=True)
    tag(rgb, '放电 造成 行为？', (soma[0] + pip_xy[0]) / 2 - 30, (soma[1] + pip_xy[1]) / 2 - 10, a1, GOLD)
    a2 = win(t, 105.6, 109.3, 0.4, 0.5)
    rgb = leader(rgb, (pip_xy[0] - 96, pip_xy[1] + 70), (soma[0] + 40, soma[1] + 10), (20, 20, 30), 0.7 * a2, 8, dashed=True)
    rgb = leader(rgb, (pip_xy[0] - 96, pip_xy[1] + 70), (soma[0] + 40, soma[1] + 10), (215, 215, 235), a2, 3, dashed=True, arrow=True)
    tag(rgb, '只是跟着亮？', (soma[0] + pip_xy[0]) / 2 + 30, (soma[1] + pip_xy[1]) / 2 + 70, a2, (190, 190, 210))
    # D: drive with blue light / hold with amber light
    for colr, a in ((CYAN, win(t, 109.7, 113.35, 0.3, 0.2)), (AMBER, hold)):
        if a > 0:
            ov = overlay_layer()
            src = (W * 0.92, -40)
            tgt = v.pt(*CROWD_SOMA[3])
            pts = np.array([src, (tgt[0] - 90, tgt[1] + 40), (tgt[0] + 90, tgt[1] + 40), (src[0] + 90, src[1])], np.int32)
            flick = 1.0 if colr is AMBER else (0.55 + 0.45 * drive)
            cv2.fillConvexPoly(ov, pts, (1, 1, 1, 1), cv2.LINE_AA)
            bm = cv2.GaussianBlur(ov[..., 3], (0, 0), 10)
            rgb = add_glow(rgb, bm, colr, 0.95 * a * flick)
            add_radial(rgb, tgt[0], tgt[1] + 20, 70, colr, 0.45 * a * flick)
    chip(rgb, '相关：这一类亮着时，动物醒了', t, 97.1, 102.9, GOLD)
    chip(rgb, '因果要多问一句', t, 102.9, 109.5, CREAM)
    chip(rgb, '推动：蓝光一闪 → 这一类放电', t, 109.7, 113.3, CYAN)
    chip(rgb, '按住：黄光 → 这一类静默', t, 113.35, 115.5, AMBER)
    # ms panel
    ma = win(t, 115.4, 121.6, 0.4, 0.4)
    if ma > 0:
        x0, y0, w, h = 860, 40, 380, 190
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, ma, MINT)
        paste(rgb, text_sprite('时间尺度：毫秒', 24, MINT), x0 + 16, y0 + 6, ma, center=False)
        ov = overlay_layer()
        scroll = (t * 0.8) % 1.0
        for k in range(8):
            xx = x0 + 30 + ((k / 8 + scroll) % 1.0) * (w - 60)
            cv2.rectangle(ov, (int(xx), y0 + 64), (int(xx + 6), y0 + 90), col(CYAN, ma), -1)
            cv2.line(ov, (int(xx + 3), y0 + 150), (int(xx + 3), y0 + 106), col(AMBER, ma), 3, cv2.LINE_AA)
        cv2.line(ov, (x0 + 30, y0 + 150), (x0 + w - 30, y0 + 150), col((120, 140, 170), ma), 1, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('光脉冲', 14, CYAN, False, False), x0 + w - 70, y0 + 66, ma, center=False)
        paste(rgb, text_sprite('锋电位', 14, AMBER, False, False), x0 + w - 70, y0 + 120, ma, center=False)
        sa = ramp(t, 118.0, 118.6) * ma
        paste(rgb, text_sprite('一一对应 · 不是分钟', 16, CREAM, True, False), x0 + 16, y0 + 158, sa, center=False)
    return rgb


def f_spike(t):
    if t < 83.0:
        rgb = f_spike_membrane(t)
        if t > 82.7:
            rgb = mix(rgb, f_spike_tools(t), ramp(t, 82.7, 83.5))
    elif t < 96.2:
        rgb = f_spike_tools(t)
        if t > 95.9:
            rgb = mix(rgb, f_spike_cause(t), ramp(t, 95.9, 96.6))
    else:
        rgb = f_spike_cause(t)
    if t > 121.1:
        rgb = mix(rgb, f_early(t), ramp(t, 121.1, 121.7))
    return rgb


# ---------------- s08 early: 4-step relay cascade (note #8)
RELAY = [(0.112, 0.42, '受体'), (0.215, 0.52, 'G 蛋白'), (0.41, 0.50, '酶'), (0.575, 0.49, '通道')]
STEP_T = [126.2, 126.9, 127.6, 128.3]


def badge(rgb, x, y, n, al, color=GOLD):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    cv2.circle(ov, (int(x), int(y)), 17, col(INK, 0.9 * al), -1, cv2.LINE_AA)
    cv2.circle(ov, (int(x), int(y)), 17, col(color, al), 2, cv2.LINE_AA)
    rgb = comp(rgb, ov)
    paste(rgb, text_sprite(str(n), 20, color, True, False), x, y, al)
    return rgb


def relay_cascade(rgb, v, t, steps_t, slow=1.0):
    """light → ①→②→③→④ with travelling signal dot."""
    for i, (fx, fy, name) in enumerate(RELAY):
        on = ramp(t, steps_t[i], steps_t[i] + 0.25 * slow)
        x, y = v.pt(fx, fy)
        if on > 0:
            add_radial(rgb, x, y, 34, (255, 225, 140), 0.55 * on * (0.85 + 0.15 * math.sin(t * 6)))
        rgb = badge(rgb, x, y - v.px(0.075), i + 1, max(on, 0.35))
        paste(rgb, text_sprite(name, 16, CREAM, True), x, y + v.px(0.085), max(on, 0.3) * 0.95)
        if i < 3:
            a, b = steps_t[i] + 0.05, steps_t[i + 1]
            if a <= t <= b + 0.1:
                k = ease((t - a) / (b - a))
                fx2, fy2, _ = RELAY[i + 1]
                p0, p1 = v.pt(fx, fy + 0.04), v.pt(fx2, fy2 + 0.04)
                px_, py_ = p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k
                paste(rgb, ion_sprite(9, YELLOW, ''), px_, py_, 1.0)
    return rgb


def f_early(t):
    pe, pd = P('relay'), P('relayd')
    # camera: whole relay → channel 2 (switch) → pull back
    k1 = ramp(t, 128.9, 131.7); k2 = ramp(t, 132.5, 135.2)
    z = 1.04 + 0.06 * ramp(t, 121.1, 128.8)
    cx, cy = 0.36, 0.47
    z = z + (1.32 - z) * k1 + (1.08 - 1.32) * k2
    cx = cx + (0.72 - cx) * k1 + (0.42 - 0.72) * k2
    cy = cy + (0.38 - cy) * k1 + (0.46 - 0.38) * k2
    rgb, v = pe.cam(z, cx, cy)
    sw = win(t, 129.0, 136.0, 0.8, 0.8)
    if sw > 0:
        rgbd, _ = pd.cam(z, cx, cy)
        rgb = mix(rgb, rgbd, sw)
    # light flash on squiggle at start of each cascade
    fl = math.exp(-((t - 126.0) / 0.18) ** 2) + math.exp(-((t - 133.4) / 0.18) ** 2)
    rgb = add_glow(rgb, pe.warp_mask(MASK('relay_squig'), v), (180, 230, 255), 1.4 * fl)
    ca = win(t, 125.8, 129.4, 0.2, 0.5)
    if ca > 0:
        rgb = mix(rgb, relay_cascade(rgb.copy(), v, t, STEP_T), ca)
    # slow replay during 「达不到毫秒」
    sl = win(t, 133.2, 137.3, 0.3, 0.4)
    if sl > 0:
        rgb = mix(rgb, relay_cascade(rgb.copy(), v, t, [133.5, 134.5, 135.5, 136.5], 2.0), sl)
    # ④ opens at end of cascade
    if t > STEP_T[3]:
        x0, y0 = v.pt(0.575, 0.40); x1, y1 = v.pt(0.575, 0.60)
        oa = win(t, STEP_T[3], 129.6, 0.2, 0.4)
        for k in range(5):
            add_radial(rgb, x0, y0 + (y1 - y0) * k / 4, 14, NA, 0.4 * oa)
    # photoswitch highlight
    if sw > 0:
        x, y = v.pt(0.80, 0.29)
        rgb = ring(rgb, x, y, 58 + 4 * math.sin(t * 4), (255, 90, 230), sw * ramp(t, 129.8, 130.4), 3)
        tag(rgb, '外加的化学光开关', x, y - 92, sw * ramp(t, 130.0, 130.5), (255, 90, 230))
    chip(rgb, '更早的光控尝试', t, 121.6, 125.8, GOLD, '诺奖科学背景')
    chip(rgb, '方案一：好几步信号接力', t, 125.9, 128.9, GOLD, '光 → 受体 → G 蛋白 → 酶 → 通道')
    chip(rgb, '方案二：通道上外加化学光开关', t, 128.9, 132.7, (255, 90, 230))
    chip(rgb, '都达不到毫秒级', t, 132.7, 137.4, AMBER, '接力一步步传，太慢')
    if t > 136.8:
        rgb = mix(rgb, f_chr2(t), ramp(t, 136.8, 137.4))
    return rgb


# ---------------- s09 ChR2: ions through the pore centre (note #9)
def f_chr2(t):
    p = P('chr2')
    u = (t - 136.8) / 8.8
    rgb, v = p.cam(1.04 + 0.16 * ease(u), 0.495, 0.47)
    lit = ramp(t, 139.4, 140.0)
    beam = p.warp_mask(MASK('chr2_beam'), v)
    rgb = dim(rgb, beam, 0.75 * (1 - lit), 0.2)
    pore = p.warp_mask(MASK('chr2_pore'), v)
    op = ramp(t, 140.1, 140.6)
    rgb = mix(rgb, np.array([0.22, 0.62, 0.56], np.float32), (0.8 * (1 - op) * pore)[..., None])
    rgb = add_glow(rgb, pore, CYAN, 0.6 * op)
    # light pulse travels down the beam
    if 139.3 < t < 140.2:
        k = (t - 139.3) / 0.9
        a0, a1 = v.pt(0.12, -0.02), v.pt(0.42, 0.40)
        add_radial(rgb, a0[0] + (a1[0] - a0[0]) * k, a0[1] + (a1[1] - a0[1]) * k, 40, (170, 220, 255), 0.8)
    # retinal flash
    for fx, fy in ((0.385, 0.44), (0.60, 0.44)):
        x, y = v.pt(fx, fy)
        add_radial(rgb, x, y, 20, (255, 170, 80), 0.9 * math.exp(-((t - 140.0) / 0.25) ** 2))
    ia = ramp(t, 140.4, 140.9) * (1 - ramp(t, 145.0, 145.6))
    for px_, sd in ((0.435, 3), (0.555, 4)):
        rgb = draw_ions(rgb, v, t, 7, 0.45, px_, 0.36, 0.62, NA, 0.0125, ia, seed=sd, spread=0.05)
    x, y = v.pt(0.495, 0.20)
    tag(rgb, '阳离子 (Na^{+} 等) 从孔中穿过', x, y, win(t, 140.8, 145.3, 0.4, 0.4), NA)
    card(rgb, SPR('card_chr2'), W - 596, 30, t, 137.7, 141.3, anchor='right')
    chip(rgb, '光打上去 → 它自己开门', t, 139.4, 141.4, CYAN)
    chip(rgb, '不必再请一套帮手', t, 141.45, 145.6, MINT, '一步：光 → 开孔')
    if t > 144.95:
        rgb = mix(rgb, f_orexin(t), ramp(t, 144.95, 145.5))
    return rgb


# ---------------- s14 orexin cluster: gold + fire (note #10)
OREX = [(0.36, 0.42), (0.455, 0.33), (0.57, 0.30), (0.63, 0.45), (0.505, 0.52), (0.40, 0.62), (0.62, 0.66)]


def f_orexin(t):
    p = P('orexin')
    u = (t - 144.95) / 16.4
    rgb, v = p.cam(1.02 + 0.14 * ease(u), 0.5, 0.48)
    m = p.warp_mask(MASK('orexin_cy'), v)
    gold = ramp(t, 150.2, 151.4)
    rgb = tint(rgb, m, (255, 186, 90), 0.85 * gold)
    # secretion: small peptide beads drifting out of somas
    sa = win(t, 151.0, 157.4, 0.6, 0.6)
    if sa > 0:
        spr = ion_sprite(4, (255, 210, 120), '')
        for i, (fx, fy) in enumerate(OREX):
            for j in range(3):
                ph = (t * 0.35 + j / 3 + i * 0.13) % 1.0
                ang = i * 1.3 + j * 2.1
                x, y = v.pt(fx + math.cos(ang) * 0.07 * ph, fy + math.sin(ang) * 0.09 * ph)
                paste(rgb, spr, x, y, sa * (1 - ph))
    # firing: bursts + ripple rings (157.4 「放电本身」)
    fa = win(t, 157.3, 161.4, 0.2, 0.4)
    if fa > 0:
        for i, (fx, fy) in enumerate(OREX):
            ph = (t * 2.2 + i * 0.41) % 1.0
            x, y = v.pt(fx, fy)
            add_radial(rgb, x, y, v.px(0.035), (255, 150, 60), fa * 0.9 * math.exp(-(ph / 0.12) ** 2))
            rgb = ring(rgb, x, y, v.px(0.03) + 60 * ph, (255, 170, 80), fa * (1 - ph), 2)
    card(rgb, SPR('card_orexin'), 36, 30, t, 150.3, 155.9)
    chip(rgb, '一次干净的实验', t, 145.9, 149.8, GOLD)
    chip(rgb, '下丘脑外侧 · 食欲素神经元', t, 156.0, 157.35, AMBER)
    chip(rgb, '已知：和清醒有关', t, 154.3, 156.0, MINT)
    chip(rgb, '问题：放电本身够不够？', t, 157.4, 161.4, AMBER)
    if t > 160.8:
        rgb = mix(rgb, f_mouse(t), ramp(t, 160.8, 161.4))
    return rgb


# ---------------- s10 mouse: light-on same beat (note #10b)
def fiber_glow(rgb, v, top, imp, a, pulse_k=None):
    x0, y0 = v.pt(*top); x1, y1 = v.pt(*imp)
    ov = overlay_layer()
    cv2.line(ov, (int(x0), int(y0)), (int(x1), int(y1)), col((120, 210, 255), 0.75 * a), 5, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 3)
    rgb = comp(rgb, ov)
    if pulse_k is not None:
        add_radial(rgb, x0 + (x1 - x0) * pulse_k, y0 + (y1 - y0) * pulse_k, 22, (170, 230, 255), 0.9)
    return rgb


def f_mouse(t):
    ps, pw = P('msleep'), P('mwake')
    u = (t - 160.8) / 23.0
    xf = ramp(t, 169.5, 171.2)
    rs, vs = ps.cam(1.04 + 0.14 * u, 0.56 + 0.04 * u, 0.42)
    rw, vw = pw.cam(1.06 + 0.12 * u, 0.54 + 0.03 * u, 0.44)
    # light state
    on = ramp(t, 167.95, 168.15)
    off = ramp(t, 179.5, 179.9)
    light = on * (1 - off)
    blink = 1.0
    if 174.0 <= t < 177.85:
        blink = 1.0 if ((t * 10) % 1.0) < 0.5 else 0.25
    elif 177.85 <= t < 179.5:
        blink = 1.0 if ((t - 177.85) % 1.0) < 0.12 else 0.15
    L = light * blink
    for rgb_, v_, top, imp, w_ in ((rs, vs, (0.815, 0.0), (0.81, 0.33), 1 - xf), (rw, vw, (0.60, 0.0), (0.595, 0.37), xf)):
        if w_ <= 0:
            continue
        fa = win(t, 166.2, 179.9, 0.3, 0.3)
        pk = ((t - 166.3) / 1.6) if 166.3 < t < 167.9 else None
        fiber_glow(rgb_, v_, top, imp, fa * (0.35 + 0.65 * L), pk)
        x, y = v_.pt(*imp)
        add_radial(rgb_, x, y, 30, (110, 200, 255), 1.2 * L)
        add_radial(rgb_, x, y, 90, (80, 160, 255), 0.35 * L)
    rgb = mix(rs, rw, xf)
    # flash cue at light-on
    rgb = rgb + np.array([0.10, 0.18, 0.30], np.float32) * math.exp(-((t - 168.05) / 0.12) ** 2) * 0.6
    # PIP: orexin cells + ChR2 (162.5 「放进这群细胞」)
    pa = win(t, 162.5, 166.4, 0.4, 0.4)
    if pa > 0:
        po = P('orexin')
        if not hasattr(f_mouse, 'pip'):
            img = tint(po.img.copy(), MASK('orexin_cy'), (255, 186, 90), 0.85)
            f_mouse.pip = circle_crop(img, 0.50, 0.47, int(po.w * 0.17), 105, MINT)
        paste(rgb, f_mouse.pip, 170, 250, pa)
        paste(rgb, text_sprite('食欲素神经元 + 光控通道', 18, CREAM), 170, 378, pa)
        imp = vs.pt(0.81, 0.36)
        rgb = leader(rgb, (275, 250), (imp[0] - 20, imp[1] + 10), MINT, pa, 2, dashed=True)
    # status panel (top-right)
    sa = win(t, 168.0, 180.2, 0.2, 0.5)
    if sa > 0:
        x0, y0, w, h = 900, 30, 340, 168
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, sa, CYAN)
        lamp = (110, 200, 255) if L > 0.5 else (60, 80, 110)
        ov = overlay_layer()
        cv2.circle(ov, (x0 + 30, y0 + 30), 12, col(lamp, sa), -1, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        mode = '光：开' if t < 174.0 else ('脉冲 5–30 次/秒' if t < 177.85 else '脉冲 1 次/秒')
        paste(rgb, text_sprite(mode, 20, CREAM), x0 + 52, y0 + 12, sa, center=False)
        if t < 174.0:
            lab, frac = '清醒概率', 0.25 + 0.55 * ramp(t, 169.0, 173.5)
            barc = MINT
        elif t < 177.85:
            lab, frac = '入睡→清醒的等待', 0.8 - 0.5 * ramp(t, 174.3, 177.0)
            barc = MINT
        else:
            lab, frac = '入睡→清醒的等待', 0.8
            barc = (200, 120, 120)
        paste(rgb, text_sprite(lab, 16, (200, 210, 225), False, False), x0 + 20, y0 + 58, sa, center=False)
        ov = overlay_layer()
        cv2.rectangle(ov, (x0 + 20, y0 + 92), (x0 + w - 20, y0 + 116), col((40, 50, 80), sa), -1)
        cv2.rectangle(ov, (x0 + 20, y0 + 92), (x0 + 20 + int((w - 40) * frac), y0 + 116), col(barc, sa), -1)
        rgb = comp(rgb, ov)
        if t >= 174.0:
            # pulse train ticks
            ov = overlay_layer()
            hz = 10 if t < 177.85 else 1
            for k in range(30):
                tt = t - 2.0 + k * (2.0 / 30)
                if (tt * hz) % 1.0 < (0.5 if hz > 1 else 0.12):
                    xx = x0 + 20 + k * (w - 40) / 30
                    cv2.rectangle(ov, (int(xx), y0 + 128), (int(xx + 6), y0 + 150), col(CYAN, sa), -1)
            rgb = comp(rgb, ov)
        if t >= 177.85:
            paste(rgb, text_sprite('不能缩短 ×', 18, (255, 140, 140)), x0 + w - 70, y0 + 66, sa)
    chip(rgb, '2007 · 光纤小鼠实验', t, 161.2, 166.3, GOLD)
    chip(rgb, '光纤把光送进去', t, 166.3, 168.0, CYAN)
    chip(rgb, '光一开', t, 168.0, 169.5, CYAN)
    chip(rgb, '慢波 / 快速眼动睡眠 → 清醒', t, 169.5, 174.0, MINT)
    chip(rgb, '开关的来历：微生物的膜', t, 181.0, 190.0, PURPLE)
    if t > 182.9:
        rgb = mix(rgb, f_B(t), ramp(t, 182.9, 183.9))
    return rgb


# ---------------- B chain head (notes #11–#15)
def f_B_archaea(t):
    k = ramp(t, 190.6, 196.6)
    z = 1.04 + (1.48 - 1.04) * k + 0.04 * ramp(t, 183.0, 191.0) + 0.08 * ramp(t, 196.6, 205.6)
    cx = 0.40 + (0.22 - 0.40) * k
    cy = 0.50 + (0.45 - 0.50) * k
    rods = ramp(t, 192.3, 193.3) * (0.30 + 0.10 * math.sin(t * 2.2))
    rgb, v = microbe_frame(t, z, cx, cy, rods=rods)
    rod = v.pt(0.205, 0.43)
    if 192.4 < t < 196.2:
        rgb = ring(rgb, rod[0], rod[1], v.px(0.085), (215, 170, 255), win(t, 192.4, 196.2, 0.3, 0.4), 3)
    chip(rgb, '开关的来历：微生物的膜', t, 181.0, 190.0, PURPLE)
    chip(rgb, '1971 · 嗜盐古菌', t, 191.0, 196.0, PURPLE, '分离出「紫膜」')
    card(rgb, SPR('card_retinal'), W - 640, 30, t, 195.8, 201.4, target=(rod[0] + 10, rod[1] - 10))
    # 蛋白只有这一种 — one-protein membrane patch inset
    pa = win(t, 200.9, 205.3, 0.4, 0.3)
    if pa > 0:
        patch = scaled(SPR('br_patch'), 0.62)
        cx_, cy_ = W - 230, 300
        rgb = leader(rgb, (rod[0] + 30, rod[1]), (cx_ - 130, cy_), (215, 170, 255), pa, 2)
        paste(rgb, patch, cx_, cy_, pa)
        paste(rgb, text_sprite('膜片段里只有这一种蛋白', 20, CREAM), cx_, cy_ + 152, pa)
    return rgb


PUMP = (0.112, 0.43)
FLASH0, FLASHP = 210.6, 2.2


def flash_phase(t):
    if t < FLASH0:
        return None
    return ((t - FLASH0) % FLASHP) / FLASHP, int((t - FLASH0) // FLASHP)


def f_B_pump(t):
    p = P('relay')
    # steady framing on the pump (note #13: no zoom while protons move), then pull to pump+channel, pan to channel
    k1 = ramp(t, 221.6, 225.0)       # pump+channel wide
    k2 = ramp(t, 227.4, 230.9)       # pan to channel
    z = 1.56 + 0.10 * ramp(t, 205.0, 221.6)
    cx, cy = 0.20, 0.45
    z += (1.15 - z) * k1; cx += (0.36 - cx) * k1; cy += (0.46 - cy) * k1
    z += (1.62 - 1.15) * k2; cx += (0.50 - 0.36) * k2; cy += (0.48 - 0.46) * k2
    rgb, v = p.cam(z, cx, cy)
    fp = flash_phase(t)
    pumping = t < 229.4
    nH = 0
    if fp is not None and pumping:
        ph, n = fp
        nH = n
        fl = math.exp(-((ph - 0.02) / 0.05) ** 2)
        rgb = add_glow(rgb, p.warp_mask(MASK('relay_squig'), v), (200, 240, 255), 1.6 * fl)
        hit = v.pt(0.11, 0.29)
        add_radial(rgb, hit[0], hit[1], 34, (230, 245, 255), 0.9 * fl)
        # absorption peak shift: purple → yellow briefly
        sh = math.exp(-((ph - 0.18) / 0.14) ** 2)
        rgb = tint(rgb, p.warp_mask(MASK('relay_pump'), v), (255, 205, 90), 0.75 * sh)
        # one proton: inside → through pump → outside
        if 0.12 < ph < 0.95:
            q = (ph - 0.12) / 0.83
            pts = [(0.098, 0.74), (0.112, 0.58), (0.112, 0.29), (0.14, 0.20)]
            seg = min(2, int(q * 3)); w_ = q * 3 - seg
            fx = pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * ease(w_)
            fy = pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * ease(w_)
            x, y = v.pt(fx, fy)
            paste(rgb, ion_sprite(max(8, int(v.px(0.009))), HION, '+'), x, y, 1.0)
            nH = n
        else:
            nH = n + (1 if ph >= 0.95 else 0)
    # accumulated H+ outside (gradient builds)
    if t > FLASH0:
        spr = ion_sprite(max(7, int(v.px(0.008))), HION, '+')
        for j in range(min(nH, 14)):
            a_ = 0.9 * win(t, FLASH0, 238.0, 0.3, 1.0)
            fx = 0.04 + (j * 0.37 % 1.0) * 0.30 + 0.006 * math.sin(t * 1.7 + j)
            fy = 0.13 + (j * 0.61 % 1.0) * 0.12 + 0.006 * math.cos(t * 1.3 + j)
            x, y = v.pt(fx, fy)
            paste(rgb, spr, x, y, a_)
        for j in range(3):
            x, y = v.pt(0.05 + j * 0.08, 0.80 + 0.01 * math.sin(t + j))
            paste(rgb, spr, x, y, 0.8 * win(t, FLASH0, 238.0, 0.3, 1.0))
    # flash indicator (note #13)
    ia = win(t, 210.3, 229.4, 0.3, 0.5)
    if ia > 0:
        x0, y0 = W - 300, 30
        rgb = panel_bg(rgb, x0, y0, x0 + 268, y0 + 92, ia, (200, 230, 255))
        lamp = 0.25
        if fp is not None:
            lamp = max(0.25, math.exp(-((fp[0] - 0.02) / 0.06) ** 2))
        ov = overlay_layer()
        cv2.circle(ov, (x0 + 34, y0 + 46), 18, col((220, 240, 255), ia * lamp), -1, cv2.LINE_AA)
        cv2.circle(ov, (x0 + 34, y0 + 46), 18, col((200, 230, 255), ia), 2, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('闪光', 22, CREAM), x0 + 64, y0 + 12, ia, center=False)
        paste(rgb, text_sprite('每闪一次 → 搬一个 H+（示意节奏）', 13, (190, 205, 225), False, False), x0 + 64, y0 + 52, ia, center=False)
    pump_pt = v.pt(*PUMP)
    card(rgb, SPR('card_br'), 390, 30, t, 209.4, 213.05, target=(pump_pt[0] + 24, pump_pt[1] - 40), accent=PURPLE)
    chip(rgb, '1973 · 命名', t, 205.0, 209.3, PURPLE)
    chip(rgb, '同时把质子放出去、再收回来', t, 213.1, 215.7, HION)
    chip(rgb, '光驱动质子泵 · 定向：膜内 → 膜外', t, 215.7, 222.7, HION)
    chip(rgb, '泵 ≠ 通道', t, 222.7, 227.8, MINT)
    ta = win(t, 224.4, 229.4, 0.4, 0.4)
    tag(rgb, '泵：往指定方向推，可逆梯度', pump_pt[0] + 40, pump_pt[1] - v.px(0.13), ta, HION)
    # ---- channel part
    ch = (0.575, 0.49)
    chp = v.pt(*ch)
    tag(rgb, '通道：一个孔', chp[0], chp[1] - v.px(0.12), win(t, 229.2, 237.5, 0.4, 0.4), MINT)
    op = ramp(t, 230.4, 231.0) * (1 - ramp(t, 243.0, 244.0))
    if op > 0:
        x0, y0 = v.pt(0.575, 0.38); x1, y1 = v.pt(0.575, 0.60)
        for kk in range(6):
            add_radial(rgb, x0, y0 + (y1 - y0) * kk / 5, 16, NA, 0.4 * op)
    rgb = draw_ions(rgb, v, t, 12, 0.5, 0.575, 0.38, 0.60, NA, 0.0085, op * ramp(t, 231.0, 231.6), seed=7, spread=0.08)
    chip(rgb, '孔打开 → 离子顺浓度差、电压差自己涌过去', t, 230.9, 238.0, NA)
    # membrane charges & voltage card (note #14)
    va = win(t, 237.7, 243.7, 0.5, 0.5)
    xs = [0.46 + 0.05 * i for i in range(10)]
    flip = ramp(t, 238.6, 241.0)
    ca = win(t, 234.8, 244.3, 0.5, 0.5)
    rgb = charges_row(rgb, v, xs, 0.33, +1, ca, (255, 120, 110))
    rgb = charges_row(rgb, v, xs, 0.66, -1, ca * (1 - flip), (120, 170, 255))
    rgb = charges_row(rgb, v, xs, 0.66, +1, ca * flip, (255, 120, 110))
    if va > 0:
        rgb = dim_all(rgb, 0.45 * va)
        rgb = charges_row(rgb, v, xs, 0.33, +1, va, (255, 120, 110))
        rgb = charges_row(rgb, v, xs, 0.66, -1, va * (1 - flip), (120, 170, 255))
        rgb = charges_row(rgb, v, xs, 0.66, +1, va * flip, (255, 120, 110))
        x0, y0, w, h = 60, 70, 520, 420
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, va, GOLD)
        paste(rgb, text_sprite('电压差', 52, GOLD), x0 + 28, y0 + 14, va, center=False)
        paste(rgb, text_sprite('膜两侧 · 膜电位', 20, CREAM, False), x0 + 210, y0 + 40, va, center=False)
        mv = -70 + 40 * flip
        paste(rgb, text_sprite(f'{int(round(mv)):+d} mV'.replace('-', '−'), 64, CREAM), x0 + 28, y0 + 100, va, center=False)
        # meter
        mx0, my0, mx1, my1 = x0 + 360, y0 + 100, x0 + 400, y0 + 380
        ov = overlay_layer()
        cv2.rectangle(ov, (mx0, my0), (mx1, my1), col((40, 50, 80), va), -1)
        def MY(m):
            return int(my1 - (m + 90) / 130 * (my1 - my0))
        cv2.rectangle(ov, (mx0, MY(mv)), (mx1, my1), col(GOLD, va), -1)
        for m in (30, 0, -70):
            cv2.line(ov, (mx0 - 8, MY(m)), (mx1 + 8, MY(m)), col(CREAM, 0.7 * va), 1, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        for m, lab in ((30, '+30'), (0, '0'), (-70, '−70')):
            paste(rgb, text_sprite(lab, 15, CREAM, False, False), mx1 + 14, MY(m) - 12, va, center=False)
        paste(rgb, text_sprite('正离子进来', 22, NA), x0 + 28, y0 + 210, va, center=False)
        paste(rgb, text_sprite('→ 膜内变正', 22, CREAM), x0 + 28, y0 + 248, va, center=False)
        paste(rgb, text_sprite('→ 电压跟着变', 22, GOLD), x0 + 28, y0 + 286, va, center=False)
        paste(rgb, text_sprite('神经元在意的正是它', 18, MINT, False), x0 + 28, y0 + 350, ramp(t, 240.7, 241.3) * va, center=False)
    return rgb


CHL = (0.70, 0.55); EYE = (0.733, 0.478)


def f_B_chlamy(t):
    k = ramp(t, 244.0, 266.0)
    z = 1.45 + 0.20 * k
    rgb, v = microbe_frame(t, z, 0.71, 0.42 + 0.03 * k, light=0.0)
    lx, ly = v.pt(0.56, 0.0)
    add_radial(rgb, lx, ly + 40, 160, (120, 200, 255), 0.20 + 0.06 * math.sin(t * 1.4))
    # phototaxis: dashed trajectory toward the light
    ta = win(t, 246.6, 251.6, 0.4, 0.4)
    if ta > 0:
        c0 = v.pt(0.70, 0.40); c1 = (lx + 30, ly + 120)
        ov = overlay_layer()
        n = 18
        off = (t * 2.0) % 1.0
        for i in range(n):
            q = (i + off) / n
            x = c0[0] + (c1[0] - c0[0]) * q
            y = c0[1] + (c1[1] - c0[1]) * q - 40 * math.sin(math.pi * q)
            cv2.circle(ov, (int(x), int(y)), 4, col((170, 230, 255), ta * (1 - 0.5 * q)), -1, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        tag(rgb, '朝光游', (c0[0] + c1[0]) / 2 + 70, (c0[1] + c1[1]) / 2, ta, (170, 230, 255))
    ex, ey = v.pt(*EYE)
    ea = win(t, 249.0, 259.5, 0.4, 0.5)
    rgb = ring(rgb, ex, ey, 26 + 3 * math.sin(t * 5), (255, 140, 80), ea, 3)
    add_radial(rgb, ex, ey, 20, (255, 150, 70), 0.4 * ea * (0.6 + 0.4 * math.sin(t * 5)))
    tag(rgb, '眼点：谁在感光？', ex + 120, ey - 30, win(t, 249.1, 255.0, 0.4, 0.4), (255, 150, 80))
    card(rgb, SPR('card_chlamy'), 36, 96, t, 245.3, 250.9, target=v.pt(*CHL), accent=(140, 220, 110))
    chip(rgb, '故事从这里讲起 · 诺奖新闻稿', t, 251.5, 256.3, GOLD)
    chip(rgb, '2002 · 衣藻的一种蛋白 → 爪蟾卵母细胞', t, 256.4, 268.0, GOLD)
    # protein lifted from eyespot → oocyte PIP that becomes the next shot
    pa = ramp(t, 258.9, 259.6)
    if pa > 0:
        ooc = SPR('oocyte')
        grow = ramp(t, 266.9, 267.875)
        r0 = 150
        if grow < 1:
            pip = circle_crop(ooc[..., :3], 0.5, 0.5, 330, r0, (230, 200, 120))
            px_, py_ = W - 250, 320
            # protein travelling eyespot → pip
            if 259.3 < t < 261.5:
                q = ease((t - 259.3) / 2.2)
                paste(rgb, ion_sprite(10, (120, 240, 190), ''), ex + (px_ - ex) * q, ey + (py_ - ey) * q - 60 * math.sin(math.pi * q), 1.0)
            # retinal + light into PIP (264.4)
            if 264.3 < t < 265.6:
                q = ease((t - 264.3) / 1.3)
                paste(rgb, ion_sprite(8, (255, 180, 90), ''), px_ - 220 + 220 * q, py_ - 200 + 200 * q, 1.0)
            if grow > 0:
                # PIP grows into the next shot's first frame (true zoom, ends pixel-identical)
                g = ease(grow)
                sc = 150 / 330 + (1 - 150 / 330) * g
                R_ = r0 + (760 - r0) * g
                cx_, cy_ = px_ + (W / 2 - px_) * g, py_ + (H / 2 - py_) * g
                M = np.array([[sc, 0, cx_ - sc * W / 2], [0, sc, cy_ - sc * H / 2]], np.float32)
                big = cv2.warpAffine(ooc[..., :3], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.04, 0.06, 0.13))
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                cm = np.clip(R_ - np.sqrt((xx - cx_) ** 2 + (yy - cy_) ** 2), 0, 1)[..., None]
                rgb = rgb * (1 - cm) + big * cm
            else:
                paste(rgb, pip, px_, py_, pa)
                tag(rgb, '爪蟾卵母细胞的膜', px_, py_ + r0 + 24, pa, (230, 200, 120))
                tag(rgb, '自己不感光', px_, py_ - r0 - 22, win(t, 261.9, 264.3, 0.3, 0.3), (190, 190, 210))
                tag(rgb, '+ 视黄醛 + 光', px_, py_ - r0 - 22, win(t, 264.4, 266.9, 0.3, 0.2), (255, 180, 90))
                flash = math.exp(-((t - 265.7) / 0.25) ** 2)
                add_radial(rgb, px_, py_, 110, (170, 220, 255), 0.6 * flash)
        else:
            rgb = ooc[..., :3].copy()
    return rgb


def f_B(t):
    if t < 205.4:
        rgb = f_B_archaea(t)
        if t > 204.6:
            rgb = mix(rgb, f_B_pump(t), ramp(t, 204.6, 205.4))
    elif t < 244.6:
        rgb = f_B_pump(t)
        if t > 243.8:
            rgb = mix(rgb, f_B_chlamy(t), ramp(t, 243.8, 244.6))
    else:
        rgb = f_B_chlamy(t)
    return rgb


# ================================================================== orchestration
CHUNKS = [('s00_sting', f_sting), ('s01_open', f_open), ('s02_1979', f_1979), ('s03_microbe', f_microbe),
          ('s04_crick', f_crick), ('s12_select', f_select), ('s05_nobel', f_nobel), ('s06_switch', f_switch),
          ('s07_title', f_title), ('s13_spike', f_spike), ('s08_early', f_early), ('s09_chr2', f_chr2),
          ('s14_orexin', f_orexin), ('s10_mouseA', f_mouse), ('sB_head', f_B)]


def frames_of(name):
    if name == 'sB_head':
        return int(round(B0 * FPS)), END_F
    t0, t1 = SEG[name]
    return int(round(t0 * FPS)), int(round(t1 * FPS))


def render_one(name):
    fn = dict(CHUNKS)[name]
    f0, f1 = frames_of(name)
    SEG6.mkdir(parents=True, exist_ok=True)
    out = SEG6 / f'{name}.mp4'
    write_segment(out, f0, f1, fn)
    return name, f1 - f0


def still(name_or_t, out):
    t = float(name_or_t)
    fn = None
    for n, f in CHUNKS:
        f0, f1 = frames_of(n)
        if f0 <= round(t * FPS) < f1:
            fn = f
    rgb = fn(t)
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(out)


def render(names):
    with Pool(min(7, len(names))) as pool:
        for n, k in pool.imap_unordered(render_one, sorted(names, key=lambda n: -(frames_of(n)[1] - frames_of(n)[0]))):
            print('rendered', n, k, flush=True)


def probe(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], text=True))


def run(cmd):
    subprocess.run(cmd, check=True)


def mux():
    WORK.mkdir(exist_ok=True)
    head = [SEG6 / f'{n}.mp4' for n, _ in CHUNKS]
    # old chain tail from the pure-oocyte frame onward
    tail_b = WORK / 'sB_tail.mp4'
    run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(SEGS_OLD / 'sB_chain.mp4'), '-vf',
         f'trim=start_frame={OLD_SB_HANDOFF},setpts=PTS-STARTPTS', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
         '-crf', '17', '-pix_fmt', 'yuv420p', '-r', '24', str(tail_b)])
    order = [s['name'] for s in plan['segments']]
    rest = [SEGS_OLD / f'{n}.mp4' for n in order[order.index('s17_credit'):]]
    lst = WORK / 'concat_v6.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in head + [tail_b] + rest))
    raw = WORK / 'video_concat_v6.mp4'
    run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c:v', 'libx264',
         '-preset', 'fast', '-crf', '18', '-an', '-pix_fmt', 'yuv420p', '-r', '24', str(raw)])
    d = probe(raw)
    print(f'CONCAT {d:.3f}', flush=True)
    final_v = WORK / 'video_full_v6.mp4'
    if d >= FILM_DUR - 0.05:
        run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(raw), '-t', f'{FILM_DUR:.3f}', '-c:v', 'copy', '-an', str(final_v)])
    else:
        pad = FILM_DUR - d
        run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(raw), '-vf', f'tpad=stop_mode=clone:stop_duration={pad:.3f}',
             '-t', f'{FILM_DUR:.3f}', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', '-pix_fmt', 'yuv420p', str(final_v)])
    vo = OUT / 'work' / 'vo_full.m4a'
    ass = OUT / 'captions.ass'
    ass_esc = str(ass).replace('\\', '/').replace(':', '\\:')
    master = HERE / 'E2_cut10_full_lowres_INTERNAL.mp4'
    share = HERE / 'E2_cut10_full_lowres_share_INTERNAL.mp4'
    pub = OUT / 'E2_cut10_full_lowres_share.mp4'
    pub_m = pub.stat().st_mtime
    run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(final_v), '-i', str(vo), '-vf',
         f'ass={ass_esc}:fontsdir=/usr/share/fonts/opentype/noto', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
         '-preset', 'fast', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(master)])
    run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(master), '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(share)])
    assert pub.stat().st_mtime == pub_m, 'public share touched!'
    print('MASTER', probe(master), 'SHARE_INTERNAL', probe(share), flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == 'render':
        names = args[1:] or [n for n, _ in CHUNKS]
        render(names)
    if args and args[0] == 'still':
        still(args[1], args[2])
    if not args or 'mux' in args:
        mux()
