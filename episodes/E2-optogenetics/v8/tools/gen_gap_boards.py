#!/usr/bin/env python3
"""Generate loopable EigenLens-style diagram/type boards for v7 gap windows.
$0 / no Blender / no gen API. Output: v8/styleframes/SF12..SF23.{mp4,png}
"""
from __future__ import annotations
import math, sys, os
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *

OUT = '/workspace/e2work/v8/styleframes'
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 960, 540, 24  # match existing SF delivery; assemble upscales

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

# ---------- SF12 selective neurons ----------
def sf12(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, CYAN, 0.5, 0.45)
    L = Layer(W, H)
    header(L, W, H, '他要的方法很具体', '只动某一类 · 可开可关 · 要快', t, s)
    # row of neurons
    n = 7; cx0 = 180 * s; gap = 140 * s; cy = 300 * s
    sel = 3
    for i in range(n):
        x = cx0 + i * gap
        on = (i == sel)
        a = ramp(t, 0.4 + 0.08 * i, 1.0)
        col = CYAN if on else (90, 100, 130)
        L.ring((x, cy), 28 * s, fill=col, width=2.2 * s, alpha=a)
        L.dot((x, cy), 10 * s, fill=col, alpha=a * (0.9 if on else 0.35))
        # axon
        L.line([(x, cy + 28 * s), (x, cy + 90 * s)], fill=col, width=1.5 * s, alpha=a * 0.7)
        if on:
            pulse = 0.5 + 0.5 * math.sin(t * 8)
            L.dot((x, cy + 50 * s + 20 * s * math.sin(t * 6)), 5 * s, fill=GOLD, alpha=a * pulse)
    chip(L, (80 * s, 460 * s, 560 * s, 530 * s), '中间一类被圈出', '两侧保持灰色 · 示意，不标未核实比例', ramp(t, 1.5, 2.3), CYAN, s)
    chip(L, (620 * s, 460 * s, 1200 * s, 530 * s), '旁边的细胞大体不动', '而且要快（毫秒尺度）', ramp(t, 2.2, 3.0), GOLD, s)
    footer_tick(L, W, H, t, s, 'A0 · 选择性')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF13 spike / causality / ms ----------
def sf13(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, CYAN, 0.25, 0.35)
    L = Layer(W, H)
    # phase cycle 0-12s: 0 membrane, 1 correlate, 2 ms
    phase = (t % 12.0)
    if phase < 4.0:
        header(L, W, H, '神经元靠膜两侧的电压说话', '一次锋电位：离子穿过 · 电压翻过去再恢复', phase, s)
        # membrane line + ions
        L.line([(120 * s, 280 * s), (1160 * s, 280 * s)], fill=(80, 100, 140), width=3 * s, alpha=ramp(phase, 0.3, 1.0))
        L.text((120 * s, 250 * s), '膜外', F(SANS, 14 * s), fill=MUTED, alpha=0.8, anchor='ls')
        L.text((120 * s, 320 * s), '膜内', F(SANS, 14 * s), fill=MUTED, alpha=0.8, anchor='ls')
        for i in range(8):
            p = (phase * 0.4 + i / 8) % 1.0
            x = 200 * s + i * 110 * s
            y = 280 * s + (p - 0.5) * 100 * s
            L.dot((x, y), 6 * s, fill=GOLD, alpha=0.7 * ramp(phase, 0.5, 1.2))
        # voltage curve
        pts = []
        for i in range(40):
            u = i / 39
            x = 200 * s + u * 880 * s
            # spike shape
            sp = math.exp(-((u - 0.45) / 0.06) ** 2) - 0.15 * math.exp(-((u - 0.55) / 0.1) ** 2)
            y = 430 * s - sp * 90 * s
            pts.append((x, y))
        L.line(pts, fill=CYAN, width=2.2 * s, alpha=ramp(phase, 1.0, 1.8))
        chip(L, (80 * s, 480 * s, 500 * s, 540 * s), '锋电位', '极短时间里电压忽然翻过去', ramp(phase, 2.0, 2.8), CYAN, s)
    elif phase < 8.0:
        p2 = phase - 4.0
        header(L, W, H, '相关还不够', '因果要多问一句：是它造成的，还是只是一起亮？', p2, s)
        # two columns
        L.rrect((100 * s, 140 * s, 560 * s, 420 * s), 10 * s, fill=(14, 20, 40), alpha=0.75 * ramp(p2, 0.3, 1.0))
        L.rrect((680 * s, 140 * s, 1180 * s, 420 * s), 10 * s, fill=(14, 20, 40), alpha=0.75 * ramp(p2, 0.6, 1.3))
        L.text((330 * s, 190 * s), '同时亮着', F(SANS_B, 28 * s), fill=CREAM, alpha=ramp(p2, 0.4, 1.1), anchor='ms')
        L.text((330 * s, 250 * s), '细胞亮 · 动物醒了 / 怕了', F(SANS, 16 * s), fill=MUTED, alpha=ramp(p2, 0.6, 1.3), anchor='ms')
        L.text((930 * s, 190 * s), '是它造成的吗？', F(SANS_B, 28 * s), fill=GOLD, alpha=ramp(p2, 0.8, 1.5), anchor='ms')
        L.text((930 * s, 250 * s), '还是跟着行为一起亮', F(SANS, 16 * s), fill=MUTED, alpha=ramp(p2, 1.0, 1.7), anchor='ms')
        L.text((930 * s, 340 * s), '？', F(SERIF_B, 72 * s), fill=GOLD, alpha=0.5 + 0.3 * math.sin(p2 * 3), anchor='ms')
        chip(L, (100 * s, 450 * s, 1180 * s, 520 * s), '记录与损毁证明不了因果关系', '诺奖新闻稿写明 · 要能只推动 / 按住那一类细胞', ramp(p2, 2.2, 3.0), AMBER, s)
    else:
        p3 = phase - 8.0
        header(L, W, H, '时间尺度要对', '毫秒，不是分钟', p3, s)
        # two timers
        L.rrect((160 * s, 160 * s, 560 * s, 400 * s), 12 * s, fill=(14, 20, 40), alpha=0.8 * ramp(p3, 0.2, 0.8))
        L.rrect((700 * s, 160 * s, 1100 * s, 400 * s), 12 * s, fill=(14, 20, 40), alpha=0.55 * ramp(p3, 0.4, 1.0))
        L.ring((360 * s, 260 * s), 70 * s, fill=CYAN, width=4 * s, alpha=ramp(p3, 0.3, 1.0))
        ms = int((p3 * 37) % 100)
        L.text((360 * s, 270 * s), f'{ms:02d} ms', F(SANS_B, 36 * s), fill=CREAM, alpha=ramp(p3, 0.4, 1.1), anchor='ms')
        L.text((360 * s, 360 * s), '可用 · 对齐锋电位', F(SANS, 16 * s), fill=CYAN, alpha=ramp(p3, 0.8, 1.4), anchor='ms')
        L.ring((900 * s, 260 * s), 70 * s, fill=(90, 100, 130), width=3 * s, alpha=0.6)
        L.text((900 * s, 270 * s), '分钟', F(SANS_B, 32 * s), fill=MUTED, alpha=0.7, anchor='ms')
        L.text((900 * s, 360 * s), '太慢', F(SANS, 16 * s), fill=MUTED, alpha=0.7, anchor='ms')
        chip(L, (160 * s, 440 * s, 1100 * s, 520 * s), '只动一类 · 可开可关 · 毫秒', '要回答因果，缺的是这枚开关', ramp(p3, 1.8, 2.6), GOLD, s)
    footer_tick(L, W, H, t, s, 'A · 锋电位 / 因果 / 毫秒')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF14 orexin question ----------
def sf14(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, AMBER, 0.45, 0.5)
    L = Layer(W, H)
    header(L, W, H, '下丘脑外侧 · 食欲素神经元', '和清醒有关 —— 但放电本身够不够？', t, s)
    # stylized brain oval + cluster
    L.ring((640 * s, 300 * s), 160 * s, fill=(70, 90, 130), width=2 * s, alpha=ramp(t, 0.3, 1.0))
    L.ring((640 * s, 300 * s), 100 * s, fill=(60, 80, 120), width=1.5 * s, alpha=0.5)
    # highlight cluster
    for i in range(12):
        ang = i / 12 * 2 * math.pi + t * 0.3
        r = 28 * s + (i % 3) * 8 * s
        x = 580 * s + r * math.cos(ang)
        y = 340 * s + r * 0.6 * math.sin(ang)
        L.dot((x, y), 5 * s, fill=GOLD, alpha=0.5 + 0.4 * ramp(t, 0.8, 1.6) * (0.6 + 0.4 * math.sin(t * 5 + i)))
    L.ring((580 * s, 340 * s), 42 * s, fill=GOLD, width=1.8 * s, alpha=ramp(t, 1.0, 1.8))
    chip(L, (80 * s, 200 * s, 360 * s, 300 * s), '左：和清醒有关', '相关已知', ramp(t, 1.6, 2.4), MUTED, s)
    chip(L, (80 * s, 320 * s, 360 * s, 420 * s), '右：放电够不够？', '因果未决 · 被圈出', ramp(t, 2.2, 3.0), GOLD, s)
    footer_tick(L, W, H, t, s, 'A_07 · 示意剖面 · 非写实鼠')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF15 BR / pump vs channel ----------
def sf15(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, (160, 80, 180), 0.4, 0.4)
    L = Layer(W, H)
    phase = t % 10.0
    if phase < 5.0:
        header(L, W, H, '开关先在微生物膜上', '1971 紫膜 · 1973 细菌视紫红质 · 光驱动质子泵', phase, s)
        # membrane patch
        L.rrect((400 * s, 160 * s, 880 * s, 400 * s), 16 * s, fill=(60, 30, 80), alpha=0.85 * ramp(phase, 0.3, 1.0))
        for i in range(5):
            for j in range(3):
                x = 460 * s + i * 80 * s; y = 210 * s + j * 60 * s
                L.ring((x, y), 18 * s, fill=(180, 100, 200), width=2 * s, alpha=0.7)
                L.dot((x, y), 6 * s, fill=GOLD, alpha=0.5 + 0.3 * math.sin(phase * 3 + i + j))
        chip(L, (80 * s, 180 * s, 360 * s, 280 * s), '紫膜片段', '蛋白只有这一种', ramp(phase, 1.2, 2.0), GOLD, s)
        chip(L, (80 * s, 300 * s, 360 * s, 400 * s), '视黄醛', '吸收光 · 质子泵出', ramp(phase, 2.0, 2.8), AMBER, s)
        chip(L, (400 * s, 430 * s, 880 * s, 510 * s), '细菌视紫红质 = 光驱动的质子泵', '定向搬运 · 不是通道', ramp(phase, 3.0, 3.8), CYAN, s)
    else:
        p2 = phase - 5.0
        header(L, W, H, '泵 ≠ 通道', '神经元在意的是电压', p2, s)
        L.rrect((100 * s, 130 * s, 580 * s, 420 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((660 * s, 130 * s, 1140 * s, 420 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.text((340 * s, 170 * s), '泵', F(SANS_B, 32 * s), fill=AMBER, alpha=ramp(p2, 0.3, 1.0), anchor='ms')
        L.text((340 * s, 230 * s), '逆着梯度推一趟', F(SANS, 18 * s), fill=CREAM, alpha=ramp(p2, 0.5, 1.2), anchor='ms')
        # arrow up
        for i in range(4):
            y = 360 * s - i * 30 * s - (p2 * 40 % 30)
            L.dot((340 * s, y), 5 * s, fill=AMBER, alpha=0.8)
        L.text((900 * s, 170 * s), '通道', F(SANS_B, 32 * s), fill=CYAN, alpha=ramp(p2, 0.5, 1.2), anchor='ms')
        L.text((900 * s, 230 * s), '孔打开 · 离子顺梯度涌', F(SANS, 18 * s), fill=CREAM, alpha=ramp(p2, 0.7, 1.4), anchor='ms')
        for i in range(6):
            y = 280 * s + ((p2 * 50 + i * 20) % 120) - 60
            L.dot((900 * s + (i % 2) * 20 * s, y), 5 * s, fill=GOLD, alpha=0.75)
        chip(L, (100 * s, 450 * s, 1140 * s, 520 * s), '离子带电荷 → 膜电压变 → 神经元说话', '泵和通道不要混成一个分子', ramp(p2, 2.5, 3.3), GOLD, s)
    footer_tick(L, W, H, t, s, 'B · 紫膜 / 泵与通道')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF16 ChR path ----------
def sf16(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, CYAN, 0.55, 0.4)
    L = Layer(W, H)
    phase = t % 14.0
    steps = [
        (0, '衣藻朝光游', '眼点 · 谁在感光？', GOLD),
        (2.5, '2002 · 通道视紫红质一', '放进卵母细胞 · 光 → 质子电流', AMBER),
        (5.0, '关键：光与孔在同一分子', '不必多步接力 · 送进一个基因就行', CYAN),
        (7.5, '2003 · 通道视紫红质二', '蓝光开阳离子 · 哺乳细胞也能用', CYAN),
        (10.0, '持续光照会脱敏', '高峰→平台 · 要用短脉冲', AMBER),
        (12.0, '2005 · 培养神经元', '蓝光脉冲对齐锋电位', GOLD),
    ]
    header(L, W, H, '从衣藻到毫秒级开关', 'ChR1 → 一体分子 → ChR2 → 锋电位', t, s)
    # timeline rail
    L.line([(100 * s, 200 * s), (1180 * s, 200 * s)], fill=(50, 60, 90), width=2 * s, alpha=0.8)
    for i, (t0, title, sub, col) in enumerate(steps):
        x = 100 * s + i * 180 * s
        a = ramp(phase, t0, t0 + 0.6)
        L.dot((x, 200 * s), 8 * s, fill=col, alpha=a)
        active = ramp(phase, t0, t0 + 0.4) * (1 - ramp(phase, t0 + 2.0, t0 + 2.4))
        if active > 0.05 or (i == len(steps) - 1 and phase > 12):
            aa = max(active, 0.35 if phase > t0 else 0)
            L.rrect((x - 70 * s, 240 * s, x + 100 * s, 360 * s), 8 * s, fill=(14, 20, 40), alpha=0.75 * aa)
            L.text((x + 15 * s, 280 * s), title, F(SANS_B, 15 * s), fill=CREAM, alpha=aa, anchor='ms')
            L.text((x + 15 * s, 320 * s), sub[:18], F(SANS, 12 * s), fill=MUTED, alpha=aa, anchor='ms')
    # big card for current
    cur = steps[0]
    for st in steps:
        if phase >= st[0]:
            cur = st
    chip(L, (100 * s, 400 * s, 1180 * s, 500 * s), cur[1], cur[2], 1.0, cur[3], s)
    footer_tick(L, W, H, t, s, 'B · ChR 路径')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF17 credit / word ----------
def sf17(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, GOLD, 0.5, 0.35)
    L = Layer(W, H)
    phase = t % 8.0
    if phase < 4.0:
        header(L, W, H, '署名和授奖名单，不是同一份', '2005 论文 · 2026 新闻稿', phase, s)
        L.rrect((80 * s, 130 * s, 580 * s, 400 * s), 10 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((660 * s, 130 * s, 1160 * s, 400 * s), 10 * s, fill=(14, 20, 40), alpha=0.8)
        L.text((330 * s, 170 * s), '论文署名', F(SANS_B, 22 * s), fill=MUTED, alpha=ramp(phase, 0.3, 1.0), anchor='ms')
        L.text((330 * s, 240 * s), 'Boyden 第一作者', F(SANS_B, 24 * s), fill=CREAM, alpha=ramp(phase, 0.6, 1.3), anchor='ms')
        L.text((330 * s, 290 * s), 'Deisseroth 通讯', F(SANS, 18 * s), fill=MUTED, alpha=ramp(phase, 0.9, 1.5), anchor='ms')
        L.text((910 * s, 170 * s), '2026 授奖', F(SANS_B, 22 * s), fill=MUTED, alpha=ramp(phase, 0.5, 1.2), anchor='ms')
        for i, nm in enumerate(['Deisseroth', 'Hegemann', 'Nagel']):
            L.text((910 * s, 230 * s + i * 40 * s), nm, F(SANS_B, 22 * s), fill=GOLD, alpha=ramp(phase, 0.8 + i * 0.2, 1.5), anchor='ms')
        L.text((910 * s, 360 * s), '第四行空着', F(SANS, 16 * s), fill=MUTED, alpha=ramp(phase, 2.0, 2.6), anchor='ms')
    else:
        p2 = phase - 4.0
        header(L, W, H, '2006 · optogenetics', '光学 + 遗传靶向：基因决定装谁，光决定何时拨', p2, s)
        word = 'optogenetics'
        # reveal letters
        n = int(min(len(word), 1 + p2 * 3))
        L.text((W / 2, 280 * s), word[:n], F(SANS_B, 48 * s), fill=CREAM, alpha=ramp(p2, 0.2, 0.8), anchor='ms', tracking=4 * s)
        L.text((W / 2, 360 * s), '2006 · 《神经科学杂志》示意', F(SANS, 16 * s), fill=MUTED, alpha=ramp(p2, 1.5, 2.2), anchor='ms')
    footer_tick(L, W, H, t, s, 'B · 署名 / 一词')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF18 invivo dual prizes ----------
def sf18(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, CYAN, 0.35, 0.4)
    L = Layer(W, H)
    phase = t % 12.0
    if phase < 4.0:
        header(L, W, H, '2007 · 光纤进活体脑', '运动皮层 · 只驱动表达 ChR2 的兴奋性神经元', phase, s)
        # head silhouette schematic
        L.ring((500 * s, 280 * s), 120 * s, fill=(70, 90, 130), width=2.5 * s, alpha=ramp(phase, 0.3, 1.0))
        L.line([(500 * s, 160 * s), (500 * s, 280 * s)], fill=CYAN, width=3 * s, alpha=ramp(phase, 0.8, 1.5))
        L.dot((500 * s, 280 * s), 10 * s, fill=CYAN, alpha=0.7 + 0.3 * math.sin(phase * 6))
        rgb = rgb + radial(W, H, 500 * s, 280 * s, 40 * s, CYAN, 0.35 * ramp(phase, 1.0, 1.8))
        chip(L, (700 * s, 180 * s, 1180 * s, 280 * s), '不另加视黄醛', '光也足够做出行为', ramp(phase, 1.5, 2.3), GOLD, s)
        chip(L, (700 * s, 300 * s, 1180 * s, 400 * s), '2005 培养皿 → 2007 活体', '大约两年', ramp(phase, 2.2, 3.0), CYAN, s)
    elif phase < 8.0:
        p2 = phase - 4.0
        header(L, W, H, '开还不够 · NpHR', '黄光泵入 Cl⁻ · 电压更负 · 锋电位被按住', p2, s)
        L.rrect((120 * s, 140 * s, 560 * s, 400 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((640 * s, 140 * s, 1080 * s, 400 * s), 12 * s, fill=(14, 20, 40), alpha=0.8)
        L.text((340 * s, 200 * s), '蓝光 · 开', F(SANS_B, 28 * s), fill=CYAN, alpha=ramp(p2, 0.3, 1.0), anchor='ms')
        L.text((340 * s, 270 * s), 'ChR2 通道', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((860 * s, 200 * s), '黄光 · 关', F(SANS_B, 28 * s), fill=AMBER, alpha=ramp(p2, 0.6, 1.3), anchor='ms')
        L.text((860 * s, 270 * s), 'NpHR 氯泵', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((W / 2, 450 * s), '同一套细胞 · 光谱分开 · 可从两头问因果', F(SANS, 16 * s), fill=MUTED, alpha=ramp(p2, 2.0, 2.8), anchor='ms')
    else:
        p3 = phase - 8.0
        header(L, W, H, '荣誉不止一份', '2013 Brain Prize 六人 ≠ 2026 诺奖三人', p3, s)
        six = ['Bamberg', 'Boyden', 'Deisseroth', 'Hegemann', 'Miesenböck', 'Nagel']
        for i, nm in enumerate(six):
            x = 120 * s + (i % 3) * 200 * s
            y = 160 * s + (i // 3) * 80 * s
            L.rrect((x, y, x + 180 * s, y + 60 * s), 6 * s, fill=(14, 20, 40), alpha=0.75 * ramp(p3, 0.2 + i * 0.1, 0.8))
            L.text((x + 90 * s, y + 38 * s), nm, F(SANS, 15 * s), fill=CREAM, alpha=ramp(p3, 0.3 + i * 0.1, 0.9), anchor='ms')
        L.text((900 * s, 220 * s), '六人奖', F(SANS_B, 24 * s), fill=MUTED, alpha=ramp(p3, 1.5, 2.2), anchor='ms')
        L.text((900 * s, 280 * s), '≠', F(SANS_B, 36 * s), fill=GOLD, alpha=ramp(p3, 2.0, 2.6), anchor='ms')
        L.text((900 * s, 340 * s), '三人诺奖', F(SANS_B, 24 * s), fill=GOLD, alpha=ramp(p3, 2.4, 3.0), anchor='ms')
    footer_tick(L, W, H, t, s, 'B · 活体 / 双色 / 奖项 · 鼠写实 deferred')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF19 engram ----------
def sf19(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, GOLD, 0.4, 0.45)
    L = Layer(W, H)
    phase = t % 12.0
    header(L, W, H, '小鼠海马 · 假恐惧记忆（2013）', '只讲小鼠 · 不讲人体记忆操作', t, s)
    # env A / B blocks
    L.rrect((80 * s, 130 * s, 480 * s, 320 * s), 12 * s, fill=(30, 50, 90), alpha=0.85 * ramp(phase, 0.2, 0.8))
    L.rrect((720 * s, 130 * s, 1120 * s, 320 * s), 12 * s, fill=(90, 40, 50), alpha=0.85 * ramp(phase, 1.0, 1.6))
    L.text((280 * s, 170 * s), '环境甲', F(SANS_B, 26 * s), fill=CYAN, alpha=ramp(phase, 0.3, 0.9), anchor='ms')
    L.text((920 * s, 170 * s), '环境乙', F(SANS_B, 26 * s), fill=AMBER, alpha=ramp(phase, 1.1, 1.7), anchor='ms')
    # cells in A
    for i in range(8):
        x = 140 * s + (i % 4) * 70 * s
        y = 220 * s + (i // 4) * 50 * s
        on = ramp(phase, 0.8, 1.4)
        L.dot((x, y), 8 * s, fill=GOLD, alpha=0.4 + 0.5 * on)
    L.text((280 * s, 290 * s), '齿状回细胞装上 ChR2', F(SANS, 14 * s), fill=CREAM, alpha=ramp(phase, 1.2, 1.8), anchor='ms')
    # shock mark in B
    L.text((920 * s, 240 * s), '电击 + 光召回甲细胞', F(SANS, 15 * s), fill=CREAM, alpha=ramp(phase, 2.0, 2.8), anchor='ms')
    if phase > 4.0:
        chip(L, (80 * s, 350 * s, 1120 * s, 430 * s), '再回甲：无电击，却冻结', '作者：制造出虚假恐惧记忆', ramp(phase, 4.0, 4.8), GOLD, s)
    if phase > 7.0:
        chip(L, (80 * s, 450 * s, 1120 * s, 520 * s), '写进去的是一批细胞的活动 · 不是一句话 / 一段人生', '小鼠恐惧行为已驱动 · 人体记忆：本研究不涉及', ramp(phase, 7.0, 7.8), AMBER, s)
    footer_tick(L, W, H, t, s, 'C · 假记忆示意 · 笼写实 deferred')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF20 retina intro ----------
def sf20(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, AMBER, 0.55, 0.45)
    L = Layer(W, H)
    header(L, W, H, '眼睛走另一条路', '感光细胞死去 · 神经节细胞还可留着', t, s)
    # layered retina
    layers = [
        (180, '感光细胞层', '逐渐变稀', (120, 120, 140), 0.35),
        (280, '双极等中间层', '', (90, 100, 130), 0.5),
        (380, '神经节细胞层', '可转导 · 幸存', CYAN, 0.9),
    ]
    for y, title, sub, col, dens in layers:
        a = ramp(t, 0.4, 1.2)
        L.rrect((200 * s, y * s, 1000 * s, (y + 70) * s), 8 * s, fill=(14, 20, 40), alpha=0.75 * a)
        L.line([(200 * s, y * s), (200 * s, (y + 70) * s)], fill=col, width=4 * s, alpha=a)
        L.text((230 * s, (y + 30) * s), title, F(SANS_B, 20 * s), fill=CREAM, alpha=a, anchor='ls')
        if sub:
            L.text((230 * s, (y + 55) * s), sub, F(SANS, 14 * s), fill=MUTED, alpha=a, anchor='ls')
        # density dots
        n = int(18 * dens)
        for i in range(n):
            L.dot((700 * s + i * 14 * s, (y + 35) * s), 3.5 * s, fill=col, alpha=a * dens)
    chip(L, (200 * s, 480 * s, 1000 * s, 530 * s), '若幸存细胞自己感光 → 后面通路也许还能被点着', '衔接 SF11 护目镜 / ChrimsonR', ramp(t, 2.5, 3.3), GOLD, s)
    footer_tick(L, W, H, t, s, 'C_07 · 视网膜剖面')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF21 partial vision ----------
def sf21(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, AMBER, 0.4, 0.4)
    L = Layer(W, H)
    phase = t % 10.0
    header(L, W, H, '部分功能恢复', '必须戴护目镜 · 不是日常视觉', t, s)
    # objects as sparse wireframes
    for i, (x, y) in enumerate([(280, 250), (500, 220), (720, 260), (900, 230)]):
        a = ramp(phase, 0.5 + i * 0.3, 1.2 + i * 0.3)
        pulse = 0.5 + 0.5 * math.sin(phase * 4 + i)
        # only visible when "goggles on"
        gog = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(phase * 0.8))
        L.rrect(((x - 40) * s, (y - 40) * s, (x + 40) * s, (y + 40) * s), 4 * s, outline=CREAM, width=1.5 * s, alpha=a * gog * pulse)
        L.dot((x * s, y * s), 4 * s, fill=AMBER, alpha=a * gog)
    chip(L, (80 * s, 360 * s, 600 * s, 450 * s), '戴护目镜：能指位置 / 数个数 / 触到', '摘掉护目镜：看不见这些物体', ramp(phase, 2.0, 2.8), GOLD, s)
    chip(L, (640 * s, 360 * s, 1200 * s, 450 * s), '护目镜：亮度变化 → 视网膜光脉冲', '打开新装的 ChrimsonR 通道', ramp(phase, 3.0, 3.8), AMBER, s)
    L.text((W / 2, 500 * s), '诺奖新闻稿措辞停在「尝试恢复视力」', F(SANS, 14 * s), fill=MUTED, alpha=ramp(phase, 4.5, 5.2), anchor='ms')
    footer_tick(L, W, H, t, s, 'C · 部分视觉 · 无人脸')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF22 regulatory (highest ROI) ----------
def sf22(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, GOLD, 0.45, 0.35)
    L = Layer(W, H)
    phase = t % 16.0
    cards = [
        (0, '2026-09-09', 'BLA 已受理 · MCO-010 / MOGENRY', '公告写「如果获批」→ 当时尚未获批', GOLD),
        (3.5, '第 52 / 76 周', '视力主要终点与关键次要终点', '申请方公告 · 不是已生效许可', CYAN),
        (7.0, '2026-10-08', '另一款 · 1/2 期 · 《新英格兰医学杂志》', '安全性为主 · 非确证疗效设计', AMBER),
        (10.5, '数字连同分母', '光敏感 6/10 · 行为测试 4/8（部分任务）', '戴着护目镜 · 不写成全体患者', CYAN),
        (13.5, '脚注', '任何司法辖区都没有上市许可', 'GS030 · 仍是申请/探索', AMBER),
    ]
    header(L, W, H, '临床边界 · 以公告与论文为准', '受理 ≠ 获批 · 探索 ≠ 确证', t, s)
    cur = cards[0]
    for c in cards:
        if phase >= c[0]:
            cur = c
    a = 1.0
    L.rrect((100 * s, 140 * s, 1180 * s, 420 * s), 14 * s, fill=(14, 20, 40), alpha=0.82)
    L.line([(100 * s, 140 * s), (100 * s, 420 * s)], fill=cur[4], width=5 * s, alpha=a)
    L.text((140 * s, 200 * s), cur[1], F(SANS_B, 20 * s), fill=cur[4], alpha=a, anchor='ls', tracking=2 * s)
    L.text((140 * s, 270 * s), cur[2], F(SANS_B, 28 * s), fill=CREAM, alpha=a, anchor='ls')
    L.text((140 * s, 340 * s), cur[3], F(SANS, 18 * s), fill=MUTED, alpha=a, anchor='ls')
    # progress dots
    for i, c in enumerate(cards):
        on = phase >= c[0]
        L.dot((200 * s + i * 180 * s, 480 * s), 7 * s, fill=c[4] if on else (60, 70, 100), alpha=0.9 if on else 0.4)
    footer_tick(L, W, H, t, s, 'C · 监管与数字')
    return grade(over(rgb, L.get()), seed=int(t * 24))

# ---------- SF23 limits + close ----------
def sf23(t, W, H):
    s = W / 1280; rgb = bg(W, H, t, CYAN, 0.4, 0.4)
    L = Layer(W, H)
    phase = t % 14.0
    if phase < 5.0:
        header(L, W, H, '边界停在已发表的事实', '脱敏 · 光必须送到细胞旁 · 部分且绑装置', phase, s)
        items = [
            ('限制 1', '持续光照 → ChR2 脱敏', '不能当成永不疲劳的门'),
            ('限制 2', '光得送到细胞旁边', '脑：光纤 · 眼：护目镜'),
            ('限制 3', '人体视觉：部分功能', '一条未获批 · 一条无上市许可'),
        ]
        for i, (k, a, b) in enumerate(items):
            y = 140 * s + i * 100 * s
            aa = ramp(phase, 0.4 + i * 0.7, 1.2 + i * 0.7)
            L.rrect((100 * s, y, 1180 * s, y + 80 * s), 8 * s, fill=(14, 20, 40), alpha=0.78 * aa)
            L.text((130 * s, y + 30 * s), k, F(SANS_B, 16 * s), fill=GOLD, alpha=aa, anchor='ls')
            L.text((280 * s, y + 30 * s), a, F(SANS_B, 20 * s), fill=CREAM, alpha=aa, anchor='ls')
            L.text((280 * s, y + 58 * s), b, F(SANS, 15 * s), fill=MUTED, alpha=aa, anchor='ls')
    elif phase < 9.0:
        p2 = phase - 5.0
        header(L, W, H, '做得到 / 做不到', '', p2, s)
        L.rrect((80 * s, 130 * s, 600 * s, 400 * s), 12 * s, fill=(14, 40, 30), alpha=0.75 * ramp(p2, 0.2, 0.8))
        L.rrect((640 * s, 130 * s, 1160 * s, 400 * s), 12 * s, fill=(40, 20, 20), alpha=0.75 * ramp(p2, 0.5, 1.1))
        L.text((340 * s, 180 * s), '做得到', F(SANS_B, 28 * s), fill=CYAN, alpha=ramp(p2, 0.3, 0.9), anchor='ms')
        L.text((340 * s, 260 * s), '实验里打开或关掉', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((340 * s, 300 * s), '选定细胞 · 推进成因果', F(SANS, 18 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((900 * s, 180 * s), '做不到', F(SANS_B, 28 * s), fill=AMBER, alpha=ramp(p2, 0.6, 1.2), anchor='ms')
        L.text((900 * s, 250 * s), '小鼠恐惧 ≠ 某人的人生', F(SANS, 17 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((900 * s, 295 * s), '部分视觉 ≠ 失明结束', F(SANS, 17 * s), fill=CREAM, alpha=0.9, anchor='ms')
    else:
        p3 = phase - 9.0
        header(L, W, H, '牵强的是当年的工程', '今天：实验方法 · 仍在审查的临床尝试', p3, s)
        L.text((W / 2, 260 * s), '光遗传学', F(SERIF_B, 64 * s), fill=CREAM, alpha=ramp(p3, 0.3, 1.2), anchor='ms', tracking=6 * s)
        L.line([(W / 2 - 160 * s, 310 * s), (W / 2 + 160 * s * ease_out(ramp(p3, 1.0, 2.2)), 310 * s)], fill=CYAN, width=2 * s, alpha=ramp(p3, 1.0, 1.8))
        L.text((W / 2, 360 * s), '这一期在这里结束', F(SANS, 20 * s), fill=MUTED, alpha=ramp(p3, 2.0, 2.8), anchor='ms')
        L.text((W / 2, 420 * s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 14 * s), fill=MUTED, alpha=ramp(p3, 2.5, 3.2) * 0.8, anchor='ms')
    footer_tick(L, W, H, t, s, 'D · 边界与收束')
    return grade(over(rgb, L.get()), seed=int(t * 24))


SCENES = {
    'SF12_neuron_select': (sf12, 6.0),
    'SF13_spike_causality': (sf13, 36.0),
    'SF14_orexin_q': (sf14, 6.0),
    'SF15_br_pump_channel': (sf15, 30.0),
    'SF16_chr_path': (sf16, 42.0),
    'SF17_credit_word': (sf17, 8.0),
    'SF18_invivo_dual': (sf18, 12.0),
    'SF19_engram': (sf19, 12.0),
    'SF20_retina_intro': (sf20, 6.0),
    'SF21_partial_vision': (sf21, 10.0),
    'SF22_regulatory': (sf22, 48.0),
    'SF23_limits_close': (sf23, 42.0),
}


def render_one(name):
    fn, dur = SCENES[name]
    n = int(round(dur * FPS))
    still_t = dur * 0.55
    png = f'{OUT}/{name}.png'
    mp4 = f'{OUT}/{name}.mp4'
    print(f'render {name} dur={dur}s frames={n}', flush=True)
    save(fn(still_t, 1280, 720), png)
    write_video(lambda i, fn=fn, dur=dur: fn(i / FPS, W, H), n, mp4, W, H, FPS)
    print(f'  done {png} {mp4}', flush=True)


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SCENES)
    for n in names:
        if n not in SCENES:
            raise SystemExit(f'unknown {n}')
        render_one(n)
    print('ALL_OK', len(names))
