"""Muzik + SFX untuk video tutorial log masuk (40 s) -> assets/audio/mix.wav

Muzik: "Tutorial" oleh The Mountain (Pixabay #508040), 116 BPM, downbeat pada lagu 17.06 + 2.069k s.
  A: lagu 7.14 s  -> video 0-32.68  (intro ringan di bawah tajuk; bahagian penuh masuk 9.92 s,
                                     serentak telefon muncul)
  B: lagu 95.68 s -> video 32.68-40  (2 bar terakhir lagu di bawah kad penutup; bar terakhir
                                     lagu 97.75 s = 34.75 s video, serentak "LUCKY LOGIN!",
                                     kemudian reda semula jadi hingga 40 s)
Kedua-dua titik potongan jatuh pada downbeat.
SFX (Pixabay): klik pada setiap tekanan skrin, whoosh pada peralihan, kilauan pada "berjaya" dan "LUCKY LOGIN!".

Pilihan kedua: "Educational Presentation" oleh Monume (Pixabay #547934), 105 BPM:
  lagu 45.28 s -> video 0-40 (breakdown lembut di bawah tajuk; drop lagu 54.85 s = 9.57 s video,
  serentak telefon muncul; hit lagu 80.03 s = 34.75 s video, serentak "LUCKY LOGIN!";
  outro lembut dari 38.7 s, reda hingga 40 s)

    python3 tools/mix_audio.py                 # Tutorial (The Mountain) -> assets/audio/mix.wav
    python3 tools/mix_audio.py --lagu monume   # Monume -> assets/audio/mix-monume.wav
"""
import sys
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


LAGU = sys.argv[sys.argv.index("--lagu") + 1] if "--lagu" in sys.argv else "tutorial"
song = decode(os.path.join(ROOT, {
    "tutorial": "assets/source/the-mountain-tutorial-508040.mp3",
    "monume": "assets/source/monume-educational-presentation-547934.mp3",
}[LAGU]))


def take(start, n):
    s = int(round(start * SR))
    seg = song[s:s + n]
    return np.pad(seg, ((0, n - len(seg)), (0, 0)))


if LAGU == "monume":
    # satu potongan berterusan; breakdown -> drop -> bahagian penuh -> outro
    music = take(45.28, N)
    fi = int(0.6 * SR)
    music[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo0 = int(38.9 * SR)  # pudar keluar lembut atas outro lagu
    music[fo0:] *= (np.cos(np.linspace(0, 1, N - fo0) * np.pi / 2) ** 1.2)[:, None]
    music *= 10 ** (-3 / 20)
else:
    OFF_A, SPLICE, HIT = 7.14, 32.68, 34.75
    OFF_B = 95.68 - SPLICE
    XF = int(0.15 * SR)
    cut = int(SPLICE * SR)
    music = np.zeros((N, 2))
    a = take(OFF_A, cut + XF)
    b = take(OFF_B + SPLICE - 0.15, N - cut + XF)
    ramp = np.linspace(0, 1, XF)[:, None]
    music[:cut] = a[:cut]
    music[cut - XF:cut] = a[cut - XF:cut] * (1 - ramp) + b[:XF] * ramp
    music[cut:] = b[XF:XF + N - cut]
    fi = int(0.5 * SR)
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


    # lapisan lembut penutup: bunyi bar terakhir "dibekukan" supaya ada bunyi reda perlahan hingga 40 s
    tail = take(98.85, int(0.6 * SR))
    p0, pk, pf = 35.9, 36.8, DUR - 1.2
    pad = paulstretch(tail, N - int(p0 * SR))
    pad /= np.sqrt((pad[int(0.5 * SR):int(1.5 * SR)] ** 2).mean()) + 1e-9
    pad *= np.sqrt((tail ** 2).mean()) * 10 ** (-4 / 20)
    tt = np.arange(len(pad)) / SR + p0
    env = np.clip((tt - p0) / (pk - p0), 0, 1)
    env *= 10 ** (-6 * np.clip((tt - pk) / (pf - pk), 0, 1) / 20)
    env *= np.cos(np.clip((tt - pf) / (DUR - pf), 0, 1) * np.pi / 2)
    music[int(p0 * SR):] += pad * env[:, None]
    music *= 10 ** (-4 / 20)

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
    ("sparkle.mp3", 34.72, -8),     # LUCKY LOGIN! (bar terakhir / hit lagu)
]
sfx = np.zeros((N, 2))
for f, at, g in CUES:
    x = decode(os.path.join(SFX, f)) * 10 ** (g / 20)
    s = int(at * SR)
    e = min(N, s + len(x))
    sfx[s:e] += x[: e - s]

mix = music + sfx
mix *= np.clip((DUR - t) / 0.2, 0, 1)[:, None]
out = os.path.join(ROOT, "assets/audio/mix.wav" if LAGU == "tutorial" else f"assets/audio/mix-{LAGU}.wav")
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
