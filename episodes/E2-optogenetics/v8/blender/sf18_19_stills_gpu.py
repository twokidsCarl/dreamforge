"""Render SF18/19 hero stills from locked mouse_c57.glb on GPU.
Outputs: sleep (fiber off), awake (fiber on), 3/4 view, top-ish — for macro_photo_boost insets.
Usage: blender -b --factory-startup -P sf18_19_stills_gpu.py -- OUT_DIR [SAMPLES] [W] [H]
"""
import bpy, mathutils, math, sys, os, random
import numpy as np
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT_DIR = argv[0] if argv else '/workspace/e2work/v8/renders/sf18_19_stills'
SAMPLES = int(argv[1]) if len(argv) > 1 else 96
RES = (int(argv[2]), int(argv[3])) if len(argv) > 3 else (1280, 720)
os.makedirs(OUT_DIR, exist_ok=True)
GLB = os.environ.get('MOUSE_GLB', '/workspace/e2work/v8/tripo/mouse_c57.glb')
CHIPS = os.environ.get('WOOD_CHIPS', '/workspace/e2work/v8/assets/wood_chips')
DENS = 150000.0

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
m = [o for o in sc.objects if o.type == 'MESH'][0]
m.name = 'Mouse'
bpy.context.view_layer.update()
co = np.array([m.matrix_world @ v.co for v in m.data.vertices])
m.location.z -= co[:, 2].min(); bpy.context.view_layer.update()
co = np.array([m.matrix_world @ v.co for v in m.data.vertices])
ymin, ymax = co[:, 1].min(), co[:, 1].max()

def ext(a, b):
    s = co[(co[:, 1] >= a) & (co[:, 1] <= b)]
    return np.ptp(s[:, 0]) if len(s) else 0

nose_at_min = ext(ymin, ymin + 0.12) > ext(ymax - 0.12, ymax)
sgn = 1 if nose_at_min else -1
ynose = ymin if nose_at_min else ymax
sl = co[(np.abs(co[:, 1] - ynose) > 0.10) & (np.abs(co[:, 1] - ynose) < 0.15) & (np.abs(co[:, 0] - np.median(co[:, 0])) < 0.03)]
top = sl[sl[:, 2].argmax()]
print('STILLS setup', nose_at_min, top)

mat = m.data.materials[0]
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
tex = None
lk = bsdf.inputs['Base Color'].links
if lk:
    n = lk[0].from_node
    while n.type != 'TEX_IMAGE' and n.inputs and n.inputs[0].links:
        n = n.inputs[0].links[0].from_node
    if n.type == 'TEX_IMAGE':
        tex = n.image
vg = m.vertex_groups.new(name='fur')
if tex:
    W, H = tex.size
    px = np.array(tex.pixels[:]).reshape(H, W, 4)
    uv = m.data.uv_layers.active.data
    w = np.zeros(len(m.data.vertices)); cnt = np.zeros(len(m.data.vertices))
    li = np.array([l.vertex_index for l in m.data.loops])
    uvs = np.array([d.uv[:] for d in uv])
    xs = np.clip((uvs[:, 0] % 1) * W, 0, W - 1).astype(int)
    ys = np.clip((uvs[:, 1] % 1) * H, 0, H - 1).astype(int)
    c = px[ys, xs, :3]; lum = c.mean(1); pink = c[:, 0] - c[:, 2]
    furry = ((lum < 0.22) & (pink < 0.12)).astype(float)
    np.add.at(w, li, furry); np.add.at(cnt, li, 1); w = w / np.maximum(cnt, 1)
    for i in np.nonzero(w > 0.5)[0]:
        vg.add([int(i)], 1.0, 'REPLACE')
    wh = np.zeros(len(m.data.vertices))
    np.add.at(wh, li, ((lum > 0.6) & (np.abs(pink) < 0.12)).astype(float)); wh /= np.maximum(cnt, 1)
    near = np.abs(co[:, 1] - ynose) < 0.13
    import bmesh
    bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table()
    dv = [bm.verts[i] for i in np.nonzero((wh > 0.7) & near)[0]]
    bmesh.ops.delete(bm, geom=dv, context='VERTS'); bm.to_mesh(m.data); bm.free()
bsdf.inputs['Roughness'].default_value = 0.6
try:
    bsdf.inputs['Subsurface Weight'].default_value = 0.15
    bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.25)
    bsdf.inputs['Subsurface Scale'].default_value = 0.01
except Exception:
    pass

FURLEN = 0.011
ng = bpy.data.node_groups.new('Fur', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, K = ng.nodes, ng.links
gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
dist = N.new('GeometryNodeDistributePointsOnFaces'); dist.inputs['Density'].default_value = DENS
na = N.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'; na.inputs['Name'].default_value = 'fur'
K.new(gi.outputs[0], dist.inputs['Mesh'])
K.new(na.outputs['Attribute'], [i for i in dist.inputs if i.name == 'Density Factor'][0])
sn = N.new('ShaderNodeVectorMath'); sn.operation = 'SCALE'; sn.inputs[3].default_value = 0.55
K.new(dist.outputs['Normal'], sn.inputs[0])
add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'; add.inputs[1].default_value = (0.0, 1.0 * sgn, -0.35)
K.new(sn.outputs[0], add.inputs[0])
nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 40
ns = N.new('ShaderNodeVectorMath'); ns.operation = 'SUBTRACT'; ns.inputs[1].default_value = (0.5, 0.5, 0.5)
K.new(nz.outputs['Color'], ns.inputs[0])
ns2 = N.new('ShaderNodeVectorMath'); ns2.operation = 'SCALE'; ns2.inputs[3].default_value = 0.9
K.new(ns.outputs[0], ns2.inputs[0])
add2 = N.new('ShaderNodeVectorMath'); add2.operation = 'ADD'
K.new(add.outputs[0], add2.inputs[0]); K.new(ns2.outputs[0], add2.inputs[1])
al = N.new('FunctionNodeAlignRotationToVector'); al.axis = 'Z'; K.new(add2.outputs[0], al.inputs['Vector'])
cl = N.new('GeometryNodeCurvePrimitiveLine'); cl.inputs['End'].default_value = (0, 0, 1)
rs = N.new('GeometryNodeResampleCurve'); rs.inputs['Count'].default_value = 3; K.new(cl.outputs[0], rs.inputs['Curve'])
rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT'
rnd.inputs['Min'].default_value = FURLEN * 0.6; rnd.inputs['Max'].default_value = FURLEN * 1.3
iop = N.new('GeometryNodeInstanceOnPoints')
K.new(dist.outputs['Points'], iop.inputs['Points']); K.new(rs.outputs[0], iop.inputs['Instance'])
K.new(al.outputs[0], iop.inputs['Rotation']); K.new(rnd.outputs['Value'], iop.inputs['Scale'])
ri = N.new('GeometryNodeRealizeInstances'); K.new(iop.outputs[0], ri.inputs[0])
rad = N.new('GeometryNodeSetCurveRadius'); rad.inputs['Radius'].default_value = 0.00035
K.new(ri.outputs[0], rad.inputs['Curve'])
sm = N.new('GeometryNodeSetMaterial'); K.new(rad.outputs[0], sm.inputs['Geometry'])
j = N.new('GeometryNodeJoinGeometry')
K.new(sm.outputs[0], j.inputs[0]); K.new(gi.outputs[0], j.inputs[0]); K.new(j.outputs[0], go.inputs[0])
hm = bpy.data.materials.new('fur'); hm.use_nodes = True; nt = hm.node_tree
for n in list(nt.nodes):
    if n.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n)
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
hb = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
try: hb.parametrization = 'MELANIN'
except Exception: pass
hb.inputs['Melanin'].default_value = 0.92; hb.inputs['Melanin Redness'].default_value = 0.45
hb.inputs['Roughness'].default_value = 0.32; hb.inputs['Radial Roughness'].default_value = 0.4; hb.inputs['Coat'].default_value = 0.15
nt.links.new(hb.outputs[0], out.inputs[0]); sm.inputs['Material'].default_value = hm
m.modifiers.new('fur', 'NODES').node_group = ng

bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); fl = bpy.context.object
fm = bpy.data.materials.new('floor'); fm.use_nodes = True
Nn, Lk = fm.node_tree.nodes, fm.node_tree.links; fb = Nn['Principled BSDF']
tc_ = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.5, 4.5, 4.5)
Lk.new(tc_.outputs['UV'], mp.inputs[0])
def T(f, cs):
    t = Nn.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(CHIPS, f))
    t.image.colorspace_settings.name = cs; Lk.new(mp.outputs[0], t.inputs[0]); return t
d = T('Diffuse.jpg', 'sRGB'); r = T('Rough.jpg', 'Non-Color'); nn = T('nor_gl.jpg', 'Non-Color')
hs = Nn.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.5; hs.inputs['Saturation'].default_value = 1.1
Lk.new(d.outputs[0], hs.inputs['Color']); Lk.new(hs.outputs[0], fb.inputs['Base Color'])
Lk.new(r.outputs[0], fb.inputs['Roughness'])
nm = Nn.new('ShaderNodeNormalMap'); Lk.new(nn.outputs[0], nm.inputs['Color']); Lk.new(nm.outputs[0], fb.inputs['Normal'])
fl.data.materials.append(fm)

imp = mathutils.Vector(top)
bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=0.05, location=imp + mathutils.Vector((0, 0, 0.02))); fer = bpy.context.object
cm = bpy.data.materials.new('ceramic'); cm.use_nodes = True; cb = cm.node_tree.nodes['Principled BSDF']
cb.inputs['Base Color'].default_value = (0.9, 0.88, 0.82, 1); cb.inputs['Roughness'].default_value = 0.35
cb.inputs['Emission Color'].default_value = (0.15, 0.5, 1, 1); fer.data.materials.append(cm)
bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.012, location=imp + mathutils.Vector((0, 0, 0.004))); cap = bpy.context.object
dm = bpy.data.materials.new('cement'); dm.use_nodes = True
dm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.75, 0.72, 1); cap.data.materials.append(dm)
cu = bpy.data.curves.new('fiber', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0035; cu.bevel_resolution = 4
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
pts = [imp + mathutils.Vector((0, 0, 0.045)), imp + mathutils.Vector((-0.05, -sgn * 0.15, 0.45)), mathutils.Vector((imp.x - 0.1, imp.y - sgn * 0.2, 1.6))]
for bpnt, p in zip(sp.bezier_points, pts):
    bpnt.co = p; bpnt.handle_left_type = bpnt.handle_right_type = 'AUTO'
fo = bpy.data.objects.new('fiber', cu); sc.collection.objects.link(fo)
km = bpy.data.materials.new('jacket'); km.use_nodes = True; kb = km.node_tree.nodes['Principled BSDF']
kb.inputs['Base Color'].default_value = (0.02, 0.05, 0.12, 1); kb.inputs['Roughness'].default_value = 0.4
kb.inputs['Emission Color'].default_value = (0.1, 0.45, 1, 1); fo.data.materials.append(km)
bpy.ops.object.light_add(type='POINT', location=imp + mathutils.Vector((0, 0, 0.03))); gl = bpy.context.object
gl.data.color = (0.15, 0.5, 1); gl.data.shadow_soft_size = 0.02

def area(loc, rot, energy, color, size):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    L = bpy.context.object; L.data.energy = energy; L.data.color = color; L.data.size = size; return L
area((1.4, -sgn * 1.0, 1.3), (math.radians(50), 0, math.radians(55 if sgn > 0 else 125)), 150, (1.0, 0.86, 0.72), 1.0)
area((-1.2, sgn * 0.9, 0.9), (math.radians(-60), 0, math.radians(-120 if sgn > 0 else -60)), 320, (0.45, 0.62, 1.0), 0.6)
area((0.5, -sgn * 0.3, 2.2), (0, 0, 0), 8, (0.6, 0.65, 1.0), 2)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.016, 0.04, 1)

cam = bpy.data.cameras.new('cam'); cam.lens = 55; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.8
co_ = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co_); sc.camera = co_
ctr = mathutils.Vector((float(np.median(co[:, 0])), ynose * 0.15, 0.17))
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt); tgt.location = ctr
tc = co_.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
cam.dof.focus_object = tgt

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'; prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type == 'CUDA')
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'; sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPTIX'
except Exception: pass
sc.cycles.samples = SAMPLES
sc.render.resolution_x, sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'

shots = [
    # name, cam_offset, fiber_e, glow_e, lens
    ('sleep_side', mathutils.Vector((1.55, -sgn * 0.90, 0.40)), 0.0, 0.0, 55),
    ('awake_side', mathutils.Vector((1.40, -sgn * 0.80, 0.36)), 1.4, 8.0, 55),
    ('awake_threeq', mathutils.Vector((1.10, -sgn * 1.35, 0.48)), 1.4, 8.0, 50),
    ('sleep_threeq', mathutils.Vector((1.20, -sgn * 1.25, 0.45)), 0.0, 0.0, 50),
]
for name, coff, fe, ge, lens in shots:
    cam.lens = lens
    co_.location = ctr + coff
    kb.inputs['Emission Strength'].default_value = fe
    try: cb.inputs['Emission Strength'].default_value = fe * 0.5
    except Exception: pass
    gl.data.energy = ge
    path = os.path.join(OUT_DIR, f'mouse_{name}.png')
    sc.render.filepath = path
    print('STILL', name, path)
    bpy.ops.render.render(write_still=True)
print('STILLS_DONE')
