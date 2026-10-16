"""Style board: the B1 source scene from outside the vessel, rendered in the four visual
languages (styles.py). Uses sample_b1's simulation; frame 230 = plasma burning."""
import build_source as S
import build_vacuum as V
import sample_b1

CUTS = [("CamStyle", 230, 230)]


def build():
    sc = sample_b1.build()
    V.source_vessel()
    S.light_rays()
    sample_b1._camera("CamStyle", [
        (1, (4.0, -1.5, 0.0), (44.0, 38.0, 24.0), 30, 11.0),
    ])
    return sc
