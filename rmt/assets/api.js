/* Lapisan API — fetch mentah ke Supabase. Tiada dependency luar, tiada
   CDN, jadi tiada pihak ketiga yang perlu dipercayai di muka surat awam. */
(function () {
  "use strict";

  var C = window.RMT_CONFIG || {};
  if (!C.SUPABASE_URL || !C.SUPABASE_ANON_KEY) {
    console.error("RMT_CONFIG tidak lengkap — semak config.js");
  }
  var BASE = (C.SUPABASE_URL || "").replace(/\/+$/, "");
  var ANON = C.SUPABASE_ANON_KEY || "";

  /* Sesi staf disimpan dalam sessionStorage, bukan localStorage: hilang
     bila tab ditutup, jadi tempoh pendedahan token lebih pendek. */
  var SESI_KEY = "rmt_sesi";

  function simpanSesi(s) {
    try { sessionStorage.setItem(SESI_KEY, JSON.stringify(s)); } catch (e) {}
  }
  function ambilSesi() {
    try {
      var raw = sessionStorage.getItem(SESI_KEY);
      if (!raw) return null;
      var s = JSON.parse(raw);
      if (!s.access_token || !s.expires_at || s.expires_at * 1000 < Date.now()) {
        buangSesi();
        return null;
      }
      return s;
    } catch (e) { return null; }
  }
  function buangSesi() {
    try { sessionStorage.removeItem(SESI_KEY); } catch (e) {}
  }

  function pesanRalat(data, res) {
    if (data && typeof data === "object") {
      var m = data.message || data.error_description || data.error || data.msg;
      if (m) return String(m);
    }
    if (res && res.status === 401) return "Sesi tamat. Sila log masuk semula.";
    if (res && res.status === 429) return "Terlalu banyak permintaan. Cuba sebentar lagi.";
    return "Sambungan gagal. Cuba lagi.";
  }

  function minta(path, opts) {
    opts = opts || {};
    var sesi = ambilSesi();
    var h = {
      apikey: ANON,
      Authorization: "Bearer " + ((opts.anon ? null : sesi && sesi.access_token) || ANON),
      "Content-Type": "application/json",
    };
    if (opts.headers) {
      for (var k in opts.headers) h[k] = opts.headers[k];
    }
    return fetch(BASE + path, {
      method: opts.method || "GET",
      headers: h,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (res) {
      return res.text().then(function (t) {
        var data = null;
        if (t) { try { data = JSON.parse(t); } catch (e) { data = t; } }
        if (!res.ok) {
          var err = new Error(pesanRalat(data, res));
          err.status = res.status;
          throw err;
        }
        return data;
      });
    }, function () {
      throw new Error("Tiada sambungan internet, atau pelayan tidak dapat dihubungi.");
    });
  }

  function rpc(nama, args, opts) {
    return minta("/rest/v1/rpc/" + nama, {
      method: "POST",
      body: args || {},
      anon: opts && opts.anon,
    });
  }

  function pilih(jadual, query) {
    return minta("/rest/v1/" + jadual + (query ? "?" + query : ""));
  }

  function logMasuk(emel, katalaluan) {
    return minta("/auth/v1/token?grant_type=password", {
      method: "POST",
      anon: true,
      body: { email: emel, password: katalaluan },
    }).then(function (d) {
      var sesi = {
        access_token: d.access_token,
        refresh_token: d.refresh_token,
        expires_at: d.expires_at || Math.floor(Date.now() / 1000) + (d.expires_in || 3600),
        email: d.user && d.user.email,
        user_id: d.user && d.user.id,
      };
      simpanSesi(sesi);
      return sesi;
    });
  }

  function logKeluar() {
    var sesi = ambilSesi();
    buangSesi();
    if (!sesi) return Promise.resolve();
    /* Revoke di server juga, bukan sekadar buang dari browser. */
    return minta("/auth/v1/logout", {
      method: "POST",
      headers: { Authorization: "Bearer " + sesi.access_token },
    }).catch(function () {});
  }

  window.RMT = {
    rpc: rpc,
    pilih: pilih,
    logMasuk: logMasuk,
    logKeluar: logKeluar,
    sesi: ambilSesi,
  };
})();
