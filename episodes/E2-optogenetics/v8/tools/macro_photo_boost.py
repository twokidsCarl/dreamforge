#!/usr/bin/env python3
"""Macro photo boost: larger dual-layer photo insets + ken-burns on SF18/19/21.
Keeps multibeat durations (96/88/46). Caption-safe above ~0.80H. $0 / no Blender.
"""
from __future__ import annotations
import math, sys, time as _time
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
CAP = 0.80  # keep primary content above this fraction of H

def load_rgba(path):
    im = Image.open(path).convert('RGBA')
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr[..., :3], arr[..., 3:4]

def matte_gray(rgb, a, thr=0.90):
    lum = rgb.mean(axis=2, keepdims=True)
    sat = rgb.max(axis=2, keepdims=True) - rgb.min(axis=2, keepdims=True)
    bgm = (lum > thr) & (sat < 0.08)
    aa = a.copy(); aa[bgm] = 0.0
    return rgb, aa

def kb_crop(rgb, a, tw, th, t, total, pan_x=0.04, pan_y=0.03, zoom_amp=0.06):
    """Ken-burns crop from larger plate into tw×th. t progresses 0..total."""
    h, w = rgb.shape[:2]
    frac = min(max(t / max(total, 1e-6), 0), 1)
    zoom = 1.0 + zoom_amp * frac
    # source window size
    sw = tw / zoom; sh = th / zoom
    # if plate smaller than window, just resize whole
    if w < sw or h < sh:
        im = Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        aa = Image.fromarray((np.clip(a[...,0],0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        return np.asarray(im).astype(np.float32)/255, (np.asarray(aa).astype(np.float32)/255)[..., None]
    cx = 0.5 + pan_x * math.sin(frac * math.pi)   # one-way feel across board
    cy = 0.5 + pan_y * math.cos(frac * math.pi * 0.7)
    x0 = int(np.clip(cx * w - sw / 2, 0, w - sw))
    y0 = int(np.clip(cy * h - sh / 2, 0, h - sh))
    x1, y1 = int(x0 + sw), int(y0 + sh)
    patch = rgb[y0:y1, x0:x1]
    pa = a[y0:y1, x0:x1]
    im = Image.fromarray((np.clip(patch,0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    aa = Image.fromarray((np.clip(pa[...,0] if pa.ndim==3 else pa,0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)/255, (np.asarray(aa).astype(np.float32)/255)[..., None]


def fit_plate(rgb, a, tw, th, t, total, pan_x=0.02, pan_y=0.015, zoom_amp=0.02, pad_rgb=(0.05, 0.07, 0.12)):
    """Contain full plate in tw×th (letterbox), then gentle KB — avoids hindquarter crops."""
    h, w = rgb.shape[:2]
    # scale to fit inside (1+zoom_amp) virtual canvas so mild zoom still shows whole body
    frac = min(max(t / max(total, 1e-6), 0), 1)
    zoom = 1.0 + zoom_amp * frac
    # base contain scale into tw×th
    scale0 = min(tw / w, th / h)
    # render onto canvas slightly larger than panel, then crop window = panel
    cw, ch = int(tw * (1.0 + zoom_amp + 0.04)), int(th * (1.0 + zoom_amp + 0.04))
    scale = min(cw / w, ch / h) * 0.92  # small margin so body not edge-clipped
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    im = Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    aa = Image.fromarray((np.clip(a[...,0] if a.ndim==3 else a,0,1)*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = np.zeros((ch, cw, 3), np.float32)
    canvas[:] = np.array(pad_rgb, np.float32)
    ca = np.zeros((ch, cw, 1), np.float32)
    x0 = (cw - nw) // 2; y0 = (ch - nh) // 2
    canvas[y0:y0+nh, x0:x0+nw] = np.asarray(im).astype(np.float32)/255
    ca[y0:y0+nh, x0:x0+nw] = (np.asarray(aa).astype(np.float32)/255)[..., None]
    # mild pan within canvas
    sw, sh = tw / zoom, th / zoom
    cx = 0.5 + pan_x * math.sin(frac * math.pi)
    cy = 0.5 + pan_y * math.cos(frac * math.pi * 0.7)
    sx0 = int(np.clip(cx * cw - sw / 2, 0, max(0, cw - sw)))
    sy0 = int(np.clip(cy * ch - sh / 2, 0, max(0, ch - sh)))
    sx1, sy1 = int(sx0 + sw), int(sy0 + sh)
    patch = canvas[sy0:sy1, sx0:sx1]
    pa = ca[sy0:sy1, sx0:sx1]
    im2 = Image.fromarray((np.clip(patch,0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    aa2 = Image.fromarray((np.clip(pa[...,0],0,1)*255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
    return np.asarray(im2).astype(np.float32)/255, (np.asarray(aa2).astype(np.float32)/255)[..., None]

def place(dst, src, a, x, y, opacity=1.0):
    h, w = src.shape[:2]; Hh, Ww = dst.shape[:2]
    x0, y0 = int(x), int(y)
    x1, y1 = min(Ww, x0 + w), min(Hh, y0 + h)
    if x1 <= x0 or y1 <= y0: return dst
    sx0 = max(0, -x0); sy0 = max(0, -y0)
    dx0 = max(0, x0); dy0 = max(0, y0)
    sw, sh = x1 - dx0, y1 - dy0
    pa = a[sy0:sy0+sh, sx0:sx0+sw] * opacity
    region = dst[dy0:dy0+sh, dx0:dx0+sw]
    dst[dy0:dy0+sh, dx0:dx0+sw] = region * (1 - pa) + src[sy0:sy0+sh, sx0:sx0+sw] * pa
    return dst

def bg(W, H, t, accent=CYAN, ax=0.3, ay=0.4):
    ax2 = ax + 0.03 * math.sin(t * 0.1)
    ay2 = ay + 0.02 * math.cos(t * 0.08)
    rgb = np.zeros((H, W, 3), np.float32) + np.array(INK) / 255
    rgb = rgb + radial(W, H, W * ax2, H * ay2, W * 0.35, accent, 0.18 + 0.03 * math.sin(t * 0.6))
    rgb = rgb + radial(W, H, W * 0.75, H * 0.65, W * 0.25, GOLD, 0.06)
    return rgb

def chip(L, box, title, sub, t, accent=GOLD, s=1.0):
    a = float(np.clip(t, 0, 1))
    if a <= 0: return
    x0, y0, x1, y1 = box
    L.rrect((x0, y0, x1, y1), 8 * s, fill=(14, 20, 40), alpha=0.78 * a)
    L.line([(x0, y0), (x0, y1)], fill=accent, width=3 * s, alpha=a)
    L.text((x0 + 14 * s, y0 + 26 * s), title, F(SANS_B, 20 * s), fill=CREAM, alpha=a, anchor='ls')
    if sub:
        L.text((x0 + 14 * s, y0 + 52 * s), sub, F(SANS, 14 * s), fill=MUTED, alpha=a, anchor='ls')

def header(L, W, H, title, sub, t, s):
    a = ramp(t, 0.0, 0.5)
    L.text((W / 2, 36 * s), title, F(SANS_B, 20 * s), fill=GOLD, alpha=a, anchor='ms', tracking=2 * s)
    if sub:
        L.text((W / 2, 62 * s), sub, F(SANS, 14 * s), fill=MUTED, alpha=ramp(t, 0.3, 0.9), anchor='ms')

def footer_tick(L, W, H, t, s, label=''):
    a = 0.4 + 0.1 * math.sin(t * 1.2)
    L.line([(80 * s, H - 24 * s), (W - 80 * s, H - 24 * s)], fill=(50, 60, 90), width=1 * s, alpha=a)
    if label:
        L.text((W / 2, H - 12 * s), label, F(SANS, 10 * s), fill=MUTED, alpha=0.5, anchor='ms')

def progress_rail(L, W, H, t, total, s, n, accent=CYAN):
    frac = min(max(t / max(total, 1e-6), 0), 1)
    y = H * CAP + 6 * s
    x0, x1 = 100 * s, W - 100 * s
    L.line([(x0, y), (x1, y)], fill=(40, 50, 80), width=2 * s, alpha=0.45)
    L.line([(x0, y), (x0 + (x1 - x0) * frac, y)], fill=accent, width=2.2 * s, alpha=0.8)
    for i in range(n):
        xf = x0 + (x1 - x0) * (i / max(n - 1, 1))
        on = frac >= i / max(n - 1, 1)
        L.dot((xf, y), 3.2 * s, fill=accent if on else (60, 70, 100), alpha=0.85 if on else 0.3)

# ---- load plates once ----
_sf10_rgb, _sf10_a = load_rgba('/workspace/e2work/v8/styleframes/SF10_mouse_tripo.png')
_sf10_a = np.ones((_sf10_rgb.shape[0], _sf10_rgb.shape[1], 1), np.float32)

_sleep_rgb, _sleep_a = load_rgba('/workspace/e2work/v8/gen/sf10_sleep.png')
_sleep_rgb, _sleep_a = matte_gray(_sleep_rgb, _sleep_a, 0.92)

_awake_rgb, _awake_a = load_rgba('/workspace/e2work/v8/gen/sf10_awake.png')
_awake_rgb, _awake_a = matte_gray(_awake_rgb, _awake_a, 0.92)


_sleep_tq_rgb, _sleep_tq_a = load_rgba('/workspace/e2work/v8/gen/sf10_sleep_threeq.png')
_sleep_tq_rgb, _sleep_tq_a = matte_gray(_sleep_tq_rgb, _sleep_tq_a, 0.92)

_awake_tq_rgb, _awake_tq_a = load_rgba('/workspace/e2work/v8/gen/sf10_awake_threeq.png')
_awake_tq_rgb, _awake_tq_a = matte_gray(_awake_tq_rgb, _awake_tq_a, 0.92)

_mref_rgb, _mref_a = load_rgba('/workspace/e2work/v8/gen/mouse_ref.png')
_mref_rgb, _mref_a = matte_gray(_mref_rgb, _mref_a, 0.90)

_eye_rgb, _eye_a = load_rgba('/workspace/e2work/v8/gen/sf11_eye.png')
_gog_rgb, _gog_a = load_rgba('/workspace/e2work/v8/gen/sf11_goggles.png')
_sf11still_rgb, _sf11still_a = load_rgba('/workspace/e2work/v8/styleframes/SF11_eye_goggles.png')
_sf11still_a = np.ones((_sf11still_rgb.shape[0], _sf11still_rgb.shape[1], 1), np.float32)


# =====================================================================
# SF18 — photo-forward invivo · 96s
# Layout: LARGE photo left (~58% width), slim chips right; plate swaps by act
# =====================================================================
def sf18(t, W, H):
    s = W / 1280
    TOTAL = 96.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.28, 0.38)
    L = Layer(W, H)

    # large photo frame (caption-safe bottom)
    fx0, fy0 = 40 * s, 85 * s
    fx1, fy1 = 720 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)
    # fiber accent
    L.line([((fx0 + fx1) / 2, fy0 + 4 * s), ((fx0 + fx1) / 2, fy0 + 36 * s)],
           fill=CYAN, width=2.5 * s, alpha=0.65 + 0.3 * math.sin(tt * 1.8))

    if tt < 32.0:
        p = tt
        header(L, W, H, '2007 · 光纤进活体脑', '运动皮层 · 只驱动表达 ChR2 的兴奋性神经元', min(p, 2.0) + 1.0, s)
        chip(L, (740 * s, 100 * s, 1240 * s, 185 * s), '不另加视黄醛', '光也足够做出行为',
             ramp(p, 2.0, 4.0), GOLD, s)
        chip(L, (740 * s, 205 * s, 1240 * s, 290 * s), '2005 培养皿 → 2007 活体', '大约两年',
             ramp(p, 12.0, 14.0), CYAN, s)
        chip(L, (740 * s, 310 * s, 1240 * s, H * CAP - 14 * s), '光纤植入 · 清醒活动', '头戴光纤 · 自由走动',
             ramp(p, 20.0, 22.0), CYAN, s)
        plate_mode = 'sf10'
    elif tt < 64.0:
        p2 = tt - 32.0
        header(L, W, H, '开还不够 · NpHR', '黄光泵入 Cl⁻ · 电压更负 · 锋电位被按住', min(p2, 2.0) + 1.0, s)
        chip(L, (740 * s, 100 * s, 980 * s, 220 * s), '蓝光 · 开', 'ChR2',
             1.0, CYAN, s)
        chip(L, (1000 * s, 100 * s, 1240 * s, 220 * s), '黄光 · 关', 'NpHR',
             1.0, AMBER, s)
        chip(L, (740 * s, 240 * s, 1240 * s, 330 * s), '同一套细胞 · 光谱分开', '可从两头问因果',
             ramp(p2, 6.0, 9.0), GOLD, s)
        chip(L, (740 * s, 350 * s, 1240 * s, H * CAP - 14 * s), '开与关都在同一只活体里', '蓝开黄关 · 同一只鼠',
             ramp(p2, 16.0, 18.0), CYAN, s)
        plate_mode = 'awake'
        side = 0.5 + 0.5 * math.sin(p2 * 0.35)
        rgb = rgb + radial(W, H, 380 * s, 250 * s, 60 * s, CYAN if side > 0.5 else AMBER, 0.10)
    else:
        p3 = tt - 64.0
        header(L, W, H, '荣誉不止一份', '2013 Brain Prize 六人 ≠ 2026 诺奖三人', min(p3, 2.0) + 1.0, s)
        six = ['Bamberg', 'Boyden', 'Deisseroth', 'Hegemann', 'Miesenböck', 'Nagel']
        for i, nm in enumerate(six):
            x = 740 * s + (i % 2) * 250 * s
            y = 95 * s + (i // 2) * 70 * s
            aa = ramp(p3, 0.3 + i * 0.5, 1.0 + i * 0.5)
            L.rrect((x, y, x + 230 * s, y + 55 * s), 6 * s, fill=(14, 20, 40), alpha=0.8 * max(aa, 0.2))
            L.text((x + 115 * s, y + 34 * s), nm, F(SANS, 14 * s), fill=CREAM, alpha=max(aa, 0.2), anchor='ms')
        chip(L, (740 * s, 320 * s, 1240 * s, H * CAP - 14 * s), '六人奖 ≠ 三人诺奖', '名单不是同一份',
             ramp(p3, 12.0, 15.0), GOLD, s)
        plate_mode = 'sleep'

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'B · 活体 · 光纤植入小鼠')
    out = over(rgb, L.get())

    # photo into frame with ken-burns; soft crossfade between act plates
    tw = int(fx1 - fx0 - 16 * s)
    th = int(fy1 - fy0 - 16 * s)
    if plate_mode == 'sf10':
        # full-body contain (avoid hindquarter crop)
        pr, pa = fit_plate(_sf10_rgb, _sf10_a, tw, th, tt, TOTAL, pan_x=0.015, pan_y=0.01, zoom_amp=0.02)
        pa = np.ones_like(pa)
    elif plate_mode == 'awake':
        pr, pa = fit_plate(_awake_rgb, _awake_a, tw, th, tt - 32.0, 32.0, pan_x=0.02, pan_y=0.015, zoom_amp=0.025)
        # soft pad where matte is empty
        pa = np.maximum(pa, 0.25)
    else:
        pr, pa = fit_plate(_sleep_rgb, _sleep_a, tw, th, tt - 64.0, 32.0, pan_x=-0.02, pan_y=0.015, zoom_amp=0.025)
        pa = np.maximum(pa, 0.25)
    out = place(out, pr, pa, int(fx0 + 8 * s), int(fy0 + 8 * s), opacity=0.98)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF19 — engram photo-forward · 88s
# Large A/B photo panels (sleep vs awake); chips below caption-safe
# =====================================================================
def sf19(t, W, H):
    s = W / 1280
    TOTAL = 88.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.38, 0.42)
    L = Layer(W, H)
    header(L, W, H, '小鼠海马 · 假恐惧记忆（2013）', '只讲小鼠 · 不讲人体记忆操作', min(tt, 2.0) + 1.0, s)

    # two large photo frames
    aA = ramp(tt, 0.4, 1.5)
    aB = ramp(tt, 6.0, 10.0)
    y1 = H * CAP - 90 * s  # leave room for chips
    L.rrect((40 * s, 80 * s, 610 * s, y1), 12 * s, fill=(16, 28, 55), alpha=0.55 * aA)
    L.rrect((670 * s, 80 * s, 1240 * s, y1), 12 * s, fill=(55, 22, 30), alpha=0.55 * max(aB, 0.2))
    L.rrect((40 * s, 80 * s, 610 * s, y1), 12 * s, outline=CYAN, width=1.5 * s, alpha=0.45 * aA)
    L.rrect((670 * s, 80 * s, 1240 * s, y1), 12 * s, outline=AMBER, width=1.5 * s, alpha=0.45 * max(aB, 0.2))
    L.text((325 * s, 100 * s), '环境甲', F(SANS_B, 18 * s), fill=CYAN, alpha=0.95 * aA, anchor='ms')
    L.text((955 * s, 100 * s), '环境乙', F(SANS_B, 18 * s), fill=AMBER, alpha=0.95 * max(aB, 0.2), anchor='ms')

    # cell dots overlay (small, not covering faces)
    n_on = int(np.clip((tt - 10.0) / 14.0, 0, 1) * 6)
    for i in range(6):
        x = 70 * s + (i % 3) * 70 * s
        y = y1 - 50 * s + (i // 3) * 22 * s
        on = 1.0 if i < n_on else 0.2
        L.dot((x, y), 5 * s, fill=GOLD, alpha=on * (0.5 + 0.4 * math.sin(tt * 2 + i)) * aA)

    L.text((325 * s, y1 - 18 * s), '齿状回 · ChR2', F(SANS, 12 * s), fill=CREAM,
           alpha=ramp(tt, 12.0, 16.0), anchor='ms')
    L.text((955 * s, y1 - 18 * s), '电击 + 光召回', F(SANS, 12 * s), fill=CREAM,
           alpha=ramp(tt, 24.0, 30.0), anchor='ms')

    if 24.0 <= tt < 38.0:
        flash = math.sin((tt - 24.0) * 1.6) ** 2
        rgb = rgb + radial(W, H, 955 * s, (80 * s + y1) / 2, 90 * s, AMBER, 0.16 * flash)

    chip(L, (40 * s, H * CAP - 78 * s, 1240 * s, H * CAP - 8 * s),
         '再回甲：无电击，却冻结 · 虚假恐惧记忆',
         '写进去的是一批细胞的活动 · 人体记忆：本研究不涉及',
         ramp(tt, 38.0, 46.0), GOLD, s)

    progress_rail(L, W, H, tt, TOTAL, s, 5, GOLD)
    footer_tick(L, W, H, tt, s, 'C · 假记忆 · 环境甲 / 环境乙')
    out = over(rgb, L.get())

    # photo panels: A = sleep (calm), B = awake (stressed tint)
    pw = int(610 * s - 40 * s - 20 * s)
    ph = int(y1 - 80 * s - 50 * s)
    prA, paA = fit_plate(_sleep_tq_rgb, _sleep_tq_a, pw, ph, tt, TOTAL, pan_x=0.015, pan_y=0.01, zoom_amp=0.018)
    prB, paB = fit_plate(_awake_tq_rgb, _awake_tq_a, pw, ph, tt, TOTAL, pan_x=-0.015, pan_y=0.01, zoom_amp=0.018)
    # warm tint on B
    prB = np.clip(prB * np.array([1.06, 0.94, 0.92], np.float32), 0, 1)
    paA = np.maximum(paA, 0.35)
    paB = np.maximum(paB, 0.35)
    out = place(out, prA, paA * aA, int(50 * s), int(115 * s), opacity=0.97)
    out = place(out, prB, paB * max(aB, 0.15), int(680 * s), int(115 * s), opacity=0.97)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF21 — dual-layer eye/goggles ken-burns · 46s
# =====================================================================
def sf21(t, W, H):
    s = W / 1280
    TOTAL = 46.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.38, 0.38)
    L = Layer(W, H)
    header(L, W, H, '部分功能恢复', '必须戴护目镜 · 不是日常视觉', min(tt, 2.0) + 1.0, s)

    # large apparatus frame right
    fx0, fy0 = 560 * s, 85 * s
    fx1, fy1 = 1240 * s, H * CAP - 85 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=AMBER, width=2 * s, alpha=0.5)

    # left: sparse objects progressive
    objs = [(160, 160), (300, 145), (420, 175), (240, 240), (380, 255)]
    n_vis = max(1, int(np.clip(tt / 10.0, 0, 1) * len(objs)))
    gog = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(tt * 0.28))
    for i, (x, y) in enumerate(objs[:n_vis]):
        pulse = 0.55 + 0.45 * math.sin(tt * 2.0 + i)
        L.rrect(((x - 30) * s, (y - 30) * s, (x + 30) * s, (y + 30) * s), 4 * s,
                outline=CREAM, width=1.5 * s, alpha=0.8 * gog * pulse)
        L.dot((x * s, y * s), 4 * s, fill=AMBER, alpha=0.85 * gog)

    chip(L, (40 * s, H * CAP - 78 * s, 540 * s, H * CAP - 8 * s),
         '戴护目镜：能指 / 数 / 触到', '摘掉：看不见',
         ramp(tt, 12.0, 16.0), GOLD, s)
    chip(L, (560 * s, H * CAP - 78 * s, 1240 * s, H * CAP - 8 * s),
         '亮度变化 → 视网膜光脉冲 · ChrimsonR', '无人脸 · 护目镜装置板',
         ramp(tt, 20.0, 24.0), AMBER, s)

    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'C · 部分视觉 · 眼/护目镜双层照片 · 无人脸')
    out = over(rgb, L.get())

    tw = int(fx1 - fx0 - 16 * s)
    th = int(fy1 - fy0 - 16 * s)
    # dual-layer: eye early → goggles mid → SF11 still late, soft blends
    # blend weights across 46s
    w_eye = float(np.clip(1.0 - (tt - 8.0) / 18.0, 0, 1))
    w_gog = float(np.clip(min(tt / 12.0, (38.0 - tt) / 14.0), 0, 1))
    w_still = float(np.clip((tt - 28.0) / 12.0, 0, 1))
    ws = w_eye + w_gog + w_still + 1e-6
    w_eye, w_gog, w_still = w_eye / ws, w_gog / ws, w_still / ws

    pr1, pa1 = kb_crop(_eye_rgb, np.ones((_eye_rgb.shape[0], _eye_rgb.shape[1], 1), np.float32),
                       tw, th, tt, TOTAL, pan_x=0.05, pan_y=0.03, zoom_amp=0.08)
    pr2, pa2 = kb_crop(_gog_rgb, np.ones((_gog_rgb.shape[0], _gog_rgb.shape[1], 1), np.float32),
                       tw, th, tt, TOTAL, pan_x=-0.04, pan_y=0.02, zoom_amp=0.07)
    pr3, pa3 = kb_crop(_sf11still_rgb, _sf11still_a, tw, th, tt, TOTAL, pan_x=0.02, pan_y=-0.02, zoom_amp=0.04)

    blend = pr1 * w_eye + pr2 * w_gog + pr3 * w_still
    ba = np.ones((th, tw, 1), np.float32)
    out = place(out, blend, ba, int(fx0 + 8 * s), int(fy0 + 8 * s), opacity=0.97)
    return grade(out, seed=int(tt * 24) % 100000)


SCENES = {
    'SF18_invivo_dual': (sf18, 96.0),
    'SF19_engram': (sf19, 88.0),
    'SF21_partial_vision': (sf21, 46.0),
}

def render_one(name):
    fn, dur = SCENES[name]
    n = int(round(dur * FPS))
    print(f'render {name} dur={dur}s frames={n}', flush=True)
    save(fn(dur * 0.4, 1280, 720), f'{OUT}/{name}.png')
    t0 = _time.time()
    write_video(lambda i, fn=fn: fn(i / FPS, W, H), n, f'{OUT}/{name}.mp4', W, H, FPS)
    print(f'  done in {_time.time()-t0:.1f}s', flush=True)

if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SCENES)
    for n in names:
        render_one(n)
    print('ALL_OK', len(names))
