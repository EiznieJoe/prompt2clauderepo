"""Potong rakaman skrin asal kepada klip langkah log masuk sahaja.

Sumber: assets/source/rakaman-skrin-asal.mp4 (576x1280, 110 s, tanpa audio).
Hanya 0-12.5 s yang berkaitan; bakinya (melayari aplikasi, panel notifikasi) dibuang.
Frame penting ditahan supaya murid sempat membaca. Maklumat peribadi dikaburkan:
  - senarai akaun Google (nama & emel)
  - nama, avatar dan emel di banner papan pemuka

    python3 tools/build_screen.py   ->  assets/video/skrin-login.mp4 (720x1600, 30 fps)
"""
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets/source/rakaman-skrin-asal.mp4")
OUT = os.path.join(ROOT, "assets/video/skrin-login.mp4")
TMP = os.path.join(ROOT, "assets/video/_tmp")
W, H, FPS = 720, 1600, 30

# kawasan kabur, dalam koordinat sumber 576x1280: (x, y, w, h)
BLUR_ACCOUNTS = [(126, 630, 316, 200)]
BLUR_BANNER = [(14, 222, 420, 66), (536, 138, 40, 40)]

# (jenis, masa sumber mula, tempoh output, kabur, label)
#   play  = main dari sumber selama tempoh
#   hold  = tahan frame pada masa sumber selama tempoh
SEGMENTS = [
    ("play", 0.20, 1.00, [], "landing"),
    ("hold", 1.20, 2.40, [], "L1 tahan: buka laman"),
    ("play", 1.20, 0.50, [], "landing"),
    ("hold", 1.70, 2.60, [], "L2 tahan: tekan Log Masuk ke DELIMa"),
    ("play", 1.70, 0.70, [], "menu terbuka"),
    ("hold", 2.60, 3.00, [], "L3 tahan: pilih Log masuk"),
    ("play", 2.60, 1.40, [], "tekan Log masuk"),
    ("play", 4.00, 0.40, BLUR_ACCOUNTS, "Google dimuatkan"),
    ("hold", 5.00, 4.60, BLUR_ACCOUNTS, "L4 tahan: pilih akaun"),
    ("play", 5.00, 1.00, BLUR_ACCOUNTS, "tekan akaun"),
    ("play", 9.00, 0.70, [], "mengesahkan"),
    ("play", 10.20, 2.30, BLUR_BANNER, "L5 papan pemuka"),
    ("hold", 12.50, 2.00, BLUR_BANNER, "papan pemuka tahan"),
]


def blur_filter(regions):
    """Rantai filter: kabur kuat setiap kawasan (koordinat sumber), kemudian skala."""
    if not regions:
        return f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p[v]"
    parts = ["[0:v]split=%d[base]%s" % (len(regions) + 1, "".join(f"[c{i}]" for i in range(len(regions))))]
    last = "base"
    for i, (x, y, w, h) in enumerate(regions):
        parts.append(f"[c{i}]crop={w}:{h}:{x}:{y},gblur=sigma=14:steps=4[b{i}]")
        parts.append(f"[{last}][b{i}]overlay={x}:{y}[o{i}]")
        last = f"o{i}"
    parts.append(f"[{last}]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p[v]")
    return ";".join(parts)


os.makedirs(TMP, exist_ok=True)
pieces, t, timeline = [], 0.0, []
for i, (kind, src_t, dur, regions, label) in enumerate(SEGMENTS):
    out = os.path.join(TMP, f"seg{i:02d}.mp4")
    if kind == "play":
        inp = ["-ss", f"{src_t:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    else:
        still = os.path.join(TMP, f"still{i:02d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src_t:.3f}", "-i", SRC, "-frames:v", "1", still], check=True)
        inp = ["-loop", "1", "-t", f"{dur:.3f}", "-i", still]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", blur_filter(regions), "-map", "[v]",
                    "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "14", "-preset", "medium", out], check=True)
    pieces.append(out)
    timeline.append({"start": round(t, 2), "end": round(t + dur, 2), "label": label})
    t += dur

lst = os.path.join(TMP, "list.txt")
with open(lst, "w") as f:
    f.writelines(f"file '{p}'\n" for p in pieces)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "16",
                "-preset", "medium", "-r", str(FPS), "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], check=True)
for p in pieces:
    os.remove(p)
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
json.dump(timeline, open(os.path.join(ROOT, "tools/screen-timeline.json"), "w"), indent=1, ensure_ascii=False)
for seg in timeline:
    print(f"{seg['start']:6.2f}-{seg['end']:6.2f}  {seg['label']}")
print("total", round(t, 2), "s ->", os.path.relpath(OUT, ROOT))
