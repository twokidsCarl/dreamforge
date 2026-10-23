"""SF10: realistic mouse on locked static ground (Carl style v1.3 direction).
Beads/lobes only for micro; mouse is photo-real fur, ground never crawls.
Matte tighten: kill studio floor plate / white fringe under paws.
$0 — local OpenCV/numpy/ffmpeg only.
"""
from __future__ import annotations
import math, os, subprocess
import cv2
import numpy as np

ROOT = '/workspace/e2work/v8'
G = f'{ROOT}/gen/'
OUT_MP4 = f'{ROOT}/styleframes/SF10_mouse_tripo.mp4'
OUT_PNG = f'{ROOT}/styleframes/SF10_mouse_tripo.png'
BEFORE = f'{ROOT}/styleframes/before_carl_style/SF10_mouse_tripo.mp4'
REVIEW = f'{ROOT}/review'
FAT = f'{G}vid/sf10_real20.mp4'
FPS, DUR = 24, 9.4
W, H = 960, 540
N = int(round(DUR * FPS)) + 2  # match prior 226
FAT_WH = (1176, 784)


def ease(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _largest(sil: np.ndarray) -> np.ndarray:
    n, lab, st, _ = cv2.connectedComponentsWithStats(sil.astype(np.uint8))
    if n <= 1:
        return sil.astype(np.uint8)
    return (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)


def segment_mouse(im_bgr: np.ndarray):
    """Studio gray bg -> tight soft alpha. Kills floor plate under paws (keeps body/paws)."""
    h, w = im_bgr.shape[:2]
    hsv = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2HSV)
    meanv = im_bgr.mean(2)

    bg = ((hsv[..., 1] < 35) & (hsv[..., 2] > 140)).astype(np.uint8)
    bg |= ((meanv > 185) & (hsv[..., 1] < 45)).astype(np.uint8)
    fg = 1 - bg
    mask = np.where(fg > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)
    mask[:4, :] = cv2.GC_BGD
    mask[-4:, :] = cv2.GC_BGD
    mask[:, :4] = cv2.GC_BGD
    mask[:, -4:] = cv2.GC_BGD
    cv2.ellipse(mask, (w // 2, int(h * 0.55)), (int(w * 0.22), int(h * 0.28)),
                0, 0, 360, cv2.GC_FGD, -1)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(im_bgr, mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    gcsil = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    gcsil = cv2.morphologyEx(gcsil, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    gcsil = _largest(gcsil)

    dark = (meanv < 105).astype(np.uint8)
    flesh = ((hsv[..., 1] >= 50) & (meanv > 65) & (meanv < 200) &
             ((hsv[..., 0] < 22) | (hsv[..., 0] > 155))).astype(np.uint8)
    body = ((dark | flesh) & gcsil).astype(np.uint8)
    body = cv2.morphologyEx(body, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
    body = _largest(body)

    xs = np.nonzero(body)[1]
    x_right = int(np.percentile(xs, 88)) if len(xs) else w // 2
    pale = ((hsv[..., 1] < 45) & (meanv > 100) & (meanv < 215) & (gcsil > 0)).astype(np.uint8)
    pale[:, :x_right] = 0
    pale = pale & cv2.dilate(body, np.ones((21, 21), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pale)
    tail = np.zeros_like(pale)
    for i in range(1, n):
        ww, hh, area = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT], st[i, cv2.CC_STAT_AREA]
        if (ww > 25 and hh < 150 and area < 100000) or (area < 8000 and hh < 100):
            tail[lab == i] = 1

    sil = np.maximum(body, tail)
    sil = cv2.dilate(sil, np.ones((3, 3), np.uint8), iterations=2)
    sil = (sil * gcsil).astype(np.uint8)

    # plate kill: very bright + very low sat; protect flesh/dark; lower bbox only
    flesh_dil = cv2.dilate(flesh, np.ones((7, 7), np.uint8))
    dark_dil = cv2.dilate(dark, np.ones((5, 5), np.uint8))
    plate = ((hsv[..., 1] < 38) & (meanv > 155)).astype(np.uint8)
    plate = plate * (1 - flesh_dil) * (1 - dark_dil) * (1 - tail)
    ys = np.nonzero(gcsil)[0]
    if len(ys):
        y_cut = int(ys.min() + 0.55 * (ys.max() - ys.min()))
        plate[:y_cut, :] = 0
    sil = sil * (1 - plate)
    sil = _largest(sil)

    ys = np.nonzero(sil)[0]
    if len(ys) == 0:
        return np.zeros((h, w), np.float32)
    y_bot, y_top = int(ys.max()), int(ys.min())
    yy = np.arange(h)[:, None]
    rel = np.clip((yy - y_top) / max(1, y_bot - y_top), 0, 1)
    for thr in (0.78, 0.90):
        er = cv2.erode(sil, np.ones((3, 3), np.uint8), iterations=1)
        sil = np.where(rel > thr, er, sil).astype(np.uint8)
    sil = _largest(sil)

    alpha = np.clip(cv2.GaussianBlur(sil.astype(np.float32), (0, 0), 0.7), 0, 1)
    alpha = np.where(
        (hsv[..., 1] < 35) & (meanv > 165) & (flesh_dil == 0) & (tail == 0) & (rel > 0.55),
        alpha * 0.15, alpha)
    return np.clip(cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 0.4), 0, 1)


def despill_rgb(im_bgr: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Pull bright low-sat fringe toward interior fur color."""
    hsv = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2HSV)
    meanv = im_bgr.mean(2)
    hard = cv2.erode((alpha > 0.7).astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2)
    if hard.any():
        mc = im_bgr[hard > 0].astype(np.float32).mean(0)
    else:
        mc = np.array([50.0, 50.0, 60.0], np.float32)
    rgb = im_bgr.astype(np.float32).copy()
    bright = (meanv > 125) & (hsv[..., 1] < 50) & (alpha > 0.05)
    for c in range(3):
        rgb[..., c] = np.where(bright, mc[c] * 0.7 + rgb[..., c] * 0.3, rgb[..., c])
    return rgb


def place_mouse(ground, mouse_rgba, cx, cy, scale, rot_deg=0.0):
    """Paste mouse (BGR+A float) onto ground at (cx,cy) with scale & rotation."""
    gh, gw = ground.shape[:2]
    mh, mw = mouse_rgba.shape[:2]
    M = cv2.getRotationMatrix2D((mw / 2, mh / 2), rot_deg, scale)
    M[0, 2] += cx - mw / 2
    M[1, 2] += cy - mh / 2
    warped = cv2.warpAffine(mouse_rgba, M, (gw, gh), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT)
    a = np.clip(warped[..., 3:4] / 255.0, 0, 1)
    a = np.clip((a - 0.08) / 0.84, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.5)
    if a.ndim == 2:
        a = a[..., None]
    rgb = warped[..., :3]
    # kill residual bright low-sat fringe in soft alpha (white halo) without cutting dark fur
    meanv = rgb.mean(2)
    # approx sat from BGR
    mx = rgb.max(2); mn = rgb.min(2)
    sat = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
    fringe = (a[..., 0] > 0.02) & (a[..., 0] < 0.92) & (meanv > 145) & (sat < 0.18)
    a = np.where(fringe[..., None], a * 0.08, a)
    sh = cv2.GaussianBlur(a, (0, 0), 6)
    sh2 = cv2.warpAffine(sh[..., 0], np.array([[1, 0, 3], [0, 1, 7]], np.float32), (gw, gh))
    if sh2.ndim == 2:
        sh2 = sh2[..., None]
    out = ground * (1 - 0.28 * sh2) * (1 - a) + rgb * a
    return out, a[..., 0]


def draw_fiber(img, head_xy, t, awake):
    """Vertical fiber + ferrule on head."""
    out = img.copy()
    x, y = int(head_xy[0]), int(head_xy[1])
    pts = []
    for i in range(0, y + 8, 2):
        wob = 1.2 * math.sin(i * 0.04 + t * 0.5)
        pts.append((int(x + wob), i))
    if len(pts) > 1:
        cv2.polylines(out, [np.array(pts, np.int32)], False, (18, 22, 28), 3, cv2.LINE_AA)
        cv2.polylines(out, [np.array(pts, np.int32)], False, (40, 55, 70), 1, cv2.LINE_AA)
    cv2.rectangle(out, (x - 5, y - 10), (x + 5, y + 4), (200, 200, 195), -1, cv2.LINE_AA)
    cv2.rectangle(out, (x - 7, y + 2), (x + 7, y + 8), (160, 160, 155), -1, cv2.LINE_AA)
    if awake > 0.3:
        glow = np.zeros_like(out, np.float32)
        cv2.circle(glow, (x, y), 18, (180, 140, 40), -1)
        glow = cv2.GaussianBlur(glow, (0, 0), 8)
        out = np.clip(out + glow * (0.25 * awake), 0, 255)
    return out


def make_mouse_layers():
    mouse = cv2.imread(G + 'mouse_ref.png')
    alpha = segment_mouse(mouse)
    rgb = despill_rgb(mouse, alpha)
    # harden alpha before crop
    a_hard = np.clip((alpha - 0.10) / 0.80, 0, 1)
    ys, xs = np.nonzero(a_hard > 0.08)
    y0, y1 = max(0, ys.min() - 14), min(mouse.shape[0], ys.max() + 14)
    x0, x1 = max(0, xs.min() - 14), min(mouse.shape[1], xs.max() + 14)
    crop = rgb[y0:y1, x0:x1]
    a = a_hard[y0:y1, x0:x1][..., None]
    rgba = np.concatenate([crop, a * 255], axis=2)
    asleep = rgba.copy()
    eh, ew = asleep.shape[:2]
    cv2.ellipse(asleep, (int(ew * 0.32), int(eh * 0.38)), (int(ew * 0.045), int(eh * 0.028)),
                -15, 0, 360, (40, 35, 35, 255), -1, cv2.LINE_AA)
    return rgba, asleep


def make_ground(tw, th):
    """Static bedding plate from sf10_clean, darkened cinematic grade."""
    g = cv2.imread(G + 'sf10_clean.png').astype(np.float32)
    base = cv2.resize(g, (tw, th), interpolation=cv2.INTER_AREA)
    yy = np.linspace(0, 1, th).astype(np.float32)[:, None, None]
    grade = 0.55 + 0.55 * np.clip((yy - 0.25) / 0.5, 0, 1)
    base = base * (0.75 + 0.35 * grade)
    yy2, xx2 = np.mgrid[0:th, 0:tw].astype(np.float32)
    cx, cy = tw / 2, th * 0.55
    r = np.sqrt(((xx2 - cx) / (tw * 0.7)) ** 2 + ((yy2 - cy) / (th * 0.7)) ** 2)
    vig = np.clip(1.15 - 0.45 * r, 0.55, 1.0)[..., None]
    return np.clip(base * vig, 0, 255)


def frame_at(t, ground, awake_rgba, sleep_rgba, fat=False):
    tw, th = (FAT_WH if fat else (W, H))
    wake = ease((t - 3.6) / 1.0)
    look = 0.0
    if t > 5.0:
        look = (12.0 * ease((t - 5.0) / 0.6) - 24.0 * ease((t - 6.2) / 0.7)
                + 12.0 * ease((t - 7.6) / 0.6))
    a = wake
    mouse = sleep_rgba * (1 - a) + awake_rgba * a
    breathe = 1.0 + 0.022 * math.sin(2 * math.pi * t / 1.7)
    base_scale = (0.55 if fat else 0.50) * (th / 540.0)
    scale = base_scale * breathe * (0.96 + 0.06 * wake)
    cx = tw * (0.52 - 0.01 * look / 8.0)
    cy = th * (0.62 - 0.02 * wake)
    rot = -6.0 * (1 - wake) + look * 0.35
    out, malpha = place_mouse(ground, mouse, cx, cy, scale, rot)
    head = (cx - 0.02 * tw * scale / base_scale, cy - 0.18 * th * scale / base_scale)
    out = draw_fiber(out, head, t, wake)
    return np.clip(out, 0, 255).astype(np.uint8), malpha


def write_video(path, frames, w, h, fps=FPS):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    p = subprocess.Popen(
        ['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
         '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
         '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', path],
        stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    p.wait()
    assert p.returncode == 0, path


def ground_roi_diff(frames, mouse_alphas=None):
    h, w = frames[0].shape[:2]
    mask = np.ones((h, w), np.uint8)
    mask[int(h * 0.25):int(h * 0.85), int(w * 0.28):int(w * 0.75)] = 0
    mask[int(h * 0.88):] = 0
    diffs = []
    for i in range(1, len(frames)):
        d = cv2.absdiff(frames[i], frames[i - 1]).astype(np.float32)
        diffs.append(float(d[mask > 0].mean()))
    return float(np.mean(diffs)), float(np.median(diffs))


def add_simple_overlays(img, t):
    """Chinese HUD with Noto CJK — no lobe panels pasted from old styleframe."""
    from PIL import Image, ImageDraw, ImageFont
    out = img.copy()
    h, w = out.shape[:2]
    s = w / 960.0
    base = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).convert('RGBA')
    L = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    try:
        font_b = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', int(18 * s), index=2)
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', int(15 * s), index=2)
        font_s = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', int(13 * s), index=2)
    except Exception:
        font_b = font = font_s = ImageFont.load_default()

    def card(xyxy, alpha=150):
        d.rounded_rectangle(xyxy, radius=int(10 * s), fill=(10, 14, 34, alpha))

    if t > 0.4:
        card((int(18 * s), int(16 * s), int(270 * s), int(78 * s)), 160)
        d.text((int(30 * s), int(26 * s)), '蓝光：一串串短脉冲', font=font_b, fill=(220, 230, 255, 255))
        pl = max(0.0, math.sin((t - 0.8) * 2 * math.pi * 1.25)) ** 4 if t > 0.8 else 0.15
        for i in range(10):
            bh = int((6 + 16 * pl * (1.0 if i % 2 == 0 else 0.35)) * s)
            x = int(32 * s + i * 18 * s)
            y1 = int(68 * s)
            d.rectangle((x, y1 - bh, x + int(8 * s), y1), fill=(80, 190, 255, 255))

    card((int(18 * s), int(h - 108 * s), int(455 * s), int(h - 16 * s)), 170)
    d.text((int(32 * s), int(h - 92 * s)), '2007 · 小鼠 · 食欲素神经元', font=font_b, fill=(235, 238, 248, 255))
    d.text((int(32 * s), int(h - 62 * s)), '光脉冲一来：从睡眠转入清醒的概率升高', font=font, fill=(200, 210, 230, 255))

    awake = t >= 3.7
    label = '醒来' if awake else '睡眠中'
    col = (60, 200, 255, 255) if awake else (160, 170, 190, 255)
    x0, y0 = int(w - 140 * s), int(h - 58 * s)
    card((x0, y0, int(w - 18 * s), int(h - 20 * s)), 180)
    d.ellipse((x0 + int(12 * s), y0 + int(12 * s), x0 + int(24 * s), y0 + int(24 * s)), fill=col)
    d.text((x0 + int(34 * s), y0 + int(10 * s)), label, font=font_b, fill=(240, 244, 255, 255))

    composed = Image.alpha_composite(base, L)
    return cv2.cvtColor(np.array(composed.convert('RGB')), cv2.COLOR_RGB2BGR)


def main():
    os.makedirs(REVIEW, exist_ok=True)
    os.makedirs(G + 'vid', exist_ok=True)
    # keep previous mp4 as before for compare if not already archived
    if os.path.exists(OUT_MP4) and not os.path.exists(BEFORE):
        os.makedirs(os.path.dirname(BEFORE), exist_ok=True)
        import shutil
        shutil.copy2(OUT_MP4, BEFORE)

    awake_rgba, sleep_rgba = make_mouse_layers()
    ground = make_ground(W, H)

    before_frames = []
    if os.path.exists(BEFORE):
        cap = cv2.VideoCapture(BEFORE)
        while True:
            ok, f = cap.read()
            if not ok:
                break
            before_frames.append(f)
        cap.release()
    before_stats = ground_roi_diff(before_frames) if before_frames else (None, None)

    frames = []
    mouse_motion = []
    prev_m = None
    for i in range(N):
        t = i / FPS
        fr, mal = frame_at(t, ground, awake_rgba, sleep_rgba, fat=False)
        fr = add_simple_overlays(fr, t)
        frames.append(fr)
        if prev_m is not None:
            mouse_motion.append(float(cv2.absdiff(
                (mal * 255).astype(np.uint8), (prev_m * 255).astype(np.uint8)).mean()))
        prev_m = mal

    after_stats = ground_roi_diff(frames)
    write_video(OUT_MP4, frames, W, H)
    still = frames[int(0.55 * (N - 1))]
    cv2.imwrite(OUT_PNG, still)
    # feet crop for review
    cv2.imwrite(f'{REVIEW}/_sf10_feet_after_matte.png', still[280:480, 300:700])

    ground_f = make_ground(*FAT_WH)
    fat_frames = []
    for i in range(N):
        t = i / FPS
        fr, _ = frame_at(t, ground_f, awake_rgba, sleep_rgba, fat=True)
        fat_frames.append(fr)
    write_video(FAT, fat_frames, FAT_WH[0], FAT_WH[1])

    cmp_path = f'{REVIEW}/SF10_ground_fix_before_after.mp4'
    if before_frames:
        n = min(len(before_frames), len(frames))
        cmp = []
        for i in range(n):
            a = cv2.resize(before_frames[i], (W, H))
            b = frames[i]
            aa, bb = a.copy(), b.copy()
            cv2.putText(aa, 'BEFORE', (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(bb, 'AFTER (matte tight)', (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 0), 2, cv2.LINE_AA)
            cmp.append(np.hstack([aa, bb]))
        write_video(cmp_path, cmp, W * 2, H)
    else:
        write_video(cmp_path, frames, W, H)

    note = f'{REVIEW}/SF10_ground_lock_note.md'
    with open(note, 'w') as f:
        f.write(
            '## SF10 ground lock + realistic mouse (matte tighten)\n\n'
            '- Photo `gen/mouse_ref.png` on static `gen/sf10_clean.png` bedding.\n'
            '- Matte: dark-fur + high-S flesh core; pale tail by shape; **kill low-S bright studio plate** '
            '(incl. soft shadow disk under paws); bottom-weighted choke + despill.\n'
            '- Ground plate identical every frame — no per-frame warp.\n'
            f'- Ground ROI frame-diff mean: before={before_stats[0]} → after={after_stats[0]} '
            f'(median {before_stats[1]} → {after_stats[1]}).\n'
            f'- Mouse-mask motion mean absdiff={float(np.mean(mouse_motion)) if mouse_motion else "n/a"}.\n'
            '- Script: `tools/sf10_lock_ground.py`. Feet check: `review/_sf10_feet_after_matte.png`.\n'
        )
    print('BEFORE_GROUND', before_stats)
    print('AFTER_GROUND', after_stats)
    print('MOUSE_MOTION', float(np.mean(mouse_motion)) if mouse_motion else None)
    print('WROTE', OUT_MP4, OUT_PNG, cmp_path, note, FAT)


if __name__ == '__main__':
    main()
