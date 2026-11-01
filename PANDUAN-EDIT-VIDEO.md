# Panduan Edit Video DELIMa — SK Rugading, Tuaran

Rujukan untuk kerja edit video akan datang. Ia dikumpul daripada dua projek yang dah siap dan diluluskan:

| Projek | Folder | Format | Fail siap |
|---|---|---|---|
| Promo DELIMa Champions 2026 | `delima-champions-2026/` | 1920×1080, 60 s | `output/…-narasi-rakaman.mp4`, `…-narasi-gemini.mp4`, `…-muzik-sfx.mp4` |
| Tutorial Cara Log Masuk DELIMa 3.0 (Lucky Login) | `delima-login-tutorial/` | 1080×1920 menegak, 40 s | `output/cara-log-masuk-delima-3.mp4` |

Video baru dalam siri ini perlu ikut gaya, aliran kerja dan pilihan di bawah.

---

## 1. Pilihan pengguna (wajib diikut)

- **Bahasa:** Bahasa Melayu Malaysia yang santai. Istilah teknikal kekal dalam Bahasa Inggeris.
- **Percuma sahaja.** Jangan guna perkhidmatan berbayar atau yang perlukan kad kredit tanpa tanya dulu.
- **Muzik dari Pixabay, dipilih dan dimuat naik sendiri oleh pengguna.** Claude tak boleh muat turun dari Pixabay: laman tu pulangkan 403 anti-bot, dan jangan cuba pintas. Bagi cadangan kata kunci carian, kemudian minta pengguna upload MP3.
  - Promo DELIMa Champions: **"Epic" oleh kulakovka** (#624630), 100 BPM.
  - Tutorial: **"Educational Presentation" oleh Monume** (#547934), 105 BPM. Lagu ni dipilih berbanding "Tutorial" oleh The Mountain.
- **Muzik mesti sync dengan visual.** Bahagian kuat lagu jatuh pada momen visual utama (logo muncul, telefon muncul). Hit atau bar terakhir lagu jatuh pada CTA utama (WIN!, LUCKY LOGIN!). Teks CTA berturut (LOGIN • PLAY • WIN!) jatuh atas beat.
- **Penamat tak boleh senyap kosong.** Mesti ada bunyi lembut yang reda perlahan hingga saat terakhir. Pengguna minta ini secara khusus. Cara buat: lihat 3.4.
- **Narasi:** suara robotik (eSpeak) dan suara Yasmin (edge-tts) **ditolak, "hodoh"**. Pengguna lebih suka **rakaman suara sendiri** atau **Gemini TTS dari Google AI Studio** yang dia jana sendiri. Bila dapat lebih dari satu suara, buat versi berasingan untuk dibanding.
- **Privasi:** kaburkan semua emel, nama dan notifikasi dalam rakaman skrin. **Rakaman skrin asal yang mengandungi data peribadi tak boleh di-commit** (letak dalam `.gitignore`).
- **Penghantaran:** hantar MP4 dalam chat (SendUserFile, `display: render`), commit dan push ke branch kerja. Sebut dengan jujur apa yang diukur dan apa yang tak didengar.
- **Pilihan kreatif** yang tak diminta (contohnya label "KELAS A–E", kad kuiz tanpa teks soalan) mesti disebut supaya pengguna boleh semak. Jangan reka tarikh, hadiah, keputusan, QR atau pautan.

---

## 2. Identiti visual

- **Warna** (`assets/shared.css`): navy `#050b2e`, royal `#0b2fa8`, electric `#1f6bff`, cyan `#3fe0ff`, emas `#ffcc3a`.
- **Fon:** Montserrat 700/800/900 + 900 italic, fail woff2 dalam `assets/fonts/`, dimuatkan melalui `@font-face` dengan nama keluarga `DelimaDisplay` dalam setiap scene.
  - Tajuk hero: 900 italic dengan kelas `gold-fill` / `white-fill` (teks bergradien) + `depth` (bayang biru 3D).
  - **Perangkap:** letak kelas `gold-fill`/`white-fill` pada **setiap span perkataan**, bukan pada induk. Kalau letak pada induk, `opacity` anak tak berkesan. Jangan guna `-webkit-text-stroke`, sebab ia muncul garis dalam huruf Montserrat.
- **Logo:** `delima-champions-2026/assets/logos/delima.png` dan `sekolah.png`. Kedua-duanya dipotong terus dari poster rujukan (tidak dilukis semula) dan berlatar lutsinar. Jangan lukis semula, terbalikkan atau herotkan.
  - Rawatan 3D (`buildLogo3D()` dalam scene): lapisan siluet bertopeng di belakang muka depan (ketebalan), bevel PNG, kilauan (sheen), rim cyan. Putaran mesti terhad supaya tulisan tak terbalik.
  - **Perangkap:** `opacity` pada elemen `.l3d` atau mana-mana induknya akan meratakan 3D. Fade pada anak (`#id > *`).
- **Dunia latar:** gradien navy-biru, grid perspektif, bintang berbiji (deterministik), ikon pembelajaran di tepi, laluan cahaya pada peralihan.
- **Lencana sekolah** mesti muncul pada pembukaan dan penutup. Lambang DELIMa Champions ialah identiti utama.

---

## 3. Aliran kerja teknikal

### 3.1 Projek HyperFrames
- Satu folder bagi setiap video, dengan `hyperframes@0.8.169` dipin dalam `package.json`. Struktur: `index.html` (root: hos scene + satu `<audio id="mix">`), `compositions/*.html` (satu scene satu fail, dalam `<template>`), `assets/`, `tools/`, `output/`.
- Gunakan `fromTo` (bukan `from`). Satu timeline paused bagi setiap scene, didaftar pada `window.__timelines["<id>"]`. Peralihan antara scene dibuat dengan hos yang bertindih 0.3–0.6 s.
- Sebelum render: `npx hyperframes check`, kemudian `npx hyperframes snapshot --at <masa,…> --no-end -o <dir>`, dan semak contact sheet pada setiap peralihan.
- Render: `npm run render` (`-q delivery`). Masa render: 60 s landskap ≈ 7 min, 40 s menegak ≈ 2.5 min.
- **Kalau audio sahaja yang berubah, jangan render semula.** Tukar trek audio sahaja:
  `ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -t <tempoh> -movflags +faststart out.mp4`

### 3.2 Analisis lagu (sebelum potong)
1. Kira RMS setiap 0.5 s untuk lihat struktur: intro, bahagian penuh, breakdown, outro, penamat.
2. Kira spectral flux, kemudian BPM dan fasa beat dengan grid search. Kenal pasti downbeat dari aksen setiap 4 beat.
3. Cari titik masuk bahagian penuh (lompatan RMS) dan hit kuat (onset flux tertinggi).
Contoh kod ada dalam sejarah projek. Hasil yang dah diukur:
   - Epic (kulakovka): 100 BPM, downbeat 0.595 + 2.4k s, masuk penuh 10.195 s, hit penamat 132.595 s.
   - Educational Presentation (Monume): 105 BPM, drop 54.85 s, hit 80.03 s, breakdown 36–55 s, outro dari 84 s.
   - Tutorial (The Mountain): 116 BPM, masuk penuh 16.54 s, bar terakhir 97.75 s.

### 3.3 Potong lagu supaya sync
- Ofset = masa lagu − masa video. Pilih ofset supaya bahagian masuk atau drop lagu jatuh pada momen visual utama.
- Kalau perlu cantum (contohnya terus ke hit penamat lagu), **potong pada downbeat**, dan sebaiknya beza ofset = gandaan tepat bar. Crossfade 30–150 ms.
- Kalau hit lagu tak jatuh tepat pada visual, **alihkan visual** ke beat (contohnya LUCKY LOGIN! 35.7 → 34.75 s, penutup kotak 51.84 → 51.36 s). Kalau lagu muat tanpa cantuman, satu potongan berterusan lebih licin.
- Skrip rujukan: `delima-champions-2026/tools/prepare_music.py`, `delima-login-tutorial/tools/mix_audio.py` (`--lagu`).

### 3.4 Penamat lembut hingga saat terakhir
- Ambil 0.5–0.6 s gema sejurus selepas hit penamat, kemudian "bekukan" dengan **Paulstretch** (FFT, fasa rawak berbiji, jadi deterministik) supaya nota sama dengan hit.
- Sampul: naik 0.7 s, turun 6 dB perlahan, kemudian pudar kosinus tepat pada saat terakhir. Fade akhir pada mix cuma 0.2–0.25 s untuk elak bunyi klik.

### 3.5 SFX
- SFX Pixabay (lesen Pixabay) disalin dari bundle HyperFrames ke `assets/audio/sfx/`.
- **Letak ikut puncak, bukan mula fail.** Masa mula = masa visual − ofset puncak:
  whoosh 0.164 · pop 0.122 · click-soft 0.053 · sparkle 0.03 · ping 0.328 · impact-bass-1 0.076 · impact-bass-2 2.066 · riser 3.04 · whoosh-cinematic 2.549.
- Gunakan sedikit sahaja dan setiap satu mesti ada sebab di skrin: klik pada tekanan skrin, whoosh pada peralihan, kilauan pada "berjaya" atau CTA.

### 3.6 Narasi (rakaman / Gemini)
1. Bersihkan dengan ffmpeg: rakaman telefon guna `highpass=80,afftdn=nf=-50:nr=10,acompressor,loudnorm=I=-18:TP=-2`. Gemini cukup dengan `highpass + loudnorm`.
2. Pecahkan pada senyap (RMS 20 ms; jeda ≥ 0.45 s untuk ayat, ≥ 0.08 s untuk perkataan seperti Login/Play/Win).
3. Letak setiap frasa dalam `tools/cues.json` → `vo_sets.<nama>`: `at` / `trim` / `len` (margin 0.05 s), supaya ayat jatuh pada teks skrinnya.
4. Ducking muzik **−16 dB** bila suara masuk (turun 0.25 s, naik 0.4 s). Sasaran: suara 10–15 dB di atas muzik. Untuk perkataan yang serentak dengan hit lagu, guna `duck: 0.35–0.6` supaya klimaks tak tenggelam.
5. `python3 tools/mix_audio.py --vo <set> --out <fail>`. Mix akhir **−16 LUFS, true peak ≤ −1.3 dBFS** (2 laluan: ukur ebur128, kemudian volume + alimiter).
- Skrip narasi rasmi: `delima-champions-2026/SCRIPT.md` dan `tools/vo-script.json`. Teks untuk AI Studio: arahan "Bahasa Melayu Malaysia, bukan Indonesia", sebutan DELIMa = "de-li-ma", SK = "es-ke", jeda 2 s antara baris.

### 3.7 Rakaman skrin (tutorial)
- `delima-login-tutorial/tools/build_screen.py`: senarai segmen `play` (main) / `hold` (tahan frame) untuk buang bahagian tak berkaitan dan bagi masa membaca, `gblur` pada kawasan peribadi (koordinat sumber), skala ke 720×1600 @ 30 fps.
- Dalam komposisi: bingkai telefon, kamera `cam(z, cx, cy)` (zum + had tepi) pada lapisan dalam, gelang emas pada butang, riak tekan pada saat sebenar ditekan, langkah bernombor di atas ("LANGKAH n").
- Semak frame yang dikaburkan secara visual sebelum render.

---

## 4. Persekitaran & had

- Network cloud terhad. Yang boleh: npm, PyPI, `pixabay.com` (tapi 403 untuk akses automatik), `speech.platform.bing.com` (pengguna dah tambah). Yang disekat: HuggingFace, Google TTS dan lain-lain.
- `edge-tts` perlukan `proxy=os.environ["HTTPS_PROXY"]` dihantar secara eksplisit.
- Tiada Claude in Chrome dalam sesi cloud. Pengguna guna Chrome atau AI Studio sendiri, kemudian upload fail.
- Claude tak boleh mendengar audio. Semua semakan bunyi ialah **pengukuran** (RMS, LUFS, onset), jadi sentiasa minta pengguna dengar bahagian sambungan lagu.

## 5. Senarai semak sebelum hantar
1. `npm run check` lulus, snapshot setiap peralihan dah disemak, tiada teks melimpah keluar skrin.
2. ffprobe: resolusi, 30 fps, bilangan frame, tempoh tepat. ebur128: −16 LUFS, TP ≤ −1.3.
3. Hit lagu disahkan dengan RMS sebelum/selepas masa sasaran. Penamat masih ada bunyi hingga saat akhir.
4. Tiada data peribadi dalam frame, dan tiada fail mentah peribadi dalam commit.
5. Commit + push, hantar MP4, terangkan perubahan dan apa yang perlu pengguna dengar.
