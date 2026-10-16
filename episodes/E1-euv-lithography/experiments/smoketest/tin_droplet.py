import bpy, math, os
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end=48; sc.render.fps=24
def mat(n,c,e=0,metal=0.85):
    m=bpy.data.materials.new(n); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=c
    b.inputs["Metallic"].default_value=metal
    b.inputs["Roughness"].default_value=0.25
    if e:
        try:
            b.inputs["Emission Color"].default_value=c
            b.inputs["Emission Strength"].default_value=e
        except KeyError:
            b.inputs["Emission"].default_value=(*c[:3],1)
            b.inputs["Emission Strength"].default_value=e
    return m
# tin droplet falls then flattens then vanishes into plasma
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18,location=(0,0,2.2),segments=32,ring_count=16)
d=bpy.context.object; d.name="TinDroplet"
d.data.materials.append(mat("tin",(0.72,0.72,0.74,1)))
d.location=(0,0,2.2); d.keyframe_insert("location",frame=1)
d.location=(0,0,0); d.keyframe_insert("location",frame=20)
d.scale=(1,1,1); d.keyframe_insert("scale",frame=20)
d.scale=(2.2,2.2,0.28); d.keyframe_insert("scale",frame=28)  # pre-pulse pancake
d.hide_render=False; d.keyframe_insert("hide_render",frame=28)
d.hide_render=True; d.keyframe_insert("hide_render",frame=30)
# laser beam (cylinder along X)
bpy.ops.mesh.primitive_cylinder_add(radius=0.025,depth=5.5,location=(-2.7,0,0),rotation=(0,math.pi/2,0))
L=bpy.context.object; L.name="LaserPulse"
L.data.materials.append(mat("laser",(1.0,0.2,0.05,1),e=25,metal=0))
for f,h in [(1,True),(19,True),(20,False),(22,True),(27,True),(28,False),(30,True)]:
    L.hide_render=h; L.keyframe_insert("hide_render",frame=f)
# plasma sphere expands after main pulse
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=0.55,location=(0,0,0))
P=bpy.context.object; P.name="Plasma"
P.data.materials.append(mat("plasma",(0.6,0.45,1.0,1),e=40,metal=0))
for f,s,h in [(1,0.01,True),(29,0.01,True),(30,0.4,False),(36,1.0,False),(48,1.4,False)]:
    P.scale=(s,s,s); P.keyframe_insert("scale",frame=f)
    P.hide_render=h; P.keyframe_insert("hide_render",frame=f)
# simple collector mirror: half-shell facing +X
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.8,location=(0,0,0),segments=48,ring_count=24)
C=bpy.context.object; C.name="CollectorMirror"
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0.3,0,0),plane_no=(1,0,0),clear_inner=False,clear_outer=True)
bpy.ops.mesh.bisect(plane_co=(0,0,-0.4),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
bpy.ops.object.mode_set(mode='OBJECT')
C.data.materials.append(mat("grey",(0.45,0.45,0.48,1),metal=0.6))
# camera + light
bpy.ops.object.empty_add(location=(0,0,0.2)); aim=bpy.context.object
bpy.ops.object.camera_add(location=(3.8,-5.2,2.0)); cam=bpy.context.object; sc.camera=cam
t=cam.constraints.new('TRACK_TO'); t.target=aim; t.track_axis='TRACK_NEGATIVE_Z'; t.up_axis='UP_Y'
bpy.ops.object.light_add(type='AREA',location=(3,-3,5)); lt=bpy.context.object; lt.data.energy=400; lt.data.size=4
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.008,0.008,0.012,1)
w.node_tree.nodes["Background"].inputs[1].default_value=0.3
# Cycles CPU (no GPU / no EGL)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=16
sc.cycles.use_denoising=False; sc.render.resolution_x=640; sc.render.resolution_y=360
sc.render.film_transparent=False
out="/workspace/dreamforge-plan/smoketest/"
bpy.ops.wm.save_as_mainfile(filepath=out+"tin_droplet.blend")
sc.frame_set(34); sc.render.image_settings.file_format='PNG'; sc.render.filepath=out+"still_f34.png"
bpy.ops.render.render(write_still=True); print("STILL OK")
sc.render.image_settings.file_format='FFMPEG'
sc.render.ffmpeg.format='MPEG4'; sc.render.ffmpeg.codec='H264'
sc.render.ffmpeg.constant_rate_factor='MEDIUM'
sc.render.filepath=out+"clip_"
bpy.ops.render.render(animation=True); print("SMOKE DONE")
