# Why Passenger Jets Are Not Electric: Production Bible

A premium, photoreal, documentary-style science explainer for YouTube long-form.

| | |
|---|---|
| **Runtime** | ≈7:25 (target window 6–8 min) |
| **Format** | 16:9, 3840×2160 master (1920×1080 deliverable), 24 fps, 2.39:1 letterbox *only* in the cold open, full 16:9 everywhere else |
| **Audience** | General, curious viewers. No engineering background assumed. |
| **Narration** | ≈1,100 words at about 150 wpm, with deliberate silent beats for SFX moments |
| **Voice** | **HeyGen premium voice "Evan"** (`d21d096b4d684ea0b90a90fcbe8d645b`) via HyperFrames. Locked in [`script.json`](script.json) (`"provider": "heygen"`). Same voice as the channel's previous video. |
| **Look** | Photoreal 3D (Unreal Engine 5 / Blender Cycles) + restrained HUD motion graphics composited *into* the 3D space |

## Deliverables in this folder

| # | Deliverable | File |
|---|---|---|
| 1 | Full video concept + look bible | this file |
| 2 | Complete narration script (timestamped) | [`01_narration_script.md`](01_narration_script.md) |
| 2a | TTS-ready script: 59 lines, Evan voice, mapped to storyboard shots | [`script.json`](script.json) |
| 3–5 | Scene-by-scene storyboard with visual direction and motion graphics for every shot | [`02_storyboard.md`](02_storyboard.md) |
| 6 | SFX and music design per section, plus cue sheet and mix spec | [`03_sound_and_music.md`](03_sound_and_music.md) |
| 7 | Editing and pacing notes, retention map, YouTube chapters | [`04_edit_and_pacing.md`](04_edit_and_pacing.md) |
| 8 | On-screen text: typography system and the full text list | [`05_on_screen_text.md`](05_on_screen_text.md) |
| + | Science fact sheet: every number, how it's derived, sources, caveats | [`06_science_and_sources.md`](06_science_and_sources.md) |

---

## 1. The concept

### The one-sentence idea
**Electric flight isn't waiting on a better motor. It's waiting on a better kilogram.**

Every scene serves one visual argument: *a kilogram of jet fuel and a kilogram of battery weigh the same, but they carry wildly different amounts of energy, and an airplane pays for every kilogram it lifts.* The viewer should be able to explain the video to a friend using one number (**about 20×**) and one image (**a single cube of fuel next to a wall of twenty one-tonne battery pallets**).

### Narrative spine
1. **Hook:** we electrified cars, so why not planes? (curiosity gap)
2. **Electric planes exist.** They're just small. (reframes the question)
3. **What an airliner actually does** with energy: takeoff, climb, cruise. (stakes)
4. **The Energy Lab:** jet fuel vs batteries, kilogram for kilogram. (the core reveal, the visual centrepiece)
5. **Try to build it:** batteries flood an A320 until it can't take off. (consequence)
6. **What could work:** short hops, hybrids, better chemistry, other fuels. (hope, realistically)
7. **Close:** the "better kilogram" line over a future electric regional aircraft at dawn.

### Recurring visual devices (the video's "grammar")
These repeat so that by minute 3 the viewer reads them instantly:

| Device | What it is | Where |
|---|---|---|
| **Colour code** | **Amber = jet fuel / combustion.** **Electric cyan = battery / electricity.** **Signal red = limit exceeded.** Never break this. | Everywhere |
| **The Scale** | A precision laboratory balance beam (brushed steel, glass, real physics wobble) | S4 open, S7 callback |
| **Energy Columns** | Volumetric light columns rising from an object, their height = energy. Amber fuel column, cyan battery column. Measured against a floor-to-ceiling ruler etched in light. | S3, S4, S7 |
| **The Load Gauge** | A cockpit-grade weight indicator (EFIS-style tape plus a large digital readout) with a red **MTOW** line | S4, S5 |
| **X-Ray Mode** | The aircraft skin goes 85% transparent (Fresnel rim light only) so tanks, batteries, wiring, engines read inside a real-looking airframe | S3, S4, S5 |
| **The Map Table** | A dark, photoreal relief globe / map with range rings that grow or shrink | S2, S5, S6 |

### Aircraft "cast"
- **The Narrow-body:** an A320neo-class twin (79 t max takeoff weight, about 180 seats, LEAP-type engines with ≈2 m fans). This is the hero aircraft.
- **The Wide-body:** a 777-300ER-class twin for the long-haul scale moments.
- **The Small Electrics:** Velis Electro-class two-seat trainer, an eBeaver-class seaplane, a record-attempt electric racer, a Solar Impulse-class solar plane, and an eVTOL air-taxi silhouette.
- **The Future:** a fictional 19–30-seat hybrid-electric regional aircraft, "**Meridian**", designed for this film (high wing, six distributed electric propellers, clean white and cyan livery).

> **Legal / brand note:** use a **fictional generic livery** ("white tail, grey belly, no logos") on all airliners. Naming real aircraft *types* in narration is factual and fine. Do not show real airline brands. Real electric aircraft (Velis, eBeaver, Spirit of Innovation, Solar Impulse 2) should be shown either as licensed stock/archival footage with credit, or as closely-modelled generic versions without logos.

---

## Look bible

### Overall
Think *high-end aerospace documentary meets product film*: Apple-keynote cleanliness in the graphics, cinematic weight in the 3D. **No cartoon shading, no bouncy animation, no mascots, no comic SFX.** Motion is physical: everything has mass, inertia and settling.

### Lighting moods by environment
| Environment | Light | Palette |
|---|---|---|
| Runway / sky | Golden hour (low sun, long shadows, heat haze, volumetric atmosphere) for the hook; hard high-noon for cruise | Warm amber highlights, deep teal shadows |
| Hangar | Overhead sodium/LED high-bays, cold fill, polished epoxy floor with reflections, light dust in the beams | Neutral greys, steel |
| **The Energy Lab** (S4) | Black infinite studio. A single large soft key from above, rim lights, floor is black glossy stone with subtle reflection. Graphics glow *into* the set (light emitters, not flat overlays). | Black, amber, cyan |
| Map Table | Dark room, top-down practical light on a relief map, HUD projected onto the surface | Graphite, cyan, amber |
| Future | Blue hour into dawn, clean sky, a little lens bloom | Cool cyan to soft gold |

### Camera language
- Lenses: 24 mm for scale, 35/50 mm for narrative, 100 mm macro for components, 300–600 mm long lens for runway heat-haze telephoto shots.
- Moves: slow push-ins (2–4% scale over a shot), orbits at 6–12°/s, crane reveals, motion-controlled macro slides, cross-section "slice" reveals, exploded views that assemble or disassemble on physical easing (no linear moves).
- Add subtle *handheld or aerial drift* (0.2–0.5° noise) to exterior shots so they feel filmed, not rendered. Lab shots stay locked or motion-controlled.
- Physical camera: 1/48 shutter motion blur, real depth of field (f/2.8–f/5.6), mild chromatic aberration at frame edges, filmic grain (≈2–3%), gentle halation on highlights.

### Asset checklist (build or license)
- A320neo-class aircraft: full interior structure for X-ray mode (wing box, centre tank, wing tanks, cargo holds, cabin floor beams, seats, landing gear with working oleo struts)
- LEAP-class turbofan: hero-grade, fully cutaway-able (fan, booster, high-pressure compressor, combustor, HP and LP turbine, nozzle, nacelle with thrust reverser cascades)
- 777-300ER-class aircraft (exterior + simplified tanks)
- Battery hierarchy: **21700 cylindrical cell → module (cells + cooling plate + busbars) → pack (casing, BMS, cooling lines) → one-tonne pallet unit**
- Lab balance scale, 1 kg graduated glass fuel cylinder, 1-tonne glass fuel cube (1.25 m³, ≈1.08 m per side)
- Electric aircraft set (see cast), eVTOL silhouette, Meridian hero aircraft
- Hangar, airport apron, runway with approach lights, cockpit (for gauge close-ups)
- FX: heat haze, engine exhaust shimmer, contrails, wingtip vortices, rain on runway (optional), dust in light beams

### Render / pipeline recommendation
- **Unreal Engine 5** (Lumen + Path Tracer for hero shots, Movie Render Queue, ACES) for exteriors, hangar and runway; real-time layout lets you iterate camera fast.
- **Blender Cycles or Houdini/Karma** for the cutaway engine, liquid fuel sim (fuel sloshing and draining) and the battery-stacking rigid-body sims.
- **After Effects / Nuke** for HUD compositing; track every graphic into 3D space (C4D/Blender camera export) so labels sit *in* the world with parallax and depth-of-field.
- Colour: ACES → Rec.709 Gamma 2.4 for YouTube, slight S-curve, keep the amber/cyan separation saturated and everything else restrained.
