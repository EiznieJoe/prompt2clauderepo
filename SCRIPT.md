# Skrip & Timing — KelasQuest Promo 30s

Sumber: `assets/source/original-audio.wav` (45.4s). Untuk muat 30 saat:

1. Buang bahagian guru (asal 28.06s – 35.85s): *"Guru pula boleh menguruskan ganjaran, memantau perkembangan dan meningkatkan motivasi murid dengan lebih mudah."*
2. Cantum baki audio, kemudian percepat 1.27x (`atempo`, pitch kekal).
3. Hasil: `assets/voiceover.wav`, 29.3s.

```bash
ffmpeg -i assets/source/original-audio.wav -filter_complex \
  "[0]atrim=0:28.06,asetpts=N/SR/TB[a];[0]atrim=35.85:45.0,asetpts=N/SR/TB[b];[a][b]concat=n=2:v=0:a=1,atempo=1.27,afade=t=out:st=29.1:d=0.2[o]" \
  -map "[o]" -ar 44100 assets/voiceover.wav
```

| Masa (s) | Voiceover | Visual | Highlight |
|---|---|---|---|
| 0.0 – 7.4 | Bayangkan sebuah kelas di mana setiap usaha murid dihargai dan setiap pencapaian diraikan. | Teks kinetik, confetti | **dihargai**, **diraikan** |
| 7.2 – 7.9 | — | Selingan: jalur warna sapu | |
| 7.6 – 14.7 | Memperkenalkan KelasQuest, aplikasi ganjaran digital interaktif yang menjadikan pembelajaran lebih menyeronokkan. | Logo masuk, tagline | **ganjaran digital**, **menyeronokkan** |
| 14.6 – 15.3 | — | Selingan: jalur warna sapu | |
| 15.15 – 22.1 | Dengan imbasan QR, murid boleh mengumpul syiling, memperoleh lencana pencapaian, menaikkan level dan menebus hadiah menarik. | 5 kad ciri muncul ikut sebutan | **imbasan QR**, **syiling**, **lencana pencapaian**, **naik level**, **hadiah menarik** |
| 22.0 | — | Selingan: kilat putih | |
| 22.1 – 25.7 | KelasQuest. Belajar. Kumpul. Naik level. | Logo hentak, 3 blok slogan | Belajar / Kumpul / Naik Level |
| 25.5 – 30.0 | Kerana setiap usaha kecil membawa kepada kejayaan besar. | Tangga naik + bintang, CTA + URL | **kejayaan besar** |

Masa diambil daripada transkripsi Whisper (small) + pengesanan jeda `silencedetect`, jadi anggaran ±0.1s.
