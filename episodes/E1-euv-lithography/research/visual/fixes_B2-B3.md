# B2 / B3 修复记录与待他人落实的提案（2026-10-22）

依据：`verify_B2-D.md`、`audit_B2.yaml`、`audit_B3.yaml` 里的未解决项（wrong / unsourced / glitch）。
本轮改的文件：`blender/shots/b2_scenes.py`、`b3_scenes.py`、`mograph/b2.py`、`mograph/b3.py`、`registry.yaml` 中
B2_03 / B3_02 两行。所有改动都只用 sample 单帧（EEVEE，B3_07 / B2_11 另用 Cycles 各抽一两帧）检查过，
**没有整段重渲**：下面“需重渲”列出的镜头，样片都已过期。

## 一、已在代码里修好的（单帧已看过）

| 镜头 | 问题 | 改法 | 看过的帧 |
|---|---|---|---|
| B3_07 | IF 之后完全看不到光束 | LightPath 的 role 是 `rays`，photoreal 风格会把它隐藏；nave() 里改标成 `emitter`，饱和紫 (0.36,0.12,1.0)、强度 2.2，不再冲白 | 1–136 抽 12 帧，EEVEE + Cycles |
| B3_07 | 61–66 帧镜头穿过光阑板（灰屏、黑帧、劈成两半） | 机位改为逐帧关键帧的 3D 曲线：沿光轴直线推进，离轴 0.15，穿过半径 0.25 的孔（孔径未公开，属风格化），不碰板；第 60 帧后板隐藏（此时已在画外） | 40/46/50/54/58/62 |
| B3_07 | 光路不转折、镜子不亮 | 光束头部按段关键帧：IF→折转镜(30)→场分面镜(74)→光瞳分面镜(98)→掩模(116)；每面镜子在光到达时由一盏只照它的紫色聚光灯点亮；投影物镜和掩模台隐藏（无光的杂物）；结尾 3/4 侧视整条照明光路 | 76/96/116/136 |
| B3_05 | F2 跳约 190 px | 机位改为与 B3_04 蓝图完全对位：侧视，焦点① 602 px、焦点② 1318 px、光轴比中线低 20 px（51.2 px/单位，镜头 35 mm，距离 36.5） | 1，与 B3_04 第 195 帧对比 |
| B3_05 | 收集镜轮廓在脉冲之间几乎看不见；光线堆成静止扇面 | after_style 给收集镜计量青描边（强度 3）；每次脉冲是一圈沿 焦点①→镜面→焦点② 飞行的短光段（start 跟随 end），6 次加速脉冲，最后一次在约 79 帧汇入焦点②；两焦点发光体不再降到 0（不会出现黑点） | 1/6/10/14/17/30/45/60/70/84 |
| B3_01 | 13–34 帧冲白；第 1 帧灰色大光晕 | 改为 3 次爆发，每次 300 条短光段组成的球壳向外飞（start 跟随 end）；机位从 5.3 拉到 11（原来 2.2）；核心改成偏紫、强度 9 | 1/8/13/20/28/34/60/100/141 |
| B3_06 | 焦点①无等离子体 | 加饱和紫的发光核（r 0.38）和体积光晕 | 1/60/95 |
| B3_06 | 颈部和扫描仪机身间 1.6 的空隙 | 机身中心改到 x=38.4，正面与颈部末端 x=14.4 齐平；加对接法兰环和面板缝 | 120/160/213 |
| B3_06 | 灰底灰线，机身看不见 | after_style 给机身换“烟灰玻璃”材质（正面半透明深灰、掠射处亮），扁平倒角；光线穿过 IF 后继续发散进入机身 | 120/160/213 |
| B3_06 | 机位 | 先停在焦点①（第一句），再沿光轴到焦点②（第二句），最后升起拉远看对接（第三句） | 同上 |
| B3_03 | 无“示意”；标签远离弧线 | 标题改为“到两个焦点的距离之和处处相等（比例示意）”；“收集镜的镜面（中心留孔给激光）”放在弧线上端镜缘旁 | 1080p 第 30/70 帧 |
| B3_04 | 实线镜面弧消失 | 先画 B3_03 同一段实线弧（含中心孔），虚线椭圆降到 40 % | 1080p 第 60/120/195 帧 |
| B3_04 | “法线”压在焦点①上、22 px | 法线改为虚线，只在第一根光线标“法线”，28 px，放在镜面外侧；前三根光线画虚线法线 | 同上 |
| B3_04 | 没有角度标记 | 第一根光线上画入射角、反射角两段弧，各标 θ（30 px） | 1080p 第 80 帧局部 |
| B3_04 | 147–195 帧光晕吞掉焦点① | 末段颜色改为饱和 EUV 紫 (128,84,255)，glow 增益 1+0.35（原 1+1）；焦点标签画在光线之上并垫蓝底；画内标题改成分镜 overlay 的短句“从一个焦点出发 → 必经另一个焦点”，不再逐字重复字幕 | 195 |
| B3_02 | 第 121 帧镜旁银色薄片 | registry `step: 0.8`：121 帧覆盖模拟 1–97，薄片（模拟 106 帧出现）和预脉冲前沿都不进画 | 1/110/121 |
| B2_02 | 结尾只有空的幽灵腔体 | air() 里加收集镜、紫色光线（第二句开始画出，66–100 帧）、IF 光阑、等离子体核、三个抽气口（不透明，类型位置未公开，已有“示意”标签） | 1/30/62/100/156 |
| B2_02 | 空气管里的光发白 | 改为不透明的紫色表面光束（浅色 xray 背景上体积发光只会变白），入口最亮、约 2.2 单位内衰减完；空气分子改为深色实点 | 30/62 |
| B2_02 | 前半句腔体挡在管子后面 | 机位改为俯视管子（腔体在画外），再拉远升高到全景，死光的管子留在前景作对比 | 1/30/62/156 |
| B2_04 / B2_06 | 轨迹不消退，堆成静止星芒 | 每条轨迹是一段飞行的短光段（bevel_factor_start 跟在 end 后 4–6 帧），一直有新离子飞来（-10–140 帧开始） | 1/40/90/130 |
| B2_04 | 收集镜轮廓看不见 | after_style 给收集镜计量青描边（强度 6） | 同上 |
| B2_04 | 价态颜色编码反了 | 统一一种暖色，亮度随价态升高（1.6 + 0.6q），线宽统一 | 同上 |
| B2_06 | H₂ 静止 | 900 个氢分子缓慢向远离镜面的方向漂移（Fomenkov 2017 slide 34） | 同上 |
| B2_05 | 来袭原子被上边缘切掉 | 机位拉远（距离 17→15，镜头 100），表面以上约占画面 1/3，原子从 z=2.2 落下 | 1/30/60/113 |
| B2_05 | 注入的原子看不见 | 所有原子都放在截面上（y = 前表面），注入的原子在截面里可见；膜层加宽到 7 | 60/113 |
| B2_07 | 看不到镜面；离子半个出画 | 镜面移到 x=-1.55（离子停在 -1.19），画成淡青色薄面 + 亮青色边框；机位结束于同时框住离子和镜面；尾迹只保留最近一段，随减速变短 | 1/20/50/70/84 |
| B2_09 | V 形折线；抽气口只露一个小块 | 气流改成经过 5 个控制点的 NURBS 平滑曲线（order 4），灰蓝色、较粗，一直在流动（第 1 帧已在流，结尾仍在流）；三个抽气口（法兰管 + 泵壳）完整在画内；腔内也画出收集镜和紫色光路 | 1/36/72 |
| B2_10 | 刻度 20 px、注释 22 px | 刻度只标两端“0.01 Pa”“1 atm”，28 px；“（示意）”28 px；压力表上移到 cy=845，避开字幕带 | 1080p 第 120 帧 |
| B2_11 | 辉光是等粗的管子 | 每段光路一个圆台：两端半径取光束在该处的截面（镜面上约为镜半径的 0.7，在 IF、中间像、晶圆处收成一点），外加 1.7 倍的淡光晕；颜色饱和紫，强度 0.28（“淡淡的”） | EEVEE 60/151，Cycles 100 |
| B2_03 | 第 1 帧薄片比激光孔大 | registry `start: 191`：开场就是橙色主脉冲击中薄片（薄片只在前 2 帧出现），随后闪白 | 1/2/4 |

另：b2_scenes 注释里的“50,000 times a second”改为 60,000（F2）。

## 二、需要别人落实的提案

### 1. b1_source.py（B2_03 / B2_12 的淡紫冲白，另一个 agent 正在改这个文件）

查实冲白的主因**不是**等离子体云，而是 `S.euv_cone()` 那个 EUV 光锥替身：它是从镜缘到 IF 的发光体积
（sample_b1 第 239 行，模拟 254 帧起 emission 0.02），正好挡在 B2_03 / B2_12 的机位和镜面之间，把整个镜面罩成一片淡紫。
下面这段在临时脚本里对 B2_03 第 100/149 帧、B2_12 第 3/5/11/60 帧验证过（EEVEE）：B2_03 镜面恢复深色、等离子体和激光孔清楚；
B2_12 每次脉冲光锥亮一下再暗，能看出节拍。建议加进 `b1_source.py`，并在 `after_style` 里
`elif shot_id in ("B2_03", "B2_12"): _calm_plasma(shot_id)`：

```python
def _scale_keys(fcurves, pred, k, after):
    for fc in fcurves:
        if not pred(fc):
            continue
        for kp in fc.keyframe_points:
            if kp.co[0] >= after:
                kp.co[1] *= k
                kp.handle_left[1] *= k
                kp.handle_right[1] *= k
        fc.update()


def _calm_plasma(shot_id):
    """B2_03 / B2_12: the EUV-bundle stand-in (an emissive volume from the collector rim to the IF, 0.02 from sim
    254) lies between these cameras and the mirror and veiled the whole face in flat lavender. B2_03 drops it; B2_12
    keeps it faint and lets every (slow-motion) pulse brighten it once. The persistent plasma cloud and its light are
    also turned down after the flash so the mirror and droplets read."""
    import common as C
    import materials as M
    T = B.T_MAIN
    if shot_id == "B2_03" and bpy.data.objects.get("EUVCone"):
        bpy.data.objects["EUVCone"].hide_render = True
    vol = bpy.data.materials.get("PlasmaVol")
    if vol and vol.node_tree.animation_data and vol.node_tree.animation_data.action:
        _scale_keys(C.fcurves(vol.node_tree.animation_data.action), lambda fc: "EmissionScale" in fc.data_path,
                    0.3, T + 20)
    lt = bpy.data.objects.get("PlasmaLight")
    if lt and lt.data.animation_data and lt.data.animation_data.action:
        _scale_keys(C.fcurves(lt.data.animation_data.action), lambda fc: fc.data_path == "energy", 0.25, T + 20)
    if shot_id == "B2_12":
        cone = bpy.data.materials.get("EUVConeMat")
        core = bpy.data.materials.get("PlasmaCoreMat")
        if cone:
            cone.node_tree.animation_data_clear()
            for f0 in range(264, 347, 14):
                for f, e in ((f0, 0.0025), (f0 + 2, 0.011), (f0 + 10, 0.0025)):
                    M.set_volume_strength(cone, f, emission_strength=e, density=0.0)
        if core:
            for f0 in range(264, 347, 14):
                for f, e in ((f0, 4.0), (f0 + 1, 40.0), (f0 + 8, 4.0)):
                    M.set_emission_strength(core, f, e)
```

仍未解决（需要 b1_source 的人看）：B2_12 的锡滴流在画面里只是几粒小点（审计 glitch“droplets hardly visible”）——
需要机位更靠近锡滴线或给锡滴加一盏掠射灯；B2_01 的 EUV 光锥同样是这个 0.02 的体积，建议按下面的分镜文字删掉“光锥”，
不要再加亮它（加亮就会重现冲白）。

### 2. 分镜文字（`storyboard/parts/p2_B2-B6.yaml`，改完重跑 merge / retime）

- **B3_05 overlay**（wrong，F2）：`每秒最多 5 万次爆炸 → 汇进同一个点` → `每秒 6 万次 → 汇进同一个点（示意）`（facts F2、F56）。
  visual 末句改为“……随后连续几次脉冲，每一圈光都精确地汇进同一点”。
- **B3_06 overlays** 加 `at:`，让三条各随旁白出现（edit_film.labels_for 支持）：
  `焦点① · 等离子体（示意）` at 0.4；`焦点② · 中间焦点（IF）（示意）` at 3.3；`光源 ┃ 扫描仪（示意）` at 5.5；删掉单独的 `示意` 条。
- **B3_07 visual**：→ “穿过中间焦点的小孔，紫色光束在折转镜、场分面镜、光瞳分面镜上依次转折，一路通向掩模（示意）”；
  builders 去掉 `build_optics.mirror_blank`，改为 `build_machine.machine`。
- **B3_02 visual**：→ “巨大的凹面镜在暗腔中淡入，镜面平整明亮，中心留着激光孔；锡滴流从镜前横穿而过”；fx 去掉 `thin_film_iridescence`；style_why 去掉“虹彩镀膜”。
- **B3_04 visual**：“每根在镜面上标出入射角与反射角（虚线法线）” → “前几根标出虚线法线，第一根标出相等的入射角和反射角 θ”。
- **B3_03 overlays** 可加 `示意`（画内标题已写“比例示意”）。
- **B2_01 visual**：→ “主脉冲的闪白刚褪去，收集镜平整的镜面在暗腔中被等离子体照亮；前景里几粒尚在发光的锡碎屑缓缓飘散”；builders 去掉 `build_source.euv_cone`。
- **B2_02 visual**：“扫描光带横扫，画面变成……” → “镜头从空气管拉远升起，露出透明剖视的光源腔：鼓形腔体收窄成锥形颈部通向中间焦点，腔壁上有几个抽气口（示意），紫色光路从收集镜汇向中间焦点”（片中没有做镜头中途的扫描光带）。
- **B2_03 overlays**：建议加 `示意（非比例）`（开场 2 帧里薄片比激光孔还大，继承自 B1 的非比例模拟）。
- **B2_04 visual**：“按价态（1 到 8 价）由亮到暗分色” → “同一种暖色，价态越高越亮”；“每次撞击迸出一个小火花”可保留（artistic）。
- **B2_05 overlay**：`沉积 · 注入 · 溅射（示意 · 顶层为保护层）` → `沉积 · 注入 · 溅射（示意 · 原子放大 · 顶层为保护层）`；
  visual 删掉“角落一只小小的反射率指针一路下滑”（没有做；`反射率 ↓` 标签已表达），或由 edit 加 2D 指针。
- **B2_06 visual**：→ “从显微截面倒拉回 B2_04 同一机位；腔内铺开一层淡青色氢分子（小哑铃状 H₂），缓缓向远离镜面的方向流动；同样的离子轨迹钻进薄雾后保持直线、变短、由亮转暗橙，在碰到镜面之前一根根熄灭”。
- **B2_07 visual**：→ “一颗锡离子几乎直线前进，每撞一颗氢分子闪一下青光、把它撞飞、自己慢下来一截、尾迹缩短，最后停在镜面前一个身位处，慢慢黯淡”。
- **B2_08 visual**：没有做 EUV 闪光和 H₂ 哑铃劈开（不在本轮清单内）。二选一：改文字为“发亮的氢自由基从上方落到镜面那层锡原子上，四个一组扣住一颗锡……”，或在 `b2_scenes.clean()` 里补做。
- **B2_09 visual**：→ “透明剖视的光源腔，紫色光路从收集镜汇向中间焦点；一缕缕灰色的锡烷气流从镜面附近沿腔壁流进几个抽气口（位置示意）”。
- **B2_11 visual**：→ “光一开，沿光路浮起一层淡紫色的氢等离子体辉光：在镜面上铺开、在焦点处收细，只要曝光在进行就一直亮着”；builders 改为 `build_machine.machine`。
- **B2_12 visual** 保留“每一次脉冲都让光锥亮一下再暗下去”的前提是采纳上面的 b1_source 提案；否则删掉这句。

### 3. 审计表（`audit_B2.yaml` / `audit_B3.yaml`，由核查的人更新）

- B3_07 `aperture plate radius / hole` 一条：孔半径改为 0.25（风格化，IF 光阑尺寸未公开），仍是 artistic。
- B2_11 新增 simplified：辉光圆台的截面半径是示意（取镜半径的约 0.7，焦点处收成一点）。
- B2_02 / B2_09 的抽气口：三个，位于鼓形腔体后部，类型、数量、位置未公开，已有“示意”标签。
- B3_06：光线穿过 IF 后继续发散进入扫描仪机身（示意）；机身为通用外壳（artistic，不仿 ASML 外观）。

## 三、需重渲的镜头（样片均已过期）

B2_02、B2_03（registry start 191；若采纳 b1_source 提案再渲）、B2_04、B2_05、B2_06、B2_07、B2_08（共用 multilayer()，
膜宽 6→7，单帧看过无异常）、B2_09、B2_10、B2_11、B2_12（等 b1_source 提案）、B3_01、B3_02（registry step 0.8）、
B3_03、B3_04、B3_05、B3_06、B3_07。
