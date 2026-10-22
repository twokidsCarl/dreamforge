"""Round 13 SF07 plate: image2 dorsal mouse brain (r13_sf07_brain: symmetric hemispheres, bulbs on the frontal poles)
+ procedurally painted optical fibre and a cyan neuron network on the upper (one) hemisphere -> gen/sf07i_brain.png.
The SF07 scene detects the cyan network by hue and lights it in waves from the fibre tip."""
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFilter
G = '/workspace/e2work/v8/gen/'
im = Image.open(G+'r13_sf07_brain.png').convert('RGB'); w, h = im.size
BT = (0.420, 0.300); tip = (BT[0]*w, BT[1]*h)
# hemisphere mask (upper cortex): coral pixels above the midline
a = np.asarray(im).astype(np.float32)
hsv = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2HSV)
cortex = ((hsv[..., 0] < 12) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 80) & (hsv[..., 2] > 150)
cortex[int(0.475*h):] = False; cortex[:, :int(0.215*w)] = False; cortex[:, int(0.585*w):] = False
cortex = cv2.GaussianBlur(cortex.astype(np.float32), (0, 0), 6) > 0.5
cortex = cv2.erode(cortex.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0
print('cortex px', cortex.sum())
rng = np.random.default_rng(7)
net = Image.new('L', (w, h), 0); d = ImageDraw.Draw(net); nodes = []
def branch(x, y, ang, L, wd, depth):
    if depth == 0 or L < 12: return
    n = int(L/6); px, py = x, y
    for i in range(n):
        ang += rng.normal(0, 0.12); nx, ny = px+6*math.cos(ang), py+6*math.sin(ang)
        if not (0 <= int(ny) < h and 0 <= int(nx) < w and cortex[int(ny), int(nx)]): break
        d.line([(px, py), (nx, ny)], fill=255, width=max(1, int(round(wd)))); px, py = nx, ny
    nodes.append((px, py))
    for sg in (-1, 1):
        if rng.random() < 0.85: branch(px, py, ang+sg*rng.uniform(0.35, 0.8), L*rng.uniform(0.55, 0.75), wd*0.7, depth-1)
for k in range(9):
    branch(tip[0], tip[1]+6, 2*math.pi*k/9+rng.normal(0, 0.15), rng.uniform(120, 190), 3.2, 5)
netf = np.asarray(net).astype(np.float32)/255
glow = cv2.GaussianBlur(netf, (0, 0), 3.5)
for (x, y) in nodes[::2]:
    cv2.circle(netf, (int(x), int(y)), 4, 1.0, -1)
core = np.clip(netf, 0, 1)
cyan = np.array([110, 235, 255], np.float32)
out = a*(1-core[..., None]*0.9)+cyan*core[..., None]*0.9
out = out+np.array([60, 170, 230], np.float32)*np.clip(glow*1.6, 0, 1)[..., None]*0.45
# tip glow
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); r = np.hypot(xx-tip[0], yy-tip[1])
out = out+np.array([120, 220, 255])*np.exp(-(r/26)**2)[..., None]*0.9
# fibre: dark ferrule + steel rod from the top edge to the tip
fib = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); fd = ImageDraw.Draw(fib)
x0 = tip[0]
fd.rectangle([x0-9, 0, x0+9, tip[1]-34], fill=(52, 54, 66)); fd.rectangle([x0-4, 0, x0-1, tip[1]-34], fill=(150, 154, 170))
fd.rectangle([x0-16, tip[1]-60, x0+16, tip[1]-6], fill=(70, 72, 88)); fd.rectangle([x0-11, tip[1]-58, x0-5, tip[1]-8], fill=(170, 175, 190))
fd.rectangle([x0-6, tip[1]-6, x0+6, tip[1]+2], fill=(160, 230, 255))
fib.save(G+'sf07i_brain.png'); print('ok', len(nodes))
