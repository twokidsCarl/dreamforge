#!/usr/bin/env python3
"""Slice2 multibeat: SF22/SF15/SF13 + SF21 photo-inset ken-burns caption-safe.
$0 pillow/2.5D. Do NOT touch Blender/e1r4.
Film: SF22≈95.7 SF15≈64.3 SF13≈53.1 SF21≈47.3
"""
from __future__ import annotations
import math, sys, time as _time
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
from PIL import Image
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
# caption bar in assemble is bottom 100px @720 → keep primary content above ~0.82 H
CAP_SAFE_Y = 0.80  # fraction of H — chips/headers stay above this
MOUSE = '/workspace/e2work/v8/gen/mouse_ref.png'
SF10_STILL = '/workspace/e2work/v8/styleframes/SF10_mouse_tripo.png'
SF11_STILL = '/workspace/e2work/v8/styleframes/SF11_eye_goggles.png'

def load_rgb(path, tw, th):
    im = Image.open(path).convert('RGBA').resize((tw, th), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr[..., :3], arr[..., 3:4]

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
    # sits in caption-overlay zone — decorative only
    a = 0.45 + 0.1 * math.sin(t * 1.4)
    L.line([(80 * s, H - 28 * s), (W - 80 * s, H - 28 * s)], fill=(50, 60, 90), width=1 * s, alpha=a)
    if label:
        L.text((W / 2, H - 14 * s), label, F(SANS, 11 * s), fill=MUTED, alpha=0.55, anchor='ms')

def progress_rail(L, W, H, t, total, s, n_marks, accent=CYAN):
    frac = min(max(t / max(total, 1e-6), 0), 1)
    y = H * CAP_SAFE_Y + 8 * s  # just below safe content, above caption bar
    x0, x1 = 100 * s, W - 100 * s
    L.line([(x0, y), (x1, y)], fill=(40, 50, 80), width=2 * s, alpha=0.5)
    L.line([(x0, y), (x0 + (x1 - x0) * frac, y)], fill=accent, width=2.5 * s, alpha=0.8)
    for i in range(n_marks):
        xf = x0 + (x1 - x0) * (i / max(n_marks - 1, 1))
        on = frac >= i / max(n_marks - 1, 1)
        L.dot((xf, y), 3.5 * s, fill=accent if on else (60, 70, 100), alpha=0.85 if on else 0.3)

_sf10 = load_rgb(SF10_STILL, 480, 270)
_sf10_a = np.ones_like(_sf10[1])
_sf11 = load_rgb(SF11_STILL, 420, 236)
_sf11_a = np.ones_like(_sf11[1])

# =====================================================================
# SF22 regulatory · film ~95.7 · UNIQUE 94s · 5 cards progressive
# =====================================================================
def sf22(t, W, H):
    s = W / 1280
    TOTAL = 94.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.45, 0.35)
    L = Layer(W, H)
    cards = [
        (0.0,  18.0, '2026-09-09', 'BLA 已受理 · MCO-010 / MOGENRY', '公告写「如果获批」→ 当时尚未获批', GOLD),
        (18.0, 36.0, '第 52 / 76 周', '视力主要终点与关键次要终点', '申请方公告 · 不是已生效许可', CYAN),
        (36.0, 54.0, '2026-10-08', '另一款 · 1/2 期 · 《新英格兰医学杂志》', '安全性为主 · 非确证疗效设计', AMBER),
        (54.0, 74.0, '数字连同分母', '光敏感 6/10 · 行为测试 4/8（部分任务）', '戴着护目镜 · 不写成全体患者', CYAN),
        (74.0, 94.0, '脚注', '任何司法辖区都没有上市许可', 'GS030 · 仍是申请/探索', AMBER),
    ]
    header(L, W, H, '临床边界 · 以公告与论文为准', '受理 ≠ 获批 · 探索 ≠ 确证', min(tt, 2.0) + 1.0, s)
    cur = cards[0]
    for c in cards:
        if tt >= c[0]:
            cur = c
    t0, t1, k, title, sub, col = cur
    local = tt - t0
    # caption-safe card: bottom of card above CAP_SAFE_Y
    y1 = H * CAP_SAFE_Y - 20 * s
    L.rrect((100 * s, 120 * s, 1180 * s, y1), 14 * s, fill=(14, 20, 40), alpha=0.82)
    L.line([(100 * s, 120 * s), (100 * s, y1)], fill=col, width=5 * s, alpha=0.95)
    L.text((140 * s, 180 * s), k, F(SANS_B, 20 * s), fill=col, alpha=0.95, anchor='ls', tracking=2 * s)
    L.text((140 * s, 250 * s), title, F(SANS_B, 26 * s), fill=CREAM, alpha=0.95, anchor='ls')
    L.text((140 * s, 310 * s), sub, F(SANS, 17 * s), fill=MUTED, alpha=0.9, anchor='ls')
    # dwell pulse + slow ion ticks unique to card
    for j in range(8):
        u = (local * 0.08 + j / 8) % 1.0
        px = 160 * s + u * 900 * s
        py = 360 * s + 10 * s * math.sin(local * 1.8 + j)
        L.dot((px, py), 3 * s, fill=col, alpha=0.3 + 0.3 * math.sin(local * 2.5 + j))
    # progress dots (caption-safe)
    for i, c in enumerate(cards):
        on = tt >= c[0]
        L.dot((200 * s + i * 180 * s, H * CAP_SAFE_Y - 8 * s), 6 * s,
              fill=c[5] if on else (60, 70, 100), alpha=0.9 if on else 0.35)
    progress_rail(L, W, H, tt, TOTAL, s, 5, GOLD)
    footer_tick(L, W, H, tt, s, 'C · 监管与数字 · 多拍连续')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)

# =====================================================================
# SF15 BR pump/channel · film ~64.3 · UNIQUE 62s
# =====================================================================
def sf15(t, W, H):
    s = W / 1280
    TOTAL = 62.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, (160, 80, 180), 0.4, 0.4)
    L = Layer(W, H)
    if tt < 30.0:
        p = tt
        header(L, W, H, '开关先在微生物膜上', '1971 紫膜 · 1973 细菌视紫红质 · 光驱动质子泵',
               min(p, 2.0) + 1.0, s)
        L.rrect((400 * s, 130 * s, 880 * s, 360 * s), 16 * s, fill=(60, 30, 80), alpha=0.85)
        for i in range(5):
            for j in range(3):
                x = 460 * s + i * 80 * s; y = 180 * s + j * 55 * s
                pulse = 0.5 + 0.3 * math.sin(p * 1.2 + i + j)
                L.ring((x, y), 16 * s, fill=(180, 100, 200), width=2 * s, alpha=0.65 + 0.2 * pulse)
                L.dot((x, y), 5 * s, fill=GOLD, alpha=0.45 + 0.35 * pulse)
        chip(L, (80 * s, 140 * s, 360 * s, 230 * s), '紫膜片段', '蛋白只有这一种',
             ramp(p, 2.0, 4.0), GOLD, s)
        chip(L, (80 * s, 250 * s, 360 * s, 340 * s), '视黄醛', '吸收光 · 质子泵出',
             ramp(p, 10.0, 12.0), AMBER, s)
        chip(L, (400 * s, 380 * s, 880 * s, H * CAP_SAFE_Y - 10 * s),
             '细菌视紫红质 = 光驱动的质子泵', '定向搬运 · 不是通道',
             ramp(p, 18.0, 20.0), CYAN, s)
    else:
        p2 = tt - 30.0
        header(L, W, H, '泵 ≠ 通道', '神经元在意的是电压', min(p2, 2.0) + 1.0, s)
        L.rrect((100 * s, 120 * s, 580 * s, 360 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((660 * s, 120 * s, 1140 * s, 360 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.text((340 * s, 160 * s), '泵', F(SANS_B, 32 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((340 * s, 210 * s), '逆着梯度推一趟', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        for i in range(5):
            y = 320 * s - ((p2 * 25 + i * 28) % 140)
            L.dot((340 * s, y), 5 * s, fill=AMBER, alpha=0.75)
        L.text((900 * s, 160 * s), '通道', F(SANS_B, 32 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.text((900 * s, 210 * s), '孔打开 · 离子顺梯度涌', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        for i in range(7):
            y = 240 * s + ((p2 * 35 + i * 22) % 130) - 40
            L.dot((900 * s + (i % 2) * 18 * s, y), 5 * s, fill=GOLD, alpha=0.7)
        chip(L, (100 * s, 380 * s, 1140 * s, H * CAP_SAFE_Y - 8 * s),
             '离子带电荷 → 膜电压变 → 神经元说话', '泵和通道不要混成一个分子',
             ramp(p2, 8.0, 12.0), GOLD, s)
    progress_rail(L, W, H, tt, TOTAL, s, 2, (180, 100, 200))
    footer_tick(L, W, H, tt, s, 'B · 紫膜 / 泵与通道 · 多拍')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)

# =====================================================================
# SF13 spike/causality/ms · film ~53.1 · UNIQUE 52s
# =====================================================================
def sf13(t, W, H):
    s = W / 1280
    TOTAL = 52.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.25, 0.35)
    L = Layer(W, H)
    if tt < 17.0:
        p = tt
        header(L, W, H, '神经元靠膜两侧的电压说话', '一次锋电位：离子穿过 · 电压翻过去再恢复',
               min(p, 2.0) + 1.0, s)
        L.line([(120 * s, 250 * s), (1160 * s, 250 * s)], fill=(80, 100, 140), width=3 * s, alpha=0.85)
        L.text((120 * s, 220 * s), '膜外', F(SANS, 14 * s), fill=MUTED, alpha=0.8, anchor='ls')
        L.text((120 * s, 290 * s), '膜内', F(SANS, 14 * s), fill=MUTED, alpha=0.8, anchor='ls')
        for i in range(8):
            u = (p * 0.25 + i / 8) % 1.0
            x = 200 * s + i * 110 * s
            y = 250 * s + (u - 0.5) * 90 * s
            L.dot((x, y), 6 * s, fill=GOLD, alpha=0.65)
        pts = []
        for i in range(40):
            u = i / 39
            x = 200 * s + u * 880 * s
            sp = math.exp(-((u - 0.45) / 0.06) ** 2) - 0.15 * math.exp(-((u - 0.55) / 0.1) ** 2)
            # spike travels slowly across the 17s act
            shift = 0.15 * math.sin(p * 0.35)
            sp2 = math.exp(-((u - (0.45 + shift)) / 0.06) ** 2)
            y = 380 * s - sp2 * 80 * s
            pts.append((x, y))
        L.line(pts, fill=CYAN, width=2.2 * s, alpha=0.9)
        chip(L, (80 * s, 410 * s, 700 * s, H * CAP_SAFE_Y - 8 * s),
             '锋电位', '极短时间里电压忽然翻过去', ramp(p, 4.0, 6.0), CYAN, s)
    elif tt < 34.0:
        p2 = tt - 17.0
        header(L, W, H, '相关还不够', '因果要多问一句：是它造成的，还是只是一起亮？',
               min(p2, 2.0) + 1.0, s)
        L.rrect((100 * s, 120 * s, 560 * s, 360 * s), 10 * s, fill=(14, 20, 40), alpha=0.75)
        L.rrect((680 * s, 120 * s, 1180 * s, 360 * s), 10 * s, fill=(14, 20, 40), alpha=0.75)
        L.text((330 * s, 170 * s), '同时亮着', F(SANS_B, 28 * s), fill=CREAM, alpha=0.95, anchor='ms')
        L.text((330 * s, 230 * s), '细胞亮 · 动物醒了 / 怕了', F(SANS, 16 * s), fill=MUTED, alpha=0.9, anchor='ms')
        L.text((930 * s, 170 * s), '是它造成的吗？', F(SANS_B, 26 * s), fill=GOLD, alpha=0.95, anchor='ms')
        L.text((930 * s, 230 * s), '还是跟着行为一起亮', F(SANS, 16 * s), fill=MUTED, alpha=0.9, anchor='ms')
        L.text((930 * s, 300 * s), '？', F(SERIF_B, 64 * s), fill=GOLD,
               alpha=0.45 + 0.25 * math.sin(p2 * 1.5), anchor='ms')
        chip(L, (100 * s, 380 * s, 1180 * s, H * CAP_SAFE_Y - 8 * s),
             '记录与损毁证明不了因果关系', '诺奖新闻稿写明 · 要能只推动 / 按住那一类细胞',
             ramp(p2, 6.0, 9.0), AMBER, s)
    else:
        p3 = tt - 34.0
        header(L, W, H, '时间尺度要对', '毫秒，不是分钟', min(p3, 2.0) + 1.0, s)
        L.rrect((160 * s, 130 * s, 560 * s, 360 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((700 * s, 130 * s, 1100 * s, 360 * s), 12 * s, fill=(14, 20, 40), alpha=0.55)
        L.ring((360 * s, 230 * s), 70 * s, fill=CYAN, width=4 * s, alpha=0.9)
        ms = int((p3 * 11) % 100)  # slower unique count across act
        L.text((360 * s, 240 * s), f'{ms:02d} ms', F(SANS_B, 36 * s), fill=CREAM, alpha=0.95, anchor='ms')
        L.text((360 * s, 320 * s), '可用 · 对齐锋电位', F(SANS, 16 * s), fill=CYAN, alpha=0.9, anchor='ms')
        L.ring((900 * s, 230 * s), 70 * s, fill=(90, 100, 130), width=3 * s, alpha=0.6)
        L.text((900 * s, 240 * s), '分钟', F(SANS_B, 32 * s), fill=MUTED, alpha=0.7, anchor='ms')
        L.text((900 * s, 320 * s), '太慢', F(SANS, 16 * s), fill=MUTED, alpha=0.7, anchor='ms')
        chip(L, (160 * s, 380 * s, 1100 * s, H * CAP_SAFE_Y - 8 * s),
             '只动一类 · 可开可关 · 毫秒', '要回答因果，缺的是这枚开关',
             ramp(p3, 6.0, 9.0), GOLD, s)
    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'A · 锋电位 / 因果 / 毫秒 · 多拍')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)

# =====================================================================
# SF21 partial vision · film ~47.3 · UNIQUE 46s · SF11 ken-burns caption-safe
# =====================================================================
def sf21(t, W, H):
    s = W / 1280
    TOTAL = 46.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.4, 0.4)
    L = Layer(W, H)
    header(L, W, H, '部分功能恢复', '必须戴护目镜 · 不是日常视觉', min(tt, 2.0) + 1.0, s)
    # apparatus frame — caption-safe (above CAP_SAFE_Y)
    frame_y1 = H * 0.58
    L.rrect((680 * s, 100 * s, 1200 * s, frame_y1), 10 * s, outline=AMBER, width=2 * s, alpha=0.55)
    # sparse objects left — progressive reveal
    objs = [(180, 180), (320, 160), (460, 190), (280, 250), (400, 270)]
    n_vis = int(np.clip(tt / 12.0, 0, 1) * len(objs))
    for i, (x, y) in enumerate(objs):
        if i >= max(n_vis, 1) and tt < 12: 
            continue
        pulse = 0.55 + 0.45 * math.sin(tt * 2.2 + i)
        gog = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(tt * 0.35))  # slow goggles-on cycle unique across 46s
        aa = ramp(tt, 1.0 + i * 2.0, 3.0 + i * 2.0)
        L.rrect(((x - 32) * s, (y - 32) * s, (x + 32) * s, (y + 32) * s), 4 * s,
                outline=CREAM, width=1.5 * s, alpha=0.85 * gog * pulse * max(aa, 0.3))
        L.dot((x * s, y * s), 4 * s, fill=AMBER, alpha=0.9 * gog * max(aa, 0.3))
    chip(L, (60 * s, 340 * s, 640 * s, H * CAP_SAFE_Y - 10 * s),
         '戴护目镜：能指位置 / 数个数 / 触到', '摘掉护目镜：看不见这些物体',
         ramp(tt, 14.0, 18.0), GOLD, s)
    chip(L, (660 * s, 340 * s, 1220 * s, H * CAP_SAFE_Y - 10 * s),
         '护目镜：亮度变化 → 视网膜光脉冲', '打开新装的 ChrimsonR · 无人脸',
         ramp(tt, 24.0, 28.0), AMBER, s)
    L.text((W / 2, H * CAP_SAFE_Y - 28 * s), '诺奖新闻稿措辞停在「尝试恢复视力」',
           F(SANS, 14 * s), fill=MUTED, alpha=ramp(tt, 34.0, 38.0), anchor='ms')
    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'C · 部分视觉 · SF11 护目镜板 · 无人脸 · 多拍')
    out = over(rgb, L.get())
    # Ken-burns: slow pan+zoom feel via offset; keep plate inside frame, above caption
    # plate size 420x236 @960 → place near frame
    ox = int(700 * s + 14 * s * math.sin(tt * 0.09))
    oy = int(110 * s + 8 * s * math.cos(tt * 0.07))
    # slight opacity breathe
    op = 0.94 + 0.04 * math.sin(tt * 0.2)
    out = place(out, _sf11[0], _sf11_a, ox, oy, opacity=op)
    return grade(out, seed=int(tt * 24) % 100000)


SCENES = {
    'SF22_regulatory': (sf22, 94.0),
    'SF15_br_pump_channel': (sf15, 62.0),
    'SF13_spike_causality': (sf13, 52.0),
    'SF21_partial_vision': (sf21, 46.0),
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
