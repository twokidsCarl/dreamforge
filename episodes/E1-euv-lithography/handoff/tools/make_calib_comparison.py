"""calib_vs_roundN_comparison.jpg: each Carl pick (reference, left) next to the matching new round-N frame
(right), two pairs per row, for Carl to accept directly.
  python3 make_calib_comparison.py --refs /workspace/e1work/p1/refs --frames /workspace/e1work/p1/round2 \
      --out /workspace/e1work/p1/round2/calib_vs_round2_comparison.jpg [--round 2]"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../shared/tools"))
from overlay_labels import font  # noqa: E402

PAIRS = [  # (pick, ref file, shot, frame, what)
    ("1C", "k1C_title_white_serif_machine_person.jpg", "A0_10", 119, "片名卡：白衬线短句 + 整机全景 + 人做尺度"),
    ("2A", "k2A_studio_white_product_lighting.jpg", "B7_06", 79, "白色棚拍布光与留白（不仿外观）"),
    ("2B", "k2B_cg_cutaway_violet_path_modules.jpg", "B5_01", 64, "去壳剖视 · 紫光贯穿模块（极细致）"),
    ("2B", "k2B_cg_cutaway_violet_path_modules.jpg", "C_03", 222, "一镜到底：收集镜 → IF → 照明 → 掩模"),
    ("3A", "k3A_cg_metal_source_chamber_plasma.jpg", "A0_01", 246, "写实金属腔 + 紫色等离子"),
    ("3A", "k3A_cg_metal_source_chamber_plasma.jpg", "B3_02", 103, "收集镜 + 中心孔 + 激光入射"),
    ("3D", "k3D_mock_plasma_illustration_micro.png", "B1_10", 69, "机理放大框（预脉冲拍扁锡滴）"),
    ("4A", "k4A_cg_mirror_mounts_violet_bounce.jpg", "B8_03", 92, "紫光在金属镜座间折返 · 反射式掩模"),
    ("4D", "k4D_tem_mosi_multilayer_40pairs.png", "B4_07", 122, "约 40 对 Mo/Si 电镜截面"),
    ("5A", "k5A_real_pellicle_gloved_hands.jpg", "B6_12", 80, "真实薄膜质感的 pellicle + 间隙"),
    ("6C", "k6C_cg_chip_interconnect_layers.jpg", "B8_17", 122, "真实晶圆 + 曝光场"),
    ("6D", "k6D_mock_wafer_circular_magnifier.png", "B9_05", 59, "晶圆 + 圆形放大框（1 nm² 光子计数）"),
    ("7A", "k7A_3d_objects_same_space_scale.jpg", "B4_10", 89, "3D 实物同屏：地球 / 月球 / 高尔夫球"),
    ("8A", "k8A_night_freighter_nose_loading.jpg", "A0_02", 78, "夜间货机开鼻装货 · 钠灯"),
    ("8C", "k8C_cold_white_cleanroom_tools.jpg", "D_07", 85, "冷白光洁净室 · 设备排开"),
    ("9A", "k9A_bunnysuit_pair_walking.jpg", "D_07", 131, "洁净服两人中景（背影，无脸）"),
    ("9B", "k9B_person_beside_machine_scale.jpg", "B7_06", 122, "人站在机器旁做尺度（剪影）"),
]


def fit(im, w, h, bg=(14, 16, 22)):
    im = im.convert("RGB")
    im.thumbnail((w, h), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", default="2")
    a = ap.parse_args()
    tw, th, cap, gap = 560, 315, 44, 18
    per_row = 2
    rows = (len(PAIRS) + per_row - 1) // per_row
    pw = 2 * tw + 8
    W = per_row * pw + (per_row + 1) * gap
    head = 110
    H = head + rows * (th + cap + gap) + gap
    sheet = Image.new("RGB", (W, H), (10, 12, 18))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 24), f"E1 · Carl 点选参考（左） vs P1 第 {a.round} 轮新帧（右）", font=font(40), fill=(236, 238, 244))
    d.text((gap, 74), "1C 2A+B 3A+D 4A+D 5A 6C+D 7A 8A+C 9A+B · 参考图仅供内部比对，版权归原作者；新帧为 960×540 样片",
           font=font(22), fill=(150, 160, 182))
    for i, (pick, ref, sid, f, what) in enumerate(PAIRS):
        r, c = divmod(i, per_row)
        x = gap + c * (pw + gap)
        y = head + r * (th + cap + gap)
        rp = os.path.join(a.refs, ref)
        fp = os.path.join(a.frames, f"{sid}_{f:04d}.png")
        left = fit(Image.open(rp), tw, th) if os.path.exists(rp) else Image.new("RGB", (tw, th), (40, 0, 0))
        right = fit(Image.open(fp), tw, th) if os.path.exists(fp) else Image.new("RGB", (tw, th), (40, 0, 0))
        sheet.paste(left, (x, y + cap))
        sheet.paste(right, (x + tw + 8, y + cap))
        d.rounded_rectangle((x, y + 4, x + 58, y + 38), radius=6, fill=(138, 92, 255))
        d.text((x + 29, y + 21), pick, font=font(24), fill=(255, 255, 255), anchor="mm")
        d.text((x + 70, y + 8), f"{what}", font=font(22), fill=(236, 238, 244))
        d.text((x + tw + 8 + tw - 4, y + 10), f"R{a.round} · {sid} f{f}", font=font(20), fill=(63, 214, 224), anchor="ra")
    sheet.save(a.out, quality=88)
    print("wrote", a.out, sheet.size)


if __name__ == "__main__":
    main()
