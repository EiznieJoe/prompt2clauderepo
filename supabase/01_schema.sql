-- =====================================================================
-- Sistem Permohonan Bantuan RMT — Skema
-- Jalankan dalam Supabase SQL Editor mengikut urutan fail 01 -> 04.
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------- Jenis ----------
do $$ begin
  create type status_permohonan as enum (
    'DIHANTAR',          -- pemohon dah hantar, belum disentuh
    'DALAM_SEMAKAN',     -- penyemak sedang semak
    'DIPULANGKAN',       -- dipulangkan kepada pemohon untuk betulkan
    'DALAM_KELULUSAN',   -- penyemak dah hantar kepada pelulus
    'LULUS',
    'TOLAK',
    'DITARIK_BALIK',     -- pemohon tarik balik sendiri
    'GUGUR'              -- tamat tempoh pembetulan, auto-tutup
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type peranan_staf as enum ('penyemak', 'pelulus', 'admin');
exception when duplicate_object then null; end $$;

-- ---------- Rujukan ----------
create table if not exists sekolah (
  id          uuid primary key default gen_random_uuid(),
  kod         text not null unique,          -- kod sekolah KPM, cth ABA1234
  nama        text not null,
  aktif       boolean not null default true,
  created_at  timestamptz not null default now()
);

-- Kriteria kelayakan TIDAK dihardcode. KPM ubah PGK dari masa ke masa,
-- jadi nilai disimpan di sini dan boleh dikemas kini tanpa deploy semula.
create table if not exists kriteria (
  kunci              text primary key,
  nilai              numeric not null,
  nota               text,
  berkuatkuasa_dari  date not null default current_date,
  dikemaskini_pada   timestamptz not null default now()
);

-- Tetapan am (SLA, had pulangan, retention)
create table if not exists tetapan (
  kunci            text primary key,
  nilai            text not null,
  nota             text,
  dikemaskini_pada timestamptz not null default now()
);

-- ---------- Staf ----------
-- id = auth.users.id. Staf dicipta melalui Supabase Auth (Dashboard atau
-- jemputan emel), kemudian baris di sini memberi peranan.
create table if not exists staf (
  id          uuid primary key references auth.users(id) on delete cascade,
  nama        text not null,
  peranan     peranan_staf not null,
  sekolah_id  uuid references sekolah(id) on delete restrict,
  aktif       boolean not null default true,
  created_at  timestamptz not null default now()
);

create index if not exists idx_staf_sekolah on staf(sekolah_id) where aktif;

-- ---------- Permohonan ----------
create table if not exists permohonan (
  id                    uuid primary key default gen_random_uuid(),
  no_rujukan            text not null unique,
  sekolah_id            uuid not null references sekolah(id) on delete restrict,
  status                status_permohonan not null default 'DIHANTAR',
  sesi                  int not null default extract(year from now()),

  -- Penjaga. IC penjaga sengaja TIDAK dikumpul (data minimization, PDPA
  -- Teknik 7) — pengenalan diri memadai dengan nama + telefon + IC murid.
  penjaga_nama          text not null,
  penjaga_telefon       text not null,
  penjaga_hubungan      text not null,

  -- Murid
  murid_nama            text not null,
  murid_ic              text not null,      -- perlu: kunci padanan rekod sekolah
  murid_tahun           int  not null check (murid_tahun between 1 and 6),
  murid_kelas           text,

  -- Kewangan isi rumah
  bil_isi_rumah         int     not null check (bil_isi_rumah between 1 and 30),
  pendapatan_isi_rumah  numeric(10,2) not null check (pendapatan_isi_rumah >= 0),
  pendapatan_per_kapita numeric(10,2)
      generated always as (round(pendapatan_isi_rumah / bil_isi_rumah, 2)) stored,
  ekasih                boolean not null default false,
  no_ekasih             text,

  -- Pengakuan
  akuan_benar           boolean not null check (akuan_benar),
  persetujuan_pdpa      boolean not null check (persetujuan_pdpa),

  -- Aliran kerja
  kali_dipulangkan      int not null default 0,
  catatan_penyemak      text,
  catatan_pelulus       text,
  sebab_tolak           text,
  penyemak_id           uuid references staf(id) on delete set null,
  pelulus_id            uuid references staf(id) on delete set null,

  tarikh_hantar         timestamptz not null default now(),
  tarikh_semakan        timestamptz,
  tarikh_keputusan      timestamptz,
  tamat_tempoh_betul    date,      -- SLA pemohon bila status DIPULANGKAN
  padam_selepas         date not null default (current_date + interval '3 years'),
  dianonimkan           boolean not null default false,
  updated_at            timestamptz not null default now(),

  -- Elak permohonan berganda untuk murid yang sama dalam sesi yang sama,
  -- kecuali yang sudah ditarik balik / gugur.
  constraint ck_sebab_tolak check (status <> 'TOLAK' or sebab_tolak is not null)
);

create unique index if not exists uq_murid_sesi_aktif
  on permohonan (murid_ic, sesi)
  where status not in ('DITARIK_BALIK', 'GUGUR');

create index if not exists idx_permohonan_sekolah_status
  on permohonan (sekolah_id, status);
create index if not exists idx_permohonan_rujukan on permohonan (no_rujukan);

-- ---------- Audit (append-only) ----------
create table if not exists audit_log (
  id             bigserial primary key,
  permohonan_id  uuid references permohonan(id) on delete set null,
  no_rujukan     text,
  pelaku_id      uuid,            -- null = pemohon / orang awam / sistem
  pelaku_label   text not null,   -- 'pemohon', 'sistem', atau nama staf
  tindakan       text not null,
  status_dari    status_permohonan,
  status_ke      status_permohonan,
  sebab          text,
  perubahan      jsonb,           -- nilai sebelum/selepas bagi setiap medan
  created_at     timestamptz not null default now()
);

create index if not exists idx_audit_permohonan on audit_log (permohonan_id, created_at desc);

-- Audit mesti append-only. Walaupun admin tak boleh ubah atau padam.
create or replace function audit_append_only() returns trigger
language plpgsql as $$
begin
  raise exception 'audit_log adalah append-only — UPDATE/DELETE tidak dibenarkan';
end $$;

drop trigger if exists t_audit_append_only on audit_log;
create trigger t_audit_append_only
  before update or delete on audit_log
  for each statement execute function audit_append_only();

-- ---------- Had percubaan semak status ----------
-- Tanpa ini, no_rujukan + IC boleh dibrute-force. Dikunci per-rujukan
-- sebab fungsi Postgres tak nampak IP klien sebenar di belakang pooler.
create table if not exists semak_percubaan (
  no_rujukan  text primary key,
  bil         int not null default 0,
  reset_pada  timestamptz not null default now() + interval '15 minutes'
);

-- ---------- updated_at ----------
create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin new.updated_at := now(); return new; end $$;

drop trigger if exists t_permohonan_updated on permohonan;
create trigger t_permohonan_updated before update on permohonan
  for each row execute function set_updated_at();
