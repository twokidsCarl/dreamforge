"""Orthographic three-views from mouse_c57.glb vs mouse_ref — $0 local CPU.
Usage (when E1 Blender load drops):
  blender -b --factory-startup -P tools/mouse_threeview_orth.py
Writes: review/mouse_threeview_sheet.png
"""
import bpy, math
from mathutils import Vector
from pathlib import Path

ROOT = Path('/workspace/e2work/v8')
GLB = ROOT / 'tripo' / 'mouse_c57.glb'
OUT = ROOT / 'review' / 'mouse_threeview_sheet.png'
REF = ROOT / 'gen' / 'mouse_ref.png'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=str(GLB))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert meshes, 'no mesh'
# bbox
import numpy as np
coords = []
for m in meshes:
    for v in m.data.vertices:
        coords.append(m.matrix_world @ v.co)
co = np.array([(c.x, c.y, c.z) for c in coords])
center = Vector(co.mean(axis=0).tolist())
extent = float((co.max(0) - co.min(0)).max())
# studio
world = bpy.data.worlds.new('W'); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.75, 0.75, 0.78, 1); bg.inputs[1].default_value = 1.0
# lights
def area(loc, energy=80):
    d = bpy.data.lights.new('L', 'AREA'); d.energy = energy; d.size = extent
    o = bpy.data.objects.new('L', d); sc.collection.objects.link(o); o.location = loc
area(center + Vector((extent, -extent, extent)), 120)
area(center + Vector((-extent, extent, extent * 0.5)), 40)

camdata = bpy.data.cameras.new('C'); camdata.type = 'ORTHO'; camdata.ortho_scale = extent * 1.35
cam = bpy.data.objects.new('C', camdata); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'

views = {
    'side': (center + Vector((0, -extent * 2.2, 0)), (math.radians(90), 0, 0)),
    'front': (center + Vector((extent * 2.2, 0, 0)), (math.radians(90), 0, math.radians(90))),
    'top': (center + Vector((0, 0, extent * 2.2)), (0, 0, 0)),
}
outs = []
tmp = ROOT / 'review' / '_tv'
tmp.mkdir(exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    # aim: simpler — track to center
    cam.constraints.clear()
    t = cam.constraints.new('TRACK_TO'); t.target = bpy.data.objects.new('T', None)
    sc.collection.objects.link(t.target); t.target.location = center
    t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
    path = tmp / f'{name}.png'
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    outs.append(path)

# contact sheet with ref
try:
    from PIL import Image, ImageDraw, ImageFont
    tiles = [Image.open(p).convert('RGB') for p in outs]
    ref = Image.open(REF).convert('RGB'); ref.thumbnail((512, 512))
    sheet = Image.new('RGB', (512 * 4, 512), (30, 30, 34))
    labels = ['SIDE(glb)', 'FRONT(glb)', 'TOP(glb)', 'REF photo']
    for i, im in enumerate(tiles + [ref]):
        sheet.paste(im.resize((512, 512)), (i * 512, 0))
    d = ImageDraw.Draw(sheet)
    for i, lab in enumerate(labels):
        d.text((i * 512 + 12, 12), lab, fill=(255, 220, 80))
    sheet.save(OUT)
    print('WROTE', OUT)
except Exception as e:
    print('sheet failed', e, 'tiles', outs)
