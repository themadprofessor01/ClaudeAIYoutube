# Science Fact Sheet: Every Number, Derived

The script uses rounded, deliberately **battery-friendly** numbers, so no informed viewer can say the comparison was rigged. Each claim below shows its inputs, the arithmetic, and caveats. **Run a final fact-check against current primary sources before publishing**, especially for items marked ⚠.

## Core inputs

| Quantity | Value used | Basis |
|---|---|---|
| Jet fuel (Jet A / A-1) specific energy | **≈43 MJ/kg ≈ 11.9 kWh/kg** ("about 12 kWh") | ASTM D1655 minimum 42.8 MJ/kg; typical ≈43.0–43.2 MJ/kg |
| Jet fuel density | **≈0.8 kg/L** → 1 kg ≈ 1.25 L | Spec range ≈0.775–0.840 kg/L at 15 °C |
| Best mainstream Li-ion **cell** specific energy | **≈250 Wh/kg** ("a quarter of a kWh") | High-energy 21700 cells ≈250–270 Wh/kg (≈18 Wh, ≈70 g each). 14 cells ≈ 1 kg ≈ 250 Wh, as in shot S4.2 |
| Li-ion **pack** specific energy (cells + cooling + casing + BMS + wiring) | **≈200 Wh/kg** (generous for aviation) | Automotive packs ≈150–200 Wh/kg; aviation packs need extra fire containment and are often lower |
| Turbofan overall efficiency (fuel energy → useful propulsive work) | **≈35%** ("about a third") | Modern high-bypass turbofans in cruise ≈35–40% |
| Electric drivetrain efficiency (battery → shaft) | **≈90%** | Battery ≈95%, inverter ≈98%, motor ≈95–97% |

## The headline ratios

**Raw energy per kg (S4.4–S4.6):** 11.9 ÷ 0.25 ≈ **48 → "around fifty times."**

**Useful energy per kg (S4.10, "roughly twenty times"):**
- Fuel: 11.9 kWh × 0.35 ≈ **4.2 kWh useful per kg**
- Battery, cell level: 0.25 × 0.9 ≈ 0.225 kWh → ratio ≈ **19×**
- Battery, pack level: 0.20 × 0.9 ≈ 0.18 kWh → ratio ≈ **23×**
- → **"roughly twenty times."**

> **Why "20×" is generous to batteries:** the 35% turbofan figure *includes* propeller/fan (propulsive) losses, while the 90% electric figure stops at the motor shaft, before the fan or propeller's own losses. A strict like-for-like comparison (fuel→shaft at ≈50% core thermal efficiency vs battery→shaft at 90%) gives roughly **25–30×**. We use 20× so the film errs in the battery's favour. If a commenter challenges it, the honest answer is "if anything, the real gap is bigger."

## Section 3 numbers

| Claim | Derivation / basis |
|---|---|
| "Seventy-nine tonnes" | A320neo maximum takeoff weight (MTOW) up to 79 t (depending on weight variant) |
| "~30 s to ~270 km/h" | Typical rotation speed ≈140–150 kt ≈ 260–280 km/h; takeoff roll ≈30–40 s |
| "Fan almost two metres" | CFM LEAP-1A fan diameter 78 in ≈ 1.98 m |
| "Well over a thousand degrees" | Combustor flame temperatures ≈1,700–2,000 °C+; turbine entry ≈1,400–1,600 °C. The script's phrasing is conservative. |
| "Tens of megawatts" at takeoff | Momentum-theory estimate per engine: P ≈ T^1.5 / √(2ρA) with T ≈ 130 kN, A ≈ 3.08 m², ρ = 1.225 → ≈17 MW ideal, ≈20 MW real → **≈35–45 MW for two engines** |
| "Power a small town uses" | 40 MW ÷ ≈1.2 kW average household draw ≈ 30,000 homes. "Small town" is, if anything, an understatement |
| Climb to 11 km (graphic) | Potential energy alone: 75,000 kg × 9.81 × 11,000 m ≈ 8.1 GJ ≈ **2.2 MWh** (excluding drag) |
| "About nineteen tonnes of fuel" | A320neo standard capacity ≈23,860 L × 0.8 ≈ **19 t** (optional extra tanks add more) |
| "Over two hundred megawatt-hours" | 19,000 kg × 11.9 kWh/kg ≈ **226 MWh** of chemical energy |
| "Three thousand EV batteries" | 226 MWh ÷ 75 kWh (typical mid-size EV) ≈ **3,000** |
| "777: more than seven times" | 777-300ER capacity 181,280 L × 0.8 ≈ **145 t** → 145 ÷ 19 ≈ **7.6×** |

## Section 4 numbers

| Claim | Derivation |
|---|---|
| 1 t fuel = "≈1,250 L, a cube a little over a metre" | 1,000 kg ÷ 0.8 = 1,250 L = 1.25 m³ → cube side ∛1.25 ≈ **1.08 m** |
| "About twenty tonnes of batteries" per tonne of fuel | 1 t × 4.2 MWh useful ÷ (0.18–0.225 kWh useful/kg) ≈ **18.5–23 t** |
| "Thirteen cars" | 20 t ÷ ≈1.5 t per car ≈ **13** |
| "777 lands about a hundred tonnes lighter" | 777-300ER MTOW 351.5 t vs max landing weight 251.3 t: a long flight must burn ≈100 t before it may land normally |
| "An empty battery weighs the same as a full one" | Li-ion stores energy by moving lithium ions between electrodes inside a sealed cell; no mass leaves. (E = mc² mass change is ~10⁻¹¹ of cell mass, negligible) |
| Landing weight (extra point, storyboard only) | Because battery aircraft land at takeoff weight, their landing gear and structure must be certified for it, which adds weight. Conventional jets have a lower max landing weight than MTOW for exactly this reason |

## Section 5 numbers (the A320 thought experiment)

| Claim | Derivation |
|---|---|
| "1,000 km flight burns around 4 t" | A320neo ≈2.2–2.5 t/h average plus taxi/climb; ≈1 h 20 min airborne → **≈3.5–4 t** |
| "Reserves… about six tonnes" | Typical: contingency (≈5%) + alternate (≈1 t) + 30-min final reserve hold (≈1.1 t) → ≈2–2.5 t → total **≈6 t** |
| "120 t of batteries" | 6 t × 20 = **120 t** |
| "More than the aircraft is allowed to weigh" | OEW ≈44 t + 120 t = **164 t** vs MTOW 79 t (≈2.1×) |
| Weight spiral | Standard aircraft-sizing feedback ("mass snowball"); for battery aircraft the required mass fraction quickly exceeds 100%, so the sizing loop doesn't converge |
| "Rip out every seat… a short hop" | Battery budget ≈ MTOW − OEW ≈ 35 t → ×0.2 kWh/kg = 7 MWh × ≈80% usable depth of discharge × 0.9 ≈ 5 MWh useful ≈ 1.2 t fuel-equivalent. That's ≈30 min including climb (≈250–300 km) with **no** reserves and **no** passengers. With legal reserves, effectively nothing. (A clean-sheet electric design would do better than this conversion, but not enough for this class.) |
| "777: nearly 3,000 t… eight fully loaded 777s" | 145 t × 20 ≈ **2,900 t**; ÷ 351.5 t ≈ **8.3** |
| Takeoff heat | At tens of MW, even 95% battery efficiency means **MW-scale heat** to remove, hence pumps, coolant and heat exchangers (more mass) |

## Section 2 and 6 facts

| Claim | Basis |
|---|---|
| Velis Electro: first fully electric aircraft with full type certification (2020), 2 seats, ≈50 min | EASA type certificate, June 2020; manufacturer quotes ≈50 min flight time plus VFR reserve |
| Electric seaplane, Canada | Harbour Air's converted DHC-2 Beaver ("ePlane"/eBeaver, magniX motor), first flight December 2019, Richmond BC |
| Rolls-Royce racer, "more than 550 km/h", 2021 | *Spirit of Innovation*: 555.9 km/h over 3 km (Nov 2021, FAI-submitted record) |
| Solar plane around the world, wings wider than a 747, one pilot | Solar Impulse 2: 72 m wingspan, ≈2.3 t, circumnavigation 2015–2016, single-seat (pilots alternated legs). 747-400 span ≈64.4 m (747-8: 68.4 m) |
| Li-ion "more than tripled since the early nineties" | First commercial Li-ion (Sony, 1991) ≈80 Wh/kg → today's high-energy cells ≈250–300 Wh/kg |
| Advanced cells 400+ Wh/kg (storyboard graphic) ⚠ | Silicon-anode cells claimed at ≈400–500 Wh/kg in small volumes (e.g., Amprius). Check current claims before publishing |
| "Packs 3–4× better… a full-size electric airliner could start to work on shorter routes" ⚠ | Equivalent to ≈600–800 Wh/kg at pack level. ≈800 Wh/kg is the commonly cited threshold for a narrow-body on short routes; see Schäfer et al., "Technological, economic and environmental prospects of all-electric aircraft," *Nature Energy* 4, 160–166 (2019), [doi:10.1038/s41560-018-0294-x](https://doi.org/10.1038/s41560-018-0294-x). **Verify the exact figure in the paper before locking the graphic.** |
| "Several companies… 9–30 seat electric and hybrid aircraft" ⚠ | Several programmes target this segment (e.g., 9-seat all-electric commuters and ~30-seat hybrid-electric regionals). Programmes in this space have been paused, restructured or re-scoped often, so the script deliberately names none. Check status before naming any on screen |
| Hydrogen at −253 °C; "hard challenges" | Liquid hydrogen boils at ≈−253 °C; ≈4× the volume of jet fuel for the same energy. Airbus said in Feb 2025 that its ZEROe hydrogen aircraft will come later than the original 2035 target ([CompositesWorld](https://www.compositesworld.com/news/airbus-pushes-zeroe-aircraft-project-timeline-to-2040s), [Travel Weekly](https://travelweekly.co.uk/news/air/airbus-to-confirm-delay-to-hydrogen-powered-flights)) |
| SAF | Drop-in fuels from waste oils, biomass or captured CO₂ + green hydrogen (e-fuels). Same energy per kg as jet fuel; challenges are cost and production scale |

## Things the script intentionally does **not** claim
- That electric aircraft are pointless. (They're excellent for training, short hops, and urban air mobility.)
- A specific year for electric airliners.
- That batteries will *never* work. The framing is "with today's technology" and "for now."
- Any company's current programme status (these change too fast for an evergreen video).

## Further reading (verify and add to the YouTube description)
- Schäfer, A.W. et al. (2019). *Technological, economic and environmental prospects of all-electric aircraft.* Nature Energy 4, 160–166.
- Viswanathan, V. et al. (2022). *The challenges and opportunities of battery-powered flight.* Nature 601, 519–525.
- EASA type certificate data sheet, Pipistrel Virus SW 128 (Velis Electro), 2020.
- Airbus A320neo and Boeing 777-300ER "Aircraft Characteristics for Airport Planning" documents (weights and fuel capacities).
- ASTM D1655: Standard Specification for Aviation Turbine Fuels.
