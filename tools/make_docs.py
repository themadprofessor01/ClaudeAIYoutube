"""Generate docs/narration_script.md and docs/scene_breakdown.md from the real timeline.

usage: python3 tools/make_docs.py
Timestamps come from timeline/timing.json (measured TTS durations), so they match the render.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(f"{ROOT}/timeline/timing.json"))
spec = json.load(open(f"{ROOT}/script/script.json"))
sfx = json.load(open(f"{ROOT}/timeline/sfx_events.json")) if os.path.exists(f"{ROOT}/timeline/sfx_events.json") else []


def ts(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


# ---------------- narration script
out = [f"# Narration script — {spec['title']}", "",
       f"Channel: **{spec['channel']}** · Voice: Kokoro `{spec['voice']}` at speed {spec['speed']} · Runtime **{ts(T['duration'])}**", "",
       "Timestamps are measured from the generated voice-over (`assets/audio/narration.wav`).",
       "Lines with a `say:` note were spelled phonetically for the TTS engine; the on-screen/subtitle text is the line itself.", ""]
for sec in spec["sections"]:
    s = [x for x in T["sections"] if x["id"] == sec["id"]][0]
    out += [f"## {sec['name']}  ({ts(s['start'])} – {ts(s['end'])})", ""]
    for ln in sec["lines"]:
        l = T["lines"][ln["id"]]
        out.append(f"**[{ts(l['start'])}]** {ln['text']}  ")
        if "say" in ln and ln["say"] != ln["text"]:
            out.append(f"<sub>say: _{ln['say']}_</sub>  ")
        out.append("")
open(f"{ROOT}/docs/narration_script.md", "w").write("\n".join(out))

# ---------------- subtitles (SRT) — useful for YouTube upload
srt = []
i = 1
for lid, l in T["lines"].items():
    words = l["text"].split()
    # split long lines into ~12-word captions spread proportionally across the line
    chunks = [words[k:k + 12] for k in range(0, len(words), 12)]
    total = sum(len(c) for c in chunks)
    t0 = l["start"]
    for c in chunks:
        d = (l["end"] - l["start"]) * len(c) / total
        a, b = t0, t0 + d
        f = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
        srt += [str(i), f"{f(a)} --> {f(b)}", " ".join(c), ""]
        i += 1
        t0 = b
open(f"{ROOT}/docs/subtitles.srt", "w").write("\n".join(srt))

# ---------------- scene breakdown: parse shot lists out of each composition
out = ["# Scene-by-scene breakdown", "",
       f"Total runtime **{ts(T['duration'])}** · 1920×1080 · 30 fps · {len(sfx)} synced sound effects", "",
       "Each section is one HyperFrames sub-composition in `compositions/`. Shot times below are absolute video time.", ""]
SHOTS = json.load(open(f"{ROOT}/docs/shots.json"))
REAL = json.load(open(f"{ROOT}/timeline/shots.json")) if os.path.exists(f"{ROOT}/timeline/shots.json") else []
real_t = {(r["scene"], r["shot"]): r["abs"] for r in REAL}
for s in T["sections"]:
    out += [f"## {s['id'].upper()} · {s['name']}  ({ts(s['start'])} – {ts(s['end'])})", "",
            f"File: `compositions/{s['id']}.html`", "", "| Time | Shot | Narration beat | Visual / motion | Sound |", "|---|---|---|---|---|"]
    for sh in SHOTS.get(s["id"], []):
        lid = sh["line"]
        l = T["lines"][lid]
        key = sh["shot"].split("–")[0]
        t_abs = real_t.get((s["id"], key), l["start"])
        out.append(f"| {ts(t_abs)} | {sh['shot']} | {lid}: “{l['text'][:60]}{'…' if len(l['text']) > 60 else ''}” | {sh['visual']} | {sh['sound']} |")
    out.append("")
open(f"{ROOT}/docs/scene_breakdown.md", "w").write("\n".join(out))
print("docs written")
