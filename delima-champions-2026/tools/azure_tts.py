"""Jana narasi sebenar dengan Azure Speech (suara neural Melayu Malaysia).

Perlu:
  AZURE_SPEECH_KEY     kunci sumber Azure Speech (simpan sebagai secret/env, jangan dalam repo)
  AZURE_SPEECH_REGION  cth. southeastasia
  Domain dibenarkan:   <region>.tts.speech.microsoft.com

    python3 tools/azure_tts.py                  # suara ms-MY-YasminNeural (perempuan)
    python3 tools/azure_tts.py --voice ms-MY-OsmanNeural   # lelaki
    python3 tools/azure_tts.py --list           # senarai suara ms-MY

Output: assets/audio/vo/vo1.wav ... vo8.wav (48 kHz mono), ejaan rasmi dalam
tools/vo-script.json; sebutan dibetulkan dengan <sub alias> (DELIMa -> "de-li-ma").
Lepas itu: halakan tools/cues.json vo[].file ke assets/audio/vo/, laraskan "at", dan
jalankan python3 tools/mix_audio.py.
"""
import json
import os
import subprocess
import sys
import urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.environ.get("AZURE_SPEECH_KEY")
REGION = os.environ.get("AZURE_SPEECH_REGION", "southeastasia")
OUT_DIR = os.path.join(ROOT, "assets/audio/vo")
args = sys.argv[1:]
VOICE = args[args.index("--voice") + 1] if "--voice" in args else "ms-MY-YasminNeural"
RATE = args[args.index("--rate") + 1] if "--rate" in args else "+4%"

if not KEY:
    sys.exit("AZURE_SPEECH_KEY tiada dalam environment.")

BASE = f"https://{REGION}.tts.speech.microsoft.com/cognitiveservices"

if "--list" in args:
    req = urllib.request.Request(f"{BASE}/voices/list", headers={"Ocp-Apim-Subscription-Key": KEY})
    for v in json.load(urllib.request.urlopen(req, timeout=30)):
        if v["Locale"].startswith("ms-"):
            print(v["ShortName"], v["Gender"], v.get("StyleList", ""))
    sys.exit()

# sebutan: teks rasmi -> alias yang dibaca
ALIASES = {
    "DELIMa": "Delima",
    "SK Rugading": "Es Ke Rugading",
}

script = json.load(open(os.path.join(ROOT, "tools/vo-script.json")))
os.makedirs(OUT_DIR, exist_ok=True)


def ssml(text):
    body = escape(text)
    for word, alias in ALIASES.items():
        body = body.replace(escape(word), f'<sub alias="{escape(alias)}">{escape(word)}</sub>')
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ms-MY">'
        f'<voice name="{VOICE}"><prosody rate="{RATE}">{body}</prosody></voice></speak>'
    )


for i, line in enumerate(script, 1):
    req = urllib.request.Request(
        f"{BASE}/v1",
        data=ssml(line["text"]).encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm",
            "User-Agent": "delima-champions-2026",
        },
    )
    raw = os.path.join(OUT_DIR, f"vo{i}-raw.wav")
    with urllib.request.urlopen(req, timeout=60) as r, open(raw, "wb") as f:
        f.write(r.read())
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
