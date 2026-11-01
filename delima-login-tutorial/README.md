# Cara Log Masuk DELIMa 3.0 — Video Tutorial Lucky Login (40 s)

Video tutorial menegak 1080×1920, 30 fps, MP4 (H.264 + AAC), dibina dengan HyperFrames. Untuk aktiviti **Lucky Login** (DELIMa Champions 2026, SK Rugading, Tuaran): murid layak menyertai bila log masuk ke DELIMa 3.0 dengan ID DELIMa sendiri.

- Video siap: `output/cara-log-masuk-delima-3.mp4`
- Laman: https://d3.delima.edu.my/landing

## Aliran video

| Masa (s) | Scene | Isi |
|---|---|---|
| 0–4.8 | Tajuk | CARA LOG MASUK DELIMa 3.0 · LUCKY LOGIN · SK Rugading |
| 4.4–10.3 | Sebelum mula | Pastikan ada ID DELIMa sendiri (…@moe-dl.edu.my). Belum ada? Dapatkan daripada guru kelas |
| 10–13.4 | Langkah 1 | Buka d3.delima.edu.my/landing (zum ke bar alamat) |
| 13.4–17.1 | Langkah 2 | Tekan butang ungu "Log Masuk ke DELIMa" (penanda tekan 16.4) |
| 17.1–21.7 | Langkah 3 | Pilih "Log masuk" (penanda tekan 21.45) |
| 21.7–28.2 | Langkah 4 | Pilih akaun ID DELIMa; tiada dalam senarai → "Use another account", taip ID & kata laluan |
| 28.2–32.6 | Berjaya | Ruang Aplikasi DELIMa 3.0 + tanda betul |
| 32.5–40 | Penutup | Log masuk dengan ID DELIMa sendiri = layak LUCKY LOGIN · d3.delima.edu.my |

## Rakaman skrin

Rakaman asal (110 s) **tidak disimpan dalam repo** kerana mengandungi emel, nama dan notifikasi peribadi; untuk bina semula, letak fail itu di `assets/source/rakaman-skrin-asal.mp4` (diabaikan oleh git). Hanya 0–12.5 s digunakan; bahagian melayari aplikasi dan panel notifikasi dibuang. `tools/build_screen.py` memotong, menahan frame penting, dan **mengaburkan maklumat peribadi** (senarai akaun Google, nama/emel di banner papan pemuka, avatar) sebelum klip masuk ke video → `assets/video/skrin-login.mp4`.

## Audio

Tiada narasi. Muzik "Tutorial" oleh The Mountain (Pixabay #508040, lesen Pixabay), 116 BPM: intro ringan di bawah tajuk, bahagian penuh masuk bila telefon muncul (9.9 s), kemudian 2 bar terakhir lagu di bawah kad penutup dengan bar terakhir tepat pada "LUCKY LOGIN!" (34.75 s) dan reda perlahan hingga 40 s. SFX Pixabay: klik pada setiap tekanan skrin, whoosh pada peralihan, kilauan pada "berjaya". `python3 tools/mix_audio.py` → `assets/audio/mix.wav` (-16 LUFS).

## Edit & render

```bash
python3 tools/build_screen.py   # bina semula klip skrin
python3 tools/mix_audio.py      # bina semula audio
npm run check
npm run render
```
