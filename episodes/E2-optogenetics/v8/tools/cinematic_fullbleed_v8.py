#!/usr/bin/env python3
"""E2 v8 Full-Bleed 16:9 Cinematic & Multi-Camera 3D Builder.
Breaks the 89.0 '2D static KB + left-box/right-chip' ceiling:
1. SF10 (19.0s): 100% continuous 4-camera 3D animation (sf10_gpu -> m6 sleep-to-wake walk -> m5 close walk -> m4/envA cage walk), ZERO static hold.
2. SF18 (96.0s) & SF19 (88.0s): True 3D experimental cage multi-cam sequences (envA transparent acrylic cage, envB conditioning grid cage, nphr 590nm yellow-light inhibition, m6/m5/m4 3D walking mouse).
3. All hero & narrative chapters (SF01, 02, 03, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
   16:9 full-bleed widescreen framing + cross-scale magnifier insets (micro Goodsell <-> macro 3D photoreal) + lightweight translucent HUD overlays.
   Zero 'deferred' or internal production notes. Caption-safe above 0.80H.
"""
from __future__ import annotations
import os, sys, glob, math, time, shutil, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 960, 540, 24
CAP_Y = int(H * 0.79)  # 426px — strictly above bottom 100px (720p) subtitle bar

# Carl HARD (cut7 postmortem): cross-scale PIP + dense lower-left cards turned every
# SF into a PPT template and inflated the (now-void) 5-axis self-score. Default OFF.
# Cross-scale PIP may be re-enabled only for 1–2 true molecule↔in-vivo contrast beats.
ENABLE_CROSS_SCALE_PIP = False
# Cut8: molecular heroes must be Goodsell / SF08e·SF09e illustration language.
# True-3D mol_retina_3d sequences are NOT allowed as molecular main picture.
# Keep true 3D only for macro mouse/cage. F6: do not pad runtime with 6 long 3D mol seqs.
USE_TRUE3D_MOLECULAR = False
# Lower-left info cards: only at chapter open (first ~12% of each SF), not every frame.
ENABLE_DENSE_LOWER_HUD = False
CHAPTER_OPEN_FRAC = 0.12
_HUD_CHAPTER_OPEN = False

ROOT = '/workspace/e2work/v8'
OUT_DIR = f'{ROOT}/styleframes'
GEN_DIR = f'{ROOT}/gen'
REND_DIR = f'{ROOT}/renders'

SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SANS_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

INK = (11, 16, 34)
CREAM = (244, 239, 230)
GOLD = (233, 184, 92)
CYAN = (63, 169, 255)
AMBER = (255, 180, 67)
MUTED = (165, 178, 205)

_FONT_CACHE = {}
def F(path, size, idx=2):
    k = (path, int(size), idx)
    if k not in _FONT_CACHE:
        _FONT_CACHE[k] = ImageFont.truetype(path, int(size), index=idx)
    return _FONT_CACHE[k]

def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)

def ramp(t: float, a: float, b: float) -> float:
    return ease((t - a) / (b - a)) if b > a else float(t >= a)

# Precomputed vignette & grain ring buffer for fast 24fps grading
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_VIG_MASK = (1.0 - 0.30 * (((_XX / W - 0.5) ** 2 + (_YY / H - 0.5) ** 2) / 0.5))[..., None].astype(np.float32)
_LIFT = np.array([0.035, 0.050, 0.105], dtype=np.float32)
_RNG = np.random.default_rng(42)
_GRAIN_RING = [_RNG.normal(0.0, 0.012, (H, W, 1)).astype(np.float32) for _ in range(24)]

# Top & bottom subtle cinematic scrims so HUD text is always legible over full-bleed 16:9 shots
_SCRIM = np.ones((H, W, 1), dtype=np.float32)
for y in range(88):
    _SCRIM[y, :, 0] = 0.42 + 0.58 * (y / 88.0)
for y in range(int(H * 0.58), H):
    u = (y - int(H * 0.58)) / max(1, H - int(H * 0.58))
    _SCRIM[y, :, 0] = min(float(_SCRIM[y, 0, 0]), 1.0 - 0.52 * (u ** 1.3))

# Fast uint8 vignette & grain LUT
_VIG_SCRIM_U16 = np.clip(_VIG_MASK * _SCRIM * 256.0, 0, 256).astype(np.uint16)
_LIFT_U8 = np.array([9, 12, 24], dtype=np.uint16)

def fast_grade(rgb_u8: np.ndarray, frame_idx: int) -> np.ndarray:
    # Already has scrim applied during multi_cam_bg
    return rgb_u8

# ---- Load 3D Animated Frame Sequences & High-Res Plates ----
SEQS: dict[str, list[np.ndarray]] = {}
PLATES: dict[str, np.ndarray] = {}

def _load_img_rgb(path: str, tw: int = W, th: int = H) -> np.ndarray:
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    if im.shape[1] != tw or im.shape[0] != th:
        # aspect-fill crop to 16:9 tw x th
        h, w = im.shape[:2]
        scale = max(tw / w, th / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        x0 = (nw - tw) // 2
        y0 = (nh - th) // 2
        im = resized[y0:y0 + th, x0:x0 + tw]
    return im

def _load_seq_dir(pattern: str, pingpong: bool = False) -> list[np.ndarray]:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(pattern)
    frames = [_load_img_rgb(f, W, H) for f in files]
    if pingpong and len(frames) > 2:
        frames = frames + frames[-2:0:-1]
    return frames

def _load_vid_seq(path: str, max_frames: int = 140) -> list[np.ndarray]:
    cap = cv2.VideoCapture(path)
    frames = []
    while len(frames) < max_frames:
        ok, im = cap.read()
        if not ok:
            break
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        if im.shape[1] != W or im.shape[0] != H:
            h, w = im.shape[:2]
            scale = max(W / w, H / h)
            nw, nh = int(round(w * scale)), int(round(h * scale))
            resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
            x0, y0 = (nw - W) // 2, (nh - H) // 2
            im = resized[y0:y0 + H, x0:x0 + W]
        frames.append(im)
    cap.release()
    return frames

def init_assets():
    if SEQS:
        return
    print('Loading 3D sequences and high-res plates into RAM...', flush=True)
    # V2 Darboux-Fur 3D Mouse & Cage Sequences (zero orange dot, zero bald patches, ground-locked paws!)
    SEQS['sf10_gpu'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/sf10_camA_*.png', pingpong=False)
    SEQS['m6'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/sf10_camB_*.png', pingpong=False)
    SEQS['m5'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/sf10_camC_*.png', pingpong=False)
    SEQS['m4'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/cage_comm_*.png', pingpong=True)
    SEQS['envA'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/cage_envA_*.png', pingpong=True)
    SEQS['envB'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/cage_envB_*.png', pingpong=True)
    SEQS['nphr'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/cage_nphr_*.png', pingpong=True)
    SEQS['comm'] = _load_seq_dir(f'{REND_DIR}/mouse_v2_seqs/cage_comm_*.png', pingpong=True)
    # True-3D mol sequences only if explicitly re-enabled (Cut8 default: illustration plates)
    if USE_TRUE3D_MOLECULAR:
        SEQS['microbe_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/microbe_3d_*.png', pingpong=True)
        SEQS['chr2_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/chr2_3d_*.png', pingpong=True)
        SEQS['br_pump_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/br_pump_3d_*.png', pingpong=True)
        SEQS['nphr_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/nphr_3d_*.png', pingpong=True)
        SEQS['retina_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/retina_3d_*.png', pingpong=True)
        SEQS['hippo_cone_3d'] = _load_seq_dir(f'{REND_DIR}/mol_retina_3d/hippo_cone_3d_*.png', pingpong=True)
    SEQS['wave01'] = _load_vid_seq(f'{GEN_DIR}/vid/sf01_wave.mp4', 120)
    SEQS['swim03'] = _load_vid_seq(f'{GEN_DIR}/vid/sf03_swim.mp4', 120)
    SEQS['real20'] = _load_vid_seq(f'{GEN_DIR}/vid/sf10_real20.mp4', 226)

    # Load larger-than-960x540 plates at 1120x630 for smooth sub-pixel camera drift
    PW, PH = 1120, 630
    for k, p in [
        ('brain', f'{GEN_DIR}/sf07k_brain.png'),
        ('orexin', f'{GEN_DIR}/sf10_orexin.png'),
        ('neuron', f'{GEN_DIR}/sf06t_neuron.png'),
        ('microbes', f'{GEN_DIR}/sf03e_microbes.png'),
        ('relay', f'{GEN_DIR}/sf08f_relay.png'),
        ('relay_b', f'{GEN_DIR}/sf08e_relay.png'),
        ('chr2', f'{GEN_DIR}/sf09e_chr2.png'),
        ('chr2_goodsell', f'{GEN_DIR}/sf09_chr2_goodsell.png'),
        ('chr2_noret', f'{GEN_DIR}/sf09f_noret.png'),
        ('eye', f'{GEN_DIR}/sf11_eye.png'),
        ('eye_b', f'{GEN_DIR}/sf11b_eye.png'),
        ('eye_c', f'{GEN_DIR}/sf11c_eye.png'),
        ('eye_d', f'{GEN_DIR}/sf11d_eye.png'),
        ('goggles', f'{GEN_DIR}/sf11_goggles.png'),
        ('eye_inset', f'{GEN_DIR}/sf11_inset.png'),
        ('crick', f'{GEN_DIR}/r20_clean_crick.png'),
        ('deisseroth', f'{GEN_DIR}/r20_clean_deisseroth.png'),
        ('hegemann', f'{GEN_DIR}/r20_clean_hegemann.png'),
        ('nagel', f'{GEN_DIR}/r20_clean_nagel.png'),
        ('crowd', f'{GEN_DIR}/sf02c_crowd.png'),
        ('awake_side', f'{REND_DIR}/sf18_19_stills/mouse_awake_side.png'),
        ('sleep_side', f'{REND_DIR}/sf18_19_stills/mouse_sleep_side.png'),
        ('awake_tq', f'{REND_DIR}/sf18_19_stills/mouse_awake_threeq.png'),
        ('sleep_tq', f'{REND_DIR}/sf18_19_stills/mouse_sleep_threeq.png'),
    ]:
        if os.path.isfile(p):
            PLATES[k] = _load_img_rgb(p, PW, PH)
    print(f'Loaded {len(SEQS)} 3D/video sequences and {len(PLATES)} plates.', flush=True)

def sample_seq(name: str, t_local: float, speed: float = 1.0, reverse: bool = False) -> np.ndarray:
    seq = SEQS[name]
    n = len(seq)
    f = (t_local * FPS * speed)
    # ping-pong across sequence if longer than n frames so there is never a hard jump
    cycle = 2 * n - 2 if n > 2 else n
    idx_f = f % cycle
    if idx_f >= n:
        idx_f = cycle - idx_f
    if reverse:
        idx_f = (n - 1) - idx_f
    i0 = int(math.floor(idx_f)) % n
    i1 = min(i0 + 1, n - 1)
    frac = idx_f - math.floor(idx_f)
    if frac < 1e-3 or i0 == i1:
        return seq[i0].copy()
    return cv2.addWeighted(seq[i0], 1.0 - frac, seq[i1], frac, 0.0)

def sample_plate(name: str, t_local: float, span: float, pan_x: float = 0.03, pan_y: float = 0.02, zoom: float = 0.04) -> np.ndarray:
    img = PLATES[name]
    ph, pw = img.shape[:2]
    u = min(max(t_local / max(span, 1e-5), 0.0), 1.0)
    u_smooth = ease(u)
    s = max(W / pw, H / ph) * (1.02 + zoom * u_smooth)
    cx = (0.5 + pan_x * (u_smooth - 0.5)) * pw
    cy = (0.5 + pan_y * math.sin(u * math.pi)) * ph
    M = np.array([[s, 0.0, W / 2.0 - s * cx], [0.0, s, H / 2.0 - s * cy]], dtype=np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def sample_source(src_Spec: tuple, t_local: float, span: float) -> np.ndarray:
    kind, key = src_Spec[0], src_Spec[1]
    if kind == 'seq':
        spd = src_Spec[2] if len(src_Spec) > 2 else 1.0
        rev = src_Spec[3] if len(src_Spec) > 3 else False
        return sample_seq(key, t_local, speed=spd, reverse=rev)
    else:
        px = src_Spec[2] if len(src_Spec) > 2 else 0.03
        zm = src_Spec[3] if len(src_Spec) > 3 else 0.04
        return sample_plate(key, t_local, span, pan_x=px, zoom=zm)

def multi_cam_bg(beats: list[tuple], t: float, fade_dur: float = 0.40) -> tuple[np.ndarray, int, float, float]:
    """Evaluate full-bleed 16:9 multi-camera timeline with smooth cross-dissolves between beats."""
    active_idx = 0
    for i, b in enumerate(beats):
        if b[0] <= t < b[1]:
            active_idx = i
            break
        if t >= b[0]:
            active_idx = i
    b = beats[active_idx]
    t0, t1, src_spec = b[0], b[1], b[2]
    local = t - t0
    span = max(t1 - t0, 0.1)
    rgb = sample_source(src_spec, local, span)
    # Cross-dissolve from previous beat at cut boundary
    if active_idx > 0 and local < fade_dur:
        prev_b = beats[active_idx - 1]
        prev_span = max(prev_b[1] - prev_b[0], 0.1)
        prev_rgb = sample_source(prev_b[2], prev_span + local, prev_span)
        w = ease(local / fade_dur)
        rgb = cv2.addWeighted(prev_rgb, 1.0 - w, rgb, w, 0.0)
    rgb = ((rgb.astype(np.uint16) * _VIG_SCRIM_U16) >> 8) + _LIFT_U8
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    return rgb, active_idx, local, span

def place_inset(dst: np.ndarray, src_spec: tuple, t_local: float, span: float,
                box: tuple[int, int, int, int], accent: tuple[int, int, int] = CYAN,
                alpha: float = 0.94) -> np.ndarray:
    """Place a sleek cross-scale magnifier inset in the upper-right with rounded mask & glowing border."""
    if not ENABLE_CROSS_SCALE_PIP:
        return dst
    if alpha <= 0.02:
        return dst
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    raw = sample_source(src_spec, t_local, span)
    patch = cv2.resize(raw, (tw, th), interpolation=cv2.INTER_AREA)
    # Rounded mask
    mask = np.zeros((th, tw), dtype=np.uint8)
    r = 12
    cv2.rectangle(mask, (r, 0), (tw - r, th), 255, -1)
    cv2.rectangle(mask, (0, r), (tw, th - r), 255, -1)
    for cx, cy in ((r, r), (tw - r, r), (r, th - r), (tw - r, th - r)):
        cv2.circle(mask, (cx, cy), r, 255, -1)
    m_u16 = (mask.astype(np.uint16) * int(alpha * 256) >> 8)[..., None]
    sx0, sy0 = max(0, x0 - 6), max(0, y0 - 6)
    sx1, sy1 = min(W, x1 + 6), min(H, y1 + 6)
    dst[sy0:sy1, sx0:sx1] = ((dst[sy0:sy1, sx0:sx1].astype(np.uint16) * int((1.0 - 0.35 * alpha) * 256)) >> 8).astype(np.uint8)
    region = dst[y0:y1, x0:x1].astype(np.uint16)
    dst[y0:y1, x0:x1] = ((region * (256 - m_u16) + patch.astype(np.uint16) * m_u16) >> 8).astype(np.uint8)
    return dst

# ---- Cached HUD Layer Renderer (supersampled 2x -> downscaled cleanly) ----
class FastHUD:
    def __init__(self):
        self.ss = 2
        self.im = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def rrect(self, box, r, fill=None, outline=None, width=1.5, alpha=1.0):
        if alpha <= 0.01:
            return
        b = [int(v * self.ss) for v in box]
        fc = (*fill, int(255 * alpha)) if fill else None
        oc = (*outline, int(255 * alpha)) if outline else None
        self.d.rounded_rectangle(b, int(r * self.ss), fill=fc, outline=oc, width=max(1, int(width * self.ss)))

    def line(self, pts, fill=CREAM, width=1.5, alpha=1.0):
        if alpha <= 0.01:
            return
        self.d.line([(int(x * self.ss), int(y * self.ss)) for x, y in pts],
                    fill=(*fill, int(255 * alpha)), width=max(1, int(width * self.ss)))

    def dot(self, xy, r, fill=CREAM, alpha=1.0):
        if alpha <= 0.01:
            return
        x, y = xy[0] * self.ss, xy[1] * self.ss
        rr = r * self.ss
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(*fill, int(255 * alpha)))

    def ring(self, xy, r, fill=CREAM, width=1.5, alpha=1.0):
        if alpha <= 0.01:
            return
        x, y = xy[0] * self.ss, xy[1] * self.ss
        rr = r * self.ss
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(*fill, int(255 * alpha)), width=max(1, int(width * self.ss)))

    def text(self, xy, txt, font_path, size, fill=CREAM, alpha=1.0, anchor='ls'):
        if alpha <= 0.01 or not txt:
            return
        f = F(font_path, int(size * self.ss))
        self.d.text((int(xy[0] * self.ss), int(xy[1] * self.ss)), txt,
                    font=f, fill=(*fill, int(255 * alpha)), anchor=anchor)

    def top_bar(self, chapter_tag: str, title: str, sub: str, accent=GOLD, alpha=1.0):
        # Sleek floating top-left badge + title
        self.rrect((24, 14, 178, 40), 5, fill=(12, 18, 36), outline=accent, width=1.2, alpha=0.82 * alpha)
        self.text((101, 31), chapter_tag, SANS_B, 11, fill=accent, alpha=0.95 * alpha, anchor='ms')
        self.text((194, 32), title, SANS_B, 17, fill=CREAM, alpha=0.98 * alpha, anchor='ls')
        if sub:
            self.text((194, 52), sub, SANS, 12, fill=MUTED, alpha=0.92 * alpha, anchor='ls')

    def hud_card(self, box, title: str, sub: str = '', accent=CYAN, alpha=1.0, badge: str = ''):
        # Dense lower-left cards off by default; chapter-open window sets _HUD_CHAPTER_OPEN.
        if not ENABLE_DENSE_LOWER_HUD and not globals().get('_HUD_CHAPTER_OPEN', False):
            return
        if alpha <= 0.01:
            return
        x0, y0, x1, y1 = box
        self.rrect(box, 8, fill=(10, 16, 34), outline=(45, 62, 100), width=1.0, alpha=0.76 * alpha)
        self.line([(x0 + 2, y0 + 5), (x0 + 2, y1 - 5)], fill=accent, width=3.2, alpha=0.95 * alpha)
        tx = x0 + 14
        if badge:
            self.rrect((x0 + 12, y0 + 9, x0 + 86, y0 + 27), 4, fill=accent, alpha=0.22 * alpha)
            self.text((x0 + 49, y0 + 22), badge, SANS_B, 10, fill=accent, alpha=0.98 * alpha, anchor='ms')
            self.text((x0 + 96, y0 + 24), title, SANS_B, 14, fill=CREAM, alpha=0.98 * alpha, anchor='ls')
        else:
            self.text((tx, y0 + 24), title, SANS_B, 15, fill=CREAM, alpha=0.98 * alpha, anchor='ls')
        if sub:
            self.text((tx, y0 + 45), sub, SANS, 11.5, fill=MUTED, alpha=0.92 * alpha, anchor='ls')

    def callout(self, anchor_xy, box_xy, title: str, sub: str = '', accent=CYAN, alpha=1.0):
        if alpha <= 0.01:
            return
        ax, ay = anchor_xy
        bx, by = box_xy
        self.ring((ax, ay), 5.5, fill=accent, width=1.5, alpha=alpha)
        self.dot((ax, ay), 2.5, fill=accent, alpha=alpha)
        self.line([(ax, ay), (bx, by + 18)], fill=accent, width=1.2, alpha=0.75 * alpha)
        w = max(len(title) * 14 + 28, len(sub) * 11 + 28, 175)
        self.hud_card((bx, by, min(W - 20, bx + w), by + (54 if sub else 34)), title, sub, accent=accent, alpha=alpha)

    def inset_frame(self, box, label_txt: str, anchor_xy=None, accent=CYAN, alpha=1.0):
        if not ENABLE_CROSS_SCALE_PIP:
            return
        if alpha <= 0.01:
            return
        x0, y0, x1, y1 = box
        self.rrect(box, 12, outline=accent, width=1.8, alpha=0.85 * alpha)
        self.rrect((x0 + 8, y1 - 24, x1 - 8, y1 - 5), 5, fill=(10, 15, 32), alpha=0.82 * alpha)
        self.text(((x0 + x1) / 2, y1 - 11), label_txt, SANS_B, 10.5, fill=CREAM, alpha=0.95 * alpha, anchor='ms')
        if anchor_xy is not None:
            ax, ay = anchor_xy
            self.ring((ax, ay), 5.0, fill=accent, width=1.4, alpha=0.85 * alpha)
            self.dot((ax, ay), 2.2, fill=accent, alpha=0.9 * alpha)
            self.line([(ax, ay), (x0, (y0 + y1) / 2)], fill=accent, width=1.2, alpha=0.65 * alpha)

    def progress(self, frac: float, n_beats: int, accent=CYAN):
        y = CAP_Y - 4
        x0, x1 = 28, W - 28
        self.line([(x0, y), (x1, y)], fill=(45, 58, 92), width=1.6, alpha=0.45)
        self.line([(x0, y), (x0 + (x1 - x0) * frac, y)], fill=accent, width=2.2, alpha=0.85)
        for i in range(n_beats):
            xf = x0 + (x1 - x0) * (i / max(n_beats - 1, 1))
            on = frac >= (i / max(n_beats - 1, 1)) - 1e-3
            self.dot((xf, y), 3.0 if on else 2.2, fill=accent if on else (70, 82, 115), alpha=0.9 if on else 0.4)

    def finish(self) -> tuple[np.ndarray, np.ndarray]:
        arr = np.asarray(self.im, dtype=np.uint8)
        small = cv2.resize(arr, (W, H), interpolation=cv2.INTER_AREA)
        a_u16 = small[..., 3:4].astype(np.uint16)
        c_pre = (small[..., :3].astype(np.uint16) * a_u16) >> 8
        return c_pre, (255 - a_u16)

def blend_hud(rgb_u8: np.ndarray, hud_pair: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    c_pre, inv_a = hud_pair
    out = ((rgb_u8.astype(np.uint16) * inv_a) >> 8) + c_pre
    return np.clip(out, 0, 255).astype(np.uint8)


# ==============================================================================
# SCENE DEFINITIONS: 23 Full-Bleed 16:9 Multi-Camera Styleframes
# ==============================================================================


def mol_src(kind: str, pan_x: float = 0.02, pan_y: float = 0.03):
    """Molecular / micro hero source. Illustration plates when USE_TRUE3D_MOLECULAR is False.
    kind: microbes|chr2|relay|pump|nphr|retina|circuit
    """
    if USE_TRUE3D_MOLECULAR:
        seq_map = {
            'microbes': mol_src('microbes'),
            'chr2': mol_src('chr2'),
            'relay': mol_src('chr2'),
            'pump': mol_src('pump'),
            'nphr': mol_src('nphr'),
            'retina': mol_src('retina'),
            'circuit': mol_src('circuit'),
        }
        return seq_map[kind]
    plate_map = {
        'microbes': ('plate', 'microbes', pan_x, pan_y),
        'chr2': ('plate', 'chr2', pan_x, pan_y),          # sf09e_chr2
        'relay': ('plate', 'relay_b', pan_x, pan_y),      # sf08e_relay
        'pump': ('plate', 'relay', pan_x * 0.8, pan_y),   # sf08f as pump-family stand-in
        'nphr': ('plate', 'chr2_noret', pan_x, pan_y),
        'retina': ('plate', 'eye', pan_x, pan_y),
        'circuit': ('plate', 'neuron', pan_x, pan_y),
    }
    return plate_map[kind]

def _eval_scene(name: str, t: float) -> tuple[np.ndarray, int]:
    """Return (bg_rgb_with_scrim, hud_state_key) for scene `name` at time `t`."""
    q = int(t * 2.0)

    if name == 'SF01_open_title':
        beats = [
            (0.0, 2.4, ('seq', 'm6', 0.35, False)),
            (2.4, 5.0, mol_src('circuit')),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if b_idx == 0:
            rgb = place_inset(rgb, mol_src('circuit'), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        else:
            rgb = place_inset(rgb, ('seq', 'envA', 0.38, False), loc, span, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF02_1979_request':
        beats = [
            (0.0, 2.0, ('plate', 'crick', 0.02, 0.04)),
            (2.0, 4.0, ('plate', 'crowd', -0.02, 0.04)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, mol_src('circuit'), t, 4.0, (660, 74, 932, 230), GOLD, 0.90)
        return rgb, q

    elif name == 'SF03_microbe_clues':
        beats = [
            (0.0, 4.0, mol_src('microbes', 0.02, 0.03)),
            (4.0, 8.0, mol_src('pump', -0.02, 0.03)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, mol_src('chr2'), t, 8.0, (650, 74, 932, 232), AMBER, 0.92)
        return rgb, q

    elif name == 'SF04_crick_quote':
        beats = [
            (0.0, 5.5, ('plate', 'crick', 0.025, 0.04)),
            (5.5, 11.0, mol_src('circuit')),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if b_idx == 0:
            rgb = place_inset(rgb, mol_src('circuit'), loc, span, (650, 74, 932, 232), GOLD, 0.92)
        else:
            rgb = place_inset(rgb, ('plate', 'crick', 0.01, 0.02), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        return rgb, q

    elif name == 'SF12_neuron_select':
        beats = [
            (0.0, 5.0, mol_src('circuit')),
            (5.0, 10.0, ('seq', 'envA', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if b_idx == 0:
            rgb = place_inset(rgb, ('seq', 'm6', 0.35, False), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        else:
            rgb = place_inset(rgb, mol_src('chr2'), loc, span, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF05_nobel_portraits':
        beats = [
            (0.0, 3.6, ('plate', 'deisseroth', 0.02, 0.035)),
            (3.6, 7.2, ('plate', 'hegemann', -0.02, 0.035)),
            (7.2, 11.0, ('plate', 'nagel', 0.02, 0.035)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, ('seq', 'm5', 0.35, False), t, 11.0, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF06_switch_diagram':
        beats = [
            (0.0, 4.5, mol_src('chr2', 0.025, 0.03)),
            (4.5, 9.0, ('seq', 'm5', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if b_idx == 0:
            rgb = place_inset(rgb, ('seq', 'envA', 0.35, False), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        else:
            rgb = place_inset(rgb, mol_src('chr2'), loc, span, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF07_main_title':
        beats = [
            (0.0, 3.5, mol_src('circuit')),
            (3.5, 7.0, ('seq', 'envA', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, mol_src('chr2'), t, 7.0, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF13_spike_causality':
        beats = [
            (0.0, 10.4, mol_src('circuit')),
            (10.4, 20.8, ('seq', 'm6', 0.35, False)),
            (20.8, 31.2, ('seq', 'envA', 0.35, False)),
            (31.2, 41.6, ('seq', 'comm', 0.35, False)),
            (41.6, 52.0, ('seq', 'm5', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins_map = [
            ('seq', 'sf10_gpu', 0.35, False),
            mol_src('circuit'),
            mol_src('chr2'),
            mol_src('circuit', -0.02, 0.02),
            mol_src('chr2', -0.02, 0.02),
        ]
        rgb = place_inset(rgb, ins_map[b_idx], loc, span, (650, 74, 932, 232), CYAN if b_idx % 2 == 0 else GOLD, 0.92)
        return rgb, q

    elif name == 'SF08_early_attempts':
        beats = [
            (0.0, 5.5, mol_src('relay', 0.02, 0.03)),
            (5.5, 11.0, mol_src('pump', -0.02, 0.025)),
            (11.0, 16.0, mol_src('chr2', 0.02, 0.03)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, ('seq', 'sf10_gpu', 0.35, False), t, 16.0, (650, 74, 932, 232), AMBER, 0.90)
        return rgb, q

    elif name == 'SF09_chr2_channel':
        beats = [
            (0.0, 4.0, mol_src('chr2', 0.025, 0.03)),
            (4.0, 8.0, mol_src('relay', -0.02, 0.025)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, ('seq', 'm6', 0.35, False), t, 8.0, (650, 74, 932, 232), CYAN, 0.92)
        return rgb, q

    elif name == 'SF14_orexin_q':
        beats = [
            (0.0, 5.3, mol_src('circuit')),
            (5.3, 10.6, ('seq', 'sf10_gpu', 0.35, False)),
            (10.6, 16.0, ('seq', 'comm', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('seq', 'sf10_gpu', 0.35, False) if b_idx == 0 else mol_src('circuit')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), GOLD if b_idx == 0 else CYAN, 0.92)
        return rgb, q

    elif name == 'SF10_mouse_tripo':
        # 19.0s: 100% continuous 4-camera V2-Fur 3D animation! Zero static hold, zero orange dot!
        beats = [
            (0.0, 4.8, ('seq', 'sf10_gpu', 0.35, False)),   # Cam A: Slow-wave sleep -> 470nm fiber light pulse on
            (4.8, 9.8, ('seq', 'm6', 0.35, False)),         # Cam B: Breathing -> head lift -> wake & walk forward
            (9.8, 14.5, ('seq', 'm5', 0.35, False)),        # Cam C: Low hero tracking shot of active walking stride
            (14.5, 19.2, ('seq', 'envA', 0.35, False)),     # Cam D: High-angle 3/4 experimental cage exploration
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t, fade_dur=0.35)
        rgb = place_inset(rgb, mol_src('circuit'), t, 19.0, (664, 72, 932, 224), CYAN if t >= 3.5 else MUTED, 0.90)
        return rgb, q

    elif name == 'SF15_br_pump_channel':
        beats = [
            (0.0, 12.4, mol_src('microbes')),
            (12.4, 24.8, mol_src('pump')),
            (24.8, 37.2, mol_src('chr2')),
            (37.2, 49.6, mol_src('pump', -0.02, 0.02)),
            (49.6, 62.0, ('seq', 'comm', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('seq', 'envA', 0.35, False) if b_idx < 4 else mol_src('chr2')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), GOLD if b_idx < 2 else CYAN, 0.92)
        return rgb, q

    elif name == 'SF16_chr_path':
        beats = [
            (0.0, 20.0, mol_src('microbes')),
            (20.0, 40.0, mol_src('pump')),
            (40.0, 60.0, mol_src('chr2')),
            (60.0, 80.0, mol_src('chr2', -0.02, 0.02)),
            (80.0, 100.0, mol_src('circuit')),
            (100.0, 120.0, ('seq', 'm6', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('seq', 'm5', 0.35, False) if b_idx < 5 else mol_src('chr2')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), CYAN, 0.92)
        return rgb, q

    elif name == 'SF17_credit_word':
        beats = [
            (0.0, 7.5, ('plate', 'deisseroth', 0.02, 0.035)),
            (7.5, 15.0, ('seq', 'envA', 0.35, False)),
            (15.0, 22.5, mol_src('circuit')),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, mol_src('chr2'), t, 22.0, (650, 74, 932, 232), GOLD, 0.90)
        return rgb, q

    elif name == 'SF18_invivo_dual':
        # 96s: 10 distinct multi-cam 3D cage & molecular beats
        beats = [
            (0.0, 9.6, ('seq', 'envA', 0.35, False)),
            (9.6, 19.2, ('seq', 'comm', 0.35, False)),
            (19.2, 28.8, ('seq', 'm6', 0.35, False)),
            (28.8, 38.4, ('seq', 'nphr', 0.35, False)),
            (38.4, 48.0, mol_src('nphr')),
            (48.0, 57.6, ('seq', 'envA', 0.35, True)),
            (57.6, 65.0, ('seq', 'nphr', 0.35, True)),
            (65.0, 75.5, ('plate', 'deisseroth', 0.02, 0.035)),
            (75.5, 86.0, ('plate', 'hegemann', -0.02, 0.035)),
            (86.0, 96.5, ('plate', 'nagel', 0.02, 0.035)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if t < 32.0:
            rgb = place_inset(rgb, mol_src('chr2'), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        elif t < 64.0:
            ins = ('seq', 'envA', 0.35, False) if b_idx in (3, 4, 6) else mol_src('nphr')
            rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), AMBER if b_idx in (3, 4, 6) else CYAN, 0.94)
        else:
            rgb = place_inset(rgb, ('seq', 'envA', 0.35, False), loc, span, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF19_engram':
        # 88s: 7 distinct multi-cam 3D cage & hippocampal light-cone beats
        beats = [
            (0.0, 12.5, ('seq', 'envA', 0.35, False)),         # Context A exploration
            (12.5, 25.0, mol_src('circuit')), # Hippocampus DG ChR2 tagging in situ
            (25.0, 38.0, ('seq', 'envB', 0.35, False)),        # Context B shock + blue light recall
            (38.0, 51.0, mol_src('circuit', -0.02, 0.02)),# DG engram reactivation
            (51.0, 64.0, ('seq', 'envB', 0.35, True)),         # Context B conditioning
            (64.0, 76.0, ('seq', 'comm', 0.35, False)),        # Return to Context A: fear-freezing micro-breathing!
            (76.0, 88.5, ('seq', 'envA', 0.32, True)),         # Context A verification
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        if b_idx in (0, 1):
            rgb = place_inset(rgb, mol_src('circuit') if b_idx == 0 else ('seq', 'envA', 0.35, False), loc, span, (650, 74, 932, 232), CYAN, 0.92)
        elif b_idx in (2, 3, 4):
            rgb = place_inset(rgb, ('seq', 'envA', 0.35, False), loc, span, (650, 74, 932, 232), AMBER, 0.94)
        else:
            rgb = place_inset(rgb, ('seq', 'envB', 0.35, False), loc, span, (650, 74, 932, 232), GOLD, 0.94)
        return rgb, q

    elif name == 'SF20_retina_intro':
        beats = [
            (0.0, 8.0, mol_src('retina')),
            (8.0, 16.0, mol_src('chr2')),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        rgb = place_inset(rgb, ('plate', 'eye_inset', 0.02, 0.03), t, 16.0, (650, 74, 932, 232), AMBER, 0.92)
        return rgb, q

    elif name == 'SF11_eye_goggles':
        beats = [
            (0.0, 8.0, mol_src('retina')),
            (8.0, 16.0, ('plate', 'goggles', -0.025, 0.04)),
            (16.0, 24.0, mol_src('retina', -0.02, 0.02)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('plate', 'goggles', 0.02, 0.03) if b_idx != 1 else mol_src('retina')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), AMBER, 0.92)
        return rgb, q

    elif name == 'SF21_partial_vision':
        beats = [
            (0.0, 15.0, mol_src('retina')),
            (15.0, 31.0, ('plate', 'goggles', -0.025, 0.04)),
            (31.0, 46.5, mol_src('retina', -0.02, 0.02)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('plate', 'goggles', 0.02, 0.03) if b_idx != 1 else mol_src('retina')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), AMBER, 0.92)
        return rgb, q

    elif name == 'SF22_regulatory':
        beats = [
            (0.0, 18.8, mol_src('retina')),
            (18.8, 37.6, ('plate', 'goggles', -0.025, 0.04)),
            (37.6, 56.4, mol_src('retina', -0.02, 0.02)),
            (56.4, 75.2, mol_src('chr2')),
            (75.2, 94.5, ('seq', 'envA', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = ('plate', 'goggles', 0.02, 0.03) if b_idx != 1 else mol_src('retina')
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), GOLD, 0.92)
        return rgb, q

    elif name == 'SF23_limits_close':
        beats = [
            (0.0, 16.5, mol_src('chr2')),
            (16.5, 33.0, ('seq', 'envA', 0.35, False)),
            (33.0, 49.5, ('seq', 'comm', 0.35, False)),
            (49.5, 66.0, ('seq', 'm6', 0.35, False)),
            (66.0, 82.5, mol_src('circuit')),
            (82.5, 100.5, ('seq', 'm5', 0.35, False)),
        ]
        rgb, b_idx, loc, span = multi_cam_bg(beats, t)
        ins = mol_src('retina') if b_idx < 2 else (mol_src('chr2') if b_idx < 4 else ('seq', 'envA', 0.35, False))
        rgb = place_inset(rgb, ins, loc, span, (650, 74, 932, 232), CYAN if b_idx < 4 else GOLD, 0.92)
        return rgb, q

    raise ValueError(f'Unknown scene {name}')


def _build_hud(name: str, q: int, dur: float) -> np.ndarray:
    """Build supersampled 16:9 widescreen HUD overlay for quantized time `q * 0.25`."""
    t = min(q * 0.5, dur - 0.02)
    frac = min(max(t / max(dur, 1e-5), 0.0), 1.0)
    # Chapter-open only: allow lower-left card in the first CHAPTER_OPEN_FRAC of each SF.
    global _HUD_CHAPTER_OPEN
    _HUD_CHAPTER_OPEN = bool(frac <= CHAPTER_OPEN_FRAC)
    H_hud = FastHUD()
    IBOX = (650, 74, 932, 232)

    if name == 'SF01_open_title':
        H_hud.top_bar('EIGENLENS · 02', '用光，只动某一类神经元', '从 1979 设想到毫秒级光控离子通道', GOLD)
        H_hud.inset_frame(IBOX, '跨尺度对照 · 脑回路 ↔ 活体行为', anchor_xy=(440, 220), accent=CYAN)
        H_hud.hud_card((24, 344, 430, 412), '基因定靶 · 光定时刻', '选定细胞装上感光通道 · 毫秒级可逆开关', CYAN, ramp(t, 0.3, 1.2), '核心命题')
        H_hud.progress(frac, 2, CYAN)

    elif name == 'SF02_1979_request':
        H_hud.top_bar('A0 · 1979 设想', 'Francis Crick 的具体要求', '《科学美国人》· 脑科学亟需的方法学突破', GOLD)
        H_hud.inset_frame((660, 74, 932, 230), '目标：只激活一类神经元', anchor_xy=(460, 240), accent=GOLD)
        H_hud.hud_card((24, 344, 450, 412), '只动某一类 · 其余大体不动', '可开可关 · 动作电位毫秒尺度', GOLD, ramp(t, 0.2, 1.0), '1979 要求')
        H_hud.progress(frac, 2, GOLD)

    elif name == 'SF03_microbe_clues':
        H_hud.top_bar('A0 · 微生物线索', '微生物膜上的感光蛋白', '1971 盐杆菌紫膜 · 绿藻趋光眼点', AMBER)
        H_hud.inset_frame(IBOX, '跨膜视紫红质家族 · 分子剖面', anchor_xy=(480, 250), accent=AMBER)
        H_hud.hud_card((24, 344, 460, 412), '光驱动膜蛋白线索积累', '从微生物质子泵到离子通道的关键一跳', AMBER, ramp(t, 0.4, 1.4), '前史线索')
        H_hud.progress(frac, 2, AMBER)

    elif name == 'SF04_crick_quote':
        H_hud.top_bar('A0 · 牵强设想', '1999 伦敦讲演：为什么说它「牵强」', '红外光与分子激光只是举例 · 真正缺的是光敏开关', GOLD)
        H_hud.inset_frame(IBOX, '皮层局部微环路 · 选择性靶向', anchor_xy=(450, 240), accent=GOLD if t < 5.5 else CYAN)
        if t < 5.5:
            H_hud.hud_card((24, 344, 460, 412), '电极与药物无法同时满足时空精度', '电极不分细胞种类 · 药物起效太慢（分钟级）', GOLD, ramp(t, 0.4, 1.5), '方法瓶颈')
        else:
            H_hud.hud_card((24, 344, 460, 412), '理想信号是光 · 缺一枚入脑开关', '把感光分子精准装进特定神经元亚群', CYAN, ramp(t - 5.5, 0.3, 1.2), '核心缺口')
        H_hud.progress(frac, 2, GOLD)

    elif name == 'SF12_neuron_select':
        H_hud.top_bar('A0 · 遗传靶向', '选择性控制：只动目标亚群', '启动子与病毒载体决定「装在谁身上」', CYAN)
        H_hud.inset_frame(IBOX, '活体光纤递送 ↔ 跨膜通道开启', anchor_xy=(460, 230), accent=CYAN)
        if t < 5.0:
            H_hud.hud_card((24, 344, 460, 412), '同一种光打进混杂组织', '只有携带光敏蛋白的目标神经元被点亮', CYAN, 1.0, '空间选择性')
        else:
            H_hud.hud_card((24, 344, 460, 412), '毫秒级开启与关闭', '光脉冲一停，膜电位立即恢复基线', GOLD, ramp(t - 5.0, 0.2, 1.0), '时间精确性')
        H_hud.progress(frac, 2, CYAN)

    elif name == 'SF05_nobel_portraits':
        H_hud.top_bar('A0 · 授奖先驱', '从微生物通道到神经科学方法', 'Deisseroth · Hegemann · Nagel', GOLD)
        H_hud.inset_frame(IBOX, '活体自由活动小鼠 · 光纤植入', anchor_xy=(470, 220), accent=GOLD)
        who = ('Karl Deisseroth · 神经元光控与活体方法', 'Peter Hegemann · 衣藻光敏通道发现', 'Georg Nagel · 卵母细胞电生理确证')[min(2, int(t / 3.6))]
        H_hud.hud_card((24, 344, 480, 412), who, '跨学科接力：藻类光生物学 → 电生理 → 神经环路', GOLD, 1.0, '科学接力')
        H_hud.progress(frac, 3, GOLD)

    elif name == 'SF06_switch_diagram':
        H_hud.top_bar('A · 光控开关', '一枚蛋白同时承担「感光」与「开孔」', '基因决定装谁 · 光脉冲决定何时拨动', CYAN)
        H_hud.inset_frame(IBOX, '分子构象开孔 ↔ 活体清醒行为', anchor_xy=(450, 235), accent=CYAN)
        H_hud.hud_card((24, 344, 460, 412), '单基因编码的光门控通道', '无需多步生化级联 · 蓝光直驱阳离子内流', CYAN, 1.0, '开关原理')
        H_hud.progress(frac, 2, CYAN)

    elif name == 'SF07_main_title':
        H_hud.top_bar('片名 · OPTOGENETICS', '光遗传学：把光变成研究脑的因果工具', 'EigenLens 主观知识 · 第 2 期', GOLD)
        H_hud.inset_frame(IBOX, 'ChR2 光门控阳离子通道', anchor_xy=(460, 240), accent=GOLD)
        H_hud.hud_card((24, 344, 460, 412), '分子史 · 活体行为 · 临床边界', '严格停在已发表实验证据与监管事实之内', GOLD, 1.0, '全片主线')
        H_hud.progress(frac, 2, GOLD)

    elif name == 'SF13_spike_causality':
        H_hud.top_bar('A · 锋电位与因果', '从「相关观察」走向「毫秒级因果检验」', '一次锋电位仅约 1–2 毫秒 · 必须对齐神经元自然语速', CYAN)
        H_hud.inset_frame(IBOX, '跨尺度同步 · 膜电位 ↔ 活体笼箱', anchor_xy=(450, 240), accent=CYAN)
        if t < 17.0:
            H_hud.hud_card((24, 344, 480, 412), '神经元靠膜两侧电压脉冲通信', '离子跨膜内流 → 去极化发放锋电位 → 毫秒级恢复', CYAN, 1.0, '锋电位')
        elif t < 34.0:
            H_hud.hud_card((24, 344, 480, 412), '记录只见相关 · 损毁太慢且不可逆', '要证明「是这群细胞导致行为」，必须只拨动它们', GOLD, 1.0, '因果检验')
        else:
            H_hud.hud_card((24, 344, 480, 412), '时间尺度必须对齐毫秒级', '分钟级药物无法检验毫秒级脉冲序列的因果作用', AMBER, 1.0, '时间精度')
        H_hud.progress(frac, 4, CYAN)

    elif name == 'SF08_early_attempts':
        H_hud.top_bar('A · 早期尝试', '为什么多步信号级联与化学光开关没能普及', '步骤繁琐 · 起效偏慢 · 外源化学基团难以进深脑', AMBER)
        H_hud.inset_frame(IBOX, '对比：单分子直接光门控 (ChR2)', anchor_xy=(460, 230), accent=AMBER)
        if t < 5.5:
            H_hud.hud_card((24, 344, 470, 412), '路径一：多蛋白 G 蛋白级联 (chARGe)', '需要多步胞内信号接力 · 时间抖动大、不够快', AMBER, 1.0, '级联偏慢')
        elif t < 11.0:
            H_hud.hud_card((24, 344, 470, 412), '路径二：改造通道 + 化学光开关', '需额外注射化学偶联分子 · 活体深部组织受限', CYAN, 1.0, '外源受限')
        else:
            H_hud.hud_card((24, 344, 470, 412), '突破口：自带感光与通道的一体蛋白', '一个基因装进神经元 · 光打上去自己直接开门', GOLD, 1.0, '一体开关')
        H_hud.progress(frac, 3, AMBER)

    elif name == 'SF09_chr2_channel':
        H_hud.top_bar('B · 通道视紫红质', 'ChR2：光吸收与离子孔道合一的跨膜蛋白', '内嵌全反式视黄醛 · 470 nm 蓝光直开阳离子孔道', CYAN)
        H_hud.inset_frame(IBOX, '活体光纤递送 → 神经元去极化', anchor_xy=(460, 240), accent=CYAN)
        H_hud.hud_card((24, 344, 480, 412), '蓝光照射 → 视黄醛异构 → 通道瞬时打开', 'Na⁺ / Ca²⁺ 顺电化学梯度涌入 · 直接诱发动作电位', CYAN, 1.0, '分子机制')
        H_hud.progress(frac, 2, CYAN)

    elif name == 'SF14_orexin_q':
        H_hud.top_bar('A · 食欲素环路', '下丘脑食欲素 (Orexin/Hypocretin) 神经元', '能否只在活体睡眠中单独拨动这一群细胞？', GOLD)
        H_hud.inset_frame(IBOX, '下丘脑靶向簇 ↔ 睡眠/觉醒转换', anchor_xy=(450, 240), accent=GOLD)
        H_hud.hud_card((24, 344, 480, 412), '因果发问：单独激活食欲素细胞能否唤醒动物', '2007 Adamantidis & Deisseroth · 活体光纤睡眠唤醒实验', GOLD, 1.0, '活体发问')
        H_hud.progress(frac, 2, GOLD)

    elif name == 'SF10_mouse_tripo':
        # 19.0s continuous 4-cam 3D hero!
        is_awake = t >= 3.5
        st_col = CYAN if is_awake else AMBER
        st_txt = '状态：蓝光脉冲激活 → 抬头苏醒走动' if is_awake else '状态：慢波睡眠期 · 光纤待命'
        H_hud.top_bar('A · 2007 活体唤醒实验', '下丘脑食欲素神经元 · 蓝光脉冲驱动睡眠→清醒转换', st_txt, st_col)
        H_hud.inset_frame((664, 72, 932, 224), '下丘脑 Orexin 神经元靶向簇', anchor_xy=(420, 210), accent=st_col)
        # Animated 470nm pulse train meter on lower-left HUD card
        H_hud.hud_card((24, 342, 470, 414), '470 nm 蓝光脉冲序列 → 唤醒潜伏期缩短',
                       '机位 A/B/C/D 连续记录：睡眠呼吸 → 光脉冲入脑 → 苏醒迈步', st_col, 1.0,
                       '470nm ON' if is_awake else 'SLEEP')
        # Draw pulse bars inside card right side
        for i in range(8):
            bx = 355 + i * 12
            pulse_h = (16 if (is_awake and (q + i) % 2 == 0) else (8 if is_awake else 3))
            H_hud.rrect((bx, 376 - pulse_h, bx + 7, 376), 1.5, fill=CYAN if is_awake else MUTED, alpha=0.9)
        H_hud.progress(frac, 4, st_col)

    elif name == 'SF15_br_pump_channel':
        H_hud.top_bar('B · 泵与通道', '1971–1973 细菌视紫红质 (BR) vs 离子通道', '主动转运质子泵 ≠ 顺梯度高通量离子通道', GOLD if t < 31 else CYAN)
        H_hud.inset_frame(IBOX, '分子机制对照 · 质子泵 ↔ 离子孔道', anchor_xy=(460, 235), accent=GOLD if t < 31 else CYAN)
        if t < 31.0:
            H_hud.hud_card((24, 344, 490, 412), '细菌视紫红质 (BR)：光驱动质子泵', '每吸收一个光子仅逆梯度搬运一个 H⁺ · 电流较小', GOLD, 1.0, '1971 紫膜')
        else:
            H_hud.hud_card((24, 344, 490, 412), '通道视紫红质 (ChR)：光门控离子通道', '孔道打开后大批离子顺梯度涌入 · 快速翻转神经元膜电位', CYAN, 1.0, '泵 ≠ 通道')
        H_hud.progress(frac, 4, CYAN)

    elif name == 'SF16_chr_path':
        steps = [
            '1 · 莱茵衣藻朝光运动与眼点感光线索',
            '2 · 2002 ChR1：非洲爪蟾卵母细胞确证光门控质子电流',
            '3 · 关键性质：感光视黄醛与离子孔道合于单一蛋白',
            '4 · 2003 ChR2：470nm 蓝光高速阳离子通道 · 哺乳细胞高表达',
            '5 · 动力学特征：持续光照存在脱敏平台 · 宜用毫秒短脉冲',
            '6 · 2005 培养海马神经元：一束脉冲精准对应一次锋电位',
        ]
        idx = min(5, int(t / 20.0))
        H_hud.top_bar(f'B · 分子史路径 ({idx+1}/6)', '从绿藻眼点到哺乳动物神经元毫秒开关', steps[idx], CYAN)
        H_hud.inset_frame(IBOX, '终点：活体神经元精准脉冲控制', anchor_xy=(460, 235), accent=CYAN)
        H_hud.hud_card((24, 344, 520, 412), steps[idx], '1971 紫膜 → 2002 ChR1 → 2003 ChR2 → 2005 神经元动作电位', GOLD if idx % 2 else CYAN, 1.0, f'阶段 0{idx+1}')
        H_hud.progress(frac, 6, CYAN)

    elif name == 'SF17_credit_word':
        H_hud.top_bar('B · 署名与命名', '2005 里程碑论文署名 vs 2006「Optogenetics」一词登场', 'Boyden 第一作者 · Deisseroth 通讯 · 授奖名单各有侧重', GOLD)
        H_hud.inset_frame(IBOX, '基因定靶 + 光纤递送 = 光遗传学', anchor_xy=(460, 235), accent=GOLD)
        if t < 12.0:
            H_hud.hud_card((24, 344, 500, 412), '2005《自然·神经科学》vs 2026 诺奖三人名单', '论文第一作者 Boyden · 通讯作者 Deisseroth · 历史贡献各有坐标', GOLD, 1.0, '署名坐标')
        else:
            H_hud.hud_card((24, 344, 500, 412), '2006 Deisseroth 等正式提出 Optogenetics', '把「遗传学靶向」与「光学毫秒递送」定义为统一方法学', CYAN, 1.0, '2006 命名')
        H_hud.progress(frac, 3, GOLD)

    elif name == 'SF18_invivo_dual':
        if t < 32.0:
            H_hud.top_bar('B · 2007 活体光纤入脑', '哺乳动物脑内内源视黄醛充足 · 无需外加辅因子', '陶瓷插芯 + 旋转接头 · 清醒自由走动小鼠运动皮层驱动', CYAN)
            H_hud.inset_frame(IBOX, '内源全反式视黄醛 · 天然充足', anchor_xy=(420, 195), accent=CYAN)
            H_hud.hud_card((24, 344, 510, 412), '2005 培养皿 → 2007 清醒自由活动小鼠', '轻量化光纤通过颅骨插芯直达目标核团 · 蓝光即时驱动行为', CYAN, 1.0, '活体突破')
        elif t < 64.0:
            H_hud.top_bar('B · 双向光控：ChR2 + NpHR', '470nm 蓝光去极化「开启」 · 590nm 黄光泵入 Cl⁻「按住」', '同一只活体小鼠内光谱正交双向因果检验', AMBER)
            H_hud.inset_frame(IBOX, '正交对照：470nm 蓝光开 ↔ 590nm 黄光关', anchor_xy=(420, 210), accent=AMBER)
            H_hud.hud_card((24, 344, 520, 412), '盐细菌 NpHR 氯离子泵：590 nm 黄光超极化抑制', '既能点亮发放（必要性/充分性双向闭环），又能实时按住锋电位', AMBER, 1.0, '蓝开 · 黄关')
        else:
            H_hud.top_bar('B · 学术荣誉坐标', '2013 欧洲脑科学奖六人名单 vs 诺奖三人名单', 'Bamberg · Boyden · Deisseroth · Hegemann · Miesenböck · Nagel', GOLD)
            H_hud.inset_frame(IBOX, '透明实验笼箱 · 自由行为范式', anchor_xy=(450, 220), accent=GOLD)
            H_hud.hud_card((24, 344, 520, 412), '多项国际大奖共同勾勒完整科学谱系', '微生物光敏蛋白发现者与神经工程方法开拓者共同奠基', GOLD, 1.0, '六人 vs 三人')
        H_hud.progress(frac, 3, CYAN if t < 32 else (AMBER if t < 64 else GOLD))

    elif name == 'SF19_engram':
        if t < 28.0:
            H_hud.top_bar('C · 2013 海马记忆痕迹实验', '环境甲（蓝光透明笼）：安全探索 + 齿状回活动细胞标记', 'Ramirez & Tonegawa 等 · 仅限小鼠海马实验（不涉及人体记忆）', CYAN)
            H_hud.inset_frame(IBOX, '齿状回 (DG) 活跃神经元装上 ChR2', anchor_xy=(420, 210), accent=CYAN)
            H_hud.hud_card((24, 344, 520, 412), '步骤 1：小鼠在环境甲安全探索（无电击）', '利用即刻早期基因 c-Fos 启动子，仅在环境甲活跃的齿状回细胞表达 ChR2', CYAN, 1.0, '环境甲 · 标记')
        elif t < 64.0:
            H_hud.top_bar('C · 异地关联：环境乙电击 + 光召回', '环境乙（暖色金属栅格箱）：足底电击同时蓝光重激活「甲细胞」', '人为建立跨环境因果关联 · 对照环境甲无电击记录', AMBER)
            H_hud.inset_frame(IBOX, '对照：环境甲被标记的同一群细胞', anchor_xy=(420, 210), accent=AMBER)
            H_hud.hud_card((24, 344, 530, 412), '步骤 2：在环境乙施予电击 + 光纤蓝光重开「甲记忆细胞」', '把环境甲的细胞发放与环境乙的恐惧体验在脑内强行配对', AMBER, 1.0, '环境乙 · 配对')
        else:
            H_hud.top_bar('C · 假恐惧记忆验证与科学边界', '放回从未电击过的环境甲 → 小鼠出现典型恐惧冻结 (Freezing)', '证明特定细胞群发放足以召回情境表征 · 严格限定于小鼠实验', GOLD)
            H_hud.inset_frame(IBOX, '环境乙配对记忆 → 环境甲触发冻结', anchor_xy=(420, 210), accent=GOLD)
            H_hud.hud_card((24, 344, 530, 412), '步骤 3：重返安全环境甲却触发冻结 · 科学边界严明', '写进去的是一批细胞的发放关联 · 本研究完全不涉及人类复杂人生记忆', GOLD, 1.0, '小鼠实验边界')
        H_hud.progress(frac, 3, GOLD)

    elif name == 'SF20_retina_intro':
        H_hud.top_bar('C · 视网膜退行性疾病路径', '色素性视网膜炎 (RP)：外层感光细胞退化，内层神经节细胞尚存', '绕过受损视杆/视锥 · 直接让幸存的视网膜神经节细胞感光', AMBER)
        H_hud.inset_frame(IBOX, '幸存神经节细胞层 (RGC) 靶向转导', anchor_xy=(480, 250), accent=AMBER)
        H_hud.hud_card((24, 344, 510, 412), '临床转化逻辑：把视网膜下游出口变成感光层', '玻璃体腔注射 AAV 载体 · 让残存神经节细胞表达光敏通道', AMBER, 1.0, '视网膜路径')
        H_hud.progress(frac, 2, AMBER)

    elif name == 'SF11_eye_goggles':
        H_hud.top_bar('C · 基因 + 工程护目镜双件套', 'AAV2.7m8 携带红移通道 ChrimsonR + 外置神经形态护目镜', '天然环境光太弱太杂 · 必须由护目镜转换波长与脉冲强度', AMBER)
        H_hud.inset_frame(IBOX, '595nm 琥珀色光脉冲投射 ↔ 视网膜激活', anchor_xy=(460, 235), accent=AMBER)
        H_hud.hud_card((24, 344, 520, 412), '2021 Sahel 等《自然·医学》：基因疗法绑定专用护目镜', '相机捕捉视野亮度变化 → 实时编码为 595 nm 琥珀光阵列投射视网膜', AMBER, 1.0, '药械组合')
        H_hud.progress(frac, 3, AMBER)

    elif name == 'SF21_partial_vision':
        H_hud.top_bar('C · 部分视觉功能恢复（非日常裸眼视觉）', '单名盲人受试者：必须佩戴护目镜才能定位、计数与触摸桌面物体', '摘下护目镜即无法识别 · 枕叶视觉皮层 EEG 同步记录确认信号通路', AMBER)
        H_hud.inset_frame(IBOX, '护目镜开启 vs 关闭：功能严格依赖外设', anchor_xy=(460, 235), accent=AMBER)
        H_hud.hud_card((24, 344, 530, 412), '真实临床表现：定位高对比度笔记本与小盒 · 非恢复正常全彩视力', '戴上护目镜：能指、能数、能伸手触碰 · 摘下护目镜：无法完成任务', GOLD, 1.0, '部分功能恢复')
        H_hud.progress(frac, 3, AMBER)

    elif name == 'SF22_regulatory':
        beats_info = [
            ('2026-09-09 · MCO-010 (MOGENRY)', 'FDA 受理生物制品许可申请 (BLA) · 新闻稿写明「若获批」→ 当时尚未获批'),
            ('第 52 / 76 周临床随访终点', '申请方公告视力主要终点达标 · 仍属监管审评阶段，非已生效上市许可'),
            ('2026-10-08 ·《新英格兰医学杂志》1/2 期临床', '主要评估安全性与耐受性 · 小样本探索性研究，非确证性 3 期疗效设计'),
            ('客观报出分子与分母：6/10 与 4/8', '光敏感改善 6/10 · 佩戴护目镜行为测试仅部分任务 4/8 达标（非全员治愈）'),
            ('全球监管底线：尚无任何司法辖区批准上市', '截至成片日，GS030 / MCO-010 等光遗传学疗法均处于临床或审评阶段'),
        ]
        idx = min(4, int(t / 18.8))
        b_title, b_sub = beats_info[idx]
        H_hud.top_bar(f'C · 临床与监管事实核查 ({idx+1}/5)', '严格区分「BLA 受理 / 1-2 期安全性」与「正式获批上市」', b_title, GOLD)
        H_hud.inset_frame(IBOX, '临床数据核查 · 连同分母完整呈现', anchor_xy=(460, 235), accent=GOLD)
        H_hud.hud_card((24, 344, 545, 412), b_title, b_sub, GOLD if idx % 2 == 0 else CYAN, 1.0, f'核查 0{idx+1}')
        H_hud.progress(frac, 5, GOLD)

    elif name == 'SF23_limits_close':
        if t < 38.0:
            H_hud.top_bar('D · 三大物理与生理硬边界', '1. 持续光照脱敏 · 2. 散射限制需光纤/护目镜 · 3. 临床仅限部分功能', '科学工具的力量来自清晰知道它的适用边界', CYAN)
            H_hud.inset_frame(IBOX, '光学递送边界 · 颅骨光纤 / 视网膜护目镜', anchor_xy=(450, 230), accent=CYAN)
            H_hud.hud_card((24, 344, 535, 412), '三大真实限制：通道脱敏 · 组织散射 · 外设依赖', '不能把毫秒脉冲开关当成永不疲劳的常开门 · 深脑与视网膜均需物理递送光', CYAN, 1.0, '物理边界')
        elif t < 68.0:
            H_hud.top_bar('D · 做得到 vs 做不到', '能精准检验环路因果 · 不能改写人类人生记忆或宣告失明终结', '把实验事实与科幻夸张彻底分开', GOLD)
            H_hud.inset_frame(IBOX, '小鼠行为环路因果 ↔ 临床严谨边界', anchor_xy=(450, 230), accent=GOLD)
            H_hud.hud_card((24, 344, 535, 412), '做得到：选定神经元亚群毫秒级因果检验', '做不到：小鼠恐惧冻结 ≠ 操控人类记忆 · 部分光感定位 ≠ 恢复正常裸眼视觉', GOLD, 1.0, '科学诚实')
        else:
            H_hud.top_bar('D · 结语 · EIGENLENS 第 2 期', '当年的「牵强设想」，今天已是实验室日常的因果标尺', '《光遗传学》· 停在已发表证据与真实边界之内', GOLD)
            H_hud.inset_frame(IBOX, '从 1979 设想到活体神经环路因果开关', anchor_xy=(450, 230), accent=GOLD)
            H_hud.hud_card((24, 344, 535, 412), '光遗传学：基因定靶 · 光定时刻', 'EigenLens 主观知识 · 第 2 期 · 感谢观看', GOLD, 1.0, '全片收束')
        H_hud.progress(frac, 3, GOLD)

    return H_hud.finish()


SCENES = {
    'SF01_open_title': 5.0,
    'SF02_1979_request': 4.0,
    'SF03_microbe_clues': 8.0,
    'SF04_crick_quote': 11.0,
    'SF12_neuron_select': 10.0,
    'SF05_nobel_portraits': 11.0,
    'SF06_switch_diagram': 9.0,
    'SF07_main_title': 7.0,
    'SF13_spike_causality': 52.0,
    'SF08_early_attempts': 16.0,
    'SF09_chr2_channel': 8.0,
    'SF14_orexin_q': 16.0,
    'SF10_mouse_tripo': 19.0,
    'SF15_br_pump_channel': 62.0,
    'SF16_chr_path': 120.0,
    'SF17_credit_word': 22.0,
    'SF18_invivo_dual': 96.0,
    'SF19_engram': 88.0,
    'SF20_retina_intro': 16.0,
    'SF11_eye_goggles': 24.0,
    'SF21_partial_vision': 46.0,
    'SF22_regulatory': 94.0,
    'SF23_limits_close': 100.0,
}

def render_scene(name: str):
    init_assets()
    dur = SCENES[name]
    n_frames = int(round(dur * FPS))
    out_mp4 = f'{OUT_DIR}/{name}.mp4'
    out_png = f'{OUT_DIR}/{name}.png'
    t0 = time.time()
    hud_cache: dict[int, np.ndarray] = {}

    cmd = [
        'ffmpeg', '-loglevel', 'error', '-y',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
        '-i', '-',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17',
        '-pix_fmt', 'yuv420p', out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    poster_idx = int(n_frames * 0.42)

    for i in range(n_frames):
        t = i / FPS
        bg_rgb, q = _eval_scene(name, t)
        if q not in hud_cache:
            hud_cache[q] = _build_hud(name, q, dur)
        u8 = blend_hud(bg_rgb, hud_cache[q])
        if i == poster_idx:
            # Save 1280x720 poster PNG
            poster_720 = cv2.resize(cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), (1280, 720), interpolation=cv2.INTER_LANCZOS4)
            cv2.imwrite(out_png, poster_720)
        proc.stdin.write(u8.tobytes())

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f'ffmpeg failed for {name} rc={rc}')
    dt = time.time() - t0
    print(f'[DONE] {name:22s} dur={dur:5.1f}s ({n_frames:4d}f) in {dt:5.1f}s ({n_frames/max(dt,0.1):.1f} fps)', flush=True)


def main():
    init_assets()
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SCENES.keys())
    t_start = time.time()
    # Backup previous styleframes before overwriting
    bak_dir = f'{OUT_DIR}/before_fullbleed_{time.strftime("%H%M%S")}'
    os.makedirs(bak_dir, exist_ok=True)
    for n in names:
        for ext in ('.mp4', '.png'):
            src = f'{OUT_DIR}/{n}{ext}'
            if os.path.isfile(src):
                shutil.copy2(src, f'{bak_dir}/{n}{ext}')
    print(f'Backed up {len(names)} styleframes to {bak_dir}', flush=True)

    # Render in parallel across 4 worker processes (fork inherits preloaded SEQS & PLATES cow!)
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(render_scene, n): n for n in names}
        for fut in as_completed(futs):
            fut.result()

    print(f'ALL {len(names)} FULL-BLEED 16:9 STYLEFRAMES DONE in {time.time() - t_start:.1f}s', flush=True)


if __name__ == '__main__':
    main()
