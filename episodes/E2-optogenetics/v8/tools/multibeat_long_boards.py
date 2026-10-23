#!/usr/bin/env python3
"""Multi-beat long boards: unique progressive motion spanning nearly full film windows.
Kills 30–48s phase cycling on SF16/SF18/SF19/SF23. $0 pillow/2.5D; keeps SF18/19 photo plates.
Film windows (assemble): SF16≈122.9s SF18≈98.2s SF19≈89.1s SF23≈103.9s
"""
from __future__ import annotations
import math, sys, os, time as _time
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
MOUSE = '/workspace/e2work/v8/gen/mouse_ref.png'
SF10_STILL = '/workspace/e2work/v8/styleframes/SF10_mouse_tripo.png'

def load_rgb(path, tw, th):
    im = Image.open(path).convert('RGBA')
    im = im.resize((tw, th), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr[..., :3], arr[..., 3:4]

def matte_gray_bg(rgb, alpha, thr=0.92):
    lum = rgb.mean(axis=2, keepdims=True)
    sat = rgb.max(axis=2, keepdims=True) - rgb.min(axis=2, keepdims=True)
    bgm = (lum > thr) & (sat < 0.08)
    a = alpha.copy(); a[bgm] = 0.0
    return rgb, a

def place(dst_rgb, src_rgb, src_a, x, y, opacity=1.0):
    h, w = src_rgb.shape[:2]
    Hh, Ww = dst_rgb.shape[:2]
    x0, y0 = int(x), int(y)
    x1, y1 = min(Ww, x0 + w), min(Hh, y0 + h)
    if x1 <= x0 or y1 <= y0: return dst_rgb
    sx0 = max(0, -x0); sy0 = max(0, -y0)
    dx0 = max(0, x0); dy0 = max(0, y0)
    sw, sh = x1 - dx0, y1 - dy0
    patch = src_rgb[sy0:sy0+sh, sx0:sx0+sw]
    pa = src_a[sy0:sy0+sh, sx0:sx0+sw] * opacity
    region = dst_rgb[dy0:dy0+sh, dx0:dx0+sw]
    dst_rgb[dy0:dy0+sh, dx0:dx0+sw] = region * (1 - pa) + patch * pa
    return dst_rgb

def bg(W, H, t, accent=CYAN, ax=0.3, ay=0.4):
    # slow drift of radial centers so long holds still feel alive
    ax2 = ax + 0.04 * math.sin(t * 0.11)
    ay2 = ay + 0.03 * math.cos(t * 0.09)
    rgb = np.zeros((H, W, 3), np.float32) + np.array(INK) / 255
    rgb = rgb + radial(W, H, W * ax2, H * ay2, W * 0.35, accent, 0.22 + 0.04 * math.sin(t * 0.7))
    rgb = rgb + radial(W, H, W * 0.75, H * 0.7, W * 0.28, GOLD, 0.08)
    return rgb

def chip(L, box, title, sub, t, accent=GOLD, s=1.0):
    a = float(np.clip(t, 0, 1))
    if a <= 0: return
    x0, y0, x1, y1 = box
    L.rrect((x0, y0, x1, y1), 8 * s, fill=(14, 20, 40), alpha=0.78 * a)
    L.line([(x0, y0), (x0, y1)], fill=accent, width=3 * s, alpha=a)
    L.text((x0 + 16 * s, y0 + 28 * s), title, F(SANS_B, 22 * s), fill=CREAM, alpha=a, anchor='ls')
    if sub:
        L.text((x0 + 16 * s, y0 + 56 * s), sub, F(SANS, 15 * s), fill=MUTED, alpha=a, anchor='ls')

def header(L, W, H, title, sub, t, s):
    a = ramp(t, 0.0, 0.5)
    L.text((W / 2, 42 * s), title, F(SANS_B, 22 * s), fill=GOLD, alpha=a, anchor='ms', tracking=2 * s)
    if sub:
        L.text((W / 2, 72 * s), sub, F(SANS, 15 * s), fill=MUTED, alpha=ramp(t, 0.3, 0.9), anchor='ms')

def footer_tick(L, W, H, t, s, label=''):
    a = 0.55 + 0.15 * math.sin(t * 1.4)
    L.line([(80 * s, H - 36 * s), (W - 80 * s, H - 36 * s)], fill=(50, 60, 90), width=1 * s, alpha=a)
    if label:
        L.text((W / 2, H - 22 * s), label, F(SANS, 12 * s), fill=MUTED, alpha=0.7, anchor='ms')

def progress_rail(L, W, H, t, total, s, n_marks, accent=CYAN):
    """Bottom progress marks — unique position across whole board (no wrap feel)."""
    frac = min(max(t / max(total, 1e-6), 0), 1)
    y = H - 52 * s
    x0, x1 = 100 * s, W - 100 * s
    L.line([(x0, y), (x1, y)], fill=(40, 50, 80), width=2 * s, alpha=0.55)
    L.line([(x0, y), (x0 + (x1 - x0) * frac, y)], fill=accent, width=2.5 * s, alpha=0.85)
    for i in range(n_marks):
        xf = x0 + (x1 - x0) * (i / max(n_marks - 1, 1))
        on = frac >= i / max(n_marks - 1, 1)
        L.dot((xf, y), 4 * s, fill=accent if on else (60, 70, 100), alpha=0.9 if on else 0.35)

# ---- photo plates (SF18/19) ----
_sf10_rgb, _sf10_a = load_rgb(SF10_STILL, 480, 270)
_sf10_a = np.ones_like(_sf10_a)
_mouse_rgb, _mouse_a = load_rgb(MOUSE, 300, 214)
_mouse_rgb, _mouse_a = matte_gray_bg(_mouse_rgb, _mouse_a, thr=0.93)

# =====================================================================
# SF16 — ChR path · film ~122.9s · UNIQUE ~120s (6 beats × ~20s)
# =====================================================================
def sf16(t, W, H):
    s = W / 1280
    TOTAL = 120.0
    # clamp: after TOTAL, hold last beat (no wrap)
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.55, 0.4)
    L = Layer(W, H)
    steps = [
        (0.0,  20.0, '衣藻朝光游', '眼点 · 谁在感光？', GOLD),
        (20.0, 40.0, '2002 · 通道视紫红质一', '放进卵母细胞 · 光 → 质子电流', AMBER),
        (40.0, 60.0, '关键：光与孔在同一分子', '不必多步接力 · 送进一个基因就行', CYAN),
        (60.0, 80.0, '2003 · 通道视紫红质二', '蓝光开阳离子 · 哺乳细胞也能用', CYAN),
        (80.0, 100.0, '持续光照会脱敏', '高峰→平台 · 要用短脉冲', AMBER),
        (100.0, 120.0, '2005 · 培养神经元', '蓝光脉冲对齐锋电位', GOLD),
    ]
    header(L, W, H, '从衣藻到毫秒级开关', 'ChR1 → 一体分子 → ChR2 → 锋电位', min(tt, 2.0) + 1.0, s)
    # timeline rail
    L.line([(80 * s, 175 * s), (1200 * s, 175 * s)], fill=(50, 60, 90), width=2 * s, alpha=0.75)
    cur = steps[0]
    for i, (t0, t1, title, sub, col) in enumerate(steps):
        x = 100 * s + i * 185 * s
        a = ramp(tt, t0, t0 + 0.8)
        L.dot((x, 175 * s), 7 * s, fill=col, alpha=max(a, 0.25))
        # short label under dots always after reveal
        if a > 0.2:
            short = title.split('·')[0].strip()[:8]
            L.text((x, 200 * s), short, F(SANS, 11 * s), fill=MUTED, alpha=0.55 * a, anchor='ms')
        if t0 <= tt < t1:
            cur = (t0, t1, title, sub, col)
            # dwell card with slow pulse
            local = tt - t0
            aa = 0.85 + 0.1 * math.sin(local * 1.5)
            L.rrect((100 * s, 230 * s, 1180 * s, 400 * s), 12 * s, fill=(14, 20, 40), alpha=0.82 * aa)
            L.line([(100 * s, 230 * s), (100 * s, 400 * s)], fill=col, width=5 * s, alpha=0.95)
            L.text((140 * s, 290 * s), title, F(SANS_B, 28 * s), fill=CREAM, alpha=0.95, anchor='ls')
            L.text((140 * s, 345 * s), sub, F(SANS, 18 * s), fill=MUTED, alpha=0.9, anchor='ls')
            # beat-local motion: ion dots or pulse ticks unique to beat index
            for j in range(10):
                u = (local * 0.15 + j / 10) % 1.0
                px = 160 * s + u * 960 * s
                py = 370 * s + 12 * s * math.sin(local * 2.2 + j)
                L.dot((px, py), 3.5 * s, fill=col, alpha=0.35 + 0.35 * math.sin(local * 3 + j))
    chip(L, (100 * s, 420 * s, 1180 * s, 505 * s), cur[2], cur[3], 1.0, cur[4], s)
    progress_rail(L, W, H, tt, TOTAL, s, 6, CYAN)
    footer_tick(L, W, H, tt, s, 'B · ChR 路径 · 多拍连续 · 无短环')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)

# =====================================================================
# SF18 — invivo dual · film ~98.2s · UNIQUE ~96s · photo mouse kept
# 3 acts × 32s: fiber / NpHR / prizes — each with sub-beats
# =====================================================================
def sf18(t, W, H):
    s = W / 1280
    TOTAL = 96.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.35, 0.4)
    L = Layer(W, H)
    # mouse frame always
    L.rrect((60 * s, 110 * s, 560 * s, 400 * s), 10 * s, outline=CYAN, width=2 * s, alpha=0.55)
    L.line([(310 * s, 115 * s), (310 * s, 155 * s)], fill=CYAN, width=2.5 * s,
           alpha=0.7 + 0.3 * math.sin(tt * 2.2))

    if tt < 32.0:
        p = tt
        header(L, W, H, '2007 · 光纤进活体脑', '运动皮层 · 只驱动表达 ChR2 的兴奋性神经元', min(p, 2.0) + 1.0, s)
        # sub-beats within act 1
        chip(L, (600 * s, 130 * s, 1200 * s, 220 * s), '照片鼠 · 锁地 2.5D', '写实毛发/笼箱仍 deferred · 本板用 SF10 照片',
             ramp(p, 0.5, 1.5), CYAN, s)
        chip(L, (600 * s, 240 * s, 1200 * s, 330 * s), '不另加视黄醛', '光也足够做出行为',
             ramp(p, 8.0, 10.0), GOLD, s)
        chip(L, (600 * s, 350 * s, 1200 * s, 440 * s), '2005 培养皿 → 2007 活体', '大约两年',
             ramp(p, 18.0, 20.0), CYAN, s)
        # slow fiber pulse unique across 32s
        pulse = 0.5 + 0.5 * math.sin(p * 0.4)
        rgb = rgb + radial(W, H, 310 * s, 250 * s, 50 * s + 20 * s * pulse, CYAN, 0.12 * pulse)
    elif tt < 64.0:
        p2 = tt - 32.0
        header(L, W, H, '开还不够 · NpHR', '黄光泵入 Cl⁻ · 电压更负 · 锋电位被按住', min(p2, 2.0) + 1.0, s)
        L.rrect((600 * s, 130 * s, 880 * s, 340 * s), 10 * s, fill=(14, 20, 40), alpha=0.85)
        L.rrect((900 * s, 130 * s, 1180 * s, 340 * s), 10 * s, fill=(14, 20, 40), alpha=0.85)
        L.text((740 * s, 190 * s), '蓝光 · 开', F(SANS_B, 24 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.text((740 * s, 250 * s), 'ChR2', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((1040 * s, 190 * s), '黄光 · 关', F(SANS_B, 24 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((1040 * s, 250 * s), 'NpHR', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        # alternating highlight over time
        side = 0.5 + 0.5 * math.sin(p2 * 0.35)
        L.rrect((600 * s, 130 * s, 880 * s, 340 * s), 10 * s, outline=CYAN, width=2 * s, alpha=0.3 + 0.5 * side)
        L.rrect((900 * s, 130 * s, 1180 * s, 340 * s), 10 * s, outline=AMBER, width=2 * s, alpha=0.3 + 0.5 * (1 - side))
        L.text((890 * s, 380 * s), '同一套细胞 · 光谱分开', F(SANS, 16 * s), fill=MUTED, alpha=ramp(p2, 4.0, 6.0), anchor='ms')
        chip(L, (600 * s, 410 * s, 1200 * s, 500 * s), '可从两头问因果', '开与关都在同一只活体里',
             ramp(p2, 12.0, 14.0), GOLD, s)
    else:
        p3 = tt - 64.0
        header(L, W, H, '荣誉不止一份', '2013 Brain Prize 六人 ≠ 2026 诺奖三人', min(p3, 2.0) + 1.0, s)
        six = ['Bamberg', 'Boyden', 'Deisseroth', 'Hegemann', 'Miesenböck', 'Nagel']
        for i, nm in enumerate(six):
            x = 600 * s + (i % 3) * 190 * s
            y = 130 * s + (i // 3) * 90 * s
            aa = ramp(p3, 0.4 + i * 0.6, 1.2 + i * 0.6)
            L.rrect((x, y, x + 170 * s, y + 70 * s), 6 * s, fill=(14, 20, 40), alpha=0.8 * max(aa, 0.15))
            L.text((x + 85 * s, y + 42 * s), nm, F(SANS, 14 * s), fill=CREAM, alpha=max(aa, 0.15), anchor='ms')
        L.text((890 * s, 340 * s), '六人奖  ≠  三人诺奖', F(SANS_B, 20 * s), fill=GOLD,
               alpha=ramp(p3, 10.0, 12.0), anchor='ms')
        chip(L, (600 * s, 380 * s, 1200 * s, 480 * s), '名单不是同一份', 'Brain Prize 六人 · 诺奖三人',
             ramp(p3, 18.0, 20.0), AMBER, s)

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'B · 活体 / 双色 · 多拍 · 照片鼠嵌板')
    out = over(rgb, L.get())
    # subtle Ken-burns-ish offset of photo over 96s (unique, no wrap)
    ox = int(72 * s + 8 * s * math.sin(tt * 0.07))
    oy = int(118 * s + 5 * s * math.cos(tt * 0.05))
    out = place(out, _sf10_rgb, _sf10_a * 0.92, ox, oy, opacity=0.98)
    return grade(out, seed=int(tt * 24) % 100000)

# =====================================================================
# SF19 — engram · film ~89.1s · UNIQUE ~88s · photo mouse kept
# Linear story: setup → cells → shock → freeze → caveat (no wrap)
# =====================================================================
def sf19(t, W, H):
    s = W / 1280
    TOTAL = 88.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.4, 0.45)
    L = Layer(W, H)
    header(L, W, H, '小鼠海马 · 假恐惧记忆（2013）', '只讲小鼠 · 不讲人体记忆操作', min(tt, 2.0) + 1.0, s)

    # env panels always after early ramp
    aA = ramp(tt, 0.5, 2.0)
    aB = ramp(tt, 8.0, 12.0)
    L.rrect((50 * s, 100 * s, 500 * s, 340 * s), 12 * s, fill=(20, 35, 70), alpha=0.88 * aA)
    L.rrect((700 * s, 100 * s, 1150 * s, 340 * s), 12 * s, fill=(70, 30, 40), alpha=0.88 * max(aB, 0.25))
    L.text((275 * s, 130 * s), '环境甲', F(SANS_B, 22 * s), fill=CYAN, alpha=0.95 * aA, anchor='ms')
    L.text((925 * s, 130 * s), '环境乙', F(SANS_B, 22 * s), fill=AMBER, alpha=0.95 * max(aB, 0.25), anchor='ms')

    # cells light up progressively 12–28s
    n_on = int(np.clip((tt - 12.0) / 16.0, 0, 1) * 8)
    for i in range(8):
        x = 100 * s + (i % 4) * 90 * s
        y = 180 * s + (i // 4) * 60 * s
        on = 1.0 if i < n_on else 0.25
        pulse = 0.6 + 0.4 * math.sin(tt * 2.5 + i) if i < n_on else 0.3
        L.dot((x, y), 7 * s, fill=GOLD, alpha=on * pulse * aA)

    L.text((275 * s, 310 * s), '齿状回细胞 · ChR2', F(SANS, 14 * s), fill=CREAM,
           alpha=ramp(tt, 14.0, 18.0), anchor='ms')
    L.text((925 * s, 240 * s), '电击 + 光召回甲细胞', F(SANS, 14 * s), fill=CREAM,
           alpha=ramp(tt, 28.0, 34.0), anchor='ms')
    # shock flash accent 28–36
    if 28.0 <= tt < 40.0:
        flash = math.sin((tt - 28.0) * 2.0) ** 2
        rgb = rgb + radial(W, H, 925 * s, 220 * s, 80 * s, AMBER, 0.18 * flash)

    chip(L, (50 * s, 360 * s, 1150 * s, 435 * s), '再回甲：无电击，却冻结',
         '作者：制造出虚假恐惧记忆', ramp(tt, 40.0, 46.0), GOLD, s)
    chip(L, (50 * s, 450 * s, 1150 * s, 520 * s),
         '写进去的是一批细胞的活动 · 不是一句话 / 一段人生',
         '小鼠恐惧行为已驱动 · 人体记忆：本研究不涉及',
         ramp(tt, 58.0, 66.0), AMBER, s)

    progress_rail(L, W, H, tt, TOTAL, s, 5, GOLD)
    footer_tick(L, W, H, tt, s, 'C · 假记忆 · 线性多拍 · 照片鼠 · 笼写实 deferred')
    out = over(rgb, L.get())
    mr2, ma2 = _mouse_rgb, np.maximum(_mouse_a, 0.35)
    # slow dual drift
    ox1 = int(120 * s + 6 * math.sin(tt * 0.06))
    oy1 = int(150 * s + 4 * math.cos(tt * 0.05))
    ox2 = int(770 * s + 6 * math.cos(tt * 0.05))
    oy2 = int(150 * s + 4 * math.sin(tt * 0.07))
    out = place(out, mr2, ma2, ox1, oy1, opacity=0.98)
    out = place(out, mr2 * np.array([1.04, 0.92, 0.92], np.float32), ma2, ox2, oy2, opacity=0.98)
    return grade(out, seed=int(tt * 24) % 100000)

# =====================================================================
# SF23 — limits + close · film ~103.9s · UNIQUE ~100s
# Act A limits 0–38 · Act B do/don't 38–68 · Act C close 68–100
# =====================================================================
def sf23(t, W, H):
    s = W / 1280
    TOTAL = 100.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.4, 0.4)
    L = Layer(W, H)

    if tt < 38.0:
        p = tt
        header(L, W, H, '边界停在已发表的事实', '脱敏 · 光必须送到细胞旁 · 部分且绑装置',
               min(p, 2.0) + 1.0, s)
        items = [
            (2.0,  '限制 1', '持续光照 → ChR2 脱敏', '不能当成永不疲劳的门'),
            (12.0, '限制 2', '光得送到细胞旁边', '脑：光纤 · 眼：护目镜'),
            (22.0, '限制 3', '人体视觉：部分功能', '一条未获批 · 一条无上市许可'),
        ]
        for i, (t0, k, a, b) in enumerate(items):
            y = 130 * s + i * 100 * s
            aa = ramp(p, t0, t0 + 1.5)
            # stay visible after reveal (no fade-out / wrap)
            hold = 1.0 if p >= t0 else 0.0
            alpha = max(aa, 0.15 * hold) if p >= t0 else 0.0
            if alpha <= 0: continue
            L.rrect((100 * s, y, 1180 * s, y + 80 * s), 8 * s, fill=(14, 20, 40), alpha=0.78 * alpha)
            L.text((130 * s, y + 30 * s), k, F(SANS_B, 16 * s), fill=GOLD, alpha=alpha, anchor='ls')
            L.text((280 * s, y + 30 * s), a, F(SANS_B, 20 * s), fill=CREAM, alpha=alpha, anchor='ls')
            L.text((280 * s, y + 58 * s), b, F(SANS, 15 * s), fill=MUTED, alpha=alpha, anchor='ls')
        # dwell pulse on active card
        active_i = 0
        for i, (t0, *_rest) in enumerate(items):
            if p >= t0: active_i = i
        y = 130 * s + active_i * 100 * s
        L.rrect((100 * s, y, 1180 * s, y + 80 * s), 8 * s, outline=CYAN, width=1.5 * s,
                alpha=0.25 + 0.25 * math.sin(p * 1.2))
    elif tt < 68.0:
        p2 = tt - 38.0
        header(L, W, H, '做得到 / 做不到', '', min(p2, 2.0) + 1.0, s)
        L.rrect((80 * s, 120 * s, 600 * s, 420 * s), 12 * s, fill=(14, 40, 30), alpha=0.75)
        L.rrect((640 * s, 120 * s, 1160 * s, 420 * s), 12 * s, fill=(40, 20, 20), alpha=0.75)
        L.text((340 * s, 170 * s), '做得到', F(SANS_B, 28 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.text((340 * s, 250 * s), '实验里打开或关掉', F(SANS, 18 * s), fill=CREAM,
               alpha=ramp(p2, 2.0, 4.0), anchor='ms')
        L.text((340 * s, 300 * s), '选定细胞 · 推进成因果', F(SANS, 18 * s), fill=CREAM,
               alpha=ramp(p2, 8.0, 10.0), anchor='ms')
        L.text((340 * s, 360 * s), '小鼠行为可被驱动', F(SANS, 16 * s), fill=MUTED,
               alpha=ramp(p2, 14.0, 16.0), anchor='ms')
        L.text((900 * s, 170 * s), '做不到', F(SANS_B, 28 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((900 * s, 250 * s), '小鼠恐惧 ≠ 某人的人生', F(SANS, 17 * s), fill=CREAM,
               alpha=ramp(p2, 4.0, 6.0), anchor='ms')
        L.text((900 * s, 300 * s), '部分视觉 ≠ 失明结束', F(SANS, 17 * s), fill=CREAM,
               alpha=ramp(p2, 10.0, 12.0), anchor='ms')
        L.text((900 * s, 360 * s), '受理 ≠ 上市许可', F(SANS, 16 * s), fill=MUTED,
               alpha=ramp(p2, 18.0, 20.0), anchor='ms')
    else:
        p3 = tt - 68.0
        header(L, W, H, '牵强的是当年的工程', '今天：实验方法 · 仍在审查的临床尝试',
               min(p3, 2.0) + 1.0, s)
        # title grows then holds
        L.text((W / 2, 250 * s), '光遗传学', F(SERIF_B, 64 * s), fill=CREAM,
               alpha=ramp(p3, 0.5, 3.0), anchor='ms', tracking=6 * s)
        line_w = 160 * s * ease_out(ramp(p3, 4.0, 10.0))
        L.line([(W / 2 - line_w, 300 * s), (W / 2 + line_w, 300 * s)], fill=CYAN, width=2 * s,
               alpha=ramp(p3, 4.0, 8.0))
        L.text((W / 2, 360 * s), '这一期在这里结束', F(SANS, 20 * s), fill=MUTED,
               alpha=ramp(p3, 14.0, 18.0), anchor='ms')
        L.text((W / 2, 420 * s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 14 * s), fill=MUTED,
               alpha=ramp(p3, 20.0, 24.0) * 0.85, anchor='ms')

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'D · 边界与收束 · 多拍连续')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


SCENES = {
    'SF16_chr_path': (sf16, 120.0),
    'SF18_invivo_dual': (sf18, 96.0),
    'SF19_engram': (sf19, 88.0),
    'SF23_limits_close': (sf23, 100.0),
}


def render_one(name):
    fn, dur = SCENES[name]
    n = int(round(dur * FPS))
    still_t = dur * 0.45
    png = f'{OUT}/{name}.png'
    mp4 = f'{OUT}/{name}.mp4'
    print(f'render {name} dur={dur}s frames={n}', flush=True)
    save(fn(still_t, 1280, 720), png)
    t0 = _time.time()
    write_video(lambda i, fn=fn: fn(i / FPS, W, H), n, mp4, W, H, FPS)
    print(f'  done {png} {mp4} in {_time.time()-t0:.1f}s', flush=True)


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SCENES)
    for n in names:
        if n not in SCENES:
            raise SystemExit(f'unknown {n}')
        render_one(n)
    print('ALL_OK', len(names))
