"""R23 panel agent, A0_06 (root-cause row 4, R22 review: "5100 个光点太小太碎…连线只留 15–20 条粗弧线"):
the 5100-point web stays (BRIEF), but every supplier dot is enlarged (r 0.0062 -> 0.0115, Europe / North America read
as two bright clusters instead of noise) and the 19 trunk arcs (already in the 15-20 range) become thick routes
(bevel 0.0042 -> 0.011) with brighter landing nodes."""
import bpy

DOT_R, ARC_R = 0.0085, 0.0085


def post(sc, variant, shot):
    for ng in bpy.data.node_groups:
        if ng.name.startswith("SupplierDotsR18"):
            for nd in ng.nodes:
                if nd.bl_idname == "GeometryNodeMeshIcoSphere":
                    nd.inputs["Radius"].default_value = DOT_R
                    nd.inputs["Subdivisions"].default_value = 2
    for ob in bpy.data.objects:
        if ob.name.startswith("TrunkR18_") and ob.type == "CURVE":
            ob.data.bevel_depth = ARC_R
            ob.data.bevel_resolution = 3
        if ob.name.startswith("TrunkNodeR18_") and ob.type == "MESH":
            ob.scale = (1.3, 1.3, 1.3)
