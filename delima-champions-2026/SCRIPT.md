# Skrip, Teks Skrin & Timing — DELIMa Champions 2026 (60 s)

Masa dalam saat (global). "Tetingkap VO" = ruang yang ada untuk baris itu tanpa bertindih dengan scene seterusnya.

| Scene | Masa | Teks skrin | Narasi (rakam baris ini) | Tetingkap VO |
|---|---|---|---|---|
| 1 Jemputan | 0–5 | WARGA SK RUGADING… / ANDA BERSEDIA? | 1. "Warga SK Rugading… bersedia untuk menjadi juara digital?" | 0.5–4.8 |
| 2 Logo | 5–12 | DELIMa CHAMPIONS 2026 / MISI JUARA DIGITAL BERMULA! | 2. "DELIMa Champions dua ribu dua puluh enam. Misi juara digital bermula!" | 6.0–11.2 |
| 3 Lucky Login | 12–20 | LUCKY LOGIN / LOG MASUK & REBUT PELUANG MENANG! | 3. "Log masuk menggunakan akaun DELIMa sendiri. Sahkan penyertaan dan rebut peluang memenangi cabutan bertuah!" | 12.5–19.5 |
| 4 Class Battle | 20–29 | DELIMa CLASS BATTLE / KELAS MANA PALING HEBAT? / Berdasarkan peratus penyertaan kelas | 4. "Bawa kelas anda ke puncak! Setiap penyertaan membantu kelas merebut gelaran terbaik." | 20.5–28.5 |
| 5 Fun Quiz | 29–37 | DELIMa FUN QUIZ / 10 SOALAN • UJI MINDA ANDA! | 5. "Uji minda melalui sepuluh soalan tentang DELIMa, keselamatan digital dan pembelajaran!" | 29.6–36.5 |
| 6 Poster Digital | 37–45 | POSTER DIGITAL / SERLAHKAN KREATIVITI! / Khas untuk Tahun 4–6 / DELIMa dan AI Menjana Murid Kreatif | 6. "Murid Tahun Empat hingga Enam, serlahkan kreativiti melalui pertandingan Poster Digital DELIMa!" | 37.6–44.5 |
| 7 Grand Lucky Draw | 45–53 | GRAND LUCKY DRAW / SIAPA BAKAL BERTUAH? / Log masuk disahkan + Siapkan Fun Quiz | 7. "Lengkapkan log masuk dan Fun Quiz untuk peluang menyertai Grand Lucky Draw!" | 45.5–51.6 |
| 8 Penutup | 53–60 | LOGIN • PLAY • WIN! / MURID TAHUN 1–6 / NANTIKAN PENGUMUMAN GURU / SK RUGADING, TUARAN | 8. "Jom sertai DELIMa Champions! Login, Play, Win! Nantikan pengumuman guru." | 53.15–58.4 (Login/Play/Win pada 54.96/55.56/56.16) |

Sebutan: DELIMa = "de-li-ma" (bukan dieja huruf); Rugading = "Ru-ga-ding".

## Suara panduan sintetik

`tools/vo-lines.txt` ialah ejaan fonetik yang diberi kepada eSpeak NG supaya sebutan hampir betul ("Delima", "Es Ke", "Cempiyens", "Plei" …). Teks skrin dan skrip di atas kekal ejaan rasmi. `tools/make_vo_guide.sh` menjana semula fail panduan.

Kedudukan setiap baris: `tools/cues.json` → `vo[].at`. Kalau rakaman sebenar lebih panjang/pendek, laraskan `at` di situ dan jalankan `python3 tools/mix_audio.py`.

## Titik sync utama

| Masa | Peristiwa | Bunyi |
|---|---|---|
| 1.05 | portal terbuka | whoosh sinematik + kilauan |
| 5.76 | logo DELIMa muncul | masuk penuh lagu + impak bass |
| 14.4 / 14.65 | butang LOG MASUK ditekan / berjaya | klik / pop |
| 15.86 | tiket emas muncul | kilauan |
| 17.85 | tiket masuk kebuk cabutan | ping |
| 21.3–24.34 | bar penyertaan naik ke trofi | riser |
| 33.05 | jawapan betul menyala | ping + letupan bintang |
| 38.6–41.1 | kanvas bertukar jadi poster | pop + whoosh + kilauan |
| 51.36 | penutup kotak hadiah terbuka | downbeat terkuat lagu + impak |
| 54.96 / 55.56 / 56.16 | LOGIN / PLAY / WIN! (atas beat lagu) | pop / pop / hit penamat lagu + kilauan |
| 56.8–60.0 | bingkai penutup tenang | gema hit dipanjangkan, reda perlahan hingga senyap tepat 60 s |
