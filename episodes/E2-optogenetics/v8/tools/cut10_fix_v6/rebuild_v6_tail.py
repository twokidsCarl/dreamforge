#!/usr/bin/env python3
"""fix_v6 round 2 — re-render film 276.0 s → 865.04 s (old B-tail / credit / memory / eye / reg / close).

Why: round-1 self-watch found the kept tail still broke gate 3 (flat chamber / card-grid / gradient-card
main pictures), note-#2-class top streaks (5:34–5:46), pillarbox (6:18–6:30), a Crick face crop at 14:18
(note-#4 class) and long static holds against verb-heavy VO. Same rules as round 1: Goodsell / illustrated
plates as main picture, overlays only for mechanism beats, cue-locked to captions.ass.

usage: rebuild_v6_tail.py [render [names..]] | [mux]
"""
from __future__ import annotations
import math, subprocess, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import rebuild_v6 as R
from rebuild_v6 import (tag, leader, ring, charges_row, mix, dim_all, panel_bg, vm_panel, draw_ions, crowd_frame,
                        relay_cascade, circle_crop, scaled, CROWD_SOMA, SPR, MASK, mouse_pip, fiber_glow)
from v6lib import *  # noqa

HERE = Path(__file__).parent
SEG6 = HERE / 'segs'
PL = HERE / 'plates'
T0 = 276.0
F0 = int(round(T0 * FPS))           # 6624
F_END = int(round(865.04 * FPS))    # 20761

_P = {}


def TP(key):
    if key in _P:
        return _P[key]
    spec = {
        'nphr': (GEN / 'g6_nphr.png', None, 1.35), 'chrimson': (GEN / 'g6_chrimson.png', None, 1.35),
        'dg': (GEN / 'g6_dg.png', None, 1.3), 'goggles': (GEN / 'g6_goggles.png', None, 1.3),
        'regdocs': (GEN / 'g6_regdocs.png', None, 1.3), 'envA': (GEN / 'g6_envA.png', None, 1.25),
        'envB': (GEN / 'g6_envB.png', None, 1.25), 'envAf': (GEN / 'g6_envAfreeze.png', None, 1.25),
        'retina': (GEN / 'sf11_inset.png', None, 1.3), 'eye': (GEN / 'sf11d_eye.png', None, 1.3),
        'cochlea': (GEN / 'g6_cochlea.png', None, 1.3), 'mfront': (GEN / 'c9_mfront.png', None, 1.25),
        'endcard': (PL / 'endcard.png', None, 1.0),
    }.get(key)
    if spec is None:
        _P[key] = R.P(key)
    else:
        _P[key] = Plate(*spec)
    return _P[key]


_TM = {}


def TMASK(key):
    if key in _TM:
        return _TM[key]
    if key == 'dg_gold':
        m = hue_mask(TP('dg'), 12, 32, smin=80, vmin=150, blur=11)
    elif key == 'chr2_core':     # membrane-spanning core of the dimer (for 「只保留通道那一段」)
        m = disc_mask(R.P('chr2'), [(0.49, 0.47)], 0.15, 0.4)
    elif key == 'chr2_tail':     # cytoplasmic part of the dimer
        p = R.P('chr2'); m = np.zeros((p.h, p.w), np.float32)
        m[int(0.565 * p.h):int(0.66 * p.h), int(0.35 * p.w):int(0.64 * p.w)] = 1
        m = cv2.GaussianBlur(m, (31, 31), 0)
    elif key == 'retina_pr':
        p = TP('retina'); m = np.zeros((p.h, p.w), np.float32)
        m[int(0.66 * p.h):int(0.82 * p.h)] = 1
        m = cv2.GaussianBlur(m, (41, 41), 0)
    _TM[key] = m
    return m


OLD = None


def old_still():
    global OLD
    if OLD is None:
        im = cv2.cvtColor(cv2.imread(str(PL / 'old_f2212.png')), cv2.COLOR_BGR2RGB)
        OLD = im.astype(np.float32) / 255
    return OLD


def hold(t, a, b):
    """0→1 over [a,b] then stays"""
    return ramp(t, a, b)


def flash_pulse(t, t0, w=0.12):
    return math.exp(-((t - t0) / w) ** 2)


# ================================================================== beats
def f_relay(t):
    p = R.P('relay')
    u = (t - 276.0) / 10.0
    rgb, v = p.cam(1.02 + 0.04 * u, 0.36, 0.47)
    ca = win(t, 278.9, 285.9, 0.3, 0.4)
    if ca > 0:
        fl = flash_pulse(t, 279.4, 0.18)
        rgb = add_glow(rgb, p.warp_mask(MASK('relay_squig'), v), (180, 230, 255), 1.4 * fl)
        rgb = mix(rgb, relay_cascade(rgb.copy(), v, t, [279.7, 280.9, 282.2, 283.5], 1.6), ca)
        x, y = v.pt(0.575, 0.36)
        tag(rgb, '别处的孔', x, y - 40, win(t, 283.4, 285.9, 0.3, 0.3), NA)
    chip(rgb, '关键的一句', t, 277.1, 278.9, GOLD)
    chip(rgb, '早先：一个分子接光 → 一层层传话 → 别处的孔', t, 278.9, 285.6, GOLD)
    if t < 276.6:
        rgb = mix(old_still(), rgb, ramp(t, 276.0, 276.6))
    if t > 285.3:
        rgb = mix(rgb, f_onemol(t), ramp(t, 285.3, 285.9))
    return rgb


def chr2_state(t, rgb, v, lit, op):
    p = R.P('chr2')
    beam = p.warp_mask(MASK('chr2_beam'), v)
    rgb = dim(rgb, beam, 0.75 * (1 - lit), 0.2)
    pore = p.warp_mask(MASK('chr2_pore'), v)
    rgb = mix(rgb, np.array([0.22, 0.62, 0.56], np.float32), (0.8 * (1 - op) * pore)[..., None])
    rgb = add_glow(rgb, pore, CYAN, 0.6 * op)
    return rgb


def f_onemol(t):
    p = R.P('chr2')
    u = (t - 285.3) / 21.6
    rgb, v = p.cam(1.18 - 0.08 * ease(u), 0.49, 0.47)
    lit = ramp(t, 289.6, 290.0)
    op = ramp(t, 289.9, 290.2)
    rgb = chr2_state(t, rgb, v, lit, op)
    # 同一个分子：接光的部分 + 孔
    ia = win(t, 286.9, 292.4, 0.4, 0.4)
    r_ = v.pt(0.385, 0.44); po = v.pt(0.435, 0.40)
    rgb = ring(rgb, r_[0], r_[1], 22, (255, 170, 80), ia, 3)
    tag(rgb, '接光：视黄醛', r_[0] - 120, r_[1] - 70, ia, (255, 170, 80))
    rgb = ring(rgb, po[0], po[1] + 30, 18, CYAN, ia, 3)
    tag(rgb, '放行离子的孔', po[0] + 30, po[1] - 110, ia, CYAN)
    sx0, sy0 = v.pt(0.34, 0.30); sx1, sy1 = v.pt(0.475, 0.64)
    ov = overlay_layer()
    cv2.rectangle(ov, (int(sx0), int(sy0)), (int(sx1), int(sy1)), col(GOLD, 0.9 * ia), 2, cv2.LINE_AA)
    rgb = comp(rgb, ov)
    tag(rgb, '同一个分子', (sx0 + sx1) / 2, sy1 + 24, ia, GOLD)
    add_radial(rgb, r_[0], r_[1], 20, (255, 170, 80), 0.9 * flash_pulse(t, 289.8, 0.25))
    # truncated: only the channel-forming part
    tr = win(t, 295.1, 301.6, 0.5, 0.5)
    if tr > 0:
        rgb = dim(rgb, p.warp_mask(TMASK('chr2_tail'), v), 0.9 * tr, 0.8)
        x, y = v.pt(0.495, 0.63)
        tag(rgb, '只保留形成通道的那一段 → 仍能打开', x, y + 40, tr, MINT)
    ia2 = ramp(t, 290.1, 290.6) * (1 - ramp(t, 306.0, 306.8))
    for px_, sd in ((0.435, 3), (0.555, 4)):
        rgb = draw_ions(rgb, v, t, 7, 0.45, px_, 0.36, 0.62, NA, 0.0125, ia2, seed=sd, spread=0.05)
    # 一个基因
    ga = win(t, 301.4, 307.0, 0.5, 0.4)
    if ga > 0:
        rgb = gene_glyph(rgb, W - 240, 200, t, ga)
        paste(rgb, text_sprite('送进这一个基因', 20, CREAM), W - 240, 290, ga)
    chip(rgb, '这个蛋白不一样', t, 285.5, 286.9, MINT)
    chip(rgb, '光一到，门就动', t, 289.5, 292.2, CYAN)
    chip(rgb, '中间不用传话', t, 292.2, 295.1, MINT, '诺奖科学背景')
    chip(rgb, '蛋白本身就够', t, 298.4, 301.4, MINT)
    chip(rgb, '要装进别的细胞：送进一个基因', t, 301.4, 306.9, GOLD)
    if t > 306.5:
        rgb = mix(rgb, f_chr2b(t), ramp(t, 306.5, 307.1))
    return rgb


def gene_glyph(rgb, cx, cy, t, al):
    ov = overlay_layer()
    for k in range(60):
        x = cx - 120 + k * 4
        ph = k * 0.22 + t * 2.0
        y1 = cy + 26 * math.sin(ph); y2 = cy - 26 * math.sin(ph)
        cv2.circle(ov, (int(x), int(y1)), 4, col((255, 200, 110), al), -1, cv2.LINE_AA)
        cv2.circle(ov, (int(x), int(y2)), 4, col((120, 220, 190), al), -1, cv2.LINE_AA)
        if k % 4 == 0:
            cv2.line(ov, (int(x), int(y1)), (int(x), int(y2)), col((200, 200, 220), 0.6 * al), 2, cv2.LINE_AA)
    return comp(rgb, ov)


def current_panel(rgb, t, al, mode, t_on, x0=860, y0=34, w=380, h=200):
    """光电流 trace: 'step' = continuous light (peak→plateau desensitisation), 'pulse' = pulse train."""
    if al <= 0:
        return rgb
    rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, al, CYAN)
    paste(rgb, text_sprite('光电流', 24, CYAN), x0 + 16, y0 + 6, al, center=False)
    ov = overlay_layer()
    gx0, gx1 = x0 + 20, x0 + w - 20
    span = 8.0
    pts = []; lp = []
    for i in range(200):
        tt = t - span + span * i / 199
        L, I = light_current(tt, mode, t_on)
        pts.append((gx0 + (gx1 - gx0) * i / 199, y0 + 170 - 95 * I))
        lp.append((gx0 + (gx1 - gx0) * i / 199, y0 + 58 - 10 * L))
    for i in range(199):
        cv2.line(ov, tuple(map(int, lp[i])), tuple(map(int, lp[i + 1])), col((120, 200, 255), al), 3, cv2.LINE_AA)
        cv2.line(ov, tuple(map(int, pts[i])), tuple(map(int, pts[i + 1])), col(YELLOW, al), 3, cv2.LINE_AA)
    rgb = comp(rgb, ov)
    paste(rgb, text_sprite('光', 14, (150, 210, 255), False, False), x0 + w - 40, y0 + 36, al, center=False)
    return rgb


def light_current(tt, mode, t_on):
    if tt < t_on:
        return 0.0, 0.0
    if mode == 'step':
        d = tt - t_on
        return 1.0, (1 - math.exp(-d / 0.08)) * (0.45 + 0.55 * math.exp(-d / 1.6))
    d = (tt - t_on) % 0.6
    L = 1.0 if d < 0.12 else 0.0
    I = (1 - math.exp(-d / 0.03)) * math.exp(-max(0, d - 0.12) / 0.06) if d < 0.5 else 0.0
    return L, I


def f_chr2b(t):
    p = R.P('chr2')
    u = (t - 306.5) / 38.0
    rgb, v = p.cam(1.02 + 0.10 * ease(u), 0.50, 0.47)
    mode, t_on = ('step', 325.6) if t < 336.85 else ('pulse', 337.0)
    lit_cur = 0.0; cur = 0.0
    if 317.2 <= t < 325.4:
        lit_cur, cur = 1.0, 0.85
    elif t >= 325.6:
        lit_cur, cur = light_current(t, mode, t_on)
    lit = max(lit_cur, 0.0)
    rgb = chr2_state(t, rgb, v, lit, min(1.0, cur * 1.4))
    # ions: rate follows current (peak → plateau, pulses)
    for px_, sd in ((0.435, 5), (0.555, 6)):
        rgb = draw_ions(rgb, v, t, max(1, int(9 * cur)), 0.5, px_, 0.36, 0.62, NA, 0.0125, min(1, cur * 1.5), seed=sd, spread=0.05)
        rgb = draw_ions(rgb, v, t + 0.3, max(1, int(4 * cur)), 0.5, px_, 0.36, 0.62, HION, 0.0075, min(1, cur * 1.5) * win(t, 318.0, 325.5, 0.4, 0.4), seed=sd + 9, spread=0.04)
    la = win(t, 318.2, 325.4, 0.4, 0.4)
    x, y = v.pt(0.66, 0.24)
    tag(rgb, 'Na^{+}（大）  H^{+}（小）… 阳离子都放行', x, y, la, NA)
    dep = win(t, 320.2, 325.4, 0.4, 0.4)
    xs = [0.08 + 0.1 * i for i in range(10)]
    rgb = charges_row(rgb, v, xs, 0.70, +1, dep, (255, 120, 110))
    x, y = v.pt(0.20, 0.76); tag(rgb, '膜内变正 = 去极化', x, y, dep, (255, 140, 120))
    # oocyte / cultured cell PIPs
    pa = win(t, 310.8, 317.3, 0.4, 0.4)
    if pa > 0:
        if not hasattr(f_chr2b, 'pips'):
            f_chr2b.pips = (circle_crop(SPR('oocyte')[..., :3], 0.5, 0.5, 330, 80, (230, 200, 120)),
                            circle_crop(R.P('neuron').img, 0.70, 0.52, int(R.P('neuron').w * 0.16), 80, MINT))
        a1 = pa; a2 = pa * ramp(t, 314.2, 314.7)
        paste(rgb, f_chr2b.pips[0], 900, 160, a1); paste(rgb, text_sprite('卵母细胞 ✓', 18, CREAM), 900, 262, a1)
        paste(rgb, f_chr2b.pips[1], 1110, 160, a2); paste(rgb, text_sprite('哺乳动物培养细胞 ✓', 18, CREAM), 1110, 262, a2)
    pan = win(t, 325.5, 344.3, 0.4, 0.5)
    rgb = current_panel(rgb, t, pan, mode, t_on)
    if pan > 0:
        tg = win(t, 326.3, 331.4, 0.3, 0.3); paste(rgb, text_sprite('高峰', 16, YELLOW), 900, 110, tg)
        tg2 = win(t, 329.0, 336.8, 0.3, 0.3); paste(rgb, text_sprite('→ 较低的平台', 16, YELLOW), 1150, 160, tg2)
    chip(rgb, '2003 · 第二种：通道视紫红质二（ChR2）', t, 307.0, 314.2, MINT)
    chip(rgb, '蓝光直接打开它', t, 317.2, 320.2, CYAN)
    chip(rgb, '持续照着：电流从高峰落到平台', t, 325.5, 331.3, YELLOW)
    chip(rgb, '通道会脱敏：一扇会疲劳的门', t, 331.3, 336.85, AMBER)
    chip(rgb, '一串短脉冲，不是一直照着', t, 336.85, 344.3, CYAN)
    if t > 343.6:
        rgb = mix(rgb, f_neuron(t), ramp(t, 343.6, 344.3))
    return rgb


def f_neuron(t):
    p = R.P('neuron')
    u = (t - 343.6) / 24.4
    rgb, v = p.cam(1.12 + 0.10 * ease(u), 0.66, 0.50)
    soma = v.pt(0.73, 0.55)
    # single big depolarisation → spike (344.4–349.1)
    dep = ramp(t, 344.6, 347.0)
    add_radial(rgb, soma[0], soma[1], 70, (120, 200, 255), 0.35 * dep * (1 - ramp(t, 347.2, 347.5)))
    sp = flash_pulse(t, 347.35, 0.12)
    add_radial(rgb, soma[0], soma[1], 60, (255, 200, 120), 1.1 * sp)
    # pulse-driven spikes (355.3–364.8): light pulse then spike 8 ms later (shown slowed)
    pulses = [355.6 + 0.8 * k for k in range(12)]
    for pt in pulses:
        if pt - 0.1 < t < pt + 0.6:
            add_radial(rgb, soma[0] - 60, soma[1] - 80, 50, (110, 190, 255), 0.9 * flash_pulse(t, pt, 0.07))
            add_radial(rgb, soma[0], soma[1], 55, (255, 200, 120), 1.0 * flash_pulse(t, pt + 0.12, 0.08))
            # synaptic: signal runs down the axon (lower-left)
            if 359.8 < pt:
                q = ease((t - pt - 0.12) / 0.45)
                if 0 < q < 1:
                    a0 = soma; a1 = v.pt(0.42, 0.98)
                    paste(rgb, ion_sprite(8, YELLOW, ''), a0[0] + (a1[0] - a0[0]) * q, a0[1] + (a1[1] - a0[1]) * q, 1 - q * 0.3)
    # Vm panel: depolarisation → spike; then pulse train
    if t < 351.0:
        rgb = vm_panel(rgb, t, win(t, 344.4, 350.6, 0.4, 0.4), 347.0, 1.2, x0=60, y0=120)
    pa = win(t, 355.2, 365.4, 0.4, 0.4)
    if pa > 0:
        x0, y0, w, h = 60, 120, 380, 190
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, pa, MINT)
        paste(rgb, text_sprite('光的节拍 → 放电的节拍', 22, MINT), x0 + 14, y0 + 6, pa, center=False)
        ov = overlay_layer()
        for i, pt in enumerate(pulses):
            if pt <= t:
                xx = x0 + 24 + (pt - 355.6) / (0.8 * 11) * (w - 60)
                cv2.rectangle(ov, (int(xx), y0 + 64), (int(xx + 6), y0 + 92), col(CYAN, pa), -1)
                cv2.line(ov, (int(xx + 3), y0 + 160), (int(xx + 3), y0 + 108), col(AMBER, pa), 3, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('蓝光脉冲', 14, CYAN, False, False), x0 + w - 80, y0 + 40, pa, center=False)
        paste(rgb, text_sprite('锋电位（毫秒级跟随）', 14, AMBER, False, False), x0 + 20, y0 + 164, pa, center=False)
    chip(rgb, '去极化又快又够大 → 自己打出锋电位', t, 344.4, 349.1, AMBER)
    chip(rgb, '2005 · ChR2 送进培养的哺乳动物神经元', t, 349.1, 355.3, MINT)
    chip(rgb, '短脉冲蓝光：毫秒尺度可靠驱动', t, 355.3, 359.85, CYAN)
    chip(rgb, '也能控制突触传递', t, 359.85, 362.5, YELLOW)
    chip(rgb, '光的节拍 = 放电的节拍', t, 362.5, 366.0, MINT)
    if t > 366.6:
        rgb = mix(rgb, f_authors(t), ramp(t, 366.6, 367.3))
    return rgb


def f_authors(t):
    p = R.P('laur')
    rgb, v = p.cam(1.0 + 0.03 * ramp(t, 366.6, 376.0), 0.5, 0.46)
    rgb = dim_all(rgb, 0.35)
    a = win(t, 367.4, 376.3, 0.4, 0.4)
    paste(rgb, text_sprite('当年论文的署名', 30, CREAM), W / 2 - 230, 70, a)
    paste(rgb, text_sprite('≠', 40, GOLD), W / 2, 70, a)
    paste(rgb, text_sprite('后来的授奖名单', 30, CREAM), W / 2 + 230, 70, a)
    chip(rgb, '不是同一份名单', t, 371.2, 376.3, GOLD)
    if t > 375.6:
        rgb = mix(rgb, f_term(t), ramp(t, 375.6, 376.3))
    return rgb


def f_term(t):
    p = R.P('open')
    u = (t - 375.6) / 15.0
    rgb, v = p.cam(1.10 + 0.08 * ease(u), 0.62, 0.48)
    # targeted class (cyan pyramidal) glows on 「基因决定哪一类」; beam pulses on 「光决定什么时候拨」
    cls = win(t, 384.5, 390.6, 0.4, 0.4)
    if cls > 0:
        m = hue_mask(p, 82, 100, smin=90, vmin=170, blur=9) if not hasattr(f_term, 'm') else f_term.m
        f_term.m = m
        rgb = add_glow(rgb, p.warp_mask(m, v), (140, 230, 255), 0.45 * cls)
    bp = 0.0
    if 387.2 < t < 390.6:
        bp = 1.0 if ((t - 387.2) % 0.7) < 0.2 else 0.0
    x, y = v.pt(0.95, 0.06)
    add_radial(rgb, x - 40, y + 40, 90, (120, 200, 255), 0.8 * bp)
    ca = win(t, 378.4, 390.6, 0.5, 0.4)
    if ca > 0:
        x0, y0, w, h = 60, 90, 560, 300
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, ca, GOLD)
        paste(rgb, text_sprite('光遗传学', 52, GOLD), x0 + 26, y0 + 10, ca, center=False)
        paste(rgb, text_sprite('= 光学 + 遗传靶向', 26, CREAM), x0 + 250, y0 + 34, ca, center=False)
        r1 = ca * ramp(t, 384.5, 385.0); r2 = ca * ramp(t, 387.2, 387.7)
        paste(rgb, text_sprite('基因 → 哪一类细胞装上开关', 24, (150, 230, 255)), x0 + 26, y0 + 130, r1, center=False)
        paste(rgb, text_sprite('光 → 什么时候拨', 24, (150, 210, 255)), x0 + 26, y0 + 190, r2, center=False)
    chip(rgb, '2006 · 「光遗传学」写进论文', t, 377.4, 384.4, GOLD)
    if t > 389.8:
        rgb = mix(rgb, f_motor(t), ramp(t, 389.8, 390.5))
    return rgb


def f_motor(t):
    pw, pf = R.P('mwake'), TP('mfront')
    u = (t - 389.8) / 28.0
    xf = ramp(t, 404.3, 405.6)
    rw, vw = pw.cam(1.08 + 0.05 * u, 0.50, 0.44)
    rf, vf = pf.cam(1.05 + 0.04 * u, 0.52, 0.46)
    L = win(t, 395.8, 412.0, 0.3, 0.6)
    for rgb_, v_, top, imp, w_ in ((rw, vw, (0.60, 0.0), (0.595, 0.37), 1 - xf), (rf, vf, (0.61, 0.0), (0.63, 0.24), xf)):
        if w_ > 0:
            fiber_glow(rgb_, v_, top, imp, L)
            x, y = v_.pt(*imp)
            add_radial(rgb_, x, y, 30, (110, 200, 255), 1.1 * L)
    rgb = mix(rw, rf, xf)
    # PIP brain motor cortex
    pa = win(t, 395.8, 404.3, 0.4, 0.4)
    if pa > 0:
        if not hasattr(f_motor, 'pip'):
            f_motor.pip = circle_crop(R.P('brain').img, 0.42, 0.33, int(R.P('brain').w * 0.13), 100, CYAN)
        paste(rgb, f_motor.pip, 170, 250, pa)
        paste(rgb, text_sprite('运动皮层 · 只驱动兴奋性神经元', 18, CREAM), 170, 372, pa)
    ta = win(t, 407.9, 417.8, 0.4, 0.4)
    if ta > 0:
        x0, y0 = 860, 40
        rgb = panel_bg(rgb, x0, y0, x0 + 380, y0 + 110, ta, MINT)
        ov = overlay_layer()
        cv2.line(ov, (x0 + 40, y0 + 70), (x0 + 340, y0 + 70), col(CREAM, ta), 2, cv2.LINE_AA)
        a1 = ta * ramp(t, 410.6, 411.0); a2 = ta * ramp(t, 412.7, 413.1)
        cv2.circle(ov, (x0 + 60, y0 + 70), 9, col(MINT, a1), -1, cv2.LINE_AA)
        cv2.circle(ov, (x0 + 320, y0 + 70), 9, col(CYAN, a2), -1, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('2005 · 培养皿神经元', 16, MINT), x0 + 110, y0 + 36, a1)
        paste(rgb, text_sprite('2007 · 活体脑', 16, CYAN), x0 + 300, y0 + 36, a2)
        paste(rgb, text_sprite('约两年', 16, CREAM, False), x0 + 190, y0 + 92, ta)
    chip(rgb, '培养皿里的光还不是活的脑', t, 390.2, 393.8, CREAM)
    chip(rgb, '2007 · 光纤把蓝光送进运动皮层', t, 393.8, 402.5, CYAN)
    chip(rgb, '不另外添加视黄醛', t, 402.5, 404.2, (255, 170, 80))
    chip(rgb, '光也足够让动物做出行为', t, 404.2, 407.9, MINT)
    if t > 417.2:
        rgb = mix(rgb, f_nphr(t), ramp(t, 417.2, 417.9))
    return rgb


NPHR = (0.38, 0.47)


def f_nphr(t):
    p = TP('nphr')
    u = (t - 417.2) / 18.6
    rgb, v = p.cam(1.12 + 0.12 * ease(u), 0.42, 0.47)
    lit = ramp(t, 425.9, 426.4)
    beam = hue_mask(p, 18, 34, smin=60, vmin=150, blur=21, region=(0.38, 0.0, 0.80, 0.36)) if not hasattr(f_nphr, 'b') else f_nphr.b
    f_nphr.b = beam
    rgb = dim(rgb, p.warp_mask(beam, v), 0.8 * (1 - lit), 0.3)
    # Cl- pumped one by one: outside → through pump → inside
    if t > 426.4:
        per = 0.9
        n = int((t - 426.4) / per)
        ph = ((t - 426.4) % per) / per
        pts = [(0.43, 0.20), (0.38, 0.33), (0.38, 0.60), (0.35, 0.74)]
        seg = min(2, int(ph * 3)); w_ = ph * 3 - seg
        fx = pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * ease(w_)
        fy = pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * ease(w_)
        x, y = v.pt(fx, fy)
        cl = ion_sprite(max(9, int(v.px(0.011))), (140, 235, 140), '−')
        paste(rgb, cl, x, y, 1.0)
        for j in range(min(n, 12)):
            x, y = v.pt(0.18 + (j * 0.37 % 1) * 0.42, 0.72 + (j * 0.61 % 1) * 0.12 + 0.005 * math.sin(t + j))
            paste(rgb, cl, x, y, 0.9)
    # outside Cl- pool
    if t > 419.0:
        cl = ion_sprite(max(9, int(v.px(0.011))), (140, 235, 140), '−')
        for j in range(8):
            x, y = v.pt(0.48 + (j * 0.37 % 1) * 0.40, 0.12 + (j * 0.61 % 1) * 0.12 + 0.005 * math.cos(t + j))
            paste(rgb, cl, x, y, 0.85 * ramp(t, 425.9, 426.5))
    x, y = v.pt(0.62, 0.22)
    tag(rgb, 'Cl^{-} 氯离子被泵进细胞', x, y, win(t, 426.5, 433.0, 0.4, 0.4), (140, 235, 140))
    # Vm going more negative, away from threshold
    va = win(t, 429.4, 436.0, 0.4, 0.4)
    if va > 0:
        x0, y0, w, h = 900, 250, 330, 230
        rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, va, (140, 235, 140))
        paste(rgb, text_sprite('膜电位', 22, CREAM), x0 + 14, y0 + 6, va, center=False)
        mv = -70 - 20 * ramp(t, 429.6, 432.5)
        def Y(m):
            return y0 + 210 - (m + 100) / 60 * 160
        ov = overlay_layer()
        cv2.line(ov, (x0 + 20, int(Y(-55))), (x0 + w - 20, int(Y(-55))), col(AMBER, va), 2, cv2.LINE_AA)
        cv2.rectangle(ov, (x0 + 140, int(Y(mv))), (x0 + 190, y0 + 210), col((140, 235, 140), va), -1)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite('放电门槛', 15, AMBER, False, False), x0 + 20, Y(-55) - 24, va, center=False)
        paste(rgb, text_sprite(f'{int(round(mv))} mV'.replace('-', '−'), 22, CREAM), x0 + 210, Y(mv) - 16, va, center=False)
    card(rgb, SPR('card_nphr'), 36, 30, t, 420.0, 425.8, target=v.pt(*NPHR), accent=(232, 170, 70))
    chip(rgb, '只有开还不够', t, 417.7, 419.9, CREAM)
    chip(rgb, '黄光照上去 → 氯离子被泵进细胞', t, 425.9, 429.5, (232, 190, 80))
    chip(rgb, '离放电门槛更远 → 锋电位被按住', t, 429.5, 435.6, (140, 235, 140))
    if t > 435.3:
        rgb = mix(rgb, f_dual(t), ramp(t, 435.3, 435.9))
    return rgb


def f_dual(t):
    if t < 442.4:
        a, va = R.P('chr2').cam(1.15, 0.49, 0.47)
        a = chr2_state(t, a, va, 1.0, 1.0)
        b, vb = TP('nphr').cam(1.15, 0.40, 0.47)
        rgb = np.concatenate([a[:, 320:960], b[:, 320:960]], axis=1)
        ov = overlay_layer()
        cv2.line(ov, (640, 0), (640, H), col(CREAM, 0.8), 2, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        sa = win(t, 435.9, 442.7, 0.4, 0.3)
        tag(rgb, '蓝光 → 打开（ChR2）', 320, 110, sa * ramp(t, 440.4, 440.8), CYAN)
        tag(rgb, '黄光 → 关掉（NpHR）', 960, 110, sa * ramp(t, 441.5, 441.9), (232, 190, 80))
        rgb = spectrum_strip(rgb, t, sa, [(470, CYAN), (590, (232, 190, 80))])
        chip(rgb, '光谱分开 → 同一套细胞里放两种蛋白', t, 435.9, 442.7, CREAM)
        if t > 442.0:
            rgb = mix(rgb, f_dual_ask(t), ramp(t, 442.0, 442.6))
        return rgb
    return f_dual_ask(t)


def spectrum_strip(rgb, t, al, marks, x0=340, y0=585, w=600):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    for i in range(w):
        nm = 420 + 260 * i / w
        c = wl_rgb(nm)
        cv2.line(ov, (x0 + i, y0), (x0 + i, y0 + 12), col(c, 0.9 * al), 1)
    rgb = comp(rgb, ov)
    for nm, c in marks:
        x = x0 + (nm - 420) / 260 * w
        ov = overlay_layer()
        cv2.line(ov, (int(x), y0 - 26), (int(x), y0 + 18), col(c, al), 3, cv2.LINE_AA)
        rgb = comp(rgb, ov)
        paste(rgb, text_sprite(f'{nm} nm', 15, c, True), x, y0 - 38, al)
    return rgb


def wl_rgb(nm):
    stops = [(420, (110, 80, 255)), (470, (60, 160, 255)), (520, (80, 230, 140)), (570, (240, 230, 80)),
             (600, (255, 160, 50)), (640, (255, 60, 40)), (680, (180, 20, 30))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= nm <= b:
            k = (nm - a) / (b - a)
            return tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
    return stops[-1][1]


def f_dual_ask(t):
    u = (t - 442.0) / 11.0
    push = win(t, 445.6, 448.5, 0.3, 0.3); hold_ = win(t, 448.5, 452.0, 0.3, 0.4)
    drive = (1.0 if ((t - 445.6) % 0.5) < 0.2 else 0.3) * push
    rgb, v = crowd_frame(t, 1.18 + 0.06 * u, 0.44, 0.5, glow=0.7 * drive, dimv=0.85 * hold_, ripple=push, ripple_rate=2.0)
    for colr, a in ((CYAN, push), (AMBER, hold_)):
        if a > 0:
            ov = overlay_layer()
            src = (W * 0.92, -40); tgt = v.pt(*CROWD_SOMA[3])
            pts = np.array([src, (tgt[0] - 90, tgt[1] + 40), (tgt[0] + 90, tgt[1] + 40), (src[0] + 90, src[1])], np.int32)
            cv2.fillConvexPoly(ov, pts, (1, 1, 1, 1), cv2.LINE_AA)
            rgb = add_glow(rgb, cv2.GaussianBlur(ov[..., 3], (0, 0), 10), colr, 0.9 * a)
    pa = win(t, 445.6, 453.0, 0.3, 0.4)
    if pa > 0:
        beh = 1.0 if t < 448.5 else 0.3
        paste(rgb, mouse_pip(), W - 150, 160, pa * beh)
        lab = '行为会不会出现？' if t < 448.5 else '行为会不会消失？'
        paste(rgb, text_sprite(lab, 18, CREAM), W - 150, 280, pa)
    chip(rgb, '同一个问题，从两头问', t, 442.6, 445.6, CREAM)
    chip(rgb, '推一把（蓝光）', t, 445.6, 448.5, CYAN)
    chip(rgb, '按住（黄光）', t, 448.5, 452.6, AMBER)
    if t > 452.3:
        rgb = mix(rgb, f_chrimson(t), ramp(t, 452.3, 452.9))
    return rgb


def f_chrimson(t):
    p = TP('chrimson')
    u = (t - 452.3) / 16.0
    rgb, v = p.cam(1.10 + 0.10 * ease(u), 0.50, 0.47)
    for px_, sd in ((0.455, 11), (0.555, 12)):
        rgb = draw_ions(rgb, v, t, 6, 0.45, px_, 0.32, 0.64, NA, 0.0115, win(t, 458.0, 468.6, 0.5, 0.4), seed=sd, spread=0.05)
    sa = win(t, 453.3, 468.6, 0.4, 0.4)
    k = ramp(t, 454.0, 457.0)
    nm = 470 + 160 * k
    rgb = spectrum_strip(rgb, t, sa, [(int(nm), wl_rgb(nm))], x0=600, y0=590, w=560)
    card(rgb, SPR('card_chrimson'), 36, 30, t, 457.3, 463.0, target=v.pt(0.505, 0.30), accent=(220, 70, 80))
    x, y = v.pt(0.505, 0.18)
    tag(rgb, '≠ 2005 年那个蓝光通道改名', x + 200, y, win(t, 463.0, 468.6, 0.3, 0.4), (220, 70, 80))
    chip(rgb, '后来的工具：往更长的波长推', t, 453.3, 457.3, (255, 120, 80))
    if t > 468.0:
        rgb = mix(rgb, f_honor(t), ramp(t, 468.0, 468.6))
    return rgb


def f_honor(t):
    p = R.P('laur')
    rgb, v = p.cam(1.0 + 0.03 * ramp(t, 468.0, 488.0), 0.5, 0.46)
    a = win(t, 469.3, 487.6, 0.4, 0.5)
    if a > 0:
        # two lists: 2013 (6 people, these 3 included) vs 2026 Nobel (3)
        x0, y0 = 70, 34
        rgb = panel_bg(rgb, x0, y0, x0 + 520, y0 + 76, a * ramp(t, 471.9, 472.4), (150, 170, 220))
        paste(rgb, text_sprite('2013 · 另一项脑科学大奖 · 6 人', 22, CREAM), x0 + 16, y0 + 6, a * ramp(t, 471.9, 472.4), center=False)
        paste(rgb, text_sprite('不是诺贝尔奖', 16, (190, 200, 220), False), x0 + 16, y0 + 42, a * ramp(t, 478.0, 478.4), center=False)
        x1 = W - 70 - 420
        rgb = panel_bg(rgb, x1, y0, x1 + 420, y0 + 76, a * ramp(t, 474.0, 474.5), GOLD)
        paste(rgb, text_sprite('2026 · 诺贝尔奖 · 3 人', 22, GOLD), x1 + 16, y0 + 6, a * ramp(t, 474.0, 474.5), center=False)
        ov_a = a * ramp(t, 479.8, 480.4)
        for fx, _, _, _ in [(l[0][0], 0, 0, 0) for l in R.LAUR]:
            x, y = v.pt(fx, 0.73)
            tag(rgb, '两份名单都有', x, y + 70, ov_a, MINT, 16)
        mg = a * ramp(t, 482.3, 482.8)
        paste(rgb, text_sprite('有重叠 · 但不能并成一份名单', 24, CREAM), W / 2, 150, mg)
    chip(rgb, '荣誉也不止一份', t, 469.3, 471.9, GOLD)
    if t > 487.1:
        rgb = mix(rgb, f_mem_intro(t), ramp(t, 487.1, 487.8))
    return rgb


def dg_frame(t, z, cx, cy, gold=0.0, cells_on=1.0, chr2=0.0, blue=0.0):
    p = TP('dg')
    rgb, v = p.cam(z, cx, cy)
    m = p.warp_mask(TMASK('dg_gold'), v)
    # hide tag colour until 「有一批神经元会活动」
    rgb = tint(rgb, m, (110, 106, 150), 0.9 * (1 - cells_on))
    if gold > 0:
        rgb = add_glow(rgb, m, (255, 190, 90), gold)
    if blue > 0:
        rgb = add_glow(rgb, m, (120, 200, 255), blue)
    if chr2 > 0:
        rgb = add_glow(rgb, cv2.dilate(m, np.ones((5, 5), np.uint8)) - m * 0.8, (120, 240, 170), chr2)
    return rgb, v


def f_mem_intro(t):
    u = (t - 487.1) / 12.0
    rgb, v = dg_frame(t, 1.04 + 0.06 * u, 0.5, 0.5, cells_on=0.0)
    chip(rgb, '开关能在活体里只拨某一类细胞', t, 488.4, 492.0, CYAN)
    chip(rgb, '→ 拿来问：记忆存在哪里', t, 492.0, 494.7, GOLD, '小鼠海马 · 齿状回')
    chip(rgb, '只深讲一件事，而且只讲小鼠', t, 494.7, 499.5, CREAM)
    if t > 498.9:
        rgb = mix(rgb, f_envA(t), ramp(t, 498.9, 499.5))
    return rgb


DG_PIP = {}


def dg_pip(t, gold, chr2, blue, r=110):
    rgb, v = dg_frame(t, 1.25, 0.55, 0.45, gold=gold, cells_on=1.0 if gold > 0 or chr2 > 0 or blue > 0 else 0.0, chr2=chr2, blue=blue)
    return circle_crop(rgb, 0.5, 0.5, 300, r, GOLD)


def f_envA(t):
    p = TP('envA')
    u = (t - 498.9) / 14.6
    rgb, v = p.cam(1.06 + 0.05 * u, 0.48, 0.47)
    on = ramp(t, 504.5, 505.5)
    chr2 = ramp(t, 509.9, 510.8)
    pa = win(t, 502.2, 513.5, 0.4, 0.4)
    if pa > 0:
        pip = dg_pip(t, 0.6 * on, 0.9 * chr2, 0.0)
        paste(rgb, pip, W - 180, 210, pa)
        imp = v.pt(0.59, 0.42)
        rgb = leader(rgb, (imp[0] + 10, imp[1] - 10), (W - 290, 230), GOLD, pa, 2, dashed=True)
        lab = '齿状回：一批神经元活动' if t < 509.8 else '给这批细胞装上 ChR2'
        tag(rgb, lab, W - 180, 345, pa, GOLD if t < 509.8 else (120, 240, 170))
    tag(rgb, '环境甲', 150, 130, win(t, 502.2, 513.5, 0.4, 0.4), (240, 210, 150), 24)
    chip(rgb, '2013 · 《科学》', t, 499.2, 502.2, GOLD)
    if t > 513.0:
        rgb = mix(rgb, f_envB(t), ramp(t, 513.0, 513.6))
    return rgb


def f_envB(t):
    p = TP('envB')
    u = (t - 513.0) / 15.6
    rgb, v = p.cam(1.06 + 0.05 * u, 0.50, 0.47)
    # foot shock: grid sparks
    sh = max(flash_pulse(t, 517.2, 0.1), flash_pulse(t, 518.4, 0.1), flash_pulse(t, 521.0, 0.1))
    if sh > 0.02:
        ov = overlay_layer()
        for k in range(14):
            x0_, y0_ = v.pt(0.10 + k * 0.065, 0.66); x1_, y1_ = v.pt(0.05 + k * 0.07, 0.98)
            cv2.line(ov, (int(x0_), int(y0_)), (int(x1_), int(y1_)), col((255, 245, 170), 0.8 * sh), 3, cv2.LINE_AA)
        rgb = comp(rgb, ov)
    L = win(t, 519.7, 528.6, 0.3, 0.4)
    fiber_glow(rgb, v, (0.60, 0.0), (0.60, 0.37), L)
    x, y = v.pt(0.60, 0.37); add_radial(rgb, x, y, 30, (110, 200, 255), 1.1 * L)
    pa = win(t, 519.7, 528.6, 0.4, 0.4)
    if pa > 0:
        pip = dg_pip(t, 0.5, 0.0, 0.8 * (0.6 + 0.4 * math.sin(t * 6)))
        paste(rgb, pip, W - 180, 210, pa)
        rgb = leader(rgb, (x + 10, y - 10), (W - 290, 230), CYAN, pa, 2, dashed=True)
        tag(rgb, '甲里活跃过的那批细胞 · 被光叫回', W - 180, 345, pa, CYAN)
    tag(rgb, '环境乙', 150, 130, win(t, 513.6, 528.6, 0.4, 0.4), (200, 210, 230), 24)
    tag(rgb, '足底电击', 260, 560, win(t, 516.9, 520.0, 0.2, 0.4), (255, 235, 150))
    chip(rgb, '在乙里做恐惧条件化', t, 515.7, 519.7, (255, 235, 150))
    chip(rgb, '电击发生在乙 · 光叫回甲的细胞', t, 523.4, 528.6, CYAN)
    if t > 528.4:
        rgb = mix(rgb, f_freeze(t), ramp(t, 528.4, 529.0))
    return rgb


def f_freeze(t):
    p = TP('envAf')
    # camera locks still on 「冻结」 — the stillness is the claim
    z = 1.06 + 0.06 * ramp(t, 528.4, 532.3)
    rgb, v = p.cam(z, 0.42, 0.50)
    tag(rgb, '回到环境甲 · 这里从没有电击', 300, 130, win(t, 529.0, 532.4, 0.4, 0.3), (240, 210, 150), 22)
    fa = win(t, 532.4, 541.2, 0.3, 0.4)
    if fa > 0:
        x, y = v.pt(0.42, 0.42)
        rgb = ring(rgb, x, y, 210, (150, 200, 255), 0.6 * fa, 2)
        tag(rgb, '冻结 = 恐惧行为', x, y - 240 if y > 300 else y + 230, fa, (150, 200, 255), 22)
    ca = win(t, 535.4, 541.2, 0.4, 0.4)
    if ca > 0:
        x0, y0 = W - 520, 60
        rgb = panel_bg(rgb, x0, y0, x0 + 470, y0 + 120, ca, GOLD)
        paste(rgb, text_sprite('一段虚假的恐惧记忆', 34, GOLD), x0 + 20, y0 + 14, ca, center=False)
        paste(rgb, text_sprite('作者的结论 · 小鼠海马', 18, CREAM, False), x0 + 20, y0 + 72, ca, center=False)
    if t > 540.7:
        rgb = mix(rgb, f_meaning(t), ramp(t, 540.7, 541.3))
    return rgb


def f_meaning(t):
    u = (t - 540.7) / 36.0
    gold = 0.55 * win(t, 541.0, 556.0, 0.5, 0.5)
    blue = 0.6 * win(t, 548.2, 553.8, 0.3, 0.4) * (0.6 + 0.4 * math.sin(t * 5))
    rgb, v = dg_frame(t, 1.06 + 0.10 * ease(u), 0.52, 0.48, gold=gold, cells_on=1.0, blue=blue)
    chip(rgb, '写进去的：一批选定细胞的活动', t, 544.8, 548.2, GOLD, '不是一句话，也不是一段人生')
    ba = win(t, 548.2, 554.0, 0.4, 0.4)
    if ba > 0:
        tag(rgb, '电击', W / 2 - 160, 120, ba, (255, 235, 150), 24)
        tag(rgb, '环境甲', W / 2 + 160, 120, ba, (240, 210, 150), 24)
        rgb = leader(rgb, (W / 2 - 100, 120), (W / 2 + 90, 120), CREAM, ba, 3)
        paste(rgb, text_sprite('绑在一起', 18, CREAM), W / 2, 150, ba)
    oa = win(t, 556.5, 577.0, 0.5, 0.5)
    if oa > 0:
        rgb = dim_all(rgb, 0.4 * oa)
        x0, y0 = 120, 110
        rgb = panel_bg(rgb, x0, y0, x0 + 1040, y0 + 220, oa, GOLD)
        paste(rgb, text_sprite('实验动物里的因果演示', 30, GOLD), x0 + 24, y0 + 14, oa, center=False)
        a1 = oa * ramp(t, 562.8, 563.3)
        paste(rgb, text_sprite('① 先用光动了细胞', 28, CYAN), x0 + 24, y0 + 80, a1, center=False)
        paste(rgb, text_sprite('→  ② 后来才有恐惧', 28, CREAM), x0 + 330, y0 + 80, a1, center=False)
        paste(rgb, text_sprite('足以支撑一种恐惧行为', 22, MINT), x0 + 24, y0 + 150, oa * ramp(t, 566.4, 566.9), center=False)
        paste(rgb, text_sprite('× 没有说明已用在人身上', 22, (255, 140, 140)), x0 + 560, y0 + 150, oa * ramp(t, 570.9, 571.4), center=False)
        paste(rgb, text_sprite('相关只能说：一起出现', 18, (190, 200, 220), False), x0 + 640, y0 + 24, oa * win(t, 558.6, 563.0, 0.3, 0.3), center=False)
    if t > 576.6:
        rgb = mix(rgb, f_retina(t), ramp(t, 576.6, 577.3))
    return rgb


RGC = [(0.21, 0.28), (0.50, 0.28), (0.80, 0.29)]


def f_retina(t):
    p = TP('retina')
    u = (t - 576.6) / 17.6
    rgb, v = p.cam(1.04 + 0.08 * ease(u), 0.5, 0.5)
    pr = win(t, 579.5, 594.4, 0.6, 0.4)
    rgb = dim(rgb, p.warp_mask(TMASK('retina_pr'), v), 0.75 * pr * ramp(t, 579.5, 582.5), 0.9)
    x, y = v.pt(0.30, 0.66)
    tag(rgb, '感光细胞 · 逐渐死去', x, y, pr, (220, 220, 230))
    ga = win(t, 583.2, 594.4, 0.4, 0.4)
    x, y = v.pt(0.50, 0.28)
    tag(rgb, '视网膜神经节细胞 · 还留着', x, y + 120, ga, CYAN)
    la = win(t, 586.7, 594.4, 0.4, 0.4)
    for i, (fx, fy) in enumerate(RGC):
        x, y = v.pt(fx, fy)
        add_radial(rgb, x, y, 50, (255, 130, 80), 0.6 * la * (0.6 + 0.4 * math.sin(t * 4 + i)))
    if la > 0:
        for k in range(5):
            q = ((t * 0.6 + k / 5) % 1.0)
            x, y = v.pt(0.02 + 0.96 * q, 0.205 + 0.01 * math.sin(q * 20))
            paste(rgb, ion_sprite(6, YELLOW, ''), x, y, la * (0.4 + 0.6 * ramp(t, 589.8, 590.5)))
    chip(rgb, '眼睛走的是另一条路', t, 577.5, 581.2, CREAM, '视网膜色素变性')
    chip(rgb, '让幸存的细胞自己感光 → 视觉通路也许还能被点着', t, 586.7, 594.4, (255, 150, 90))
    if t > 593.7:
        rgb = mix(rgb, f_trial(t), ramp(t, 593.7, 594.4))
    return rgb


def f_trial(t):
    p = TP('eye')
    u = (t - 593.7) / 25.0
    rgb, v = p.cam(1.04 + 0.08 * ease(u), 0.52, 0.48)
    inj = win(t, 600.2, 610.3, 0.4, 0.4)
    if inj > 0:
        vit = v.pt(0.60, 0.48)
        tag(rgb, '玻璃体内注射 AAV', vit[0], vit[1] - 140, win(t, 600.2, 604.4, 0.3, 0.3), MINT)
        spr = ion_sprite(5, (150, 240, 200), '')
        for k in range(24):
            q = ramp(t, 600.6, 606.0) * ((k * 0.37) % 1)
            ang = k * 2.4
            x = vit[0] + math.cos(ang) * 150 * q
            y = vit[1] + math.sin(ang) * 150 * q
            paste(rgb, spr, x, y, inj)
    rr = win(t, 604.3, 619.0, 0.5, 0.4)
    if rr > 0:
        # retinal rim takes ChrimsonR (warm red tint near the back of the eye)
        m = disc_mask(p, [(0.66, 0.48)], 0.22, 0.25) - disc_mask(p, [(0.62, 0.48)], 0.17, 0.25)
        rgb = add_glow(rgb, np.clip(p.warp_mask(np.clip(m, 0, 1), v), 0, 1), (255, 80, 60), 0.35 * rr)
        x, y = v.pt(0.85, 0.30)
        tag(rgb, 'ChrimsonR → 神经节细胞', x, y, win(t, 604.3, 610.2, 0.3, 0.3), (255, 110, 90))
    pl = win(t, 610.1, 619.0, 0.3, 0.4)
    if pl > 0:
        pulse = 1.0 if ((t - 610.1) % 0.5) < 0.18 else 0.0
        a0, a1 = v.pt(0.06, 0.36), v.pt(0.69, 0.48)
        ov = overlay_layer()
        cv2.line(ov, tuple(map(int, a0)), tuple(map(int, a1)), (1, 1, 1, 1), 6, cv2.LINE_AA)
        rgb = add_glow(rgb, cv2.GaussianBlur(ov[..., 3], (0, 0), 5), (255, 140, 70), 0.9 * pl * pulse)
        add_radial(rgb, a1[0], a1[1], 24, (255, 170, 90), 1.2 * pl * pulse)
        x, y = v.pt(0.10, 0.20)
        tag(rgb, '护目镜：亮度变化 → 光脉冲', x + 140, y, pl, (255, 150, 90))
    chip(rgb, '2021 · 《自然·医学》 · 一名已失明患者', t, 594.1, 600.2, GOLD)
    if t > 618.3:
        rgb = mix(rgb, f_patient(t), ramp(t, 618.3, 619.0))
    return rgb


def f_patient(t):
    if t < 643.8:
        p = TP('goggles')
        u = (t - 618.3) / 26.0
        rgb, v = p.cam(1.04 + 0.06 * ease(u), 0.45, 0.47)
        beam_on = 1.0
        off = win(t, 630.5, 635.6, 0.3, 0.3)
        if off > 0:
            m = hue_mask(p, 0, 20, smin=80, vmin=120, blur=31, region=(0.52, 0.2, 1.0, 0.75)) if not hasattr(f_patient, 'bm') else f_patient.bm
            f_patient.bm = m
            rgb = dim(rgb, p.warp_mask(m, v), 0.95 * off, 0.4)
        ta = win(t, 621.9, 636.3, 0.4, 0.4)
        if ta > 0:
            x0, y0 = W - 470, 70
            rgb = panel_bg(rgb, x0, y0, x0 + 420, y0 + 220, ta, (255, 150, 90))
            paste(rgb, text_sprite('能否知觉物体', 22, CREAM), x0 + 18, y0 + 10, ta, center=False)
            rows = [('注射前 · 戴/不戴护目镜', '×', (255, 130, 130), 628.1),
                    ('注射后 · 戴着护目镜', '✓', MINT, 621.9),
                    ('注射后 · 摘掉护目镜', '×', (255, 130, 130), 630.6)]
            for i, (lab, mk, c, ta0) in enumerate(rows):
                ra = ta * ramp(t, ta0, ta0 + 0.4)
                paste(rgb, text_sprite(lab, 18, CREAM, False), x0 + 18, y0 + 60 + 50 * i, ra, center=False)
                paste(rgb, text_sprite(mk, 26, c), x0 + 370, y0 + 72 + 50 * i, ra)
        chip(rgb, '只用治疗过的那只眼 · 必须戴护目镜', t, 618.8, 625.3, (255, 150, 90))
        chip(rgb, '指出位置 · 数出个数 · 伸手触到', t, 625.3, 628.1, MINT)
        chip(rgb, '论文：部分功能恢复', t, 636.1, 644.2, GOLD, '神经退行性疾病里光遗传治疗后的首次报告')
        if t > 643.3:
            rgb = mix(rgb, f_patient_retina(t), ramp(t, 643.3, 643.9))
        return rgb
    return f_patient_retina(t)


def f_patient_retina(t):
    p = TP('retina')
    u = (t - 643.3) / 22.0
    rgb, v = p.cam(1.04 - 0.02 * ease(u), 0.5, 0.45)
    rgb = dim(rgb, p.warp_mask(TMASK('retina_pr'), v), 0.75, 0.9)
    # 哪里亮度变了 → 对应位置打一束光 → 打开那里的通道
    seq = [(648.3, 0), (650.2, 2), (652.0, 1), (654.4, 0), (656.0, 2)]
    for t0, i in seq:
        a = flash_pulse(t, t0 + 0.2, 0.35)
        if a > 0.02:
            fx, fy = RGC[i]
            x, y = v.pt(fx, fy)
            ov = overlay_layer()
            cv2.line(ov, (int(x - 120), 0), (int(x), int(y)), (1, 1, 1, 1), 10, cv2.LINE_AA)
            rgb = add_glow(rgb, cv2.GaussianBlur(ov[..., 3], (0, 0), 6), (255, 140, 70), 0.8 * a)
            add_radial(rgb, x, y, 60, (255, 160, 90), 0.9 * a)
    chip(rgb, '所见 = 护目镜把亮度变化译成的光脉冲', t, 644.2, 650.1, (255, 150, 90))
    chip(rgb, '对应位置打一束光 → 打开那里新装的通道', t, 650.1, 656.4, (255, 150, 90))
    chip(rgb, '不是不依赖设备的日常视觉', t, 656.4, 659.4, CREAM)
    chip(rgb, '诺奖新闻稿：「尝试恢复视力」', t, 659.4, 665.9, GOLD)
    if t > 665.3:
        rgb = mix(rgb, f_reg(t), ramp(t, 665.3, 665.9))
    return rgb


def fact_card(rgb, t, a, b, title, lines, accent=GOLD, x0=60, y0=70, w=640):
    al = win(t, a, b, 0.4, 0.4)
    if al <= 0:
        return rgb
    h = 70 + 44 * len(lines)
    rgb = panel_bg(rgb, x0, y0, x0 + w, y0 + h, al, accent)
    paste(rgb, text_sprite(title, 28, accent), x0 + 22, y0 + 12, al, center=False)
    for i, (txt, c, ta) in enumerate(lines):
        paste(rgb, text_sprite(txt, 21, c, False), x0 + 22, y0 + 64 + 44 * i, al * ramp(t, ta, ta + 0.35), center=False)
    return rgb


def isotype(rgb, t, al, n, k, x0, y0, label, color):
    if al <= 0:
        return rgb
    ov = overlay_layer()
    for i in range(n):
        x = x0 + i * 52
        c = color if i < k else (90, 100, 130)
        cv2.circle(ov, (x, y0), 12, col(c, al), -1, cv2.LINE_AA)
        cv2.ellipse(ov, (x, y0 + 40), (18, 22), 0, 180, 360, col(c, al), -1, cv2.LINE_AA)
    rgb = comp(rgb, ov)
    paste(rgb, text_sprite(label, 22, CREAM), x0 - 10, y0 + 66, al, center=False)
    return rgb


def f_reg(t):
    if t < 725.6:
        p = TP('regdocs')
        u = (t - 665.3) / 60.3
        cx = 0.62 - 0.10 * ramp(t, 701.5, 703.5)
        rgb, v = p.cam(1.06 + 0.10 * ease(u), cx, 0.52)
        stamp = v.pt(0.87, 0.50)
        sa = win(t, 679.5, 701.3, 0.4, 0.4)
        rgb = ring(rgb, stamp[0], stamp[1], 46, (255, 140, 140), sa, 3)
        tag(rgb, '「如果获批」= 尚未获批', stamp[0] - 160, stamp[1] - 80, sa, (255, 140, 140))
        rgb = fact_card(rgb, t, 665.8, 683.3, '2026-09-09 · 一家公司公告',
                        [('FDA 已受理并立案：生物制品许可申请（BLA）', CREAM, 669.1),
                         ('针对伴严重视力丧失的视网膜色素变性', CREAM, 675.6)])
        rgb = fact_card(rgb, t, 684.5, 701.3, '同一篇公告写',
                        [('第 52 / 76 周：达到视力主要终点与关键次要终点', CREAM, 686.0),
                         ('无治疗相关的严重不良事件', CREAM, 693.4),
                         ('申请方公告 ≠ 已生效的许可', (255, 160, 140), 697.0)])
        rgb = fact_card(rgb, t, 702.4, 725.6, '2026-10-08 · 另一家公司 + 巴黎一家医院',
                        [('另一款疗法 · 一期/二期 · 发表于《新英格兰医学杂志》', CREAM, 704.6),
                         ('主要目的：安全性 · 不是为确证疗效设计', CREAM, 714.4),
                         ('研究者原话：结果仍是探索性的，需进一步确认', (255, 200, 140), 719.5)], accent=(150, 200, 255))
        if t > 725.0:
            rgb = mix(rgb, f_reg_numbers(t), ramp(t, 725.0, 725.6))
        return rgb
    return f_reg_numbers(t)


def f_reg_numbers(t):
    if t < 753.6:
        p = TP('goggles')
        rgb, v = p.cam(1.10 + 0.04 * ramp(t, 725.0, 754.0), 0.40, 0.47)
        rgb = dim_all(rgb, 0.5)
        chip(rgb, '数字要连同分母一起说 · 出自公司公告', t, 726.3, 731.9, GOLD)
        a1 = win(t, 731.8, 753.8, 0.4, 0.4)
        rgb = isotype(rgb, t, a1, 10, 6 if t > 734.0 else 0, 120, 150, '10 人中 6 人 · 全视野光敏感测试改善（公司所称）', MINT)
        a2 = win(t, 740.2, 753.8, 0.4, 0.4)
        rgb = isotype(rgb, t, a2, 8, 4 if t > 742.0 else 0, 120, 360, '完成行为测试的 8 人中 4 人 · 戴护目镜时部分任务正向变化', (255, 170, 100))
        if t > 753.0:
            rgb = mix(rgb, f_reg_foot(t), ramp(t, 753.0, 753.6))
        return rgb
    return f_reg_foot(t)


def f_reg_foot(t):
    if t < 761.6:
        p = TP('regdocs')
        rgb, v = p.cam(1.20, 0.80, 0.58)
        stamp = v.pt(0.87, 0.50)
        a = win(t, 754.2, 761.8, 0.4, 0.3)
        rgb = ring(rgb, stamp[0], stamp[1], 60, (255, 140, 140), a, 3)
        tag(rgb, '公告脚注：任何司法辖区都没有上市许可', stamp[0] - 260, stamp[1] - 110, a, (255, 140, 140), 22)
        if t > 761.0:
            rgb = mix(rgb, f_cochlea(t), ramp(t, 761.0, 761.6))
        return rgb
    return f_cochlea(t)


def f_cochlea(t):
    p = TP('cochlea')
    rgb, v = p.cam(1.04 + 0.06 * ramp(t, 761.0, 772.5), 0.45, 0.5)
    chip(rgb, '光学人工耳蜗', t, 762.3, 772.6, (255, 150, 90), '按 2023 年综述：仍是临床前')
    if t > 772.0:
        rgb = mix(rgb, f_bound(t), ramp(t, 772.0, 772.6))
    return rgb


def f_bound(t):
    if t < 784.3:
        rgb, v = R.P('chr2').cam(1.10, 0.49, 0.47)
        rgb = chr2_state(t, rgb, v, 1.0, 0.6)
        rgb = current_panel(rgb, t, win(t, 776.6, 784.6, 0.4, 0.4), 'step', 777.0)
        chip(rgb, '边界停在已发表的事实上', t, 774.2, 776.8, GOLD)
        chip(rgb, 'ChR2 持续光照会脱敏 · 不是永不疲劳的门', t, 776.8, 784.6, AMBER)
        if t > 783.9:
            rgb = mix(rgb, f_bound2(t), ramp(t, 783.9, 784.5))
        return rgb
    return f_bound2(t)


def f_bound2(t):
    if t < 789.4:
        rgb, v = R.P('brain').cam(1.15, 0.42, 0.40)
        tip = v.pt(0.425, 0.29); add_radial(rgb, tip[0], tip[1], 30, CYAN, 0.9)
        chip(rgb, '光得送到细胞旁边：2007 年在脑里用光纤', t, 784.6, 789.5, CYAN)
        if t > 788.8:
            rgb = mix(rgb, f_bound3(t), ramp(t, 788.8, 789.4))
        return rgb
    return f_bound3(t)


def f_bound3(t):
    if t < 794.6:
        p = TP('goggles')
        rgb, v = p.cam(1.08, 0.45, 0.47)
        m = hue_mask(p, 0, 20, smin=80, vmin=120, blur=31, region=(0.52, 0.2, 1.0, 0.75)) if not hasattr(f_patient, 'bm') else f_patient.bm
        f_patient.bm = m
        rgb = dim(rgb, p.warp_mask(m, v), 0.95 * ramp(t, 791.0, 792.2), 0.4)
        chip(rgb, '没有护目镜，就没有那些物体', t, 789.4, 794.7, (255, 150, 90))
        if t > 794.0:
            rgb = mix(rgb, f_bound4(t), ramp(t, 794.0, 794.6))
        return rgb
    return f_bound4(t)


def f_bound4(t):
    if t < 811.4:
        p = TP('regdocs')
        rgb, v = p.cam(1.10 + 0.06 * ramp(t, 794.0, 811.5), 0.62, 0.52)
        rgb = fact_card(rgb, t, 795.1, 811.5, '已发表 / 已申请的，到此为止',
                        [('人体视觉：部分功能 · 绑在装置上', CREAM, 795.2),
                         ('一条申请：尚未获批', (255, 160, 140), 801.7),
                         ('另一条：没有上市许可', (255, 160, 140), 802.5),
                         ('且那项研究不是为了确证疗效', (255, 200, 140), 803.7)])
        if t > 810.8:
            rgb = mix(rgb, f_can(t), ramp(t, 810.8, 811.4))
        return rgb
    return f_can(t)


def f_can(t):
    if t < 821.2:
        u = (t - 810.8) / 10.4
        on = win(t, 813.8, 817.3, 0.3, 0.3); off = win(t, 817.3, 821.4, 0.3, 0.3)
        drive = (1.0 if ((t - 813.8) % 0.5) < 0.2 else 0.3) * on
        rgb, v = crowd_frame(t, 1.18 + 0.05 * u, 0.44, 0.5, glow=0.7 * drive, dimv=0.85 * off, ripple=on, ripple_rate=2.0)
        chip(rgb, '做得到：在实验里打开或关掉选定的细胞', t, 812.0, 817.3, MINT)
        chip(rgb, '→ 把「同时发生」推进成「是它造成的」', t, 817.3, 821.4, MINT)
        if t > 820.8:
            rgb = mix(rgb, f_cannot(t), ramp(t, 820.8, 821.4))
        return rgb
    return f_cannot(t)


def f_cannot(t):
    if t < 828.4:
        rgb, v = dg_frame(t, 1.10, 0.52, 0.48, gold=0.4, cells_on=1.0)
        rgb = dim_all(rgb, 0.3)
        tag(rgb, '小鼠海马里的一段恐惧  ≠  改写了某个人的人生', W / 2, 300, win(t, 821.6, 828.6, 0.4, 0.3), (255, 150, 150), 26)
        chip(rgb, '做不到', t, 821.6, 835.0, (255, 140, 140))
        if t > 827.9:
            rgb = mix(rgb, f_cannot2(t), ramp(t, 827.9, 828.5))
        return rgb
    return f_cannot2(t)


def f_cannot2(t):
    if t < 836.4:
        p = TP('goggles')
        rgb, v = p.cam(1.12, 0.45, 0.47)
        rgb = dim_all(rgb, 0.3)
        tag(rgb, '离不开装置的部分视觉  ≠  失明已经结束', W / 2, 300, win(t, 828.5, 836.6, 0.4, 0.3), (255, 150, 150), 26)
        chip(rgb, '做不到', t, 821.6, 836.6, (255, 140, 140))
        if t > 835.9:
            rgb = mix(rgb, f_end(t), ramp(t, 835.9, 836.5))
        return rgb
    return f_end(t)


def f_end(t):
    if t < 843.4:
        p = R.P('crick')
        rgb, v = p.cam(1.0 + 0.04 * ramp(t, 835.9, 843.6), 0.57, 0.40)
        chip(rgb, '回到开场', t, 837.5, 839.5, GOLD)
        chip(rgb, '「用光拨动某一类神经元，相当牵强」', t, 839.5, 843.6, GOLD, '克里克 · 1999')
        if t > 842.9:
            rgb = mix(rgb, f_end2(t), ramp(t, 842.9, 843.6))
        return rgb
    return f_end2(t)


def f_end2(t):
    if t < 853.2:
        p = R.P('open')
        u = (t - 842.9) / 11.0
        rgb, v = p.cam(1.04 + 0.08 * u, 0.56, 0.50)
        chip(rgb, '牵强的是当年的工程', t, 843.8, 846.1, CREAM)
        chip(rgb, '今天：一套实验方法', t, 846.1, 848.6, MINT)
        chip(rgb, '也是几条仍在审查中的临床尝试', t, 848.6, 853.4, (255, 150, 90))
        if t > 852.3:
            rgb = mix(rgb, f_endcard(t), ramp(t, 852.3, 853.3))
        return rgb
    return f_endcard(t)


def f_endcard(t):
    ec = TP('endcard')
    rgb, v = ec.cam(1.0 + 0.03 * ramp(t, 852.3, 865.1), 0.5, 0.5)
    a = ramp(t, 852.3, 853.5) * (1 - ramp(t, 863.6, 865.04))
    return rgb * a


# ================================================================== orchestration
BEATS = [('t01_relay', 276.0, 285.6, f_relay), ('t02_onemol', 285.6, 306.9, f_onemol), ('t03_chr2b', 306.9, 344.0, f_chr2b),
         ('t04_neuron', 344.0, 367.0, f_neuron), ('t05_authors', 367.0, 376.0, f_authors), ('t06_term', 376.0, 390.2, f_term),
         ('t07_motor', 390.2, 417.6, f_motor), ('t08_nphr', 417.6, 435.6, f_nphr), ('t09_dual', 435.6, 452.6, f_dual),
         ('t10_chrimson', 452.6, 468.3, f_chrimson), ('t11_honor', 468.3, 487.4, f_honor), ('t12_memintro', 487.4, 499.2, f_mem_intro),
         ('t13_envA', 499.2, 513.3, f_envA), ('t14_envB', 513.3, 528.7, f_envB), ('t15_freeze', 528.7, 541.0, f_freeze),
         ('t16_meaning', 541.0, 577.0, f_meaning), ('t17_retina', 577.0, 594.0, f_retina), ('t18_trial', 594.0, 618.6, f_trial),
         ('t19_patient', 618.6, 665.6, f_patient), ('t20_reg', 665.6, 761.3, f_reg), ('t21_cochlea', 761.3, 772.3, f_cochlea),
         ('t22_bound', 772.3, 811.1, f_bound), ('t23_can', 811.1, 836.2, f_can), ('t24_end', 836.2, 865.04, f_end)]


def frames_of(name):
    for n, a, b, _ in BEATS:
        if n == name:
            return int(round(a * FPS)), int(round(b * FPS))


def render_one(name):
    fn = [f for n, _, _, f in BEATS if n == name][0]
    f0, f1 = frames_of(name)
    write_segment(SEG6 / f'{name}.mp4', f0, f1, fn)
    return name, f1 - f0


def stills(ts):
    from PIL import Image as I
    (HERE / 'stills').mkdir(exist_ok=True)
    for t in ts:
        fn = [f for n, a, b, f in BEATS if int(round(a * FPS)) <= round(t * FPS) < int(round(b * FPS))][0]
        I.fromarray((np.clip(fn(t), 0, 1) * 255).astype(np.uint8)).save(HERE / 'stills' / f't{t:07.2f}.png')
        print(t, flush=True)


def mux():
    WORK = HERE / 'work'; WORK.mkdir(exist_ok=True)
    head = [SEG6 / f'{n}.mp4' for n, _ in R.CHUNKS]
    ooc = WORK / 'sB_oocyte_slice.mp4'      # old chain frames 2017..2211 (film 267.875–276.0)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(R.SEGS_OLD / 'sB_chain.mp4'), '-vf',
                    f'trim=start_frame={R.OLD_SB_HANDOFF}:end_frame={F0 - R.OLD_SB_START_F},setpts=PTS-STARTPTS',
                    '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', '24', str(ooc)], check=True)
    tail = [SEG6 / f'{n}.mp4' for n, *_ in BEATS]
    lst = WORK / 'concat_v6r2.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in head + [ooc] + tail))
    raw = WORK / 'video_full_v6r2.mp4'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c:v', 'libx264',
                    '-preset', 'fast', '-crf', '18', '-an', '-pix_fmt', 'yuv420p', '-r', '24', str(raw)], check=True)
    n = int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                                     'stream=nb_read_frames', '-of', 'csv=p=0', str(raw)], text=True))
    print('FRAMES', n, 'expect', F_END, flush=True)
    assert n == F_END
    vo = R.OUT / 'work' / 'vo_full.m4a'
    ass_esc = str(R.OUT / 'captions.ass').replace(':', '\\:')
    master = HERE / 'E2_cut10_full_lowres_INTERNAL.mp4'
    share = HERE / 'E2_cut10_full_lowres_share_INTERNAL.mp4'
    pub = R.OUT / 'E2_cut10_full_lowres_share.mp4'; pm = pub.stat().st_mtime
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(raw), '-i', str(vo), '-vf',
                    f'ass={ass_esc}:fontsdir=/usr/share/fonts/opentype/noto', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                    '-preset', 'fast', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(master)], check=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(master), '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(share)], check=True)
    assert pub.stat().st_mtime == pm, 'public share touched!'
    print('MASTER', R.probe(master), 'SHARE_INTERNAL', R.probe(share), flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'still':
        stills([float(x) for x in a[1:]])
    elif a and a[0] == 'mux':
        mux()
    elif a and a[0] == 'render':
        names = a[1:] or [n for n, *_ in BEATS]
        assert int(round(BEATS[0][1] * FPS)) == F0 and int(round(BEATS[-1][2] * FPS)) == F_END
        with Pool(7) as pool:
            for n, k in pool.imap_unordered(render_one, sorted(names, key=lambda n: -(frames_of(n)[1] - frames_of(n)[0]))):
                print('rendered', n, k, flush=True)
