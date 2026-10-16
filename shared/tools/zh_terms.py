"""Chinese display names for storyboard codes (transitions, engines, camera moves, effects).
The storyboard keeps the English codes because tools read them; pages show these names."""
import re

TRANSITIONS = {
    "cut": "硬切", "fade": "淡入", "dissolve": "叠化", "match-cut": "匹配剪辑",
    "scan-wipe": "扫描光带转场", "fade-to-energy": "淡出只剩能量", "zoom-through": "穿越变焦",
    "push-through": "推镜穿越", "line-draw-materialize": "线稿实体化", "whip": "甩镜", "flash": "闪白",
}

ENGINES = {"cycles": "Cycles 光线追踪", "eevee": "EEVEE 实时渲染", "manim": "Manim 二维动画",
           "pillow": "后期合成图层"}

# camera moves are free text; translate word by word (longest phrases first)
CAMERA_WORDS = [
    ("whip pans between vignettes", "在小场景间甩镜"), ("impact shake then slow pull-out", "冲击震动后缓慢拉远"),
    ("follow then pull-out", "跟随后拉远"), ("static with slight push", "固定机位轻微推进"),
    ("truck alongside jet", "与喷气机并行横移"), ("side track along beam", "沿光束侧向跟移"),
    ("arc around converging beam", "绕汇聚光束弧形运动"), ("tracking dolly along chain", "沿放大链跟移"),
    ("push along light path", "沿光路推进"), ("lateral track with stream", "随锡滴流横向跟移"),
    ("track along machine", "沿整机跟移"), ("drone-track overhead", "航拍式俯视跟移"),
    ("accelerating crane-up", "加速升臂"), ("continuous-flythrough", "连续穿越"), ("continuous", "连续"),
    ("powers-of-ten", "十的幂次缩放"), ("fall-with-photon", "随光子下落"), ("track-then-descend", "跟移后下降"),
    ("pull-back-crane", "拉远升臂"), ("crane-pull-back", "升臂拉远"), ("pull-back-pan", "拉远并横摇"),
    ("pull-back reveal", "拉远揭示"), ("rapid-pull-back", "快速拉远"), ("slow-pull-back", "缓慢拉远"),
    ("pull-back", "拉远"), ("pull-out", "拉远"), ("push-in then hold", "推进后停住"), ("push-in", "推进"),
    ("push-through", "推镜穿越"), ("zoom-through", "穿越变焦"), ("fly-through", "穿越飞行"),
    ("scale-zoom-out", "尺度拉远"), ("scale-zoom", "尺度缩放"), ("crash-zoom", "急推变焦"),
    ("rack-focus", "移焦"), ("dolly-in", "推轨推进"), ("follow-dolly", "跟随推轨"), ("dolly", "推轨"),
    ("crane-up", "升臂"), ("crane-down", "降臂"), ("tilt-up", "上仰"), ("tilt-down", "下俯"),
    ("truck-right", "向右横移"), ("slide-rotate", "滑动并旋转"), ("orbit-slowmo", "慢动作环绕"),
    ("orbit-in", "环绕推进"), ("arc-to-front", "弧形绕到正面"), ("handheld-micro", "微幅手持"),
    ("static-shake", "固定机位加震动"), ("static-split", "固定分屏"), ("static-3q", "固定三分之四侧角"),
    ("locked-ortho", "锁定正交视角"), ("locked-off", "锁定机位"), ("orthographic", "正交视角"),
    ("macro-inserts", "微距插入镜头"), ("top-down", "俯视"), ("low-angle", "低角度"), ("low-glide", "低空滑行"),
    ("grazing", "贴面掠过"), ("whip-follow", "甩镜跟随"), ("2d-", "二维"), ("lateral", "横向"),
    ("side", "侧向"), ("slow", "缓慢"), ("macro", "微距"), ("orbit", "环绕"), ("track", "跟移"),
    ("truck", "横移"), ("static", "固定"), ("push", "推进"), ("pan-right", "右摇"), ("pan-left", "左摇"),
    ("pan", "横摇"), ("zoom", "变焦"), ("arc", "弧形运动"), ("drift", "漂移"), ("slide", "滑动"),
    ("descend", "下降"), ("follow", "跟随"), ("hold", "停住"), ("then", "后"), ("with", "带"),
]

FX = {
    "absorption_fade": "吸收衰减", "additive_blend": "叠加混合", "afterglow": "余辉", "ambient_occlusion": "环境光遮蔽",
    "beam_attenuation": "光束逐级变暗", "beam_glow": "光束辉光", "beam_volume": "体积光束", "bloom": "泛光",
    "blur_on_unresolved": "未分辨处模糊", "bokeh_background": "背景光斑", "camera_shake": "镜头震动",
    "camera_shake_hard": "强烈震动", "camera_shake_light": "轻微震动", "caustics": "焦散",
    "charging_glow": "蓄能辉光", "chromatic_dispersion": "色散", "color_bleed_to_violet": "颜色渗向紫色",
    "counter": "计数器", "counter_roll": "数字滚动", "cut_to_black": "切黑", "debris_particles": "碎屑粒子",
    "defocus_blur": "离焦模糊", "deposition_particles": "沉积粒子", "depth_fog": "景深雾",
    "depth_of_field": "景深", "diffraction_iridescence": "衍射虹彩", "dimension_draw_on": "尺寸线逐笔画出",
    "dimension_lines": "尺寸标注线", "dof": "景深", "drop_settle": "落下归位", "edge_smooth_morph": "边缘平滑变形",
    "emission_heat": "发热发光", "euv_flash": "EUV 闪光", "explode_stagger": "依次爆炸拆解",
    "exploded_view": "爆炸图", "facet_flip": "分面镜翻转", "film_grain": "胶片颗粒", "flare": "光晕",
    "flash_frame": "闪帧", "flash_white": "闪白", "flat_motion": "扁平动效", "flicker": "闪烁",
    "fluid_coalescence": "液滴合并", "freestyle_lines": "线稿描边", "gas_flow_particles": "气流粒子",
    "ghost_glass": "幽灵玻璃", "ghost_glass_fresnel": "菲涅尔幽灵玻璃", "glow": "辉光", "glow_core": "核心辉光",
    "glow_pulse": "辉光脉动", "glow_text": "发光文字", "glow_tip": "尖端辉光", "hatch_fill": "剖面线填充",
    "headlight_bloom": "车灯泛光", "heartbeat_pulse": "心跳式脉动", "heat_glow": "热辉光", "heat_shimmer": "热浪扭曲",
    "height_morph": "高度变形", "hidden_line_dashes": "隐藏线虚线", "highlight_pulse": "高亮脉动",
    "hud_glow": "HUD 辉光", "hud_markers": "HUD 标记", "hud_overlay": "HUD 叠加层", "impact_sparks": "冲击火花",
    "instanced_curves": "实例化曲线", "instanced_parts": "实例化零件", "interference_fringes": "干涉条纹",
    "interference_ripple": "干涉波纹", "iridescent_diffraction": "虹彩衍射", "latent_image_paint": "潜像显现",
    "led_bokeh": "指示灯光斑", "led_flicker": "指示灯闪烁", "lens_breathing": "镜头呼吸", "light_leak": "漏光",
    "light_sweep": "扫光", "light_trails": "光轨", "light_wake_up": "灯光渐亮", "light_wrap": "光线包裹",
    "line_draw": "线稿描画", "line_draw_on": "线稿逐笔画出", "material_grow_transition": "材质生长转场",
    "meter_drop": "计量条下降", "molecule_assembly": "分子组装", "morph": "形变", "mosaic_morph": "马赛克变形",
    "motion_blur": "运动模糊", "motion_trail": "运动拖尾", "motion_trails": "运动拖尾", "page_close": "翻页合上",
    "particle_arcs": "粒子弧线", "particle_glow": "粒子辉光", "particle_shatter": "粒子碎裂",
    "particle_streaks": "粒子拖影", "particle_trails": "粒子轨迹", "particle_waterfall": "粒子瀑布",
    "particles": "粒子", "path_glow": "路径辉光", "picture_in_picture": "画中画", "point_scan": "逐点扫描",
    "poisson_heatmap": "泊松分布热图", "pulse_rhythm": "脉冲节奏", "resist_fluid": "光刻胶流体", "rim_light": "轮廓光",
    "ripple_modifier": "波纹形变", "ripple_splash": "波纹飞溅", "ruler_glow": "标尺辉光", "scale_jump": "尺度跳跃",
    "scale_zoom": "尺度缩放", "scan_band": "扫描光带", "scan_band_style_morph": "扫描光带切换风格",
    "scanline": "扫描线", "scanlines": "扫描线", "sem_noise": "电镜噪点", "shallow_dof": "浅景深",
    "shockwave_ripple": "冲击波纹", "skin_sss": "皮肤次表面散射", "snap_align": "吸附对齐", "specular_glints": "高光闪点",
    "speed_lines": "速度线", "speed_ramp": "变速", "star_field": "星空", "stress_wave_shader": "应力波着色",
    "strike_through": "划掉", "strobe": "频闪", "strobe_accelerate": "频闪加速", "strobe_fill": "频闪填满",
    "structure_fade_to_energy": "结构淡出只剩能量", "sync_flash": "同步闪光", "thin_film_flash": "薄膜闪光",
    "thin_film_iridescence": "薄膜虹彩", "timelapse_blur": "延时模糊", "vignette": "暗角",
    "volumetric_beam": "体积光束", "volumetric_cone": "体积光锥", "volumetric_glow": "体积辉光",
    "volumetric_haze": "体积雾", "volumetric_light": "体积光", "volumetric_plasma": "体积等离子体",
    "warning_pulse": "警示脉动", "wave_animation": "波动动画", "wave_shader": "波动着色",
    "wet_floor_reflection": "湿地面反射", "wet_ground_reflection": "湿地面反射", "zoom_inset": "放大插图",
}


def camera_zh(move):
    if not move:
        return ""
    s = str(move)
    for en, zh in CAMERA_WORDS:
        s = re.sub(re.escape(en), zh, s, flags=re.I)
    return s.replace("-", "").replace("  ", " ").strip()


def fx_zh(code):
    return FX.get(code, code.replace("_", " "))
