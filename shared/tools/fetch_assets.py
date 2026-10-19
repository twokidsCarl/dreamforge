"""Download the free third-party assets the shots use into shared/assets/ (not committed).

  python3 shared/tools/fetch_assets.py

Poly Haven assets are CC0 (public domain, commercial use OK, no attribution required):
https://polyhaven.com/license . Files are checked against the md5 the Poly Haven API publishes.
"""
import hashlib
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shared", "assets", "polyhaven")

# reflection environments (used only in glossy rays, see common.reflection_env)
HDRIS = {"studio_small_09": "2k", "hangar_interior": "2k", "rogland_moonlit_night": "2k"}
# PBR surfaces: floors, wet asphalt, a container side, painted / plated metal
TEXTURES = {"brushed_concrete": "1k", "asphalt_02": "1k", "container_side": "1k", "metal_plate": "1k",
            "corrugated_iron": "1k", "plywood": "1k"}
MAPS = {"Diffuse": "diff", "Rough": "rough", "nor_gl": "nor_gl", "Metal": "metal"}
# real die photographs, CC0 on Wikimedia Commons (Fritzchens Fritz): masks, chips, SEM dives.
# Only dies made with EUV may illustrate "drawn by this machine's light" (research/visual/chips.md, B):
# lunar_lake (TSMC N3B + N6), zen5_ccd_full (TSMC 4 nm), zen4_ccd_full (TSMC 5 nm) are EUV; the Skylake (14 nm)
# and launch PS5 (N7) photos are DUV-era and their colours are DIC lambda-plate false colour, not diffraction.
DIES = {
    "lunar_lake": "File:Intel@TSMC N3 N6@LunarLake@LNL(4P+4LPE)@CoreUltra200Series@DSCx01 poly@5xExt.jpg",
    "zen5_ccd_full": "File:AMD@4nmCCD(6nmIOD)@Zen5@Granite Ridge@Ryzen 5 9600X@100-000001405 BY 2429SUY 9AEQ579S40073 DSCx14 CCD poly@5xExt.jpg",
    "zen4_ccd_full": "File:AMD@5nmCCD(6nmIOD)@Zen4@Raphael@Ryzen 5 7600@100-000001015 BQ 2246SUY 9LS4795W20142 DSCx13 CCD poly@5xExt.jpg",
    "ps5_apu_a": "File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@100-000000189 9JF8970V00437 S DSC09299 - DSC09299 (50943150382).jpg",
    "ps5_apu_b": "File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@100-000000189 9JF8970V00437 S DSC09310 - DSC09310 (50943149857).jpg",
    "ps5_apu_stack": "File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@100-000000189 9JF8970V00437 S DSC09328-DSC09454 - ZS-retouched-3 (50943043431).jpg",
    "ps5_apu_ir": "File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@100-000000189 9JF8970V00437 S DSCx2@IR (50951750013).jpg",
    "xeon_poly": "File:Intel@14nm@Skylake@Skylake-SP(XCC)@Xeon(ES)@QJW5 DSCx8 poly@20x - Flickr - FritzchensFritz.jpg",
    "zen5_ccd": "File:AMD@4nmCCD(6nmIOD)@Zen5@Granite Ridge@Ryzen 5 9600X@100-000001405 BY 2429SUY 9AEQ579S40073 DSCx12 CCD topmetal@50xBF.jpg",
    "ps5_poly": "File:AMD@7nm@Zen2 RDNA APU@Oberon@PlayStation5@CXD90060GG 100-000000189 WM33440U00089 S DSCx6 poly@50xDICL - Flickr - FritzchensFritz.jpg",
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dreamforge-asset-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _save(url, md5, path):
    if os.path.exists(path) and hashlib.md5(open(path, "rb").read()).hexdigest() == md5:
        return "cached"
    data = _get(url)
    if hashlib.md5(data).hexdigest() != md5:
        raise RuntimeError(f"md5 mismatch for {url}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)
    return f"{len(data) // 1024} KB"


def region_map(src, dst, min_frac=0.035, depth=11, seed=7):
    """Functional blocks of a die photo as flat rectangles, each painted a random colour: the chip shader
    hashes that colour into the block's grating pitch and line orientation. A die layout is cut by long
    straight channels, so the photo is split recursively (guillotine cuts) at the column or row where the
    image changes most sharply along its whole length, until blocks get small or no clear channel is left."""
    import random
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("L")
    W = 960
    H = round(W * im.height / im.width)
    g = np.asarray(im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32)
    gx = np.abs(np.diff(g, axis=1))
    gy = np.abs(np.diff(g, axis=0))
    rnd = random.Random(seed)
    out = np.zeros((H, W, 3), dtype=np.uint8)
    m = int(min_frac * W)

    def cut(x0, y0, x1, y1, d):
        best = None
        if d > 0:
            if x1 - x0 > 2 * m:                             # vertical channel: a column of strong x-gradients
                prof = gx[y0:y1, x0 + m - 1:x1 - m - 1].mean(axis=0)
                k = int(prof.argmax())
                best = (prof[k] / (np.median(prof) + 1e-3), "x", x0 + m + k)
            if y1 - y0 > 2 * m:
                prof = gy[y0 + m - 1:y1 - m - 1, x0:x1].mean(axis=1)
                k = int(prof.argmax())
                cand = (prof[k] / (np.median(prof) + 1e-3), "y", y0 + m + k)
                best = cand if best is None or cand[0] > best[0] else best
        if best and best[0] > 1.6:
            _, axis, c = best
            if axis == "x":
                cut(x0, y0, c, y1, d - 1)
                cut(c, y0, x1, y1, d - 1)
            else:
                cut(x0, y0, x1, c, d - 1)
                cut(x0, c, x1, y1, d - 1)
            return
        out[y0:y1, x0:x1] = (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))

    cut(0, 0, W, H, depth)
    Image.fromarray(out).save(dst)


def main():
    manifest = {"license": "CC0 (Poly Haven)", "hdri": {}, "textures": {}}
    for name, res in HDRIS.items():
        f = json.loads(_get(f"https://api.polyhaven.com/files/{name}"))["hdri"][res]["hdr"]
        p = os.path.join(OUT, "hdri", f"{name}_{res}.hdr")
        print(name, _save(f["url"], f["md5"], p))
        manifest["hdri"][name] = os.path.relpath(p, ROOT)
    for name, res in TEXTURES.items():
        files = json.loads(_get(f"https://api.polyhaven.com/files/{name}"))
        maps = {}
        for key, short in MAPS.items():
            if key not in files:
                continue
            f = files[key][res]["jpg"]
            p = os.path.join(OUT, "tex", name, f"{name}_{short}_{res}.jpg")
            print(name, short, _save(f["url"], f["md5"], p))
            maps[short] = os.path.relpath(p, ROOT)
        manifest["textures"][name] = maps
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    import urllib.parse
    dies = {}
    ddir = os.path.join(os.path.dirname(OUT), "dies")
    os.makedirs(ddir, exist_ok=True)
    for name, title in DIES.items():
        q = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo"
             "&iiprop=url|extmetadata&iiurlwidth=4096&iiextmetadatafilter=LicenseShortName|Artist&titles="
             + urllib.parse.quote(title))
        ii = list(json.loads(_get(q))["query"]["pages"].values())[0]["imageinfo"][0]
        lic = ii["extmetadata"]["LicenseShortName"]["value"]
        if lic != "CC0":
            raise RuntimeError(f"{title}: license {lic}, expected CC0")
        p = os.path.join(ddir, name + ".jpg")
        if not os.path.exists(p):
            open(p, "wb").write(_get(ii.get("thumburl") or ii["url"]))
        dies[name] = {"file": os.path.relpath(p, ROOT), "license": lic, "page": ii["descriptionurl"]}
        rp = os.path.join(ddir, name + "_regions.png")
        if not os.path.exists(rp):
            try:
                region_map(p, rp)
            except ImportError:                         # this Python has no Pillow: python3 can do it later
                print("  (region map skipped: no Pillow)")
        print(name, lic)
    json.dump(dies, open(os.path.join(ddir, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    print("ok", OUT)


if __name__ == "__main__":
    main()
