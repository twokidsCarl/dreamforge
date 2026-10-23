#!/usr/bin/env python3
"""Diagram visual boost: progressive molecule/membrane/channel motifs on long type boards.
SF16/22/23 keep multibeat lengths; SF17/20 extended to kill short loops.
$0 pillow · caption-safe · no Blender. Science claims match prior BRIEF boards.
"""
from __future__ import annotations
import math, sys, time as _time
sys.path.insert(0, '/workspace/e2work/v8/tools')
from sf import *
import numpy as np

OUT = '/workspace/e2work/v8/styleframes'
W, H, FPS = 960, 540, 24
CAP = 0.80

def bg(W, H, t, accent=CYAN, ax=0.3, ay=0.4):
    ax2 = ax + 0.035 * math.sin(t * 0.1)
    ay2 = ay + 0.025 * math.cos(t * 0.08)
    rgb = np.zeros((H, W, 3), np.float32) + np.array(INK) / 255
    rgb = rgb + radial(W, H, W * ax2, H * ay2, W * 0.34, accent, 0.20 + 0.03 * math.sin(t * 0.65))
    rgb = rgb + radial(W, H, W * 0.78, H * 0.68, W * 0.26, GOLD, 0.06)
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
    a = 0.4 + 0.08 * math.sin(t * 1.2)
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

def draw_channel(L, cx, cy, r, t, col=CYAN, open_amt=0.6, s=1.0):
    """Stylized 7TM-ish channel: ring + pore + ions."""
    L.ring((cx, cy), r, fill=col, width=2.5 * s, alpha=0.85)
    L.ring((cx, cy), r * 0.55, fill=col, width=1.5 * s, alpha=0.45)
    # pore
    L.dot((cx, cy), r * 0.22 * (0.7 + 0.3 * open_amt), fill=CREAM, alpha=0.35 + 0.4 * open_amt)
    # ions flowing
    for i in range(5):
        u = (t * 0.35 + i / 5) % 1.0
        y = cy - r * 1.1 + u * r * 2.2
        x = cx + (i % 2 - 0.5) * r * 0.25
        L.dot((x, y), 3.5 * s, fill=GOLD, alpha=0.5 + 0.4 * open_amt * math.sin(u * math.pi))

def draw_membrane(L, y, W, t, s, col=(80, 100, 140)):
    L.line([(80 * s, y), (W - 80 * s, y)], fill=col, width=3 * s, alpha=0.85)
    # lipid ticks
    for i in range(14):
        x = 100 * s + i * 80 * s
        wob = 4 * s * math.sin(t * 1.5 + i)
        L.line([(x, y - 10 * s + wob), (x, y + 10 * s - wob)], fill=col, width=1.2 * s, alpha=0.45)


# =====================================================================
# SF16 ChR path · 120s · visual motif per beat
# =====================================================================
def sf16(t, W, H):
    s = W / 1280
    TOTAL = 120.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.5, 0.38)
    L = Layer(W, H)
    steps = [
        (0.0,  20.0, '衣藻朝光游', '眼点 · 谁在感光？', GOLD, 'algae'),
        (20.0, 40.0, '2002 · 通道视紫红质一', '卵母细胞 · 光 → 质子电流', AMBER, 'chr1'),
        (40.0, 60.0, '关键：光与孔在同一分子', '不必多步接力 · 一个基因', CYAN, 'one'),
        (60.0, 80.0, '2003 · 通道视紫红质二', '蓝光开阳离子 · 哺乳细胞可用', CYAN, 'chr2'),
        (80.0, 100.0, '持续光照会脱敏', '高峰→平台 · 要用短脉冲', AMBER, 'desen'),
        (100.0, 120.0, '2005 · 培养神经元', '蓝光脉冲对齐锋电位', GOLD, 'neuron'),
    ]
    header(L, W, H, '从衣藻到毫秒级开关', 'ChR1 → 一体分子 → ChR2 → 锋电位', min(tt, 2.0) + 1.0, s)
    # timeline rail
    L.line([(70 * s, 95 * s), (1210 * s, 95 * s)], fill=(50, 60, 90), width=2 * s, alpha=0.7)
    cur = steps[0]
    for i, (t0, t1, title, sub, col, kind) in enumerate(steps):
        x = 90 * s + i * 185 * s
        a = ramp(tt, t0, t0 + 0.6)
        L.dot((x, 95 * s), 6 * s, fill=col, alpha=max(a, 0.2))
        if a > 0.15:
            L.text((x, 112 * s), title.split('·')[0].strip()[:7], F(SANS, 10 * s), fill=MUTED, alpha=0.5 * a, anchor='ms')
        if t0 <= tt < t1:
            cur = (t0, t1, title, sub, col, kind)

    t0, t1, title, sub, col, kind = cur
    local = tt - t0
    # visual stage (caption-safe)
    stage_y1 = H * CAP - 70 * s
    L.rrect((60 * s, 130 * s, 1220 * s, stage_y1), 12 * s, fill=(12, 18, 36), alpha=0.72)

    cx, cy, R = 380 * s, (130 * s + stage_y1) / 2, 95 * s
    if kind == 'algae':
        # oval cell + eyespot chasing light
        L.ring((cx, cy), R, fill=(100, 160, 90), width=2.5 * s, alpha=0.8)
        L.ring((cx, cy), R * 0.55, fill=(80, 130, 70), width=1.5 * s, alpha=0.4)
        ang = local * 0.4
        ex = cx + R * 0.55 * math.cos(ang)
        ey = cy + R * 0.35 * math.sin(ang)
        L.dot((ex, ey), 10 * s, fill=GOLD, alpha=0.9)
        # light rays from right
        for i in range(5):
            y = cy - 60 * s + i * 30 * s
            L.line([(cx + R + 20 * s, y), (cx + R + 120 * s + 20 * s * math.sin(local + i), y)],
                   fill=GOLD, width=1.5 * s, alpha=0.35 + 0.25 * math.sin(local * 2 + i))
        L.text((cx, cy + R + 28 * s), '衣藻 · 眼点', F(SANS, 14 * s), fill=MUTED, alpha=0.85, anchor='ms')
    elif kind in ('chr1', 'chr2', 'one'):
        open_amt = 0.45 + 0.45 * (0.5 + 0.5 * math.sin(local * 1.2)) if kind != 'one' else 0.85
        draw_channel(L, cx, cy, R, local, col=col, open_amt=open_amt, s=s)
        draw_membrane(L, cy, W * 0.55, local, s)
        if kind == 'one':
            L.text((cx, cy - R - 18 * s), '光感受 + 孔 = 同一蛋白', F(SANS_B, 14 * s), fill=GOLD, alpha=0.9, anchor='ms')
        elif kind == 'chr1':
            L.text((cx, cy + R + 24 * s), 'ChR1 · 质子电流', F(SANS, 14 * s), fill=AMBER, alpha=0.9, anchor='ms')
        else:
            L.text((cx, cy + R + 24 * s), 'ChR2 · 阳离子', F(SANS, 14 * s), fill=CYAN, alpha=0.9, anchor='ms')
    elif kind == 'desen':
        # peak→plateau curve
        pts = []
        for i in range(50):
            u = i / 49
            x = 120 * s + u * 500 * s
            # peak then plateau
            peak = math.exp(-((u - 0.25) / 0.08) ** 2)
            plat = 0.35 * (1 / (1 + math.exp(-(u - 0.4) * 12)))
            y = stage_y1 - 40 * s - (peak * 140 + plat * 60) * s
            # scrubber
            if u < min(local / 18.0, 1.0):
                pts.append((x, y))
        if len(pts) > 1:
            L.line(pts, fill=AMBER, width=2.5 * s, alpha=0.95)
        L.text((370 * s, 160 * s), '持续光 · 脱敏', F(SANS_B, 16 * s), fill=AMBER, alpha=0.9, anchor='ms')
        L.text((200 * s, stage_y1 - 20 * s), '高峰', F(SANS, 12 * s), fill=MUTED, alpha=0.7, anchor='ms')
        L.text((520 * s, stage_y1 - 20 * s), '平台', F(SANS, 12 * s), fill=MUTED, alpha=0.7, anchor='ms')
    else:  # neuron
        # soma + axon + spikes
        L.ring((cx - 40 * s, cy), 50 * s, fill=CYAN, width=2.5 * s, alpha=0.85)
        L.dot((cx - 40 * s, cy), 14 * s, fill=CYAN, alpha=0.5)
        L.line([(cx + 10 * s, cy), (cx + 280 * s, cy)], fill=CYAN, width=2.5 * s, alpha=0.8)
        # traveling spikes synced to "blue pulses"
        for i in range(4):
            u = (local * 0.45 + i * 0.22) % 1.0
            x = cx + 20 * s + u * 250 * s
            pulse = math.exp(-((u - 0.5) / 0.08) ** 2) if False else abs(math.sin(u * math.pi))
            L.dot((x, cy - 18 * s * math.sin(u * math.pi)), 6 * s, fill=GOLD, alpha=0.6 + 0.35 * pulse)
        L.text((cx + 80 * s, cy + 50 * s), '蓝光脉冲 → 锋电位', F(SANS, 14 * s), fill=GOLD, alpha=0.9, anchor='ms')

    # right-side chip always
    chip(L, (700 * s, 150 * s, 1200 * s, 250 * s), title, sub, 1.0, col, s)
    chip(L, (700 * s, 270 * s, 1200 * s, stage_y1 - 10 * s),
         '微观插画示意', '结构示意 · 非定量比例', 0.9, MUTED, s)

    progress_rail(L, W, H, tt, TOTAL, s, 6, CYAN)
    footer_tick(L, W, H, tt, s, 'B · ChR 路径 · 分子/膜视觉拍')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


# =====================================================================
# SF22 regulatory · 94s · icon + fraction bars per card
# =====================================================================
def sf22(t, W, H):
    s = W / 1280
    TOTAL = 94.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.42, 0.34)
    L = Layer(W, H)
    cards = [
        (0.0,  18.0, '2026-09-09', 'BLA 已受理 · MCO-010 / MOGENRY', '公告写「如果获批」→ 当时尚未获批', GOLD, 'clipboard'),
        (18.0, 36.0, '第 52 / 76 周', '视力主要终点与关键次要终点', '申请方公告 · 不是已生效许可', CYAN, 'chart'),
        (36.0, 54.0, '2026-10-08', '另一款 · 1/2 期 · 《新英格兰医学杂志》', '安全性为主 · 非确证疗效设计', AMBER, 'paper'),
        (54.0, 74.0, '数字连同分母', '光敏感 6/10 · 行为测试 4/8（部分任务）', '戴着护目镜 · 不写成全体患者', CYAN, 'frac'),
        (74.0, 94.0, '脚注', '任何司法辖区都没有上市许可', 'GS030 · 仍是申请/探索', AMBER, 'stamp'),
    ]
    header(L, W, H, '临床边界 · 以公告与论文为准', '受理 ≠ 获批 · 探索 ≠ 确证', min(tt, 2.0) + 1.0, s)
    cur = cards[0]
    for c in cards:
        if tt >= c[0]:
            cur = c
    t0, t1, k, title, sub, col, kind = cur
    local = tt - t0
    y1 = H * CAP - 18 * s
    L.rrect((70 * s, 100 * s, 1210 * s, y1), 12 * s, fill=(14, 20, 40), alpha=0.82)
    L.line([(70 * s, 100 * s), (70 * s, y1)], fill=col, width=5 * s, alpha=0.95)

    # left visual panel
    vx, vy = 220 * s, (100 * s + y1) / 2
    if kind == 'clipboard':
        L.rrect((120 * s, 140 * s, 340 * s, y1 - 40 * s), 8 * s, fill=(20, 30, 55), alpha=0.9)
        L.rrect((140 * s, 160 * s, 320 * s, 200 * s), 4 * s, fill=col, alpha=0.7)
        for i in range(4):
            yy = 230 * s + i * 35 * s
            L.line([(150 * s, yy), (310 * s, yy)], fill=MUTED, width=2 * s, alpha=0.5 + 0.2 * math.sin(local + i))
        L.text((230 * s, y1 - 55 * s), '受理中', F(SANS_B, 16 * s), fill=GOLD, alpha=0.9, anchor='ms')
    elif kind == 'chart':
        # week bars 52/76
        base = y1 - 50 * s
        for i, (hgt, lab) in enumerate([(52 / 76, '52'), (1.0, '76')]):
            x = 140 * s + i * 110 * s
            bh = 180 * s * hgt
            L.rrect((x, base - bh, x + 70 * s, base), 4 * s, fill=col if i == 0 else (60, 70, 100), alpha=0.85)
            L.text((x + 35 * s, base + 20 * s), lab, F(SANS, 14 * s), fill=MUTED, alpha=0.85, anchor='ms')
        L.text((230 * s, 150 * s), '周次终点', F(SANS_B, 14 * s), fill=CYAN, alpha=0.9, anchor='ms')
    elif kind == 'paper':
        L.rrect((130 * s, 145 * s, 340 * s, y1 - 45 * s), 6 * s, fill=(30, 35, 55), alpha=0.9)
        L.text((235 * s, 190 * s), 'NEJM', F(SANS_B, 22 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((235 * s, 240 * s), '1 / 2 期', F(SANS, 16 * s), fill=CREAM, alpha=0.9, anchor='ms')
        L.text((235 * s, 290 * s), '安全性为主', F(SANS, 14 * s), fill=MUTED, alpha=0.85, anchor='ms')
    elif kind == 'frac':
        # 6/10 and 4/8 fraction visuals
        def frac_row(y, num, den, label, c):
            for i in range(den):
                x = 130 * s + i * 28 * s
                on = i < num
                L.rrect((x, y, x + 22 * s, y + 22 * s), 3 * s,
                        fill=c if on else (40, 50, 70), alpha=0.9 if on else 0.45)
            L.text((130 * s + den * 28 * s + 20 * s, y + 14 * s), f'{num}/{den} · {label}',
                   F(SANS, 13 * s), fill=MUTED, alpha=0.9, anchor='ls')
        frac_row(200 * s, 6, 10, '光敏感', CYAN)
        frac_row(280 * s, 4, 8, '行为(部分)', GOLD)
    else:  # stamp
        L.ring((vx, vy - 20 * s), 70 * s, fill=AMBER, width=3 * s, alpha=0.7 + 0.2 * math.sin(local))
        L.text((vx, vy - 20 * s), '无上市', F(SANS_B, 20 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((vx, vy + 40 * s), '许可', F(SANS_B, 18 * s), fill=AMBER, alpha=0.9, anchor='ms')

    # text
    L.text((420 * s, 160 * s), k, F(SANS_B, 18 * s), fill=col, alpha=0.95, anchor='ls', tracking=2 * s)
    L.text((420 * s, 220 * s), title, F(SANS_B, 22 * s), fill=CREAM, alpha=0.95, anchor='ls')
    L.text((420 * s, 280 * s), sub, F(SANS, 15 * s), fill=MUTED, alpha=0.9, anchor='ls')
    # dwell dots
    for j in range(6):
        u = (local * 0.08 + j / 6) % 1.0
        L.dot((450 * s + u * 650 * s, y1 - 35 * s), 2.5 * s, fill=col, alpha=0.35)

    for i, c in enumerate(cards):
        on = tt >= c[0]
        L.dot((200 * s + i * 180 * s, H * CAP - 6 * s), 5 * s, fill=c[5] if on else (60, 70, 100), alpha=0.9 if on else 0.35)

    progress_rail(L, W, H, tt, TOTAL, s, 5, GOLD)
    footer_tick(L, W, H, tt, s, 'C · 监管 · 图标+分母视觉拍')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


# =====================================================================
# SF23 limits + close · 100s · icon acts
# =====================================================================
def sf23(t, W, H):
    s = W / 1280
    TOTAL = 100.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, CYAN, 0.38, 0.38)
    L = Layer(W, H)

    if tt < 38.0:
        p = tt
        header(L, W, H, '边界停在已发表的事实', '脱敏 · 光必须送到细胞旁 · 部分且绑装置', min(p, 2.0) + 1.0, s)
        items = [
            (2.0,  '限制 1', '持续光照 → ChR2 脱敏', '不能当成永不疲劳的门', 'desen'),
            (14.0, '限制 2', '光得送到细胞旁边', '脑：光纤 · 眼：护目镜', 'fiber'),
            (26.0, '限制 3', '人体视觉：部分功能', '一条未获批 · 一条无上市许可', 'partial'),
        ]
        for i, (t0, k, a, b, kind) in enumerate(items):
            y = 110 * s + i * 95 * s
            if y + 80 * s > H * CAP: continue
            aa = 1.0 if p >= t0 else 0.0
            if aa <= 0: continue
            L.rrect((70 * s, y, 1210 * s, y + 80 * s), 8 * s, fill=(14, 20, 40), alpha=0.78)
            # mini icon
            ix, iy = 130 * s, y + 40 * s
            if kind == 'desen':
                draw_channel(L, ix, iy, 22 * s, p, AMBER, open_amt=0.25 + 0.2 * math.sin(p), s=s)
            elif kind == 'fiber':
                L.line([(ix, iy - 25 * s), (ix, iy + 25 * s)], fill=CYAN, width=3 * s, alpha=0.9)
                L.dot((ix, iy + 25 * s), 6 * s, fill=CYAN, alpha=0.85)
            else:
                for j in range(3):
                    L.rrect((ix - 20 * s + j * 18 * s, iy - 10 * s, ix - 8 * s + j * 18 * s, iy + 10 * s),
                            2 * s, outline=AMBER, width=1.2 * s, alpha=0.5 + 0.3 * (j == 1))
            L.text((190 * s, y + 28 * s), k, F(SANS_B, 14 * s), fill=GOLD, alpha=aa, anchor='ls')
            L.text((280 * s, y + 28 * s), a, F(SANS_B, 18 * s), fill=CREAM, alpha=aa, anchor='ls')
            L.text((280 * s, y + 55 * s), b, F(SANS, 14 * s), fill=MUTED, alpha=aa, anchor='ls')
            if p >= t0:
                L.rrect((70 * s, y, 1210 * s, y + 80 * s), 8 * s, outline=CYAN, width=1.2 * s,
                        alpha=0.2 + 0.2 * math.sin(p * 1.1 + i))
    elif tt < 68.0:
        p2 = tt - 38.0
        header(L, W, H, '做得到 / 做不到', '', min(p2, 2.0) + 1.0, s)
        L.rrect((70 * s, 105 * s, 600 * s, H * CAP - 20 * s), 12 * s, fill=(14, 40, 30), alpha=0.75)
        L.rrect((660 * s, 105 * s, 1210 * s, H * CAP - 20 * s), 12 * s, fill=(40, 20, 20), alpha=0.75)
        # check / x
        L.ring((200 * s, 160 * s), 22 * s, fill=CYAN, width=2.5 * s, alpha=0.9)
        L.text((200 * s, 165 * s), '✓', F(SANS_B, 22 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.ring((790 * s, 160 * s), 22 * s, fill=AMBER, width=2.5 * s, alpha=0.9)
        L.text((790 * s, 165 * s), '×', F(SANS_B, 22 * s), fill=AMBER, alpha=0.95, anchor='ms')
        L.text((335 * s, 160 * s), '做得到', F(SANS_B, 24 * s), fill=CYAN, alpha=0.95, anchor='ms')
        L.text((960 * s, 160 * s), '做不到', F(SANS_B, 24 * s), fill=AMBER, alpha=0.95, anchor='ms')
        goods = ['实验里打开或关掉', '选定细胞 · 推进成因果', '小鼠行为可被驱动']
        bads = ['小鼠恐惧 ≠ 某人的人生', '部分视觉 ≠ 失明结束', '受理 ≠ 上市许可']
        for i, g in enumerate(goods):
            L.text((335 * s, 230 * s + i * 45 * s), g, F(SANS, 15 * s), fill=CREAM,
                   alpha=ramp(p2, 2.0 + i * 4.0, 4.0 + i * 4.0), anchor='ms')
        for i, b in enumerate(bads):
            L.text((960 * s, 230 * s + i * 45 * s), b, F(SANS, 15 * s), fill=CREAM,
                   alpha=ramp(p2, 4.0 + i * 4.0, 6.0 + i * 4.0), anchor='ms')
    else:
        p3 = tt - 68.0
        header(L, W, H, '牵强的是当年的工程', '今天：实验方法 · 仍在审查的临床尝试', min(p3, 2.0) + 1.0, s)
        L.text((W / 2, 240 * s), '光遗传学', F(SERIF_B, 60 * s), fill=CREAM,
               alpha=ramp(p3, 0.5, 3.0), anchor='ms', tracking=6 * s)
        # channel motif under title
        draw_channel(L, W / 2, 340 * s, 40 * s, p3, CYAN, open_amt=0.7, s=s)
        line_w = 150 * s * ease_out(ramp(p3, 4.0, 10.0))
        L.line([(W / 2 - line_w, 300 * s), (W / 2 + line_w, 300 * s)], fill=CYAN, width=2 * s,
               alpha=ramp(p3, 4.0, 8.0))
        L.text((W / 2, 400 * s), '这一期在这里结束', F(SANS, 18 * s), fill=MUTED,
               alpha=ramp(p3, 14.0, 18.0), anchor='ms')
        L.text((W / 2, H * CAP - 25 * s), 'EigenLens 主观知识  ·  第 2 期', F(SANS, 13 * s), fill=MUTED,
               alpha=ramp(p3, 20.0, 24.0) * 0.85, anchor='ms')

    progress_rail(L, W, H, tt, TOTAL, s, 3, CYAN)
    footer_tick(L, W, H, tt, s, 'D · 边界与收束 · 图标视觉拍')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


# =====================================================================
# SF17 credit/word · EXTEND 8→22s (film ~22.7)
# =====================================================================
def sf17(t, W, H):
    s = W / 1280
    TOTAL = 22.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, GOLD, 0.48, 0.34)
    L = Layer(W, H)
    if tt < 12.0:
        p = tt
        header(L, W, H, '署名和授奖名单，不是同一份', '2005 论文 · 2026 新闻稿', min(p, 2.0) + 1.0, s)
        L.rrect((70 * s, 110 * s, 600 * s, H * CAP - 20 * s), 10 * s, fill=(14, 20, 40), alpha=0.8)
        L.rrect((660 * s, 110 * s, 1210 * s, H * CAP - 20 * s), 10 * s, fill=(14, 20, 40), alpha=0.8)
        L.text((335 * s, 150 * s), '论文署名', F(SANS_B, 20 * s), fill=MUTED, alpha=0.9, anchor='ms')
        L.text((335 * s, 220 * s), 'Boyden 第一作者', F(SANS_B, 22 * s), fill=CREAM,
               alpha=ramp(p, 1.0, 2.5), anchor='ms')
        L.text((335 * s, 270 * s), 'Deisseroth 通讯', F(SANS, 16 * s), fill=MUTED,
               alpha=ramp(p, 2.5, 4.0), anchor='ms')
        # decorative author dots
        for i in range(4):
            L.dot((200 * s + i * 90 * s, 340 * s), 8 * s, fill=CYAN if i < 2 else (60, 70, 100),
                  alpha=0.5 + 0.3 * ramp(p, 3.0, 5.0))
        L.text((935 * s, 150 * s), '2026 授奖', F(SANS_B, 20 * s), fill=MUTED, alpha=0.9, anchor='ms')
        for i, nm in enumerate(['Deisseroth', 'Hegemann', 'Nagel']):
            L.text((935 * s, 210 * s + i * 40 * s), nm, F(SANS_B, 20 * s), fill=GOLD,
                   alpha=ramp(p, 2.0 + i * 1.5, 3.5 + i * 1.5), anchor='ms')
        L.text((935 * s, 350 * s), '第四行空着', F(SANS, 14 * s), fill=MUTED, alpha=ramp(p, 8.0, 10.0), anchor='ms')
    else:
        p2 = tt - 12.0
        header(L, W, H, '2006 · optogenetics', '光学 + 遗传靶向：基因决定装谁，光决定何时拨', min(p2, 2.0) + 1.0, s)
        word = 'optogenetics'
        n = int(min(len(word), 1 + p2 * 2.2))
        L.text((W / 2, 250 * s), word[:n], F(SANS_B, 44 * s), fill=CREAM,
               alpha=ramp(p2, 0.2, 1.0), anchor='ms', tracking=3 * s)
        # light + gene icons
        L.ring((W / 2 - 180 * s, 360 * s), 28 * s, fill=CYAN, width=2 * s, alpha=ramp(p2, 3.0, 5.0))
        L.text((W / 2 - 180 * s, 365 * s), '光', F(SANS_B, 16 * s), fill=CYAN, alpha=ramp(p2, 3.0, 5.0), anchor='ms')
        L.ring((W / 2 + 180 * s, 360 * s), 28 * s, fill=GOLD, width=2 * s, alpha=ramp(p2, 4.0, 6.0))
        L.text((W / 2 + 180 * s, 365 * s), '基因', F(SANS_B, 14 * s), fill=GOLD, alpha=ramp(p2, 4.0, 6.0), anchor='ms')
        L.text((W / 2, H * CAP - 30 * s), '2006 · 《神经科学杂志》示意', F(SANS, 14 * s), fill=MUTED,
               alpha=ramp(p2, 6.0, 8.0), anchor='ms')
    progress_rail(L, W, H, tt, TOTAL, s, 2, GOLD)
    footer_tick(L, W, H, tt, s, 'B · 署名 / 一词 · 延展无短环')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


# =====================================================================
# SF20 retina · EXTEND 6→16s (film ~16.6)
# =====================================================================
def sf20(t, W, H):
    s = W / 1280
    TOTAL = 16.0
    tt = min(t, TOTAL - 0.05)
    rgb = bg(W, H, tt, AMBER, 0.52, 0.42)
    L = Layer(W, H)
    header(L, W, H, '眼睛走另一条路', '感光细胞死去 · 神经节细胞还可留着', min(tt, 2.0) + 1.0, s)
    layers = [
        (150, '感光细胞层', '逐渐变稀', (120, 120, 140), 0.25),
        (250, '双极等中间层', '', (90, 100, 130), 0.5),
        (350, '神经节细胞层', '可转导 · 幸存', CYAN, 0.95),
    ]
    for y, title, sub, col, dens in layers:
        if y * s + 60 * s > H * CAP: continue
        a = ramp(tt, 0.4, 1.5)
        L.rrect((160 * s, y * s, 1120 * s, (y + 70) * s), 8 * s, fill=(14, 20, 40), alpha=0.75 * a)
        L.line([(160 * s, y * s), (160 * s, (y + 70) * s)], fill=col, width=4 * s, alpha=a)
        L.text((190 * s, (y + 28) * s), title, F(SANS_B, 18 * s), fill=CREAM, alpha=a, anchor='ls')
        if sub:
            L.text((190 * s, (y + 52) * s), sub, F(SANS, 13 * s), fill=MUTED, alpha=a, anchor='ls')
        # density dots with slow life
        n = int(20 * dens)
        for i in range(n):
            pulse = 0.6 + 0.4 * math.sin(tt * 2.2 + i * 0.7) if dens > 0.7 else dens
            L.dot((680 * s + i * 18 * s, (y + 35) * s), 3.5 * s, fill=col, alpha=a * pulse)
    chip(L, (160 * s, H * CAP - 70 * s, 1120 * s, H * CAP - 8 * s),
         '若幸存细胞自己感光 → 后面通路也许还能被点着', '衔接护目镜 / ChrimsonR',
         ramp(tt, 6.0, 9.0), GOLD, s)
    progress_rail(L, W, H, tt, TOTAL, s, 3, AMBER)
    footer_tick(L, W, H, tt, s, 'C_07 · 视网膜剖面 · 延展无短环')
    return grade(over(rgb, L.get()), seed=int(tt * 24) % 100000)


SCENES = {
    'SF16_chr_path': (sf16, 120.0),
    'SF22_regulatory': (sf22, 94.0),
    'SF23_limits_close': (sf23, 100.0),
    'SF17_credit_word': (sf17, 22.0),
    'SF20_retina_intro': (sf20, 16.0),
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
        if n not in SCENES: raise SystemExit(f'unknown {n}')
        render_one(n)
    print('ALL_OK', len(names))
