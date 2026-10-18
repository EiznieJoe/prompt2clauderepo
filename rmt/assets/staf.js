/* Papan pemuka pegawai. Butang yang dipapar ikut peranan, tetapi itu UX
   sahaja — kebenaran sebenar dikuatkuasakan dalam fungsi RPC di Postgres,
   jadi memanggil RPC terus dari curl pun tetap ditolak. */
(function () {
  "use strict";
  var el = UI.el, papar = UI.papar, sorok = UI.sorok;
  var $ = function (id) { return document.getElementById(id); };

  var saya = null;        // baris staf
  var baris = [];         // permohonan yang dimuatkan
  var pilihan = null;     // permohonan terpilih
  var sla = { semakan: 7, kelulusan: 5 };

  /* ---------- Log masuk ---------- */
  $("borang-masuk").onsubmit = function (ev) {
    ev.preventDefault();
    var m = $("msg-masuk");
    papar(m, "info", "Log masuk…");
    $("btn-masuk").disabled = true;
    RMT.logMasuk($("emel").value.trim(), $("katalaluan").value)
      .then(mulakan)
      .catch(function (e) {
        papar(m, "err", e.status === 400
          ? "Emel atau kata laluan salah."
          : e.message);
      })
      .then(function () { $("btn-masuk").disabled = false; $("katalaluan").value = ""; });
  };

  $("btn-keluar").onclick = function () {
    RMT.logKeluar().then(function () { location.reload(); });
  };

  function mulakan() {
    return RMT.pilih("staf", "select=id,nama,peranan,sekolah_id,aktif&id=eq." + RMT.sesi().user_id)
      .then(function (rows) {
        if (!rows.length || !rows[0].aktif) {
          throw new Error("Akaun ini belum didaftarkan sebagai pegawai, atau tidak aktif. Hubungi admin.");
        }
        saya = rows[0];
        $("borang-masuk").hidden = true;
        $("papan").hidden = false;
        $("btn-keluar").hidden = false;
        $("siapa").textContent = saya.nama + " — " + saya.peranan;
        return RMT.pilih("tetapan", "select=kunci,nilai");
      })
      .then(function (t) {
        (t || []).forEach(function (r) {
          if (r.kunci === "sla_hari_semakan") sla.semakan = Number(r.nilai);
          if (r.kunci === "sla_hari_kelulusan") sla.kelulusan = Number(r.nilai);
        });
        return muat();
      })
      .catch(function (e) {
        papar($("msg-masuk"), "err", e.message);
        RMT.logKeluar();
      });
  }

  /* ---------- Muat senarai ---------- */
  var MEDAN = "id,no_rujukan,status,murid_nama,murid_ic,murid_tahun,murid_kelas," +
    "penjaga_nama,penjaga_telefon,penjaga_hubungan,bil_isi_rumah," +
    "pendapatan_isi_rumah,pendapatan_per_kapita,ekasih,no_ekasih," +
    "kali_dipulangkan,catatan_penyemak,catatan_pelulus,sebab_tolak," +
    "penyemak_id,pelulus_id,tarikh_hantar,tarikh_semakan,tarikh_keputusan," +
    "tamat_tempoh_betul,sekolah_id";

  function muat() {
    var q = "select=" + MEDAN + "&order=tarikh_hantar.asc&limit=2000";
    var s = $("f-status").value;
    if (s) q += "&status=eq." + s;
    papar($("msg-papan"), "info", "Memuatkan…");
    return RMT.pilih("permohonan", q).then(function (rows) {
      baris = rows || [];
      sorok($("msg-papan"));
      lukisSenarai();
    }).catch(function (e) { papar($("msg-papan"), "err", e.message); });
  }

  $("btn-muat").onclick = muat;
  $("f-status").onchange = muat;
  $("f-cari").oninput = lukisSenarai;

  function ditapis() {
    var k = $("f-cari").value.trim().toLowerCase();
    if (!k) return baris;
    return baris.filter(function (r) {
      return (r.murid_nama || "").toLowerCase().indexOf(k) >= 0 ||
             (r.no_rujukan || "").toLowerCase().indexOf(k) >= 0;
    });
  }

  function lambat(r) {
    var hari = UI.hariSejak(r.tarikh_hantar);
    if (r.status === "DIHANTAR" || r.status === "DALAM_SEMAKAN") return hari > sla.semakan;
    if (r.status === "DALAM_KELULUSAN") return UI.hariSejak(r.tarikh_semakan) > sla.kelulusan;
    return false;
  }

  function lukisSenarai() {
    var rows = ditapis();
    var tb = $("senarai");
    tb.textContent = "";

    if (!rows.length) {
      tb.appendChild(el("tr", null, [el("td", { colspan: "6", text: "Tiada permohonan." })]));
    }
    rows.forEach(function (r) {
      var hari = UI.hariSejak(r.tarikh_hantar);
      var tdUmur = el("td", { text: hari + " hari" });
      if (lambat(r)) { tdUmur.className = "late"; tdUmur.textContent = hari + " hari — lewat SLA"; }

      var tr = el("tr", { "aria-selected": pilihan && pilihan.id === r.id ? "true" : "false" }, [
        el("td", { text: r.no_rujukan }),
        el("td", { text: r.murid_nama }),
        el("td", { text: String(r.murid_tahun) }),
        el("td", { text: UI.rm(r.pendapatan_per_kapita) }),
        el("td", null, [UI.lencana(r.status)]),
        tdUmur,
      ]);
      tr.onclick = function () { pilih(r); };
      tb.appendChild(tr);
    });

    var kira = {};
    baris.forEach(function (r) { kira[r.status] = (kira[r.status] || 0) + 1; });
    var lewat = baris.filter(lambat).length;
    $("ringkasan").textContent = rows.length + " dipaparkan daripada " + baris.length +
      " dimuatkan" + (lewat ? " · " + lewat + " lewat SLA" : "") + " · " +
      Object.keys(kira).map(function (k) { return (UI.LABEL[k] || k) + ": " + kira[k]; }).join(" · ");
  }

  /* ---------- Butiran ---------- */
  function pilih(r) {
    pilihan = r;
    lukisSenarai();
    $("butiran").hidden = false;
    $("d-ruj").textContent = r.no_rujukan;
    $("d-badge").textContent = "";
    $("d-badge").appendChild(UI.lencana(r.status));
    $("d-catatan").value = "";
    sorok($("msg-tindakan"));

    var kv = $("d-kv");
    kv.textContent = "";
    [["Murid", r.murid_nama],
     ["No. KP murid", r.murid_ic],
     ["Tahun / kelas", r.murid_tahun + (r.murid_kelas ? " " + r.murid_kelas : "")],
     ["Penjaga", r.penjaga_nama + " (" + r.penjaga_hubungan + ")"],
     ["Telefon", r.penjaga_telefon],
     ["Isi rumah", r.bil_isi_rumah + " orang"],
     ["Pendapatan isi rumah", UI.rm(r.pendapatan_isi_rumah)],
     ["Pendapatan per kapita", UI.rm(r.pendapatan_per_kapita)],
     ["eKasih", r.ekasih ? ("Ya" + (r.no_ekasih ? " — " + r.no_ekasih : "")) : "Tidak"],
     ["Kali dipulangkan", String(r.kali_dipulangkan)],
     ["Tarikh hantar", UI.tarikh(r.tarikh_hantar, true)],
     ["Catatan penyemak", r.catatan_penyemak || "—"],
     ["Catatan pelulus", r.catatan_pelulus || "—"],
     ["Sebab tolak", r.sebab_tolak || "—"],
    ].forEach(function (p) {
      kv.appendChild(el("dt", { text: p[0] }));
      kv.appendChild(el("dd", { text: p[1] == null ? "—" : String(p[1]) }));
    });

    lukisButang(r);
    lukisAudit(r);

    RMT.rpc("rmt_saringan", { p_id: r.id }).then(function (bendera) {
      var n = $("d-saringan");
      if (bendera && bendera.length) {
        n.hidden = false;
        n.textContent = "Saringan automatik menanda: " + bendera.join(" · ") +
          " — ini petunjuk sahaja, keputusan tetap di tangan anda.";
      } else { n.hidden = true; }
    }).catch(function () { $("d-saringan").hidden = true; });
  }

  function lukisAudit(r) {
    var ol = $("d-audit");
    ol.textContent = "";
    RMT.pilih("audit_log",
      "select=tindakan,pelaku_label,status_dari,status_ke,sebab,created_at" +
      "&permohonan_id=eq." + r.id + "&order=created_at.desc&limit=100")
      .then(function (rows) {
        if (!rows.length) { ol.appendChild(el("li", { text: "Tiada rekod." })); return; }
        rows.forEach(function (a) {
          ol.appendChild(el("li", null, [
            el("time", { text: UI.tarikh(a.created_at, true) }),
            el("span", {
              text: a.tindakan + " oleh " + a.pelaku_label +
                (a.status_dari ? " (" + a.status_dari + " → " + a.status_ke + ")" : "") +
                (a.sebab ? " — " + a.sebab : ""),
            }),
          ]));
        });
      })
      .catch(function (e) { ol.appendChild(el("li", { text: "Gagal memuatkan audit: " + e.message })); });
  }

  function lukisButang(r) {
    var wrap = $("d-butang");
    wrap.textContent = "";
    var peranan = saya.peranan;
    var boleh = function (p) { return peranan === p || peranan === "admin"; };

    function tambah(teks, kelas, kerja) {
      var b = el("button", { type: "button", class: "ghost" + (kelas ? " " + kelas : ""), text: teks });
      b.onclick = kerja;
      wrap.appendChild(b);
    }

    function jalan(nama, args, perluCatatan) {
      var catatan = $("d-catatan").value.trim();
      if (perluCatatan && !catatan) {
        return papar($("msg-tindakan"), "err", "Catatan wajib untuk tindakan ini.");
      }
      papar($("msg-tindakan"), "info", "Memproses…");
      RMT.rpc(nama, args(catatan)).then(function (res) {
        papar($("msg-tindakan"), "ok", "Status kini: " + (UI.LABEL[res.status] || res.status));
        return muat();
      }).then(function () {
        var segar = baris.filter(function (x) { return x.id === r.id; })[0];
        if (segar) pilih(segar); else { $("butiran").hidden = true; pilihan = null; }
      }).catch(function (e) { papar($("msg-tindakan"), "err", e.message); });
    }

    if (boleh("penyemak")) {
      if (r.status === "DIHANTAR") {
        tambah("Mula semakan", null, function () {
          jalan("rmt_mula_semakan", function () { return { p_id: r.id }; }, false);
        });
      }
      if (r.status === "DIHANTAR" || r.status === "DALAM_SEMAKAN") {
        tambah("Pulangkan kepada pemohon", null, function () {
          jalan("rmt_pulangkan", function (c) { return { p_id: r.id, p_catatan: c }; }, true);
        });
        tambah("Hantar untuk kelulusan", null, function () {
          jalan("rmt_ke_kelulusan", function (c) { return { p_id: r.id, p_catatan: c }; }, false);
        });
        tambah("Tolak terus (tidak layak)", "danger", function () {
          if (!window.confirm("Tolak terus tanpa ke pelulus? Pemohon akan nampak sebab yang anda tulis.")) return;
          jalan("rmt_tolak_terus", function (c) { return { p_id: r.id, p_sebab: c }; }, true);
        });
      }
    }

    if (boleh("pelulus") && r.status === "DALAM_KELULUSAN") {
      var sendiri = r.penyemak_id === saya.id;
      if (sendiri) {
        wrap.appendChild(el("span", { class: "hint",
          text: "Anda yang menyemak kes ini. Pelulus lain perlu memutuskan (pengasingan tugas)." }));
      } else {
        tambah("Lulus", null, function () {
          if (!window.confirm("Luluskan permohonan " + r.no_rujukan + "?")) return;
          jalan("rmt_putuskan", function (c) { return { p_id: r.id, p_lulus: true, p_sebab: c || null }; }, false);
        });
        tambah("Tolak", "danger", function () {
          jalan("rmt_putuskan", function (c) { return { p_id: r.id, p_lulus: false, p_sebab: c }; }, true);
        });
        tambah("Pulangkan kepada penyemak", null, function () {
          jalan("rmt_pulang_ke_penyemak", function (c) { return { p_id: r.id, p_catatan: c }; }, true);
        });
      }
    }

    if (!wrap.childNodes.length) {
      wrap.appendChild(el("span", { class: "hint", text: "Tiada tindakan tersedia untuk peranan anda pada status ini." }));
    }
  }

  /* ---------- Eksport ---------- */
  $("btn-csv").onclick = function () {
    var rows = ditapis();
    if (!rows.length) return papar($("msg-papan"), "err", "Tiada baris untuk dieksport.");
    var kepala = ["No. rujukan", "Status", "Murid", "No. KP", "Tahun", "Kelas",
      "Penjaga", "Telefon", "Hubungan", "Bil. isi rumah", "Pendapatan",
      "Per kapita", "eKasih", "Kali dipulangkan", "Tarikh hantar",
      "Tarikh keputusan", "Sebab tolak"];
    var data = rows.map(function (r) {
      return [r.no_rujukan, UI.LABEL[r.status] || r.status, r.murid_nama, r.murid_ic,
        r.murid_tahun, r.murid_kelas || "", r.penjaga_nama, r.penjaga_telefon,
        r.penjaga_hubungan, r.bil_isi_rumah, r.pendapatan_isi_rumah,
        r.pendapatan_per_kapita, r.ekasih ? "Ya" : "Tidak", r.kali_dipulangkan,
        UI.tarikh(r.tarikh_hantar, true), UI.tarikh(r.tarikh_keputusan, true),
        r.sebab_tolak || ""];
    });
    UI.muatTurunCsv("permohonan-rmt-" + new Date().toISOString().slice(0, 10) + ".csv",
      [kepala].concat(data));
    papar($("msg-papan"), "warn",
      "Fail CSV mengandungi data peribadi. Simpan dalam peranti sekolah sahaja dan padam selepas guna.");
  };

  /* ---------- Sambung sesi yang masih hidup ---------- */
  if (RMT.sesi()) mulakan();
})();
