"""Muzik + SFX untuk video tutorial log masuk (40 s) -> assets/audio/mix.wav

Muzik: "Epic" oleh kulakovka (Pixabay #624630), 100 BPM, disunting pada fasa bar yang sama:
  A: lagu 5.695 s  -> video 0-34.84   (masuk penuh lagu 10.195 s = 4.5 s video, peralihan ke "Sebelum Mula")
  B: lagu 131.735 s -> video 34.84-40 (hit penamat lagu 132.595 s = 35.7 s video, serentak "LUCKY LOGIN!")
     + gema hit dipanjangkan (Paulstretch berbiji) hingga reda tepat pada 40 s
SFX (Pixabay): klik pada setiap tekanan skrin, whoosh pada peralihan, kilauan pada "berjaya" dan hit.

    python3 tools/mix_audio.py
"""
import os
import re
import subprocess

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR, DUR = 48000, 40.0
N = int(SR * DUR)
t = np.arange(N) / SR


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


song = decode(os.path.join(ROOT, "assets/source/kulakovka-epic-624630.mp3"))


def take(start, n):
    s = int(round(start * SR))
    seg = song[s:s + n]
    return np.pad(seg, ((0, n - len(seg)), (0, 0)))


OFF_A, SPLICE, HIT = 10.195 - 4.5, 34.84, 35.7
OFF_B = 132.595 - HIT                  # OFF_B - OFF_A = 91.2 s = 38 bar @ 100 BPM
XF = int(0.06 * SR)
cut = int(SPLICE * SR)
music = np.zeros((N, 2))
a = take(OFF_A, cut + XF)
b = take(OFF_B + SPLICE - 0.06, N - cut + XF)
ramp = np.linspace(0, 1, XF)[:, None]
music[:cut] = a[:cut]
music[cut - XF:cut] = a[cut - XF:cut] * (1 - ramp) + b[:XF] * ramp
music[cut:] = b[XF:XF + N - cut]
fi = int(0.35 * SR)
music[:fi] *= np.linspace(0, 1, fi)[:, None]


def paulstretch(seg, out_len, win=0.5, seed=7):
    rng = np.random.default_rng(seed)
    w = int(win * SR) // 2 * 2
    window = np.hanning(w)
    hop = w // 4
    src_hop = max(1, (len(seg) - w) / max(1, (out_len - w) / hop))
    y = np.zeros((out_len + w, seg.shape[1]))
    pos, o = 0.0, 0
    while o + w <= len(y):
        i = int(pos) % max(1, len(seg) - w)
        for ch in range(seg.shape[1]):
            F = np.fft.rfft(seg[i:i + w, ch] * window)
            y[o:o + w, ch] += np.fft.irfft(np.abs(F) * np.exp(1j * rng.uniform(0, 2 * np.pi, len(F))), w) * window
        pos += src_hop
        o += hop
    return y[:out_len]


# lapisan lembut: gema hit penamat dibekukan, reda hingga 40 s
tail = take(132.70, int(0.6 * SR))
p0, pk, pf = HIT + 0.14, HIT + 0.84, DUR - 1.2
pad = paulstretch(tail, N - int(p0 * SR))
pad /= np.sqrt((pad[int(0.5 * SR):int(1.5 * SR)] ** 2).mean()) + 1e-9
pad *= np.sqrt((tail ** 2).mean()) * 10 ** (-3 / 20)
tt = np.arange(len(pad)) / SR + p0
env = np.clip((tt - p0) / (pk - p0), 0, 1)
env *= 10 ** (-6 * np.clip((tt - pk) / (pf - pk), 0, 1) / 20)
env *= np.cos(np.clip((tt - pf) / (DUR - pf), 0, 1) * np.pi / 2)
music[int(p0 * SR):] += pad * env[:, None]
music *= 10 ** (-3 / 20)

SFX = os.path.join(ROOT, "assets/audio/sfx")
# (fail, mula, gain dB) -- mula = puncak dikurangkan (whoosh 0.164, pop 0.122, klik 0.053, kilauan 0.03)
CUES = [
    ("whoosh.mp3", 4.25, -10),      # tajuk -> Sebelum Mula
    ("pop.mp3", 4.88, -16),         # kad ID muncul
    ("whoosh.mp3", 9.60, -10),      # telefon naik
    ("click-soft.mp3", 16.35, -6),  # tekan "Log Masuk ke DELIMa"
    ("click-soft.mp3", 21.40, -6),  # tekan "Log masuk"
    ("click-soft.mp3", 27.25, -6),  # tekan akaun
    ("sparkle.mp3", 28.42, -9),     # berjaya
    ("whoosh.mp3", 32.10, -10),     # ke kad penutup
    ("sparkle.mp3", 35.67, -8),     # LUCKY LOGIN! (hit penamat)
]
sfx = np.zeros((N, 2))
for f, at, g in CUES:
    x = decode(os.path.join(SFX, f)) * 10 ** (g / 20)
    s = int(at * SR)
    e = min(N, s + len(x))
    sfx[s:e] += x[: e - s]

mix = music + sfx
mix *= np.clip((DUR - t) / 0.2, 0, 1)[:, None]
out = os.path.join(ROOT, "assets/audio/mix.wav")
tmp = out + ".tmp.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", tmp],
               input=mix.astype(np.float32).tobytes(), check=True)
st = subprocess.run(["ffmpeg", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
gain = -16.0 - float(re.findall(r"I:\s+(-?[\d.]+) LUFS", st)[-1])
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af",
                f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=false",
                "-ar", str(SR), "-c:a", "pcm_s16le", out], check=True)
os.remove(tmp)
st = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print(os.path.relpath(out, ROOT), re.findall(r"I:\s+(-?[\d.]+) LUFS", st)[-1], "LUFS, true peak",
      re.findall(r"Peak:\s+(-?[\d.]+) dBFS", st)[-1], "dBFS")
