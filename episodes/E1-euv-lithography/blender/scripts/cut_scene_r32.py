"""Round 32 scene hook (MAIN process; r2_cutaway.R32_SCENE), layered after the R31 hooks and before beam_hook_r29.

  B302_R32 (row 3, B3_02 - scene-level REBUILD, lowest R31 84.65): R31 p2 「收集镜看不出是『一面椭球镜』。它就是左半边那只
           铬桶的内壁，没有镜面边缘的高光，也没有镜座…镜面要占画面 1/3 以上，正面朝向等离子体」「改成以镜缘为底、尖端落在 IF 的
           3D 圆锥…那块矩形紫光删掉」「机位改到能看出孔在镜面顶点、和 IF 同一条轴上的位置」; Carl t381: no visible R30 -> R31
           difference. R31 grid (sketch31/b302_grid.txt): the dish reflects exactly the polished drum wall around it, so
           darkening the wall darkens the dish (R30 / R31 returns). R32 changes the STRUCTURE, not a shade:
    * the polished drum (R2_vessel body + its flanges, x < DRUM_X) around the dish is cut away - the neck to the IF
      stays; the dish stands alone on a visible mount in a dark chamber, so it no longer reflects / merges with a drum;
    * a thick machined rim ring + pedestal column + base + two back struts (the mount);
    * the dish face = the collector material reviewers accepted on B2_08 / B1_15 (cut_mirror_r19.hi_mirror) + one
      lit wall in its camera-reflection direction (cut_mirror_r19.reflect_env, the B2_08 / B1_15 call);
    * new camera: 3/4 view from the IF side, whole dish incl. rim + mount in frame and >= 1/3 of the frame, centre
      hole at the apex on the axis with the plasma and the IF (right third); slow push-in + small orbit;
    * the rim cone (whole rim -> IF tip) is rebuilt as one volume minus the camera frustums through the dish face
      (src_r32.cut_by_faces, the B1_15 method): it leaves the rim, converges on the IF, never lies over the mirror.
Remove B3_02 from R32_SCENE / B302_R32 False -> R31 pixels.
"""
import math

import bpy
from mathutils import Vector

B302_R32 = True
TONE = 0.72              # same hi_mirror recipe, darker tone: at 0.9 the dish mirrors a mid-grey chamber (32 spp 90/10 3.83 < 4)
ENV = False             # lit wall in the dish's reflection (B2_08 recipe): 32 spp v1 with it = dish 90/10 2.58 (< 4, grey on grey)
DISH_C = Vector((-7.90, 0.0, 2.28))
AX = Vector((3.70, 0.0, 0.25)).normalized()   # collector axis = COLL -> IF (a010_r26 / build_cutaway_r2)
RIM_R = 1.30
DRUM_X = -4.70           # the whole polished vessel incl. its end wall + neck (8 spp v1: the end wall at x -5.9 lit violet
                         # behind the cone = the R31 「矩形紫光」, the half neck = a flat violet blade); the IF bellows stay
LENS = 27.0
# camera keys: (frame fraction, azimuth deg from the axis toward -y, elevation deg, distance m, target fraction dish->IF)
KEYS = ((0.0, 44.0, -5.0, 6.0, 0.30), (1.0, 36.0, -8.0, 5.0, 0.27))   # camera a little below the axis: the IF (nearer the
# camera) sits higher on screen than the plasma, so the 第一焦点 and IF tags do not collide (8 spp v2)
IF_P = Vector((-4.55, 0.0, 2.55))
MOUTH_C = Vector((-7.51, 0.0, 2.28))   # dish mouth plane centre (CollectorDishR24 x -8.25 .. -7.51, radius 1.25)
MOUTH_R = 1.25


def pre(variant, shot, mod):
    return None


def _bake(ob):
    if ob.modifiers:
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = bpy.data.meshes.new_from_object(ev)
        ob.modifiers.clear()
        ob.data = me
    elif ob.data.users > 1:
        ob.data = ob.data.copy()


def _cut_drum():
    import bmesh
    n = {}
    for name in ("R2_vessel", "R2_flange", "R2_bolt"):
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            continue
        _bake(ob)
        mw = ob.matrix_world
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        dead = []
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            if c.x < DRUM_X and c.x > -9.2 and math.hypot(c.y, c.z - DISH_C.z) > 0.25 * (name != "R2_vessel"):
                dead.append(f)
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bm.to_mesh(ob.data)
            ob.data.update()
        n[name] = len(dead)
        bm.free()
    for nm in ("NeckSectionR28",):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.hide_render = True
    fr = bpy.data.objects.get("R2_frame")       # front-left corner post of the machine frame (camera foreground)
    if fr is not None and fr.type == "MESH":
        _bake(fr)
        mw = fr.matrix_world
        bm = bmesh.new()
        bm.from_mesh(fr.data)
        dead = [f for f in bm.faces if (lambda c: c.x < -8.9 and c.y < -1.0)(mw @ f.calc_center_median())]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(fr.data)
        fr.data.update()
        bm.free()
        n["R2_frame"] = len(dead)
    return n


def _mount():
    import kit_r2 as K
    rim, mt = K.MB(), K.MB()
    q = Vector((0, 0, 1)).rotation_difference(AX)
    rim_c = DISH_C + AX * 0.36
    rim.ring(rim_c, RIM_R + 0.10, RIM_R - 0.02, 0.16, rot=q.to_euler(), seg=96)
    rim.ring(rim_c - AX * 0.14, RIM_R + 0.06, RIM_R - 0.06, 0.06, rot=q.to_euler(), seg=96)
    bottom = DISH_C + Vector((-0.15, 0, -RIM_R - 0.05))
    mt.tube(bottom + Vector((0, 0, 0.1)), Vector((bottom.x, 0, 0.36)), 0.11)
    mt.box((bottom.x, 0, 0.30), (0.9, 0.9, 0.12))
    mt.box((bottom.x + 0.05, 0, bottom.z + 0.05), (0.32, 0.5, 0.22))
    for s_ in (-1, 1):
        a = DISH_C + Vector((-0.30, s_ * 0.85, -0.6))
        mt.tube(a, Vector((bottom.x - 0.25, s_ * 0.35, 0.36)), 0.05)
    obs = [rim.obj("B302RimR32", K.mat("B302RimR32M", (0.70, 0.71, 0.74), metal=1.0, rough=0.18), bevel=0.01),
           mt.obj("B302MountR32", K.mat("B302MountR32M", (0.28, 0.29, 0.32), metal=0.9, rough=0.35), bevel=0.01)]
    return obs


def _mirror(sc):
    import cut_mirror_r19 as CM
    dish = bpy.data.objects.get("CollectorDishR24")
    if dish is None:
        return 0
    hi = CM.hi_mirror(rough=0.05, tone=TONE)
    for s in dish.material_slots:
        s.material = hi
    if not ENV:
        return 0
    heroes = []
    for ang in (60.0, 200.0, 320.0):
        a = math.radians(ang)
        p = DISH_C + Vector((0.08, 0.75 * math.cos(a), 0.75 * math.sin(a)))
        nrm = (DISH_C + AX * 2.0 - p).normalized()
        heroes.append((p, nrm, 1.4))
    import r2_source                    # same material dict the B2_08 / B1_15 reflect_env walls are built with
    obs = CM.reflect_env(sc, r2_source._mats(), heroes, tag="B302EnvR32", dist=2.2, light=35.0, seed=3021, frames=[30, 67, 103])
    return len(obs)


def _camera(sc):
    import kit_r2 as K
    cam = sc.camera
    tgt = next((c.target for c in cam.constraints if c.type == "TRACK_TO"), None)
    for o in (cam, tgt):
        if o is not None and o.animation_data:
            o.animation_data_clear()
    for c in list(cam.constraints):
        if c.type != "TRACK_TO":
            cam.constraints.remove(c)
    if cam.parent is not None:
        mw = cam.matrix_world.copy()
        cam.parent = None
        cam.matrix_world = mw
    cam.data.lens = LENS
    if cam.data.animation_data:
        cam.data.animation_data_clear()
    f0, f1 = sc.frame_start, sc.frame_end
    keys = []
    for fr, az, el, dist, tf in KEYS:
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.cos(a) * math.cos(e), -math.sin(a) * math.cos(e), math.sin(e)))
        T = DISH_C.lerp(IF_P, tf)
        keys.append((round(f0 + (f1 - f0) * fr), DISH_C + d * dist, T))
    if tgt is None:
        return keys
    K.key_path(cam, tgt, keys)
    return keys


def _cone(sc):
    """rim cone (whole dish mouth -> IF tip) rebuilt as one beam_r29 volume minus the camera frustums through the dish
    face (src_r32.cut_by_faces, the B1_15 method): the cone leaves the rim but no violet haze lies over the mirror, so
    the R29 dimming for the haze (beam_hook_r29.STRENGTH 0.55) is no longer needed -> default strength."""
    import beam_r29 as B29
    import src_r32
    legs = [o for o in bpy.data.objects if o.name.startswith("CollectBeamR27Leg") and "r25_radii" in o.keys()]
    if not legs:
        return None
    first = min(legs, key=lambda o: o.name)
    last = max(legs, key=lambda o: o.name)
    a = first.matrix_world @ B29._rings(first)[0][0]
    tip = last.matrix_world @ B29._rings(last)[1][0]
    for o in legs:
        o.hide_render = True
        o.hide_viewport = True
        o["r29_replaced"] = "cut_scene_r32"
    orig = getattr(B29.cone, "_r30_orig", B29.cone)
    ob = orig("B302ConeR32", a, tip, MOUTH_R, 0.03, None, B29.B_DEFAULT)
    src_r32.cut_by_faces(sc, ob, (30, 67, 103), MOUTH_C, AX, MOUTH_R * 1.06, "B302Face")
    return ob


def post(sc, variant, shot):
    if not (B302_R32 and shot == "B3_02"):
        return sc
    n_cut = _cut_drum()
    obs = _mount()
    keys = _camera(sc)
    n_env = _mirror(sc)
    cone = _cone(sc)
    print(f"[cut_scene_r32] B3_02 drum cut {n_cut}; rim + mount {len(obs)}; camera keys "
          f"{[(k[0], tuple(round(x, 2) for x in k[1])) for k in keys]}; dish hi mirror + {n_env} env objs; cone {cone.name if cone else None}", flush=True)
    sc.frame_set(1)
    return sc
