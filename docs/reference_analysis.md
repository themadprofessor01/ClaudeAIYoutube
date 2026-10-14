# Reference video analysis and the style it led to

## What I actually inspected

The uploaded reference (`videoplayback_3.mp4`) is 11:12 long, 640×358 H.264 at 29.97 fps, with AAC audio. I couldn't watch it in real time, so I analysed it with ffmpeg:

- Contact sheets of 90 frames, one every 8 s, covering the whole video
- Dense 2 fps strips of two 15-second stretches (the cold open and a hunting sequence) to study motion
- Scene-cut detection with ffmpeg `select='gt(scene,0.25)'`, which found 244 cuts in 672 s, about one every 2.75 s
- Loudness measurement: −14.6 dB mean and 0 dB peak, which is typical YouTube mastering

## Observations

| Aspect | What the reference does |
|---|---|
| Illustration | Hand-drawn 2D cartoon. Stick figures with big round white heads, dot pupils inside white eyes and small expressive brows. Bodies are thin ink lines, with clothing as flat colour shapes. Thick, slightly wobbly dark-brown ink outlines. |
| Palette | Warm and desaturated: sand, ochre, sky blue, cream walls, wood floors. Saturated red is saved for alarms and X marks, and green for check marks. Night scenes use deep navy with warm firelight. |
| Typography | Hand-lettered small caps (similar to Patrick Hand SC), centred on off-white "paper" cards, with one small doodle icon in a corner (clock, moon, feather). Big numbers get colour emphasis, e.g. "90,000 HOURS" in red. |
| Card rhythm | Narrative illustration alternates with white title or kinetic-text cards ("FROM THAT SECOND…", "REWIND 50,000 YEARS", "THE OFFICIAL STORY"). These act as chapter beats and pattern interrupts. |
| Motion | Mostly still illustrations brought to life by slow push-ins, small character actions (blinks, a hand reaching), motion lines, vibration marks around an alarm clock, heat squiggles and dotted path trails. Text writes or fades on, and arrows and labels pop in. |
| Diagrams | Simple annotated diagrams: skeleton with arrows and labels, timeline with map pins, split-screen comparisons with a dashed divider ("YOU \| HIM", "✓ \| ✗"), and maps with pins and dotted routes. |
| Editing | Hard cuts on narration beats, around 2–4 s per image. Split screens and crossed-out objects show contrast. Similar shots sometimes repeat with a small change, e.g. the same scene at night. |
| Sound | Voice-forward narration with a soft music bed and small SFX accents (alarm ring, whoosh on cards). |
| Story devices | A second-person cold open ("your alarm rings…"), a hard turn ("REWIND"), named researchers and dates on cards, and a callback ending to the opening scenario. |

## How I adapted it (original, not copied)

- **Same visual language, new cast and world.** Rando is a stick figure in an orange beanie, the channel's mascot. Friends, scientists, a brain character, robots, a cricket and a rat are all drawn procedurally as SVG by `assets/lib/rig.js`.
- **Ink plus wobble.** Outlines are a 6–7 px dark ink stroke with round caps. Characters get a "line boil": a displacement filter that cycles through three seeds at 8 fps, giving a hand-drawn shimmer. I limited it to characters so the render stays fast.
- **Paper cards.** Off-white #FBF8F1 cards with Patrick Hand SC kinetic type (word-by-word pops, write-ons, strike-throughs), plus doodle icons. These serve as chapter beats ("REWIND", "1998 · LONDON", "the real answer").
- **More movement than the reference.** Characters are fully rigged (shoulders, elbows, hips, knees, head, brows, eyes, 10 mouth shapes), so they walk, laugh, flail, type, poke and wave instead of sitting still. Every shot has a slow camera push, and reveals get punch-ins.
- **Same diagram grammar.** Split-screen comparisons, ✓/✗ checklists, hand-drawn bar charts, labelled brain diagrams, dotted motion paths, a stopwatch and volume knobs.
- **Transitions.** Mostly hard cuts and pops, as in the reference. Whip-pans with motion blur mark topic jumps and fades mark tone shifts. No single transition is overused.
- **Pacing.** 73 shots in 7:41 (about one every 6.3 s), and inside each shot something new happens every 1–3 s (labels, poses, props, camera). It runs faster during the hook and reveals and slows for the explanation diagrams.
- **Sound.** Narration-first mix. An original procedural score (marimba, plucked bass, pads, light percussion) changes mood per section: curious, tense, bright, weird, warm. It ducks automatically under the voice. 225 synthesized SFX are tied to on-screen beats.
