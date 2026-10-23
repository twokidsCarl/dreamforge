import bpy,mathutils,math,sys,random,json
import numpy as np
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]
MODE=argv[0]; OUT=argv[1]; DENS=float(argv[2]) if len(argv)>2 else 600000; SAMPLES=int(argv[3]) if len(argv)>3 else 40
RES=(int(argv[4]),int(argv[5])) if len(argv)>5 else (960,540)
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
sc.render.fps=24
bpy.ops.import_scene.gltf(filepath='/workspace/e2work/v8/tripo/mouse_qwalk.glb')
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o,do_unlink=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE'); m=next(o for o in bpy.data.objects if o.type=='MESH')
walk=bpy.data.actions[0]; walk.use_fake_user=True
WAKE=int(argv[6]) if len(argv)>6 else 58
arm.animation_data_create(); arm.animation_data.action=None
tr=arm.animation_data.nla_tracks.new(); s1=tr.strips.new('hold',1,walk); s1.action_frame_start=1; s1.action_frame_end=1.5; s1.scale=(WAKE+10)/0.5*1.0/1.0 if False else 1; s1.frame_end=WAKE+10
tr2=arm.animation_data.nla_tracks.new(); s2=tr2.strips.new('walk',WAKE,walk); s2.repeat=3; s2.blend_in=10
# breathing before wake (driver on a mid spine bone scale)
pbS=arm.pose.bones['tripo::Spine_2']
for i in (0,2):
    d=pbS.driver_add('scale',i).driver; d.type='SCRIPTED'; d.expression=f'1+0.035*sin(frame*0.33)*(frame<{WAKE})'
# rest-pose geometry & ground
sc.frame_set(1); bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); me=m.evaluated_get(dg).to_mesh()
co=np.array([m.matrix_world@v.co for v in me.vertices]); m.evaluated_get(dg).to_mesh_clear()
arm.location.z-=co[:,2].min(); co[:,2]-=co[:,2].min()
# orientation from rig: hip -> head
pbH=arm.pose.bones['tripo::Head_1']; pbP=arm.pose.bones['tripo::Root']
headw=arm.matrix_world@pbH.head; hipw=arm.matrix_world@pbP.head
fwd=Vector((headw.x-hipw.x,headw.y-hipw.y,0)).normalized(); print('FWD',fwd)
proj=co[:,:2]@np.array([fwd.x,fwd.y]); ynose_idx=proj.argmax(); nosept=Vector(co[ynose_idx])
sgn=1; ynose=0.0
hd=np.array(headw)
near_h=co[(np.hypot(co[:,0]-hd[0],co[:,1]-hd[1])<0.035)]
imp=Vector(near_h[near_h[:,2].argmax()]); print('IMP',imp,'NOSE',nosept)
hb=min([b for b in arm.data.bones if 'Head' in b.name],key=lambda b:((arm.matrix_world@b.head_local)-imp).length); print('HEADBONE',hb.name)
def parent_bone(o):
    o.parent=arm; o.parent_type='BONE'; o.parent_bone=hb.name
    pb=arm.pose.bones[hb.name]; o.matrix_parent_inverse=(arm.matrix_world@pb.matrix@mathutils.Matrix.Translation((0,hb.length,0))).inverted()
# --- fur weights + whisker removal from texture ---
mat=m.data.materials[0]; bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
n=bsdf.inputs['Base Color'].links[0].from_node
while n.type!='TEX_IMAGE': n=n.inputs[0].links[0].from_node
tex=n.image; W,H=tex.size; px=np.array(tex.pixels[:]).reshape(H,W,4)
li=np.array([l.vertex_index for l in m.data.loops]); uvs=np.array([d.uv[:] for d in m.data.uv_layers.active.data])
xs=np.clip((uvs[:,0]%1)*W,0,W-1).astype(int); ys=np.clip((uvs[:,1]%1)*H,0,H-1).astype(int)
c=px[ys,xs,:3]; lum=c.mean(1); pink=c[:,0]-c[:,2]; nv=len(m.data.vertices)
w=np.zeros(nv); cnt=np.zeros(nv); np.add.at(w,li,((lum<0.22)&(pink<0.12)).astype(float)); np.add.at(cnt,li,1); w/=np.maximum(cnt,1)
vg=m.vertex_groups.new(name='fur')
for i in np.nonzero(w>0.5)[0]: vg.add([int(i)],1.0,'REPLACE')
rest=np.array([v.co for v in m.data.vertices])  # mesh-local rest coords
wh=np.zeros(nv); np.add.at(wh,li,((lum>0.33)&(np.abs(pink)<0.18)).astype(float)); wh/=np.maximum(cnt,1)
# whisker verts: bright & near nose (in world rest coords)
near=np.linalg.norm(co-np.array(nosept),axis=1)<0.12
import bmesh
bm=bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table()
dv=[bm.verts[i] for i in np.nonzero((wh>0.45)&near)[0]]; print('whisker verts',len(dv)); bmesh.ops.delete(bm,geom=dv,context='VERTS'); bm.to_mesh(m.data); bm.free()
bsdf.inputs['Roughness'].default_value=0.55
src=bsdf.inputs['Base Color'].links[0].from_socket
mx=mat.node_tree.nodes.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.blend_type='MULTIPLY'
at=mat.node_tree.nodes.new('ShaderNodeAttribute'); at.attribute_name='fur'
mat.node_tree.links.new(at.outputs['Fac'],mx.inputs['Factor']); mat.node_tree.links.new(src,mx.inputs[6]); mx.inputs[7].default_value=(0.18,0.16,0.15,1)
mat.node_tree.links.new(mx.outputs[2],bsdf.inputs['Base Color'])
bsdf.inputs['Subsurface Weight'].default_value=0.2; bsdf.inputs['Subsurface Radius'].default_value=(1.0,0.35,0.25); bsdf.inputs['Subsurface Scale'].default_value=0.012
# --- GN fur (after armature) ---
FURLEN=0.02
ng=bpy.data.node_groups.new('Fur','GeometryNodeTree')
ng.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry'); ng.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
N=ng.nodes; K=ng.links; gi=N.new('NodeGroupInput'); go=N.new('NodeGroupOutput')
dist=N.new('GeometryNodeDistributePointsOnFaces'); dist.inputs['Density'].default_value=DENS
na=N.new('GeometryNodeInputNamedAttribute'); na.data_type='FLOAT'; na.inputs['Name'].default_value='fur'
K.new(gi.outputs[0],dist.inputs['Mesh']); K.new(na.outputs['Attribute'],[i for i in dist.inputs if i.name=='Density Factor'][0])
# tailward direction in object space follows body: use rest-pose position-based tangent ~ local -Y.. approximate with object-space vector
sn=N.new('ShaderNodeVectorMath'); sn.operation='SCALE'; sn.inputs[3].default_value=0.5; K.new(dist.outputs['Normal'],sn.inputs[0])
add=N.new('ShaderNodeVectorMath'); add.operation='ADD'; add.inputs[1].default_value=(-fwd.x,-fwd.y,-0.35); K.new(sn.outputs[0],add.inputs[0])
nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=60
ns=N.new('ShaderNodeVectorMath'); ns.operation='SUBTRACT'; ns.inputs[1].default_value=(0.5,0.5,0.5); K.new(nz.outputs['Color'],ns.inputs[0])
ns2=N.new('ShaderNodeVectorMath'); ns2.operation='SCALE'; ns2.inputs[3].default_value=1.0; K.new(ns.outputs[0],ns2.inputs[0])
add2=N.new('ShaderNodeVectorMath'); add2.operation='ADD'; K.new(add.outputs[0],add2.inputs[0]); K.new(ns2.outputs[0],add2.inputs[1])
al=N.new('FunctionNodeAlignRotationToVector'); al.axis='Z'; K.new(add2.outputs[0],al.inputs['Vector'])
cl=N.new('GeometryNodeCurvePrimitiveLine'); cl.inputs['End'].default_value=(0,0,1)
rs=N.new('GeometryNodeResampleCurve'); rs.inputs['Count'].default_value=4; K.new(cl.outputs[0],rs.inputs['Curve'])
rnd=N.new('FunctionNodeRandomValue'); rnd.data_type='FLOAT'; rnd.inputs['Min'].default_value=FURLEN*0.55; rnd.inputs['Max'].default_value=FURLEN*1.25
iop=N.new('GeometryNodeInstanceOnPoints'); K.new(dist.outputs['Points'],iop.inputs['Points']); K.new(rs.outputs[0],iop.inputs['Instance']); K.new(al.outputs[0],iop.inputs['Rotation']); K.new(rnd.outputs['Value'],iop.inputs['Scale'])
ri=N.new('GeometryNodeRealizeInstances'); K.new(iop.outputs[0],ri.inputs[0])
rad=N.new('GeometryNodeSetCurveRadius'); rad.inputs['Radius'].default_value=0.0002; K.new(ri.outputs[0],rad.inputs['Curve'])
sm=N.new('GeometryNodeSetMaterial'); K.new(rad.outputs[0],sm.inputs['Geometry'])
j=N.new('GeometryNodeJoinGeometry'); K.new(sm.outputs[0],j.inputs[0]); K.new(gi.outputs[0],j.inputs[0]); K.new(j.outputs[0],go.inputs[0])
hm=bpy.data.materials.new('fur'); hm.use_nodes=True; nt=hm.node_tree
for x in list(nt.nodes):
    if x.type=='BSDF_PRINCIPLED': nt.nodes.remove(x)
hbsdf=nt.nodes.new('ShaderNodeBsdfHairPrincipled')
try: hbsdf.parametrization='MELANIN'
except: pass
hbsdf.inputs['Melanin'].default_value=0.93; hbsdf.inputs['Melanin Redness'].default_value=0.35; hbsdf.inputs['Roughness'].default_value=0.26; hbsdf.inputs['Radial Roughness'].default_value=0.4; hbsdf.inputs['Coat'].default_value=0.35
nt.links.new(hbsdf.outputs[0],next(x for x in nt.nodes if x.type=='OUTPUT_MATERIAL').inputs[0])
sm.inputs['Material'].default_value=hm
md=m.modifiers.new('fur','NODES'); md.node_group=ng
# --- whiskers: thin tapered curves, bone-parented ---
wm=bpy.data.materials.new('whisker'); wm.use_nodes=True; wb=wm.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value=(0.75,0.72,0.68,1); wb.inputs['Roughness'].default_value=0.3
base=nosept-fwd*0.03+Vector((0,0,0.0)); random.seed(4)
side_v=Vector((-fwd.y,fwd.x,0))
for side in (-1,1):
    for k in range(7):
        cu=bpy.data.curves.new('wh','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.0009; cu.bevel_resolution=1
        sp=cu.splines.new('POLY'); sp.points.add(3)
        ang=math.radians(-25+k*9+random.uniform(-3,3)); L=random.uniform(0.07,0.11)
        d=(side_v*side*math.cos(ang)*0.9 - fwd*0.35 + Vector((0,0,math.sin(ang)*0.6))).normalized()
        p0=base+side_v*side*0.016+Vector((0,0,k*0.002-0.006))
        for i,pt in enumerate(sp.points):
            t=i/3; p=p0+d*L*t+Vector((0,0,-0.012*t*t)); pt.co=(*p,1); pt.radius=1.0-0.9*t
        ob=bpy.data.objects.new('whisker',cu); sc.collection.objects.link(ob); ob.data.materials.append(wm); parent_bone(ob)
# --- implant + slack fiber ---
bpy.ops.mesh.primitive_cylinder_add(radius=0.011,depth=0.05,location=imp+Vector((0,0,0.02))); fer=bpy.context.object
cm=bpy.data.materials.new('ceramic'); cm.use_nodes=True; cb=cm.node_tree.nodes['Principled BSDF']; cb.inputs['Base Color'].default_value=(0.9,0.88,0.82,1); cb.inputs['Roughness'].default_value=0.35
cb.inputs['Emission Color'].default_value=(0.15,0.5,1,1); fer.data.materials.append(cm); parent_bone(fer)
bpy.ops.mesh.primitive_cylinder_add(radius=0.017,depth=0.014,location=imp+Vector((0,0,0.004))); cap=bpy.context.object
dmm=bpy.data.materials.new('cement'); dmm.use_nodes=True; dmm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.72,0.72,0.68,1); cap.data.materials.append(dmm); parent_bone(cap)
anchor=bpy.data.objects.new('fiber_anchor',None); sc.collection.objects.link(anchor); anchor.location=imp+Vector((0,0,0.045)); parent_bone(anchor)
cu=bpy.data.curves.new('fiber','CURVE'); cu.dimensions='3D'; cu.bevel_depth=0.0045; cu.bevel_resolution=4
sp=cu.splines.new('BEZIER'); sp.bezier_points.add(3)
back=-fwd
top=imp+back*0.25+Vector((-0.1,0,1.8))
pts=[imp+Vector((0,0,0.045)), imp+back*0.08+Vector((0.04,0,0.20)), imp+back*0.2+Vector((-0.06,0,0.75)), top]
for b,p in zip(sp.bezier_points,pts): b.co=p; b.handle_left_type=b.handle_right_type='AUTO'
fo=bpy.data.objects.new('fiber',cu); sc.collection.objects.link(fo)
hk=fo.modifiers.new('hook','HOOK'); hk.object=anchor
# hook only the first point: use vertex indices (bezier: 3 per point)
hk.vertex_indices_set([0,1,2])
bpy.context.view_layer.update(); hk.matrix_inverse=anchor.matrix_world.inverted(); hk.center=anchor.matrix_world.translation
km=bpy.data.materials.new('jacket'); km.use_nodes=True; kb=km.node_tree.nodes['Principled BSDF']; kb.inputs['Base Color'].default_value=(0.03,0.06,0.14,1); kb.inputs['Roughness'].default_value=0.35
kb.inputs['Emission Color'].default_value=(0.1,0.45,1,1); fo.data.materials.append(km)
bpy.ops.object.light_add(type='POINT',location=imp+Vector((0,0,0.05))); gl=bpy.context.object; gl.data.color=(0.15,0.5,1); gl.data.shadow_soft_size=0.02; parent_bone(gl)
# --- floor: bedding ---
bpy.ops.mesh.primitive_plane_add(size=8); fl=bpy.context.object
fm=bpy.data.materials.new('floor'); fm.use_nodes=True; Nn=fm.node_tree.nodes; Lk=fm.node_tree.links; fb=Nn['Principled BSDF']
tc_=Nn.new('ShaderNodeTexCoord'); mp=Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(2.2,2.2,2.2); Lk.new(tc_.outputs['UV'],mp.inputs[0])
def T(f,cs):
    t=Nn.new('ShaderNodeTexImage'); t.image=bpy.data.images.load('/workspace/e2work/v8/assets/wood_chips/'+f); t.image.colorspace_settings.name=cs; Lk.new(mp.outputs[0],t.inputs[0]); return t
d=T('Diffuse.jpg','sRGB'); r=T('Rough.jpg','Non-Color'); nn=T('nor_gl.jpg','Non-Color')
hs=Nn.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value=0.62; hs.inputs['Saturation'].default_value=1.0; Lk.new(d.outputs[0],hs.inputs['Color']); Lk.new(hs.outputs[0],fb.inputs['Base Color'])
Lk.new(r.outputs[0],fb.inputs['Roughness']); nm=Nn.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=1.5; Lk.new(nn.outputs[0],nm.inputs['Color']); Lk.new(nm.outputs[0],fb.inputs['Normal']); fl.data.materials.append(fm)
# background lab bokeh + far wall
sidev0=Vector((fwd.y,-fwd.x,0)); C0=Vector((float(np.median(co[:,0])),float(np.median(co[:,1])),0))
bpy.ops.mesh.primitive_plane_add(size=30,location=C0-sidev0*8+Vector((0,0,3))); wall=bpy.context.object
wall.rotation_euler=(math.radians(90),0,math.atan2(sidev0.y,sidev0.x)+math.radians(90))
wmat=bpy.data.materials.new('wall'); wmat.use_nodes=True; wmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.02,0.03,0.07,1); wall.data.materials.append(wmat)
random.seed(3)
for i in range(12):
    loc=C0-sidev0*random.uniform(3.0,4.5)-fwd*random.uniform(-1.0,3.5)+Vector((0,0,random.uniform(0.15,0.9)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035,location=loc)
    b_=bpy.context.object; em=bpy.data.materials.new('bk'); em.use_nodes=True; e=em.node_tree.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value=random.choice([(0.25,0.55,1,1),(1,0.7,0.4,1),(0.4,0.8,1,1),(1,0.85,0.6,1)]); e.inputs[1].default_value=random.uniform(5,12)
    em.node_tree.links.new(e.outputs[0],em.node_tree.nodes['Material Output'].inputs[0]); b_.data.materials.append(em)
# lights
def area(loc,energy,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc); L=bpy.context.object; L.data.energy=energy; L.data.color=color; L.data.size=size
    c=L.constraints.new('TRACK_TO'); c.target=arm; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'; return L
area(Vector((0,0,1.4))+Vector((fwd.y,-fwd.x,0))*1.6+fwd*0.8,240,(1.0,0.86,0.72),1.0)
area(Vector((0,0,0.9))-Vector((fwd.y,-fwd.x,0))*1.3-fwd*0.6,170,(0.55,0.68,1.0),0.6)
area((0.3,0,2.4),12,(0.6,0.65,1.0),2.5)
w_=bpy.data.worlds.new('w'); sc.world=w_; w_.use_nodes=True; w_.node_tree.nodes['Background'].inputs[0].default_value=(0.012,0.016,0.04,1)
# camera: tracks a target that follows the mouse root
cam=bpy.data.cameras.new('cam'); cam.lens=50; cam.dof.use_dof=True; cam.dof.aperture_fstop=2.2
co_=bpy.data.objects.new('cam',cam); sc.collection.objects.link(co_); sc.camera=co_
tgt=bpy.data.objects.new('tgt',None); sc.collection.objects.link(tgt)
ctr=Vector((float(np.median(co[:,0])), float(np.median(co[:,1])), 0.18))+fwd*0.12
WALKSPEED=float(argv[7]) if len(argv)>7 else 0.0075   # BU per frame toward nose (in-place walk -> we translate)
arm.keyframe_insert('location',frame=WAKE)
L0=arm.location.copy(); arm.location=L0+fwd*WALKSPEED*(120-WAKE); arm.keyframe_insert('location',frame=120)
tgt.location=ctr; tgt.keyframe_insert('location',frame=1); tgt.keyframe_insert('location',frame=WAKE); tgt.location=ctr+fwd*WALKSPEED*(120-WAKE)*0.7; tgt.keyframe_insert('location',frame=120)
tc=co_.constraints.new('TRACK_TO'); tc.target=tgt; tc.track_axis='TRACK_NEGATIVE_Z'; tc.up_axis='UP_Y'; cam.dof.focus_object=tgt
sidev=Vector((fwd.y,-fwd.x,0))
c0=ctr+sidev*1.75+fwd*0.95+Vector((0,0,0.42)); c1=ctr+sidev*1.45+fwd*1.45+Vector((0,0,0.36))
co_.location=c0; co_.keyframe_insert('location',frame=1); co_.location=c1; co_.keyframe_insert('location',frame=120)
# light on ramp (f WAKE-18 -> WAKE-6)
LON=WAKE-18
for f,e,g in ((1,0,0),(LON,0,0),(LON+12,1.6,8),(120,1.6,8)):
    kb.inputs['Emission Strength'].default_value=e; kb.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
    cb.inputs['Emission Strength'].default_value=e*0.6; cb.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
    gl.data.energy=g; gl.data.keyframe_insert('energy',frame=f)
# render settings
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.use_denoising=True; sc.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
sc.view_settings.view_transform='AgX'
try: sc.view_settings.look='AgX - Medium High Contrast'
except: pass
sc.render.resolution_x,sc.render.resolution_y=RES; sc.cycles.samples=SAMPLES; sc.frame_start=1; sc.frame_end=120
sc.render.use_motion_blur=True; sc.render.motion_blur_shutter=0.4
if MODE=='count':
    sc.frame_set(90); dg=bpy.context.evaluated_depsgraph_get(); ev=m.evaluated_get(dg)
    g=ev.evaluated_geometry(); print('COUNT', g.curves and len(g.curves.curves), g.mesh and len(g.mesh.vertices))
    for inst in dg.object_instances:
        if inst.object.original==m or inst.object.name.startswith('tripo'): print('INST',inst.object.type,inst.object.name, getattr(inst.object.data,'curves',None) and len(inst.object.data.curves))
    print('VG',[g.name for g in m.vertex_groups], 'attr', [a.name for a in m.data.attributes][:20])
elif MODE=='proj':
    from bpy_extras.object_utils import world_to_camera_view
    res={}
    for f in range(1,121):
        sc.frame_set(f); p=fer.matrix_world@Vector((0,0,0.025)); v=world_to_camera_view(sc,co_,p); res[f]=[v.x,1-v.y]
    json.dump(res,open(OUT,'w')); print('PROJ done',res[1],res[120])
elif MODE=='frames':
    for f in [int(x) for x in argv[8].split(',')]:
        sc.frame_set(f); sc.render.filepath=OUT+'%04d.png'%f; bpy.ops.render.render(write_still=True)
else:
    sc.render.use_overwrite=False; sc.render.use_placeholder=False
    sc.render.filepath=OUT; bpy.ops.render.render(animation=True)
