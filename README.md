# KelasQuest — Video Promo 30s

Video promo 30 saat (1920x1080, 30fps) untuk KelasQuest, dibina dengan [HyperFrames](https://hyperframes.heygen.com) (HTML + GSAP).

- Video siap: [`output/kelasquest-promo-30s.mp4`](output/kelasquest-promo-30s.mp4)
- Komposisi: [`index.html`](index.html)
- Skrip, timing dan cara audio dipendekkan: [`SCRIPT.md`](SCRIPT.md)

## Struktur

```
index.html                 komposisi utama (5 scene + selingan + bar XP)
assets/voiceover.wav       voiceover 29.3s (dipendekkan daripada asal)
assets/source/             audio asal 45s
assets/vendor/gsap.min.js  GSAP 3.12.5 (lokal, tak perlu CDN)
output/                    MP4 siap
```

## Edit & render

```bash
npm run dev      # preview dalam browser
npm run check    # lint + semakan runtime
npm run render   # render ke renders/
```

Warna utama ada dalam `:root` di `index.html` (`--purple`, `--gold`, `--teal`, `--coral`). Tukar di situ kalau nak ikut warna brand sebenar.

## Projek lain dalam repo ini

- [`delima-champions-2026/`](delima-champions-2026/) — video promo 60s DELIMa Champions 2026, SK Rugading, Tuaran (projek HyperFrames berasingan, lihat README di dalamnya).
- [`delima-login-tutorial/`](delima-login-tutorial/) — video tutorial menegak 40s "Cara Log Masuk DELIMa 3.0" untuk aktiviti Lucky Login.

Panduan gaya & cara edit untuk siri video DELIMa: [`PANDUAN-EDIT-VIDEO.md`](PANDUAN-EDIT-VIDEO.md).
