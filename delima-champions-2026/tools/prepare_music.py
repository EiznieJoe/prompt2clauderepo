"""Sediakan muzik latar 60 s daripada "Epic" (kulakovka, Pixabay #624630).

Lagu asal 100 BPM, downbeat pertama 0.595 s. Dua potongan, kedua-duanya
pada fasa bar yang sama (beza ofset = 30 bar tepat), jadi rentak tak tersentak:

  A: lagu 4.435 s  -> video 0.00-55.30   (masuk penuh lagu 10.195 s = 5.76 s video,
                                          serentak pendedahan logo DELIMa)
  B: lagu 131.735 s -> video 55.30-60.00  (swell, hit penamat lagu 132.595 s =
                                          56.16 s video, serentak "WIN!", reda hingga 60 s)

    python3 tools/prepare_music.py   ->  assets/audio/stems/music.wav
"""
import os
import subprocess

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets/audio/source/kulakovka-epic-624630.mp3")
OUT = os.path.join(ROOT, "assets/audio/stems/music.wav")
SR = 48000
DUR = 60.0
OFF_A = 10.195 - 5.76          # 4.435
SPLICE = 55.30
OFF_B = 132.595 - 56.16        # 76.435  (OFF_B - OFF_A = 72.0 s = 30 bar @ 100 BPM)
XF = 0.06                      # silang-pudar pada sambungan

x = np.frombuffer(
    subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                   capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)


def take(track_start, n):
    s = int(round(track_start * SR))
    seg = x[s:s + n]
    return np.pad(seg, ((0, n - len(seg)), (0, 0)))


N = int(DUR * SR)
out = np.zeros((N, 2))
cut = int(SPLICE * SR)
xf = int(XF * SR)
a = take(OFF_A, cut + xf)
b = take(OFF_B + SPLICE - XF, N - cut + xf)
ramp = np.linspace(0, 1, xf)[:, None]
out[:cut] = a[:cut]
out[cut - xf:cut] = a[cut - xf:cut] * (1 - ramp) + b[:xf] * ramp
out[cut:] = b[xf:xf + N - cut]
# lapisan lembut penutup: gema hit penamat "dibekukan" (Paulstretch, fasa berbiji)
# supaya nota & warna bunyi sama dengan hit, kemudian reda perlahan hingga 60 s
HIT_TAIL = (132.70, 133.30)     # masa dalam lagu: sejurus selepas puncak hit
PAD_START, PAD_PEAK, PAD_FADE, PAD_DB = 56.30, 57.00, 58.80, -3.0


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
            ph = rng.uniform(0, 2 * np.pi, len(F))
            y[o:o + w, ch] += np.fft.irfft(np.abs(F) * np.exp(1j * ph), w) * window
        pos += src_hop
        o += hop
    return y[:out_len]


tail = take(HIT_TAIL[0], int((HIT_TAIL[1] - HIT_TAIL[0]) * SR))
n_pad = N - int(PAD_START * SR)
pad = paulstretch(tail, n_pad)
pad /= np.sqrt((pad[int(0.5 * SR):int(1.5 * SR)] ** 2).mean()) + 1e-9
pad *= np.sqrt((tail ** 2).mean()) * 10 ** (PAD_DB / 20)
tt = np.arange(n_pad) / SR + PAD_START
env = np.clip((tt - PAD_START) / (PAD_PEAK - PAD_START), 0, 1)
env *= 10 ** (-6 * np.clip((tt - PAD_PEAK) / (PAD_FADE - PAD_PEAK), 0, 1) / 20)  # turun 6 dB perlahan
env *= np.cos(np.clip((tt - PAD_FADE) / (DUR - PAD_FADE), 0, 1) * np.pi / 2)        # pudar habis tepat 60 s
out[int(PAD_START * SR):] += pad * env[:, None]

# pudar masuk pendek (potongan A bermula di tengah frasa intro)
fi = int(0.35 * SR)
out[:fi] *= np.linspace(0, 1, fi)[:, None]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-c:a", "pcm_s16le", OUT], input=out.astype(np.float32).tobytes(), check=True)
print("wrote", os.path.relpath(OUT, ROOT))
