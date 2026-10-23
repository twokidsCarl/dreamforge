#!/usr/bin/env python3
"""Macro photo boost MORE: photo-forward rebuild of longest illustration boards.
SF13 (52s) / SF14 (6s) / SF15 (62s) / SF16 (120s).
Uses locked glb stills + SF10 plate. No deferred on-screen copy. $0 / no Blender.
Keeps film durations. Caption-safe above ~0.80H.
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

# ---- plates (locked glb stills preferred) ----
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

PLATES = {
    'sf10': (_sf10_rgb, _sf10_a, True),
    'sleep': (_sleep_rgb, _sleep_a, False),
    'awake': (_awake_rgb, _awake_a, False),
    'sleep_tq': (_sleep_tq_rgb, _sleep_tq_a, False),
    'awake_tq': (_awake_tq_rgb, _awake_tq_a, False),
    'mref': (_mref_rgb, _mref_a, False),
}

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
# SF13 — spike / causality / ms · 52s · LARGE mouse (sleep↔awake)
# =====================================================================
def sf13(t, W, H):
    s = W / 1280
    TOTAL = 52.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.25, 0.35)
    L = Layer(W, H)

    fx0, fy0 = 40 * s, 78 * s
    fx1, fy1 = 700 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=CYAN, width=2 * s, alpha=0.5)

    if tt < 17.0:
        p = tt
        header(L, W, H, '神经元靠膜两侧的电压说话', '一次锋电位：离子穿过 · 电压翻过去再恢复',
               min(p, 2.0) + 1.0, s)
        chip(L, (720 * s, 95 * s, 1240 * s, 190 * s), '锋电位', '极短时间里电压忽然翻过去',
             ramp(p, 2.0, 4.0), CYAN, s)
        chip(L, (720 * s, 210 * s, 1240 * s, 305 * s), '膜内外电荷差', '离子穿过 · 再恢复',
             ramp(p, 8.0, 10.0), GOLD, s)
        chip(L, (720 * s, 320 * s, 1240 * s, H * CAP - 14 * s), '活体里也能读到', '动物醒来 / 害怕之前先有电压翻',
             ramp(p, 12.0, 14.0), CYAN, s)
        mode = 'sf10'
        t_loc, t_span = p, 17.0
    elif tt < 34.0:
        p2 = tt - 17.0
        header(L, W, H, '相关还不够', '因果要多问一句：是它造成的，还是只是一起亮？',
               min(p2, 2.0) + 1.0, s)
        chip(L, (720 * s, 95 * s, 1240 * s, 185 * s), '同时亮着', '细胞亮 · 动物醒了 / 怕了',
             1.0, CREAM, s)
        chip(L, (720 * s, 200 * s, 1240 * s, 290 * s), '是它造成的吗？', '还是跟着行为一起亮',
             ramp(p2, 3.0, 5.0), GOLD, s)
        chip(L, (720 * s, 305 * s, 1240 * s, H * CAP - 14 * s),
             '记录与损毁证明不了因果', '要能只推动 / 按住那一类细胞',
             ramp(p2, 8.0, 11.0), AMBER, s)
        mode = 'awake_tq'
        t_loc, t_span = p2, 17.0
    else:
        p3 = tt - 34.0
        header(L, W, H, '时间尺度要对', '毫秒，不是分钟', min(p3, 2.0) + 1.0, s)
        chip(L, (720 * s, 95 * s, 980 * s, 220 * s), '毫秒', '对齐锋电位',
             1.0, CYAN, s)
        chip(L, (1000 * s, 95 * s, 1240 * s, 220 * s), '分钟', '太慢',
             1.0, MUTED, s)
        chip(L, (720 * s, 240 * s, 1240 * s, H * CAP - 14 * s),
             '只动一类 · 可开可关 · 毫秒', '要回答因果，缺的是这枚开关',
             ramp(p3, 6.0, 9.0), GOLD, s)
        mode = 'sleep'
        t_loc, t_span = p3, 18.0

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'A · 锋电位 / 因果 / 毫秒 · 写实鼠板')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, t_loc, t_span)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF14 — orexin Q · 6s · sleep→awake photo
# =====================================================================
def sf14(t, W, H):
    s = W / 1280
    TOTAL = 6.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.35, 0.4)
    L = Layer(W, H)
    header(L, W, H, '食欲素神经元 · 睡与醒', '一类细胞 · 能不能只推动它？', min(tt, 0.8) + 0.5, s)
    fx0, fy0 = 60 * s, 85 * s
    fx1, fy1 = 820 * s, H * CAP - 16 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=GOLD, width=2 * s, alpha=0.5)
    chip(L, (840 * s, 110 * s, 1240 * s, 230 * s), '睡', '食欲素低',
         ramp(tt, 0.3, 1.0), CYAN, s)
    chip(L, (840 * s, 250 * s, 1240 * s, 370 * s), '醒', '食欲素高',
         ramp(tt, 2.5, 3.5), AMBER, s)
    progress_rail(L, W, H, tt, TOTAL, s, 2, GOLD)
    footer_tick(L, W, H, tt, s, 'A · 食欲素 · 睡↔醒写实板')
    out = over(rgb, L.get())
    # crossfade sleep → awake across 6s
    tw = int(fx1 - fx0 - 12); th = int(fy1 - fy0 - 12)
    prS, paS = fit_plate(_sleep_rgb, _sleep_a, tw, th, tt, TOTAL, pan_x=0.01, zoom_amp=0.015)
    prA, paA = fit_plate(_awake_rgb, _awake_a, tw, th, tt, TOTAL, pan_x=-0.01, zoom_amp=0.015)
    wA = float(np.clip(tt / 4.5, 0, 1))
    blend = prS * (1 - wA) + prA * wA
    ba = np.maximum(np.maximum(paS, 0.3) * (1 - wA) + np.maximum(paA, 0.3) * wA, 0.3)
    out = place(out, blend, ba, int(fx0 + 6), int(fy0 + 6), opacity=0.98)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF15 — BR pump / channel · 62s · photo mouse + slim science chips
# =====================================================================
def sf15(t, W, H):
    s = W / 1280
    TOTAL = 62.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, (160, 80, 180), 0.4, 0.4)
    L = Layer(W, H)

    fx0, fy0 = 40 * s, 78 * s
    fx1, fy1 = 700 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=(180, 100, 200), width=2 * s, alpha=0.5)

    if tt < 30.0:
        p = tt
        header(L, W, H, '开关先在微生物膜上', '1971 紫膜 · 1973 细菌视紫红质 · 光驱动质子泵',
               min(p, 2.0) + 1.0, s)
        chip(L, (720 * s, 95 * s, 1240 * s, 180 * s), '紫膜片段', '蛋白只有这一种',
             ramp(p, 2.0, 4.0), GOLD, s)
        chip(L, (720 * s, 195 * s, 1240 * s, 280 * s), '视黄醛', '吸收光 · 质子泵出',
             ramp(p, 10.0, 12.0), AMBER, s)
        chip(L, (720 * s, 295 * s, 1240 * s, H * CAP - 14 * s),
             '细菌视紫红质 = 光驱动质子泵', '定向搬运 · 不是通道',
             ramp(p, 18.0, 20.0), CYAN, s)
        mode = 'mref'
        t_loc, t_span = p, 30.0
    else:
        p2 = tt - 30.0
        header(L, W, H, '泵 ≠ 通道', '神经元在意的是电压 · 活体也一样',
               min(p2, 2.0) + 1.0, s)
        chip(L, (720 * s, 95 * s, 980 * s, 220 * s), '泵', '逆着梯度推一趟',
             1.0, AMBER, s)
        chip(L, (1000 * s, 95 * s, 1240 * s, 220 * s), '通道', '孔打开 · 离子顺梯度涌',
             1.0, CYAN, s)
        chip(L, (720 * s, 240 * s, 1240 * s, H * CAP - 14 * s),
             '离子带电荷 → 膜电压变', '泵和通道不要混成一个分子',
             ramp(p2, 8.0, 12.0), GOLD, s)
        mode = 'awake'
        t_loc, t_span = p2, 32.0

    progress_rail(L, W, H, tt, TOTAL, s, 2, (180, 100, 200))
    footer_tick(L, W, H, tt, s, 'B · 紫膜 / 泵与通道 · 写实鼠板')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, t_loc, t_span, pan_x=0.02, zoom_amp=0.025)
    return grade(out, seed=int(tt * 24) % 100000)


# =====================================================================
# SF16 — ChR path · 120s · LARGE photo + timeline chips (6 beats)
# =====================================================================
def sf16(t, W, H):
    s = W / 1280
    TOTAL = 120.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.5, 0.38)
    L = Layer(W, H)

    steps = [
        (0.0,   20.0, '衣藻朝光游', '眼点 · 谁在感光？', GOLD, 'sleep_tq'),
        (20.0,  40.0, '2002 · 通道视紫红质一', '卵母细胞 · 光 → 质子电流', AMBER, 'mref'),
        (40.0,  60.0, '关键：光与孔在同一分子', '不必多步接力 · 一个基因', CYAN, 'sf10'),
        (60.0,  80.0, '2003 · 通道视紫红质二', '蓝光开阳离子 · 哺乳细胞可用', CYAN, 'awake_tq'),
        (80.0, 100.0, '持续光照会脱敏', '高峰→平台 · 要用短脉冲', AMBER, 'sleep'),
        (100.0, 120.0, '2005 · 培养神经元', '蓝光脉冲对齐锋电位', GOLD, 'awake'),
    ]
    header(L, W, H, '从衣藻到毫秒级开关', 'ChR1 → 一体分子 → ChR2 → 锋电位 · 活体写实',
           min(tt, 2.0) + 1.0, s)

    # timeline rail
    L.line([(70 * s, 88 * s), (1210 * s, 88 * s)], fill=(50, 60, 90), width=2 * s, alpha=0.7)
    cur = steps[0]
    for i, (t0, t1, title, sub, col, mode) in enumerate(steps):
        x = 90 * s + i * 185 * s
        a = ramp(tt, t0, t0 + 0.6)
        L.dot((x, 88 * s), 6 * s, fill=col, alpha=max(a, 0.2))
        if a > 0.15:
            L.text((x, 105 * s), title.split('·')[0].strip()[:7], F(SANS, 10 * s),
                   fill=MUTED, alpha=0.55 * a, anchor='ms')
        if t0 <= tt < t1:
            cur = (t0, t1, title, sub, col, mode)

    t0, t1, title, sub, col, mode = cur
    local = tt - t0
    span = t1 - t0

    fx0, fy0 = 40 * s, 118 * s
    fx1, fy1 = 700 * s, H * CAP - 14 * s
    L.rrect((fx0, fy0, fx1, fy1), 10 * s, outline=col, width=2 * s, alpha=0.55)

    chip(L, (720 * s, 125 * s, 1240 * s, 230 * s), title, sub, 1.0, col, s)
    chip(L, (720 * s, 250 * s, 1240 * s, 345 * s),
         '写实鼠 · 研究终点在活体', '分子史 → 能开能关的动物行为',
         ramp(local, 2.0, 5.0), GOLD, s)
    chip(L, (720 * s, 360 * s, 1240 * s, H * CAP - 14 * s),
         '结构示意已让位照片', '比例非定量 · 科学措辞不变',
         ramp(local, 8.0, 12.0), MUTED, s)

    progress_rail(L, W, H, tt, TOTAL, s, 6, CYAN)
    footer_tick(L, W, H, tt, s, 'B · ChR 路径 · 写实鼠多拍')
    out = over(rgb, L.get())
    out = put_plate(out, mode, fx0, fy0, fx1, fy1, local, span, pan_x=0.018, zoom_amp=0.022)
    return grade(out, seed=int(tt * 24) % 100000)


SCENES = {
    'SF13_spike_causality': (sf13, 52.0),
    'SF14_orexin_q': (sf14, 6.0),
    'SF15_br_pump_channel': (sf15, 62.0),
    'SF16_chr_path': (sf16, 120.0),
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
