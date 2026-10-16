# FACTS.md — 光刻机动画事实核查表
> 核查日期：2026-10-15。规则：只有「✅ 已核」可以写进旁白；「⚠️ 有分歧」要按备注里的写法表述；「❌ 未能核实」不得使用。
> 来源分级：A = ASML / ZEISS / TRUMPF 官方页面；B = 同行评审论文、会议论文；C = 媒体报道。

| # | 说法 | 核实结果 | 等级 | 来源 |
|---|---|---|---|---|
| 1 | EUV 波长 13.5 nm | ✅ 13.5 nm，比 DUV（193 nm）短 14 倍以上 | A | https://www.asml.com/en/technology/lithography-principles/light-and-lasers |
| 2 | 每秒约 5 万个锡滴 | ✅ 每秒 50,000 次（ASML：每秒最多 50,000 次） | A | 同上；https://www.asml.com/en/products/euv-lithography-systems ；https://www.trumpf.com/en_US/solutions/applications/euv-lithography/euv-drive-laser/ |
| 3 | 锡滴尺寸、速度 | ✅ 直径约 25 微米，喷出速度 70 米/秒 | A | ASML light-and-lasers 页面 |
| 4 | 每个锡滴被打两次 | ✅ 先用低强度预脉冲把锡滴压成“煎饼”，再用强主脉冲把它汽化成等离子体 | A | ASML light-and-lasers 页面；TRUMPF 页面 |
| 4b | 压扁后的尺寸、脉冲能量 | ✅ 被压成直径约 300 μm 的薄盘；预脉冲约几十 mJ，主脉冲约 500 mJ（这是 ASML S2 光源的实验条件） | B | Torretti 等，J. Phys. D 2020，https://doi.org/10.1088/1361-6463/ab56d4 |
| 4c | 下一代光源 | ✅ 每秒 10 万个锡滴，每滴打三次；属于研发中的规划（2026 年 2 月报道），**不是现役机器** | C | https://www.heise.de/en/news/EUV-Lithography-ASML-will-shoot-tin-droplets-300-000-times-per-second-11187649.html |
| 5 | 等离子体温度 | ⚠️ 有分歧。ZEISS 说“将近 22 万摄氏度，几乎是太阳表面平均温度的 40 倍”；ASML 说“比太阳表面热 40 倍”；MIT Tech Review 引用 ASML 人员的说法是“约 50 万 K”；论文测得等效电子温度 30 到 40 eV。**旁白采用用户决定：“约 50 万开尔文”，并注明出自 ASML 相关人员对媒体的表述（MIT Tech Review）。ZEISS 的“约 22 万 ℃ / 约太阳表面 40 倍”作为对照保留在本表。** | A/B/C | https://www.zeiss.com/semiconductor-manufacturing-technology/inspiring-technology/euv-lithography.html ；https://www.asml.com/en/company/stories/2022/making-euv-lab-to-fab ；https://ir.arcnl.nl/pub/80/00090OA.pdf |
| 6 | CO₂ 驱动激光功率 | ⚠️ TRUMPF 写 40 kW，并说放大倍数超过 1 万倍；ZEISS 写 30 kW。**建议写“几十千瓦”。** | A | TRUMPF 页面；ZEISS 页面 |
| 7 | 反射镜数量 | ✅ 投影物镜有 6 面反射镜（ZEISS）。⚠️ 整机总数没有官方数字：MIT Tech Review 说约 11 面，euvlitho 2024 会议的示意图写“10 面加掩模加收集镜”。**旁白只用“投影物镜 6 面”。** | A / C | ZEISS 页面；https://www.technologyreview.com/2021/10/27/1037118/moores-law-computer-chips/ |
| 8 | 多层膜和反射率 | ✅ 钼和硅交替镀膜，最多约 100 层，每层只有几纳米厚。单层只能反射约 1%，多层叠加后反射率最高约 70% | A | ZEISS 页面 |
| 9 | 镜面精度的比喻 | ✅ “把镜子放大到德国那么大，最高的凸起只有 0.1 毫米” | A | ZEISS 页面 |
| 9b | 指向精度的比喻 | ✅ “用这面镜子把激光打到月球上，能命中一个乒乓球” | A | ZEISS 页面 |
| 10 | 必须在真空里 | ✅ EUV 会被所有东西吸收，连空气也不例外，所以从光源到晶圆的整条光路都在高真空中 | A | https://www.asml.com/en/products/euv-lithography-systems |
| 11 | 缩小 4 倍 | ✅ NXE 把掩模图形缩小 4 倍 | A | 同上 |
| 12 | High-NA 的变形缩放 | ✅ NA 0.55，非扫描方向缩小 4 倍、扫描方向缩小 8 倍，分辨率 8 nm | A/B | ZEISS 在 euvlitho 2023 的报告 https://euvlitho.com/2023/P21.pdf ；ASML 产品页 |
| 13 | NXE 分辨率 | ✅ NA 0.33，分辨率 13 nm | A | ASML 产品页 |
| 14 | 掩模是反射式的 | ✅ 掩模本身就是多层反射镜 | A | ASML 产品页 |
| 15 | 工件台精度 | ✅ 每次曝光把晶圆定位到四分之一纳米以内，每秒检查调整 2 万次 | A | ASML 产品页（Wafer stage 一节） |
| 15b | 掩模台加速度 | ⚠️ 只有媒体来源：MIT Tech Review 说“32 倍重力加速度”“比战斗机加速还快”。可以用，但要标明是报道。 | C | MIT Tech Review |
| 15c | “两架飞机对准一根针”的比喻 | ❌ 找不到一手出处。**删掉，改用第 15 条或第 9b 条。** | — | — |
| 16 | 整机重量 | ❌ 没找到 ASML 官方数字。媒体说约 180 吨（NXE:3400），早期 NXE:3100 约 50 吨（IEEE Spectrum） | C | https://spectrum.ieee.org/euvs-underdog-light-source-will-have-its-day |
| 17 | 运输方式 | ❌ 各说法互相矛盾：MIT Tech Review 说要 4 架 747；其他报道说 3 架 747、40 个集装箱、20 辆卡车。**脚本里不用。** | C | MIT Tech Review；Laser Focus World |
| 18 | 零件数量 | ⚠️ 只有媒体来源：约 10 万个零件、3000 根线缆、4 万颗螺栓、2 公里软管。ZEISS 官方的分项数字：照明系统 15,000 个零件、重 1.5 吨；投影物镜约 20,000 个零件、重 2 吨 | A/C | ZEISS 页面；MIT Tech Review |
| 19 | 芯片上的晶体管数量 | ✅ ZEISS：“比指尖略大的面积上有 1840 亿个元件”。“数十亿个晶体管”是 ASML 的笼统说法 | A | ZEISS 页面；ASML 产品页 |
| 20 | 研发投入 | ✅ ASML 说 17 年里投入超过 60 亿欧元；第一台 High-NA 于 2023 年 12 月交付 | A | ASML 产品页 |
