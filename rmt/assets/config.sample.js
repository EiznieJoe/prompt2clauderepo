// Salin fail ini kepada config.js untuk pembangunan setempat.
// Di Netlify, config.js dijana oleh scripts/build-config.sh dari
// environment variable SUPABASE_URL dan SUPABASE_ANON_KEY.
//
// Anon key memang direka untuk didedahkan di frontend — keselamatan
// datang dari RLS dan fungsi RPC, bukan dari menyembunyikan key ini.
// JANGAN sekali-kali letak service_role key di sini.
window.RMT_CONFIG = {
  SUPABASE_URL: "https://xxxxxxxxxxxx.supabase.co",
  SUPABASE_ANON_KEY: "eyJ...",
};
