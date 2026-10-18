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
            "corrugated_iron": "1k"}
MAPS = {"Diffuse": "diff", "Rough": "rough", "nor_gl": "nor_gl", "Metal": "metal"}


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
    print("ok", OUT)


if __name__ == "__main__":
    main()
