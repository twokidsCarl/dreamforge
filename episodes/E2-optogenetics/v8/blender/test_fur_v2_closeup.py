"""Render a razor-sharp 1280x720 close-up verification frame of the V2 Dual-Layer Tapered Curved Fur
on locked `mouse_c57.glb`:
Output: /workspace/e2work/v8/renders/fur_v2_closeup.png
Complete 3D Darboux-Frame + Shadowless Fill Solution:
1. Full 3D Orthonormal Surface Frame `(pt_n, pt_btan, pt_binorm = pt_n x pt_btan)`:
   - On the dorsal silhouette, `pt_n` is in the camera image plane, so the normal arch `(0.65 * t - 0.45 * t^2.2) * pt_n` curves the silhouette hairs.
   - On the cheek, neck, shoulder, and flank (where `pt_n` points at the camera and is foreshortened!), `pt_binorm` is in the camera image plane (`+/-Z`)! Adding a graceful gravity S-drape `(0.42 * t - 0.68 * t^2.2) * pt_binorm` + per-clump wave along `pt_binorm` makes every single hair on the cheek, neck, shoulder, and flank visibly curve in the 2D image!
2. Shadowless Camera Fill Light (`L.data.use_shadow = False` near camera) + `Melanin = 0.80` -> completely eliminates the pitch-black self-shadowed creases (`Patch1` on neck/shoulder and `Patch2` on flank) that looked like bald black skin patches!
"""
import bpy, mathutils, math, sys, os, random
import numpy as np
from mathutils import Vector

OUT_PATH = '/workspace/e2work/v8/renders/fur_v2_closeup.png'
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
imp = Vector(top)

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

# 1) Smooth outward normal `n_smooth`
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

# 2) Strictly orthogonal backward tangent `b_tan = normalize(B - (B . n_smooth) * n_smooth)`
B_flow = np.array([[0.0, sgn * 1.0, -0.12]], dtype=np.float32)
B_flow /= np.linalg.norm(B_flow)
dot_bn = (B_flow * n_smooth).sum(axis=1, keepdims=True)
b_tan = B_flow - dot_bn * n_smooth
# Enforce outward lateral flare on cheek/neck/shoulder so hairs never angle inward into the shoulder bulge!
lat_sign = np.where(co[:, 0:1] >= x_mid, 1.0, -1.0)
lat_mag = np.clip(np.abs(co[:, 0:1] - x_mid) / 0.06, 0.0, 1.0)
b_tan[:, 0:1] = lat_sign * np.maximum(lat_sign * b_tan[:, 0:1], 0.38 * lat_mag)
b_tan /= np.maximum(np.linalg.norm(b_tan, axis=1, keepdims=True), 1e-6)

# 3) Third orthonormal basis vector `b_binorm = normalize(n_smooth x b_tan)` (oriented so Z >= 0, i.e., dorsal-up in the side-view image plane!)
b_binorm = np.cross(n_smooth, b_tan)
b_binorm /= np.maximum(np.linalg.norm(b_binorm, axis=1, keepdims=True), 1e-6)
# Ensure `b_binorm` always points upward (+Z) on both left and right sides of the body so gravity drape is symmetric!
b_binorm = np.where(b_binorm[:, 2:3] < 0.0, -b_binorm, b_binorm)

# Extremity masks:
paw_fac = np.clip((0.056 - co[:, 2]) / 0.012, 0.0, 1.0)
tail_fac = np.clip((0.42 - dist_tail) / 0.03, 0.0, 1.0)
nose_fac = np.clip((0.025 - dist_nose) / 0.008, 0.0, 1.0)
is_ear = ((co[:, 2] > (imp[2] - 0.002)) & (dist_nose > 0.12) & (dist_nose < 0.25) & (np.abs(co[:, 0] - x_mid) > 0.045) & (v_pink > 0.095)).astype(np.float32)
ebox = (dist_nose > 0.055) & (dist_nose < 0.145) & (co[:, 2] > 0.105) & (co[:, 2] < 0.185) & (np.abs(co[:, 0] - x_mid) > 0.025)
is_eye = ebox & (v_lum <= np.percentile(v_lum[ebox], 15))

pink_mask = np.maximum(np.maximum(paw_fac, tail_fac), np.maximum(nose_fac, is_ear)).astype(np.float32)
w = (1.0 - pink_mask) * (1.0 - is_eye.astype(np.float32))
if is_eye.sum() > 0:
    for ept in co[is_eye][::3]:
        w *= np.clip((np.linalg.norm(co - ept, axis=1) - 0.022) / 0.010, 0.0, 1.0)
    # Add proud glossy corneal eye spheres on both sides so eye catchlight is 100% unobstructed by cheek fur!
    mat_cornea = bpy.data.materials.new('cornea_gloss')
    mat_cornea.use_nodes = True
    cbsdf = mat_cornea.node_tree.nodes['Principled BSDF']
    cbsdf.inputs['Base Color'].default_value = (0.002, 0.002, 0.003, 1.0)
    cbsdf.inputs['Roughness'].default_value = 0.015
    if 'Specular IOR Level' in cbsdf.inputs:
        cbsdf.inputs['Specular IOR Level'].default_value = 1.0
    for esgn in (-1, 1):
        esub = is_eye & ((co[:, 0] - x_mid) * esgn > 0)
        if esub.any():
            ec = Vector(co[esub].mean(axis=0)) + Vector((esgn * 0.006, 0.0, 0.002))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=0.0125, location=ec)
            eob = bpy.context.object
            for poly in eob.data.polygons: poly.use_smooth = True
            eob.data.materials.append(mat_cornea)

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
co_local = np.array([v.co[:] for v in m.data.vertices], dtype=np.float32)
recess = (np.clip((w - 0.25) / 0.5, 0.0, 1.0)[:, None]) * n_smooth * 0.0032
m.data.vertices.foreach_set('co', (co_local - recess).ravel())
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
mx_skin.inputs[6].default_value = (0.055, 0.042, 0.034, 1.0)  # Warm C57 mid-charcoal under-fur skin (never black!)
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

# --- Step 3: Native `CURVES` Object (`FurObj`) with Full 3D Darboux-Frame Arching + Gravity Drape ---
hc = bpy.data.hair_curves.new('FurData')
fur_obj = bpy.data.objects.new('FurObj', hc)
sc.collection.objects.link(fur_obj)
fur_obj.data.materials.append(hm)

ng = bpy.data.node_groups.new('FurV2', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, K = ng.nodes, ng.links
go = N.new('NodeGroupOutput')

oi = N.new('GeometryNodeObjectInfo')
oi.inputs['Object'].default_value = m
oi.transform_space = 'RELATIVE'

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

    # Store `pt_n`, `pt_btan`, `pt_binorm`, and randomized `pt_len` on the distributed points BEFORE `InstanceOnPoints`!
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

    # 1) Outward Normal Arch: `h_norm(t) = pt_n * (pt_len * (0.85 * t - 0.62 * t^2.1))`
    mul_t1 = N.new('ShaderNodeMath')
    mul_t1.operation = 'MULTIPLY'
    mul_t1.inputs[1].default_value = 0.85
    K.new(sp.outputs['Factor'], mul_t1.inputs[0])

    pow_t21 = N.new('ShaderNodeMath')
    pow_t21.operation = 'POWER'
    pow_t21.inputs[1].default_value = 2.1
    K.new(sp.outputs['Factor'], pow_t21.inputs[0])

    mul_t21 = N.new('ShaderNodeMath')
    mul_t21.operation = 'MULTIPLY'
    mul_t21.inputs[1].default_value = 0.62
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

    # 2) Tangential Sweep: `s_tan(t) = pt_btan * (pt_len * (0.20 * t + 1.15 * t^1.75))`
    mul_tb1 = N.new('ShaderNodeMath')
    mul_tb1.operation = 'MULTIPLY'
    mul_tb1.inputs[1].default_value = 0.20
    K.new(sp.outputs['Factor'], mul_tb1.inputs[0])

    pow_t175 = N.new('ShaderNodeMath')
    pow_t175.operation = 'POWER'
    pow_t175.inputs[1].default_value = 1.75
    K.new(sp.outputs['Factor'], pow_t175.inputs[0])

    mul_tb2 = N.new('ShaderNodeMath')
    mul_tb2.operation = 'MULTIPLY'
    mul_tb2.inputs[1].default_value = 1.15
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

    # 3) Cross-Tangential (Binormal) Gravity S-Drape: `b_binorm * (pt_len * (0.45 * t - 0.72 * t^2.1))`
    #    Because `pt_binorm` is in the 2D image plane (`+/-Z`) on the cheek, neck, shoulder, and flank,
    #    this gives EVERY lateral hair a pronounced, graceful 2D arch & downward curve in the side view!
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

    # Crisp Tip Taper: radius = root_rad * (1.0 - pow(t, 0.78)) + 0.000010
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
    density=280000.0, len_min=0.018, len_max=0.025, root_rad=0.00022,
    clump_amp=0.0042, wave_amp=0.0028, seed=11
)
guard_geo = build_fur_layer(
    density=55000.0, len_min=0.026, len_max=0.036, root_rad=0.00026,
    clump_amp=0.0036, wave_amp=0.0024, seed=77
)

j = N.new('GeometryNodeJoinGeometry')
K.new(undercoat_geo, j.inputs['Geometry'])
K.new(guard_geo, j.inputs['Geometry'])
K.new(j.outputs['Geometry'], go.inputs[0])

md = fur_obj.modifiers.new('fur', 'NODES')
md.node_group = ng

# Delicate, translucent, curved & tapered vibrissae (whiskers)
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
        p0 = nose_pt + Vector((side * 0.020, 0, k * 0.002 - 0.005))
        for i, bp in enumerate(sp.bezier_points):
            t = i / 3.0
            p = p0 + d * L * t + Vector((0, 0, -0.012 * t * t))
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = 'AUTO'
            bp.radius = max(0.02, (1.0 - t) ** 1.8)
        ob = bpy.data.objects.new('whisker', cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(wm)

# Implant + fiber
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.011, depth=0.05, location=imp + Vector((0, 0, 0.02)))
fer = bpy.context.object
cm = bpy.data.materials.new('ceramic'); cm.use_nodes = True; cb = cm.node_tree.nodes['Principled BSDF']
cb.inputs['Base Color'].default_value = (0.9, 0.88, 0.82, 1); cb.inputs['Roughness'].default_value = 0.35
cb.inputs['Emission Color'].default_value = (0.15, 0.5, 1, 1); cb.inputs['Emission Strength'].default_value = 0.6
fer.data.materials.append(cm)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.016, depth=0.012, location=imp + Vector((0, 0, 0.004)))
cap = bpy.context.object
dm = bpy.data.materials.new('cement'); dm.use_nodes = True
dm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.75, 0.72, 1)
cap.data.materials.append(dm)

cu = bpy.data.curves.new('fiber', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0040; cu.bevel_resolution = 6; cu.resolution_u = 32
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
pts = [imp + Vector((0, 0, 0.045)), imp + Vector((-0.05, -sgn * 0.15, 0.45)), Vector((imp.x - 0.1, imp.y - sgn * 0.2, 1.6))]
for bpnt, p in zip(sp.bezier_points, pts):
    bpnt.co = p; bpnt.handle_left_type = bpnt.handle_right_type = 'AUTO'
fo = bpy.data.objects.new('fiber', cu); sc.collection.objects.link(fo)
km = bpy.data.materials.new('jacket'); km.use_nodes = True; kb = km.node_tree.nodes['Principled BSDF']
kb.inputs['Base Color'].default_value = (0.05, 0.15, 0.32, 1); kb.inputs['Roughness'].default_value = 0.35
kb.inputs['Emission Color'].default_value = (0.12, 0.52, 1, 1); kb.inputs['Emission Strength'].default_value = 0.9
fo.data.materials.append(km)

bpy.ops.object.light_add(type='POINT', location=imp + Vector((0, 0, 0.03)))
gl = bpy.context.object; gl.data.color = (0.15, 0.5, 1); gl.data.energy = 4.0; gl.data.shadow_soft_size = 0.03

# Matte wood-chip floor bedding
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); fl = bpy.context.object
fm = bpy.data.materials.new('floor'); fm.use_nodes = True; Nn = fm.node_tree.nodes; Lk = fm.node_tree.links; fb = Nn['Principled BSDF']
tc_ = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.5, 4.5, 4.5); Lk.new(tc_.outputs['UV'], mp.inputs[0])
def T(f, cs):
    t = Nn.new('ShaderNodeTexImage'); t.image = bpy.data.images.load('/workspace/e2work/v8/assets/wood_chips/' + f); t.image.colorspace_settings.name = cs; Lk.new(mp.outputs[0], t.inputs[0]); return t
d = T('Diffuse.jpg', 'sRGB'); nn = T('nor_gl.jpg', 'Non-Color')
hs = Nn.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.35; hs.inputs['Saturation'].default_value = 0.75; Lk.new(d.outputs[0], hs.inputs['Color']); Lk.new(hs.outputs[0], fb.inputs['Base Color'])
fb.inputs['Roughness'].default_value = 0.90
if 'Specular IOR Level' in fb.inputs:
    fb.inputs['Specular IOR Level'].default_value = 0.05
nm = Nn.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.2; Lk.new(nn.outputs[0], nm.inputs['Color']); Lk.new(nm.outputs[0], fb.inputs['Normal']); fl.data.materials.append(fm)

def area(loc, rot, energy, color, size, cast_shadow=True):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    L = bpy.context.object; L.data.energy = energy; L.data.color = color; L.data.size = size
    L.data.use_shadow = cast_shadow
    c = L.constraints.new('TRACK_TO'); c.target = m; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return L

area((1.4, -sgn * 1.0, 1.3), (0, 0, 0), 175, (0.98, 0.98, 1.0), 1.2, True)
area((-1.2, sgn * 0.9, 0.95), (0, 0, 0), 360, (0.82, 0.90, 1.0), 0.65, True)
area((0.5, -sgn * 0.3, 2.2), (0, 0, 0), 28, (0.88, 0.92, 1.0), 2.0, True)
# Shadowless camera-side fill light (`use_shadow=False`) so concave neck/shoulder/flank creases NEVER turn into black holes!
area((1.35, -sgn * 0.85, 0.25), (0, 0, 0), 115, (0.96, 0.97, 1.0), 1.8, False)

w_ = bpy.data.worlds.new('w'); sc.world = w_; w_.use_nodes = True; w_.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.016, 0.04, 1)

cam = bpy.data.cameras.new('cam'); cam.lens = 55; cam.dof.use_dof = False
co_ = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co_); sc.camera = co_
ctr = Vector((float(np.median(co[:, 0])), ynose * 0.15, 0.17))
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt); tgt.location = ctr
tc = co_.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
co_.location = ctr + Vector((1.22, -sgn * 0.82, 0.32))

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles_curves.shape = 'THICK'
sc.cycles_curves.subdivisions = 2
sc.cycles.sample_clamp_direct = 2.8
sc.cycles.sample_clamp_indirect = 1.8
sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'
sc.cycles.filter_width = 0.85
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = (1280, 720)
sc.cycles.samples = 40
sc.render.filepath = OUT_PATH
bpy.ops.render.render(write_still=True)
print('SAVED_FUR_V2_DARBOUX_FILL', OUT_PATH, flush=True)
