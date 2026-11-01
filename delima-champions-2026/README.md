# DELIMa Champions 2026 — Video Promo 60s (SK Rugading, Tuaran)

Video promo 60 saat, 1920×1080, 30 fps, MP4 (H.264 + AAC), dibina dengan [HyperFrames](https://hyperframes.heygen.com) (HTML + GSAP). Semua teks ialah tipografi boleh edit, bukan huruf dalam imej.

## Fail siap

| Fail | Isi |
|---|---|
| `output/delima-champions-2026-60s-vo-panduan.mp4` | Muzik + SFX + **suara panduan sintetik** (lihat nota di bawah) |
| `output/delima-champions-2026-60s-muzik-sfx.mp4` | Muzik + SFX sahaja, semua teks promosi kekal |

### Nota penting: suara latar

Persekitaran produksi ini tiada akses kepada mana-mana enjin suara neural Bahasa Melayu (Microsoft/Google TTS, HuggingFace dan seumpamanya disekat rangkaian). Narasi dalam versi pertama dijana dengan **eSpeak NG (`ms`)**, yang berbunyi robotik. Ia **suara panduan untuk timing sahaja**, bukan untuk ditayangkan kepada murid.

Untuk versi akhir:

1. Rakam 8 baris dalam `SCRIPT.md` (suara guru/murid sebenar, atau TTS Melayu berkualiti dari luar).
2. Simpan sebagai `assets/audio/vo-panduan/vo1.wav` … `vo8.wav` (nama sama, ganti fail lama). Panjang setiap baris sebaiknya tidak melebihi tetingkap dalam `SCRIPT.md`.
3. `python3 tools/mix_audio.py` — bina semula mix (ducking muzik ikut panjang rakaman baharu).
4. `npm run render` — render semula.

## Struktur

```
index.html                     root 60 s: world + 8 scene + satu trek audio mix
compositions/world.html        dunia digital berterusan (grid, bintang, ikon, laluan cahaya)
compositions/s1-invite.html    0–5 s    portal + lencana sekolah
compositions/s2-hero.html      5–12 s   pendedahan lambang DELIMa Champions 3D
compositions/s3-login.html     12–20 s  Lucky Login → tiket emas → kebuk cabutan
compositions/s4-battle.html    20–29 s  DELIMa Class Battle (bar konsep, tiada data sebenar)
compositions/s5-quiz.html      29–37 s  DELIMa Fun Quiz
compositions/s6-poster.html    37–45 s  Poster Digital (Tahun 4–6)
compositions/s7-draw.html      45–53 s  Grand Lucky Draw (tiada hadiah khusus)
compositions/s8-finale.html    53–60 s  penutup: kedua-dua logo + LOGIN • PLAY • WIN!
assets/logos/                  logo dipotong daripada poster rujukan (lutsinar) + lapisan bevel
assets/audio/                  mix siap, stem muzik, SFX, suara panduan
assets/shared.css              warna, tipografi, rawatan logo 3D
tools/                         skrip logo, muzik, suara panduan, mix
```

## Edit & render

```bash
npm run check             # lint + runtime + layout + contrast
npm run dev               # preview dalam Studio
npm run render            # versi dengan narasi
npm run render:tanpa-vo   # versi muzik + SFX sahaja
```

Versi tanpa narasi hanya menukar pemboleh ubah `audioMix` kepada `assets/audio/mix-tanpa-vo.wav`; visual sama.

## Logo

Kedua-dua logo dipotong terus daripada piksel poster rujukan (`assets/source/poster-rujukan.png`), tidak dilukis semula. Latar luar dibuang dengan GrabCut + pembersihan tepi (`assets/source/mask-*.png`, `tools/build_logos.py`). Muka depan setiap logo kekal asal; rawatan 3D (ketebalan, bevel, kilauan, rim) ditambah di belakang/atas dalam CSS.

Had: poster rujukan hanya 1672×941, jadi lencana sekolah asalnya ~300 px tinggi. Ia kelihatan sedikit lembut pada saiz besar. Kalau ada fail logo asal beresolusi tinggi (PNG/SVG), letak di `assets/logos/delima.png` dan `assets/logos/sekolah.png` (lutsinar), jalankan semula bahagian bevel dalam `tools/build_logos.py`, dan render semula.

## Muzik & SFX

- Muzik: **"Epic" oleh kulakovka** (Pixabay #624630, Lesen Kandungan Pixabay: bebas guna, termasuk komersial, tanpa atribusi wajib). Fail asal: `assets/audio/source/kulakovka-epic-624630.mp3`.
- Lagu 100 BPM disunting jadi 60 s dalam dua potongan pada fasa bar yang sama (`tools/prepare_music.py`): bahagian masuk penuh lagu jatuh tepat pada pendedahan logo DELIMa (5.76 s), penutup kotak hadiah pada downbeat terkuat (51.36 s), LOGIN • PLAY pada beat 54.96/55.56 s dan hit penamat lagu tepat pada "WIN!" (56.16 s), kemudian lagu reda hingga senyap pada 60 s.
- Muzik diturunkan 16 dB di bawah narasi supaya suara jelas.
- SFX: Pixabay (lesen Pixabay, lihat `assets/audio/sfx/CREDITS.md`). Setiap SFX disegerakkan dengan peristiwa visual; senarai penuh dalam `tools/cues.json`.
- Loudness kedua-dua mix: -16 LUFS, true peak ≤ -1.4 dBFS (diukur, bukan didengar).
- Gubahan asal yang digunakan sebelum ini (GeneralUser GS) masih ada dalam `tools/compose_music.py` + `tools/render_music.mjs` sebagai alternatif.

Bina semula muzik: `python3 tools/prepare_music.py && python3 tools/mix_audio.py`.
