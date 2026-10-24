#!/usr/bin/env python3
"""Cut9 styleframes: photoreal mouse (route A) + locked Goodsell mol, minimal HUD, no PIP."""
from __future__ import annotations
import os, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/workspace/e2work/v8')
OUT = ROOT / 'styleframes'
GEN = ROOT / 'gen'
SEQ = ROOT / 'cut9' / 'seqs'
GRAD = ROOT / 'cut9' / 'graded'
W, H, FPS = 1280, 720, 24
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
CREAM = (236, 230, 214)
CYAN = (90, 200, 230)

def F(path, size, idx=0):
    return ImageFont.truetype(path, int(size), index=idx)

def load_fit(path, w=W, h=H):
    im = Image.open(path).convert('RGB')
    im.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new('RGB', (w, h), (8, 10, 22))
    canvas.paste(im, ((w - im.width)//2, (h - im.height)//2))
    return canvas

def seq_frame(name, i, loop=True):
    d = SEQ / name
    files = sorted(d.glob('*.png'))
    if not files:
        raise FileNotFoundError(name)
    n = len(files)
    if loop:
        # ping-pong
        cycle = n * 2 - 2
        k = i % cycle
        if k >= n:
            k = cycle - k
        return load_fit(files[k])
    return load_fit(files[min(i, n-1)])

def kenburns(plate: Image.Image, i, n, zoom=1.08):
    """Slow push-in on a still plate."""
    z = 1.0 + (zoom - 1.0) * (i / max(n - 1, 1))
    pw, ph = plate.size
    cw, ch = int(pw / z), int(ph / z)
    # drift slightly right
    x0 = int((pw - cw) * 0.35 * (i / max(n - 1, 1)))
    y0 = int((ph - ch) * 0.25 * (i / max(n - 1, 1)))
    crop = plate.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    return crop

def badge(im, chapter='', title=''):
    """Minimal HUD: small top-left badge + optional short title first seconds."""
    d = ImageDraw.Draw(im, 'RGBA')
    # badge
    d.rounded_rectangle((18, 16, 178, 42), radius=6, fill=(10, 14, 28, 200))
    d.text((28, 20), 'EIGENLENS · 02', font=F(SANS_B, 14), fill=CREAM)
    if chapter:
        d.rounded_rectangle((188, 16, 188 + 12 + len(chapter)*13, 42), radius=6, fill=(20, 40, 70, 180))
        d.text((198, 20), chapter, font=F(SANS, 13), fill=CYAN)
    if title:
        # soft title band top-centre, translucent
        tw = min(900, 40 + len(title) * 22)
        x0 = (W - tw)//2
        d.rounded_rectangle((x0, 56, x0 + tw, 100), radius=8, fill=(8, 10, 22, 160))
        d.text((W//2, 78), title, font=F(SERIF_B, 26), fill=CREAM, anchor='mm')
    return im

def write_mp4(name, frames, poster_i=None):
    out = OUT / f'{name}.mp4'
    png = OUT / f'{name}.png'
    cmd = ['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
           '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast',
           '-crf','18','-pix_fmt','yuv420p', str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    if poster_i is None:
        poster_i = len(frames)//3
    for i, fr in enumerate(frames):
        arr = np.asarray(fr.convert('RGB'), dtype=np.uint8)
        if i == poster_i:
            fr.save(png)
        p.stdin.write(arr.tobytes())
    p.stdin.close()
    rc = p.wait()
    if rc != 0:
        raise RuntimeError(name)
    print(f'[SF] {name:22s} {len(frames)/FPS:.1f}s', flush=True)

def chain_seqs(plan, total_s, chapter='', title='', title_s=2.0):
    """plan: list of (seq_name, weight). Weights normalised to total_s."""
    n = int(round(total_s * FPS))
    wsum = sum(w for _, w in plan)
    frames = []
    # precompute segment lengths
    segs = []
    acc = 0
    for name, w in plan:
        ln = int(round(n * w / wsum))
        segs.append((name, ln))
        acc += ln
    # fix rounding
    if segs:
        segs[-1] = (segs[-1][0], segs[-1][1] + (n - acc))
    i_global = 0
    for name, ln in segs:
        for j in range(ln):
            fr = seq_frame(name, j, loop=True)
            ch = chapter if i_global < int(title_s * FPS) + 12 else ''
            ti = title if i_global < int(title_s * FPS) else ''
            frames.append(badge(fr, ch, ti))
            i_global += 1
    return frames

def plate_clip(path, total_s, chapter='', title='', title_s=2.0, zoom=1.06):
    plate = load_fit(path)
    n = int(round(total_s * FPS))
    frames = []
    for i in range(n):
        fr = kenburns(plate, i, n, zoom=zoom)
        ch = chapter if i < int(title_s * FPS) + 12 else ''
        ti = title if i < int(title_s * FPS) else ''
        frames.append(badge(fr, ch, ti))
    return frames

def multi_plate(items, total_s, chapter='', title=''):
    """items: list of (path, weight)."""
    n = int(round(total_s * FPS))
    wsum = sum(w for _, w in items)
    frames = []
    i_global = 0
    for path, w in items:
        ln = max(1, int(round(n * w / wsum)))
        plate = load_fit(path)
        for j in range(ln):
            if i_global >= n:
                break
            fr = kenburns(plate, j, ln, zoom=1.05)
            ch = chapter if i_global < 36 else ''
            ti = title if i_global < 48 else ''
            frames.append(badge(fr, ch, ti))
            i_global += 1
    while len(frames) < n:
        frames.append(frames[-1])
    return frames[:n]

def main():
    OUT.mkdir(exist_ok=True)
    # backup key ones
    bak = OUT / f'before_cut9'
    bak.mkdir(exist_ok=True)
    for n in ['SF01_open_title','SF10_mouse_tripo','SF18_invivo_dual','SF19_engram']:
        for ext in ('.mp4','.png'):
            src = OUT / f'{n}{ext}'
            if src.exists():
                os.rename(src, bak / f'{n}{ext}') if not (bak/f'{n}{ext}').exists() else None

    # SF01 — Goodsell tissue, minimal title
    write_mp4('SF01_open_title', chain_seqs([('sf01', 1)], 5.0, '开场', '用光，只动某一类神经元', 3.0))

    # Portraits / early — plates only (no mouse)
    write_mp4('SF02_1979_request', plate_clip(GEN/'sf06t_neuron.png', 4.0, '1979', '理想的信号，也许是光'))
    write_mp4('SF03_microbe_clues', plate_clip(GEN/'sf03e_microbes.png', 8.0, '线索', '微生物膜上的光驱动蛋白'))
    # Crick / nobel — use existing gen portraits if present
    crick = next((GEN/p for p in ['sf04h_crick.png','sf04_crick.png','r18_crick_small.png'] if (GEN/p).exists()), GEN/'sf06t_neuron.png')
    write_mp4('SF04_crick_quote', plate_clip(crick, 11.0, '设想', '用光去拨动某一类神经元'))
    # nobel trio — cycle available portrait plates
    portraits = [GEN/p for p in ['sf05p_deisseroth.png','sf05p_hegemann.png','sf05p_nagel.png',
                                  'r18_small_hegemann.png'] if (GEN/p).exists()]
    if not portraits:
        portraits = [GEN/'sf09e_chr2.png']
    items = [(p, 1) for p in portraits[:3]] or [(GEN/'sf09e_chr2.png', 1)]
    write_mp4('SF05_nobel_portraits', multi_plate(items, 11.0, '2026', '诺贝尔生理学或医学奖'))

    write_mp4('SF06_switch_diagram', plate_clip(GEN/'sf09e_chr2.png', 9.0, '开关', '一枚能用光拨动的开关'))
    write_mp4('SF07_main_title', plate_clip(GEN/'sf09e_chr2.png', 7.0, '片名', '《光遗传学》', 4.0))
    write_mp4('SF12_neuron_select', plate_clip(GEN/'sf06t_neuron.png', 10.0, '原理', '只让某一类神经元打开或关掉'))
    write_mp4('SF13_spike_causality', plate_clip(GEN/'sf06t_neuron.png', 20.0, '因果', '相关不够，要能推动那一类细胞'))
    write_mp4('SF08_early_attempts', plate_clip(GEN/'sf08e_relay.png', 16.0, '早期', '多步接力达不到毫秒'))
    write_mp4('SF09_chr2_channel', plate_clip(GEN/'sf09e_chr2.png', 8.0, 'ChR2', '光一到，门就动'))
    # SF14 orexin — photoreal sleep→wake
    write_mp4('SF14_orexin_q', chain_seqs([('sleep', 1), ('side', 1), ('front', 1)], 16.0, '2007', '光纤蓝光：睡眠 → 清醒'))
    # SF10 hero mouse
    write_mp4('SF10_mouse_tripo', chain_seqs([('sleep', 1), ('sideA', 1.2), ('side', 1), ('front', 1), ('oh', 0.8)], 15.0, '活体', '下丘脑食欲素神经元 · 蓝光唤醒'))
    write_mp4('SF15_br_pump_channel', multi_plate([(GEN/'sf03e_microbes.png', 1), (GEN/'sf08e_relay.png', 1), (GEN/'sf09e_chr2.png', 1)], 30.0, '泵与通道', '泵推离子，通道是孔'))
    write_mp4('SF16_chr_path', multi_plate([(GEN/'sf03e_microbes.png', 1), (GEN/'sf09e_chr2.png', 2), (GEN/'sf08e_relay.png', 1)], 40.0, '通道视紫红质', '接光与放行，在同一个分子里'))
    # credit
    write_mp4('SF17_credit_word', multi_plate(items, 22.0, '命名', '光遗传学'))
    # SF18 invivo — photoreal cage behaviour, shortened
    write_mp4('SF18_invivo_dual', chain_seqs([('oh', 1), ('side', 1), ('front', 1), ('yellow', 1), ('close', 0.8), ('sideA', 1)], 30.0, '活体', '蓝开 · 黄关'))
    # SF19 engram
    write_mp4('SF19_engram', chain_seqs([('oh', 1), ('side', 1), ('front', 1), ('sideA', 1)], 30.0, '记忆', '海马齿状回 · 虚假恐惧记忆'))
    # retina path — use available plates
    retina = GEN/'sf09e_chr2.png'
    for cand in ['sf20_retina.png','sf11_goggles.png','sf09e_chr2.png']:
        if (GEN/cand).exists():
            retina = GEN/cand; break
    write_mp4('SF20_retina_intro', plate_clip(retina, 16.0, '视网膜', '让幸存的神经节细胞自己感光'))
    gog = next((GEN/p for p in ['sf11_goggles.png','sf11e_goggles.png'] if (GEN/p).exists()), retina)
    write_mp4('SF11_eye_goggles', plate_clip(gog, 24.0, '护目镜', '基因 + 工程护目镜'))
    write_mp4('SF21_partial_vision', plate_clip(gog, 20.0, '部分恢复', '戴上才能看见 · 摘下即无'))
    write_mp4('SF22_regulatory', plate_clip(GEN/'sf09e_chr2.png', 40.0, '监管', '受理 ≠ 获批 · 连同分母一起说'))
    write_mp4('SF23_limits_close', plate_clip(GEN/'sf06t_neuron.png', 45.0, '边界', '做得到与做不到'))

if __name__ == '__main__':
    main()
