#!/usr/bin/env python3
"""Replace worst schematic macro placeholders with photo/2.5D insets.
SF18 invivo: photo mouse + fiber schematic (was empty ring)
SF19 engram: photo mouse in env A/B panels (cage deferred → photo plate)
SF21 partial vision: keep no-face; add SF11 eye still as apparatus inset
Also lengthen to reduce loop count. $0 / no Blender.
"""
from __future__ import annotations
import math, sys, os
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
MOUSE = '/workspace/e2work/v8/gen/mouse_ref.png'
SF10_STILL = '/workspace/e2work/v8/styleframes/SF10_mouse_tripo.png'
SF11_STILL = '/workspace/e2work/v8/styleframes/SF11_eye_goggles.png'

def load_rgb(path, tw, th):
    im = Image.open(path).convert('RGBA')
    im = im.resize((tw, th), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr[..., :3], arr[..., 3:4]

def matte_gray_bg(rgb, alpha, thr=0.92):
    """Knock out near-white/gray studio bg of mouse_ref for soft plate."""
    # mouse_ref is on light gray — treat bright near-gray as bg
    lum = rgb.mean(axis=2, keepdims=True)
    sat = rgb.max(axis=2, keepdims=True) - rgb.min(axis=2, keepdims=True)
    bg = (lum > thr) & (sat < 0.08)
    a = alpha.copy()
    a[bg] = 0.0
    # soft edge
    return rgb, a

def place(dst_rgb, src_rgb, src_a, x, y, opacity=1.0):
    h, w = src_rgb.shape[:2]
    H, W = dst_rgb.shape[:2]
    x0, y0 = int(x), int(y)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
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
    rgb = np.zeros((H, W, 3), np.float32) + np.array(INK) / 255
    rgb = rgb + radial(W, H, W * ax, H * ay, W * 0.35, accent, 0.22 + 0.04 * math.sin(t * 1.2))
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
    a = 0.55 + 0.15 * math.sin(t * 2.5)
    L.line([(80 * s, H - 36 * s), (W - 80 * s, H - 36 * s)], fill=(50, 60, 90), width=1 * s, alpha=a)
    if label:
        L.text((W / 2, H - 22 * s), label, F(SANS, 12 * s), fill=MUTED, alpha=0.7, anchor='ms')

# Load plates once
_mouse_rgb, _mouse_a = load_rgb(MOUSE, 420, 300)
_mouse_rgb, _mouse_a = matte_gray_bg(_mouse_rgb, _mouse_a, thr=0.88)
# Prefer SF10 cage photo if exists (already locked ground)
_sf10_rgb, _sf10_a = load_rgb(SF10_STILL, 480, 270)
_sf10_a = np.ones_like(_sf10_a)  # full plate in frame
_sf11_rgb, _sf11_a = load_rgb(SF11_STILL, 400, 225)
_sf11_a = np.ones_like(_sf11_a)

def sf18(t, W, H):
    """Invivo dual — photo mouse plate + dual-color diagram. Longer continuous phases."""
    s = W / 1280
    rgb = bg(W, H, t, CYAN, 0.35, 0.4)
    L = Layer(W, H)
    # 36s cycle: 0-12 fiber, 12-24 NpHR, 24-36 prizes — but keep content dense from t=0
    # Use slow phase so first frame already has content (offset into cycle)
    phase = (t + 1.2) % 36.0
    # Frame for mouse plate (outline only — photo placed after overlay)
    L.rrect((60 * s, 110 * s, 560 * s, 400 * s), 10 * s, outline=CYAN, width=2 * s, alpha=0.55)
    # thin cyan fiber accent marker
    L.line([(310 * s, 115 * s), (310 * s, 155 * s)], fill=CYAN, width=2.5 * s, alpha=0.7 + 0.3 * math.sin(t * 5))

    if phase < 12.0:
        p = phase
        header(L, W, H, '2007 · 光纤进活体脑', '运动皮层 · 只驱动表达 ChR2 的兴奋性神经元', min(p, 2.0) + 1.0, s)
        chip(L, (600 * s, 140 * s, 1200 * s, 240 * s), '照片鼠 · 锁地 2.5D', '写实毛发/笼箱仍 deferred · 本板用 SF10 照片', 1.0, CYAN, s)
        chip(L, (600 * s, 260 * s, 1200 * s, 360 * s), '不另加视黄醛', '光也足够做出行为', ramp(p, 2.0, 3.0) + 0.5, GOLD, s)
        chip(L, (600 * s, 380 * s, 1200 * s, 470 * s), '2005 培养皿 → 2007 活体', '大约两年', ramp(p, 4.0, 5.0) + 0.5, CYAN, s)
    elif phase < 24.0:
        p2 = phase - 12.0
        header(L, W, H, '开还不够 · NpHR', '黄光泵入 Cl⁻ · 电压更负 · 锋电位被按住', min(p2, 2.0) + 1.0, s)
        L.rrect((600 * s, 140 * s, 880 * s, 360 * s), 10 * s, fill=(14, 20, 40), alpha=0.85)
        L.rrect((900 * s, 140 * s, 1180 * s, 360 * s), 10 * s, fill=(14, 20, 40), alpha=0.85)
        L.text((740 * s, 200 * s), '蓝光 · 开', F(SANS_B, 24 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.text((740 * s, 260 * s), 'ChR2', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((1040 * s, 200 * s), '黄光 · 关', F(SANS_B, 24 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((1040 * s, 260 * s), 'NpHR', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((890 * s, 420 * s), '同一套细胞 · 光谱分开', F(SANS, 16 * s), fill=MUTED, alpha=0.85, anchor='ms')
    else:
        p3 = phase - 24.0
        header(L, W, H, '荣誉不止一份', '2013 Brain Prize 六人 ≠ 2026 诺奖三人', min(p3, 2.0) + 1.0, s)
        six = ['Bamberg', 'Boyden', 'Deisseroth', 'Hegemann', 'Miesenböck', 'Nagel']
        for i, nm in enumerate(six):
            x = 600 * s + (i % 3) * 190 * s
            y = 140 * s + (i // 3) * 90 * s
            L.rrect((x, y, x + 170 * s, y + 70 * s), 6 * s, fill=(14, 20, 40), alpha=0.8)
            L.text((x + 85 * s, y + 42 * s), nm, F(SANS, 14 * s), fill=CREAM, alpha=0.95, anchor='ms')
        L.text((890 * s, 360 * s), '六人奖  ≠  三人诺奖', F(SANS_B, 20 * s), fill=GOLD, alpha=0.9, anchor='ms')
    footer_tick(L, W, H, t, s, 'B · 活体 / 双色 · 照片鼠嵌板')
    out = over(rgb, L.get())
    # Place SF10 photo INSIDE the frame after overlay so Layer fill cannot cover it
    plate_a = 0.92
    out = place(out, _sf10_rgb, _sf10_a * plate_a, int(72 * s), int(118 * s), opacity=0.98)
    return grade(out, seed=int(t * 24) % 10000)

def sf19(t, W, H):
    """Engram — photo mouse in both env panels instead of dots-only schematic."""
    s = W / 1280
    rgb = bg(W, H, t, GOLD, 0.4, 0.45)
    L = Layer(W, H)
    phase = (t + 1.0) % 36.0
    header(L, W, H, '小鼠海马 · 假恐惧记忆（2013）', '只讲小鼠 · 不讲人体记忆操作', min(t, 2.0) + 1.0, s)
    # env A / B
    L.rrect((50 * s, 100 * s, 500 * s, 360 * s), 12 * s, fill=(20, 35, 70), alpha=0.88)
    L.rrect((700 * s, 100 * s, 1150 * s, 360 * s), 12 * s, fill=(70, 30, 40), alpha=0.88)
    L.text((275 * s, 130 * s), '环境甲', F(SANS_B, 22 * s), fill=CYAN, alpha=0.95, anchor='ms')
    L.text((925 * s, 130 * s), '环境乙', F(SANS_B, 22 * s), fill=AMBER, alpha=0.95, anchor='ms')
    L.text((275 * s, 340 * s), '齿状回细胞 · ChR2', F(SANS, 14 * s), fill=CREAM, alpha=0.9, anchor='ms')
    L.text((925 * s, 340 * s), '电击 + 光召回甲细胞', F(SANS, 14 * s), fill=CREAM, alpha=0.9, anchor='ms')
    # chips always visible after short ramp
    chip(L, (50 * s, 380 * s, 1150 * s, 455 * s), '再回甲：无电击，却冻结', '作者：制造出虚假恐惧记忆', 1.0, GOLD, s)
    if phase > 12.0:
        chip(L, (50 * s, 465 * s, 1150 * s, 525 * s), '写进去的是一批细胞的活动 · 不是一句话 / 一段人生', '小鼠恐惧行为已驱动 · 人体记忆：本研究不涉及', 1.0, AMBER, s)
    footer_tick(L, W, H, t, s, 'C · 假记忆 · 照片鼠嵌板 · 笼写实仍 deferred')
    out = over(rgb, L.get())
    # Soft studio pad + photo mouse (gentle matte keeps readable fur on dark panels)
    mr, ma = load_rgb(MOUSE, 300, 214)
    mr2, ma2 = matte_gray_bg(mr, ma, thr=0.93)  # keep more gray floor as soft pad
    out = place(out, mr2, np.maximum(ma2, 0.35), int(120 * s), int(150 * s), opacity=0.98)
    out = place(out, mr2 * np.array([1.04, 0.92, 0.92], np.float32), np.maximum(ma2, 0.35), int(770 * s), int(150 * s), opacity=0.98)
    return grade(out, seed=int(t * 24) % 10000)

def sf21(t, W, H):
    """Partial vision — no face; SF11 eye/goggles plate as apparatus."""
    s = W / 1280
    rgb = bg(W, H, t, AMBER, 0.4, 0.4)
    L = Layer(W, H)
    phase = (t + 1.0) % 30.0
    header(L, W, H, '部分功能恢复', '必须戴护目镜 · 不是日常视觉', min(t, 2.0) + 1.0, s)
    # eye apparatus frame (photo after overlay)
    L.rrect((680 * s, 110 * s, 1180 * s, 340 * s), 10 * s, outline=AMBER, width=2 * s, alpha=0.55)
    # sparse objects left
    for i, (x, y) in enumerate([(180, 200), (320, 180), (460, 210), (280, 280)]):
        pulse = 0.55 + 0.45 * math.sin(t * 3.5 + i)
        gog = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.6))
        L.rrect(((x - 36) * s, (y - 36) * s, (x + 36) * s, (y + 36) * s), 4 * s, outline=CREAM, width=1.5 * s, alpha=0.85 * gog * pulse)
        L.dot((x * s, y * s), 4 * s, fill=AMBER, alpha=0.9 * gog)
    chip(L, (60 * s, 370 * s, 620 * s, 460 * s), '戴护目镜：能指位置 / 数个数 / 触到', '摘掉护目镜：看不见这些物体', 1.0, GOLD, s)
    chip(L, (640 * s, 370 * s, 1220 * s, 460 * s), '护目镜：亮度变化 → 视网膜光脉冲', '打开新装的 ChrimsonR · 无人脸', 1.0, AMBER, s)
    L.text((W / 2, 500 * s), '诺奖新闻稿措辞停在「尝试恢复视力」', F(SANS, 14 * s), fill=MUTED, alpha=0.85, anchor='ms')
    footer_tick(L, W, H, t, s, 'C · 部分视觉 · SF11 护目镜板 · 无人脸')
    out = over(rgb, L.get())
    out = place(out, _sf11_rgb, _sf11_a, int(700 * s), int(118 * s), opacity=0.98)
    return grade(out, seed=int(t * 24) % 10000)

SCENES = {
    'SF18_invivo_dual': (sf18, 36.0),
    'SF19_engram': (sf19, 36.0),
    'SF21_partial_vision': (sf21, 30.0),
}

def render_one(name):
    fn, dur = SCENES[name]
    n = int(round(dur * FPS))
    still_t = 2.5
    png = f'{OUT}/{name}.png'
    mp4 = f'{OUT}/{name}.mp4'
    print(f'render {name} dur={dur}s frames={n}', flush=True)
    save(fn(still_t, 1280, 720), png)
    t0 = __import__('time').time()
    write_video(lambda i, fn=fn: fn(i / FPS, W, H), n, mp4, W, H, FPS)
    print(f'  done {png} {mp4} in {__import__("time").time()-t0:.1f}s', flush=True)

if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SCENES)
    for n in names:
        render_one(n)
    print('ALL_OK', len(names))
