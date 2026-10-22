"""A1 — what lithography is (F44, F55). Variants:

  cut      A1_02  clay wafer with a wedge cut away: substrate and film layers in section
  spin     A1_03  yellow-room spin coater: amber resist spreads into an even film
  expose   A1_04  energy: light through a patterned (transmissive, generic) mask prints a glow on the resist
  process  A1_06  clay section: develop -> etch -> deposit, one layer of wiring left behind
           A1_07  the cycle repeats faster and faster; the stack grows, the camera rises
  stack    A1_09  xray chip section: ~100 layers, coarse at the top, the finest ~20 at the bottom glow violet
Illustrative, not to scale.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import a0_scenes as A0
import common as C
import materials as M
import sample_b1 as B
import styles

FRAMES = 360
VIOLET = (0.62, 0.45, 1.0)
GOLD = (0.83, 0.62, 0.3)


def _key(ob, f, **kw):
    for k, v in kw.items():
        setattr(ob, k, v)
        ob.keyframe_insert(k, frame=f)


_box = A0._box
_cyl = A0._cyl


def _apply_scale(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def _additive(name, color):
    """Emission added over a fully transparent surface: invisible at strength 0 (no black card)."""
    m = M.emission(name, color, 0.0)
    nt = m.node_tree
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(nt.nodes["Emission"].outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def _floor(mat):
    return _box("Floor", (0, 0, -0.6), (60, 60, 0.1), mat)


def _shot_frames(sid, default):
    """Shot length in frames from storyboard.timed.yaml (real VO timing), so no key ends before the shot does."""
    try:
        import os
        import yaml
        import paths
        sb = yaml.safe_load(open(os.path.join(paths.EP, "storyboard/storyboard.timed.yaml"), encoding="utf-8"))
        return max(1, round(next(x for x in sb["shots"] if x["id"] == sid)["duration"] * 24))
    except Exception:
        return default


# ---- A1_02 ---------------------------------------------------------------------------------
def cut(sc, rnd):
    clay = M.principled("Clay", (0.7, 0.7, 0.7))
    _floor(clay)
    bpy.ops.mesh.primitive_cube_add(location=(1.2, -1.2, 0.0))
    wedge = bpy.context.object
    wedge.scale = (1.2, 1.2, 1.0)
    wedge.hide_render = wedge.hide_viewport = True
    # substrate + three films, each its own muted clay tone so the section reads as separate materials (the clay
    # style would flatten 'structure' to one grey, so the layers carry role 'emitter', which keeps its material);
    # a thin dark seam sits between neighbours. Thickness ratios are not to scale (audit_A1: simplified)
    z = -0.5
    layers = ((0.30, (0.34, 0.36, 0.41)),            # silicon substrate: cool dark grey
              (0.075, (0.88, 0.74, 0.48)),           # film 1: warm sand
              (0.065, (0.48, 0.64, 0.84)),           # film 2: blue-grey
              (0.055, (0.84, 0.56, 0.48)))           # film 3: dusty rose
    seam = M.principled("LayerSeam", (0.08, 0.08, 0.085), roughness=0.6)
    for k, (th, col) in enumerate(layers):
        d = _cyl(f"Layer{k}", 2.0, th - 0.01, (0, 0, z + th / 2), M.principled(f"L{k}", col, roughness=0.55),
                 verts=160, role="emitter")
        b = d.modifiers.new("Cut", "BOOLEAN")
        b.object = wedge
        b.operation = "DIFFERENCE"
        if k:                                           # seam below every film: a slightly inset dark disc
            s_ = _cyl(f"Seam{k}", 1.99, 0.01, (0, 0, z), seam, verts=160, role="emitter")
            bs = s_.modifiers.new("Cut", "BOOLEAN")
            bs.object = wedge
            bs.operation = "DIFFERENCE"
        z += th
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    B._area("ClayFill", (-6, -5, 2), (1.3, 0, -0.9), 6, 500, (0.95, 0.97, 1.0))   # lifts the cut faces
    n = _shot_frames("A1_02", 145)
    B._camera("CamA1_02", [(1, (0.6, -0.6, -0.3), (-2.5, -6.0, 2.6), 45, 8.0),
                           (n, (0.8, -0.7, -0.32), (2.8, -6.4, 0.8), 50, 8.0)])


# ---- A1_03 ---------------------------------------------------------------------------------
def _film_mesh(name, R, t, segs=160):
    """A spun resist film as a lathe with two shapes on the same rings. Basis: flat top of thickness t, a faint edge
    bead, then a wetting meniscus tapering to zero at radius R (no vertical wall). Shape key 'Dome': the freshly
    dispensed puddle, a smooth cap. Origin at the film's base centre."""
    fr = (0.0, 0.3, 0.55, 0.75, 0.87, 0.93, 0.975, 1.0)
    spun = (1.0, 1.0, 1.0, 1.0, 1.05, 1.3, 0.75, 0.0)
    dome = tuple((1 - f * f) ** 0.5 * 1.6 for f in fr)

    def ring(f, z):
        if f == 0.0:
            return [(0.0, 0.0, z)]
        return [(f * R * math.cos(2 * math.pi * j / segs), f * R * math.sin(2 * math.pi * j / segs), z)
                for j in range(segs)]
    verts, faces, idx = [], [], []
    for f, z in zip(fr, spun):
        r = ring(f, t * z)
        idx.append(list(range(len(verts), len(verts) + len(r))))
        verts += r
    c = len(verts)
    verts.append((0.0, 0.0, 0.0))
    for j in range(segs):
        j1 = (j + 1) % segs
        faces.append((idx[0][0], idx[1][j], idx[1][j1]))
        for a_, b_ in zip(idx[1:], idx[2:]):
            faces.append((a_[j], b_[j], b_[j1], a_[j1]))
        faces.append((idx[-1][j1], idx[-1][j], c))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.shape_key_add(name="Basis")
    sk = ob.shape_key_add(name="Dome")
    k = 0
    for f, z in zip(fr, dome):
        for p in ring(f, t * z):
            sk.data[k].co = p
            k += 1
    return ob, sk


def spin(sc, rnd):
    n = _shot_frames("A1_03", 197)
    C.set_world(top=(0.04, 0.03, 0.005), horizon=(0.02, 0.015, 0.002), bottom=(0.002, 0.002, 0.0))
    steel = M.polished_steel("Bowl", 0.5)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.0, depth=1.2, vertices=192, end_fill_type="NOTHING", location=(0, 0, -0.5))
    bowl = bpy.context.object
    bowl.data.polygons.foreach_set("use_smooth", [True] * len(bowl.data.polygons))   # no faceted bands on the rim
    bowl.modifiers.new("Wall", "SOLIDIFY").thickness = 0.08
    bowl.data.materials.append(steel)
    styles.tag(bowl, "structure")
    _cyl("Chuck", 0.6, 0.4, (0, 0, -0.25), steel)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    rot = bpy.context.object
    rot.name = "Spinner"
    wafer = _cyl("Wafer", 2.0, 0.03, (0, 0, 0), M.principled("WaferSi", (0.4, 0.4, 0.45), metallic=1.0, roughness=0.04),
                 verts=192)
    wafer.parent = rot
    # orientation notch: a small V cut into the rim (SEMI M1; about 1 mm on a 300 mm wafer, exaggerated here),
    # not a raised feature. The same cutter trims the resist film so the film follows the rim
    bpy.ops.mesh.primitive_cube_add(location=(2.0, 0, 0), rotation=(0, 0, math.radians(45)))
    cutter = bpy.context.object
    cutter.name = "NotchCutter"
    cutter.scale = (0.045, 0.045, 0.2)
    cutter.hide_render = cutter.hide_viewport = True
    cutter.parent = rot
    nb = wafer.modifiers.new("Notch", "BOOLEAN")
    nb.object = cutter
    nb.operation = "DIFFERENCE"
    bpy.context.view_layer.objects.active = wafer
    bpy.ops.object.modifier_move_to_index(modifier="Notch", index=0)   # edge split after the cut: flat mirror top
    resist = M.principled("Resist", (0.9, 0.42, 0.04), roughness=0.05, coat=1.0)
    rb = resist.node_tree.nodes["Principled BSDF"]
    rb.inputs["Transmission Weight"].default_value = 0.35
    # the puddle is a dome with a wetting edge; it spreads as the wafer spins up, reaches the rim, then thins
    # (spin-off) to a film far thinner than the wafer, with a faint edge bead (MicroChemicals, A1_sources S9)
    film, dome = _film_mesh("ResistFilm", 1.985, 0.012)
    film.data.materials.append(resist)
    styles.tag(film, "structure")
    film.location = (0, 0, 0.0153)
    film.parent = rot
    fb = film.modifiers.new("Notch", "BOOLEAN")
    fb.object = cutter
    fb.operation = "DIFFERENCE"
    for f, xy, z in ((1, 0.10, 1.6), (40, 0.14, 2.0), (62, 0.2, 1.9), (90, 0.5, 1.4), (106, 1.0, 1.0),
                     (150, 1.0, 0.28), (n + 10, 1.0, 0.22)):
        _key(film, f, scale=(xy, xy, z))
    for f, v in ((1, 1.0), (62, 1.0), (106, 0.0)):                   # puddle cap -> flat film with an edge bead
        dome.value = v
        dome.keyframe_insert("value", frame=f)
    # spin coating: resist is dispensed while the wafer turns slowly, then it spins up to a few thousand rpm
    # (MicroChemicals application notes; research/visual/A1_sources.md). 3000 rpm = 750 deg per frame at 24 fps,
    # read through motion blur; the keys run past the shot end so the wafer never stops on screen
    _key(rot, 1, rotation_euler=(0, 0, 0))
    _key(rot, 60, rotation_euler=(0, 0, math.radians(60)))          # dispense, wafer turning slowly
    _key(rot, 90, rotation_euler=(0, 0, math.radians(60 + 15 * 750)))   # ramp (about half the top speed on average)
    _key(rot, n + 10, rotation_euler=(0, 0, math.radians(60 + 15 * 750 + (n + 10 - 90) * 750)))
    for fc in C.fcurves(rot.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    k = 0
    for f0 in range(104, n + 1, 3):                                 # excess flung off the rim once the film reaches it
        for _ in range(2):
            th = 2 * math.pi * rnd.random()
            p0 = Vector((2.0 * math.cos(th), 2.0 * math.sin(th), 0.03))
            tang = Vector((-math.sin(th), math.cos(th), 0.0))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=tuple(p0))
            d = bpy.context.object
            d.name = f"Fling{k}"
            d.data.materials.append(resist)
            styles.tag(d, "structure")
            ff = f0 + rnd.randint(0, 2)
            _key(d, 1, hide_render=True)
            _key(d, ff, hide_render=False, location=tuple(p0))
            _key(d, ff + 6, location=tuple(p0 + tang * 1.4 + Vector((p0.x, p0.y, 0)) * 0.08))
            _key(d, ff + 7, hide_render=True)
            k += 1
    stream = _cyl("Drip", 0.04, 3.0, (0, 0, 1.55), resist, verts=12)
    _key(stream, 1, scale=(1, 1, 1))
    _key(stream, 60, scale=(1, 1, 1))
    _key(stream, 75, scale=(0.0, 0.0, 1))
    _cyl("Nozzle", 0.08, 0.6, (0, 0, 3.3), steel)
    yellow = M.emission("YellowRoom", (1.0, 0.72, 0.18), 6.0)
    for k in range(4):                                              # yellow light strips mirrored in the wafer: low
        _box(f"Strip{k}", (-1.0 + 0.6 * k, 9.0 + 1.6 * k, 0.9 + 0.3 * k), (9.0, 0.3, 0.1), yellow,   # and far, so the
             role="emitter")                                         # grazing view picks them up in the mirror
    bpy.ops.object.light_add(type="AREA", location=(0, 2, 6))
    l = bpy.context.object
    l.data.energy = 600
    l.data.size = 6
    l.data.color = (1.0, 0.75, 0.3)
    styles.tag(l, "rig")
    sc.render.use_motion_blur = True
    B._camera("CamA1_03", [(1, (0.6, 0.2, 0.0), (2.6, -2.8, 0.45), 50, 2.8),
                           (n, (-0.2, 0.4, 0.0), (1.4, -3.2, 0.5), 50, 2.8)])
    cam = bpy.data.objects["CamA1_03"]
    for ob in (cam, bpy.data.objects["CamA1_03Aim"]):              # an even drift: no ease-out stop at the end
        for fc in C.fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


# ---- A1_04 ---------------------------------------------------------------------------------
def _frustum(name, z0, h0, z1, h1, mat):
    """Open square tube (no end caps, so no flat glow lids) from half-width h0 at z0 to h1 at z1."""
    v = [(-h0, -h0, z0), (h0, -h0, z0), (h0, h0, z0), (-h0, h0, z0),
         (-h1, -h1, z1), (h1, -h1, z1), (h1, h1, z1), (-h1, h1, z1)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    styles.tag(ob, "emitter")
    return ob


def expose(sc, rnd):
    import b7_scenes
    n = _shot_frames("A1_04", 191)
    C.set_world(top=(0, 0, 0), horizon=(0, 0, 0), bottom=(0, 0, 0))
    # the resist on the wafer: a dim amber slab (an emitter keeps it visible on the energy look's black)
    _box("ResistLayer", (0, 0, -0.08), (3.4, 3.4, 0.16), M.emission("ResistDark", (0.5, 0.26, 0.06), 0.08), role="emitter")
    # reduction printing: scanners shrink the reticle pattern four times (ASML; A1_sources S4, S10 p2), so the beam
    # narrows below the mask and the glowing latent pattern is a quarter the size of the mask pattern. The single
    # lens stands for the projection optics (示意); B7 shows the real mirror train
    red = 4.0
    glow = A0.circuit_emission("Latent", (0.95, 0.7, 0.3), 0.0, scale=0.6)
    bpy.ops.mesh.primitive_plane_add(size=4.0 / red, location=(0, 0, 0.005))
    p = bpy.context.object
    p.data.materials.append(glow)
    styles.tag(p, "emitter")
    M.set_emission_strength(glow, 60, 0.0)
    M.set_emission_strength(glow, 115, 3.6)
    _box("MaskPlate", (0, 0, 3.0), (4.6, 4.6, 0.12), M.principled("MaskGlass", (0.5, 0.5, 0.55)))
    lit = A0.circuit_emission("MaskLit", (0.85, 0.75, 1.0), 0.0, scale=0.6)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 3.07))
    mp = bpy.context.object
    mp.data.materials.append(lit)
    styles.tag(mp, "emitter")
    M.set_emission_strength(lit, 20, 0.0)
    M.set_emission_strength(lit, 40, 3.0)
    bm = b7_scenes._cone_mat("ExposeBeam", 0.3)
    _frustum("Beam", 3.06, 2.0, 9.5, 2.0, bm)                        # parallel illumination onto the mask
    shadow = b7_scenes._cone_mat("ShadowBeam", 0.16)                # patterned light, converging onto the resist
    _frustum("BeamBelow", 2.94, 2.0, 0.01, 2.0 / red, shadow)
    zl, hl = 1.7, 2.0 / red + (2.0 - 2.0 / red) * (1.7 - 0.01) / (2.94 - 0.01)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48, location=(0, 0, zl))
    ln = bpy.context.object
    ln.name = "ReductionLens"
    ln.scale = (hl + 0.25, hl + 0.25, 0.22)
    ln.data.polygons.foreach_set("use_smooth", [True] * len(ln.data.polygons))
    ln.data.materials.append(M.principled("LensGlass", (0.6, 0.6, 0.65)))
    styles.tag(ln, "structure")
    bpy.ops.mesh.primitive_torus_add(major_radius=hl + 0.3, minor_radius=0.025, major_segments=128, location=(0, 0, zl))
    ring = bpy.context.object                                        # the lens mount, drawn as a thin cool outline
    ring.data.materials.append(M.emission("LensRing", (0.45, 0.7, 1.0), 0.7))
    styles.tag(ring, "emitter")
    # crane down from above the mask to a three-quarter view outside the beam: mask on top, the converging light,
    # the small pattern glowing on the resist; the last stretch keeps drifting so the shot never freezes
    cam = B._camera("CamA1_04", [(1, (0, 0, 3.0), (0.0, -6.0, 9.0), 35, 11.0),
                                 (int(n * 0.72), (-0.5, 0, 1.2), (2.6, -8.8, 7.4), 35, 11.0),
                                 (n, (-0.5, 0, 1.1), (2.9, -8.3, 6.9), 35, 11.0)])
    for ob in (cam, bpy.data.objects["CamA1_04Aim"]):
        for fc in C.fcurves(ob.animation_data.action):
            fc.keyframe_points[-1].interpolation = "LINEAR"
            if len(fc.keyframe_points) > 2:
                fc.keyframe_points[-2].handle_right_type = "VECTOR"


# ---- A1_06 / A1_07 -------------------------------------------------------------------------
def process(sc, rnd):
    clay = M.principled("ClayProc", (0.7, 0.7, 0.7))
    film_m = M.principled("Film", (0.55, 0.58, 0.62))
    resist_m = M.principled("ResistClay", (0.86, 0.8, 0.66))
    metal_m = M.principled("Metal", GOLD, metallic=0.6, roughness=0.35)
    _box("Substrate", (0, 0, -0.5), (8.0, 2.0, 1.0), clay)
    n = 9
    w = 8.0 / n
    exposed = [k % 2 == 1 for k in range(n)]
    for k in range(n):
        x = -4.0 + w * (k + 0.5)
        film = _apply_scale(_box(f"Film{k}", (x, 0, 0.15), (w, 2.0, 0.3), film_m))
        res = _apply_scale(_box(f"Resist{k}", (x, 0, 0.42), (w, 2.0, 0.24), resist_m, role="emitter"))
        # scale about the bottom face: move the origin down
        for ob, zb in ((film, 0.0), (res, 0.3)):
            ob.data.transform(Matrix.Translation((0, 0, ob.location.z - zb)))
            ob.location.z = zb
        # damascene order (IBM): develop -> etch the trench -> strip the resist -> deposit metal over the whole
        # wafer (filling and overfilling the trenches) -> chemical-mechanical polish back to the dielectric
        if exposed[k]:
            _key(res, 20, scale=(1, 1, 1))
            _key(res, 55, scale=(1, 1, 0.001))                      # develop: exposed resist dissolves
            _key(res, 1, hide_render=False)
            _key(res, 56, hide_render=True)                         # no flat sliver left on the film
            _key(film, 60, scale=(1, 1, 1))
            _key(film, 95, scale=(1, 1, 0.001))                     # etch: trench bites into the film
            met = _apply_scale(_box(f"Metal{k}", (x, 0, 0.0), (w * 0.98, 2.0, 0.3), metal_m, role="emitter"))
            met.data.transform(Matrix.Translation((0, 0, 0.15)))
            _key(met, 1, scale=(1, 1, 0.001), hide_render=True)     # no metal anywhere before the strip ends
            _key(met, 121, hide_render=True)
            _key(met, 122, scale=(1, 1, 0.001), hide_render=False)
            _key(met, 145, scale=(1, 1, 1))                         # deposit: metal fills the trench
        else:
            _key(res, 98, scale=(1, 1, 1))
            _key(res, 118, scale=(1, 1, 0.001))                     # strip the remaining resist (before metal)
            _key(res, 1, hide_render=False)
            _key(res, 119, hide_render=True)
    over = _apply_scale(_box("Overburden", (0, 0, 0.0), (8.0, 2.0, 0.14), metal_m, role="emitter"))
    over.data.transform(Matrix.Translation((0, 0, 0.07)))
    over.location.z = 0.3
    _key(over, 1, scale=(1, 1, 0.001))
    _key(over, 124, scale=(1, 1, 0.001))
    _key(over, 145, scale=(1, 1, 1))                                # blanket deposition overfills the trenches
    _key(over, 152, scale=(1, 1, 1))
    _key(over, 174, scale=(1, 1, 0.001))                            # CMP polishes it away: lines left in the trenches
    _key(over, 1, hide_render=True)                                 # hidden while flat: no sliver on the film top
    _key(over, 123, hide_render=False)
    _key(over, 175, hide_render=True)
    # A1_07 (sim 191-341, after A1_06's 185 frames, so its first layer never shows in A1_06): the cycle repeats, faster and faster; each new layer grows on top with a violet flash
    flash = _additive("ExpoFlash", (0.42, 0.16, 1.0))               # saturated EUV violet: stays violet, no white
    # the exposure flash lights only the newest layer's top face (a full-frame card blew the picture out)
    fl = _box("FlashSheet", (0, 0, 0.3), (8.0, 2.0, 0.005), flash, role="emitter")
    top = 0.3
    f = 192
    for c in range(12):
        dur = max(6, int(30 * 0.8 ** c))
        th = 0.3 * (1 + 0.06 * c)                                   # upper levels thicker and coarser (ASML: the
        grow = 1 + 0.1 * c                                          # most complex layers sit at the bottom)
        # every level is dielectric with metal embedded: wire levels carry parallel lines (direction alternating
        # from one wire level to the next), via levels carry vertical plugs; a continuous metal sheet would short
        # everything. As in a TEM cross-section, every level shows metal on the front cut face (y = -1): one line
        # of an along-x level lies on the face as a long bar, along-y lines end on it as dots, vias sit on it.
        # Metal faces stand 0.003 proud of the cut faces (flush faces z-fought into slivers)
        parts = [_apply_scale(_box(f"Stack{c}", (0, 0, 0), (8.0, 2.0, th), film_m, bevel=0.012))]   # bevel: seams read
        if c % 2 == 0:
            along_x = (c // 2) % 2 == 0
            if along_x:
                wl = 0.13 * grow
                cnt = max(3, 6 - c // 3)
                ys = [-1.003 + wl / 2 + (2.006 - wl) * j / (cnt - 1) for j in range(cnt)]   # first and last on faces
                for j, y in enumerate(ys):
                    parts.append(_apply_scale(_box(f"Stack{c}W{j}", (0, y, 0), (8.006, wl, th * 0.8), metal_m,
                                                   role="emitter")))
            else:
                wl = 0.22 * grow
                cnt = max(4, 7 - c // 3)
                for j in range(cnt):
                    parts.append(_apply_scale(_box(f"Stack{c}W{j}", (-3.6 + 7.2 * j / (cnt - 1), 0, 0),
                                                   (wl, 2.006, th * 0.8), metal_m, role="emitter")))
        else:
            vs = 0.12 * grow
            for j in range(5):
                y = -1.003 + vs / 2 if j % 2 == 0 else -0.2 + 0.5 * (j // 2)     # three vias on the cut face
                parts.append(_apply_scale(_box(f"Stack{c}V{j}", (-3.0 + 1.5 * j, y, 0), (vs, vs, th), metal_m,
                                               role="emitter")))
        for lay in parts:
            _key(lay, 1, hide_render=True)
            _key(lay, f, hide_render=False)
            lay.data.transform(Matrix.Translation((0, 0, th / 2)))
            lay.location.z = top
            _key(lay, 1, scale=(1, 1, 0.001))
            _key(lay, f, scale=(1, 1, 0.001))
            _key(lay, f + dur // 2, scale=(1, 1, 1))
        _key(fl, f + dur // 2 - 1, location=(0, 0, top + th + 0.004))
        M.set_emission_strength(flash, f + dur // 2 - 1, 0.0)
        M.set_emission_strength(flash, f + dur // 2, 1.6)
        M.set_emission_strength(flash, f + dur // 2 + 3, 0.0)
        top += th
        f += dur
    for fc in C.fcurves(fl.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    B._area("ClayKey", (5, -6, 8), (0.8, 0, 0.6), 8, 1800, (1.0, 0.98, 0.95))
    # last keys lie past the shot ends (A1_06 185 frames, A1_07 ends at sim frame 341): the ease-out never shows
    B._camera("CamA1_06", [(1, (0, 0, 0.2), (0.0, -12.5, 1.4), 50, 11.0), (200, (0, 0, 0.2), (0.9, -12.5, 1.51), 50, 11.0)])
    B._camera("CamA1_07", [(191, (0, 0, 0.6), (0.8, -12.5, 1.6), 50, 11.0), (355, (0.3, 0, 2.8), (7.6, -18.2, 6.9), 45, 11.0)])


# ---- A1_09 ---------------------------------------------------------------------------------
def _band_mat(name, scale, color, emit=0.0, emit_color=None):
    m = M.principled(name, color, metallic=0.5, roughness=0.4)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.48
    ramp.color_ramp.elements[1].position = 0.52
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Alpha"])
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_color or VIOLET), 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


EUV_SAT = (0.42, 0.16, 1.0)          # the saturated EUV violet used for beams: stays violet instead of clipping white


def stack(sc, rnd):
    C.set_world(top=(0.9, 0.91, 0.93), horizon=(0.78, 0.79, 0.82), bottom=(0.6, 0.61, 0.64))
    _box("ChipSub", (0, 0, -0.4), (6.0, 6.0, 0.8), M.principled("SubPanel", (0.78, 0.8, 0.82), metallic=0.2,
                                                                roughness=0.45), role="shell")
    # 60 levels, finest at the bottom, thicker and coarser upward (ASML annual report 2021: the most complex layers
    # sit at the bottom). Only a few of the bottom levels are EUV: about 8 violet levels within the lowest 12, two
    # left grey because EUV and DUV layers interleave on the same chip (ASML; audit_A1 A1_09). Count illustrative (示意)
    n = 60
    euv = {0, 1, 3, 4, 5, 7, 8, 10}
    z = 0.0
    for k in range(n):
        th = 0.05 if k < 12 else 0.05 + 0.0021 * (k - 12)
        scale = 90.0 - 1.4 * k if k < 50 else 18.0
        if k in euv:                                                 # solid, matte, saturated: reads violet on the
            m = M.principled(f"Lay{k}", (0.03, 0.0, 0.12), roughness=0.7,    # light studio instead of washing out
                             emission=(0.30, 0.06, 1.0), emission_strength=1.0)      # (as styles.xray does for rays)
            m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.15
        else:
            m = _band_mat(f"Lay{k}", scale, (0.6, 0.62, 0.68) if k >= 12 else (0.5, 0.52, 0.58))
        lay = _box(f"ChipLayer{k}", (0, 0, z + th / 2), (5.6, 5.6, th * 0.72), m,
                   role="emitter" if k in euv else "structure")
        lay.rotation_euler = (0, 0, 0 if k % 2 else math.pi / 2)
        z += th * 1.12
    B._area("MKey", (0, -9, 8), (0.9, 0, 0), 16, 2500, (0.8, 0.85, 1.0))
    nf = _shot_frames("A1_09", 169)
    # side view of the whole stack -> three-quarter view down onto the glowing bottom levels; the last key lies past
    # the shot end so the orbit is still moving on the last frame
    B._camera("CamA1_09", [(1, (0, 0, 2.7), (0.0, -18.0, 2.7), 40, 8.0),
                           (nf + 20, (0.3, 0, 0.75), (8.6, -9.8, 4.4), 40, 5.6)])


def build(variant="cut", seed=21):
    sc = C.reset_scene(FRAMES)
    C.set_world(top=(0.03, 0.035, 0.05), horizon=(0.012, 0.014, 0.02), bottom=(0.003, 0.004, 0.006))
    C.set_color_management(exposure=0.4)
    rnd = random.Random(seed)
    {"cut": cut, "spin": spin, "expose": expose, "process": process, "stack": stack}[variant](sc, rnd)
    return sc
