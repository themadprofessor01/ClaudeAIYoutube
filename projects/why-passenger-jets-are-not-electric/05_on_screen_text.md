# On-Screen Text and Motion-Graphics System

## Typography
| Role | Typeface (free/open alternatives in brackets) | Style |
|---|---|---|
| Title / big numbers | **Söhne Breit** or **Neue Haas Grotesk Display** (Inter Display / Inter Tight) | Bold, tight tracking (−2%), all caps for titles |
| Labels / callouts | **Neue Haas Grotesk Text** (Inter) | Medium, all caps, +6% tracking, 26–34 px at 1080p |
| HUD / readouts / counters | **Berkeley Mono** or **SF Mono** (JetBrains Mono / IBM Plex Mono) | Tabular figures, so counters never jitter |
| Chapter markers | Inter Medium, all caps | `01 — TITLE`, lower-left, with a 1 px rule |

## Colour tokens
| Token | Hex | Meaning |
|---|---|---|
| `fuel` | `#F2A33A` (amber) | Jet fuel, combustion, engine energy |
| `battery` | `#39C6F4` (electric cyan) | Batteries, electricity, electric aircraft |
| `limit` | `#FF4B3E` (signal red) | Exceeded limits, MTOW line, warnings |
| `text` | `#F2F4F5` | Neutral labels |
| `muted` | `#8A949C` | Secondary labels, units, rules |
| `panel` | `#0B0F12` @ 70% + 12 px blur | Backing plates for readouts (only when the background is busy) |

## Graphic rules
- **Graphics live in the world.** Labels are 3D-tracked with parallax and depth of field. Leader lines are 1 px, ending in a 4 px dot on the object.
- **No drop shadows, no bevels, no gradients on text.** A soft glow (bloom) is allowed only on amber/cyan light elements.
- **Safe areas:** keep text inside 90% title-safe; nothing in the bottom-right 300×120 px area (YouTube controls and end-screen elements).
- **Numbers:** always with a unit, always rounded honestly (`≈20×`, not `19.7×`). Use `≈` whenever a figure is an estimate.
- **Animation:** labels type on with a 6-frame expo-out slide and fade; numbers count up over 12–24 frames with tabular figures; everything exits with a 6-frame fade (no fly-outs).
- **Readability:** 3 words or fewer per callout where possible; on screen for at least 1.5 s per 3 words.

## Reusable components
1. **Chapter marker:** `0X — TITLE` + thin rule, lower-left, on for 3 s.
2. **Spec card:** small stacked readout tracked to an aircraft (name, year, seats, endurance).
3. **Energy Column + light ruler:** volumetric column; ruler ticks light up as it passes; value tag at the top.
4. **Load Gauge:** vertical tape + large digital readout + red `MAX TAKEOFF 79 t` line; turns red with an `OVERWEIGHT` caution when exceeded.
5. **Split-screen readouts:** mirrored left/right gauges, flight timer scrubber, weight-vs-time line graph (amber falling, cyan flat).
6. **Map Table:** range rings, route arcs, holding pattern.
7. **`20×` bug:** persistent top-left corner from 3:17 to 5:30.

---

## Full on-screen text list (by shot)

| Shot | Time | Text | Colour |
|---|---|---|---|
| S1.6 | 0:29 | **WHY PASSENGER JETS ARE NOT ELECTRIC** ("JETS" amber, "ELECTRIC" cyan) | mixed |
| S2.1 | 0:32 | `01 — ELECTRIC FLIGHT IS REAL` | text |
| S2.2 | 0:35 | `PIPISTREL VELIS ELECTRO` · `FIRST TYPE-CERTIFIED ELECTRIC AIRCRAFT · 2020` · `2 SEATS` · `≈50 MIN FLIGHT` | battery |
| S2.3 | 0:50 | `555.9 km/h` · `ALL-ELECTRIC SPEED RECORD · 2021` | battery |
| S2.4 | 0:57 | `SOLAR PLANE · 72 m WINGSPAN` · `BOEING 747 · ≈64 m` · `PASSENGERS: 0 · CREW: 1` | battery / muted |
| S2.6 | 1:10 | `79 TONNES` · `180 PEOPLE` · `800 km/h` | text |
| S3.1 | 1:15 | `02 — THE ENERGY PROBLEM` · `WING TANKS` · `CENTRE TANK` · `FUEL LINES → ENGINES` | text / fuel |
| S3.2 | 1:22 | `0 → 270 km/h IN ≈30 s` · `WEIGHT 79 t` | fuel |
| S3.3 | 1:31 | `FAN ≈2 m` · `COMPRESSOR` · `COMBUSTOR >1,000 °C` · `TURBINE` · `TURBINE SPINS THE FAN` | fuel |
| S3.4 | 1:40 | `TAKEOFF POWER: TENS OF MEGAWATTS` · `≈ A SMALL TOWN` | fuel |
| S3.5 | 1:47 | `LIFTING ≈75 t TO 11 km` · `EVEREST 8.8 km` (ghost) | text |
| S3.6 | 1:53 | `THRUST` / `DRAG` · distance counter | text |
| S3.7 | 2:01 | `FULL TANKS ≈19 t OF FUEL` → `>200 MWh` → `≈3,000 EV BATTERIES` | fuel → battery |
| S3.8 | 2:11 | `LONG-HAUL 777: ×7` | fuel |
| S4.1 | 2:16 | `03 — FUEL vs BATTERY` | text |
| S4.2 | 2:20 | `JET FUEL · 1 kg` · `LITHIUM-ION CELLS · 1 kg` | fuel / battery |
| S4.3 | 2:28 | `1.000 kg │ 1.000 kg` | text |
| S4.4 | 2:34 | `≈12 kWh` | fuel |
| S4.5 | 2:39 | `≈0.25 kWh` | battery |
| S4.6 | 2:43 | **`≈50×`** · `ENERGY PER KILOGRAM` | text |
| S4.7 | 2:50 | `LOST AS HEAT ≈2/3` · `USEFUL ≈1/3` · `≈4 kWh USEFUL` | fuel |
| S4.8 | 2:58 | `≈90% BECOMES MOTION` | battery |
| S4.9 | 3:03 | `COOLING` · `WIRING` · `CASING` · `PROTECTION` · `+ WEIGHT` | battery |
| S4.10 | 3:10 | counter `1 … 20` · **`≈20×`** · `MORE USEFUL ENERGY PER kg` | text |
| S4.11 | 3:17 | **`20×`** → becomes corner bug | text |
| S4.12 | 3:24 | `1 TONNE` · `≈1,250 LITRES` · `≈1.08 m` | fuel |
| S4.13 | 3:31 | `BATTERIES: 1 t → 20 t` · Load Gauge | battery |
| S4.14 | 3:38 | `20 t ≈ 13 CARS` · `1 CUBE OF FUEL` vs `20 t OF BATTERIES` | muted / fuel / battery |
| S4.16 | 3:47 | `351 t → 251 t` · `≈100 TONNES LIGHTER AT LANDING` · timer `0 h → 13 h` | fuel |
| S4.17 | 3:57 | `LESS THRUST NEEDED` | fuel |
| S4.18 | 4:03 | `CHARGE: 100% → 0%` · `WEIGHT: UNCHANGED` · 🔒 | battery |
| S4.19 | 4:10 | `LANDS: 251 t` vs `LANDS: 351 t` | fuel / limit |
| S5.1 | 4:15 | `04 — BUILDING AN ELECTRIC AIRLINER` | text |
| S5.2 | 4:19 | `1,000 km` · `TRIP ≈4 t` + `RESERVES ≈2 t` = `≈6 t` · `RESERVES: DIVERT + HOLD (REQUIRED BY REGULATION)` | fuel |
| S5.3 | 4:31 | `6 t × 20 =` | text |
| S5.4 | 4:35 | **`120 t OF BATTERIES`** | battery |
| S5.5 | 4:39 | `EMPTY AIRCRAFT 44 t` + `BATTERIES 120 t` = `164 t` · `MAX TAKEOFF 79 t` · `OVERWEIGHT` · `PASSENGERS 0 · BAGS 0` · `MORE THAN TWICE THE PLANE'S MAXIMUM TAKEOFF WEIGHT` | battery / limit |
| S5.6 | 4:48 | `MORE WEIGHT → STRONGER STRUCTURE → MORE DRAG → MORE ENERGY → MORE BATTERIES` · **`THE WEIGHT SPIRAL`** · `IT NEVER CLOSES` | limit |
| S5.7 | 5:03 | `TAKEOFF DRAW: TENS OF MEGAWATTS → HEAT → COOLING → MORE WEIGHT` | limit |
| S5.8 | 5:12 | `SEATS: 0` · `NORMAL RANGE ≈6,000 km` → `ELECTRIC: A SHORT HOP` | battery |
| S5.9 | 5:23 | `≈3,000 t OF BATTERIES = 8 FULLY LOADED 777s` | battery |
| S6.1 | 5:36 | `FOR NOW` | battery |
| S6.2 | 5:40 | `05 — WHAT COULD WORK` | text |
| S6.3 | 5:48 | `SWEET SPOT: SHORT ROUTES` · `9–30 SEATS` · `A FEW HUNDRED km` | battery |
| S6.4 | 6:00 | `TAKEOFF: BATTERY + ENGINE` → `CRUISE: ENGINE` → `RESERVES: FUEL` | mixed |
| S6.5 | 6:09 | `≈80 Wh/kg (1991)` → `≈250–300 Wh/kg (TODAY)` → `400+ (ADVANCED CELLS)` → `LITHIUM-SULFUR / SOLID-STATE?` · `×3+ SINCE THE EARLY '90s` | battery |
| S6.6 | 6:23 | `≈3–4× TODAY'S PACKS` · `THRESHOLD FOR A SHORT-RANGE ELECTRIC AIRLINER (STUDY ESTIMATES)` | battery |
| S6.7 | 6:32 | `SUSTAINABLE AVIATION FUEL` · `CHALLENGES: COST & SCALE` · `HYDROGEN (−253 °C)` · `CHALLENGES: VOLUME & INFRASTRUCTURE` | muted |
| S7.1 | 6:45 | `06 — THE ANSWER` | text |
| S7.2 | 6:50 | `QUIET` · `SIMPLE` · `EFFICIENT` | battery |
| S7.3 | 6:57 | `≈20× MORE USEFUL ENERGY PER kg` · `FUEL GETS LIGHTER` │ `BATTERIES DON'T` | fuel / battery |
| S7.6 | 7:19 | **`WAITING ON A BETTER KILOGRAM.`** | text |

## Subtitles / captions
Burned-in captions are **not** recommended for the main upload (they clash with the HUD). Upload an accurate `.srt` from the final VO instead. The Shorts cut should use burned-in captions in the upper third (above the energy columns).
