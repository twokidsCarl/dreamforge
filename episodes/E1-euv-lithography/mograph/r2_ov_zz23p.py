"""Round-23 overlays, panel agent (R23_ROOT_CAUSE row 4 - rides only on the 3D structural change of each shot):
  A0_03  the R18 2D count panel goes: 250+ / 43 / 20 are printed on the 3D crate stack / ULD / trailer in front of the
         plate (panel_r23_crates). Only the planes keep a tag, pinned to the freighter in the plate ("好几架货机",
         narration wording, no invented number).
  B1_18  the 2D spectrum panel goes: the bars are a 3D array (panel_r23_spectrum); this overlay only writes the text
         (title, nm ticks, +-1 % window, Sn8+..Sn14+ legend in the same blue->violet ion colours) at the screen
         positions of that 3D chart.
Active only while the shot is in its module's R23_PANEL set (read from the module source) and ENABLED.
"""
import importlib.util
import os
import re

ENABLED = True
OVERLAYS = {}
NO_STORYBOARD_LABELS = set()
_HERE = os.path.dirname(os.path.abspath(__file__))
_SH = os.path.join(_HERE, "..", "blender", "shots")
_SC = os.path.join(_HERE, "..", "blender", "scripts")


def _r23(module):
    try:
        src = open(os.path.join(_SH, module + ".py"), encoding="utf-8").read()
        m = re.search(r"^R23_PANEL\s*=\s*\{([^}]*)\}", src, re.M)
        return set(re.findall(r"\"([A-Z0-9_]+)\"", m.group(1))) if m else set()
    except OSError:
        return set()


def _mod(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def a003(img, t, dur, W, H):
    from r2_ov_common import Layer, fade
    L = Layer(W, H)
    a = fade(t, 2.6, None, 0.5)                   # narration order: crates, containers, then planes, then trucks
    if a <= 0:
        return img
    u = min(1.0, max(0.0, t / dur))
    anchor = (0.60 - 0.26 * u, 0.40 - 0.02 * u)   # freighter nose door in the plate, follows the truck move
    L.label(anchor, (anchor[0] - 0.05, 0.12), ["好几架货机"], a=a)
    return L.compose(img)


def b118(img, t, dur, W, H):
    S = _mod(os.path.join(_HERE, "r2_ov_source.py"), "r2_ov_source_r23p")
    G = _mod(os.path.join(_SC, "panel_r23_spectrum.py"), "panel_r23_spectrum_ov")
    L = S.Layer(W, H)
    a = S.ease((t - 0.2) / 0.5)
    k = W / (G.D * G.SENSOR / G.LENS)

    def sx(xm):
        return W / 2 + xm * k

    def sy(ym):
        return H / 2 - ym * k

    x0, x1, yb, yt = sx(G.X0), sx(G.X1), sy(G.YB), sy(G.YB + G.HMAX * 1.08)
    L.text((x0, yt - 0.075 * H), "锡离子谱线（示意）", 0.042 * H, S.INK, a)
    for nm in G.TICKS:
        L.text((sx(G.X(nm)), yb + 9), f"{nm:g}", 0.036 * H, S.CYAN if nm == 13.5 else S.INK, a, anchor="ma")
    L.text((x1 + 0.03 * W, yb + 9), "nm", 0.036 * H, S.INK2, a)
    xw = sx(G.X(13.5 * 1.01)) + 8
    L.text((xw, yt + 2), "镜子反射窗口", 0.034 * H, S.CYAN, a)
    L.text((xw, yt + 2 + 0.045 * H), "±1 %", 0.034 * H, S.CYAN, a)
    f = t * 24.0
    ions = ["Sn⁸⁺", "Sn⁹⁺", "Sn¹⁰⁺", "Sn¹¹⁺", "Sn¹²⁺", "Sn¹³⁺", "Sn¹⁴⁺"]
    for i, s in enumerate(ions):
        col = tuple(int(255 * (0.4 + 0.6 * c)) for c in G.ICOL[i])
        ai = a * S.ease((f - (G.F0 + i * G.FK)) / 6.0)
        yy = yt - 0.01 * H + i * 0.064 * H
        L.rect((x1 + 0.05 * W, yy + 0.012 * H, x1 + 0.05 * W + 0.012 * H, yy + 0.034 * H), (*col, 255), radius=2, a=ai)
        L.text((x1 + 0.06 * W, yy), s, 0.038 * H, col, ai)
    return L.compose(img)


if ENABLED and "A0_03" in _r23("r2_plates"):
    OVERLAYS["A0_03"] = a003
    NO_STORYBOARD_LABELS.add("A0_03")
if ENABLED and "B1_18" in _r23("r2_source"):
    OVERLAYS["B1_18"] = b118
