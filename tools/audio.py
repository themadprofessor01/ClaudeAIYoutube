"""Original procedural audio for the video — no samples, no third-party audio.

  python3 tools/audio.py
    → assets/audio/sfx/<name>.wav   (synthesised sound-effect library)
    → assets/audio/sfx.wav          (all SFX placed from timeline/sfx_events.json)
    → assets/audio/music.wav        (score, arranged per section, ducked under narration)

Everything is generated from code with numpy, so it is 100% original and license-free.
"""
import json, os
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
rs = np.random.RandomState(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.005, d=None, curve=6.0):
    """attack then exponential decay over n samples"""
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    k = np.arange(n - na) / max(1, n - na)
    e[na:] = np.exp(-curve * k)
    return e


def lp(x, cutoff):
    """one-pole low-pass (vectorised via cumulative filter in chunks)"""
    a = np.exp(-2 * np.pi * cutoff / SR)
    from scipy.signal import lfilter  # type: ignore
    return lfilter([1 - a], [1, -a], x)


try:
    import scipy.signal  # noqa
    HAVE_SCIPY = True
except Exception:  # pragma: no cover
    HAVE_SCIPY = False


def lowpass(x, cutoff):
    if HAVE_SCIPY:
        return lp(x, cutoff)
    # crude fallback: moving average
    k = max(1, int(SR / cutoff / 2))
    return np.convolve(x, np.ones(k) / k, mode="same")


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, lo, hi):
    return highpass(lowpass(x, hi), lo)


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


# ---------------------------------------------------------------- SFX library
def sfx_library():
    L = {}
    noise = lambda d: rs.uniform(-1, 1, int(d * SR))

    # whoosh: band-passed noise with a swept centre + swell
    def whoosh(d=0.45, f0=400, f1=2600):
        n = noise(d)
        tt = t_(d)
        out = np.zeros_like(n)
        segs = 24
        L_ = len(n) // segs
        for i in range(segs):
            f = f0 + (f1 - f0) * (i / segs) ** 1.5
            seg = n[i * L_:(i + 1) * L_ + 2000]
            out[i * L_:i * L_ + len(seg)] += bandpass(seg, f * 0.6, f * 1.6)[: len(out) - i * L_] * np.hanning(len(seg))[: len(out) - i * L_]
        e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.6
        return norm(out * e, 0.7)

    L["whoosh"] = whoosh()
    L["swish"] = whoosh(0.25, 1200, 5000) * 0.8
    L["whoosh_big"] = whoosh(0.8, 200, 1800)

    # pop: short sine blip with pitch drop
    def pop(f=900, d=0.09):
        tt = t_(d)
        f_t = f * np.exp(-tt * 18)
        return norm(np.sin(2 * np.pi * np.cumsum(f_t) / SR) * env(len(tt), 0.002, curve=9), 0.8)

    L["pop"] = pop()
    L["pop2"] = pop(1300, 0.07)
    L["blip"] = pop(1800, 0.06) * 0.7

    # click / tick
    tt = t_(0.03)
    L["click"] = norm(bandpass(noise(0.03), 2000, 7000) * env(len(tt), 0.0005, curve=30), 0.7)
    tt = t_(0.05)
    L["tick"] = norm(np.sin(2 * np.pi * 2400 * tt) * env(len(tt), 0.0005, curve=40), 0.5)

    # impact: low thump + noise crack
    tt = t_(0.7)
    thump = np.sin(2 * np.pi * np.cumsum(110 * np.exp(-tt * 9) + 40) / SR) * env(len(tt), 0.001, curve=7)
    crack = lowpass(noise(0.7), 3000) * env(len(tt), 0.001, curve=25)
    L["impact"] = norm(thump + 0.5 * crack, 0.95)
    tt = t_(0.35)
    L["thud"] = norm(np.sin(2 * np.pi * np.cumsum(90 * np.exp(-tt * 12) + 35) / SR) * env(len(tt), 0.001, curve=9), 0.9)

    # ding (bell) / buzz (wrong)
    tt = t_(1.2)
    ding = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, a, k in [(1568, 1, 3.5), (3136, 0.4, 6), (4704, 0.25, 9), (2350, 0.2, 5)])
    L["ding"] = norm(ding * env(len(tt), 0.002, curve=1), 0.6)
    tt = t_(0.4)
    saw = 2 * ((tt * 140) % 1) - 1
    L["buzz"] = norm(lowpass(saw + 0.5 * (2 * ((tt * 147) % 1) - 1), 1800) * (np.minimum(1, tt * 60)) * np.exp(-tt * 3), 0.55)

    # boing: pitch-wobbling sine
    tt = t_(0.6)
    f = 220 + 160 * np.exp(-tt * 4) * np.sin(2 * np.pi * 9 * tt) + 80 * tt
    L["boing"] = norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.003, curve=4), 0.6)

    # tickle: fast fluttery high blips
    out = np.zeros(int(1.0 * SR))
    for i in range(14):
        b = pop(2200 + 400 * ((i * 7) % 5), 0.04) * 0.5
        s = int(i * 0.065 * SR)
        out[s:s + len(b)] += b
    L["tickle"] = norm(out, 0.5)

    # wind (for tumbleweed)
    tt = t_(2.8)
    w = bandpass(noise(2.8), 300, 1200)
    L["wind"] = norm(w * np.sin(np.pi * tt / 2.8) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.8 * tt)), 0.45)

    # riser: rising filtered noise + rising tone
    d = 2.2
    tt = t_(d)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / d) ** 2) / SR) * 0.3
    nz = highpass(noise(d), 800) * 0.6
    L["riser"] = norm((tone + nz) * (tt / d) ** 2.2, 0.6)

    # sparkle: cascade of bell pings
    out = np.zeros(int(1.4 * SR))
    for i, f in enumerate([2093, 2637, 3136, 3951, 4186, 5274]):
        tt2 = t_(0.8)
        b = np.sin(2 * np.pi * f * tt2) * np.exp(-tt2 * 7) * 0.4
        s = int(i * 0.07 * SR)
        out[s:s + len(b)] += b
    L["sparkle"] = norm(out, 0.45)

    # glitch: bit-crushed stutter
    tt = t_(0.5)
    g = np.sign(np.sin(2 * np.pi * 180 * tt)) * (rs.uniform(size=len(tt)) > 0.4)
    g = np.repeat(g[::40], 40)[: len(tt)]
    gate = (np.floor(tt * 24) % 2 == 0)
    L["glitch"] = norm(lowpass(g * gate, 5000) * np.exp(-tt * 2), 0.45)

    # chirp (cricket): repeated 4.5 kHz pulses
    out = np.zeros(int(0.5 * SR))
    for i in range(4):
        tt2 = t_(0.035)
        b = np.sin(2 * np.pi * 4500 * tt2) * np.sin(np.pi * tt2 / 0.035)
        s = int(i * 0.05 * SR)
        out[s:s + len(b)] += b
    L["chirp"] = norm(out, 0.55)

    # alarm: two-tone
    tt = t_(0.9)
    f = np.where((tt * 6).astype(int) % 2 == 0, 880, 660)
    L["alarm"] = norm(lowpass(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 2500) * np.minimum(1, (0.9 - tt) * 10), 0.4)

    # typing: random clicks
    out = np.zeros(int(1.2 * SR))
    r = np.random.RandomState(3)
    for i in range(14):
        s = int((i * 0.08 + r.uniform(0, 0.03)) * SR)
        c = L["click"] * r.uniform(0.5, 1)
        out[s:s + len(c)] += c
    L["typing"] = norm(out, 0.5)

    # stamp: thump + paper
    L["stamp"] = norm(L["thud"][: int(0.3 * SR)] + 0.4 * np.pad(L["click"], (0, int(0.27 * SR))), 0.85)

    # drumroll
    d = 1.6
    out = np.zeros(int(d * SR))
    for i in range(int(d / 0.045)):
        tt2 = t_(0.05)
        hit = bandpass(noise(0.05), 150, 2500) * np.exp(-tt2 * 60) * (0.4 + 0.6 * i / (d / 0.045))
        s = int(i * 0.045 * SR)
        out[s:s + len(hit)] += hit
    L["drumroll"] = norm(out, 0.6)

    # beep (robot)
    tt = t_(0.18)
    L["beep"] = norm(np.sign(np.sin(2 * np.pi * 1200 * tt)) * env(len(tt), 0.002, curve=3) * 0.3, 0.35)
    tt = t_(0.5)
    L["robot"] = norm(np.concatenate([np.sin(2 * np.pi * f * t_(0.1)) * 0.5 for f in (660, 990, 880, 1320, 1100)]), 0.4)

    # squeak (rat)
    tt = t_(0.18)
    L["squeak"] = norm(np.sin(2 * np.pi * np.cumsum(2600 + 900 * np.sin(np.pi * tt / 0.18)) / SR) * np.sin(np.pi * tt / 0.18), 0.45)

    # heartbeat / shimmer / page
    tt = t_(0.5)
    hb = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 14)
    L["heartbeat"] = norm(hb + np.pad(hb, (int(0.18 * SR), 0))[: len(hb)] * 0.7, 0.8)
    L["page"] = norm(bandpass(noise(0.35), 1500, 6000) * np.sin(np.pi * t_(0.35) / 0.35) ** 2, 0.4)
    tt = t_(0.25)
    L["snap"] = norm(bandpass(noise(0.25), 800, 4000) * np.exp(-tt * 40), 0.8)
    # rewind: descending fast blips
    out = np.zeros(int(1.0 * SR))
    for i in range(16):
        b = pop(3000 - i * 150, 0.04) * 0.4
        s = int(i * 0.055 * SR)
        out[s:s + len(b)] += b
    L["rewind"] = norm(out + whoosh(1.0, 3000, 300) * 0.4, 0.55)
    # swell: soft pad swell for reveals
    d = 1.8
    tt = t_(d)
    sw = sum(np.sin(2 * np.pi * f * tt) for f in (261.6, 329.6, 392.0, 523.3)) * (tt / d) ** 2 * np.exp(-np.maximum(0, tt - d * 0.85) * 30)
    L["swell"] = norm(sw, 0.35)
    # muffle (volume down) + thump-down
    tt = t_(0.5)
    L["down"] = norm(np.sin(2 * np.pi * np.cumsum(600 * np.exp(-tt * 4)) / SR) * env(len(tt), 0.01, curve=4), 0.4)
    L["up"] = norm(np.sin(2 * np.pi * np.cumsum(300 + 900 * tt) / SR) * env(len(tt), 0.01, curve=4), 0.4)
    return L


# ---------------------------------------------------------------- music
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name):
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + 12 * (o + 1) - 69) / 12)


def marimba(f, d=0.6, vel=1.0):
    tt = t_(d)
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) + 0.35 * np.sin(2 * np.pi * f * 3.93 * tt) * np.exp(-tt * 14) \
        + 0.12 * np.sin(2 * np.pi * f * 9.2 * tt) * np.exp(-tt * 30)
    a = int(0.003 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return x * vel


def pluck(f, d=0.8, vel=1.0, bright=0.5):
    """Karplus-Strong, block-vectorised"""
    N = int(SR / f)
    n = int(d * SR)
    buf = rs.uniform(-1, 1, N)
    buf = lowpass(buf, 2000 + 6000 * bright) if HAVE_SCIPY else buf
    out = np.zeros(n + N)
    out[:N] = buf
    i = N
    while i < n:
        j = min(n, i + N)
        prev = out[i - N:j - N]
        prev2 = out[i - N - 1:j - N - 1] if i - N - 1 >= 0 else np.concatenate([[0], out[i - N:j - N - 1]])
        out[i:j] = 0.497 * (prev + prev2[: len(prev)])
        i = j
    x = out[:n]
    a = int(0.002 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return x * vel


def pad(freqs, d, vel=1.0, bright=900):
    tt = t_(d)
    x = np.zeros(len(tt))
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            x += 2 * ((tt * ff + rs.uniform()) % 1) - 1
    x = lowpass(lowpass(x, bright), bright)
    a = min(len(tt) // 3, int(0.8 * SR))
    e = np.ones(len(tt))
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-a:] = np.linspace(1, 0, a) ** 2
    return x * e * vel / (len(freqs) * 3)


def kick(vel=1.0):
    tt = t_(0.35)
    return np.sin(2 * np.pi * np.cumsum(55 + 120 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9) * vel


def shaker(vel=1.0):
    tt = t_(0.08)
    return highpass(rs.uniform(-1, 1, len(tt)), 5000) * np.exp(-tt * 50) * vel


def snap(vel=1.0):
    tt = t_(0.18)
    return bandpass(rs.uniform(-1, 1, len(tt)), 900, 3500) * np.exp(-tt * 35) * vel


CHORDS = {
    "C": ["C3", "E3", "G3"], "G": ["G2", "B2", "D3"], "Am": ["A2", "C3", "E3"], "F": ["F2", "A2", "C3"],
    "Dm": ["D3", "F3", "A3"], "E": ["E2", "G#2", "B2"], "Em": ["E3", "G3", "B3"], "Bb": ["A#2", "D3", "F3"],
}


def up(note, k):
    n, o = note[:-1], int(note[-1])
    return n + str(o + k)


def arrange(mood, dur, bpm, seed):
    """Return a stereo music bed of `dur` seconds for a given mood."""
    r = np.random.RandomState(seed)
    beat = 60 / bpm
    bar = 4 * beat
    n = int(dur * SR) + SR * 2
    L = np.zeros(n)
    Rr = np.zeros(n)

    def put(x, t, pan=0.0, g=1.0):
        s = int(t * SR)
        if s >= n:
            return
        e = min(n, s + len(x))
        L[s:e] += x[: e - s] * g * (1 - max(0, pan))
        Rr[s:e] += x[: e - s] * g * (1 + min(0, pan))

    progs = {
        "curious": ["C", "Am", "F", "G"],
        "weird": ["Am", "F", "Dm", "E"],
        "warm": ["F", "C", "Am", "G"],
        "bright": ["C", "G", "Am", "F"],
        "tense": ["Dm", "Bb", "Dm", "E"],
    }
    prog = progs[mood]
    nbars = int(np.ceil(dur / bar))
    # melodic motif: scale degrees over chord tones
    motif = [0, 2, 1, 2, 0, 1, 2, 1] if mood in ("curious", "bright") else [0, 1, 2, 1, 2, 0, 1, 0]
    for b in range(nbars):
        t0 = b * bar
        ch = CHORDS[prog[b % 4]]
        # pad
        put(pad([hz(up(x, 1)) for x in ch], bar + 0.4, 0.55 if mood != "tense" else 0.65, 1100 if mood != "warm" else 800), t0, 0, 1)
        # bass pluck on 1 and 3 (+ & of 4)
        bn = hz(ch[0]) / (2 if hz(ch[0]) > 110 else 1)
        if mood != "warm":
            put(pluck(bn, 0.9, 0.9, 0.2), t0, 0, 0.8)
            put(pluck(bn, 0.6, 0.6, 0.2), t0 + 2 * beat, 0, 0.7)
            put(pluck(bn * 1.5, 0.4, 0.4, 0.2), t0 + 3.5 * beat, 0, 0.5)
        else:
            put(pluck(bn, 2.0, 0.8, 0.1), t0, 0, 0.7)
        # arpeggio
        if mood in ("curious", "bright", "weird"):
            for i in range(8):
                note = up(ch[motif[i] % 3], 2 if mood != "weird" else 2)
                v = 0.55 if i % 2 == 0 else 0.38
                put(marimba(hz(note), 0.5, v), t0 + i * beat / 2, -0.3 if i % 2 else 0.3, 0.8)
            # occasional melody notes an octave up every other bar
            if b % 2 == 1:
                for i, k in enumerate([2, 1, 0] if mood != "weird" else [0, 2, 1]):
                    put(marimba(hz(up(ch[k], 3)), 0.8, 0.35), t0 + (i + 1) * beat, 0.1, 0.7)
        elif mood == "warm":
            for i in range(4):
                put(marimba(hz(up(ch[i % 3], 2)), 1.2, 0.35), t0 + i * beat, 0.2 * (-1) ** i, 0.7)
        elif mood == "tense":
            for i in range(4):
                put(pluck(hz(up(ch[(i * 2) % 3], 2)), 0.25, 0.35, 0.6), t0 + i * beat, 0.2 * (-1) ** i, 0.7)
        # light percussion
        if mood in ("curious", "bright"):
            for i in range(8):
                put(shaker(0.5 if i % 2 else 0.3), t0 + i * beat / 2, 0.4, 0.5)
            put(kick(0.7), t0, 0, 0.6)
            put(kick(0.5), t0 + 2 * beat, 0, 0.6)
            put(snap(0.5), t0 + beat, -0.2, 0.5)
            put(snap(0.5), t0 + 3 * beat, -0.2, 0.5)
        elif mood == "weird":
            for i in range(4):
                put(shaker(0.35), t0 + (i + 0.5) * beat, 0.5, 0.5)
            put(kick(0.5), t0, 0, 0.5)
    out = np.stack([L, Rr], 1)[: int(dur * SR)]
    return out


# section → mood. Music drops out for dramatic beats via `holes` (absolute times from cues)
MOODS = {"s01": "curious", "s02": "tense", "s03": "curious", "s04": "bright", "s05": "weird", "s06": "warm", "s07": "bright"}
MIN_GAP = 0.6   # only pauses at least this long get music
FADE = 0.25      # seconds
MUSIC_DB = -12.0  # music level inside the windows
UNDER_VOICE_DB = {"s01": -34.0, "s07": -34.0}  # quiet bed under the voice, these sections only
BPM = {"curious": 100, "bright": 104, "weird": 96, "tense": 80, "warm": 78}


def main():
    T = json.load(open(f"{ROOT}/timeline/timing.json"))
    total = T["duration"]
    N = int(np.ceil(total * SR))
    os.makedirs(f"{ROOT}/assets/audio/sfx", exist_ok=True)

    # ---- SFX
    lib = sfx_library()
    for k, v in lib.items():
        sf.write(f"{ROOT}/assets/audio/sfx/{k}.wav", v.astype(np.float32), SR)
    ev_path = f"{ROOT}/timeline/sfx_events.json"
    events = json.load(open(ev_path)) if os.path.exists(ev_path) else []
    sfx = np.zeros((N, 2))
    missing = set()
    for e in events:
        x = lib.get(e["name"])
        if x is None:
            missing.add(e["name"])
            continue
        s = int(e["abs"] * SR)
        if s >= N or s < 0:
            continue
        x = x[: N - s] * e.get("gain", 1) * 0.36
        sfx[s:s + len(x), 0] += x
        sfx[s:s + len(x), 1] += x
    if missing:
        print("WARNING unknown sfx:", sorted(missing))
    pk = np.abs(sfx).max()
    if pk > 0.98:
        sfx *= 0.98 / pk
    sf.write(f"{ROOT}/assets/audio/sfx.wav", sfx.astype(np.float32), SR)
    print("sfx events:", len(events))

    # ---- music: one bed per section with short crossfades
    music = np.zeros((N + SR * 3, 2))
    for i, sec in enumerate(T["sections"]):
        mood = MOODS[sec["id"]]
        st, en = sec["start"], sec["end"]
        d = en - st + 1.0
        bed = arrange(mood, d, BPM[mood], seed=i + 1)
        fade = int(0.8 * SR)
        e = np.ones(len(bed))
        if i > 0:
            e[:fade] = np.linspace(0, 1, fade)
        e[-fade:] = np.linspace(1, 0, fade)
        if sec["id"] == "s07":  # final ring-out
            e[-int(2.5 * SR):] = np.linspace(1, 0, int(2.5 * SR)) ** 2
        bed = bed * e[:, None]
        s = int(st * SR)
        music[s:s + len(bed)] += bed
    music = music[:N]
    music = music / (np.abs(music).max() + 1e-9)

    # ---- music only where it's needed: never under the narrator.
    # The bed plays in the intro, in real pauses between lines (section breaks / dramatic beats)
    # and over the end card. Whenever the voice speaks, the music is fully cut (with short fades).
    lines = sorted(T["lines"].values(), key=lambda l: l["start"])
    windows = [(0.0, lines[0]["start"])]
    for a_, b_ in zip(lines, lines[1:]):
        if b_["start"] - a_["end"] >= MIN_GAP:
            windows.append((a_["end"], b_["start"]))
    windows.append((lines[-1]["end"], total))
    gate = np.zeros(N)
    fade = int(FADE * SR)
    for w0, w1 in windows:
        i0, i1 = int(w0 * SR), min(N, int(w1 * SR))
        if i1 - i0 < 2 * fade:
            continue
        gate[i0:i1] = 1.0
        gate[i0:i0 + fade] = np.linspace(0, 1, fade)   # fade in after the voice stops
        gate[i1 - fade:i1] = np.linspace(1, 0, fade)   # fade out just before the voice returns
    # a very quiet bed under the voice only in the hook and the outro (energy), silence elsewhere
    under = np.zeros(N)
    for sec in T["sections"]:
        if sec["id"] in UNDER_VOICE_DB:
            i0, i1 = int(sec["start"] * SR), min(N, int(sec["end"] * SR))
            under[i0:i1] = 10 ** ((UNDER_VOICE_DB[sec["id"]] - MUSIC_DB) / 20)
    from scipy.signal import lfilter  # type: ignore
    a_ = np.exp(-1 / (0.3 * SR))
    under = lfilter([1 - a_], [1, -a_], under)
    music *= (np.maximum(gate, under) * 10 ** (MUSIC_DB / 20))[:, None]
    print("music windows:", len(windows), "| total music time", round(gate.sum() / SR, 1), "s")
    # global fade in/out
    fi = int(0.4 * SR)
    music[:fi] *= np.linspace(0, 1, fi)[:, None]
    sf.write(f"{ROOT}/assets/audio/music.wav", music.astype(np.float32), SR)
    print("music written", round(total, 2), "s")
    encode_m4a(["sfx", "music"])


def encode_m4a(names):
    """Compressed copies of the stems (what index.html references; WAVs are local intermediates)."""
    import subprocess
    for n in names:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{ROOT}/assets/audio/{n}.wav", "-c:a", "aac", "-b:a", "256k",
                        f"{ROOT}/assets/audio/{n}.m4a"], check=True)


if __name__ == "__main__":
    main()
