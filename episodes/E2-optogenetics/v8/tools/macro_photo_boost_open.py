#!/usr/bin/env python3
"""Macro photo boost OPEN: photo/clean rebuild of residual opening illustration.
SF01/02/03/06/07/08/09/11/12 (~91s film). Diverse plates — NOT one mouse side KB.
People → clean 2.5D; apparatus/eye → SF21-class; mouse → multi-pose/multi-cam;
micro (microbes/ChR2) → LARGE clean micro plates (scale-correct). $0 / no Blender.
Caption-safe above ~0.80H. No deferred on-screen copy.
"""
from __future__ import annotations
import math, sys, time as _time, os
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
CAP = 0.80
GEN = '/workspace/e2work/v8/gen'
STILLS = '/workspace/e2work/v8/renders/sf18_19_stills'

def load_rgba(path):
    im = Image.open(path).convert('RGBA')
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr[..., :3], arr[..., 3:4]

def load_full(path):
    rgb, a = load_rgba(path)
    return rgb, np.ones((rgb.shape[0], rgb.shape[1], 1), np.float32), True

def matte_gray(rgb, a, thr=0.90):
    lum = rgb.mean(axis=2, keepdims=True)
    sat = rgb.max(axis=2, keepdims=True) - rgb.min(axis=2, keepdims=True)
    bgm = (lum > thr) & (sat < 0.08)
    aa = a.copy(); aa[bgm] = 0.0
    return rgb, aa

def fit_plate(rgb, a, tw, th, t, total, pan_x=0.02, pan_y=0.015, zoom_amp=0.02, pad_rgb=(0.05, 0.07, 0.12), fit=0.92):
    h, w = rgb.shape[:2]
    frac = min(max(t / max(total, 1e-6), 0), 1)
    zoom = 1.0 + zoom_amp * frac
    cw, ch = int(tw * (1.0 + zoom_amp + 0.04)), int(th * (1.0 + zoom_amp + 0.04))
    scale = min(cw / w, ch / h) * fit
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    # if fit>1 makes plate larger than crop canvas, expand canvas
    cw = max(cw, nw + 4); ch = max(ch, nh + 4)
    im = Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    aa = Image.fromarray((np.clip(a[...,0] if a.ndim==3 else a,0,1)*255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = np.zeros((ch, cw, 3), np.float32); canvas[:] = np.array(pad_rgb, np.float32)
    ca = np.zeros((ch, cw, 1), np.float32)
    x0 = (cw - nw) // 2; y0 = (ch - nh) // 2
    canvas[y0:y0+nh, x0:x0+nw] = np.asarray(im).astype(np.float32)/255
    ca[y0:y0+nh, x0:x0+nw] = (np.asarray(aa).astype(np.float32)/255)[..., None]
    sw, sh = tw / zoom, th / zoom
    cx = 0.5 + pan_x * math.sin(frac * math.pi)
    cy = 0.5 + pan_y * math.cos(frac * math.pi * 0.7)
    sx0 = int(np.clip(cx * cw - sw / 2, 0, max(0, cw - sw)))
    sy0 = int(np.clip(cy * ch - sh / 2, 0, max(0, ch - sh)))
    sx1, sy1 = int(sx0 + sw), int(sy0 + sh)
    patch = canvas[sy0:sy1, sx0:sx1]; pa = ca[sy0:sy1, sx0:sx1]
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
    L.text((x0 + 14 * s, y0 + 26 * s), title, F(SANS_B, 18 * s), fill=CREAM, alpha=a, anchor='ls')
    if sub:
        L.text((x0 + 14 * s, y0 + 50 * s), sub, F(SANS, 13 * s), fill=MUTED, alpha=a, anchor='ls')

def header(L, W, H, title, sub, t, s):
    a = ramp(t, 0.0, 0.5)
    L.text((W / 2, 34 * s), title, F(SANS_B, 20 * s), fill=GOLD, alpha=a, anchor='ms', tracking=2 * s)
    if sub:
        L.text((W / 2, 58 * s), sub, F(SANS, 13 * s), fill=MUTED, alpha=ramp(t, 0.25, 0.8), anchor='ms')

def footer_tick(L, W, H, t, s, label=''):
    a = 0.4 + 0.1 * math.sin(t * 1.2)
    L.line([(80 * s, H - 22 * s), (W - 80 * s, H - 22 * s)], fill=(50, 60, 90), width=1 * s, alpha=a)
    if label:
        L.text((W / 2, H - 11 * s), label, F(SANS, 10 * s), fill=MUTED, alpha=0.5, anchor='ms')

def progress_rail(L, W, H, t, total, s, n, accent=CYAN):
    frac = min(max(t / max(total, 1e-6), 0), 1)
    y = H * CAP + 4 * s
    x0, x1 = 90 * s, W - 90 * s
    L.line([(x0, y), (x1, y)], fill=(40, 50, 80), width=2 * s, alpha=0.4)
    L.line([(x0, y), (x0 + (x1 - x0) * frac, y)], fill=accent, width=2.2 * s, alpha=0.8)
    for i in range(n):
        xf = x0 + (x1 - x0) * (i / max(n - 1, 1))
        on = frac >= i / max(n - 1, 1)
        L.dot((xf, y), 3 * s, fill=accent if on else (60, 70, 100), alpha=0.85 if on else 0.3)

# ---- plates (diverse: clean people, multi-pose mouse, eye/goggles, brain, micro) ----
def _cutout(path, thr=0.92):
    rgb, a = load_rgba(path)
    return matte_gray(rgb, a, thr)

PLATES = {}

# full-bleed editorial / micro / apparatus
for key, path in [
    ('brain', f'{GEN}/sf07k_brain.png'),
    ('microbes', f'{GEN}/sf03e_microbes.png'),
    ('chr2', f'{GEN}/sf09e_chr2.png'),
    ('neuron', f'{GEN}/sf06t_neuron.png'),
    ('orexin', f'{GEN}/sf10_orexin.png'),
    ('eye', f'{GEN}/sf11_eye.png'),
    ('eye_b', f'{GEN}/sf11b_eye.png'),
    ('eye_c', f'{GEN}/sf11c_eye.png'),
    ('eye_d', f'{GEN}/sf11d_eye.png'),
    ('goggles', f'{GEN}/sf11_goggles.png'),
    ('eye_inset', f'{GEN}/sf11_inset.png'),
    ('crick', f'{GEN}/r20_clean_crick.png'),
    ('deisseroth', f'{GEN}/r20_clean_deisseroth.png'),
    ('sf11board', '/workspace/e2work/v8/styleframes/SF11_eye_goggles.png'),
    ('sf21board', '/workspace/e2work/v8/styleframes/SF21_partial_vision.png'),
]:
    if os.path.isfile(path):
        PLATES[key] = load_full(path)

# cutout mouse — MULTI pose / cam (forbid whole-film one side plate)
for key, path, thr in [
    ('sleep_3d', f'{GEN}/sf10_sleep_3d.png', 0.93),
    ('awake_3d', f'{GEN}/sf10_awake_3d.png', 0.93),
    ('awake_3d_tq', f'{GEN}/sf10_awake_3d_tq.png', 0.93),
    ('sleep_3d_tq', f'{GEN}/sf10_sleep_3d_tq.png', 0.93),
    ('sleep_tq', f'{GEN}/sf10_sleep_threeq.png', 0.92),
    ('awake_tq', f'{GEN}/sf10_awake_threeq.png', 0.92),
    ('sleep', f'{GEN}/sf10_sleep.png', 0.92),
    ('awake', f'{GEN}/sf10_awake.png', 0.92),
    ('mref', f'{GEN}/mouse_ref.png', 0.90),
    ('still_awake_tq', f'{STILLS}/mouse_awake_threeq.png', 0.93),
    ('still_sleep_side', f'{STILLS}/mouse_sleep_side.png', 0.93),
    ('still_awake_side', f'{STILLS}/mouse_awake_side.png', 0.93),
    ('still_sleep_tq', f'{STILLS}/mouse_sleep_threeq.png', 0.93),
]:
    if os.path.isfile(path):
        rgb, a = _cutout(path, thr)
        PLATES[key] = (rgb, a, False)

print('PLATES loaded:', sorted(PLATES.keys()), flush=True)

def put_plate(out, mode, fx0, fy0, fx1, fy1, t_local, t_span, pan_x=0.015, pan_y=0.01, zoom_amp=0.02, fit=0.92):
    if mode not in PLATES:
        mode = 'brain' if 'brain' in PLATES else list(PLATES)[0]
    tw = int(fx1 - fx0 - 12)
    th = int(fy1 - fy0 - 12)
    rgb, a, full = PLATES[mode]
    pr, pa = fit_plate(rgb, a if not full else np.ones_like(a), tw, th, t_local, t_span,
                       pan_x=pan_x, pan_y=pan_y, zoom_amp=zoom_amp, fit=fit)
    if full:
        pa = np.ones_like(pa)
    else:
        pa = np.maximum(pa, 0.30)
    return place(out, pr, pa, int(fx0 + 6), int(fy0 + 6), opacity=0.98)


# =====================================================================
# SF01 — open title · 5s · clean brain (NO mouse side)
# =====================================================================
def sf01(t, W, H):
    s = W / 1280
    TOTAL = 5.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.4, 0.4)
    L = Layer(W, H)
    header(L, W, H, '用光，只动某一类神经元', 'EigenLens · 主观知识 · 第 2 期',
           min(tt, 1.0) + 0.5, s)
    fx0, fy0 = 40 * s, 78 * s
    fx1, fy1 = 700 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.45)
    chip(L, (720 * s, 100 * s, 1240 * s, 210 * s), '光遗传学',
         '基因定靶 · 光定时刻', ramp(tt, 0.8, 1.8), GOLD, s)
    chip(L, (720 * s, 230 * s, 1240 * s, H * CAP - 12 * s), '本期要讲的',
         '从一句牵强设想 → 一枚能用的开关', ramp(tt, 2.2, 3.2), CYAN, s)
    progress_rail(L, W, H, tt, TOTAL, s, 2, CYAN)
    footer_tick(L, W, H, tt, s, '开场')
    out = over(rgb, L.get())
    out = put_plate(out, 'awake_3d_tq', fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.012, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF02 — 1979 request · 4s · clean Crick 2.5D
# =====================================================================
def sf02(t, W, H):
    s = W / 1280
    TOTAL = 4.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.35, 0.38)
    L = Layer(W, H)
    header(L, W, H, '1979 · 一个很具体的要求', 'Francis Crick · 《科学美国人》',
           min(tt, 0.8) + 0.4, s)
    fx0, fy0 = 60 * s, 85 * s
    fx1, fy1 = 560 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.5)
    chip(L, (590 * s, 100 * s, 1220 * s, 210 * s), '只动某一类神经元',
         '其余的大体不动', 1.0, CYAN, s)
    chip(L, (590 * s, 230 * s, 1220 * s, H * CAP - 12 * s), '可开可关 · 要快',
         '毫秒尺度 · 不是分钟', ramp(tt, 1.2, 2.2), GOLD, s)
    progress_rail(L, W, H, tt, TOTAL, s, 2, GOLD)
    footer_tick(L, W, H, tt, s, 'A0 · 1979')
    out = over(rgb, L.get())
    out = put_plate(out, 'crick', fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.01, zoom_amp=0.015, fit=0.88)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF03 — microbe clues · 8s · LARGE clean micro (scale-correct)
# =====================================================================
def sf03(t, W, H):
    s = W / 1280
    TOTAL = 8.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.45, 0.4)
    L = Layer(W, H)
    header(L, W, H, '微生物那边，线索越来越多', '能被光推动的膜蛋白正在被找到',
           min(tt, 1.2) + 0.5, s)
    fx0, fy0 = 40 * s, 80 * s
    fx1, fy1 = 720 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=AMBER, width=2 * s, alpha=0.5)
    chip(L, (740 * s, 100 * s, 1240 * s, 200 * s), '光驱动膜蛋白',
         '微生物 · 膜上', ramp(tt, 0.5, 1.5), AMBER, s)
    chip(L, (740 * s, 220 * s, 1240 * s, 320 * s), '线索在积累',
         '还不是脑里那枚开关', ramp(tt, 2.5, 3.5), GOLD, s)
    chip(L, (740 * s, 340 * s, 1240 * s, H * CAP - 12 * s), '还差一跳',
         '从微生物膜 → 脑里的开关', ramp(tt, 4.5, 5.5), MUTED, s)
    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'A0 · 微生物')
    out = over(rgb, L.get())
    out = put_plate(out, 'microbes', fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.018, zoom_amp=0.03, fit=1.02)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF06 — switch diagram · 9s · awake 3D threeq (not side KB)
# =====================================================================
def sf06(t, W, H):
    s = W / 1280
    TOTAL = 9.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.3, 0.35)
    L = Layer(W, H)
    header(L, W, H, '缺的是一枚能用光拨动的开关', '从牵强设想 → 能用的方法',
           min(tt, 1.2) + 0.5, s)
    fx0, fy0 = 40 * s, 80 * s
    fx1, fy1 = 680 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)
    if tt < 4.5:
        chip(L, (700 * s, 100 * s, 1240 * s, 210 * s), '理想信号是光',
             '快 · 可定位 · 可开关', 1.0, CYAN, s)
        chip(L, (700 * s, 230 * s, 1240 * s, H * CAP - 12 * s), '中间缺一枚',
             '装进选定细胞 · 光一到就拨', ramp(tt, 1.5, 2.8), GOLD, s)
        mode = 'awake_3d_tq'
        t_loc, span = tt, 4.5
    else:
        p2 = tt - 4.5
        chip(L, (700 * s, 100 * s, 1240 * s, 210 * s), '开关 = 方法',
             '基因决定装谁 · 光决定何时', 1.0, GOLD, s)
        chip(L, (700 * s, 230 * s, 1240 * s, H * CAP - 12 * s), '后面各章都围着它',
             '分子 · 小鼠 · 临床边界', ramp(p2, 1.0, 2.2), CYAN, s)
        mode = 'still_awake_tq'
        t_loc, span = p2, 4.5
    progress_rail(L, W, H, tt, TOTAL, s, 2, CYAN)
    footer_tick(L, W, H, tt, s, 'A · 开关')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, t_loc, span, pan_x=0.014, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF07 — main title · 7s · clean brain full
# =====================================================================
def sf07(t, W, H):
    s = W / 1280
    TOTAL = 7.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.42, 0.38)
    L = Layer(W, H)
    header(L, W, H, '这一期就讲这枚开关', '片名：《光遗传学》',
           min(tt, 1.0) + 0.5, s)
    fx0, fy0 = 40 * s, 80 * s
    fx1, fy1 = 720 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.45)
    chip(L, (740 * s, 110 * s, 1240 * s, 230 * s), '光遗传学',
         'optogenetics', 1.0, GOLD, s)
    chip(L, (740 * s, 250 * s, 1240 * s, H * CAP - 12 * s), 'EigenLens · 第 2 期',
         '主观知识 · 边界内讲述', ramp(tt, 2.0, 3.5), MUTED, s)
    progress_rail(L, W, H, tt, TOTAL, s, 2, GOLD)
    footer_tick(L, W, H, tt, s, '片名')
    out = over(rgb, L.get())
    mode = 'still_awake_tq' if tt < 3.5 else 'sleep_3d'
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.012, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF08 — early attempts · 16s · 3 unique mouse poses (no one-side loop)
# =====================================================================
def sf08(t, W, H):
    s = W / 1280
    TOTAL = 16.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.35, 0.4)
    L = Layer(W, H)
    beats = [
        (0.0,  5.5, '更早的光控尝试', '有的要靠好几步信号接力',
         '达不到毫秒级', AMBER, 'sleep_3d'),
        (5.5, 11.0, '化学光开关', '通道上再外加一种化学基团',
         '步骤多 · 慢', CYAN, 'still_sleep_tq'),
        (11.0, 16.0, '都不够快', '缺一个：光打上去自己就开门',
         '不必再请一套帮手', GOLD, 'awake_3d'),
    ]
    cur = beats[0]
    for b in beats:
        if b[0] <= tt < b[1]:
            cur = b
            break
        if tt >= b[0]:
            cur = b
    t0, t1, title, sub, note, col, mode = cur
    local = tt - t0
    span = t1 - t0
    header(L, W, H, title, sub, min(local, 1.2) + 0.4, s)
    fx0, fy0 = 40 * s, 85 * s
    fx1, fy1 = 680 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=col, width=2 * s, alpha=0.5)
    chip(L, (700 * s, 110 * s, 1240 * s, 230 * s), note, '', 1.0, col, s)
    chip(L, (700 * s, 250 * s, 1240 * s, H * CAP - 12 * s),
         '早期路径都偏慢', '接力 / 化学基团 · 达不到毫秒',
         ramp(local, 1.5, 3.0), MUTED, s)
    for i, b in enumerate(beats):
        on = tt >= b[0]
        L.dot((180 * s + i * 220 * s, H * CAP + 4 * s), 4 * s,
              fill=b[5] if on else (60, 70, 100), alpha=0.9 if on else 0.35)
    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'A · 早期尝试')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, local, span, pan_x=0.016, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF09 — ChR2 channel · 8s · LARGE clean micro ChR2
# =====================================================================
def sf09(t, W, H):
    s = W / 1280
    TOTAL = 8.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.38, 0.42)
    L = Layer(W, H)
    header(L, W, H, '缺的是一个蛋白', '光打上去，它自己就开门',
           min(tt, 1.2) + 0.5, s)
    fx0, fy0 = 40 * s, 80 * s
    fx1, fy1 = 700 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)
    chip(L, (720 * s, 100 * s, 1240 * s, 200 * s), 'ChR2 类通道',
         '光门控离子通道', ramp(tt, 0.5, 1.5), CYAN, s)
    chip(L, (720 * s, 220 * s, 1240 * s, 320 * s), '不必再请帮手',
         '蛋白自己完成开门', ramp(tt, 2.5, 3.5), GOLD, s)
    chip(L, (720 * s, 340 * s, 1240 * s, H * CAP - 12 * s), '一束蓝光',
         '通道打开 · 离子流过', ramp(tt, 4.5, 5.5), MUTED, s)
    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'B · ChR2')
    out = over(rgb, L.get())
    out = put_plate(out, 'chr2', fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.015, zoom_amp=0.028, fit=1.0)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF11 — eye / goggles · 24s · apparatus dual-layer (SF21-class)
# =====================================================================
def sf11(t, W, H):
    s = W / 1280
    TOTAL = 24.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.48, 0.4)
    L = Layer(W, H)
    beats = [
        (0.0,  8.0,  '病毒携带 ChrimsonR', '主要转导视网膜神经节细胞',
         '感光细胞已稀 · 神经节还可留', AMBER, 'eye'),
        (8.0,  16.0, '护目镜把光脉冲打上去', '送到视网膜上的目标细胞旁',
         '装置绑定 · 不是裸眼奇迹', CYAN, 'eye_b'),
        (16.0, 24.0, '通路或可被点着', '部分功能 · 仍绑装置',
         '临床边界后面再写清', GOLD, 'eye_c'),
    ]
    cur = beats[0]
    for b in beats:
        if b[0] <= tt < b[1]:
            cur = b
            break
        if tt >= b[0]:
            cur = b
    t0, t1, title, sub, note, col, mode = cur
    local = tt - t0
    span = t1 - t0
    header(L, W, H, title, sub, min(local, 1.2) + 0.5, s)
    fx0, fy0 = 40 * s, 85 * s
    fx1, fy1 = 700 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=col, width=2 * s, alpha=0.55)
    chip(L, (720 * s, 110 * s, 1240 * s, 230 * s), note, '', 1.0, col, s)
    chip(L, (720 * s, 250 * s, 1240 * s, H * CAP - 12 * s),
         '光脉冲打到视网膜', '护目镜递送 · 不是裸眼',
         ramp(local, 1.5, 3.0), MUTED, s)
    for i, b in enumerate(beats):
        on = tt >= b[0]
        L.dot((180 * s + i * 220 * s, H * CAP + 4 * s), 4 * s,
              fill=b[5] if on else (60, 70, 100), alpha=0.9 if on else 0.35)
    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'C · 眼与护目镜')
    out = over(rgb, L.get())
    if mode not in PLATES:
        mode = 'eye'
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, local, span, pan_x=0.012, zoom_amp=0.018, fit=1.0)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF12 — neuron select · 10s · sleep threeq + neuron editorial
# =====================================================================
def sf12(t, W, H):
    s = W / 1280
    TOTAL = 10.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.5, 0.42)
    L = Layer(W, H)
    header(L, W, H, '他要的方法很具体', '只动某一类 · 可开可关 · 要快',
           min(tt, 1.2) + 0.5, s)
    fx0, fy0 = 40 * s, 80 * s
    fx1, fy1 = 680 * s, H * CAP - 12 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)
    if tt < 5.0:
        chip(L, (700 * s, 100 * s, 1240 * s, 200 * s), '中间一类被圈出',
             '两侧保持灰色 · 示意', 1.0, CYAN, s)
        chip(L, (700 * s, 220 * s, 1240 * s, H * CAP - 12 * s), '旁边的细胞大体不动',
             '而且要快（毫秒）', ramp(tt, 1.5, 2.8), GOLD, s)
        mode = 'sleep_tq'
        t_loc, span = tt, 5.0
    else:
        p2 = tt - 5.0
        chip(L, (700 * s, 100 * s, 1240 * s, 200 * s), '遗传靶向的意思',
             '基因决定装谁', 1.0, GOLD, s)
        chip(L, (700 * s, 220 * s, 1240 * s, H * CAP - 12 * s), '光决定何时拨',
             '选定细胞 · 可开可关', ramp(p2, 1.0, 2.2), CYAN, s)
        mode = 'awake_3d'
        t_loc, span = p2, 5.0
    progress_rail(L, W, H, tt, TOTAL, s, 2, CYAN)
    footer_tick(L, W, H, tt, s, 'A0 · 选择性')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, t_loc, span,
                    pan_x=0.014, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


SCENES = {
    'SF01_open_title': (sf01, 5.0),
    'SF02_1979_request': (sf02, 4.0),
    'SF03_microbe_clues': (sf03, 8.0),
    'SF06_switch_diagram': (sf06, 9.0),
    'SF07_main_title': (sf07, 7.0),
    'SF08_early_attempts': (sf08, 16.0),
    'SF09_chr2_channel': (sf09, 8.0),
    'SF11_eye_goggles': (sf11, 24.0),
    'SF12_neuron_select': (sf12, 10.0),
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
