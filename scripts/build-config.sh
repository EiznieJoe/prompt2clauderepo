#!/bin/sh
# Menjana rmt/assets/config.js dari environment variable Netlify.
# Dengan cara ini key tidak perlu di-commit, dan tukar projek Supabase
# hanya perlu tukar env var di dashboard Netlify.
#
# Set di Netlify: Site configuration -> Environment variables
#   SUPABASE_URL       = https://xxxx.supabase.co
#   SUPABASE_ANON_KEY  = eyJ...
#
# JANGAN sekali-kali letak SUPABASE_SERVICE_ROLE_KEY di sini — key itu
# memintas semua RLS dan tidak sepatutnya sampai ke browser.
set -eu

if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_ANON_KEY:-}" ]; then
  echo "RALAT: SUPABASE_URL dan SUPABASE_ANON_KEY belum ditetapkan." >&2
  echo "Tetapkan kedua-duanya dalam Netlify environment variables." >&2
  exit 1
fi

case "${SUPABASE_ANON_KEY}" in
  *service_role*)
    echo "RALAT: SUPABASE_ANON_KEY nampak macam service_role key. Hentikan build." >&2
    exit 1 ;;
esac

cat > rmt/assets/config.js <<EOF
/* Dijana semasa build. Jangan edit terus — edit env var di Netlify. */
window.RMT_CONFIG = {
  SUPABASE_URL: "${SUPABASE_URL}",
  SUPABASE_ANON_KEY: "${SUPABASE_ANON_KEY}",
};
EOF

echo "config.js dijana untuk ${SUPABASE_URL}"
