"""Anatomical C57 mouse eye anchors — mid-cheek orbit via UV-dark cluster.
Rejects neck/shoulder luminance heuristic AND near-ear forehead creases.
"""
from __future__ import annotations
import numpy as np


def place_c57_eyes(co, ynose, sgn, x_mid, imp_z, v_lum=None, v_pink=None):
    co = np.asarray(co, dtype=np.float32)
    dist_nose = np.abs(co[:, 1] - float(ynose))
    x_mid = float(x_mid); imp_z = float(imp_z); sgn = float(sgn)

    if v_pink is not None:
        is_ear = (
            (co[:, 2] > (imp_z - 0.002)) & (dist_nose > 0.12) & (dist_nose < 0.25)
            & (np.abs(co[:, 0] - x_mid) > 0.045) & (v_pink > 0.095)
        )
        ear_d = float(np.median(dist_nose[is_ear])) if is_ear.any() else 0.16
    else:
        ear_d = 0.16

    # Orbit ~0.60 along snout→ear (slightly ear-biased avoids "on the snout tip")
    eye_d = 0.02 + 0.60 * (ear_d - 0.02)
    eye_z = imp_z - 0.105          # mid-cheek (~0.24)
    z_lo, z_hi = imp_z - 0.150, imp_z - 0.075
    head_len = max(ear_d, 0.12)
    radius = float(np.clip(0.045 * head_len, 0.0095, 0.0120))

    is_eye = np.zeros(len(co), dtype=bool)
    centers = []
    for esgn in (-1.0, 1.0):
        band = (
            (np.abs(dist_nose - eye_d) < 0.028)
            & (co[:, 2] > z_lo) & (co[:, 2] < z_hi)
            & ((co[:, 0] - x_mid) * esgn > 0.025)
            & (dist_nose > 0.055) & (dist_nose < ear_d - 0.025)
        )
        if v_lum is not None and band.sum() >= 20:
            # Tightest dark cluster inside band (true painted eye), not global darkest
            thr = np.percentile(v_lum[band], 12)
            dark = band & (v_lum <= thr)
            if dark.sum() >= 6:
                # Keep compact cluster around darkest mode
                idx = np.where(dark)[0]
                # seed = darkest vert
                seed = idx[np.argmin(v_lum[idx])]
                d = np.linalg.norm(co[idx] - co[seed], axis=1)
                keep = idx[d <= np.percentile(d, 55)]
                is_eye[keep] = True
                ctr = co[keep].mean(axis=0).astype(np.float32)
            else:
                idx = np.where(band)[0]
                lat = (co[idx, 0] - x_mid) * esgn
                keep = idx[lat >= np.percentile(lat, 50)]
                is_eye[keep] = True
                ctr = co[keep].mean(axis=0).astype(np.float32)
        elif band.any():
            idx = np.where(band)[0]
            lat = (co[idx, 0] - x_mid) * esgn
            keep = idx[lat >= np.percentile(lat, 50)]
            is_eye[keep] = True
            ctr = co[keep].mean(axis=0).astype(np.float32)
        else:
            eye_y = float(ynose) + sgn * eye_d
            ctr = np.array([x_mid + esgn * 0.058, eye_y, eye_z], dtype=np.float32)
            d = np.linalg.norm(co - ctr[None, :], axis=1)
            near = (d < radius * 1.5) & (co[:, 2] > z_lo) & (co[:, 2] < z_hi)
            is_eye[near] = True

        # Mild outward push only (0.3R) — less "floating bead / ghost highlight"
        n_out = np.array([esgn, -0.10 * sgn, 0.02], dtype=np.float32)
        n_out /= max(float(np.linalg.norm(n_out)), 1e-6)
        ctr = ctr + n_out * (0.30 * radius)
        centers.append((esgn, ctr))
    return is_eye, centers, radius


def apply_eye_fur_gap(w, co, centers, radius):
    w = np.asarray(w, dtype=np.float32).copy()
    gap = max(radius * 1.55, 0.016)
    soft = max(radius * 0.65, 0.007)
    for _, ctr in centers:
        d = np.linalg.norm(co - ctr[None, :], axis=1)
        w *= np.clip((d - gap) / soft, 0.0, 1.0).astype(np.float32)
    return w
