"""Original procedural sound design + score for "Why Passenger Jets Are Not Electric".

  python3 tools/audio.py
    → assets/audio/sfx/<name>.wav   cinematic SFX library (synthesised: jets, electrics, impacts, HUD, risers)
    → assets/audio/sfx.m4a          every SFX placed from timeline/sfx_events.json
    → assets/audio/music.m4a        score (pads, pulse, felt-piano motif), ducked under the narration

Everything is generated with numpy/scipy — no samples, fully original, license-free.
"""
import json, os, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
TAIL = 3.5
rs = np.random.RandomState(11)


def T(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rs.uniform(-1, 1, int(d * SR))


def pink(d):
    n = int(d * SR)
    X = np.fft.rfft(rs.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X /= np.sqrt(np.maximum(f, 20))
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-9)


def brown(d):
    x = np.cumsum(rs.standard_normal(int(d * SR)))
    x = hp(x, 15)
    return x / (np.abs(x).max() + 1e-9)


def lp(x, f, o=4):
    return sosfilt(butter(o, min(f, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def hp(x, f, o=4):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, o=3):
    return sosfilt(butter(o, [lo, min(hi, SR / 2 - 100)], "band", fs=SR, output="sos"), x)


def norm(x, p=0.9):
    m = np.abs(x).max()
    return x * (p / m) if m > 0 else x


def expdec(n, k):
    return np.exp(-k * np.arange(n) / SR)


def fade(x, a=0.01, r=0.05):
    x = x.copy()
    na, nr = int(a * SR), int(r * SR)
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nr:
        x[-nr:] *= np.linspace(1, 0, nr)
    return x


def swell(n, peak=0.8, curve=2.0):
    """rise to `peak` (fraction of length) then fall."""
    k = np.arange(n) / n
    up = np.clip(k / peak, 0, 1) ** curve
    dn = np.clip((1 - k) / (1 - peak + 1e-9), 0, 1)
    return np.minimum(up, dn) if peak < 1 else up


def sine_sweep(f0, f1, d, curve="exp"):
    t = T(d)
    f = f0 * (f1 / f0) ** (t / d) if curve == "exp" else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def sweep_noise(d, f0, f1, q=0.6, segs=40, src=None):
    """noise through a band-pass whose centre glides f0→f1 (chunked, overlap-added)."""
    x = noise(d) if src is None else src
    out = np.zeros_like(x)
    L = len(x) // segs
    win = np.hanning(2 * L)
    for i in range(segs):
        f = f0 * (f1 / f0) ** (i / max(1, segs - 1))
        a = max(0, i * L - L // 2)
        seg = x[a:a + 2 * L]
        y = bp(seg, max(20, f * (1 - q)), f * (1 + q), 2)
        out[a:a + len(y)] += y * win[: len(y)]
    return out


IR = None


def reverb(x, rt=2.0, mix=0.3, bright=4000):
    global IR
    n = int(rt * SR)
    ir = lp(noise(rt), bright) * np.exp(-6.9 * np.arange(n) / n)
    ir /= np.sqrt((ir ** 2).sum())
    dry = np.concatenate([x, np.zeros(n)])
    wet = fftconvolve(x, ir)[: len(dry)]
    wet = np.pad(wet, (0, len(dry) - len(wet)))
    return dry * (1 - mix) + wet * mix * 3


def piano(f, d=3.5, vel=1.0):
    t = T(d)
    x = sum(a * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * (1.2 + 0.9 * h)) for h, a in
            ((1, 1), (2, 0.45), (3, 0.25), (4, 0.12), (5, 0.07)))
    x *= (1 - np.exp(-t * 300))
    return lp(x, 2400) * vel


def pad(freqs, d, bright=1200, detune=0.004):
    t = T(d)
    x = np.zeros_like(t)
    for f in freqs:
        for dt in (-detune, 0, detune):
            ph = rs.rand() * 6.28
            x += 2 * (((f * (1 + dt) * t + ph / 6.28) % 1) - 0.5)
    return lp(x, bright) / len(freqs)


NOTE = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def hz(n):
    name, octv = n[:-1], int(n[-1])
    return 440 * 2 ** ((NOTE[name] + 12 * (octv - 4)) / 12)


# =================================================================== SFX library
def library():
    L = {}
    # --- transitions
    L["whoosh"] = norm(sweep_noise(0.7, 300, 3000) * swell(int(0.7 * SR), 0.6), 0.7)
    L["whoosh_big"] = norm(reverb(sweep_noise(1.3, 120, 1600) * swell(int(1.3 * SR), 0.55) + 0.4 * lp(brown(1.3), 120) * swell(int(1.3 * SR), 0.5), 1.4, 0.25), 0.85)
    L["whoosh_up"] = norm(sweep_noise(1.1, 200, 5000) * swell(int(1.1 * SR), 0.9), 0.6)
    L["riser"] = norm(sweep_noise(2.6, 150, 5000) * swell(int(2.6 * SR), 1.0, 2.5) + 0.35 * sine_sweep(80, 320, 2.6) * swell(int(2.6 * SR), 1.0, 2.5), 0.75)
    t = T(3.6)
    chord = sum(np.sin(2 * np.pi * hz(n) * t) for n in ("D3", "F#3", "A3", "D4")) * np.exp(-t * 0.9)
    L["riser_resolve"] = norm(np.concatenate([L["riser"][: int(1.6 * SR)] * 0.7, lp(chord, 2500) * 0.6]), 0.7)
    # shepard tone (endlessly rising), 6 s
    d = 6.0
    t = T(d)
    x = np.zeros_like(t)
    for k in range(6):
        oc = (k + t / d * 1.5) % 6
        f = 40 * 2 ** oc
        a = np.exp(-((oc - 3) ** 2) / 2.5)
        x += a * np.sin(2 * np.pi * np.cumsum(f) / SR)
    L["shepard"] = norm(x * swell(len(t), 1.0, 1.2), 0.6)
    # --- low end
    def boom(f0=55, f1=30, d=3.2, body=1.0):
        t = T(d)
        f = f1 + (f0 - f1) * np.exp(-t * 6)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4)
        mid = np.sin(2 * np.pi * np.cumsum(f * 2.2) / SR) * np.exp(-t * 6) * 0.35 * body  # audible on phones
        tr = lp(noise(d), 1800) * np.exp(-t * 30) * 0.5
        return norm(reverb(s + mid + tr, 2.4, 0.2, 2500), 0.95)
    L["boom"] = boom()
    L["hit"] = boom(70, 42, 1.8, 1.3)
    L["hit_soft"] = norm(boom(80, 50, 1.4, 1.0) * 0.6, 0.6)
    L["hit_dry"] = norm(boom(90, 45, 0.9, 1.4)[: int(0.9 * SR)], 0.85)
    L["sub"] = norm(sine_sweep(70, 28, 1.6) * expdec(int(1.6 * SR), 2.2), 0.9)
    L["pulse"] = norm(np.sin(2 * np.pi * 55 * T(0.35)) * expdec(int(0.35 * SR), 9) + 0.3 * np.sin(2 * np.pi * 110 * T(0.35)) * expdec(int(0.35 * SR), 14), 0.8)
    L["rumble"] = norm(lp(brown(5.0), 90) * swell(int(5 * SR), 0.3), 0.8)
    L["cut"] = norm(lp(noise(0.25), 600) * expdec(int(0.25 * SR), 25), 0.6)
    # --- jets
    def jet(d, n_lp=900, whine=(900, 2600), rise=0.0, amp_env=None, tone=0.18):
        t = T(d)
        body = lp(pink(d), n_lp) + 0.6 * lp(brown(d), 160)
        f = whine[0] + (whine[1] - whine[0]) * np.clip(t / max(rise, 1e-3), 0, 1) ** 1.5 if rise else np.full_like(t, whine[1])
        f = f * (1 + 0.004 * np.sin(2 * np.pi * 5 * t))
        wh = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
        x = body + tone * wh
        if amp_env is not None:
            x *= amp_env
        return x
    d = 3.8
    L["spool"] = norm(jet(d, 500, (250, 2400), rise=3.6, amp_env=np.linspace(0.05, 1, int(d * SR)) ** 1.6, tone=0.4), 0.8)
    d = 6.0
    e = np.concatenate([np.linspace(0.3, 1, int(0.6 * SR)), np.ones(int(3.4 * SR)), np.linspace(1, 0, int(2.0 * SR))])
    L["roar"] = norm(jet(d, 1400, (2000, 2000), amp_env=e, tone=0.08), 0.95)
    d = 2.8
    t = T(d)
    dop = 1.5 - np.tanh((t - 1.0) * 3) * 0.5
    L["flyby"] = norm(sweep_noise(d, 2500, 300, 0.7, src=pink(d)) * np.exp(-((t - 1.0) ** 2) / 0.35) + 0.15 * np.sin(2 * np.pi * np.cumsum(1800 * dop) / SR) * np.exp(-((t - 1.0) ** 2) / 0.2), 0.85)
    L["flyover"] = norm(lp(pink(3.5), 600) * swell(int(3.5 * SR), 0.5), 0.4)
    L["turbine"] = norm(jet(4.0, 700, (3200, 3200), tone=0.3) * swell(int(4 * SR), 0.2), 0.6)
    L["climb"] = norm(jet(4.5, 900, (1800, 2100), rise=4.5, tone=0.15) * swell(int(4.5 * SR), 0.3), 0.7)
    L["cabin"] = norm(lp(pink(4.0), 350) + 0.2 * bp(noise(4.0), 200, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * T(4.0))), 0.7)
    L["burn"] = norm(lp(pink(2.2), 1200) * swell(int(2.2 * SR), 0.35) + 0.25 * (rs.rand(int(2.2 * SR)) > 0.9985) * noise(2.2), 0.75)
    L["burn_rise"] = norm(sweep_noise(2.6, 120, 1400, 0.8, src=pink(2.6)) * swell(int(2.6 * SR), 0.9) + 0.4 * sine_sweep(60, 180, 2.6) * swell(int(2.6 * SR), 0.9), 0.85)
    L["heat"] = norm(bp(pink(2.0), 300, 2200) * swell(int(2 * SR), 0.3) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * T(2.0))), 0.6)
    # --- electrics (cyan)
    def humtone(d, f=60, harm=(1, 2, 3, 4, 6), env=None):
        t = T(d)
        x = sum(np.sin(2 * np.pi * f * h * t * (1 + 0.0007 * h)) / h for h in harm)
        x += 0.15 * bp(noise(d), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 120 * t))
        return x * (env if env is not None else 1)
    L["hum"] = norm(humtone(2.5, env=swell(int(2.5 * SR), 0.3)), 0.5)
    L["hum_build"] = norm(humtone(3.0, env=np.linspace(0, 1, int(3 * SR)) ** 2), 0.6)
    t = T(3.0)
    L["hum_down"] = norm(np.sin(2 * np.pi * np.cumsum(120 * (1 - 0.5 * t / 3)) / SR) * np.linspace(1, 0, len(t)) + 0.3 * np.sin(2 * np.pi * 60 * t), 0.5)
    L["charge"] = norm(np.concatenate([sine_sweep(300, 1600, 0.25) * np.linspace(0.2, 1, int(0.25 * SR)), humtone(0.6, 120) * expdec(int(0.6 * SR), 4)]), 0.6)
    L["zip"] = norm(bp(2 * ((np.cumsum(np.linspace(200, 2400, int(0.22 * SR))) / SR) % 1) - 1, 300, 6000) * np.linspace(0.6, 1, int(0.22 * SR)), 0.7)
    L["surge"] = norm(humtone(1.6, 50, (1, 2, 3, 5, 7)) * np.linspace(0, 1, int(1.6 * SR)) ** 2 + 0.4 * sweep_noise(1.6, 300, 4000) * np.linspace(0, 1, int(1.6 * SR)), 0.8)
    t = T(2.2)
    saw = 2 * ((100 * t) % 1) - 1
    L["buzz"] = norm(lp(saw, 1200) * swell(len(t), 0.2), 0.45)
    t = T(3.5)
    L["motor"] = norm((np.sin(2 * np.pi * np.cumsum(np.minimum(400 + 900 * t, 1700)) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(np.minimum(800 + 1800 * t, 3400)) / SR)) * swell(len(t), 0.4) * 0.7 + 0.2 * lp(pink(3.5), 400), 0.55)
    t = T(2.4)
    L["racer"] = norm(np.sin(2 * np.pi * np.cumsum(2600 * (1.25 - np.tanh((t - 0.9) * 4) * 0.25)) / SR) * np.exp(-((t - 0.9) ** 2) / 0.25) + sweep_noise(2.4, 3000, 600, src=pink(2.4)) * np.exp(-((t - 0.9) ** 2) / 0.2), 0.8)
    # --- interface
    t = T(0.12)
    L["hud"] = norm(np.concatenate([np.sin(2 * np.pi * 2400 * t[:int(0.05 * SR)]) * expdec(int(0.05 * SR), 60), np.zeros(int(0.02 * SR)),
                                    np.sin(2 * np.pi * 3200 * t[:int(0.05 * SR)]) * expdec(int(0.05 * SR), 60)]), 0.4)
    L["click"] = norm(bp(noise(0.03), 2000, 8000) * expdec(int(0.03 * SR), 200), 0.5)
    L["tick"] = norm(np.sin(2 * np.pi * 2000 * T(0.04)) * expdec(int(0.04 * SR), 120), 0.35)
    L["tick_up"] = norm(np.sin(2 * np.pi * 1600 * T(0.06)) * expdec(int(0.06 * SR), 70) + 0.5 * np.sin(2 * np.pi * 3200 * T(0.06)) * expdec(int(0.06 * SR), 90), 0.4)
    L["blip"] = norm(np.sin(2 * np.pi * 1300 * T(0.09)) * expdec(int(0.09 * SR), 45), 0.4)
    L["node"] = norm(np.sin(2 * np.pi * 880 * T(0.25)) * expdec(int(0.25 * SR), 14) + 0.3 * np.sin(2 * np.pi * 1320 * T(0.25)) * expdec(int(0.25 * SR), 20), 0.45)
    roll = np.zeros(int(2.2 * SR))
    for k in range(40):
        p = int((1 - (1 - k / 40) ** 1.6) * 2.0 * SR)
        roll[p:p + len(L["tick"])] += L["tick"][: len(roll) - p] * 0.8
    L["tick_roll"] = norm(roll, 0.4)
    tk = np.zeros(int(2.2 * SR))
    for k in range(14):
        p = int((k / 14) ** 1.7 * 2.0 * SR)
        c = bp(noise(0.02), 1500, 6000) * expdec(int(0.02 * SR), 250)
        tk[p:p + len(c)] += c * (1 - k / 16)
    L["ticks"] = norm(tk, 0.5)
    dom = np.zeros(int(2.6 * SR))
    for k in range(60):
        p = int((1 - (1 - k / 60) ** 2.2) * 2.4 * SR)
        c = bp(noise(0.03), 800, 5000) * expdec(int(0.03 * SR), 150)
        dom[p:p + len(c)] += c * (0.5 + 0.5 * k / 60)
    L["dominoes"] = norm(dom, 0.55)
    t = T(1.2)
    tone = lambda f: np.sin(2 * np.pi * f * t[: int(0.35 * SR)]) * expdec(int(0.35 * SR), 6)
    L["caution"] = norm(np.concatenate([tone(1200), tone(900), np.zeros(int(0.1 * SR)), tone(1200), tone(900)]), 0.45)
    L["radar"] = norm(reverb(np.sin(2 * np.pi * 1100 * T(0.3)) * expdec(int(0.3 * SR), 10), 1.5, 0.4), 0.35)
    L["draw"] = norm(bp(noise(1.0), 2500, 7000) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * T(1.0))) * swell(int(SR), 0.2), 0.25)
    t = T(1.8)
    L["deflate"] = norm(np.sin(2 * np.pi * np.cumsum(600 * np.exp(-t * 1.5) + 80) / SR) * np.linspace(1, 0, len(t)), 0.5)
    L["glitch"] = norm(np.concatenate([bp(noise(0.05), 500 + 300 * k, 9000) * (k % 2) + np.sin(2 * np.pi * (300 + 200 * k) * T(0.05)) * ((k + 1) % 2) for k in range(12)]), 0.55)
    # --- foley / mechanical
    def metal(f0=220, d=1.6, parts=(1, 2.35, 4.06, 5.41), k=3.0):
        t = T(d)
        return sum(np.sin(2 * np.pi * f0 * p * t) * np.exp(-t * k * (1 + i * 0.6)) / (i + 1) for i, p in enumerate(parts))
    t = T(1.8)
    thud = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 8) + 38) / SR) * np.exp(-t * 4)
    L["pallet"] = norm(reverb(thud + 0.35 * metal(180, 1.8, k=4) + 0.4 * lp(noise(1.8), 2000) * np.exp(-t * 35), 1.6, 0.25), 0.95)
    L["thud_heavy"] = norm(reverb(thud * 1.2 + 0.5 * lp(brown(1.8), 200) * np.exp(-t * 3), 1.2, 0.2), 0.95)
    t = T(1.4)
    L["clunk"] = norm(reverb(np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 20) + 60) / SR) * np.exp(-t * 10) + 0.5 * bp(noise(1.4), 1500, 6000) * np.exp(-t * 80), 2.8, 0.45), 0.9)
    L["glass"] = norm(metal(2100, 1.2, (1, 1.52, 2.21, 2.9), 5) + 0.3 * bp(noise(1.2), 4000, 9000) * expdec(int(1.2 * SR), 60), 0.5)
    L["clack"] = norm(metal(900, 0.5, (1, 1.8, 3.1), 18) + 0.5 * bp(noise(0.5), 1500, 6000) * expdec(int(0.5 * SR), 80), 0.55)
    L["snap"] = norm(bp(noise(0.06), 1200, 7000) * expdec(int(0.06 * SR), 120) + 0.4 * np.sin(2 * np.pi * 380 * T(0.06)) * expdec(int(0.06 * SR), 60), 0.6)
    L["lock"] = norm(np.concatenate([L["snap"], np.zeros(int(0.05 * SR)), metal(400, 0.5, k=14)]), 0.6)
    t = T(1.3)
    L["creak"] = norm(bp(2 * ((np.cumsum(70 + 25 * np.sin(2 * np.pi * 1.3 * t)) / SR) % 1) - 1, 200, 2500) * swell(len(t), 0.4) * (0.6 + 0.4 * (rs.rand(len(t)) > 0.5)), 0.5)
    L["strain"] = norm(np.concatenate([L["creak"], L["creak"][::-1] * 0.7]) + 0.3 * lp(brown(2.6), 150), 0.7)
    t = T(1.0)
    L["screech"] = norm(bp(noise(1.0), 1800, 4200) * (0.6 + 0.4 * np.sin(2 * np.pi * 60 * t)) * np.exp(-t * 2.2), 0.6)
    L["chirp"] = norm(L["screech"][: int(0.35 * SR)] * np.linspace(1, 0, int(0.35 * SR)), 0.45)
    t = T(1.6)
    sl = lp(noise(1.6), 900) * swell(len(t), 0.3)
    for k in range(14):
        p = rs.randint(0, int(1.4 * SR))
        b = np.sin(2 * np.pi * np.cumsum(np.linspace(300, 900 + rs.rand() * 600, int(0.05 * SR))) / SR) * expdec(int(0.05 * SR), 60)
        sl[p:p + len(b)] += b * 0.6
    L["liquid"] = norm(sl, 0.5)
    t = T(3.2)
    L["drain"] = norm(lp(noise(3.2), 600) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) * np.linspace(1, 0.3, len(t)), 0.35)
    L["water"] = norm(hp(pink(3.0), 400) * swell(int(3 * SR), 0.2) + 0.3 * lp(brown(3.0), 300), 0.65)
    t = T(4.0)
    blade = (0.55 + 0.45 * np.sin(2 * np.pi * 38 * t)) ** 2
    L["prop"] = norm(lp(pink(4.0), 1400) * blade * swell(len(t), 0.2) + 0.2 * np.sin(2 * np.pi * 76 * t), 0.5)
    L["props_quiet"] = norm(lp(pink(4.0), 2200) * (0.7 + 0.3 * np.sin(2 * np.pi * 52 * t)) * swell(len(t), 0.25), 0.35)
    t = T(0.6)
    L["wrench"] = norm(bp(2 * ((t * 55) % 1) - 1 + 0.3 * noise(0.6), 300, 3000) * swell(len(t), 0.1), 0.45)
    t = T(2.4)
    L["pump"] = norm(lp(noise(2.4), 500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 3 * t))) * 0.8 + 0.2 * np.sin(2 * np.pi * 50 * t), 0.4)
    L["cryo"] = norm(hp(noise(2.4), 3000) * swell(len(t), 0.15), 0.4)
    L["mech_open"] = norm(np.concatenate([bp(2 * ((T(0.8) * 90) % 1) - 1, 200, 2000) * swell(int(0.8 * SR), 0.5) * 0.6, L["clunk"][: int(0.9 * SR)]]), 0.7)
    t = T(3.5)
    L["doors"] = norm(lp(brown(3.5), 220) * swell(len(t), 0.2) + 0.25 * bp(noise(3.5), 300, 1200) * (rs.rand(len(t)) > 0.6), 0.75)
    # --- ambiences
    t = T(9.0)
    apu = np.sin(2 * np.pi * 3100 * t) * 0.04 + np.sin(2 * np.pi * 410 * t) * 0.05
    L["amb_airport"] = norm(lp(pink(9.0), 900) * 0.5 + apu + 0.3 * lp(brown(9.0), 140), 0.45)
    L["hangar"] = norm(reverb(lp(pink(6.0), 500) * 0.3 + 0.03 * np.sin(2 * np.pi * 120 * T(6.0)), 2.5, 0.4)[: int(6 * SR)], 0.35)
    L["room"] = norm(lp(pink(5.0), 250) * 0.4, 0.25)
    L["wind"] = norm(bp(pink(5.0), 200, 1800) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * T(5.0))), 0.5)
    L["wind_high"] = norm(bp(pink(5.0), 400, 3000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * T(5.0))) + 0.4 * lp(brown(5.0), 120), 0.55)
    L["industrial"] = norm(lp(pink(4.0), 600) * 0.4 + 0.05 * np.sin(2 * np.pi * 100 * T(4.0)) + 0.4 * L["clack"].tolist().__len__() * 0, 0.4)
    bird = np.zeros(int(4 * SR))
    for k in range(9):
        p = rs.randint(0, int(3.5 * SR))
        n = int(0.12 * SR)
        f = 3200 + 900 * np.sin(np.linspace(0, 3, n) * (2 + rs.rand() * 3))
        bird[p:p + n] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.hanning(n) * 0.5
    L["birds"] = norm(bird, 0.25)
    L["eerie"] = norm(pad([hz("A4"), hz("D#5")], 4.0, 3000, 0.006) * swell(int(4 * SR), 0.4), 0.25)
    L["drone_l"] = norm(pad([hz("D2"), hz("A2")], 4.0, 400) * swell(int(4 * SR), 0.3), 0.4)
    # --- musical one-shots
    L["piano"] = norm(reverb(piano(hz("D4"), 4.0) + 0.5 * piano(hz("A3"), 4.0), 3.0, 0.35), 0.6)
    L["final_note"] = norm(reverb(piano(hz("D3"), 5.0) + 0.6 * pad([hz("D2"), hz("A2"), hz("F#3")], 5.0, 900) * expdec(int(5 * SR), 0.6), 4.0, 0.4), 0.8)
    L["pad"] = norm(pad([hz("D3"), hz("A3"), hz("F#4")], 3.5, 1400) * swell(int(3.5 * SR), 0.4), 0.45)
    L["silence_pad"] = norm(pad([hz("D2"), hz("A2")], 6.0, 500) * swell(int(6 * SR), 0.5), 0.25)
    L["swell"] = norm(pad([hz("D3"), hz("A3"), hz("E4")], 2.4, 2000) * np.linspace(0, 1, int(2.4 * SR)) ** 2, 0.5)
    L["chime"] = norm(reverb(sum(np.sin(2 * np.pi * hz(n) * T(1.2)) * expdec(int(1.2 * SR), 4) for n in ("A5", "E6")), 1.5, 0.3), 0.35)
    return L


# =================================================================== score
SECTION_MOOD = {"s01": "hook", "s02": "airy", "s03": "drive", "s04": "lab", "s05": "dark", "s06": "hope", "s07": "finale"}


def score(T_, total):
    """One bed per section; returns stereo array."""
    N = int(total * SR)
    out = np.zeros((N + 4 * SR, 2))
    bpm = 90
    beat = 60 / bpm
    prog = {"hook": [("D2", "A2", "F3")], "airy": [("D3", "A3", "E4"), ("B2", "F#3", "D4")], "drive": [("D2", "A2", "F3"), ("A#1", "F2", "D3"), ("C2", "G2", "E3")],
            "lab": [("D2", "A2")], "dark": [("D2", "G#2", "C3"), ("C#2", "G2", "A#2")], "hope": [("D3", "F#3", "A3"), ("B2", "D3", "F#3"), ("G2", "B2", "D3"), ("A2", "C#3", "E3")],
            "finale": [("D3", "F#3", "A3", "E4"), ("G2", "B2", "D3", "F#3")]}
    motif = ["D4", "F4", "A4", "E4"]
    for i, sec in enumerate(T_["sections"]):
        mood = SECTION_MOOD[sec["id"]]
        st = sec["start"]
        en = sec["end"] + (TAIL if i == len(T_["sections"]) - 1 else 0)
        d = en - st + 1.0
        n = int(d * SR)
        bed = np.zeros(n)
        chords = prog[mood]
        bar = 4 * beat
        k = 0
        while k * 2 * bar < d:
            ch = chords[k % len(chords)]
            seg = pad([hz(c) for c in ch], 2 * bar + 0.6, {"dark": 500, "lab": 700}.get(mood, 1200))
            seg *= swell(len(seg), 0.15, 1.0)
            a = int(k * 2 * bar * SR)
            bed[a:a + len(seg)] += seg[: n - a] * 0.5
            k += 1
        # pulse (sub kick on beats) for drive / lab / dark
        if mood in ("drive", "lab", "dark", "hook"):
            pk = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-T(0.4) * 18) + 38) / SR) * expdec(int(0.4 * SR), 9)
            step = beat if mood != "lab" else beat
            nb = int(d / step)
            for b in range(nb):
                a = int(b * step * SR)
                g = 0.55 if mood == "drive" else 0.4
                bed[a:a + len(pk)] += pk[: n - a] * g
        # glassy arpeggio in drive / hope
        if mood in ("drive", "hope", "finale", "airy"):
            notes = [hz(x) for x in (motif if mood != "hope" else ["D5", "F#5", "A5", "E5"])]
            step = beat / 2 if mood == "drive" else beat
            for b in range(int(d / step)):
                f = notes[b % 4] * (0.5 if mood == "airy" else 1)
                p = piano(f, 1.2, 0.25 if mood != "drive" else 0.18)
                a = int(b * step * SR)
                bed[a:a + len(p)] += p[: n - a]
        if mood == "finale":
            bed += 0.6 * lp(pad([hz("D2"), hz("A2")], d, 300), 300)[:n]
        e = np.ones(n)
        f = int(1.0 * SR)
        e[:f] = np.linspace(0, 1, f)
        e[-f:] = np.linspace(1, 0, f)
        if mood == "finale":
            e[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR)) ** 2
        bed = reverb(bed * e, 2.5, 0.25, 3500)[:n]
        a = int(st * SR)
        out[a:a + n, 0] += bed[: len(out) - a]
        out[a:a + n, 1] += np.roll(bed, int(0.012 * SR))[: len(out) - a]
    out = out[:N]
    return out / (np.abs(out).max() + 1e-9)


def main():
    T_ = json.load(open(f"{ROOT}/timeline/timing.json"))
    total = T_["duration"] + TAIL
    N = int(np.ceil(total * SR))
    os.makedirs(f"{ROOT}/assets/audio/sfx", exist_ok=True)
    L = library()
    for k, v in L.items():
        sf.write(f"{ROOT}/assets/audio/sfx/{k}.wav", fade(np.asarray(v, np.float32), 0.0, 0.02), SR)
    ev = json.load(open(f"{ROOT}/timeline/sfx_events.json"))
    sfx = np.zeros((N, 2))
    miss = set()
    for e in ev:
        x = L.get(e["name"])
        if x is None:
            miss.add(e["name"])
            continue
        s = int(e["abs"] * SR)
        if s < 0 or s >= N:
            continue
        x = fade(np.asarray(x), 0.0, 0.02)[: N - s] * e.get("gain", 1) * 0.42
        pan = 0.5 + 0.12 * np.sin(e["abs"] * 1.7)  # slight stereo spread per event
        sfx[s:s + len(x), 0] += x * (1 - pan) * 1.6
        sfx[s:s + len(x), 1] += x * pan * 1.6
    if miss:
        print("WARNING unknown sfx:", sorted(miss))
    pk = np.abs(sfx).max()
    if pk > 0.95:
        sfx *= 0.95 / pk
    sf.write(f"{ROOT}/assets/audio/sfx.wav", sfx.astype(np.float32), SR)
    print("sfx events:", len(ev))
    # ---- music, side-chained under the narration
    music = score(T_, total)
    vo, vsr = sf.read(f"{ROOT}/assets/audio/narration.wav", dtype="float32")
    if vo.ndim > 1:
        vo = vo.mean(1)
    vo = np.interp(np.arange(N) * vsr / SR, np.arange(len(vo)), vo, right=0)
    env = np.sqrt(lp(vo ** 2, 6, 2).clip(0))
    env = env / (env.max() + 1e-9)
    talk = np.clip(env * 6, 0, 1)
    # smooth attack/release
    from scipy.signal import lfilter
    a = np.exp(-1 / (0.25 * SR))
    talk = lfilter([1 - a], [1, -a], talk)
    gain_db = -16 - 10 * talk  # −16 dB in gaps, −26 dB under the voice
    music *= (10 ** (gain_db / 20))[:, None]
    music[: int(0.5 * SR)] *= np.linspace(0, 1, int(0.5 * SR))[:, None]
    sf.write(f"{ROOT}/assets/audio/music.wav", music.astype(np.float32), SR)
    print("music written", round(total, 2), "s")
    for n in ("sfx", "music"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{ROOT}/assets/audio/{n}.wav", "-c:a", "aac", "-b:a", "256k", f"{ROOT}/assets/audio/{n}.m4a"], check=True)


if __name__ == "__main__":
    main()
