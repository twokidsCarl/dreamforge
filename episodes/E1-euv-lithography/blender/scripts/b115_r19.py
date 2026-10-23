"""Round 19 (P1) helper for r2_source variant "contrast" (B1_15). Started as a copy of b115_r18.py (left untouched).

R19 root cause #1 (R18 B1_15 = H1: the dark-metal mirror + chamber reflection read as "a matte light-grey wall panel";
only an oblique slice of the dish was seen, concave / hole / plasma not on one readable axis; three frames static):
  * KEEP: external cut view, true through-hole (chamfered lip, dark bore, entry tube), orange drive laser through the
    hole onto the plasma, cut-away vessel with flanges / viewports / H2 nozzles, silver-white debris;
  * CAMERA: turned to face the concave side from outside at ~3/4 (about 28 deg off the mirror axis): the whole
    concave face + the centre hole are in frame, the plasma floats on the axis in front of the bowl, and the dashed
    metrology axis runs hole -> plasma -> on toward the IF (one readable axis);
  * MIRROR FACE: bright highly polished metal (light tone, roughness 0.04, no emission, no violet base, no rainbow);
    the plasma sits on the axis INSIDE the mirror's focal length (vertex 0.25 from the plasma, f = 0.42), so the
    dish shows a magnified upright image of the violet plasma glow (a makeup-mirror image, visible from the 3/4
    camera) - the face's brightness comes only from that reflection and the plasma-lit chamber parts around it;
    every lamp / fill and the lit viewport windows are invisible to glossy rays (no cards, no softboxes);
  * PUSH-IN: 1.5 s dolly to 0.78 of the distance (+ focus pull plasma -> mirror face): mirror screen area grows
    >= 15 % between the job frames.
Not repeating: no dark no-reflection face (R18), no solid hub (R17), no in-mirror / rim / off-axis camera, no rim
highlight (R15-R16), no light cards.
"""
import math
import random

import bpy
from mathutils import Vector

import kit_r2 as K

F = 0.42                  # focal length: the plasma (origin) sits at the focus
VX = -0.25                # dish vertex: the plasma (origin) sits on the axis inside the focal length
R = 0.68                  # clear aperture
HOLE = 0.075              # through-hole radius
CHAMF = 0.035             # chamfer width at the lip
SHELL = 0.085             # substrate thickness
A0, A1 = -70.0, 200.0     # kept arc (a: y = r cos a, z = r sin a); the lower-left quadrant (a 200..290) is cut away
VES_R = 1.38              # vessel radius (axis = X)
ROT_X = (0, math.radians(90), 0)   # local Z -> world X (local (cos b, sin b) -> world (y, z) = (sin b, -cos b))


def fx(r):
    return VX + r * r / (4 * F)


def face_normal(y, z):
    return Vector((1, -y / (2 * F), -z / (2 * F))).normalized()


def _arc(n):
    return [math.radians(A0 + (A1 - A0) * j / (n - 1)) for j in range(n)]


def _surface(mb, rows, angs, flip=False):
    """rows: list of (r, x) -> a ruled surface over the kept arc."""
    V = mb.bm.verts.new
    grid = [[V((x, r * math.cos(a), r * math.sin(a))) for a in angs] for r, x in rows]
    for i in range(len(grid) - 1):
        for j in range(len(angs) - 1):
            q = (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
            mb.bm.faces.new(q[::-1] if flip else q).smooth = True
    return grid


def _section(mb, a, pts_face, pts_back):
    """Flat section cap in the plane of angle a between the face profile and the back profile."""
    V = mb.bm.verts.new
    ca, sa = math.cos(a), math.sin(a)
    prev = None
    for (rf, xf), (rb, xb) in zip(pts_face, pts_back):
        pair = (V((xf, rf * ca, rf * sa)), V((xb, rb * ca, rb * sa)))
        if prev is not None:
            mb.bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
        prev = pair


def mats(M):
    M.setdefault("b19_face", K.mat("CollFaceBrightR19", (0.9, 0.91, 0.93), metal=1.0, rough=0.04))
    M.setdefault("b19_lip", K.mat("CollLipR19", (0.62, 0.63, 0.66), metal=1.0, rough=0.28))
    M.setdefault("b19_bore", K.mat("CollBoreR19", (0.015, 0.015, 0.018), metal=0.3, rough=0.7))
    M.setdefault("b19_sub", K.mat("CollSubR19", (0.62, 0.63, 0.66), metal=0.25, rough=0.55, speck=0.06))
    M.setdefault("b19_flange", K.mat("CollFlangeR19", (0.2, 0.21, 0.24), metal=1.0, rough=0.35))
    M.setdefault("b19_wall", K.mat("VesselWallR19", (0.24, 0.25, 0.28), metal=1.0, rough=0.32, brushed=0.1))
    M.setdefault("b19_window", K.emit_mat("ViewportLightR19", (0.78, 0.84, 1.0), 6.0))
    M.setdefault("b19_axis", K.emit_mat("OpticalAxisR19", (0.08, 0.78, 1.0), 2.2))
    M.setdefault("b19_deb", K.mat("DebrisTinR19", (0.86, 0.87, 0.9), metal=1.0, rough=0.22))
    return M


def collector(M):
    """Cut-open collector with a true through-hole. Returns the objects."""
    mats(M)
    angs = _arc(73)
    nr = 18
    face = K.MB()
    rows = [(HOLE + CHAMF + (R - HOLE - CHAMF) * i / nr, 0.0) for i in range(nr + 1)]
    rows = [(r, fx(r)) for r, _ in rows]
    _surface(face, rows, angs)
    lip = K.MB()                         # chamfer: from the face edge down into the bore
    x_lip = fx(HOLE + CHAMF)
    _surface(lip, [(HOLE + CHAMF, x_lip), (HOLE, x_lip - CHAMF * 0.9)], angs)
    bore = K.MB()                        # dark bore through the substrate + open entry tube behind it
    xb0 = x_lip - CHAMF * 0.9
    xback = fx(HOLE) - SHELL
    _surface(bore, [(HOLE, xb0), (HOLE, xback), (HOLE, xback - 0.7)], angs, flip=True)
    sub = K.MB()
    back_rows = [(r, fx(r) - SHELL) for r, _ in rows]
    _surface(sub, [(HOLE, xback)] + back_rows, angs, flip=True)
    _surface(sub, [(R, fx(R)), (R, fx(R) - SHELL)], angs, flip=True)        # outer rim band
    for a in (math.radians(A0), math.radians(A1)):                         # the two section planes
        prof_f = [(HOLE, xb0), (HOLE + CHAMF, x_lip)] + rows
        prof_b = [(HOLE, xback), (HOLE + CHAMF, xback)] + back_rows
        _section(sub, a, prof_f, prof_b)
    # entry tube wall (outer skin) behind the dish
    tube = K.MB()
    tube.shell((xback - 0.35, 0, 0), HOLE, HOLE + 0.018, 0.7, 0, 270, rot=ROT_X, seg=64)
    fl = K.MB()                           # bolted flange ring at the rim + cooling ring on the back
    rimx = fx(R)
    fl.shell((rimx - 0.02, 0, 0), R - 0.005, R + 0.085, 0.06, 0, 270, rot=ROT_X, seg=96)
    fl.shell((fx(0.35) - SHELL - 0.03, 0, 0), 0.33, 0.37, 0.04, 0, 270, rot=ROT_X, seg=64)
    bolt = K.MB()
    for k in range(19):
        a = math.radians(A0 + 6 + (A1 - A0 - 12) * k / 18)
        p = (rimx + 0.012, (R + 0.045) * math.cos(a), (R + 0.045) * math.sin(a))
        bolt.cyl(p, 0.011, 0.022, rot=ROT_X, seg=6)
    return [face.obj("CollFaceR19", M["b19_face"]), lip.obj("CollLipR19", M["b19_lip"]),
            bore.obj("CollBoreR19", M["b19_bore"]), sub.obj("CollSubR19", M["b19_sub"]),
            tube.obj("CollTubeR19", M["b19_flange"], bevel=0.002), fl.obj("CollFlangeR19", M["b19_flange"], bevel=0.003),
            bolt.obj("CollBoltsR19", M["steel"])]


def h2_nozzles(M, P, H):
    """H2 gas nozzles on the collector rim, aimed across the mirror face."""
    rimx = fx(R)
    for k, deg in enumerate((-60, -10, 40, 90, 140)):
        a = math.radians(deg)
        u = Vector((0, math.cos(a), math.sin(a)))
        base = Vector((rimx + 0.03, 0, 0)) + u * (R + 0.03)
        tip = base + (Vector((0, 0, 0)) - base).normalized() * 0.09     # short nozzle aimed at the plasma
        P["alu_dark"].tube(base, tip, 0.016, seg=16, r2=0.009)
        H._ring(P["alu"], base, (tip - base).normalized(), 0.028, 0.014, 0.02, seg=20)
        P["alu_dark"].tube(base, base + u * 0.07 + Vector((-0.04, 0, 0)), 0.008, seg=10)  # feed line


def chamber(M):
    """Cut-away vacuum vessel around the dish (axis X): wall over the kept arc, back end plate, CF flanges,
    two viewports with a dim lit window behind the glass."""
    import hero_kit_r10 as H
    mats(M)
    w = K.MB()
    # world (y, z) = (sin b, -cos b): b 0 = floor, 90 = +y side, 180 = top; the camera sits near b ~ 250
    w.shell((0.05, 0, 0), VES_R, VES_R + 0.07, 2.3, -25, 185, rot=ROT_X, seg=160)
    w.cyl((-1.12, 0, 0), VES_R + 0.07, 0.07, rot=ROT_X, seg=128)                   # back end plate
    for x in (-0.55, 0.65):                                                          # stiffening rings
        w.shell((x, 0, 0), VES_R - 0.05, VES_R, 0.05, -25, 185, rot=ROT_X, seg=160)
    # front end plate (the camera's sector cut away like the wall): the concave face mirrors what lies along +X,
    # so this plate with its ports / lit viewports is what the dish shows
    w.shell((1.17, 0, 0), 0.0, VES_R + 0.07, 0.07, -25, 185, rot=ROT_X, seg=160)
    P = H.new_parts()
    wins = K.MB()
    for y, z, r, window in ((0.55, -0.35, 0.13, True), (0.15, -0.8, 0.09, False), (0.85, 0.3, 0.1, True),
                            (0.3, 0.75, 0.08, False), (-0.35, -0.95, 0.08, True), (0.95, -0.7, 0.07, False),
                            (-0.1, 1.05, 0.09, True)):
        p = Vector((1.13, y, z))
        nn = Vector((-1, 0, 0))
        H.flange_viewport(P, p, nn, r, nipple=r * 0.9, side_port=not window)
        if window:
            H._cyl(wins, p + nn * r * 1.23, nn, r * 0.6, r * 0.03, seg=40)
    ports = ((0.35, 35, 0.11, True), (-0.35, 120, 0.09, False), (0.55, 150, 0.08, False), (0.0, 80, 0.07, False),
             (-0.6, 30, 0.07, False), (0.7, 100, 0.12, True), (0.15, 175, 0.08, False))
    for x, bdeg, r, window in ports:
        b = math.radians(bdeg)
        p = Vector((x, VES_R * math.sin(b), -VES_R * math.cos(b)))
        n = (Vector((0, 0, 0)) - p).normalized()
        n = (n + Vector((0, 0, 0))).normalized()
        H.flange_viewport(P, p, n, r, nipple=r * 1.0, side_port=(bdeg % 3 == 0))
        if window:                                                           # dim light outside the glass
            f1 = p + n * r * 1.0
            H._cyl(wins, f1 + n * r * 0.33, n, r * 0.6, r * 0.03, seg=40)
    # back plate: two blank flanges + the droplet-catcher stub
    for y, z, r in ((0.75, 0.75, 0.09), (-0.9, 0.55, 0.07)):
        p = Vector((-1.08, y, z))
        H.flange_viewport(P, p, (1, 0, 0), r, nipple=r * 0.8, side_port=False)
    objs = [w.obj("VesselWallR19", M["b19_wall"], bevel=0.004)]
    wo = wins.obj("ViewportLightsR19", M["b19_window"])
    wo.visible_diffuse = False                # a lit window, not a lamp (the plasma / fills light the room)
    objs.append(wo)
    return objs, P


def debris(M, seed=4):
    """Silver-white tin debris: small metal specks with short tapered trails, flying out of the plasma."""
    rnd = random.Random(seed)
    mats(M)
    mb = K.MB()
    for _ in range(40):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        if v.x < -0.3:
            v.x = -v.x
        p = v * rnd.uniform(0.07, 0.36)
        r0 = rnd.uniform(0.0022, 0.0038)
        mb.sphere(tuple(p), r0, 8)
        mb.tube(p, p - v * rnd.uniform(0.012, 0.03), r0 * 0.8, seg=6, r2=r0 * 0.08)
    ob = mb.obj("DebrisTinR19", M["b19_deb"])
    ob.visible_shadow = False
    ob.visible_glossy = False
    return [ob]


def optical_axis(M):
    """Very thin metrology-cyan line from the hole centre to the plasma (the focus)."""
    mats(M)
    mb = K.MB()
    x0, x1, dash, gap = fx(HOLE), 0.42, 0.022, 0.012        # dashed: hole -> plasma -> on toward the IF
    x = x0
    while x < x1:
        if -0.06 < x < 0.08:              # leave the plasma core clear
            x += dash + gap
            continue
        mb.tube((x, 0, 0), (min(x + dash, x1), 0, 0), 0.0013, seg=8)
        x += dash + gap
    ob = mb.obj("OpticalAxisR19", M["b19_axis"])
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
                 "visible_shadow"):
        setattr(ob, attr, False)
    return ob


# ---------------------------------------------------------------- B1_15 scene
CAM_DIR = Vector((0.88, -0.44, 0.19)).normalized()   # ~28 deg off the mirror axis, from the open (cut) sector
CAM_DIST = float(__import__("os").environ.get("B115_DIST", "2.75"))
LOOK = Vector((-0.12, 0.02, 0.0))
PUSH = 0.78


def build_contrast(sc, M, cam, tgt, n, S):
    """S = the r2_source module. Returns a post-hook that adds the B1_15 lights after the module's shared relight."""
    import hero_kit_r10 as H
    import common as C
    C.set_world(top=(0.03, 0.034, 0.05), horizon=(0.018, 0.02, 0.032), bottom=(0.008, 0.009, 0.014))
    S._metals_r15(M, coll_rough=0.035)
    collector(M)
    objs, P = chamber(M)
    for ob in objs:                       # lit windows: not mirrored (the face shows the plasma, not lamps)
        if ob.name.startswith("ViewportLights"):
            ob.visible_glossy = False
    h2_nozzles(M, P, H)
    H.droplet_generator(P, (0, 0, 0.42), (0, 0, -1), s=1.0, flange_at=0.3)
    H.finish(P, M, "B115KitR19")
    cat = K.MB()
    cat.tube((0, 0, -1.36), (0, 0, -0.55), 0.06, seg=32)
    cat.tube((0, 0, -0.55), (0, 0, -0.47), 0.06, seg=32, r2=0.11)
    cat.obj("B115CatcherR19", M["steel"], bevel=0.002)
    # plasma on the axis, inside the focal length: the polished dish shows its magnified violet image
    pl, li = S.plasma_r10(M, (0, 0, 0), 0.045, energy=0.0, gas=1.6, li_color=(0.74, 0.6, 1.0), mirror_core=True)
    for i, ob in enumerate(pl):
        ob.visible_glossy = i >= 1        # the violet glow + cloud (not the white kernel) is what the mirror shows
    S.key_energy(li, [(1, 260), (n, 300)])
    lz = S.main_pulse_cone_r15((fx(HOLE) - SHELL - 0.6, 0, 0), (-0.006, 0, 0), HOLE * 0.8, 0.008, "DriveLaserR19")
    for nd in lz.active_material.node_tree.nodes:
        if nd.type == "MAP_RANGE" and abs(nd.inputs["To Min"].default_value - 3.2) < 1e-6:
            nd.inputs["To Min"].default_value = 6.0
    optical_axis(M)
    for ob in debris(M):
        S.key_scale(ob, [(1, 0.6), (n, 1.15)], interp="LINEAR")
    rr, aa = 0.5, math.radians(100)        # label leader lands on the clean face just above-left of the hole
    face_pt = Vector((fx(rr), rr * math.cos(aa), rr * math.sin(aa)))
    K.anchors("B1_15", {"coll": face_pt, "plasma": Vector((0, 0, 0)), "hole": Vector((fx(HOLE), 0, 0))})
    cam.data.lens = 32
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4.0
    foc = bpy.data.objects.new("FocusR19", None)
    sc.collection.objects.link(foc)
    cam.data.dof.focus_object = foc
    S.key_loc(foc, [(1, (0.0, 0.0, 0.0)), (n, tuple(face_pt))], interp="BEZIER")
    c0 = LOOK + CAM_DIR * CAM_DIST
    c1 = LOOK + (c0 - LOOK) * PUSH
    K.key_path(cam, tgt, [(1, tuple(c0), tuple(LOOK)), (n, tuple(c1), tuple(LOOK + Vector((0.02, 0.0, -0.01))))],
               interp="BEZIER")

    def post(sc_):
        # shapeless soft fills (spherical point lights) for the vessel metal - R16 deleting fill = black chamber;
        # none of them is seen by glossy rays: the mirror shows the plasma image + plasma-lit parts only
        for nm, lo, en, co in (("Key", (1.9, -1.5, 1.1), 420.0, (0.95, 0.96, 1.0)),
                               ("Top", (0.7, -0.6, 1.25), 160.0, (0.9, 0.93, 1.0)),
                               ("Side", (1.5, -0.4, -0.9), 140.0, (0.8, 0.85, 1.0)),
                               ("Wall", (0.6, 0.6, 0.9), 90.0, (0.7, 0.76, 1.0)),
                               ("Low", (0.4, 0.5, -0.9), 60.0, (0.65, 0.72, 1.0)),
                               ("Front", (0.85, 1.05, -0.85), 45.0, (0.85, 0.88, 1.0))):
            K.point("B115Fill%sR19" % nm, lo, en, co, 0.4)
        # the fills light everything EXCEPT the mirror face (Cycles light linking): the face is never lit by a lamp
        # and never mirrors one - its brightness is the plasma's reflection (+ plasma-lit parts) only
        recv = bpy.data.collections.new("B115FillRecvR19")
        for ob in bpy.data.objects:
            if ob.type == "MESH" and ob.name != "CollFaceR19":
                recv.objects.link(ob)
        for ob in bpy.data.objects:
            if ob.type == "LIGHT" and ob.name != "PlasmaLight":
                ob.light_linking.receiver_collection = recv
    return post
