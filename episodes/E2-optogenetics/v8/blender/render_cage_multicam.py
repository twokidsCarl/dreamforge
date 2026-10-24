"""Render 7 Multi-Camera V2-Fur 3D Mouse & Experimental Cage Sequences from locked `mouse_c57.glb`
using the full 3D Darboux-Frame Arching + Gravity S-Drape + 0.0032 BU Skin Recess Cushion +
Outward Lateral Flare + Scale=320 Shaft Wave + Chiang Principled Hair BSDF (Melanin=0.82) +
Shadowless Camera Fill Light + Proud Corneal Eye Catchlights:
1. sf10_camA (8f): Slow-wave sleep breathing -> 470nm blue fiber pulse ON (zero orange dot!).
2. sf10_camB (8f): Front-3/4 close-up of 470nm pulse -> head lift, awakening & forward stride start.
3. sf10_camC (8f): Low-angle hero tracking shot of active walking stride across dark wood-chip bedding.
4. cage_envA (8f): High-angle 3/4 view inside Transparent Acrylic Cage A (470nm blue pulse + exploration walk).
5. cage_envB (8f): Conditioning Chamber B with metal shock-grid floor rods + warm amber light + 470nm blue recall.
6. cage_nphr (8f): Transparent cage under 590nm yellow-amber NpHR chloride-pump light inhibition.
7. cage_comm (8f): Overhead rotary commutator joint + Context A fear-freezing micro-breathing posture.
"""
import bpy, mathutils, math, sys, os, random
import numpy as np
from mathutils import Vector
import sys as _sys
_sys.path.insert(0, '/workspace/e2work/v8/blender')
from mouse_eye_anatomy import place_c57_eyes, apply_eye_fur_gap

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT_DIR = argv[0] if argv else '/workspace/e2work/v8/renders/mouse_v2_seqs'
SAMPLES = int(argv[1]) if len(argv) > 1 else 16
RES = (int(argv[2]), int(argv[3])) if len(argv) > 3 else (960, 540)
GROUP = argv[4] if len(argv) > 4 else 'all'
os.makedirs(OUT_DIR, exist_ok=True)
GLB = '/workspace/e2work/v8/tripo/mouse_c57.glb'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24

bpy.ops.import_scene.gltf(filepath=GLB)
m = [o for o in sc.objects if o.type == 'MESH'][0]
m.name = 'Mouse'
bpy.context.view_layer.update()

co = np.array([m.matrix_world @ v.co for v in m.data.vertices], dtype=np.float32)
m.location.z -= float(co[:, 2].min())
bpy.context.view_layer.update()
co = np.array([m.matrix_world @ v.co for v in m.data.vertices], dtype=np.float32)

ymin, ymax = float(co[:, 1].min()), float(co[:, 1].max())
def ext(a, b):
    s = co[(co[:, 1] >= a) & (co[:, 1] <= b)]
    return float(np.ptp(s[:, 0])) if len(s) else 0.0

nose_at_min = ext(ymin, ymin + 0.12) > ext(ymax - 0.12, ymax)
sgn = 1.0 if nose_at_min else -1.0
ynose = ymin if nose_at_min else ymax
ytail = ymax if nose_at_min else ymin

sl = co[(np.abs(co[:, 1] - ynose) > 0.10) & (np.abs(co[:, 1] - ynose) < 0.15) & (np.abs(co[:, 0] - np.median(co[:, 0])) < 0.03)]
top = sl[sl[:, 2].argmax()]
imp0 = Vector(top)

# --- Step 1: Watertight Mesh + Full Orthonormal Darboux Frame (`smooth_n`, `smooth_btan`, `smooth_binorm`) ---
for poly in m.data.polygons:
    poly.use_smooth = True
bpy.context.view_layer.update()

mat = m.data.materials[0]
mnodes = mat.node_tree.nodes
mlinks = mat.node_tree.links
bsdf = next(n for n in mnodes if n.type == 'BSDF_PRINCIPLED')

tex = None
lk = bsdf.inputs['Base Color'].links
if lk:
    n = lk[0].from_node
    while n.type != 'TEX_IMAGE' and n.inputs and n.inputs[0].links:
        n = n.inputs[0].links[0].from_node
    if n.type == 'TEX_IMAGE':
        tex = n.image

W, H = tex.size
px = np.array(tex.pixels[:], dtype=np.float32).reshape(H, W, 4)
nv = len(m.data.vertices)
vc = np.zeros((nv, 3), dtype=np.float32)
cnt = np.zeros((nv, 1), dtype=np.float32)
li = np.array([l.vertex_index for l in m.data.loops])
uvs = np.array([d.uv[:] for d in m.data.uv_layers.active.data])
xs = np.clip((uvs[:, 0] % 1) * W, 0, W - 1).astype(int)
ys = np.clip((uvs[:, 1] % 1) * H, 0, H - 1).astype(int)
c = px[ys, xs, :3]
np.add.at(vc, li, c)
np.add.at(cnt, li[:, None], 1.0)
vc /= np.maximum(cnt, 1.0)
v_lum = vc.mean(axis=1)
v_pink = vc[:, 0] - vc[:, 2]

dist_nose = np.abs(co[:, 1] - ynose)
dist_tail = np.abs(co[:, 1] - ytail)
x_mid = float(np.median(co[:, 0]))

v_norms = np.array([v.normal[:] for v in m.data.vertices], dtype=np.float32)
z_spine = np.clip(0.08 + 0.16 * np.clip(dist_nose / 0.35, 0.0, 1.0), 0.08, 0.14)
rad_vec = np.stack([
    (co[:, 0] - x_mid) * 1.45,
    -sgn * 0.35 * np.clip((0.22 - dist_nose) / 0.22, 0.0, 1.0),
    (co[:, 2] - z_spine) * 1.15,
], axis=1)
rad_norm = rad_vec / np.maximum(np.linalg.norm(rad_vec, axis=1, keepdims=True), 1e-6)
dot_rn = (v_norms * rad_norm).sum(axis=1, keepdims=True)
v_norms_out = np.where(dot_rn < 0.0, -v_norms, v_norms)
n_smooth = 0.75 * rad_norm + 0.25 * v_norms_out
n_smooth /= np.maximum(np.linalg.norm(n_smooth, axis=1, keepdims=True), 1e-6)

B_flow = np.array([[0.0, sgn * 1.0, -0.12]], dtype=np.float32)
B_flow /= np.linalg.norm(B_flow)
dot_bn = (B_flow * n_smooth).sum(axis=1, keepdims=True)
b_tan = B_flow - dot_bn * n_smooth
lat_sign = np.where(co[:, 0:1] >= x_mid, 1.0, -1.0)
lat_mag = np.clip(np.abs(co[:, 0:1] - x_mid) / 0.06, 0.0, 1.0)
b_tan[:, 0:1] = lat_sign * np.maximum(lat_sign * b_tan[:, 0:1], 0.38 * lat_mag)
b_tan /= np.maximum(np.linalg.norm(b_tan, axis=1, keepdims=True), 1e-6)

b_binorm = np.cross(n_smooth, b_tan)
b_binorm /= np.maximum(np.linalg.norm(b_binorm, axis=1, keepdims=True), 1e-6)
b_binorm = np.where(b_binorm[:, 2:3] < 0.0, -b_binorm, b_binorm)

paw_fac = np.clip((0.056 - co[:, 2]) / 0.012, 0.0, 1.0)
tail_fac = np.clip((0.42 - dist_tail) / 0.03, 0.0, 1.0)
nose_fac = np.clip((0.025 - dist_nose) / 0.008, 0.0, 1.0)
is_ear = ((co[:, 2] > (imp0[2] - 0.002)) & (dist_nose > 0.12) & (dist_nose < 0.25) & (np.abs(co[:, 0] - x_mid) > 0.045) & (v_pink > 0.095)).astype(np.float32)
# Anatomical orbital anchors (NO luminance-percentile ebox)
is_eye, eye_centers, eye_radius = place_c57_eyes(
    co, ynose=ynose, sgn=sgn, x_mid=x_mid, imp_z=float(imp0[2]),
    v_lum=v_lum, v_pink=v_pink,
)
print('EYE_ANATOMY', 'n=', int(is_eye.sum()), 'radius=', round(eye_radius, 5),
      'centers=', [list(map(float, c)) for _, c in eye_centers], flush=True)

pink_mask = np.maximum(np.maximum(paw_fac, tail_fac), np.maximum(nose_fac, is_ear)).astype(np.float32)
w = (1.0 - pink_mask) * (1.0 - is_eye.astype(np.float32))
w = apply_eye_fur_gap(w, co, eye_centers, eye_radius)

cns_boost = 1.0 + 0.85 * np.exp(-((dist_nose - 0.19) / 0.14) ** 2)
w_dens = (w * cns_boost).astype(np.float32)

head_len = np.clip((dist_nose - 0.020) / 0.045, 0.55, 1.05)
ankle_len = np.clip((co[:, 2] - 0.042) / 0.035, 0.55, 1.05)
w_len = np.minimum(head_len, ankle_len).astype(np.float32)

attr_fur = m.data.attributes.new(name='fur_mask', type='FLOAT', domain='POINT')
attr_fur.data.foreach_set('value', w_dens)
attr_len = m.data.attributes.new(name='fur_len', type='FLOAT', domain='POINT')
attr_len.data.foreach_set('value', w_len)
attr_pink = m.data.attributes.new(name='pink_mask', type='FLOAT', domain='POINT')
attr_pink.data.foreach_set('value', pink_mask)
attr_eye = m.data.attributes.new(name='eye_mask', type='FLOAT', domain='POINT')
attr_eye.data.foreach_set('value', is_eye.astype(np.float32))
attr_nsm = m.data.attributes.new(name='smooth_n', type='FLOAT_VECTOR', domain='POINT')
attr_nsm.data.foreach_set('vector', n_smooth.ravel())
attr_btan = m.data.attributes.new(name='smooth_btan', type='FLOAT_VECTOR', domain='POINT')
attr_btan.data.foreach_set('vector', b_tan.ravel())
attr_bbin = m.data.attributes.new(name='smooth_binorm', type='FLOAT_VECTOR', domain='POINT')
attr_bbin.data.foreach_set('vector', b_binorm.ravel())

# Recess furry skin vertices inward by 0.0032 BU so convex cheek/neck/shoulder ridges never poke through the curved fur!
co_local0 = np.array([v.co[:] for v in m.data.vertices], dtype=np.float32)
recess = (np.clip((w - 0.25) / 0.5, 0.0, 1.0)[:, None]) * n_smooth * 0.0032
co_base = co_local0 - recess
m.data.vertices.foreach_set('co', co_base.ravel())
m.data.update()

for sock_name in ('Base Color', 'Metallic', 'Roughness', 'Normal'):
    if sock_name in bsdf.inputs:
        for lk in list(bsdf.inputs[sock_name].links):
            mlinks.remove(lk)
bsdf.inputs['Metallic'].default_value = 0.0
if 'Coat Weight' in bsdf.inputs:
    bsdf.inputs['Coat Weight'].default_value = 0.0

sh_pink = mnodes.new('ShaderNodeAttribute')
sh_pink.attribute_name = 'pink_mask'
sh_eye = mnodes.new('ShaderNodeAttribute')
sh_eye.attribute_name = 'eye_mask'

mx_skin = mnodes.new('ShaderNodeMix')
mx_skin.data_type = 'RGBA'
mx_skin.blend_type = 'MIX'
mlinks.new(sh_pink.outputs['Fac'], mx_skin.inputs['Factor'])
mx_skin.inputs[6].default_value = (0.055, 0.042, 0.034, 1.0)
mx_skin.inputs[7].default_value = (0.22, 0.115, 0.125, 1.0)

mx_eye_col = mnodes.new('ShaderNodeMix')
mx_eye_col.data_type = 'RGBA'
mx_eye_col.blend_type = 'MIX'
mlinks.new(sh_eye.outputs['Fac'], mx_eye_col.inputs['Factor'])
mlinks.new(mx_skin.outputs[2], mx_eye_col.inputs[6])
mx_eye_col.inputs[7].default_value = (0.002, 0.002, 0.003, 1.0)
mlinks.new(mx_eye_col.outputs[2], bsdf.inputs['Base Color'])

mx_rough = mnodes.new('ShaderNodeMix')
mx_rough.data_type = 'FLOAT'
mlinks.new(sh_eye.outputs['Fac'], mx_rough.inputs['Factor'])
mx_rough.inputs[2].default_value = 1.00
mx_rough.inputs[3].default_value = 0.02
mlinks.new(mx_rough.outputs['Result'], bsdf.inputs['Roughness'])

mx_spec = mnodes.new('ShaderNodeMix')
mx_spec.data_type = 'FLOAT'
mlinks.new(sh_eye.outputs['Fac'], mx_spec.inputs['Factor'])
mx_spec.inputs[2].default_value = 0.00
mx_spec.inputs[3].default_value = 0.95
if 'Specular IOR Level' in bsdf.inputs:
    mlinks.new(mx_spec.outputs['Result'], bsdf.inputs['Specular IOR Level'])

bsdf.inputs['Subsurface Weight'].default_value = 0.0

# --- Step 2: Chiang Principled Hair BSDF (`Melanin=0.82, Melanin Redness=0.22, Roughness=0.38, Radial Roughness=0.52, Coat=0.0`) ---
hm = bpy.data.materials.new('fur_v2')
hm.use_nodes = True
nt = hm.node_tree
for x in list(nt.nodes):
    if x.type == 'BSDF_PRINCIPLED':
        nt.nodes.remove(x)
hbsdf = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
try:
    hbsdf.parametrization = 'MELANIN'
except Exception:
    pass
hbsdf.inputs['Melanin'].default_value = 0.82
hbsdf.inputs['Melanin Redness'].default_value = 0.22
hbsdf.inputs['Roughness'].default_value = 0.38
hbsdf.inputs['Radial Roughness'].default_value = 0.52
hbsdf.inputs['Coat'].default_value = 0.0
hbsdf.inputs['IOR'].default_value = 1.54
hbsdf.inputs['Random Roughness'].default_value = 0.16
hbsdf.inputs['Random Color'].default_value = 0.20
nt.links.new(hbsdf.outputs[0], next(x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL').inputs[0])

# --- Step 3: Native `CURVES` Object (`FurObj`) Parented to `m` ---
hc = bpy.data.hair_curves.new('FurData')
fur_obj = bpy.data.objects.new('FurObj', hc)
sc.collection.objects.link(fur_obj)
fur_obj.data.materials.append(hm)
fur_obj.parent = m

ng = bpy.data.node_groups.new('FurV2', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, K = ng.nodes, ng.links
go = N.new('NodeGroupOutput')

oi = N.new('GeometryNodeObjectInfo')
oi.inputs['Object'].default_value = m
oi.transform_space = 'ORIGINAL'

na = N.new('GeometryNodeInputNamedAttribute')
na.data_type = 'FLOAT'
na.inputs['Name'].default_value = 'fur_mask'

na_len = N.new('GeometryNodeInputNamedAttribute')
na_len.data_type = 'FLOAT'
na_len.inputs['Name'].default_value = 'fur_len'

na_nsm = N.new('GeometryNodeInputNamedAttribute')
na_nsm.data_type = 'FLOAT_VECTOR'
na_nsm.inputs['Name'].default_value = 'smooth_n'

na_btan = N.new('GeometryNodeInputNamedAttribute')
na_btan.data_type = 'FLOAT_VECTOR'
na_btan.inputs['Name'].default_value = 'smooth_btan'

na_bbin = N.new('GeometryNodeInputNamedAttribute')
na_bbin.data_type = 'FLOAT_VECTOR'
na_bbin.inputs['Name'].default_value = 'smooth_binorm'

def build_fur_layer(density, len_min, len_max, root_rad, clump_amp, wave_amp, seed):
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    dist.inputs['Seed'].default_value = seed
    K.new(oi.outputs['Geometry'], dist.inputs['Mesh'])

    mul_dens = N.new('ShaderNodeMath')
    mul_dens.operation = 'MULTIPLY'
    mul_dens.inputs[1].default_value = density
    K.new(na.outputs['Attribute'], mul_dens.inputs[0])
    K.new(mul_dens.outputs['Value'], dist.inputs['Density'])

    st_n = N.new('GeometryNodeStoreNamedAttribute')
    st_n.data_type = 'FLOAT_VECTOR'
    st_n.domain = 'POINT'
    st_n.inputs['Name'].default_value = 'pt_n'
    K.new(dist.outputs['Points'], st_n.inputs['Geometry'])
    K.new(na_nsm.outputs['Attribute'], st_n.inputs['Value'])

    st_btan = N.new('GeometryNodeStoreNamedAttribute')
    st_btan.data_type = 'FLOAT_VECTOR'
    st_btan.domain = 'POINT'
    st_btan.inputs['Name'].default_value = 'pt_btan'
    K.new(st_n.outputs['Geometry'], st_btan.inputs['Geometry'])
    K.new(na_btan.outputs['Attribute'], st_btan.inputs['Value'])

    st_bbin = N.new('GeometryNodeStoreNamedAttribute')
    st_bbin.data_type = 'FLOAT_VECTOR'
    st_bbin.domain = 'POINT'
    st_bbin.inputs['Name'].default_value = 'pt_binorm'
    K.new(st_btan.outputs['Geometry'], st_bbin.inputs['Geometry'])
    K.new(na_bbin.outputs['Attribute'], st_bbin.inputs['Value'])

    rnd = N.new('FunctionNodeRandomValue')
    rnd.data_type = 'FLOAT'
    rnd.inputs['Min'].default_value = len_min
    rnd.inputs['Max'].default_value = len_max
    rnd.inputs['Seed'].default_value = seed + 100

    mul_len = N.new('ShaderNodeMath')
    mul_len.operation = 'MULTIPLY'
    K.new(rnd.outputs['Value'], mul_len.inputs[0])
    K.new(na_len.outputs['Attribute'], mul_len.inputs[1])

    st_len = N.new('GeometryNodeStoreNamedAttribute')
    st_len.data_type = 'FLOAT'
    st_len.domain = 'POINT'
    st_len.inputs['Name'].default_value = 'pt_len'
    K.new(st_bbin.outputs['Geometry'], st_len.inputs['Geometry'])
    K.new(mul_len.outputs['Value'], st_len.inputs['Value'])

    cl = N.new('GeometryNodeCurvePrimitiveLine')
    cl.inputs['End'].default_value = (0.0, 0.0, 0.0)
    rs = N.new('GeometryNodeResampleCurve')
    rs.inputs['Count'].default_value = 8
    K.new(cl.outputs['Curve'], rs.inputs['Curve'])

    iop = N.new('GeometryNodeInstanceOnPoints')
    K.new(st_len.outputs['Geometry'], iop.inputs['Points'])
    K.new(rs.outputs['Curve'], iop.inputs['Instance'])

    ri = N.new('GeometryNodeRealizeInstances')
    K.new(iop.outputs['Instances'], ri.inputs['Geometry'])

    in_n = N.new('GeometryNodeInputNamedAttribute')
    in_n.data_type = 'FLOAT_VECTOR'
    in_n.inputs['Name'].default_value = 'pt_n'

    in_btan = N.new('GeometryNodeInputNamedAttribute')
    in_btan.data_type = 'FLOAT_VECTOR'
    in_btan.inputs['Name'].default_value = 'pt_btan'

    in_bbin = N.new('GeometryNodeInputNamedAttribute')
    in_bbin.data_type = 'FLOAT_VECTOR'
    in_bbin.inputs['Name'].default_value = 'pt_binorm'

    in_len = N.new('GeometryNodeInputNamedAttribute')
    in_len.data_type = 'FLOAT'
    in_len.inputs['Name'].default_value = 'pt_len'

    sp = N.new('GeometryNodeSplineParameter')

    # 1) Outward Normal Arch + 0.0032 Recess Cushion
    mul_t1 = N.new('ShaderNodeMath')
    mul_t1.operation = 'MULTIPLY'
    mul_t1.inputs[1].default_value = 0.95
    K.new(sp.outputs['Factor'], mul_t1.inputs[0])

    pow_t21 = N.new('ShaderNodeMath')
    pow_t21.operation = 'POWER'
    pow_t21.inputs[1].default_value = 2.1
    K.new(sp.outputs['Factor'], pow_t21.inputs[0])

    mul_t21 = N.new('ShaderNodeMath')
    mul_t21.operation = 'MULTIPLY'
    mul_t21.inputs[1].default_value = 0.72
    K.new(pow_t21.outputs['Value'], mul_t21.inputs[0])

    sub_hn = N.new('ShaderNodeMath')
    sub_hn.operation = 'SUBTRACT'
    K.new(mul_t1.outputs['Value'], sub_hn.inputs[0])
    K.new(mul_t21.outputs['Value'], sub_hn.inputs[1])

    mul_hn_len = N.new('ShaderNodeMath')
    mul_hn_len.operation = 'MULTIPLY'
    K.new(sub_hn.outputs['Value'], mul_hn_len.inputs[0])
    K.new(in_len.outputs['Attribute'], mul_hn_len.inputs[1])

    add_cushion = N.new('ShaderNodeMath')
    add_cushion.operation = 'ADD'
    add_cushion.inputs[1].default_value = 0.0032
    K.new(mul_hn_len.outputs['Value'], add_cushion.inputs[0])

    v_norm_arch = N.new('ShaderNodeVectorMath')
    v_norm_arch.operation = 'SCALE'
    K.new(in_n.outputs['Attribute'], v_norm_arch.inputs[0])
    K.new(add_cushion.outputs['Value'], v_norm_arch.inputs['Scale'])

    # 2) Tangential Sweep
    mul_tb1 = N.new('ShaderNodeMath')
    mul_tb1.operation = 'MULTIPLY'
    mul_tb1.inputs[1].default_value = 0.15
    K.new(sp.outputs['Factor'], mul_tb1.inputs[0])

    pow_t175 = N.new('ShaderNodeMath')
    pow_t175.operation = 'POWER'
    pow_t175.inputs[1].default_value = 1.75
    K.new(sp.outputs['Factor'], pow_t175.inputs[0])

    mul_tb2 = N.new('ShaderNodeMath')
    mul_tb2.operation = 'MULTIPLY'
    mul_tb2.inputs[1].default_value = 1.35
    K.new(pow_t175.outputs['Value'], mul_tb2.inputs[0])

    add_tb = N.new('ShaderNodeMath')
    add_tb.operation = 'ADD'
    K.new(mul_tb1.outputs['Value'], add_tb.inputs[0])
    K.new(mul_tb2.outputs['Value'], add_tb.inputs[1])

    mul_tb_len = N.new('ShaderNodeMath')
    mul_tb_len.operation = 'MULTIPLY'
    K.new(add_tb.outputs['Value'], mul_tb_len.inputs[0])
    K.new(in_len.outputs['Attribute'], mul_tb_len.inputs[1])

    v_tan_sweep = N.new('ShaderNodeVectorMath')
    v_tan_sweep.operation = 'SCALE'
    K.new(in_btan.outputs['Attribute'], v_tan_sweep.inputs[0])
    K.new(mul_tb_len.outputs['Value'], v_tan_sweep.inputs['Scale'])

    # 3) Binormal Gravity S-Drape
    mul_bb1 = N.new('ShaderNodeMath')
    mul_bb1.operation = 'MULTIPLY'
    mul_bb1.inputs[1].default_value = 0.45
    K.new(sp.outputs['Factor'], mul_bb1.inputs[0])

    mul_bb2 = N.new('ShaderNodeMath')
    mul_bb2.operation = 'MULTIPLY'
    mul_bb2.inputs[1].default_value = 0.72
    K.new(pow_t21.outputs['Value'], mul_bb2.inputs[0])

    sub_bb = N.new('ShaderNodeMath')
    sub_bb.operation = 'SUBTRACT'
    K.new(mul_bb1.outputs['Value'], sub_bb.inputs[0])
    K.new(mul_bb2.outputs['Value'], sub_bb.inputs[1])

    mul_bb_len = N.new('ShaderNodeMath')
    mul_bb_len.operation = 'MULTIPLY'
    K.new(sub_bb.outputs['Value'], mul_bb_len.inputs[0])
    K.new(in_len.outputs['Attribute'], mul_bb_len.inputs[1])

    v_binorm_drape = N.new('ShaderNodeVectorMath')
    v_binorm_drape.operation = 'SCALE'
    K.new(in_bbin.outputs['Attribute'], v_binorm_drape.inputs[0])
    K.new(mul_bb_len.outputs['Value'], v_binorm_drape.inputs['Scale'])

    add_ba1 = N.new('ShaderNodeVectorMath')
    add_ba1.operation = 'ADD'
    K.new(v_norm_arch.outputs['Vector'], add_ba1.inputs[0])
    K.new(v_tan_sweep.outputs['Vector'], add_ba1.inputs[1])

    add_ba = N.new('ShaderNodeVectorMath')
    add_ba.operation = 'ADD'
    K.new(add_ba1.outputs['Vector'], add_ba.inputs[0])
    K.new(v_binorm_drape.outputs['Vector'], add_ba.inputs[1])

    # 4) Clumping (`Scale=55`) + High-Frequency Shaft S-Wave (`Scale=320`)
    pos_in = N.new('GeometryNodeInputPosition')
    wave_coord = N.new('ShaderNodeVectorMath')
    wave_coord.operation = 'ADD'
    K.new(pos_in.outputs['Position'], wave_coord.inputs[0])
    K.new(add_ba.outputs['Vector'], wave_coord.inputs[1])

    nz_clump = N.new('ShaderNodeTexNoise')
    nz_clump.inputs['Scale'].default_value = 55.0
    nz_clump.inputs['Detail'].default_value = 2.0
    sub_c = N.new('ShaderNodeVectorMath')
    sub_c.operation = 'SUBTRACT'
    sub_c.inputs[1].default_value = (0.5, 0.5, 0.5)
    K.new(nz_clump.outputs['Color'], sub_c.inputs[0])
    sc_c = N.new('ShaderNodeVectorMath')
    sc_c.operation = 'SCALE'
    sc_c.inputs['Scale'].default_value = clump_amp
    K.new(sub_c.outputs['Vector'], sc_c.inputs[0])

    nz_wave = N.new('ShaderNodeTexNoise')
    nz_wave.inputs['Scale'].default_value = 320.0
    nz_wave.inputs['Detail'].default_value = 1.5
    K.new(wave_coord.outputs['Vector'], nz_wave.inputs['Vector'])
    sub_w = N.new('ShaderNodeVectorMath')
    sub_w.operation = 'SUBTRACT'
    sub_w.inputs[1].default_value = (0.5, 0.5, 0.5)
    K.new(nz_wave.outputs['Color'], sub_w.inputs[0])
    sc_w = N.new('ShaderNodeVectorMath')
    sc_w.operation = 'SCALE'
    sc_w.inputs['Scale'].default_value = wave_amp
    K.new(sub_w.outputs['Vector'], sc_w.inputs[0])

    add_nf = N.new('ShaderNodeVectorMath')
    add_nf.operation = 'ADD'
    K.new(sc_c.outputs['Vector'], add_nf.inputs[0])
    K.new(sc_w.outputs['Vector'], add_nf.inputs[1])

    mul_t = N.new('ShaderNodeVectorMath')
    mul_t.operation = 'SCALE'
    K.new(add_nf.outputs['Vector'], mul_t.inputs[0])
    K.new(sp.outputs['Factor'], mul_t.inputs['Scale'])

    tot_off = N.new('ShaderNodeVectorMath')
    tot_off.operation = 'ADD'
    K.new(add_ba.outputs['Vector'], tot_off.inputs[0])
    K.new(mul_t.outputs['Vector'], tot_off.inputs[1])

    set_pos = N.new('GeometryNodeSetPosition')
    K.new(ri.outputs['Geometry'], set_pos.inputs['Geometry'])
    K.new(tot_off.outputs['Vector'], set_pos.inputs['Offset'])

    pow_tap = N.new('ShaderNodeMath')
    pow_tap.operation = 'POWER'
    pow_tap.inputs[1].default_value = 0.78
    K.new(sp.outputs['Factor'], pow_tap.inputs[0])

    sub_tap = N.new('ShaderNodeMath')
    sub_tap.operation = 'SUBTRACT'
    sub_tap.inputs[0].default_value = 1.0
    K.new(pow_tap.outputs['Value'], sub_tap.inputs[1])

    mul_rad = N.new('ShaderNodeMath')
    mul_rad.operation = 'MULTIPLY'
    mul_rad.inputs[1].default_value = root_rad
    K.new(sub_tap.outputs['Value'], mul_rad.inputs[0])

    add_min = N.new('ShaderNodeMath')
    add_min.operation = 'ADD'
    add_min.inputs[1].default_value = 0.000010
    K.new(mul_rad.outputs['Value'], add_min.inputs[0])

    rad = N.new('GeometryNodeSetCurveRadius')
    K.new(set_pos.outputs['Geometry'], rad.inputs['Curve'])
    K.new(add_min.outputs['Value'], rad.inputs['Radius'])

    sm = N.new('GeometryNodeSetMaterial')
    K.new(rad.outputs['Curve'], sm.inputs['Geometry'])
    sm.inputs['Material'].default_value = hm
    return sm.outputs['Geometry']

undercoat_geo = build_fur_layer(
    density=210000.0, len_min=0.018, len_max=0.025, root_rad=0.00022,
    clump_amp=0.0042, wave_amp=0.0028, seed=11
)
guard_geo = build_fur_layer(
    density=42000.0, len_min=0.026, len_max=0.036, root_rad=0.00026,
    clump_amp=0.0036, wave_amp=0.0024, seed=77
)

j = N.new('GeometryNodeJoinGeometry')
K.new(undercoat_geo, j.inputs['Geometry'])
K.new(guard_geo, j.inputs['Geometry'])
K.new(j.outputs['Geometry'], go.inputs[0])

md = fur_obj.modifiers.new('fur', 'NODES')
md.node_group = ng

# Head pivot empty for whiskers, corneal eyes, ferrule, cap, fiber anchor, and point light
head_piv = bpy.data.objects.new('head_piv', None)
sc.collection.objects.link(head_piv)
head_piv.parent = m
head_piv.location = imp0 - m.location

mat_cornea = bpy.data.materials.new('cornea_gloss')
mat_cornea.use_nodes = True
cbsdf = mat_cornea.node_tree.nodes['Principled BSDF']
cbsdf.inputs['Base Color'].default_value = (0.002, 0.002, 0.003, 1.0)
cbsdf.inputs['Roughness'].default_value = 0.015
if 'Specular IOR Level' in cbsdf.inputs:
    cbsdf.inputs['Specular IOR Level'].default_value = 1.0
for esgn, ctr in eye_centers:
    ec = Vector(ctr) - imp0
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=14, radius=eye_radius, location=ec)
    eob = bpy.context.object
    for poly in eob.data.polygons:
        poly.use_smooth = True
    eob.data.materials.append(mat_cornea)
    eob.parent = head_piv

wm = bpy.data.materials.new('whisker')
wm.use_nodes = True
wb = wm.node_tree.nodes['Principled BSDF']
wb.inputs['Base Color'].default_value = (0.35, 0.34, 0.32, 1)
wb.inputs['Roughness'].default_value = 0.25
nose_pt = Vector((float(np.median(co[:, 0])), ynose + sgn * 0.032, 0.112))
random.seed(4)
for side in (-1, 1):
    for k in range(6):
        cu = bpy.data.curves.new('wh', 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.00010
        cu.bevel_resolution = 2
        sp = cu.splines.new('BEZIER')
        sp.bezier_points.add(3)
        ang = math.radians(-20 + k * 7 + random.uniform(-2, 2))
        L = random.uniform(0.055, 0.088)
        d = (Vector((side * math.cos(ang) * 0.92, sgn * 0.22, math.sin(ang) * 0.28))).normalized()
        p0 = (nose_pt - imp0) + Vector((side * 0.020, 0, k * 0.002 - 0.005))
        for i, bp in enumerate(sp.bezier_points):
            t = i / 3.0
            p = p0 + d * L * t + Vector((0, 0, -0.012 * t * t))
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = 'AUTO'
            bp.radius = max(0.02, (1.0 - t) ** 1.8)
        ob = bpy.data.objects.new('whisker', cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(wm)
        ob.parent = head_piv

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.011, depth=0.05, location=(0, 0, 0.02))
fer = bpy.context.object; fer.parent = head_piv
cm = bpy.data.materials.new('ceramic'); cm.use_nodes = True; cb = cm.node_tree.nodes['Principled BSDF']
cb.inputs['Base Color'].default_value = (0.9, 0.88, 0.82, 1); cb.inputs['Roughness'].default_value = 0.35
cb.inputs['Emission Color'].default_value = (0.15, 0.5, 1, 1); cb.inputs['Emission Strength'].default_value = 0.6
fer.data.materials.append(cm)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.016, depth=0.012, location=(0, 0, 0.004))
cap = bpy.context.object; cap.parent = head_piv
dm = bpy.data.materials.new('cement'); dm.use_nodes = True
dm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.75, 0.72, 1)
cap.data.materials.append(dm)

cu = bpy.data.curves.new('fiber', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0040; cu.bevel_resolution = 6; cu.resolution_u = 32
sp_fib = cu.splines.new('BEZIER'); sp_fib.bezier_points.add(2)
fo = bpy.data.objects.new('fiber', cu); sc.collection.objects.link(fo)
km = bpy.data.materials.new('jacket'); km.use_nodes = True; kb = km.node_tree.nodes['Principled BSDF']
kb.inputs['Base Color'].default_value = (0.05, 0.15, 0.32, 1); kb.inputs['Roughness'].default_value = 0.35
kb.inputs['Emission Color'].default_value = (0.12, 0.52, 1, 1); kb.inputs['Emission Strength'].default_value = 0.9
fo.data.materials.append(km)

bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.035))
gl = bpy.context.object; gl.parent = head_piv; gl.data.color = (0.15, 0.5, 1); gl.data.energy = 4.0; gl.data.shadow_soft_size = 0.03

# Matte wood-chip floor bedding
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); fl = bpy.context.object
fm = bpy.data.materials.new('floor'); fm.use_nodes = True; Nn = fm.node_tree.nodes; Lk = fm.node_tree.links; fb = Nn['Principled BSDF']
tc_ = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.5, 4.5, 4.5); Lk.new(tc_.outputs['UV'], mp.inputs[0])
def T(f, cs):
    t = Nn.new('ShaderNodeTexImage'); t.image = bpy.data.images.load('/workspace/e2work/v8/assets/wood_chips/' + f); t.image.colorspace_settings.name = cs; Lk.new(mp.outputs[0], t.inputs[0]); return t
d = T('Diffuse.jpg', 'sRGB'); nn = T('nor_gl.jpg', 'Non-Color')
hs = Nn.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.34; hs.inputs['Saturation'].default_value = 0.75; Lk.new(d.outputs[0], hs.inputs['Color']); Lk.new(hs.outputs[0], fb.inputs['Base Color'])
fb.inputs['Roughness'].default_value = 0.90
if 'Specular IOR Level' in fb.inputs:
    fb.inputs['Specular IOR Level'].default_value = 0.05
nm = Nn.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.2; Lk.new(nn.outputs[0], nm.inputs['Color']); Lk.new(nm.outputs[0], fb.inputs['Normal']); fl.data.materials.append(fm)

# Transparent Acrylic Experimental Cage + Corner Posts + Overhead Rotary Commutator Joint + Shock Grid Rods
C0 = Vector((float(np.median(co[:, 0])), float(np.median(co[:, 1])), 0.0))
cage_mat = bpy.data.materials.new('cage_acrylic'); cage_mat.use_nodes = True
c_bsdf = cage_mat.node_tree.nodes['Principled BSDF']
c_bsdf.inputs['Base Color'].default_value = (0.82, 0.92, 1.0, 1)
c_bsdf.inputs['Transmission Weight'].default_value = 0.92
c_bsdf.inputs['Roughness'].default_value = 0.05
c_bsdf.inputs['IOR'].default_value = 1.49

metal_mat = bpy.data.materials.new('cage_metal'); metal_mat.use_nodes = True
m_bsdf = metal_mat.node_tree.nodes['Principled BSDF']
m_bsdf.inputs['Base Color'].default_value = (0.55, 0.60, 0.68, 1)
m_bsdf.inputs['Metallic'].default_value = 0.85
m_bsdf.inputs['Roughness'].default_value = 0.25

W_HALF = 0.68
H_CAGE = 0.76
# Place corner posts ONLY on the back wall (sx = -1) so front camera views are 100% unobstructed!
for sx in (-1,):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.015, depth=H_CAGE, location=C0 + Vector((sx * W_HALF, sy * W_HALF, H_CAGE / 2)))
        post = bpy.context.object; post.data.materials.append(metal_mat)
for sy in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=C0 + Vector((0, sy * W_HALF, H_CAGE)))
    bar = bpy.context.object; bar.scale = (W_HALF * 2, 0.018, 0.018); bar.data.materials.append(metal_mat)
for sx in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=C0 + Vector((sx * W_HALF, 0, H_CAGE)))
    bar = bpy.context.object; bar.scale = (0.018, W_HALF * 2, 0.018); bar.data.materials.append(metal_mat)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=C0 + Vector((0, 0, H_CAGE)))
xbar = bpy.context.object; xbar.scale = (W_HALF * 2, 0.022, 0.016); xbar.data.materials.append(metal_mat)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.042, depth=0.068, location=C0 + Vector((0, 0, H_CAGE - 0.02)))
comm = bpy.context.object; comm.data.materials.append(metal_mat)
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.018, depth=0.045, location=C0 + Vector((0, 0, H_CAGE - 0.065)))
comm_rotor = bpy.context.object; comm_rotor.data.materials.append(cm)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=C0 + Vector((-W_HALF, 0, H_CAGE / 2)))
bwall = bpy.context.object; bwall.scale = (0.008, W_HALF * 1.96, H_CAGE * 0.96); bwall.data.materials.append(cage_mat)

grid_objs = []
for gi_idx in range(-7, 8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0055, depth=W_HALF * 1.9, location=C0 + Vector((0, gi_idx * 0.09, 0.007)), rotation=(0, math.radians(90), 0))
    grod = bpy.context.object; grod.data.materials.append(metal_mat); grid_objs.append(grod)

def area(loc, energy, color, size, cast_shadow=True):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object; L.data.energy = energy; L.data.color = color; L.data.size = size
    L.data.use_shadow = cast_shadow
    c = L.constraints.new('TRACK_TO'); c.target = m; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return L

key_l = area((1.4, -sgn * 1.0, 1.3), 175, (0.98, 0.98, 1.0), 1.2, True)
rim_l = area((-1.2, sgn * 0.9, 0.95), 360, (0.82, 0.90, 1.0), 0.65, True)
top_l = area((0.5, -sgn * 0.3, 2.2), 28, (0.88, 0.92, 1.0), 2.0, True)
fill_l = area((1.35, -sgn * 0.85, 0.25), 115, (0.96, 0.97, 1.0), 1.8, False)

w_ = bpy.data.worlds.new('w'); sc.world = w_; w_.use_nodes = True; w_.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.016, 0.04, 1)

cam = bpy.data.cameras.new('cam'); cam.lens = 52; cam.dof.use_dof = False
co_ = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co_); sc.camera = co_
ctr0 = Vector((float(np.median(co[:, 0])), ynose * 0.15, 0.17))
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt); tgt.location = ctr0
tc = co_.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles_curves.shape = 'THICK'
sc.cycles_curves.subdivisions = 2
sc.cycles.sample_clamp_direct = 2.8
sc.cycles.sample_clamp_indirect = 1.8
sc.cycles.max_bounces = 2
sc.cycles.diffuse_bounces = 1
sc.cycles.glossy_bounces = 1
sc.cycles.transmission_bounces = 2
sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'
sc.cycles.filter_width = 0.85
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = RES
sc.cycles.samples = SAMPLES

d_nose0 = np.abs(co_local0[:, 1] - ynose)
head_wt = np.clip((0.28 - d_nose0) / 0.14, 0.0, 1.0) ** 1.5
breath_wt = np.exp(-((d_nose0 - 0.36) / 0.14) ** 2) * np.clip(co[:, 2] / 0.15, 0.0, 1.0)
is_low_limb = np.clip((0.095 - co[:, 2]) / 0.055, 0.0, 1.0)
front_wt = is_low_limb * np.clip((0.35 - d_nose0) / 0.10, 0.0, 1.0)
hind_wt  = is_low_limb * np.clip((d_nose0 - 0.38) / 0.10, 0.0, 1.0)
left_s   = (co_local0[:, 0] > x_mid).astype(np.float32)
right_s  = 1.0 - left_s
diag_A = front_wt * left_s + hind_wt * right_s
diag_B = front_wt * right_s + hind_wt * left_s
z_min_base = float(co_local0[:, 2].min())

def set_pose_and_fiber(head_pitch, head_yaw, breathe_amp, walk_dist, stride_phase, fiber_col, fiber_str, glow_str):
    v = co_base.copy()
    v[:, 0] += (v[:, 0] - x_mid) * (0.045 * breathe_amp) * breath_wt
    v[:, 2] += (0.012 * breathe_amp) * breath_wt
    v[:, 2] += head_pitch * head_wt
    v[:, 0] += head_yaw * head_wt
    if abs(stride_phase) > 1e-4:
        sA = math.sin(stride_phase)
        sB = -sA
        # Half lift / half paw-Y: forward travel, not in-place rock
        liftA = max(0.0, math.cos(stride_phase)) * 0.010
        liftB = max(0.0, -math.cos(stride_phase)) * 0.010
        v[:, 1] += (-sgn * 0.012 * sA) * diag_A + (-sgn * 0.012 * sB) * diag_B
        v[:, 2] += liftA * diag_A + liftB * diag_B

    m.data.vertices.foreach_set('co', v.ravel())
    m.data.update()
    m.location = (0.0, -sgn * walk_dist, -z_min_base)
    head_piv.location = (head_yaw * 0.85, imp0.y, imp0.z - z_min_base + head_pitch * 0.85)
    bpy.context.view_layer.update()

    imp_now = m.matrix_world @ head_piv.location
    top_comm = Vector((imp_now.x - 0.04, imp_now.y + sgn * 0.06, H_CAGE - 0.05))
    pts = [
        imp_now + Vector((0, 0, 0.042)),
        Vector((imp_now.x - 0.02, imp_now.y + sgn * 0.03, 0.36)),
        top_comm,
    ]
    for bpnt, p in zip(sp_fib.bezier_points, pts):
        bpnt.co = p
        bpnt.handle_left_type = bp.handle_right_type = 'AUTO'

    kb.inputs['Emission Color'].default_value = (*fiber_col, 1.0)
    kb.inputs['Emission Strength'].default_value = fiber_str
    cb.inputs['Emission Color'].default_value = (*fiber_col, 1.0)
    cb.inputs['Emission Strength'].default_value = fiber_str * 0.55
    gl.data.color = fiber_col
    gl.data.energy = glow_str

N_F = 5

def ease_mono(u):
    """Smoothstep 0→1. Monotonic. No return sweep."""
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)

# MOTION RULE (Carl): every mouse SF clip advances one way only.
# Forbidden: sin(2πu)/cos(2πu) head_yaw, breathe, stride reverse, camera orbit ping-pong.

if GROUP in ('all', 'part1', 'sf10_camA'):
    for g in grid_objs: g.hide_render = True
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        light_on = max(0.0, min(1.0, (eu - 0.35) / 0.25))
        set_pose_and_fiber(
            head_pitch=-0.022 * (1.0 - 0.4 * light_on), head_yaw=0.0,
            breathe_amp=0.06, walk_dist=0.0, stride_phase=0.0,
            fiber_col=(0.12, 0.55, 1.0), fiber_str=1.5 * light_on, glow_str=6.5 * light_on
        )
        co_.location = ctr0 + Vector((1.35 - 0.18 * eu, -sgn * (0.85 - 0.12 * eu), 0.34 - 0.04 * eu))
        tgt.location = ctr0
        sc.render.filepath = os.path.join(OUT_DIR, f'sf10_camA_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[sf10_camA] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part1', 'sf10_camB'):
    for g in grid_objs: g.hide_render = True
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        wake_u = eu
        walk_u = max(0.0, (eu - 0.25) / 0.75)
        pulse = 0.75 + 0.25 * eu
        set_pose_and_fiber(
            head_pitch=-0.012 + 0.038 * wake_u,
            head_yaw=0.010 * wake_u,
            breathe_amp=0.08,
            walk_dist=0.14 * walk_u,
            stride_phase=walk_u * math.pi * 0.9,
            fiber_col=(0.12, 0.55, 1.0), fiber_str=1.6 * pulse, glow_str=7.5 * pulse
        )
        cur_ctr = ctr0 + Vector((0, -sgn * 0.10 * walk_u, 0.01 * wake_u))
        tgt.location = cur_ctr
        co_.location = cur_ctr + Vector((1.05 - 0.10 * eu, -sgn * (1.12 - 0.10 * eu), 0.38 - 0.04 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'sf10_camB_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[sf10_camB] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part1', 'sf10_camC'):
    for g in grid_objs: g.hide_render = True
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        pulse = 0.8 + 0.2 * eu
        set_pose_and_fiber(
            head_pitch=0.022, head_yaw=0.0,
            breathe_amp=0.08,
            walk_dist=0.22 * eu,
            stride_phase=eu * math.pi * 1.0,
            fiber_col=(0.12, 0.55, 1.0), fiber_str=1.6 * pulse, glow_str=7.5 * pulse
        )
        cur_ctr = ctr0 + Vector((0, -sgn * 0.18 * eu, 0.01))
        tgt.location = cur_ctr
        co_.location = cur_ctr + Vector((1.18 - 0.12 * eu, -sgn * (0.55 - 0.25 * eu), 0.24 + 0.04 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'sf10_camC_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[sf10_camC] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part1', 'cage_envA'):
    for g in grid_objs: g.hide_render = True
    hs.inputs['Value'].default_value = 0.34
    key_l.data.color = (0.95, 0.97, 1.0)
    rim_l.data.color = (0.65, 0.82, 1.0)
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        pulse = 0.7 + 0.3 * eu
        set_pose_and_fiber(
            head_pitch=0.020, head_yaw=0.008 * eu,
            breathe_amp=0.08,
            walk_dist=0.18 * eu,
            stride_phase=eu * math.pi * 1.0,
            fiber_col=(0.10, 0.52, 1.0), fiber_str=1.7 * pulse, glow_str=8.0 * pulse
        )
        cur_ctr = ctr0 + Vector((0, -sgn * 0.14 * eu, 0.0))
        tgt.location = cur_ctr
        co_.location = cur_ctr + Vector((1.15 - 0.15 * eu, sgn * (0.75 - 0.20 * eu), 0.72 - 0.08 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'cage_envA_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[cage_envA] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part2', 'cage_envB'):
    for g in grid_objs: g.hide_render = False
    hs.inputs['Value'].default_value = 0.20
    key_l.data.color = (1.0, 0.65, 0.38)
    rim_l.data.color = (1.0, 0.48, 0.28)
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        pulse = 0.75 + 0.25 * eu
        set_pose_and_fiber(
            head_pitch=0.015, head_yaw=-0.008 * eu,
            breathe_amp=0.08,
            walk_dist=0.15 * eu,
            stride_phase=eu * math.pi * 1.0,
            fiber_col=(0.12, 0.56, 1.0), fiber_str=1.9 * pulse, glow_str=8.5 * pulse
        )
        cur_ctr = ctr0 + Vector((0, -sgn * 0.12 * eu, 0.0))
        tgt.location = cur_ctr
        co_.location = cur_ctr + Vector((1.10 - 0.12 * eu, -sgn * (1.05 - 0.18 * eu), 0.62 - 0.06 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'cage_envB_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[cage_envB] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part2', 'cage_nphr'):
    for g in grid_objs: g.hide_render = True
    hs.inputs['Value'].default_value = 0.30
    key_l.data.color = (1.0, 0.90, 0.78)
    rim_l.data.color = (1.0, 0.75, 0.32)
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        set_pose_and_fiber(
            head_pitch=-0.008 * eu, head_yaw=0.0,
            breathe_amp=0.07,
            walk_dist=0.04 * eu,
            stride_phase=eu * math.pi * 0.6,
            fiber_col=(1.0, 0.68, 0.12), fiber_str=2.0, glow_str=9.0
        )
        tgt.location = ctr0
        co_.location = ctr0 + Vector((0.98 + 0.12 * eu, -sgn * (0.88 - 0.15 * eu), 0.42 + 0.05 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'cage_nphr_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[cage_nphr] {f}/{N_F}', flush=True)

if GROUP in ('all', 'part2', 'cage_comm'):
    key_l.data.color = (0.92, 0.96, 1.0)
    rim_l.data.color = (0.55, 0.78, 1.0)
    for f in range(1, N_F + 1):
        u = (f - 1) / (N_F - 1)
        eu = ease_mono(u)
        pulse = 0.7 + 0.3 * eu
        set_pose_and_fiber(
            head_pitch=-0.015 - 0.004 * eu, head_yaw=0.0,
            breathe_amp=0.05,
            walk_dist=0.0, stride_phase=0.0,
            fiber_col=(0.12, 0.55, 1.0), fiber_str=1.6 * pulse, glow_str=7.5 * pulse
        )
        tgt.location = ctr0 + Vector((0, 0, 0.18))
        co_.location = ctr0 + Vector((1.28 - 0.15 * eu, -sgn * (0.65 - 0.25 * eu), 0.78 - 0.08 * eu))
        sc.render.filepath = os.path.join(OUT_DIR, f'cage_comm_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[cage_comm] {f}/{N_F}', flush=True)

print(f'MOUSE_V2_GROUP_{GROUP}_DONE', flush=True)
