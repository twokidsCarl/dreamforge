#!/usr/bin/env python3
"""fix_v6 static plates + knowledge cards.
- Crick / laureates: full bust with ≥10% headroom, feathered into navy (note #4)
- knowledge cards: 中文大名醒目 + 英文 + 结构 (note #12, gate 2)
- bR one-protein membrane patch (B: 「蛋白只有这一种」)
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import sys
sys.path.insert(0, str(Path(__file__).parent))
from v6lib import draw_rich, font, GOLD, MINT, CYAN, AMBER, CREAM, PURPLE, INK, GEN, card_base

OUT = Path(__file__).parent / 'plates'
OUT.mkdir(exist_ok=True)
BG = (10, 20, 50)


def navy_bg(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w * 0.6) / w) ** 2 + ((yy - h * 0.35) / h) ** 2)
    base = np.array(BG, np.float32)
    img = base[None, None, :] * (1.15 - 0.55 * d[..., None])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')


def feather_paste(canvas, im, x, y, feather=60, bottom_open=True):
    im = im.convert('RGB')
    w, h = im.size
    m = np.ones((h, w), np.float32)
    ramp = np.linspace(0, 1, feather)
    m[:, :feather] *= ramp[None, :]
    m[:, -feather:] *= ramp[::-1][None, :]
    m[:feather, :] *= ramp[:, None]
    if not bottom_open:
        m[-feather:, :] *= ramp[::-1][:, None]
    mask = Image.fromarray((m * 255).astype(np.uint8), 'L')
    canvas.paste(im, (int(x), int(y)), mask)


def crick_plate():
    # 1728x972 working canvas (1.35x of 1280x720) so camera can push gently
    Wc, Hc = 1728, 972
    c = navy_bg(Wc, Hc)
    im = Image.open(GEN / 'r20_clean_crick.png')
    s = int(Hc * 0.86)               # bust height 86% → hair top ≈ 14% from top
    im = im.resize((s, s), Image.LANCZOS)
    feather_paste(c, im, Wc * 0.60 - s / 2, Hc - s, feather=70)
    c.save(OUT / 'crick_v6.png')


def laureates_plate():
    Wc, Hc = 1728, 972
    c = navy_bg(Wc, Hc)
    names = ['nagel', 'hegemann', 'deisseroth']
    tile = int(Hc * 0.56)
    gap = 40
    x0 = (Wc - 3 * tile - 2 * gap) / 2
    y = Hc * 0.17
    for i, n in enumerate(names):
        im = Image.open(GEN / f'r20_clean_{n}.png').resize((tile, tile), Image.LANCZOS)
        feather_paste(c, im, x0 + i * (tile + gap), y, feather=50, bottom_open=False)
    c.save(OUT / 'laureates_v6.png')
    # tile centres (fractions) for name labels
    return [((x0 + i * (tile + gap) + tile / 2) / Wc, (y + tile) / Hc) for i in range(3)]


# ---------------------------------------------------------------- chemistry drawing
def draw_retinal(d, ox, oy, L, color, width=4):
    """all-trans retinal skeletal formula. ring C1..C6, chain C7..C15, O. methyls on C1(x2), C5, C9, C13."""
    def P(a, b):
        return (ox + a, oy + b)
    r = L
    # hexagon with flat sides vertical (pointy top)
    ang0 = -90
    ring = [(r * math.cos(math.radians(ang0 + 60 * k)), r * math.sin(math.radians(ang0 + 60 * k))) for k in range(6)]
    # label ring atoms: index0 top=C1? choose: C6 = right-upper vertex (k=1), C1 = top (k=0), C5 = right-lower (k=2)
    C1, C6, C5, C4, C3, C2 = ring[0], ring[1], ring[2], ring[3], ring[4], ring[5]
    pts = [C1, C6, C5, C4, C3, C2]
    for k in range(6):
        a, b = pts[k], pts[(k + 1) % 6]
        d.line([P(*a), P(*b)], fill=color, width=width)
    # C5=C6 double bond (inner line)
    cx, cy = 0, 0
    def inner(a, b, f=0.18):
        ax, ay = a[0] + (cx - a[0]) * f, a[1] + (cy - a[1]) * f
        bx, by = b[0] + (cx - b[0]) * f, b[1] + (cy - b[1]) * f
        ax, ay = ax + (bx - ax) * 0.12, ay + (by - ay) * 0.12
        bx, by = bx + (ax - bx) * 0.12, by + (ay - by) * 0.12
        return [P(ax, ay), P(bx, by)]
    d.line(inner(C6, C5), fill=color, width=width - 1)
    # methyls: C1 gem-dimethyl (up-left & up-right), C5 methyl (down)
    def stub(a, ang, ln=0.85):
        b = (a[0] + r * ln * math.cos(math.radians(ang)), a[1] + r * ln * math.sin(math.radians(ang)))
        d.line([P(*a), P(*b)], fill=color, width=width)
        return b
    stub(C1, -125); stub(C1, -55)
    stub(C5, 90)
    # chain zigzag from C6 heading right; 9 atoms C7..C15
    chain = [C6]
    up = True
    x, y = C6
    for i in range(9):
        ang = -30 if up else 30
        x, y = x + r * math.cos(math.radians(ang)), y + r * math.sin(math.radians(ang))
        chain.append((x, y)); up = not up
    for i in range(len(chain) - 1):
        d.line([P(*chain[i]), P(*chain[i + 1])], fill=color, width=width)
    # double bonds C7=C8, C9=C10, C11=C12, C13=C14  → chain indices (1,2),(3,4),(5,6),(7,8)
    for i in (1, 3, 5, 7):
        a, b = chain[i], chain[i + 1]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        # offset toward the side away from zigzag
        nx, ny = -(b[1] - a[1]), (b[0] - a[0])
        nl = math.hypot(nx, ny); nx, ny = nx / nl, ny / nl
        sgn = 1 if a[1] > b[1] else -1
        off = 0.16 * r * sgn
        aa = (a[0] + nx * off + (b[0] - a[0]) * 0.14, a[1] + ny * off + (b[1] - a[1]) * 0.14)
        bb = (b[0] + nx * off - (b[0] - a[0]) * 0.14, b[1] + ny * off - (b[1] - a[1]) * 0.14)
        d.line([P(*aa), P(*bb)], fill=color, width=width - 1)
    # methyls on C9 (chain idx 3) and C13 (idx 7): point outward of zigzag
    for i in (3, 7):
        a = chain[i]
        ang = -90 if chain[i][1] < chain[i - 1][1] else 90
        stub(a, ang, 0.8)
    # C15 aldehyde: C15 = chain[9]; =O
    c15 = chain[9]
    ang = 30 if c15[1] < chain[8][1] else -30
    o = (c15[0] + r * 0.9 * math.cos(math.radians(ang)), c15[1] + r * 0.9 * math.sin(math.radians(ang)))
    d.line([P(*c15), P(*o)], fill=color, width=width)
    nx, ny = -(o[1] - c15[1]), (o[0] - c15[0]); nl = math.hypot(nx, ny)
    d.line([P(c15[0] + nx / nl * 0.16 * r, c15[1] + ny / nl * 0.16 * r),
            P(o[0] + nx / nl * 0.16 * r, o[1] + ny / nl * 0.16 * r)], fill=color, width=width - 1)
    f = font(int(r * 0.75), True)
    d.text(P(o[0] + 4, o[1] - r * 0.45), 'O', font=f, fill=(255, 110, 100, 255))
    return P(*C6), P(*chain[9])


def retinal_card():
    w, h = 600, 330
    im, d = card_base(w, h, GOLD)
    d.text((28, 16), '视黄醛', font=font(56), fill=GOLD + (255,))
    draw_rich(d, (222, 40), 'Retinal  ·  C_{20}H_{28}O', 22, CREAM + (255,))
    d.text((222, 70), '维生素 A 的醛 · 吸光的那一小段', font=font(18, False), fill=(200, 210, 225, 255))
    draw_retinal(d, 92, 205, 36, (255, 190, 110, 255), 4)
    d.text((28, h - 40), '共轭双键链吸收可见光 → 紫色', font=font(18, False), fill=MINT + (255,))
    im.save(OUT / 'card_retinal.png')


def br_card():
    w, h = 560, 210
    im, d = card_base(w, h, PURPLE)
    d.text((28, 14), '细菌视紫红质', font=font(46), fill=(206, 170, 255, 255))
    d.text((28, 82), 'Bacteriorhodopsin  ·  1973 命名', font=font(22, False), fill=CREAM + (255,))
    d.text((28, 120), '7 段螺旋跨膜 · 内含一个视黄醛', font=font(19, False), fill=(200, 210, 225, 255))
    draw_rich(d, (28, 152), '光驱动质子泵：一次闪光 → 搬一个 H^{+}', 19, MINT + (255,))
    im.save(OUT / 'card_br.png')


def orexin_card():
    w, h = 600, 260
    im, d = card_base(w, h, AMBER)
    d.text((28, 14), '食欲素', font=font(56), fill=(255, 176, 90, 255))
    d.text((222, 34), 'Orexin（下丘脑分泌素）', font=font(22, False), fill=CREAM + (255,))
    d.text((222, 66), '神经肽 · 食欲素 A 由 33 个氨基酸组成', font=font(18, False), fill=(200, 210, 225, 255))
    # peptide bead chain, 33 residues, two disulfide bridges
    pts = []
    x, y = 46, 160
    for i in range(33):
        pts.append((x, y))
        x += 15.5
        y = 160 + 16 * math.sin(i * 0.9)
    for i in range(32):
        d.line([pts[i], pts[i + 1]], fill=(255, 200, 140, 200), width=3)
    pal = [(255, 170, 70), (255, 140, 90), (240, 200, 110), (255, 120, 60)]
    for i, (px, py) in enumerate(pts):
        c = pal[i % 4]
        d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=c + (255,), outline=(90, 50, 20, 255))
    # disulfides Cys6–Cys12, Cys7–Cys14 (orexin-A)
    for a, b, off in ((5, 11, 30), (6, 13, 44)):
        (ax, ay), (bx, by) = pts[a], pts[b]
        d.line([(ax, ay), (ax, ay + off), (bx, by + off), (bx, by)], fill=YELLOWS + (255,), width=2)
    d.text((pts[5][0] + 10, pts[5][1] + 44), 'S–S', font=font(14), fill=YELLOWS + (255,))
    d.text((28, h - 38), '这群神经元分泌它 · 与清醒相关', font=font(18, False), fill=MINT + (255,))
    im.save(OUT / 'card_orexin.png')


YELLOWS = (255, 225, 110)


def chr2_card():
    w, h = 560, 190
    im, d = card_base(w, h, MINT)
    d.text((28, 14), '通道视紫红质-2', font=font(44), fill=(130, 235, 200, 255))
    d.text((28, 78), 'Channelrhodopsin-2  ·  ChR2', font=font(22, False), fill=CREAM + (255,))
    d.text((28, 116), '蓝光 → 视黄醛翻转 → 孔自己打开', font=font(19, False), fill=(200, 210, 225, 255))
    d.text((28, 146), '阳离子顺梯度流入 · 一步完成', font=font(19, False), fill=MINT + (255,))
    im.save(OUT / 'card_chr2.png')


def chlamy_card():
    w, h = 520, 190
    im, d = card_base(w, h, (140, 220, 110))
    d.text((28, 14), '衣藻', font=font(56), fill=(160, 230, 120, 255))
    d.text((170, 30), 'Chlamydomonas', font=font(24, False), fill=CREAM + (255,))
    d.text((170, 62), '单细胞绿藻', font=font(20, False), fill=(200, 210, 225, 255))
    d.text((28, 112), '两根鞭毛划水 · 一个橙红眼点', font=font(19, False), fill=(200, 210, 225, 255))
    d.text((28, 144), '朝光游：眼点附近的蛋白在感光', font=font(19, False), fill=MINT + (255,))
    im.save(OUT / 'card_chlamy.png')


def crick_card():
    w, h = 470, 170
    im, d = card_base(w, h, GOLD)
    d.text((26, 12), '弗朗西斯·克里克', font=font(40), fill=GOLD + (255,))
    d.text((26, 70), 'Francis Crick · 1916–2004', font=font(21, False), fill=CREAM + (255,))
    d.text((26, 106), 'DNA 双螺旋共同发现者', font=font(19, False), fill=(200, 210, 225, 255))
    d.text((26, 134), '晚年转向研究大脑', font=font(19, False), fill=(200, 210, 225, 255))
    im.save(OUT / 'card_crick.png')


def br_patch():
    """membrane patch with ONE protein type (bR row) — circle inset for 「蛋白只有这一种」."""
    src = Image.open(GEN / 'sf08e_relay.png').convert('RGB')
    Wd, Hd = src.size
    pump = src.crop((int(0.060 * Wd), int(0.285 * Hd), int(0.165 * Wd), int(0.565 * Hd)))
    lip = src.crop((int(0.655 * Wd), int(0.395 * Hd), int(0.765 * Wd), int(0.575 * Hd)))
    S = 420
    c = Image.new('RGB', (S, S), (16, 30, 72))
    # outside / inside tint
    dd = ImageDraw.Draw(c)
    dd.rectangle((0, S // 2 + 40, S, S), fill=(48, 24, 72))
    lw = int(lip.width * 0.9); lh = int(lip.height * 0.9)
    lip = lip.resize((lw, lh), Image.LANCZOS)
    yb = S // 2 - lh // 2 + 8
    for x in range(-lw, S + lw, lw):
        c.paste(lip, (x, yb))
    pw, ph = int(pump.width * 0.62), int(pump.height * 0.62)
    pump = pump.resize((pw, ph), Image.LANCZOS)
    pm = Image.new('L', pump.size, 0)
    # mask: drop the light squiggle; keep body via brightness/sat
    a = np.asarray(pump).astype(np.float32)
    sat = a.max(-1) - a.min(-1)
    m = ((sat > 45) & (a[..., 0] > 70) & (a[..., 2] > 110)).astype(np.float32)
    from scipy.ndimage import binary_closing, binary_fill_holes, gaussian_filter
    m = binary_fill_holes(binary_closing(m > 0, iterations=3)).astype(np.float32)
    m = gaussian_filter(m, 1.2)
    pm = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), 'L')
    for k, x in enumerate(range(-pw // 3, S, int(pw * 0.92))):
        c.paste(pump, (x, S // 2 - ph // 2 + 4), pm)
    circ = Image.new('L', (S, S), 0)
    ImageDraw.Draw(circ).ellipse((4, 4, S - 4, S - 4), fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(c, (0, 0), circ)
    ring = ImageDraw.Draw(out)
    ring.ellipse((2, 2, S - 2, S - 2), outline=(206, 170, 255, 255), width=4)
    out.save(OUT / 'br_patch.png')


def title_assets():
    lk = Image.open(Path('/workspace/eigenlens/brand/eigenlens_logo_locked/lockup_16x9.png')).convert('RGB')
    lk.resize((1280, 720), Image.LANCZOS).save(OUT / 'lockup_1280.png')
    mk = Image.open(Path('/workspace/eigenlens/brand/eigenlens_logo_locked/mark_1024.png')).convert('RGBA')
    mk.resize((96, 96), Image.LANCZOS).save(OUT / 'mark_96.png')


def nphr_card():
    w, h = 560, 200
    im, d = card_base(w, h, (232, 170, 70))
    d.text((28, 14), '嗜盐菌视紫红质', font=font(42), fill=(240, 190, 90, 255))
    d.text((28, 74), 'Halorhodopsin  ·  NpHR', font=font(22, False), fill=CREAM + (255,))
    d.text((28, 112), '古菌蛋白 · 黄光驱动的泵（不是通道）', font=font(19, False), fill=(200, 210, 225, 255))
    draw_rich(d, (28, 146), '把 Cl^{-} 泵进细胞 → 膜电位更负', 19, MINT + (255,))
    im.save(OUT / 'card_nphr.png')


def chrimson_card():
    w, h = 560, 190
    im, d = card_base(w, h, (220, 70, 80))
    d.text((28, 14), 'ChrimsonR', font=font(44), fill=(240, 110, 110, 255))
    d.text((290, 34), '红移的光控通道', font=font(24), fill=CREAM + (255,))
    d.text((28, 84), '对更长波长（橙红光）敏感', font=font(19, False), fill=(200, 210, 225, 255))
    d.text((28, 118), '2021 年用于人眼的那项研究', font=font(19, False), fill=(200, 210, 225, 255))
    d.text((28, 150), '不是 2005 年蓝光通道 ChR2 的改名', font=font(19, False), fill=MINT + (255,))
    im.save(OUT / 'card_chrimson.png')


if __name__ == '__main__':
    crick_plate()
    print('laureate label anchors', laureates_plate())
    retinal_card(); br_card(); nphr_card(); chrimson_card(); orexin_card(); chr2_card(); chlamy_card(); crick_card()
    br_patch(); title_assets()
    print('plates ->', OUT)
