"""Generate narration with Kokoro (Apache-2.0) and build timeline/timing.json.

usage: python3 tools/tts.py <kokoro_model_dir> [--only L01,L02]
Writes assets/voice/<id>.wav (per line), assets/audio/narration.wav, timeline/timing.json
"""
import json, sys, os
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 24000

def trim(x, thr=0.008, pad=0.04):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x
    a = max(0, idx[0] - int(pad*SR)); b = min(len(x), idx[-1] + int(pad*SR))
    return x[a:b]

def main():
    mdir = sys.argv[1]
    only = None
    if "--only" in sys.argv: only = set(sys.argv[sys.argv.index("--only")+1].split(","))
    spec = json.load(open(f"{ROOT}/script/script.json"))
    os.makedirs(f"{ROOT}/assets/voice", exist_ok=True)
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{mdir}/kokoro-v1.0.onnx", f"{mdir}/voices-v1.0.bin")
    for sec in spec["sections"]:
        for ln in sec["lines"]:
            p = f"{ROOT}/assets/voice/{ln['id']}.wav"
            if (only and ln["id"] not in only) or (not only and os.path.exists(p)): continue
            s, sr = k.create(ln.get("say", ln["text"]), voice=spec["voice"], speed=ln.get("speed", spec["speed"]), lang="en-us")
            assert sr == SR
            sf.write(p, trim(s), SR)
            print("tts", ln["id"], round(len(s)/SR, 2), flush=True)
    build_timing(spec)

def build_timing(spec):
    t = 0.0; out = {"sections": [], "lines": {}}; chunks = []
    for i, sec in enumerate(spec["sections"]):
        s0 = t
        t += sec.get("lead_in", 0.0)
        for ln in sec["lines"]:
            a, _ = sf.read(f"{ROOT}/assets/voice/{ln['id']}.wav", dtype="float32")
            d = len(a)/SR
            out["lines"][ln["id"]] = {"start": round(t, 3), "end": round(t+d, 3), "section": sec["id"], "text": ln["text"]}
            chunks.append((t, a))
            t += d + ln.get("gap", spec["default_gap"])
        out["sections"].append({"id": sec["id"], "name": sec["name"], "start": round(s0, 3), "end": round(t, 3)})
    out["duration"] = round(t, 3)
    n = int(np.ceil(t*SR)) + SR
    mix = np.zeros(n, np.float32)
    for st, a in chunks:
        i = int(round(st*SR)); mix[i:i+len(a)] += a
    peak = np.abs(mix).max(); mix *= 0.89/peak
    sf.write(f"{ROOT}/assets/audio/narration.wav", mix[:int(t*SR)], SR)
    json.dump(out, open(f"{ROOT}/timeline/timing.json", "w"), indent=1)
    print("duration", round(t, 2), "s =", f"{int(t//60)}:{t%60:05.2f}")

if __name__ == "__main__":
    main()
