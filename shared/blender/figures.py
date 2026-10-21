"""Faceless human figures for scale: one metaball body per person (hooded clean-room suit, boots), so the
silhouette reads as a person instead of a cylinder with a ball on top. Feet stand at z = 0 of `loc`.

  person("Worker3", (x, y, z), height=1.75, pose="stand" | "work" | "walk", facing=deg, mat=..., role="env")
"""
import math

import bpy
from mathutils import Quaternion, Vector

import styles

_X = Vector((1, 0, 0))
_GROW = 1.35         # a metaball's surface sits well inside its influence radius; radii below are body sizes


def _capsule(mb, a, b, r):
    """A capsule element between points a and b (a metaball capsule lies along its local X)."""
    a, b = Vector(a), Vector(b)
    e = mb.elements.new(type="CAPSULE")
    e.co = (a + b) / 2
    e.radius = r * _GROW
    e.size_x = max(0.001, (b - a).length / 2)
    e.rotation = _X.rotation_difference((b - a).normalized())
    return e


def _ellipsoid(mb, c, r, sx, sy, sz):
    e = mb.elements.new(type="ELLIPSOID")
    e.co = c
    e.radius = r * _GROW
    e.size_x, e.size_y, e.size_z = sx, sy, sz
    return e


def person(name, loc, height=1.75, pose="stand", facing=0.0, mat=None, role="env"):
    k = height / 1.75
    mb = bpy.data.metaballs.new(name.replace(".", "_"))
    mb.resolution = 0.03
    mb.render_resolution = 0.012
    mb.threshold = 0.6

    def p(x, y, z):
        return Vector((x, y, z)) * k

    _ellipsoid(mb, p(0, 0, 1.62), 0.16 * k, 0.78, 0.86, 1.0)               # hooded head
    _capsule(mb, p(0, 0, 1.50), p(0, 0, 1.43), 0.11 * k)                   # neck under the hood
    _ellipsoid(mb, p(0, 0, 1.22), 0.30 * k, 0.78, 0.5, 1.0)                # chest and shoulders
    _ellipsoid(mb, p(0, 0, 0.98), 0.25 * k, 0.72, 0.52, 0.85)              # belly / hips of the suit
    stride = 0.16 if pose == "walk" else 0.0
    for s in (-1, 1):                                                        # legs and boots
        hip, foot = p(0.09 * s, 0, 0.88), p(0.1 * s, stride * s, 0.1)
        knee = (hip + foot) / 2 + p(0, 0.02, 0)
        _capsule(mb, hip, knee, 0.105 * k)
        _capsule(mb, knee, foot, 0.095 * k)
        _capsule(mb, foot, foot + p(0, -0.12, -0.03), 0.075 * k)
    for s in (-1, 1):                                                        # arms
        sh = p(0.2 * s, 0, 1.36)
        if pose == "work" and s == 1:                                        # right forearm reaches forward
            el, hand = p(0.24, -0.08, 1.08), p(0.2, -0.38, 1.12)
        else:
            swing = -stride * s * 0.8
            el, hand = p(0.25 * s, swing * 0.5, 1.07), p(0.25 * s, swing, 0.8)
        _capsule(mb, sh, el, 0.075 * k)
        _capsule(mb, el, hand, 0.065 * k)
    ob = bpy.data.objects.new(name.replace(".", "_"), mb)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(facing))
    if mat:
        mb.materials.append(mat)
    styles.tag(ob, role)
    return ob
