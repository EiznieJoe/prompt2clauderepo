# Sistem Permohonan Bantuan RMT

Borang permohonan Rancangan Makanan Tambahan untuk orang awam, dengan aliran
semakan dua peringkat (penyemak → pelulus) dan jejak audit penuh.

Dibina untuk kos sifar: frontend statik di Netlify, pangkalan data Supabase
free tier, cron harian di GitHub Actions.

---

## Aliran status

```
DIHANTAR ──► DALAM_SEMAKAN ──► DALAM_KELULUSAN ──► LULUS
   │              │   ▲              │  │
   │              │   └──────────────┘  └──► TOLAK
   │              ▼
   └──────► DIPULANGKAN ──(pemohon betulkan)──► DIHANTAR
                 │
                 └──(14 hari tiada tindakan)──► GUGUR

Pemohon boleh tarik balik sendiri dari DIHANTAR / DALAM_SEMAKAN / DIPULANGKAN
                                                      └──► DITARIK_BALIK

Penyemak boleh TOLAK terus dari DIHANTAR / DALAM_SEMAKAN bila jelas tidak layak.
```

Peraturan yang dikuatkuasakan di pangkalan data, bukan di browser:

- **Pengasingan tugas** — pegawai yang menyemak satu kes tidak boleh meluluskan
  kes yang sama. `rmt_putuskan()` menolaknya.
- **Had pulangan** — 3 kali (boleh ubah). Selepas itu penyemak wajib buat
  keputusan, tidak boleh ping-pong lagi.
- **Sebab wajib** — tiada TOLAK tanpa sebab, tiada DIPULANGKAN tanpa catatan.
- **Satu permohonan aktif per murid per sesi** — indeks unik.
- **Audit append-only** — `audit_log` ada trigger yang menolak UPDATE dan
  DELETE. Admin pun tidak boleh mengubahnya.

## Saringan automatik menasihat, tidak memutuskan

`rmt_saringan()` menanda perkara seperti pendapatan per kapita melebihi had,
atau murid yang sudah ada permohonan LULUS. Ia **tidak** menolak sendiri.
Sebabnya: pendapatan yang diisytihar belum disemak terhadap dokumen, jadi
menolak secara automatik bermakna menolak berdasarkan maklumat yang belum
disahkan. Penyemak tekan "Tolak terus (tidak layak)" bila dia sudah pasti.

Had kelayakan disimpan dalam jadual `kriteria`, bukan dalam kod — lihat
`supabase/04_seed.sql`. Selagi `pgk_per_kapita` tidak diisi, saringan tidak
menanda apa-apa pada pendapatan dan sistem tetap berfungsi.

---

## Pemasangan

### 1. Supabase

Cipta projek baharu (free tier), kemudian dalam **SQL Editor** jalankan ikut urutan:

```
supabase/01_schema.sql
supabase/02_rls.sql
supabase/03_rpc.sql
supabase/04_seed.sql
```

Kemudian:

1. **Sekolah** — ganti baris contoh dalam `sekolah` dengan sekolah sebenar.
2. **Pegawai** — Authentication → Users → Add user (emel + kata laluan) untuk
   setiap pegawai. Salin UUID setiap pengguna, masukkan ke jadual `staf`
   dengan peranan `penyemak`, `pelulus`, atau `admin`. Contoh SQL ada dalam
   `04_seed.sql`.
3. **Kriteria** — isi `pgk_per_kapita` bila angka rasmi diperoleh.

> Supabase Auth hadkan kata laluan minimum 6 aksara secara default. Naikkan ke
> 10 dan hidupkan semakan kata laluan terbocor: Authentication → Policies.

### 2. Netlify

Sambung repo ini ke Netlify. Tetapan sudah ada dalam `netlify.toml`
(`publish = "rmt"`, header CSP, dan build script).

Tetapkan dua environment variable — **Site configuration → Environment variables**:

| Nama | Nilai |
|---|---|
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | anon / publishable key |

Jangan masukkan `service_role` key. Build script akan gagal dengan sengaja
kalau ia dikesan.

### 3. GitHub Actions

Settings → Secrets and variables → Actions, tambah:

| Secret | Nilai |
|---|---|
| `SUPABASE_URL` | sama seperti di atas |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key |

Workflow `rmt-sweep.yml` berjalan setiap hari 09:17 pagi (MYT). Ia menggugurkan
permohonan yang tamat tempoh pembetulan, menganonimkan rekod lama, dan sebagai
kesan sampingan menghalang projek Supabase free tier dari dijeda selepas 7 hari
tiada aktiviti.

### 4. Pembangunan setempat

```bash
cp rmt/assets/config.sample.js rmt/assets/config.js   # isi URL + anon key
cd rmt && python3 -m http.server 8080
```

Buka `http://localhost:8080`. `config.js` ada dalam `.gitignore`.

---

## Apa yang sudah diuji

Skema ini dijalankan terhadap PostgreSQL 16 sebenar dengan tiruan persekitaran
Supabase (peranan `anon` / `authenticated`, `auth.uid()`). Yang lulus:

| Ujian | Keputusan |
|---|---|
| `anon` cuba `select * from permohonan` | 0 baris |
| IC bukan 12 angka, akuan tak ditanda | ditolak |
| Permohonan kedua untuk murid sama dalam sesi sama | ditolak |
| 6 kali IC salah pada rujukan sah | dikunci pada kali ke-6 |
| Selepas dikunci, IC betul pun | ditolak sampai tempoh reset |
| `rmt_tarik_balik` sebagai jalan pintas had | juga dikunci |
| Pulangkan → pemohon betulkan sebahagian → hantar semula | medan lain kekal |
| Pulangan ke-4 | ditolak, had 3 kali |
| Penyemak yang sama cuba luluskan kes sendiri | ditolak |
| Admin yang menyemak sendiri cuba luluskan | ditolak |
| Penyemak sekolah lain bertindak ke atas kes kita | ditolak |
| Pelulus guna fungsi penyemak | ditolak |
| Pengguna auth tanpa rekod `staf` | ditolak |
| `anon` panggil fungsi staf atau `rmt_sweep` | permission denied |
| TOLAK tanpa sebab | ditolak |
| `update` / `delete` pada `audit_log` | ditolak oleh trigger |
| `rmt_sweep()` gugur + anonim | betul |

Dua bug sebenar terjumpa semasa ujian dan sudah dibetulkan:

1. **Rate limiter tak berfungsi sama sekali.** `RAISE EXCEPTION` membatalkan
   seluruh transaksi, termasuk kiraan percubaan yang baru ditambah — jadi
   kaunter sentiasa kembali sifar dan had tak pernah tercapai. Sebab itu
   `rmt_semak_status`, `rmt_tarik_balik` dan `rmt_hantar_semula` memulangkan
   `{"ralat": "..."}` sebagai data untuk kegagalan padanan, bukan exception.
2. **Pengasingan tugas boleh dipintas.** Semakan asal hanya membandingkan
   medan `penyemak_id`, yang merekod seorang sahaja. Admin yang menyemak
   sendiri masih boleh meluluskan. Sekarang ia memeriksa jejak audit untuk
   mana-mana tindakan semakan oleh orang yang sama.

## Ujian yang wajib anda buat sendiri pada projek Supabase anda

RLS mudah nampak betul tanpa diuji. Buat lima ujian ini sekurang-kurangnya:

1. Buka DevTools di borang awam dan cuba `fetch` terus ke
   `/rest/v1/permohonan?select=*` dengan anon key. Patut dapat **array kosong**.
2. Log masuk sebagai penyemak Sekolah A, cuba lihat permohonan Sekolah B.
   Patut tidak nampak.
3. Semak status dengan IC salah 6 kali. Patut dikunci pada kali ke-6.
4. Sebagai penyemak, hantar satu kes ke kelulusan, kemudian log masuk sebagai
   pelulus yang **sama orang** dan cuba luluskan. Patut ditolak.
5. Cuba `update audit_log set sebab='x'` dalam SQL Editor. Patut gagal.

## Had yang perlu difahami

- **Tiada muat naik dokumen.** Reka bentuk sengaja: Supabase free tier hanya
  ada ~1 GB storan, dan menyimpan salinan IC serta penyata pendapatan 1,500
  keluarga menambah risiko PDPA yang besar untuk pulangan yang kecil. Dokumen
  disemak secara fizikal di sekolah, dan pemohon mengaku maklumat benar dalam
  borang.
- **Tiada notifikasi automatik.** Emel dan SMS pukal bukan kos sifar yang
  boleh dijamin. Pemohon menyemak sendiri guna no. rujukan + No. KP murid.
  Kalau notifikasi diperlukan kemudian, Netlify Functions + penyedia emel
  free tier boleh ditambah tanpa mengubah skema.
- **Free tier Supabase** — 500 MB pangkalan data (jauh lebih dari cukup untuk
  1,500 permohonan), 2 projek aktif per organisasi, dan dijeda selepas 7 hari
  tiada aktiviti. Cron harian menangani jeda itu, tetapi kalau sistem ini jadi
  kritikal, Pro ($25/bulan) membuang risiko jeda sepenuhnya.
- **Rate limiting borang awam** hanya berdasarkan nombor telefon, sebab fungsi
  Postgres tidak nampak IP klien sebenar di belakang connection pooler. Kalau
  spam jadi masalah, tambah Netlify Function sebagai proksi dan rate-limit di
  sana.
