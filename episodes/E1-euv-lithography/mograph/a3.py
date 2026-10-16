"""A3 2D shots: three hard problems as cards (F1, F10), air eating the beam, and the light ledger
introduced on the right of the frame."""
import math
import random

from mograph import CYAN, INK, INK2, VIOLET, Canvas, ease, ease_out, fade, seg, shot

CARD = (30, 34, 48)


def card(c, cx, cy, flip, a, num, title=None, w=440, h=600):
    """A card that flips around its vertical axis: back shows the number, front the title."""
    sx = abs(math.cos(math.pi * flip))
    hw = w / 2 * max(0.02, sx)
    front = flip > 0.5
    c.rect((cx - hw, cy - h / 2, cx + hw, cy + h / 2), fill=CARD if not front else (40, 44, 62),
           outline=(70, 76, 100) if not front else VIOLET, width=3, a=a, radius=18)
    if sx > 0.3:
        if not front:
            c.text((cx, cy), str(num), int(160 * sx), (70, 76, 100), a, anchor="mm")
        elif title:
            c.text((cx - w / 2 + 40, cy + h / 2 - 40), f"难题 {num} / 3", 22, INK2, a * sx, anchor="lm")


@shot("A3_01")
def three_cards(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    c.text((960, 150), "三道难题", 72, INK, a * ease(seg(t, 0.2, 0.9)), anchor="mm", weight_glow=True)
    for k in range(3):
        card(c, 480 + 480 * k, 600, 0.0, a * ease(seg(t, 0.6 + 0.2 * k, 1.2 + 0.2 * k)), k + 1)
    return c.finish(glow_radius=10, glow_gain=0.7)


@shot("A3_02")
def problem1(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    flip = ease(seg(t, 0.2, 1.0))
    card(c, 960, 520, flip, a, 1, title=True, w=1500, h=640)
    if flip > 0.5:
        on = ease(seg(t, 0.9, 1.6))
        # a horizontal spectrum band with a dark gap at 13.5 nm
        x0, x1, y = 300, 1620, 560
        for i in range(132):
            x = x0 + (x1 - x0) * i / 132
            u = i / 132
            col = (int(120 + 120 * math.sin(6.28 * (u + 0.0))), int(120 + 120 * math.sin(6.28 * (u + 0.33))),
                   int(120 + 120 * math.sin(6.28 * (u + 0.66))))
            gap = 0.08 < u < 0.14
            c.rect((x, y - 50, x + 11, y + 50), fill=(10, 10, 14) if gap else tuple(max(0, v) for v in col),
                   a=a * on * (1.0 if gap else 0.55))
        c.text((x0 + (x1 - x0) * 0.11, y + 90), "13.5 nm", 26, VIOLET, a * on, anchor="mm")
        c.text((960, 330), "① 没有现成的 13.5 nm 强光源", 44, INK, a * on, anchor="mm", weight_glow=True)
        c.text((1640, 760), "（F1）", 20, INK2, a * on, anchor="rm")
    return c.finish(glow_radius=10, glow_gain=0.7)


@shot("A3_03")
def problem2(t, dur, W, H):
    c = Canvas(W, H, bg=(0, 0, 0))
    a = fade(t, 0.0, dur, dur, 0.3)
    rnd = random.Random(10)
    mol = [(rnd.uniform(300, 1800), rnd.uniform(380, 700)) for _ in range(140)]
    front = 200 + 1600 * ease_out(seg(t, 0.3, 4.2))
    hits = sum(1 for x, y in mol if x < front and abs(y - 540) < 60)
    level = math.exp(-hits / 9)
    # the beam fading as it is eaten
    prev = 200
    for x in range(200, int(front), 20):
        h_here = sum(1 for mx, my in mol if mx < x and abs(my - 540) < 60)
        lv = math.exp(-h_here / 9)
        c.line((prev, 540), (x, 540), (200, 170, 255), int(4 + 22 * lv), a * lv, glow=True)
        prev = x
    for (x, y) in mol:
        hit = x < front and abs(y - 540) < 60
        flash = max(0.0, 1 - (front - x) / 160) if hit else 0
        c.circle((x, y), 4 + 4 * flash, fill=(140, 150, 180) if not flash else (240, 220, 255), a=a * (0.5 + 0.5 * flash),
                 glow=flash > 0)
    c.text((960, 160), "② 几乎所有物质都吸收它，连空气也不例外", 40, INK, a, anchor="mm", weight_glow=True)
    c.text((1880, 1030), "示意 · F10", 18, INK2, a, anchor="rm")
    return c.finish(glow_radius=10, glow_gain=1.0)


@shot("A3_07")
def ledger_intro(t, dur, W, H):
    c = Canvas(W, H)
    a = fade(t, 0.0, dur, dur, 0.3)
    x, w, top, bot = 1700, 70, 160, 920
    draw = ease_out(seg(t, 0.2, 1.0))
    c.line((x + w / 2, bot), (x + w / 2, bot - (bot - top) * draw), INK2, 2, a)
    fill = ease(seg(t, 1.0, 2.4))
    if fill > 0:
        c.rect((x, bot - (bot - top) * fill, x + w, bot), fill=VIOLET, a=a * 0.85, glow=True, radius=8)
        c.rect((x, top, x + w, bot), outline=INK2, width=2, a=a, radius=8)
    c.text((x + w / 2, top - 50), "光的账本", 32, INK, a * draw, anchor="mm", weight_glow=True)
    # lightning icon at the base: electricity is where it starts
    bx, by = x + w / 2, bot + 60
    pts = [(bx - 8, by - 30), (bx + 12, by - 30), (bx + 2, by - 6), (bx + 16, by - 6), (bx - 10, by + 30), (bx - 2, by + 4),
           (bx - 16, by + 4)]
    c.d.polygon([(c.px(px), c.px(py)) for px, py in pts], fill=(250, 220, 120, int(255 * a * draw)))
    c.text((bx, by + 60), "起点：电", 24, INK2, a * draw, anchor="mm")
    # dim machine outline on the left and a dashed link from the light path's start
    c.rect((160, 360, 1100, 760), outline=(50, 56, 74), width=2, a=a * 0.8, radius=20)
    c.circle((300, 560), 14, fill=VIOLET, a=a, glow=True)
    link = ease(seg(t, 2.6, 3.6))
    for i in range(0, int(1380 * link), 30):
        c.line((300 + i, 560 + (bot - 40 - 560) * i / 1380), (300 + i + 16, 560 + (bot - 40 - 560) * (i + 16) / 1380),
               CYAN, 2, a)
    return c.finish(glow_radius=10, glow_gain=0.7)
