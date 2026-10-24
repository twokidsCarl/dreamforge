"""Round 22 (P1) hook for B7_06 / A0_10 / B8_03 / B8_03M (R22_ROOT_CAUSE row(s) 1 / 4 / 5 / 6). Owned by the cutb sub-agent.

Called by the scene module's build(): pre(variant, shot, module) before the build, post(sc, variant, shot) after it.
Each shot's change is gated by ON (remove a shot id -> exact R21 pixels).
"""
import math

ON = {"B7_06", "B8_03", "B8_03M"}   # A0_10 (cut_2b_r22_title) tried, Q4 no -> off


def pre(variant, shot, mod):
    if shot not in ON:
        return
    if shot == "B7_06":
        import cut_2b_r22_po as P
        P.pre(mod)


def post(sc, variant, shot):
    if shot not in ON:
        return
    if shot == "B7_06":
        import cut_2b_r22_po as P
        P.post(sc)
    elif shot == "A0_10":
        import cut_2b_r22_title as T
        T.post(sc)
    elif shot in ("B8_03", "B8_03M"):
        import cut_2b_r22_scan as S
        S.post(sc, shot)
