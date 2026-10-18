-- =====================================================================
-- Row Level Security
-- Prinsip: anon TIDAK boleh baca atau tulis permohonan secara terus.
-- Semua akses awam melalui fungsi RPC di 03_rpc.sql.
-- =====================================================================

alter table sekolah          enable row level security;
alter table kriteria         enable row level security;
alter table tetapan          enable row level security;
alter table staf             enable row level security;
alter table permohonan       enable row level security;
alter table audit_log        enable row level security;
alter table semak_percubaan  enable row level security;

-- Tiada satu pun table ini boleh ditulis terus oleh klien.
revoke insert, update, delete on permohonan      from anon, authenticated;
revoke insert, update, delete on audit_log       from anon, authenticated;
revoke all                   on semak_percubaan  from anon, authenticated;
revoke insert, update, delete on staf            from anon, authenticated;
revoke insert, update, delete on kriteria        from anon, authenticated;
revoke insert, update, delete on tetapan         from anon, authenticated;
revoke insert, update, delete on sekolah         from anon, authenticated;

-- Grant SELECT secara EKSPLISIT. Supabase memberi grant default kepada
-- jadual baharu, tetapi bergantung pada default platform bermakna sistem
-- ini boleh pecah kalau default itu berubah. Nyatakan sendiri.
grant select on sekolah, kriteria, tetapan to anon, authenticated;
grant select on permohonan, audit_log, staf to authenticated;
revoke select on permohonan, audit_log, staf from anon;

-- ---------- Pembantu ----------
create or replace function saya_peranan() returns peranan_staf
language sql stable security definer set search_path = public, pg_temp as $$
  select peranan from staf where id = auth.uid() and aktif limit 1;
$$;

create or replace function saya_sekolah() returns uuid
language sql stable security definer set search_path = public, pg_temp as $$
  select sekolah_id from staf where id = auth.uid() and aktif limit 1;
$$;

-- ---------- sekolah: senarai nama boleh dibaca sesiapa (perlu untuk borang)
drop policy if exists sekolah_baca_awam on sekolah;
create policy sekolah_baca_awam on sekolah
  for select to anon, authenticated using (aktif);

-- ---------- kriteria / tetapan: baca sahaja, tiada data peribadi
drop policy if exists kriteria_baca on kriteria;
create policy kriteria_baca on kriteria
  for select to anon, authenticated using (true);

drop policy if exists tetapan_baca on tetapan;
create policy tetapan_baca on tetapan
  for select to anon, authenticated using (true);

-- ---------- staf: hanya boleh lihat rekod sendiri + rakan sekolah sama
drop policy if exists staf_baca on staf;
create policy staf_baca on staf
  for select to authenticated
  using (id = auth.uid() or sekolah_id = saya_sekolah());

-- ---------- permohonan: staf sekolah sendiri sahaja. anon tiada policy
--            sama sekali, jadi anon dapat sifar baris.
drop policy if exists permohonan_baca_staf on permohonan;
create policy permohonan_baca_staf on permohonan
  for select to authenticated
  using (
    sekolah_id = saya_sekolah()
    or saya_peranan() = 'admin'
  );

-- ---------- audit_log: baca sahaja, ikut sekolah
drop policy if exists audit_baca_staf on audit_log;
create policy audit_baca_staf on audit_log
  for select to authenticated
  using (
    saya_peranan() = 'admin'
    or exists (
      select 1 from permohonan p
      where p.id = audit_log.permohonan_id
        and p.sekolah_id = saya_sekolah()
    )
  );
