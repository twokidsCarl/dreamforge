#!/usr/bin/env python3
"""Macro photo boost TAIL: photo-forward rebuild of SF17/SF20/SF22/SF23.
Film windows ≈22.7 / 16.6 / 95.7 / 103.6s — render unique near-window lengths.
Uses locked glb stills + SF10 plate + mouse_ref. No deferred on-screen copy. $0.
Caption-safe above ~0.80H.
"""
from __future__ import annotations
import math, sys, time as _time
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
CAP = 0.80

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

def fit_plate(rgb, a, tw, th, t, total, pan_x=0.02, pan_y=0.015, zoom_amp=0.02, pad_rgb=(0.05, 0.07, 0.12)):
    h, w = rgb.shape[:2]
    frac = min(max(t / max(total, 1e-6), 0), 1)
    zoom = 1.0 + zoom_amp * frac
    cw, ch = int(tw * (1.0 + zoom_amp + 0.04)), int(th * (1.0 + zoom_amp + 0.04))
    scale = min(cw / w, ch / h) * 0.92
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
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

# SF21 / SF11 stills as secondary plates when present (eye/goggles apparatus)
def _try_full(path):
    try:
        rgb, a = load_rgba(path)
        return rgb, np.ones((rgb.shape[0], rgb.shape[1], 1), np.float32), True
    except Exception:
        return None

_sf21 = _try_full('/workspace/e2work/v8/styleframes/SF21_partial_vision.png')
_sf11 = _try_full('/workspace/e2work/v8/styleframes/SF11_eye_goggles.png')
_sf18 = _try_full('/workspace/e2work/v8/styleframes/SF18_invivo_dual.png')

PLATES = {
    'sf10': (_sf10_rgb, _sf10_a, True),
    'sleep': (_sleep_rgb, _sleep_a, False),
    'awake': (_awake_rgb, _awake_a, False),
    'sleep_tq': (_sleep_tq_rgb, _sleep_tq_a, False),
    'awake_tq': (_awake_tq_rgb, _awake_tq_a, False),
    'mref': (_mref_rgb, _mref_a, False),
}
if _sf21: PLATES['sf21'] = _sf21
if _sf11: PLATES['sf11'] = _sf11
if _sf18: PLATES['sf18'] = _sf18

def put_plate(out, mode, fx0, fy0, fx1, fy1, t_local, t_span, pan_x=0.015, pan_y=0.01, zoom_amp=0.02):
    tw = int(fx1 - fx0 - 12)
    th = int(fy1 - fy0 - 12)
    rgb, a, full = PLATES[mode]
    pr, pa = fit_plate(rgb, a if not full else np.ones_like(a), tw, th, t_local, t_span,
                       pan_x=pan_x, pan_y=pan_y, zoom_amp=zoom_amp)
    if full:
        pa = np.ones_like(pa)
    else:
        pa = np.maximum(pa, 0.30)
    return place(out, pr, pa, int(fx0 + 6), int(fy0 + 6), opacity=0.98)


# =====================================================================
# SF17 — credit / word · 22s · LARGE mouse + dual credit panels
# =====================================================================
def sf17(t, W, H):
    s = W / 1280
    TOTAL = 22.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.45, 0.35)
    L = Layer(W, H)

    fx0, fy0 = 40 * s, 78 * s
    fx1, fy1 = 620 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.5)

    if tt < 12.0:
        p = tt
        header(L, W, H, '署名和授奖名单，不是同一份', '2005 论文 · 2026 新闻稿',
               min(p, 2.0) + 1.0, s)
        chip(L, (640 * s, 95 * s, 1240 * s, 200 * s), '论文署名',
             'Boyden 第一作者 · Deisseroth 通讯',
             ramp(p, 1.5, 3.0), CYAN, s)
        chip(L, (640 * s, 220 * s, 1240 * s, 325 * s), '2026 授奖三人',
             'Deisseroth · Hegemann · Nagel',
             ramp(p, 4.0, 5.5), GOLD, s)
        chip(L, (640 * s, 345 * s, 1240 * s, H * CAP - 14 * s),
             '第四行空着', '授奖名单 ≠ 论文署名',
             ramp(p, 7.0, 9.0), AMBER, s)
        mode = 'awake_tq'
        t_loc, t_span = p, 12.0
    else:
        p2 = tt - 12.0
        header(L, W, H, '2006 · optogenetics', '光学 + 遗传靶向：基因决定装谁，光决定何时拨',
               min(p2, 1.5) + 0.5, s)
        chip(L, (640 * s, 110 * s, 1240 * s, 240 * s), 'optogenetics',
             '2006 · 《神经科学杂志》示意',
             1.0, GOLD, s)
        chip(L, (640 * s, 260 * s, 1240 * s, H * CAP - 14 * s),
             '一词定场', '基因定靶 · 光定时刻',
             ramp(p2, 2.0, 4.0), CYAN, s)
        mode = 'sf10'
        t_loc, t_span = p2, 10.0

    progress_rail(L, W, H, tt, TOTAL, s, 2, GOLD)
    footer_tick(L, W, H, tt, s, 'B · 署名 / 一词 · 写实鼠板')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, t_loc, t_span)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF20 — retina intro · 16s · photo mouse / apparatus + slim layers
# =====================================================================
def sf20(t, W, H):
    s = W / 1280
    TOTAL = 16.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.5, 0.42)
    L = Layer(W, H)
    header(L, W, H, '眼睛走另一条路', '感光细胞死去 · 神经节细胞还可留着',
           min(tt, 1.5) + 0.5, s)

    fx0, fy0 = 40 * s, 85 * s
    fx1, fy1 = 680 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=AMBER, width=2 * s, alpha=0.5)

    chip(L, (700 * s, 95 * s, 1240 * s, 185 * s), '感光细胞层', '逐渐变稀',
         ramp(tt, 0.5, 1.5), MUTED, s)
    chip(L, (700 * s, 200 * s, 1240 * s, 290 * s), '中间层', '双极等',
         ramp(tt, 2.5, 3.5), CYAN, s)
    chip(L, (700 * s, 305 * s, 1240 * s, H * CAP - 14 * s),
         '神经节细胞层 · 可转导', '若幸存细胞自己感光 → 通路或可被点着',
         ramp(tt, 5.0, 7.0), GOLD, s)

    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'C_07 · 视网膜 · 写实板')
    out = over(rgb, L.get())
    # prefer apparatus still if available, else mouse
    mode = 'sf21' if 'sf21' in PLATES else ('sf11' if 'sf11' in PLATES else 'mref')
    if tt > 8.0:
        mode = 'awake' if 'awake' in PLATES else mode
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, tt, TOTAL, pan_x=0.012, zoom_amp=0.018)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF22 — regulatory · 94s · 5 unique beats + LARGE photo
# =====================================================================
def sf22(t, W, H):
    s = W / 1280
    TOTAL = 94.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.42, 0.35)
    L = Layer(W, H)

    beats = [
        (0.0,  18.0, '2026-09-09', 'BLA 已受理 · MCO-010 / MOGENRY',
         '公告写「如果获批」→ 当时尚未获批', GOLD, 'sf10'),
        (18.0, 36.0, '第 52 / 76 周', '视力主要终点与关键次要终点',
         '申请方公告 · 不是已生效许可', CYAN, 'awake_tq'),
        (36.0, 54.0, '2026-10-08', '另一款 · 1/2 期 · 《新英格兰医学杂志》',
         '安全性为主 · 非确证疗效设计', AMBER, 'mref'),
        (54.0, 74.0, '数字连同分母', '光敏感 6/10 · 行为测试 4/8（部分任务）',
         '戴着护目镜 · 不写成全体患者', CYAN, 'sf21' if 'sf21' in PLATES else 'awake'),
        (74.0, 94.0, '脚注', '任何司法辖区都没有上市许可',
         'GS030 · 仍是申请/探索', AMBER, 'sleep_tq'),
    ]
    header(L, W, H, '临床边界 · 以公告与论文为准', '受理 ≠ 获批 · 探索 ≠ 确证',
           min(tt, 2.0) + 1.0, s)

    cur = beats[0]
    for b in beats:
        if b[0] <= tt < b[1]:
            cur = b
            break
        if tt >= b[0]:
            cur = b
    t0, t1, date, title, sub, col, mode = cur
    local = tt - t0
    span = t1 - t0

    fx0, fy0 = 40 * s, 95 * s
    fx1, fy1 = 700 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=col, width=2 * s, alpha=0.55)

    chip(L, (720 * s, 105 * s, 1240 * s, 195 * s), date, '', 1.0, col, s)
    chip(L, (720 * s, 210 * s, 1240 * s, 320 * s), title, sub, 1.0, GOLD, s)
    chip(L, (720 * s, 335 * s, 1240 * s, H * CAP - 14 * s),
         '写实装置 / 鼠 · 临床仍在边界内', '比例非定量 · 措辞以公告为准',
         ramp(local, 3.0, 6.0), MUTED, s)

    # beat dots
    for i, b in enumerate(beats):
        on = tt >= b[0]
        L.dot((160 * s + i * 200 * s, H * CAP + 4 * s), 4 * s,
              fill=b[5] if on else (60, 70, 100), alpha=0.9 if on else 0.35)

    progress_rail(L, W, H, tt, TOTAL, s, 5, GOLD)
    footer_tick(L, W, H, tt, s, 'C · 监管与数字 · 写实板')
    out = over(rgb, L.get())
    if mode not in PLATES:
        mode = 'sf10'
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, local, span, pan_x=0.018, zoom_amp=0.022)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF23 — limits + close · 100s · 3 acts + LARGE photo
# =====================================================================
def sf23(t, W, H):
    s = W / 1280
    TOTAL = 100.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.38, 0.4)
    L = Layer(W, H)

    fx0, fy0 = 40 * s, 95 * s
    fx1, fy1 = 680 * s, H * CAP - 14 * s

    if tt < 38.0:
        p = tt
        header(L, W, H, '边界停在已发表的事实', '脱敏 · 光必须送到细胞旁 · 部分且绑装置',
               min(p, 2.0) + 1.0, s)
        L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)
        items = [
            (2.0,  '限制 1', '持续光照 → ChR2 脱敏', '不能当成永不疲劳的门'),
            (12.0, '限制 2', '光得送到细胞旁边', '脑：光纤 · 眼：护目镜'),
            (22.0, '限制 3', '人体视觉：部分功能', '一条未获批 · 一条无上市许可'),
        ]
        for i, (t0, k, a, b) in enumerate(items):
            y = 105 * s + i * 95 * s
            aa = ramp(p, t0, t0 + 1.5)
            if p < t0: continue
            alpha = max(aa, 0.85)
            chip(L, (700 * s, y, 1240 * s, y + 85 * s), f'{k}  {a}', b, alpha, GOLD if i < 2 else AMBER, s)
        mode = 'sleep' if p < 20 else 'awake_tq'
        t_loc, t_span = p, 38.0
        out_mode = mode
    elif tt < 68.0:
        p2 = tt - 38.0
        header(L, W, H, '做得到 / 做不到', '实验边界 · 不夸大',
               min(p2, 2.0) + 1.0, s)
        L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.5)
        chip(L, (700 * s, 105 * s, 1240 * s, 220 * s), '做得到',
             '选定细胞 · 实验里开或关 · 小鼠行为可驱动',
             1.0, CYAN, s)
        chip(L, (700 * s, 240 * s, 1240 * s, 355 * s), '做不到',
             '小鼠恐惧 ≠ 某人的人生 · 部分视觉 ≠ 失明结束',
             ramp(p2, 4.0, 7.0), AMBER, s)
        chip(L, (700 * s, 370 * s, 1240 * s, H * CAP - 14 * s),
             '受理 ≠ 上市许可', '边界写清楚，才站得住',
             ramp(p2, 12.0, 16.0), MUTED, s)
        out_mode = 'mref' if p2 < 15 else 'sf10'
        t_loc, t_span = p2, 30.0
    else:
        p3 = tt - 68.0
        header(L, W, H, '牵强的是当年的工程', '今天：实验方法 · 仍在审查的临床尝试',
               min(p3, 2.0) + 1.0, s)
        L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.45)
        chip(L, (700 * s, 130 * s, 1240 * s, 260 * s), '光遗传学',
             '这一期在这里结束',
             1.0, GOLD, s)
        chip(L, (700 * s, 280 * s, 1240 * s, H * CAP - 14 * s),
             'EigenLens 主观知识 · 第 2 期',
             '边界内收束 · 写实鼠板',
             ramp(p3, 6.0, 10.0), MUTED, s)
        out_mode = 'awake'
        t_loc, t_span = p3, 32.0

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'D · 边界与收束 · 写实鼠板')
    out = over(rgb, L.get())
    out = put_plate(out, out_mode, fx0, fy0, fx1, fy1, t_loc, t_span, pan_x=0.016, zoom_amp=0.02)
    return grade(out, seed=int(tt * 24) % 100000)


SCENES = {
    'SF17_credit_word': (sf17, 22.0),
    'SF20_retina_intro': (sf20, 16.0),
    'SF22_regulatory': (sf22, 94.0),
    'SF23_limits_close': (sf23, 100.0),
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
