"""Round 19 (P1) mirror helpers for blender/shots/r2_misc.py only (R19_ROOT_CAUSE #2 "镜面哑光塑料 + 光锥散成雾").
Never used by the photons variant (B9_05 gold control). Shared mirror_r15 / misc_beam_r17/18 untouched.

mirror_mat   - high-reflective polished mirror (metallic 1, roughness ~0.05, LIGHT silver tone, no emission, no violet
               base): its brightness comes from reflecting the lit structure around it, not from light cards.
solid_mirror - k4A thick silver mirror blank: solid disc that fills (and slightly overlaps) a ring mount, a bright
               chamfered rim (highlight edge) and a darker ground back - reads as "a mirror", not as a donut ring.
landing      - soft landing highlight lying on a mirror face where a cone ends (thin wrapper of misc_beam_r17.landing,
               which is read-only and only imported).
"""
import bpy
from mathutils import Vector

import kit_r2 as K


def mirror_mat(name="MirrorR19", tone=(0.88, 0.89, 0.92), rough=0.05):
    return K.mat(name, tone, metal=1.0, rough=rough)


def solid_mirror(name, p, nrm, r, thick=0.07, back=0.004, mat=None, rim_mat=None, back_mat=None):
    """Mirror face centre = p (front face plane passes through p - n * back); returns [face, rim, back] objects."""
    n = Vector(nrm).normalized()
    mat = mat or mirror_mat(name + "M")
    rim_mat = rim_mat or K.mat(name + "RimM", (0.95, 0.95, 0.97), metal=1.0, rough=0.12)
    back_mat = back_mat or K.mat(name + "BackM", (0.32, 0.33, 0.36), metal=0.8, rough=0.45)
    q = Vector((0, 0, 1)).rotation_difference(n)
    obs = []
    fm, rm, bm = K.MB(), K.MB(), K.MB()
    fm.cyl(Vector((0, 0, -0.004)), r * 0.94, 0.008, seg=96)                    # polished optical face
    rm.ring(Vector((0, 0, -0.012)), r, r * 0.935, 0.024, seg=96)               # bright chamfer / highlight edge
    bm.cyl(Vector((0, 0, -0.008 - thick / 2)), r * 0.985, thick, seg=96)       # thick blank behind the face
    for mb_, nm, m in ((fm, "", mat), (rm, "Rim", rim_mat), (bm, "Blank", back_mat)):
        ob = mb_.obj(name + nm, m, bevel=0.002 if nm else 0.0)
        ob.rotation_euler = q.to_euler()
        ob.location = Vector(p) - n * back
        obs.append(ob)
    return obs


def landing(name, p, nrm, r, strength=7.0, light=2.0, color=None):
    import misc_beam_r17 as BR17
    return BR17.landing(name, Vector(p), Vector(nrm), r, color=color, strength=strength, light=light)
