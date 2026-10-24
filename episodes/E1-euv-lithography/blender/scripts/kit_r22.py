"""Round 22 (P1, R22_ROOT_CAUSE row 5): named-part background kit. Owned by cuth; others import it READ-ONLY.

R21 review: "B5_01 和 C_03 用的是同一面模块墙…每镜至少 8 种、不同镜之间不同". The illuminator bay back wall
(x -4.25..-0.75, z 1.55..4.3, plate y 1.075) is built once by build_cutaway_r2._interior_fill for every r2_cutaway
variant, so B5_01 (illum) and C_03 (tour) showed the same wall. rebuild_wall() runs in a shot's post hook: it deletes
the merged wall islands (R8Kit* meshes, every island fully behind y > front_y inside the bay) and builds a new wall
from a per-shot SELECTION of >= 8 nameable part kinds with a per-shot SEED, plus extra named parts that are not
wall blocks (interferometer head on a post, coolant run with clamps).
"""
import bpy
from mathutils import Vector

import hero_kit_r10 as H
import hero_kit_r11 as H11
import hero_kit_r12 as H12

# kind -> (builder, fit class); every builder named by what it is
ALL = dict(H12.KINDS12)
NAMES = {"turbo_gate": "turbo pump on gate valve", "gate_valve": "gate valve", "ion_pump": "ion getter pump",
         "hexapod_mount": "hexapod", "metrology_ring": "metrology ring", "drag_chain": "cable drag chain",
         "manifold": "coolant manifold", "viewport_stack": "viewport stack", "pump": "roughing pump",
         "gas_panel": "gas panel", "power_supply": "power supply", "card_cage": "card cage",
         "valve_island": "valve island", "bellows_spool": "bellows spool"}
SEL = {
    "B5_01": dict(seed=221, kinds=("turbo_gate", "gate_valve", "ion_pump", "hexapod_mount", "metrology_ring",
                                   "drag_chain", "manifold", "viewport_stack", "bellows_spool")),
    "C_03": dict(seed=322, kinds=("pump", "gas_panel", "power_supply", "card_cage", "valve_island", "ion_pump",
                                  "metrology_ring", "drag_chain", "hexapod_mount")),
}
BAY = (-4.25, -0.75, 1.55, 4.3)      # illuminator bay (build_cutaway_r2._illuminator)
Y_PLATE, FRONT_Y = 1.075, 0.55


def _islands(me):
    par = list(range(len(me.vertices)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b:
            par[a] = b
    g = {}
    for i in range(len(me.vertices)):
        g.setdefault(f(i), []).append(i)
    return list(g.values())


def clear_wall(bay=BAY, front_y=FRONT_Y, avoid=()):
    import bmesh
    x0, x1, z0, z1 = bay
    nd = 0
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or not ob.name.startswith("R8Kit") or "facet" in ob.name:
            continue
        mw = ob.matrix_world
        me = ob.data
        kill = []
        for isl in _islands(me):
            pts = [mw @ me.vertices[i].co for i in isl]
            if all(p.y > front_y - 0.05 and x0 - 0.02 < p.x < x1 + 0.02 and z0 - 0.02 < p.z < z1 + 0.02 for p in pts):
                c = sum(pts, Vector()) / len(pts)
                if any((c - Vector(a)).length < r for a, r in avoid):
                    continue
                kill += isl
        if kill:
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context="VERTS")
            bm.to_mesh(me)
            bm.free()
            nd += 1
    print("[kit_r22] cleared wall islands in", nd, "objects")


def rebuild_wall(shot, M, keep=(), avoid=()):
    cfg = SEL[shot]
    clear_wall(avoid=avoid)
    kinds = cfg["kinds"]
    kt = {k: ALL[k] for k in kinds}
    ft = {"wide": tuple(k for k in kinds if ALL[k][1] == "wide") + tuple(k for k in kinds if ALL[k][1] == "any"),
          "tall": tuple(k for k in kinds if ALL[k][1] == "tall") + tuple(k for k in kinds if ALL[k][1] == "any"),
          "any": kinds}
    P = H.new_parts()
    x0, x1, z0, z1 = BAY
    log = []
    H11.wall_r11(P, x0 + 0.08, x1 - 0.08, z0 + 0.06, z1 - 0.06, Y_PLATE, seed=cfg["seed"], keep=keep, scale=1.0,
                 depth=1.5, blocks=len(kinds) + 3, log=log, front_y=FRONT_Y, use={}, tone="dark",
                 fallback=kinds[-3:], kinds_tab=kt, fit_tab=ft)
    out = H.finish(P, M, f"Kit22{shot}")
    used = sorted(set(k for k in log if "(" not in k))
    print(f"[kit_r22] {shot} seed {cfg['seed']}: {len(used)} kinds: {[NAMES.get(k, k) for k in used]}")
    return out, used
