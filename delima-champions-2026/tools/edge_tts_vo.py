"""Jana narasi dengan suara Yasmin (ms-MY-YasminNeural) melalui edge-tts.

edge-tts guna perkhidmatan "Read Aloud" Microsoft Edge: percuma, tanpa kunci,
tetapi BUKAN API rasmi (boleh berhenti berfungsi bila-bila masa).
Perlu domain dibenarkan: speech.platform.bing.com

    pip install edge-tts
    python3 tools/edge_tts_vo.py                      # Yasmin
    python3 tools/edge_tts_vo.py --voice ms-MY-OsmanNeural

Output: assets/audio/vo/vo1.wav ... vo8.wav (48 kHz mono) daripada tools/vo-script.json.
"""
import asyncio
import json
import os
import subprocess
import sys

import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets/audio/vo")
args = sys.argv[1:]
VOICE = args[args.index("--voice") + 1] if "--voice" in args else "ms-MY-YasminNeural"
RATE = args[args.index("--rate") + 1] if "--rate" in args else "+4%"

# sebutan: edge-tts tidak terima SSML penuh, jadi ejaan dibetulkan terus dalam teks
SPOKEN = {
    "DELIMa": "Delima",
    "SK Rugading": "S K Rugading",
}


def spoken(text):
    for word, alias in SPOKEN.items():
        text = text.replace(word, alias)
    return text


async def main():
    script = json.load(open(os.path.join(ROOT, "tools/vo-script.json")))
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, line in enumerate(script, 1):
        raw = os.path.join(OUT_DIR, f"vo{i}-raw.mp3")
        await edge_tts.Communicate(spoken(line["text"]), VOICE, rate=RATE).save(raw)
        out = os.path.join(OUT_DIR, f"vo{i}.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
             "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
             "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
             "highpass=f=70,loudnorm=I=-18:TP=-2:LRA=7",
             "-ar", "48000", "-ac", "1", out],
            check=True,
        )
        os.remove(raw)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                                   capture_output=True, text=True).stdout)
        print(f"vo{i}.wav {dur:.2f}s  (tetingkap {line['window']})  {line['text']}")


asyncio.run(main())
