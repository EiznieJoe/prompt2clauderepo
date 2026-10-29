#!/usr/bin/env bash
# Suara panduan SINTETIK (eSpeak NG, Bahasa Melayu) untuk timing sahaja.
# Ganti fail assets/audio/vo-panduan/voN.wav dengan rakaman suara sebenar
# (nama fail sama), kemudian jalankan tools/mix_audio.py dan render semula.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out ../assets/audio/vo-panduan
i=1
while IFS= read -r line; do
  node tts.cjs "$line" out/vo$i-raw.wav ms+m3 155 48
  ffmpeg -y -v error -i out/vo$i-raw.wav -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,highpass=f=90,lowpass=f=7500,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-18:TP=-2:LRA=7" -ar 48000 -ac 1 ../assets/audio/vo-panduan/vo$i.wav
  i=$((i+1))
done < vo-lines.txt
