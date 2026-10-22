"""Round 12 SF10: wake (Wan 3.0, round 11, f0-76: asleep -> eyes open) -> rise (Wan 3.0 first/last: lying eyes-open
-> half-up keyframe, one tail sliding back, no dissolve) -> walk (Wan 2.6 from the rise's last frame).
No optical-flow bridges, no blink frames; push ~4 %/s."""
import math
import sf_r12 as R12, sf_r11 as R11, sf_r10 as R10
from sf_r12 import _fat, _clip12, ease, lin
WK, RA, WL = 'sf10_wake11', 'sf10_riseA12', 'sf10_walk12'
def src13(t):
    if t < 2.6: return _fat(WK, t*24/2.6)
    if t < 3.4: return _fat(WK, 24+(t-2.6)/0.8*36)
    if t < 3.933: return _fat(WK, 60+(t-3.4)/0.533*16)
    if t < 4.15: return _fat(RA, (t-3.933)/0.217*20)
    if t < 5.75: return _fat(RA, 20+(t-4.15)/1.6*80)
    if t < 6.15: return _fat(RA, 100+(t-5.75)/0.4*49)
    return _fat(WL, (t-6.15)*30)
R12.src10 = src13
R12._cache.pop('trk12', None)
R10.CAM10 = [1.0, 0.042, 0.16, 0.10]
R11.rerun10('sf10', [
    ("circ_img(img('sf10_orexin'), r, zoom=1.15+0.05*lin(t, 3), cx=0.5, cy=0.47)", "circ_img(_orx11(), r, zoom=1.55+0.10*lin(t, 3), cx=0.73, cy=0.53)"),
    ("radial(W, H, C[0], C[1]-6*s, 70*s, CYAN, 0.5*pl*a)", "radial(W, H, C[0]+4*s, C[1]+4*s, 46*s, CYAN, 0.55*pl*a)"),
    ("L = Layer(W, H); C = (1100*s, 250*s); R = int(138*s)", "L = Layer(W, H); C = (205*s, 352*s); R = int(116*s)"),
    ("z = 1.04+0.05*lin(t, SF10_D); cxx = 0.55-0.05*lin(t, SF10_D); cyy = 0.50", "z = CAM10[0]*math.exp(CAM10[1]*t); cxx = 0.53-0.03*ease(lin(t, 5.8))-CAM10[2]*ease(ramp(t, 5.8, 9.4)); cyy = 0.50-CAM10[3]*ease(ramp(t, 3.9, 6.2)); cxx = max(cxx, 0.5/z+0.004)"),
    ("cx_, cy_ = W*0.36, 112*s+120*s", "cx_, cy_ = W*0.74, 150*s"),
    ("L2.text((C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'", "plate_text(L2, (C[0], C[1]+R+34*s), '下丘脑外侧 · 食欲素神经元'"),
    ("L2.text((C[0], C[1]+R+62*s), '膜上装了光控通道，随光脉冲放电'", "plate_text(L2, (C[0]+6*s, C[1]+R+66*s), '膜上装了光控通道，随光脉冲放电'"),
])
