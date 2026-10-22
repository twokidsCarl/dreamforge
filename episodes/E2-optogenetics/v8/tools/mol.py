"""Flat Goodsell-style molecule drawing shared by SF06/SF08/SF09 (retinal, azobenzene).
Same look everywhere: rounded thick bonds, dark outline, soft top highlight, methyl nubs."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter

def hexring(cx, cy, r, rot=0.0):
    return [(cx + r*math.cos(rot + k*math.pi/3), cy + r*math.sin(rot + k*math.pi/3)) for k in range(6)]

def retinal_geom():
    """all-trans retinal: beta-ionone ring (non-aromatic, one C5=C6 double bond, gem-dimethyl C1, methyl C5),
    polyene chain C7..C15 with methyls on C9 and C13, Schiff base N to Lys. Local units: bond length 1."""
    ring = hexring(0, 0, 1.0, rot=math.pi/6)        # C1..C6 order around ring
    C = {f'C{i+1}': ring[i] for i in range(6)}
    # ring atoms: choose C6 = attachment point (right side)
    # relabel so C6 is the rightmost vertex
    idx = max(range(6), key=lambda i: ring[i][0])
    order = [(idx + k) % 6 for k in range(6)]          # C6, C1, C2, C3, C4, C5 going around
    names = ['C6', 'C1', 'C2', 'C3', 'C4', 'C5']
    C = {n: ring[i] for n, i in zip(names, order)}
    bonds = [('C6', 'C1', 1), ('C1', 'C2', 1), ('C2', 'C3', 1), ('C3', 'C4', 1), ('C4', 'C5', 1), ('C5', 'C6', 2)]
    # chain zigzag to the right
    x, y = C['C6']; up = True; chain = ['C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'N']
    prev = 'C6'; orders = [1, 2, 1, 2, 1, 2, 1, 2, 2]   # C6-C7 single, C7=C8, C8-C9, C9=C10, ... C15=N
    for i, n in enumerate(chain):
        x += math.cos(math.pi/6); y += (-0.5 if up else 0.5); up = not up
        C[n] = (x, y); bonds.append((prev, n, orders[i] if i < len(orders) else 1)); prev = n
    # Lys stub
    x += math.cos(math.pi/6); y += (-0.5 if up else 0.5); C['Lys'] = (x, y); bonds.append(('N', 'Lys', 1))
    # methyls: C1 gem-dimethyl, C5, C9, C13
    def methyl(a, name, ang_off=0.0, length=0.8):
        ax, ay = C[a]
        # direction away from ring centre / chain side
        if a in ('C1', 'C5'):
            vx, vy = ax - 0, ay - 0
        else:
            # perpendicular, on the 'outer' side of the zigzag vertex
            vy = -1 if C[a][1] < C['C7'][1] + 0.01 else 1; vx = 0
        L = math.hypot(vx, vy); vx, vy = vx/L, vy/L
        ca, sa = math.cos(ang_off), math.sin(ang_off); vx, vy = vx*ca - vy*sa, vx*sa + vy*ca
        C[name] = (ax + vx*length, ay + vy*length); bonds.append((a, name, 1))
    methyl('C1', 'M1a', 0.55); methyl('C1', 'M1b', -0.55); methyl('C5', 'M5'); methyl('C9', 'M9'); methyl('C13', 'M13')
    nubs = ['M1a', 'M1b', 'M5', 'M9', 'M13']
    return C, bonds, nubs, {'N': (90, 140, 255)}

def azobenzene_geom(cis=False):
    """trans azobenzene Ph-N=N-Ph (aromatic rings) with a tether stub (maleimide linker) on one ring"""
    C = {}; bonds = []
    r1 = hexring(0, 0, 1.0, rot=0)
    for i, p in enumerate(r1): C[f'a{i}'] = p
    for i in range(6): bonds.append((f'a{i}', f'a{(i+1)%6}', 2 if i % 2 == 0 else 1))
    C['N1'] = (r1[0][0] + 0.9, r1[0][1] + 0.5)
    C['N2'] = (C['N1'][0] + 1.0, C['N1'][1] - 0.0) if not cis else (C['N1'][0] + 0.5, C['N1'][1] + 0.87)
    bonds += [('a0', 'N1', 1), ('N1', 'N2', 2)]
    bx, by = (C['N2'][0] + 0.9, C['N2'][1] - 0.5) if not cis else (C['N2'][0] + 0.2, C['N2'][1] + 0.98)
    r2 = hexring(bx + 1.0, by, 1.0, rot=0) if not cis else hexring(bx + 0.5, by + 0.87, 1.0, rot=math.pi/3)
    for i, p in enumerate(r2): C[f'b{i}'] = p
    for i in range(6): bonds.append((f'b{i}', f'b{(i+1)%6}', 2 if i % 2 == 0 else 1))
    near = min(range(6), key=lambda i: math.hypot(r2[i][0]-C['N2'][0], r2[i][1]-C['N2'][1]))
    bonds.append(('N2', f'b{near}', 1))
    # tether from far side of ring a
    C['T1'] = (r1[3][0] - 0.9, r1[3][1] + 0.5); C['T2'] = (C['T1'][0] - 0.9, C['T1'][1] + 0.5)
    bonds += [('a3', 'T1', 1), ('T1', 'T2', 1)]
    return C, bonds, [], {'N1': (90, 140, 255), 'N2': (90, 140, 255)}

def draw(geom, size_px, angle_deg, fill=(244, 146, 60), outline=(70, 34, 18), scale=1.0, ss=4, highlight=True, bond=0.30):
    """render molecule to RGBA (premultiplied-free), returns (PIL image, anchor offset of local origin)"""
    C, bonds, nubs, atoms = geom
    a = math.radians(angle_deg); ca, sa = math.cos(a), math.sin(a)
    pts = {k: (x*ca - y*sa, x*sa + y*ca) for k, (x, y) in C.items()}
    xs = [p[0] for p in pts.values()]; ys = [p[1] for p in pts.values()]
    span = max(max(xs)-min(xs), max(ys)-min(ys)); u = size_px*ss/span*scale
    pad = 0.12*size_px*ss + 10
    W = int((max(xs)-min(xs))*u + 2*pad); H = int((max(ys)-min(ys))*u + 2*pad)
    P = {k: ((x-min(xs))*u + pad, (y-min(ys))*u + pad) for k, (x, y) in pts.items()}
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bw = bond*u; ow = bw + 0.16*u
    def seg(p, q, w, col):
        d.line([p, q], fill=col, width=max(1, int(w)))
        for c in (p, q): d.ellipse([c[0]-w/2, c[1]-w/2, c[0]+w/2, c[1]+w/2], fill=col)
    for (p, q, o) in bonds: seg(P[p], P[q], ow, (*outline, 255))
    for n in nubs: c = P[n]; r = 0.30*u; d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=(*outline, 255))
    for k, col in atoms.items(): c = P[k]; r = 0.33*u; d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=(*outline, 255))
    for (p, q, o) in bonds: seg(P[p], P[q], bw, (*fill, 255))
    for n in nubs: c = P[n]; r = 0.22*u; d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=(*fill, 255))
    for k, col in atoms.items(): c = P[k]; r = 0.25*u; d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=(*col, 255))
    # double bonds: thin dark inner line offset toward the inside
    for (p, q, o) in bonds:
        if o != 2: continue
        (x0, y0), (x1, y1) = P[p], P[q]; L = math.hypot(x1-x0, y1-y0); nx, ny = -(y1-y0)/L, (x1-x0)/L
        sh = 0.0; t0 = 0.22
        d.line([(x0+(x1-x0)*t0+nx*sh, y0+(y1-y0)*t0+ny*sh), (x1-(x1-x0)*t0+nx*sh, y1-(y1-y0)*t0+ny*sh)], fill=(*outline, 210), width=max(1, int(0.07*u)))
    if highlight:
        arr = np.asarray(im).astype(np.float32); A = arr[..., 3:4]/255
        hl = Image.fromarray((A[..., 0]*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.12*u))
        hl = np.asarray(hl).astype(np.float32)/255
        sh = np.roll(hl, (int(0.10*u), int(0.06*u)), (0, 1))          # light from upper-left
        lit = np.clip(hl - sh, 0, 1)[..., None]
        inner = (arr[..., :3] != np.array(outline)).any(-1, keepdims=True)
        arr[..., :3] = np.clip(arr[..., :3] + lit*inner*90, 0, 255)
        im = Image.fromarray(arr.astype(np.uint8))
    im = im.resize((W//ss, H//ss), Image.LANCZOS)
    return im, P

def composite(base_rgb01, sprite, center_xy, glow=None):
    """paste sprite centred at pixel xy into float image"""
    out = base_rgb01.copy(); w, h = sprite.size; x0 = int(center_xy[0]-w/2); y0 = int(center_xy[1]-h/2)
    a = np.asarray(sprite).astype(np.float32)/255
    H, W = out.shape[:2]; xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0+w), min(H, y0+h)
    if xb <= xa or yb <= ya: return out
    sa = a[ya-y0:yb-y0, xa-x0:xb-x0]
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb]*(1-sa[..., 3:4]) + sa[..., :3]*sa[..., 3:4]
    return out
