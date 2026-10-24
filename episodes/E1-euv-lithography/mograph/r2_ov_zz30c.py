"""Round-30 overlay for A0_10 (main process; copy of r2_ov_zz26a gated on r2_cutaway.R30_A010): R29 p2 「照明系统的引线
现在指着一个空箱子，要改成指向光落点」 - the 照明系统 tag becomes a leader label onto the field-facet landing in the opened
housing (a010_r30 writes that point into the r26_house anchor). Everything else as R26:
Round-26 overlay for A0_10 (main process; rides on the R26_ROOT_CAUSE row 1 scene-level restructure a010_r26.py:
illuminator housing -> one front-facing mask turn -> projection barrel -> wafer). Same title card as r2_ov_cutaway.title;
adds three small part tags so the path reads 光源 → 照明 → 掩模（顶）→ 投影 → 晶圆 (R25 p2 改法 1), and moves the
「人 ≈ 1.8 m / 机器为示意」 tag above the figures (R25 p2 改法 3: the 55 % subtitle covered 「机器为示意」).
Active only while A0_10 is in r2_cutaway.R26_A010 and ENABLED."""
import os
import re
from r2_ov_common import CYAN, INK, INK2, VIOLET, Layer, anchor, ease, fade

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "shots")


def _r26(module, name):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^" + name + r"\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def title(img, t, dur, W, H):
    L = Layer(W, H)
    a = fade(t, 0.6, None, 0.8)
    txt, y0 = "一台光刻机里发生了什么", 0.06
    size = 0.6 * W / H / 11 * 1.0
    L.text((0.5, y0), txt, size, INK, a, anchor="ma", serif="bold")
    b = L.bbox((0.5, y0), txt, size, anchor="ma", serif="bold")
    k = ease((t - 1.4) / 1.0)
    if k > 0:
        b2 = L.bbox((b[0] / W, y0), "一台", size, serif="bold")
        b3 = L.bbox((b[0] / W, y0), "一台光刻机", size, serif="bold")
        x0, x1, y = b2[2], b3[2], b[3] + H * 0.014
        L.d.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(3, H * 0.008)), fill=(*VIOLET, int(255 * a)))
        L.g.rectangle((x0, y, x0 + (x1 - x0) * k, y + max(3, H * 0.008)), fill=(*VIOLET, int(160 * a)))
    L.text((0.5, b[3] / H + 0.045), "WHAT HAPPENS INSIDE AN EUV LITHOGRAPHY MACHINE", 0.026, INK2,
           fade(t, 1.6, None, 0.8), anchor="ma")
    a4 = fade(t, 3.0, None)
    d1, d0 = anchor("A0_10", t, "eng_dim", (0.2, 0.62)), anchor("A0_10", t, "eng_dim0", (0.2, 0.8))
    if a4 > 0:
        lw = max(2, int(H * 0.003))
        col = (*CYAN, int(240 * a4))
        L.d.line([L.P(d0), L.P(d1)], fill=col, width=lw)
        for p in (d0, d1):
            L.d.line([L.P((p[0] - 0.008, p[1])), L.P((p[0] + 0.008, p[1]))], fill=col, width=lw)
        L.tag((d1[0] - 0.012, d1[1] - 0.005), ["人 ≈ 1.8 m", "机器为示意"], a4, size=0.028, anchor="ra")   # top of the bar, clear of the subtitle
    # part tags (small, after the title has settled)
    hs, mk, br = (anchor("A0_10", t, k_, d_) for k_, d_ in
                  (("r26_house", (0.5, 0.55)), ("r26_mask", (0.66, 0.45)), ("r26_barrel", (0.66, 0.65))))
    if 0.05 < hs[0] < 0.95:
        L.label(hs, (hs[0] - 0.11, hs[1] + 0.05), ["照明系统"], fade(t, 2.2, None), accent=VIOLET, size=0.026)
    if 0.05 < mk[0] < 0.95:
        L.label(mk, (mk[0] + 0.045, mk[1] - 0.06), ["掩模"], fade(t, 2.5, None), accent=VIOLET, size=0.026)
    if 0.05 < br[0] < 0.95:
        L.label(br, (br[0] - 0.05, br[1] + 0.02), ["投影物镜"], fade(t, 2.8, None), accent=VIOLET, size=0.026)
    return L.compose(img)


if ENABLED and "A0_10" in _r26("r2_cutaway", "R30_A010") and "A0_10" in _r26("r2_cutaway", "R26_A010"):
    OVERLAYS["A0_10"] = title
    NO_STORYBOARD_LABELS.add("A0_10")
