-- =====================================================================
-- Fungsi RPC — satu-satunya pintu masuk untuk menulis.
-- Semua SECURITY DEFINER dengan search_path ditetapkan (elak hijack),
-- dan setiap peralihan status menulis audit dalam transaksi yang sama.
-- =====================================================================

-- ---------- Pembantu dalaman ----------

create or replace function _tetapan_int(p_kunci text, p_default int)
returns int language sql stable security definer set search_path = public, pg_temp as $$
  select coalesce((select nilai::int from tetapan where kunci = p_kunci), p_default);
$$;

create or replace function _bersih(p_teks text) returns text
language sql immutable as $$
  -- Buang aksara kawalan, pangkas ruang. Had panjang dikuatkuasakan pemanggil.
  select nullif(btrim(regexp_replace(coalesce(p_teks, ''), '[\u0000-\u001F\u007F]', '', 'g')), '');
$$;

-- No rujukan: tidak berurutan, jadi tak boleh diteka walaupun satu diketahui.
create or replace function _rujukan_baru() returns text
language plpgsql security definer set search_path = public, pg_temp as $$
declare
  abjad text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; -- tiada I/O/0/1, elak silap taip
  calon text;
  i int;
begin
  loop
    calon := 'RMT-' || to_char(now(), 'YY') || '-';
    for i in 1..8 loop
      calon := calon || substr(abjad, 1 + floor(random() * length(abjad))::int, 1);
    end loop;
    exit when not exists (select 1 from permohonan where no_rujukan = calon);
  end loop;
  return calon;
end $$;

create or replace function _audit(
  p_permohonan_id uuid, p_no_rujukan text, p_tindakan text,
  p_dari status_permohonan, p_ke status_permohonan,
  p_sebab text default null, p_perubahan jsonb default null,
  p_pelaku_label text default null
) returns void language plpgsql security definer set search_path = public, pg_temp as $$
declare v_staf staf;
begin
  select * into v_staf from staf where id = auth.uid();
  insert into audit_log (permohonan_id, no_rujukan, pelaku_id, pelaku_label,
                         tindakan, status_dari, status_ke, sebab, perubahan)
  values (p_permohonan_id, p_no_rujukan, v_staf.id,
          coalesce(p_pelaku_label, v_staf.nama, 'pemohon'),
          p_tindakan, p_dari, p_ke, p_sebab, p_perubahan);
end $$;

-- Saringan automatik. SISTEM HANYA MENASIHAT — ia tak menolak sendiri.
-- Pendapatan yang diisytihar belum disemak terhadap dokumen, jadi keputusan
-- "tidak layak" kekal di tangan penyemak (fungsi rmt_tolak_terus).
create or replace function _saringan(p_id uuid) returns jsonb
language plpgsql stable security definer set search_path = public, pg_temp as $$
declare
  p permohonan;
  had numeric;
  bendera text[] := '{}';
begin
  select * into p from permohonan where id = p_id;
  if p.id is null then return '[]'::jsonb; end if;

  select nilai into had from kriteria where kunci = 'pgk_per_kapita';

  if had is not null and p.pendapatan_per_kapita > had and not p.ekasih then
    bendera := bendera || format('Pendapatan per kapita RM%s melebihi had RM%s',
                                 p.pendapatan_per_kapita, had);
  end if;
  if p.ekasih and _bersih(p.no_ekasih) is null then
    bendera := bendera || 'Tanda eKasih dipilih tetapi nombor eKasih tiada';
  end if;
  if exists (select 1 from permohonan x
             where x.murid_ic = p.murid_ic and x.id <> p.id
               and x.status in ('LULUS')) then
    bendera := bendera || 'Murid ini sudah ada permohonan LULUS';
  end if;

  return to_jsonb(bendera);
end $$;

-- =====================================================================
-- AWAM (anon)
-- =====================================================================

-- Kaunter percubaan pengenalan diri.
--
-- PENTING: fungsi ini TIDAK boleh digunakan bersama RAISE EXCEPTION untuk
-- kegagalan padanan. RAISE membatalkan seluruh transaksi, jadi kiraan yang
-- baru ditambah turut dibatalkan dan had tak pernah tercapai. Sebab itu
-- ketiga-tiga fungsi awam di bawah memulangkan {"ralat": ...} sebagai DATA
-- untuk kegagalan padanan, bukan melemparkan exception.
create or replace function _kira_cubaan(p_ruj text) returns int
language plpgsql security definer set search_path = public, pg_temp as $$
declare v_bil int;
begin
  insert into semak_percubaan (no_rujukan, bil)
  values (p_ruj, 1)
  on conflict (no_rujukan) do update
    set bil = case when semak_percubaan.reset_pada < now()
                   then 1 else semak_percubaan.bil + 1 end,
        reset_pada = case when semak_percubaan.reset_pada < now()
                          then now() + interval '15 minutes'
                          else semak_percubaan.reset_pada end
  returning bil into v_bil;
  return v_bil;
end $$;

-- Mengesahkan pasangan no_rujukan + IC murid, dengan had percubaan.
-- Pulangan: baris permohonan, atau NULL kalau gagal/dikunci. p_ralat
-- memegang mesej untuk dipulangkan kepada pemanggil.
create or replace function _sahkan_pemohon(
  p_no_rujukan text, p_murid_ic text, out p_rekod permohonan, out p_ralat text)
language plpgsql security definer set search_path = public, pg_temp as $$
declare
  v_ruj text := upper(_bersih(p_no_rujukan));
  v_ic  text := regexp_replace(coalesce(p_murid_ic,''), '[^0-9]', '', 'g');
  v_bil int;
begin
  p_ralat := null;
  if v_ruj is null or v_ic = '' then
    p_ralat := 'Masukkan no. rujukan dan no. Kad Pengenalan murid.';
    return;
  end if;

  v_bil := _kira_cubaan(v_ruj);
  if v_bil > _tetapan_int('had_percubaan_semak', 5) then
    p_ralat := 'Terlalu banyak percubaan. Cuba lagi dalam 15 minit.';
    return;
  end if;

  select * into p_rekod from permohonan
   where no_rujukan = v_ruj and murid_ic = v_ic;

  if p_rekod.id is null then
    p_ralat := 'Tiada permohonan sepadan. Semak no. rujukan dan no. Kad Pengenalan.';
    return;
  end if;

  -- Padanan berjaya — kosongkan kaunter.
  delete from semak_percubaan where no_rujukan = v_ruj;
end $$;


create or replace function rmt_hantar(p_data jsonb)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare
  v_id   uuid;
  v_ruj  text;
  v_tel  text := _bersih(p_data->>'penjaga_telefon');
  v_ic   text := upper(regexp_replace(coalesce(p_data->>'murid_ic',''), '[^0-9]', '', 'g'));
begin
  -- Pengesahan input. Jangan percaya apa-apa dari klien.
  if _bersih(p_data->>'penjaga_nama') is null
     or length(p_data->>'penjaga_nama') > 150 then
    raise exception 'Nama penjaga tidak sah';
  end if;
  if v_tel is null or v_tel !~ '^[0-9+\- ]{9,20}$' then
    raise exception 'Nombor telefon tidak sah';
  end if;
  if v_ic !~ '^[0-9]{12}$' then
    raise exception 'No. Kad Pengenalan murid mesti 12 angka';
  end if;
  if not coalesce((p_data->>'akuan_benar')::boolean, false)
     or not coalesce((p_data->>'persetujuan_pdpa')::boolean, false) then
    raise exception 'Akuan dan persetujuan PDPA wajib ditanda';
  end if;
  if not exists (select 1 from sekolah
                 where id = (p_data->>'sekolah_id')::uuid and aktif) then
    raise exception 'Sekolah tidak sah';
  end if;

  -- Perisai flood ringkas: had permohonan per nombor telefon per hari.
  if (select count(*) from permohonan
      where penjaga_telefon = v_tel and tarikh_hantar > now() - interval '1 day')
     >= _tetapan_int('had_hantar_per_telefon_sehari', 5) then
    raise exception 'Terlalu banyak permohonan dari nombor ini hari ini';
  end if;

  v_ruj := _rujukan_baru();

  insert into permohonan (
    no_rujukan, sekolah_id, penjaga_nama, penjaga_telefon, penjaga_hubungan,
    murid_nama, murid_ic, murid_tahun, murid_kelas,
    bil_isi_rumah, pendapatan_isi_rumah, ekasih, no_ekasih,
    akuan_benar, persetujuan_pdpa
  ) values (
    v_ruj,
    (p_data->>'sekolah_id')::uuid,
    _bersih(p_data->>'penjaga_nama'),
    v_tel,
    _bersih(p_data->>'penjaga_hubungan'),
    _bersih(p_data->>'murid_nama'),
    v_ic,
    (p_data->>'murid_tahun')::int,
    _bersih(p_data->>'murid_kelas'),
    (p_data->>'bil_isi_rumah')::int,
    (p_data->>'pendapatan_isi_rumah')::numeric,
    coalesce((p_data->>'ekasih')::boolean, false),
    _bersih(p_data->>'no_ekasih'),
    true, true
  ) returning id into v_id;

  perform _audit(v_id, v_ruj, 'HANTAR', null, 'DIHANTAR', null,
                 jsonb_build_object('saringan', _saringan(v_id)), 'pemohon');

  return jsonb_build_object('no_rujukan', v_ruj, 'status', 'DIHANTAR');
exception
  when unique_violation then
    raise exception 'Murid ini sudah ada permohonan aktif untuk sesi ini';
end $$;

-- Semak status: no_rujukan + IC murid, dengan had percubaan.
create or replace function rmt_semak_status(p_no_rujukan text, p_murid_ic text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare p permohonan; v_t record;
begin
  select * into v_t from _sahkan_pemohon(p_no_rujukan, p_murid_ic) as t(r, e);
  if v_t.e is not null then
    return jsonb_build_object('ralat', v_t.e);
  end if;
  p := v_t.r;

  return jsonb_build_object(
    'no_rujukan',   p.no_rujukan,
    'status',       p.status,
    'murid_nama',   p.murid_nama,
    'sekolah',      (select nama from sekolah where id = p.sekolah_id),
    'tarikh_hantar', p.tarikh_hantar,
    -- Catatan penyemak didedahkan HANYA bila dipulangkan, supaya pemohon
    -- tahu apa yang perlu dibetulkan. Catatan dalaman lain tak didedahkan.
    'perlu_betulkan', case when p.status = 'DIPULANGKAN'
                           then p.catatan_penyemak end,
    'tamat_tempoh_betul', case when p.status = 'DIPULANGKAN'
                               then p.tamat_tempoh_betul end,
    'sebab_tolak',  case when p.status = 'TOLAK' then p.sebab_tolak end,
    'tarikh_keputusan', p.tarikh_keputusan
  );
end $$;

create or replace function rmt_tarik_balik(p_no_rujukan text, p_murid_ic text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare p permohonan; v_t record;
begin
  select * into v_t from _sahkan_pemohon(p_no_rujukan, p_murid_ic) as t(r, e);
  if v_t.e is not null then return jsonb_build_object('ralat', v_t.e); end if;
  p := v_t.r;

  if p.status not in ('DIHANTAR','DIPULANGKAN','DALAM_SEMAKAN') then
    return jsonb_build_object('ralat',
      'Permohonan pada status ini tidak boleh ditarik balik.');
  end if;

  update permohonan set status = 'DITARIK_BALIK' where id = p.id;
  perform _audit(p.id, p.no_rujukan, 'TARIK_BALIK', p.status, 'DITARIK_BALIK',
                 null, null, 'pemohon');
  return jsonb_build_object('status', 'DITARIK_BALIK');
end $$;

create or replace function rmt_hantar_semula(
  p_no_rujukan text, p_murid_ic text, p_data jsonb)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare p permohonan; v_lama jsonb; v_t record;
begin
  select * into v_t from _sahkan_pemohon(p_no_rujukan, p_murid_ic) as t(r, e);
  if v_t.e is not null then return jsonb_build_object('ralat', v_t.e); end if;
  p := v_t.r;

  if p.status <> 'DIPULANGKAN' then
    return jsonb_build_object('ralat',
      'Hanya permohonan yang dipulangkan boleh dihantar semula.');
  end if;
  if p.tamat_tempoh_betul is not null and p.tamat_tempoh_betul < current_date then
    return jsonb_build_object('ralat', 'Tempoh pembetulan sudah tamat.');
  end if;

  v_lama := jsonb_build_object(
    'penjaga_nama', p.penjaga_nama, 'penjaga_telefon', p.penjaga_telefon,
    'murid_nama', p.murid_nama, 'murid_tahun', p.murid_tahun,
    'murid_kelas', p.murid_kelas, 'bil_isi_rumah', p.bil_isi_rumah,
    'pendapatan_isi_rumah', p.pendapatan_isi_rumah,
    'ekasih', p.ekasih, 'no_ekasih', p.no_ekasih);

  update permohonan set
    penjaga_nama         = coalesce(_bersih(p_data->>'penjaga_nama'), penjaga_nama),
    penjaga_telefon      = coalesce(_bersih(p_data->>'penjaga_telefon'), penjaga_telefon),
    penjaga_hubungan     = coalesce(_bersih(p_data->>'penjaga_hubungan'), penjaga_hubungan),
    murid_nama           = coalesce(_bersih(p_data->>'murid_nama'), murid_nama),
    murid_tahun          = coalesce((p_data->>'murid_tahun')::int, murid_tahun),
    murid_kelas          = coalesce(_bersih(p_data->>'murid_kelas'), murid_kelas),
    bil_isi_rumah        = coalesce((p_data->>'bil_isi_rumah')::int, bil_isi_rumah),
    pendapatan_isi_rumah = coalesce((p_data->>'pendapatan_isi_rumah')::numeric,
                                    pendapatan_isi_rumah),
    ekasih               = coalesce((p_data->>'ekasih')::boolean, ekasih),
    no_ekasih            = coalesce(_bersih(p_data->>'no_ekasih'), no_ekasih),
    status               = 'DIHANTAR',
    catatan_penyemak     = null,
    tamat_tempoh_betul   = null
  where id = p.id;

  perform _audit(p.id, p.no_rujukan, 'HANTAR_SEMULA', 'DIPULANGKAN', 'DIHANTAR',
                 null, jsonb_build_object('sebelum', v_lama, 'selepas', p_data),
                 'pemohon');
  return jsonb_build_object('status', 'DIHANTAR');
end $$;

-- =====================================================================
-- STAF (authenticated)
-- =====================================================================

create or replace function _staf_sah(p_peranan peranan_staf[], p_permohonan_id uuid)
returns staf language plpgsql stable security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan;
begin
  select * into s from staf where id = auth.uid() and aktif;
  if s.id is null then raise exception 'Tidak dibenarkan — sila log masuk semula'; end if;
  if not (s.peranan = any(p_peranan) or s.peranan = 'admin') then
    raise exception 'Peranan anda tiada kebenaran untuk tindakan ini';
  end if;
  if p_permohonan_id is not null then
    select * into p from permohonan where id = p_permohonan_id;
    if p.id is null then raise exception 'Permohonan tidak dijumpai'; end if;
    if s.peranan <> 'admin' and p.sekolah_id <> s.sekolah_id then
      raise exception 'Permohonan ini bukan di bawah sekolah anda';
    end if;
  end if;
  return s;
end $$;

create or replace function rmt_mula_semakan(p_id uuid)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan;
begin
  s := _staf_sah(array['penyemak']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status <> 'DIHANTAR' then
    raise exception 'Hanya permohonan berstatus DIHANTAR boleh dimulakan';
  end if;
  update permohonan set status = 'DALAM_SEMAKAN', penyemak_id = s.id,
         tarikh_semakan = now() where id = p_id;
  perform _audit(p_id, p.no_rujukan, 'MULA_SEMAKAN', p.status, 'DALAM_SEMAKAN');
  return jsonb_build_object('status','DALAM_SEMAKAN');
end $$;

create or replace function rmt_pulangkan(p_id uuid, p_catatan text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan; v_had int; v_hari int;
begin
  s := _staf_sah(array['penyemak','pelulus']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status not in ('DIHANTAR','DALAM_SEMAKAN') then
    raise exception 'Status % tidak boleh dipulangkan', p.status;
  end if;
  if _bersih(p_catatan) is null then
    raise exception 'Catatan wajib — pemohon perlu tahu apa yang hendak dibetulkan';
  end if;

  v_had  := _tetapan_int('had_pulangan', 3);
  v_hari := _tetapan_int('hari_tempoh_betul', 14);
  if p.kali_dipulangkan >= v_had then
    raise exception 'Had % kali pulangan sudah dicapai. Buat keputusan LULUS atau TOLAK.', v_had;
  end if;

  update permohonan set
    status = 'DIPULANGKAN',
    catatan_penyemak = _bersih(p_catatan),
    kali_dipulangkan = kali_dipulangkan + 1,
    penyemak_id = coalesce(penyemak_id, s.id),
    tamat_tempoh_betul = current_date + v_hari
  where id = p_id;

  perform _audit(p_id, p.no_rujukan, 'PULANGKAN', p.status, 'DIPULANGKAN',
                 _bersih(p_catatan),
                 jsonb_build_object('kali_dipulangkan', p.kali_dipulangkan + 1));
  return jsonb_build_object('status','DIPULANGKAN');
end $$;

create or replace function rmt_ke_kelulusan(p_id uuid, p_catatan text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan;
begin
  s := _staf_sah(array['penyemak']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status not in ('DIHANTAR','DALAM_SEMAKAN') then
    raise exception 'Status % tidak boleh dihantar untuk kelulusan', p.status;
  end if;
  update permohonan set status = 'DALAM_KELULUSAN',
         penyemak_id = s.id,   -- penyemak rasmi = orang yang hantar ke kelulusan
         catatan_penyemak = _bersih(p_catatan),
         tarikh_semakan = coalesce(tarikh_semakan, now())
   where id = p_id;
  perform _audit(p_id, p.no_rujukan, 'KE_KELULUSAN', p.status, 'DALAM_KELULUSAN',
                 _bersih(p_catatan));
  return jsonb_build_object('status','DALAM_KELULUSAN');
end $$;

-- Tolak terus tanpa ke pelulus, untuk kes yang jelas tidak layak.
-- Sebab WAJIB — ini yang pemohon nampak dan yang audit akan soal.
create or replace function rmt_tolak_terus(p_id uuid, p_sebab text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan;
begin
  s := _staf_sah(array['penyemak']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status not in ('DIHANTAR','DALAM_SEMAKAN') then
    raise exception 'Status % tidak boleh ditolak terus', p.status;
  end if;
  if _bersih(p_sebab) is null then raise exception 'Sebab tolak wajib'; end if;

  update permohonan set status = 'TOLAK', sebab_tolak = _bersih(p_sebab),
         penyemak_id = coalesce(penyemak_id, s.id), tarikh_keputusan = now()
   where id = p_id;
  perform _audit(p_id, p.no_rujukan, 'TOLAK_TERUS', p.status, 'TOLAK', _bersih(p_sebab));
  return jsonb_build_object('status','TOLAK');
end $$;

create or replace function rmt_putuskan(p_id uuid, p_lulus boolean, p_sebab text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan; v_status status_permohonan;
begin
  s := _staf_sah(array['pelulus']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status <> 'DALAM_KELULUSAN' then
    raise exception 'Hanya permohonan DALAM_KELULUSAN boleh diputuskan';
  end if;
  -- Pengasingan tugas. Medan penyemak_id sahaja tidak mencukupi: ia hanya
  -- merekod seorang. Jejak audit merekod SETIAP tindakan semakan, jadi ia
  -- yang menutup kes seperti admin yang menyemak sendiri lalu meluluskan.
  if p.penyemak_id = s.id or exists (
       select 1 from audit_log a
        where a.permohonan_id = p_id
          and a.pelaku_id = s.id
          and a.tindakan in ('MULA_SEMAKAN','KE_KELULUSAN','PULANGKAN','TOLAK_TERUS')
     ) then
    raise exception 'Anda terlibat dalam semakan permohonan ini. Pelulus lain perlu memutuskan.';
  end if;
  if not p_lulus and _bersih(p_sebab) is null then
    raise exception 'Sebab tolak wajib';
  end if;

  v_status := case when p_lulus then 'LULUS' else 'TOLAK' end;
  update permohonan set status = v_status, pelulus_id = s.id,
         catatan_pelulus = _bersih(p_sebab),
         sebab_tolak = case when p_lulus then null else _bersih(p_sebab) end,
         tarikh_keputusan = now()
   where id = p_id;
  perform _audit(p_id, p.no_rujukan, 'KEPUTUSAN', p.status, v_status, _bersih(p_sebab));
  return jsonb_build_object('status', v_status);
end $$;

-- Pelulus pulangkan kepada penyemak (bukan kepada pemohon).
create or replace function rmt_pulang_ke_penyemak(p_id uuid, p_catatan text)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare s staf; p permohonan;
begin
  s := _staf_sah(array['pelulus']::peranan_staf[], p_id);
  select * into p from permohonan where id = p_id;
  if p.status <> 'DALAM_KELULUSAN' then
    raise exception 'Status % tidak boleh dipulangkan kepada penyemak', p.status;
  end if;
  if _bersih(p_catatan) is null then raise exception 'Catatan wajib'; end if;
  update permohonan set status = 'DALAM_SEMAKAN', catatan_pelulus = _bersih(p_catatan)
   where id = p_id;
  perform _audit(p_id, p.no_rujukan, 'PULANG_KE_PENYEMAK', p.status, 'DALAM_SEMAKAN',
                 _bersih(p_catatan));
  return jsonb_build_object('status','DALAM_SEMAKAN');
end $$;

create or replace function rmt_saringan(p_id uuid)
returns jsonb language plpgsql stable security definer set search_path = public, pg_temp as $$
begin
  perform _staf_sah(array['penyemak','pelulus']::peranan_staf[], p_id);
  return _saringan(p_id);
end $$;

-- =====================================================================
-- SISTEM — dipanggil oleh GitHub Actions cron (lihat .github/workflows)
-- =====================================================================

create or replace function rmt_sweep()
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare v_gugur int := 0; v_anon int := 0; r record;
begin
  -- 1) Gugurkan permohonan yang tamat tempoh pembetulan.
  for r in select id, no_rujukan, status from permohonan
            where status = 'DIPULANGKAN'
              and tamat_tempoh_betul is not null
              and tamat_tempoh_betul < current_date
  loop
    update permohonan set status = 'GUGUR' where id = r.id;
    perform _audit(r.id, r.no_rujukan, 'AUTO_GUGUR', r.status, 'GUGUR',
                   'Tempoh pembetulan tamat', null, 'sistem');
    v_gugur := v_gugur + 1;
  end loop;

  -- 2) Retention PDPA: anonimkan rekod yang melepasi tempoh simpanan.
  --    Baris dikekalkan untuk statistik, data peribadi dibuang.
  for r in select id, no_rujukan, status from permohonan
            where padam_selepas < current_date and not dianonimkan
  loop
    update permohonan set
      penjaga_nama = '[dibuang]', penjaga_telefon = '[dibuang]',
      murid_nama   = '[dibuang]',
      murid_ic     = 'ANON-' || substr(md5(id::text), 1, 12),
      murid_kelas  = null, no_ekasih = null,
      catatan_penyemak = null, catatan_pelulus = null,
      dianonimkan  = true
    where id = r.id;
    perform _audit(r.id, r.no_rujukan, 'ANONIM_RETENTION', r.status, r.status,
                   'Tempoh simpanan tamat', null, 'sistem');
    v_anon := v_anon + 1;
  end loop;

  delete from semak_percubaan where reset_pada < now() - interval '1 day';

  return jsonb_build_object('gugur', v_gugur, 'dianonimkan', v_anon, 'pada', now());
end $$;

-- =====================================================================
-- Kebenaran EXECUTE — eksplisit, bukan default
-- =====================================================================
revoke all on function rmt_hantar(jsonb)                       from public;
revoke all on function rmt_semak_status(text,text)             from public;
revoke all on function rmt_tarik_balik(text,text)              from public;
revoke all on function rmt_hantar_semula(text,text,jsonb)      from public;
revoke all on function rmt_mula_semakan(uuid)                  from public;
revoke all on function rmt_pulangkan(uuid,text)                from public;
revoke all on function rmt_ke_kelulusan(uuid,text)             from public;
revoke all on function rmt_tolak_terus(uuid,text)              from public;
revoke all on function rmt_putuskan(uuid,boolean,text)         from public;
revoke all on function rmt_pulang_ke_penyemak(uuid,text)       from public;
revoke all on function rmt_saringan(uuid)                      from public;
revoke all on function rmt_sweep()                             from public;
revoke all on function _saringan(uuid)                         from public;
revoke all on function _audit(uuid,text,text,status_permohonan,status_permohonan,text,jsonb,text) from public;
revoke all on function _rujukan_baru()                         from public;
revoke all on function _kira_cubaan(text)                      from public;
revoke all on function _sahkan_pemohon(text,text)              from public;
revoke all on function _staf_sah(peranan_staf[],uuid)          from public;

grant execute on function rmt_hantar(jsonb)                  to anon, authenticated;
grant execute on function rmt_semak_status(text,text)        to anon, authenticated;
grant execute on function rmt_tarik_balik(text,text)         to anon, authenticated;
grant execute on function rmt_hantar_semula(text,text,jsonb) to anon, authenticated;

grant execute on function rmt_mula_semakan(uuid)             to authenticated;
grant execute on function rmt_pulangkan(uuid,text)           to authenticated;
grant execute on function rmt_ke_kelulusan(uuid,text)        to authenticated;
grant execute on function rmt_tolak_terus(uuid,text)         to authenticated;
grant execute on function rmt_putuskan(uuid,boolean,text)    to authenticated;
grant execute on function rmt_pulang_ke_penyemak(uuid,text)  to authenticated;
grant execute on function rmt_saringan(uuid)                 to authenticated;

-- rmt_sweep() hanya untuk service_role (cron). JANGAN beri kepada anon.
grant execute on function rmt_sweep() to service_role;
