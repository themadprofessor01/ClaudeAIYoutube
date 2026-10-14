"""Generate the narration and build timeline/timing.json.

Two providers (script.json "provider"):
  heygen  — HeyGen premium voice (script.json "heygen_voice"), via the HyperFrames media-use
            heygen-tts.mjs script. Needs `npx hyperframes auth login` (or HEYGEN_API_KEY).
            Also returns word timestamps, saved to assets/voice/<id>.words.json.
  kokoro  — local Kokoro-82M (Apache-2.0) fallback; pass the model dir as argv[1].

usage: python3 tools/tts.py [kokoro_model_dir] [--only L01,L02] [--force]
Writes assets/voice/<id>.wav (+ .words.json), assets/audio/narration.wav/.m4a, timeline/timing.json
"""
import json, sys, os, subprocess
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100  # narration mix sample rate
HEYGEN_TTS = os.path.expanduser("~/.claude/skills/media-use/audio/scripts/heygen-tts.mjs")


def trim(x, sr, thr=0.008, pad=0.04):
    """Trim leading/trailing silence. Returns (audio, seconds removed from the start)."""
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] - int(pad * sr)); b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b], a / sr


def to_sr(x, sr):
    if sr == SR:
        return x
    n = int(round(len(x) * SR / sr))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def gen_heygen(text, voice, wav, words):
    env = dict(os.environ, NODE_USE_ENV_PROXY="1", NODE_NO_WARNINGS="1")
    r = subprocess.run(["node", HEYGEN_TTS, text, "--voice", voice, "-o", wav, "--words", words],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"heygen-tts failed: {r.stderr.strip()[-400:]}")
    a, sr = sf.read(wav, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    a, off = trim(to_sr(a, sr), SR)
    sf.write(wav, a, SR)
    w = json.load(open(words))
    for x in w:  # shift word times by the trimmed lead-in
        x["start"] = round(max(0.0, x["start"] - off), 3); x["end"] = round(max(0.0, x["end"] - off), 3)
    json.dump(w, open(words, "w"), indent=0)


def main():
    spec = json.load(open(f"{ROOT}/script/script.json"))
    provider = spec.get("provider", "kokoro")
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    force = "--force" in sys.argv
    os.makedirs(f"{ROOT}/assets/voice", exist_ok=True)
    k = None
    for sec in spec["sections"]:
        for ln in sec["lines"]:
            p = f"{ROOT}/assets/voice/{ln['id']}.wav"
            if only and ln["id"] not in only:
                continue
            if not only and not force and os.path.exists(p):
                continue
            if provider == "heygen":
                # premium TTS reads digits/years correctly, so only explicit heygen_say overrides apply
                gen_heygen(ln.get("heygen_say", ln["text"]), spec["heygen_voice"], p, p.replace(".wav", ".words.json"))
            else:
                if k is None:
                    from kokoro_onnx import Kokoro
                    mdir = sys.argv[1]
                    k = Kokoro(f"{mdir}/kokoro-v1.0.onnx", f"{mdir}/voices-v1.0.bin")
                s, sr = k.create(ln.get("say", ln["text"]), voice=spec["voice"], speed=ln.get("speed", spec["speed"]), lang="en-us")
                s, _ = trim(to_sr(s, sr), SR)
                sf.write(p, s, SR)
                wj = p.replace(".wav", ".words.json")
                if os.path.exists(wj):
                    os.remove(wj)
            print("tts", ln["id"], round(sf.info(p).duration, 2), flush=True)
    build_timing(spec)


def build_timing(spec):
    t = 0.0; out = {"sections": [], "lines": {}}; chunks = []
    for sec in spec["sections"]:
        s0 = t
        t += sec.get("lead_in", 0.0)
        for ln in sec["lines"]:
            a, sr = sf.read(f"{ROOT}/assets/voice/{ln['id']}.wav", dtype="float32")
            a = to_sr(a if a.ndim == 1 else a.mean(1), sr)
            d = len(a) / SR
            rec = {"start": round(t, 3), "end": round(t + d, 3), "section": sec["id"], "text": ln["text"]}
            wj = f"{ROOT}/assets/voice/{ln['id']}.words.json"
            if os.path.exists(wj):
                rec["words"] = [[x["text"], round(t + x["start"], 3)] for x in json.load(open(wj))]
            out["lines"][ln["id"]] = rec
            chunks.append((t, a))
            t += d + ln.get("gap", spec["default_gap"])
        out["sections"].append({"id": sec["id"], "name": sec["name"], "start": round(s0, 3), "end": round(t, 3)})
    out["duration"] = round(t, 3)
    n = int(np.ceil(t * SR)) + SR
    mix = np.zeros(n, np.float32)
    for st, a in chunks:
        i = int(round(st * SR)); mix[i:i + len(a)] += a
    peak = np.abs(mix).max(); mix *= 0.89 / peak
    sf.write(f"{ROOT}/assets/audio/narration.wav", mix[:int(t * SR)], SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{ROOT}/assets/audio/narration.wav", "-c:a", "aac", "-b:a", "192k",
                    f"{ROOT}/assets/audio/narration.m4a"], check=True)
    json.dump(out, open(f"{ROOT}/timeline/timing.json", "w"), indent=1)
    print("duration", round(t, 2), "s =", f"{int(t//60)}:{t%60:05.2f}")


if __name__ == "__main__":
    main()
