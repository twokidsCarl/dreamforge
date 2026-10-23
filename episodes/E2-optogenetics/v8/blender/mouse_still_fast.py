"""Fast locked-glb stills for SF10 poster + SF18/19 insets. $0 CPU, nice-friendly."""
import bpy, mathutils, math, sys, os
import numpy as np
OUTDIR = '/workspace/e2work/v8/renders/sf10_hero'
os.makedirs(OUTDIR, exist_ok=True)
# Import scene builder by running mouse_scene with MODE=proj then hijack — simpler: duplicate minimal path
# Exec mouse_scene body with forced MODE still but override samples after import.
sys.argv = [sys.argv[0], '--', 'still', OUTDIR + '/_tmp.png', '40000']
# We'll run mouse_scene until render settings, then override — monkeypatch bpy.ops.render.render
_real_render = bpy.ops.render.render
_calls = []
def _fake_render(**kw):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.cycles.samples = 28
    sc.cycles.use_denoising = True
    # fiber ON for awake poster
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'POINT':
            o.data.energy = 6
    for mat in bpy.data.materials:
        if mat.name == 'jacket' and mat.node_tree:
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Emission Strength'].default_value = 1.2
    sc.render.filepath = OUTDIR + '/awake.png'
    _real_render(write_still=True)
    # fiber OFF for sleep
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'POINT':
            o.data.energy = 0
    for mat in bpy.data.materials:
        if mat.name == 'jacket' and mat.node_tree:
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Emission Strength'].default_value = 0.0
    sc.render.filepath = OUTDIR + '/sleep.png'
    _real_render(write_still=True)
    print('FAST_STILLS_DONE', OUTDIR)
bpy.ops.render.render = _fake_render
# run mouse_scene (will call our fake render in still branch)
exec(open('/workspace/e2work/v8/blender/mouse_scene.py').read())
