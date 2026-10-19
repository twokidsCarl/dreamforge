# First High-NA shipment (EXE:5000 → Intel Hillsboro) and ASML supplier map

Researched 2026-10-19. Confidence tags:
- **[H] high**: stated outright by Intel or ASML (newsroom, annual report, SEC filing, official X post or YouTube video), or plainly visible in official footage.
- **[M] medium**: a secondary outlet quoting ASML staff, or an identification made from official footage plus third-party registries.
- **[L] low**: inferred. These are marked as inferences.

Local copies. `L = /Users/adam429/Desktop/project-2026/dreamforge/episodes/E1-euv-lithography/renders/review/refs/logistics`
- `L/asml_x_20231221_first_highna_shipment.jpg`: ASML's X photo from Veldhoven.
- `L/intel_x_20240104_hillsboro_delivery.jpg`: Intel's X photo from Hillsboro.
- `L/video/intel_3PCtf1ONYMU.mp4`: Intel YouTube, "Intel Receives ASML's First High NA EUV system", 57 s, uploaded 2024-03-01. Key frames are in `L/video/frames/intel_t*.jpg`.
- `L/video/intel_WHmRj2mZ-dk.mp4` plus `.en-GB.vtt` (official captions): Intel YouTube, "Intel Adds ASML's First High NA EUV Tool to Oregon Factory", 3:50, uploaded 2024-04-18. Key frames are in `L/video/frames_w/w_t*.jpg`.
- `L/intel_highna_zip/`: Intel's April 2024 press-image ZIP. All five images are installed-tool and clean-room shots. **None show the shipment.**
- `L/asml_ar/`: ASML Annual Report 2025 and 2024 as filed with the SEC (6-K EX-99.1 HTML), plus page images `ar2025_p239.jpg`, `ar2024_p289.jpg` and `ar2024_p005.jpg`.

---

## Part A. The first High-NA shipment

### A1. Official numbers, route and dates

**Numbers (Intel)**
- [H] Intel newsroom, 18 Apr 2024, "With High NA EUV, Intel Foundry Opens New Frontier in Chipmaking": *"The TWINSCAN EXE:5000 system was transported to Oregon in more than 250 crates inside 43 freight containers. These were loaded onto multiple cargo planes that landed in Seattle. They were then transferred to 20 trucks for the drive to Oregon."* The same page says: *"The total weight of each new system is more than 150 metric tons."* It also calls it *"The 165-ton High NA EUV tool"* (photo caption).
  https://www.intel.com/content/www/us/en/newsroom/news/intel-foundry-opens-new-frontier-chipmaking.html (live on 2026-10-19).
- [H] Intel video WHmRj2mZ-dk, narration (official en-GB captions, 0:12 to 0:21): *"To get it from ASML's headquarters in The Netherlands to Intel's Gordon Moore Park in Oregon took more than 250 crates in 43 freight containers loaded in multiple cargo planes and 20 semi-trucks."* On-screen supers read "250 | crates", "43 | containers", "Cargo | planes" and "20 | semi-trucks". https://www.youtube.com/watch?v=WHmRj2mZ-dk
- **Planes: no official count.** Intel says only "multiple cargo planes". [M] For a High-NA system in general, CNBC (22 May 2025, Katie Tarasov) quotes ASML High NA qualification team lead Assia Haddou: *"Haddou said it takes seven partially loaded Boeing 747s, or at least 25 trucks, to get one system to a customer."* https://www.cnbc.com/2025/05/22/exclusive-look-at-high-na-asmls-new-400-million-chipmaking-colossus.html (read via the Wayback copy; cnbc.com returns 403 to bots). This is a general statement, not a count for the Intel flight.
- **Conflicting "13 containers" figure.** [M] Reuters, 21 Dec 2023, as found in syndicated copies: *"being shipped in 250 separate crates, including 13 large containers."* AnandTech, 21 Dec 2023 (the page is now dead and redirects to its forum; read via Wayback): *"requires 13 truck-sized containers and 250 crates."* [L] One reading reconciles the two: the 13 large ASML "shipment boxes" (see A3) count among the 250+ crates, while Intel's 43 counts the freight containers they were packed into. That is an inference. **Neither company has explained the difference.** On screen, use Intel's 250+ / 43 / 20.

**Dates**
- [H] ASML on X, 21 Dec 2023, 15:16 UTC: *"A decade of groundbreaking science and systems engineering deserves a bow! 🎀 We're excited and proud to ship our first High NA EUV system to @intel. ✈️🌎"* https://x.com/ASMLcompany/status/1737854448876257672
- [H] ASML Q4 2023 results press release, 24 Jan 2024 (SEC 6-K EX-99.1), CEO Peter Wennink: *"We shipped the first modules of the first High NA EUV system, EXE:5000, to a customer before the end of the year."* https://www.sec.gov/Archives/edgar/data/937966/000093796624000003/pressreleasequarterlyresul.htm
- [H] ASML story "5 things you should know about High NA EUV lithography" (2024): *"ASML shipped the first modules of the first High NA EUV lithography system to Intel"* (December 2023). https://www.asml.com/en/news/stories/2024/5-things-high-na-euv
- [H] Intel on X, 4 Jan 2024: *"The best way to start the year. 🎊 Intel Oregon welcomes major components of @ASMLcompany's first shipped High-NA EUV technology…"* In the attached photo the banner reads *"World's 1st EUV High NA system delivery — Hillsboro, January 2024"*. https://x.com/intelnews/status/1743046633506427165
- [H] Intel, 18 Apr 2024: *"Installation is complete and calibration started … in a clean room at Intel Corporation's Fab D1X in Hillsboro, Oregon, in April 2024."*
- [H] ASML Annual Report 2024, p.21: *"Two more TWINSCAN EXE:5000 systems were assembled and installed at an Intel plant near Hillsboro, Oregon (US), and a fourth system was shipped to a customer in Asia."* This means Intel had two EXE:5000s by the end of 2024.
- Note: ASML and Intel both describe the shipment as going out in batches. ASML says "first modules … before the end of the year" and Intel says "major components" in January. **No official text gives the date of the last batch.**

**Route**
- [H] Veldhoven (ASML HQ) → cargo planes → **Seattle** → 20 trucks → Hillsboro (Intel Gordon Moore Park / Fab D1X). The source is Intel's text above.
- **Departure airport: not stated in any official text.** [L] Clues in official footage, which are inferences only:
  - In the Intel video WHmRj2mZ-dk, the "Cargo planes" shot (0:17 to 0:19, daylight) shows the crate on a nose-door highloader stencilled *"…air CARGO"* and *"MAX 35T"*. This is consistent with Luxair Cargo, the handler at Luxembourg-Findel, the Cargolux hub.
  - The "43 containers" shot (0:16) shows a truck leaving a cargo-terminal gate with a *"RUTGES CARGO"* sign. Rutges is a Dutch air-cargo road-feeder company.
  - None of this names Schiphol or Luxembourg. **Treat the departure airport as not public.**
- [L] Arrival airport cross-check: in Intel video 3PCtf1ONYMU (0:11), a night apron with a Cargolux 747 has a runway sign reading **"34R-16L"** behind it. Seattle-Tacoma has a 16L/34R runway. Portland (PDX) runways are 10/28 and 03/21, so the shot cannot be PDX. This fits Intel's "landed in Seattle". **Tom's Hardware (4 Mar 2024) wrote "to Portland, Oregon"; that contradicts Intel, so do not use it.**

### A2. Aircraft, operator, loading method and official footage

**Aircraft and airline: Cargolux Boeing 747 freighters**, identified from Intel's own videos. Intel and ASML have never named the airline in text.
- [H] (visible) In video 3PCtf1ONYMU (0:05 to 0:08), a Cargolux-liveried 747 taxis in at night: red tail with the white cube logo, "cargolux" titles with a small "DSV" beneath them. Two marshallers in hi-vis vests stand in front of it.
  - [M] The nose-gear door reads **"VCH"**. Third-party registries (airport-data.com, planefinder, FlightAware) list **LX-VCH as a Boeing 747-8R7F (747-8F), "City of Dudelange"**. The engines at 0:11 have the GEnx spiral spinner, consistent with a 747-8F.
- [H] (visible) In video WHmRj2mZ-dk ("Cargo planes", 0:17 to 0:19, daylight, low sun), a Cargolux 747 sits with its **nose door raised**. An ASML box is on a scissor highloader level with the main-deck nose opening, and two workers stand on the highloader's operator platform.
  - [M] The fuselage registration reads **"LX-YCV"**, which third-party registries list as a **Boeing 747-4R7F (747-400F)**. [L] This daylight shot may come from a different leg or batch, or even a different ASML shipment. Intel does not say.
- **Loading method: NOSE-LOADED.** [H] (visible) Both Intel videos show ASML boxes going through the 747F **nose cargo door** via a scissor highloader. In 3PCtf1ONYMU (0:13 to 0:20) the box sits on the main-deck roller floor just behind the open nose door, with the hinged nose-door frame in the foreground and a **Swissport** loader/vehicle outside. Another shot shows the box on the highloader platform at the raised nose, with the "cargolux" logo on the underside of the nose cone. No side-door loading of ASML boxes appears in any official footage. Whether every crate was nose-loaded is **not public**.
- **Freight forwarder: DSV** [H] (visible): the "DSV" logo is on the Cargolux 747's fuselage under the titles, on the hi-vis vests of the ground crew around the box at the arrival airport, on the netted/wrapped air-cargo pallets in the "250 crates" shot, and on the rear of the US flatbed trailer ("DSV 1006"). **No Intel, ASML, DSV or Cargolux press text names DSV or Cargolux**; my searches found none.
- **Ground handling**: Swissport-branded loader and vehicles at the night apron [H visible]. "…air CARGO" highloader in the daylight shot [M].

**Shot-by-shot description of the official footage**

Video 1, Intel "Intel Receives ASML's First High NA EUV system" (3PCtf1ONYMU, 57 s, 2024-03-01). The YouTube description says *"Intel Oregon welcomes the delivery of a key component of ASML's first TWINSCAN EXE:5000 system"*. No narration.
- 0:01 to 0:05, drone shot over ASML Veldhoven on an overcast, wet day. One white ASML shipment box tied with a red ribbon and bow sits on a **teal low-bed semitrailer** (a teal flatbed with grey ramp/loading sections at the rear). The tractor is a **European cab-over in teal with magenta/pink stripes**. A cluster of staff cheers at the rear of the trailer. The truck pulls out, with a white van leading and a dark car following. No police escort is visible.
- 0:05 to 0:08, the Cargolux 747 (LX-VCH) taxis at night with marshallers. Then a "High NA EUV is here." title card.
- 0:11, ground crew in Cargolux/Swissport hi-vis vests at the bottom of the aircraft stairs under the wing, with the two inboard GEnx engines behind them and the 34R-16L sign in the distance.
- 0:13 to 0:20, the box inside the main deck at the nose door. Its end face reads **"MZA 10005 ASML"** above a large blue **ASML** logo. Split screen: the box on the nose highloader; two DSV-vested men beside the box on a trailer; a long flatbed waiting on the apron with other freighters behind.
- 0:21 to 0:22, night apron. The box rides on a **multi-axle blue/purple US flatbed** (three axles visible at the rear) pulled by a white US conventional tractor, with people in hi-vis standing beside it. The box is roughly 1.5 to 2 times the height of the people standing on the ground, and its length about equals the trailer deck. These ratios are a visual estimate.
- 0:22 to 0:23, Hillsboro, grey rainy day, wet car park, portable toilets and blue construction fencing. A white long-nose US tractor with a blue **DSV flatbed, rear number "1006"**, three rear axles. The red ribbon and bow are back on the box. One worker walks alongside. No escort vehicles are visible.
- 0:24 to 0:25, at a dock, both end doors of the box are swung open to an indoor bay. Inside, the module is wrapped in **pinkish-copper translucent barrier foil** on a metal skid that runs on the box's built-in rails. Workers wear orange hi-vis vests and white hard hats.
- 0:25 to 0:31, the foil-wrapped module (**silver foil printed with repeated "ASML"**) is rolled on a low skid into the sub-fab/clean area. Workers handle hoses connected to the skid; [L] this is consistent with air-caster movement. Then clean-room bunny suits.
- 0:31 to 0:50, overhead crane hook labelled **"WLL 10,000 KG"**; a module frame labelled "SOURCE SIDE"; time-lapse of the frame being assembled in the clean room.

Video 2, Intel "Intel Adds ASML's First High NA EUV Tool to Oregon Factory" (WHmRj2mZ-dk, 3:50, 2024-04-18), presented by Rob Kelton.
- 0:14 to 0:15, the **"250 crates"** shot. In a DSV air-cargo warehouse, tall loads of **light-brown wooden/cardboard-faced crates printed "ASML"** are stretch-wrapped in clear film, strapped with red straps and covered by black **cargo nets** on air-cargo pallets on a roller deck. Large blue-on-white "DSV" placards are on the wrap, a worker in orange hi-vis stands at a yellow control console, and a "ZONE DGR TEMPORAIRE" sign is in French. [L] French-language signage fits Luxembourg (French is an official language there); this is an inference.
- 0:16, the **"43 containers"** shot. **Two white ASML shipment boxes** in tandem on one flatbed, pulled by the same teal/magenta cab-over tractor, pass under a steel-truss canopy at a cargo-terminal gate with a "RUTGES CARGO" sign behind.
- 0:17 to 0:19, the **"Cargo planes"** shot. The box (end text **"RZY 10001 ASML"** or similar, hard to read) rides on a scissor highloader at the raised nose of Cargolux 747 LX-YCV, in daylight.
- 0:19 to 0:21, the **"20 semi-trucks"** shot. The Hillsboro DSV flatbed with the bowed box, the same as in video 1.
- 0:30 to 0:35, the foil-wrapped module on a skid in the clean room; a wide hall with several pink-foil-wrapped modules.

### A3. What the crates, boxes and trucks look like

**The large ASML "shipment boxes"** (ASML's own alt text calls one *"an ASML shipment box"*)
- [H visible] **Shape:** a long box with **bevelled ("gabled") top edges**. The roof is a flat centre strip with two angled panels, so the end profile is an elongated hexagon, which suits the 747F nose/main-deck contour. Panels are divided into three to four bays by **bright aluminium extrusions/corner posts**, and diamond-shaped aluminium gussets sit where the posts meet the base rail.
- **Material and colour:** white panels in a riveted aluminium frame; a silver aluminium base frame with a row of tie-down/fork points.
- **Graphics:** a light-grey dotted **world-map** pattern over the side panels; a blue **ASML** logo; the slogan *"Driving microchip advancement around the world"*; a box ID stencilled in navy on the side and end, e.g. **"MZA 10005 ASML"** (the box at Veldhoven, on the plane and at Hillsboro) and "RZY 10001 ASML" (the daylight plane shot).
- **End face** (3PCtf1ONYMU, 0:13): a white panel carrying four small recessed windows/ports in a row (two look like indicator/gauge windows, two like recessed hardware or fittings). A lockable hatch is labelled *"MANUALS INSIDE / BATTERY INSIDE"* (small print, best reading). Small print near the bottom reads "PLACE DOLLY HERE", and a placard top-left reads "ASML … 3 CRS…". The other end has **full-height double doors** with recessed latches, shown open at the Intel dock.
- **Size:** roughly as long as a 40-ft flatbed deck. Two boxes fit in tandem on one European trailer in the "43 containers" shot, and one large box fills a US flatbed. Height is a little more than one storey. **Exact dimensions, weight and internal climate control are not public.** The "BATTERY INSIDE" hatch and the windows suggest on-board monitoring or logging, but that is an inference [L].
- **How many of the 250+ crates are these big boxes?** Not public. [M] Reuters' "13 large containers" may be this count.

**The ordinary crates** [H visible, WHmRj2mZ-dk 0:14]: light-brown, wooden or cardboard-faced, printed with "ASML"; stacked on air-cargo pallets (ULD pallets), stretch-wrapped in clear film, strapped with red straps and covered with black cargo nets, with DSV placards. Whether they are plywood, cardboard or something else cannot be told from the footage. **Not public.**

**Inside the boxes** [H visible]: modules are wrapped in metallised barrier foil, either pinkish-copper or silver printed with repeated "ASML", and sit on rail-mounted skids that slide out of the box's end doors.

**Trucks**
- Netherlands leg [H visible]: a European cab-over tractor in teal with magenta/pink stripes pulling a teal low-bed/flatbed semitrailer, with no logo readable in the footage. The haulier is **not public**.
- US leg [H visible]: a white US conventional (long-nose) tractor pulling a blue **DSV** flatbed with three rear axles (rear number "1006"). Whether the trailers had air-ride suspension, and whether there was a police or pilot escort, is **not public**. No escort vehicle appears in any official shot.

**Reusable transport materials** [H] ASML Annual Report 2025, p.191: *"Shipping our lithography systems requires substantial packaging and transportation materials."* … *"Valuable transportation materials – such as packaging, locking and plug materials – are used to safely transport our modules and systems, either from our suppliers to our factories or from our factories to our customers."* p.164: *"transport materials used for system shipments returned to Veldhoven resulted in approximately 9 kt CO2e savings."* This implies the boxes are returned and reused.

### A4. ASML's general description of how EUV systems ship

- [H] ASML story "Busting ASML myths" (Jessica Timings, 23 Feb 2022): *"We spent 20 years developing EUV with our partners and suppliers, resulting in a machine that contains around 100,000 parts. To ship just one of these huge machines to customers requires 40 freight containers, three cargo planes and 20 trucks."* **The URL https://www.asml.com/news/stories/2022/busting-asml-myths now returns 404.** Text verified from the Wayback Machine snapshot (2023) of /en/news/stories/2022/busting-asml-myths.
- [H] Intel newsroom, "EUV: The Most Precise, Complex Machine at Intel" ("Behind this Door" video, 21 Dec 2021): *"Delivering just one of these tools to D1X takes three Boeing 747 cargo planes, 40 freight containers and 20 trucks. The school bus-sized machine comprises 100,000 parts and weighs nearly 200 tons."* **The URL https://www.intel.com/content/www/us/en/newsroom/news/euv-most-precise-complex-machine.html now 404s** (it redirects to Intel's 404 handler). Verified from the Wayback snapshot of 2023-02-17. The video is still on YouTube: https://www.youtube.com/watch?v=Jv40Viz-KTc. These figures are for **NXE (0.33 NA)**, not High-NA.
- [M] High-NA (CNBC 2025, Haddou): *"seven partially loaded Boeing 747s, or at least 25 trucks."* Also: *"The machine is made up of four modules, manufactured in Connecticut, California, Germany and the Netherlands, then assembled in the Veldhoven, Netherlands, lab for testing and approval, before being disassembled again to ship out."*
- [H] ASML "5 things…High NA" (2024): *"EXE systems are made up of modules that can be independently tested before being integrated into a complete system,"* and *"the modules streamline the system's installation and integration into a customer fab."*
- [H] ASML Annual Report 2025, p.68: *"Historically, we shipped systems by air, but have recently begun using ocean freight for some deliveries."* p.164: the air-to-ocean project covers mature DUV and metrology systems (*"For DUV, the shipment of 17 full systems…"*). **EUV and High-NA are not mentioned as going by sea.**
- **Time to install:**
  - [H] Intel's own dates: arrival in January 2024 ("Hillsboro, January 2024"), then assembly complete and calibration started in April 2024. That is about 3 to 4 months to mechanical completion; calibration then continued.
  - [M] Tom's Hardware (4 Mar 2024) wrote *"it will take 250 ASML and Intel engineers about six months to install the machine completely"*. **I could not find this in any Intel or ASML text, so do not use it.**
  - ASML's official general install time for EXE is **not public**.
- Other dead links: Intel's 2022 release "Intel and ASML Strengthen their Collaboration…" (intel.com/…/intel-asml-strengthen-collaboration.html) now 404s, and the Jan 2024 Intel X post still links to it. The Intel High-NA press kit (newsroom.intel.com/press-kit/intel-high-na-euv) redirects to a 404. The AnandTech article (anandtech.com/show/21194) redirects to forums.anandtech.com.

---

## Part B. ASML suppliers: real regional split for the 5,100-dot map

### B1. Annual Report 2025 (FY2025, published 25 Feb 2026). Primary source

Source: SEC 6-K EX-99.1 https://www.sec.gov/Archives/edgar/data/937966/000162828026011377/asml-2025xannualxreportx.htm. Page numbers are the report's own; the SEC slide numbers match them. Page image: `L/asml_ar/ar2025_p239.jpg`.

- [H] p.4 and p.41: *"5,100 Total number of suppliers"* (p.41 adds *"2024: 5,150"*).
- [H] **p.239, "Responsible value chain: Responsible supply chain", map titled "ASML suppliers"** with bars for *"Suppliers split by % spend"* and *"Suppliers split by number"*:

| Region (ASML's label) | % of spend | Number of suppliers | Share of 5,100 |
|---|---|---|---|
| The Netherlands | 34% | 1,600 | 31.4% |
| EMEA (excluding The Netherlands) | 47% | 700 | 13.7% |
| North America | 12% | 1,350 | 26.5% |
| Asia | 7% | 1,450 | 28.4% |
| **Total** | 100% (€16.2bn) | **5,100** | 100% |

  The four counts add up to exactly 5,100. I paired each figure with its region by reading the page image, because the SEC text layer lists the labels and numbers out of order.
- [H] Same page: *"€16.2bn Total"* spend, split *"Product-related spend 72%"* and *"Non-product-related spend 28%"*. Supplier base: *"Product-related suppliers 900"* and *"Non-product-related suppliers 4,200"*. *"272 business-critical suppliers generate 89% of product-related spend"* and *"153 business-critical suppliers generate 19% of non-product-related spend"*.
- [H] p.239 text: *"Our supply chain (see diagram) covers our three main regions: EMEA, North America and Asia."*
- **Map note:** ASML's own map draws the Netherlands bars over Western Europe and the EMEA bar over Central Europe. **ASML publishes no country, city or coordinate breakdown below these four regions.** Dots inside each region must be placed illustratively.
  - Dot counts: NL 1,600 / rest of EMEA 700 / North America 1,350 / Asia 1,450.
  - Spend weighting: NL 34%, EMEA 47%, NA 12%, Asia 7%.
  - The two rankings differ: the rest of EMEA has the fewest suppliers but the largest spend (ZEISS is in Germany), while Asia has many suppliers but only 7% of spend.
- [M] CNBC 2025 (in the same paragraph as an interview with ASML's Benschop) writes *"With about 800 global suppliers, tariff implications for ASML are complex."* That figure fits the ~900 product-related suppliers, not the 5,100 total. **Do not mix the two.**

### B2. Annual Report 2024 (FY2024), for comparison

Source: SEC 6-K EX-99.1 https://www.sec.gov/Archives/edgar/data/937966/000093796625000011/a2024annualreportbasedon.htm. Page images: `L/asml_ar/ar2024_p289.jpg` and `ar2024_p005.jpg`.
- [H] p.5: *"5,150 Total suppliers 1,600 in the Netherlands 750 in EMEA (excl. NL) 1,400 in North America 1,400 in Asia"*. p.284 gives the same figures.
- [H] p.289 donut chart: *"Supplier base geographic split by percent spend"*: 39% The Netherlands, 41% EMEA (excl. The Netherlands), 13% North America, 7% Asia. Total *"€16.0bn Total spend"*; 72% product-related and 28% non-product-related; *"250 suppliers … 90% of this spend"* (business-critical, product-related) and *"161 suppliers … 21% of this spend"* (non-product-related).

### B3. Where the named key suppliers and ASML's own module sites are

- [H] **ZEISS (Carl Zeiss SMT): Oberkochen and Wetzlar, Germany.** ASML AR 2025, p.319: *"Carl Zeiss SMT GmbH is our single supplier, and we are their single customer, of optical columns for lithography systems. Carl Zeiss SMT GmbH is capable of developing and producing these items only in limited numbers and only through the use of manufacturing and testing facilities in Oberkochen and Wetzlar, Germany."* p.68: *"Carl Zeiss SMT, our sole supplier of lenses, mirrors, illuminators, collectors and other critical optical components."* p.322: *"Carl Zeiss SMT Holding GmbH & Co. KG (24.9%) Germany (Oberkochen)"* (an ASML associate).
- [H] **Cymer (San Diego), Berliner Glas (Berlin) and Wilton (Connecticut) are ASML's own sites, not outside suppliers.** AR 2025, p.68: *"All of our manufacturing activities, including subassembly, final assembly and system testing, take place in (cleanroom) facilities in Veldhoven, Eindhoven, Oirschot (the Netherlands), Berlin (Germany), Wilton, San Diego (US), Pyeongtaek (South Korea) and Linkou and Tainan (Taiwan)."* AR 2025, p.109 calls San Diego *"the lithography light source center of excellence"* (Cymer). On the map they should be drawn as ASML sites, distinct from supplier dots.
- [M] **TRUMPF: Ditzingen, Germany** (the CO2 drive laser for the EUV source). The TRUMPF release "ASML honors TRUMPF for new EUV laser" is datelined *"Veldhoven/Ditzingen, October 24, 2025"* and describes a new EUV high-energy laser with *"more than 450,000 individual parts"* and *"a weight of over 20 tons"*. https://www.trumpf.com/en_INT/newsroom/global-press-releases/press-release-detail-page/release/asml-honors-trumpf-for-new-euv-laser-9838/ That release does not explicitly name the production site. Trade press (2017) reported a TRUMPF EUV-laser facility at the Ditzingen HQ. TRUMPF's 2017 release on buying Access Laser (Everett, WA) says the low-power CO2 seed lasers work "together with TRUMPF laser amplifiers in EUV systems". ASML's annual report does not name TRUMPF.
- [L/M] **VDL ETG** (Eindhoven, plus Almelo and Switzerland per VDL news): a long-time ASML module supplier. **No ASML annual-report mention, and I found no current official VDL statement of which EUV modules it builds.** VDL's "builds complex frames for Zeiss" news page no longer shows the text. Treat as "not public" for specific modules.
- [M] CNBC 2025: the four High-NA modules are made in *"Connecticut, California, Germany and the Netherlands"*. [L] This most likely maps to Wilton (reticle/wafer stage area), San Diego (source), Oberkochen (ZEISS optics) and Veldhoven, but **ASML has not published which module comes from which site.**

---

## What is NOT public (searched for, not found)

1. The exact number of cargo flights for the Intel EXE:5000 shipment. Intel says only "multiple"; the "seven partially loaded 747s" is a general High-NA statement to CNBC.
2. The departure airport (Schiphol? Luxembourg?) and the flight dates or numbers. Footage clues point to Luxembourg (Luxair Cargo highloader, Cargolux aircraft) but nothing official.
3. Any official naming of **Cargolux** or **DSV**. They appear only as logos in Intel's footage, with no press release from Intel, ASML, Cargolux or DSV.
4. Exact dimensions, weight, material spec and climate or shock control of the white ASML shipment boxes, and how many of the 250+ crates are these big boxes rather than ordinary crates.
5. Material of the ordinary crates (plywood or cardboard), and the type of the "43 freight containers" (air ULDs or ISO containers).
6. The Dutch haulier, trailer suspension (air-ride) and any escort. No escort appears in official footage.
7. Why Reuters and AnandTech reported "13 containers" while Intel reported 43. Neither company has explained it.
8. ASML's official installation duration for an EXE system. The "250 engineers, ~6 months" figure is Tom's Hardware only.
9. Any supplier breakdown finer than the four regions (country, city or coordinates). The count of suppliers per country is not published.
10. Which High-NA module is made at which site, beyond CNBC's state/country list.
