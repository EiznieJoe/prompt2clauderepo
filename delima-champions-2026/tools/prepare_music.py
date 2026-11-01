"""Sediakan muzik latar 60 s daripada "Epic" (kulakovka, Pixabay #624630).

Lagu asal 100 BPM, downbeat pertama 0.595 s. Dua potongan, kedua-duanya
pada fasa bar yang sama (beza ofset = 29 bar tepat), jadi rentak tak tersentak:

  A: lagu 4.435 s  -> video 0.00-57.66   (masuk penuh lagu 10.195 s = 5.76 s video,
                                          serentak pendedahan logo DELIMa)
  B: lagu 131.695 s -> video 57.66-60.00  (jeda sekejap, swell, hit penamat lagu
                                          132.595 s = 58.56 s video)

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
SPLICE = 57.66
OFF_B = 132.595 - 58.56        # 74.035  (OFF_B - OFF_A = 69.6 s = 29 bar @ 100 BPM)
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
# pudar masuk pendek (potongan A bermula di tengah frasa intro)
fi = int(0.35 * SR)
out[:fi] *= np.linspace(0, 1, fi)[:, None]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-c:a", "pcm_s16le", OUT], input=out.astype(np.float32).tobytes(), check=True)
print("wrote", os.path.relpath(OUT, ROOT))
