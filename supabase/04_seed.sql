-- =====================================================================
-- Data awal
-- =====================================================================

-- Tetapan aliran kerja. Ubah nilai di sini, bukan dalam kod.
insert into tetapan (kunci, nilai, nota) values
  ('had_pulangan',                 '3',  'Berapa kali satu permohonan boleh dipulangkan kepada pemohon'),
  ('hari_tempoh_betul',            '14', 'Hari diberi kepada pemohon untuk betulkan sebelum GUGUR'),
  ('sla_hari_semakan',             '7',  'Sasaran hari untuk penyemak — papar bendera merah bila lebih'),
  ('sla_hari_kelulusan',           '5',  'Sasaran hari untuk pelulus'),
  ('had_percubaan_semak',          '5',  'Percubaan salah semak status sebelum dikunci 15 minit'),
  ('had_hantar_per_telefon_sehari','5',  'Perisai flood borang awam')
on conflict (kunci) do nothing;

-- ---------------------------------------------------------------------
-- KRITERIA KELAYAKAN — SENGAJA TIDAK DIISI.
--
-- Kelayakan RMT ditetapkan KPM dan terikat pada Jadual Paras Garis
-- Kemiskinan (PGK) Nasional, yang berubah dari semasa ke semasa. Saya
-- tidak dapat mengesahkan angka rasmi terkini, jadi ia tidak diletakkan
-- di sini. Dapatkan angka dari surat pekeliling KPM / PGK semasa, lalu:
--
--   insert into kriteria (kunci, nilai, nota, berkuatkuasa_dari)
--   values ('pgk_per_kapita', <ANGKA_RM>, 'PGK per kapita, sumber: <rujukan>', '2026-01-01')
--   on conflict (kunci) do update
--     set nilai = excluded.nilai, nota = excluded.nota,
--         berkuatkuasa_dari = excluded.berkuatkuasa_dari,
--         dikemaskini_pada = now();
--
-- Selagi baris ini tiada, saringan automatik tidak menanda apa-apa pada
-- pendapatan — penyemak buat penilaian sendiri. Sistem tetap berfungsi.
-- ---------------------------------------------------------------------

-- Sekolah contoh. Ganti dengan sekolah sebenar.
insert into sekolah (kod, nama) values
  ('ABA0001', 'SK Contoh Satu')
on conflict (kod) do nothing;

-- ---------------------------------------------------------------------
-- STAF
-- Cipta pengguna dahulu di Supabase Dashboard -> Authentication -> Users
-- (Add user, email + password), kemudian salin UUID pengguna itu ke sini.
--
--   insert into staf (id, nama, peranan, sekolah_id) values
--     ('<uuid-dari-auth>', 'Nama Penyemak', 'penyemak',
--      (select id from sekolah where kod = 'ABA0001')),
--     ('<uuid-dari-auth>', 'Nama Pelulus',  'pelulus',
--      (select id from sekolah where kod = 'ABA0001'));
--
-- Penyemak dan pelulus WAJIB dua orang berbeza — rmt_putuskan() menolak
-- percubaan meluluskan kes yang anda sendiri semak.
-- ---------------------------------------------------------------------
