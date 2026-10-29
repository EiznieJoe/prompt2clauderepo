"""Mix muzik + SFX (+ VO) mengikut tools/cues.json.

    python3 tools/mix_audio.py            # tulis dua mix dalam assets/audio/
    python3 tools/mix_audio.py --peaks    # cetak masa puncak setiap fail SFX

Output:
  assets/audio/mix-dengan-vo.wav   muzik diduck di bawah narasi
  assets/audio/mix-tanpa-vo.wav    muzik + SFX sahaja (tiada duck)
Kedua-duanya ~-16 LUFS, true peak <= -1.5 dBTP.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_DIR = os.path.join(ROOT, "assets/audio/sfx")
DUR = 60.0
SR = 48000
cues = json.load(open(os.path.join(ROOT, "tools/cues.json")))


def decode(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def peak_time(x):
    m = np.abs(x).mean(axis=1)
    win = 480
    r = np.sqrt(np.convolve(m ** 2, np.ones(win) / win, "same"))
    return np.argmax(r) / SR


if "--peaks" in sys.argv:
    for f in sorted(os.listdir(SFX_DIR)):
        if f.endswith(".mp3"):
            print(f, round(peak_time(decode(os.path.join(SFX_DIR, f))), 3))
    sys.exit()

N = int(DUR * SR)
t = np.arange(N) / SR


def place(buf, x, at, gain_db=0.0, trim=0.0):
    x = x[int(trim * SR):] * (10 ** (gain_db / 20))
    s = int(round(at * SR))
    e = min(N, s + len(x))
    if e > s:
        buf[s:e] += x[: e - s]


music = decode(os.path.join(ROOT, cues["music"]["file"]))[:N]
music = np.pad(music, ((0, N - len(music)), (0, 0))) * (10 ** (cues["music"]["gain_db"] / 20))
# fade the tail so the film ends clean on the last frame
fade = np.clip((DUR - t) / 1.2, 0, 1) ** 1.5
music *= fade[:, None]

sfx = np.zeros((N, 2))
for c in cues["sfx"]:
    place(sfx, decode(os.path.join(SFX_DIR, c["file"])), c["at"], c.get("gain_db", 0), c.get("trim", 0))

vo = np.zeros((N, 2))
windows = []
for c in cues["vo"]:
    x = decode(os.path.join(ROOT, c["file"]))
    place(vo, x, c["at"], c.get("gain_db", 0))
    windows.append((c["at"], c["at"] + len(x) / SR))

# ducking envelope: smooth 0.25 s down, 0.4 s back up
duck = np.zeros(N)
for a, b in windows:
    down = np.clip((t - (a - 0.25)) / 0.25, 0, 1)
    up = np.clip(((b + 0.4) - t) / 0.4, 0, 1)
    duck = np.maximum(duck, np.minimum(down, up))
duck_gain = 10 ** (cues["music"]["duck_db"] * duck / 20)


def master(x, out, target=-16.0):
    tmp = out + ".tmp.wav"
    write_wav(tmp, x)
    stats = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", stats)[-1])
    gain = target - lufs
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af",
         f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=false",
         "-ar", str(SR), "-c:a", "pcm_s16le", out],
        check=True,
    )
    os.remove(tmp)
    check = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", check)[-1]
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", check)[-1]
    print(f"{os.path.relpath(out, ROOT)}: {i} LUFS, true peak {tp} dBFS")


def write_wav(path, x):
    pcm = np.clip(x, -4, 4).astype(np.float32).tobytes()
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", path],
        input=pcm, check=True,
    )


master(music * duck_gain[:, None] + sfx + vo, os.path.join(ROOT, "assets/audio/mix-dengan-vo.wav"))
master(music + sfx, os.path.join(ROOT, "assets/audio/mix-tanpa-vo.wav"))

if "--report" in sys.argv:
    def db(x):
        return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
    for a, b in windows:
        s, e = int(a * SR), int(b * SR)
        print(f"VO {a:5.1f}-{b:5.1f}: vo {db(vo[s:e]):6.1f} dB, music(ducked) {db((music * duck_gain[:, None])[s:e]):6.1f} dB, sfx {db(sfx[s:e]):6.1f}")
    for s in range(0, 60, 2):
        seg = slice(s * SR, (s + 2) * SR)
        print(s, f"music {db(music[seg]):6.1f} sfx {db(sfx[seg]):6.1f}")
