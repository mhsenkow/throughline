#!/usr/bin/env bash
# Deploy Throughline to the STAGING copy at mhsenkow.org/notebook.
#
#   ./deploy.sh [cpanel-user] [remote-dir]
#
# PRODUCTION IS NOT HERE. ibm.io is served by the `portfolio` Cloudflare
# Worker (OpenNext/Next.js), not by GreenGeeks — see "Production" in
# README.md. GreenGeeks serves mhsenkow.org only, which makes it a useful
# staging URL and nothing more.
#
# Uses SFTP, not rsync/scp. GreenGeeks disables shell access on this plan
# ("Shell access is not enabled on your account"), but leaves the SFTP
# subsystem open — key auth works, an interactive shell does not. rsync needs
# a shell on the far end, so it cannot be used here.
#
# public_html is the docroot for mhsenkow.org (the primary domain). The
# public_html/ibm.io folder is a legacy addon-domain docroot that no longer
# serves anything — ibm.io resolves to Cloudflare, not to this server.
set -euo pipefail

USER="${1:-mhsenkow}"
HOST="chi202.greengeeks.net"
REMOTE="${2:-/home/${USER}/public_html/notebook}"

./check.sh

echo "→ uploading to ${REMOTE}"
sftp -b - -o BatchMode=yes "${USER}@${HOST}" <<EOF
-mkdir ${REMOTE}
put index.html ${REMOTE}/index.html
put library.json ${REMOTE}/library.json
put .htaccess ${REMOTE}/.htaccess
EOF

echo "→ verifying it is actually being served"
sleep 1
code=$(curl -s -o /dev/null -w '%{http_code}' "https://mhsenkow.org/notebook/")
echo "  https://mhsenkow.org/notebook/ → HTTP ${code}"

echo
echo "Staging deployed: https://mhsenkow.org/notebook/"
echo
echo "To ship PRODUCTION (ibm.io/notebook):"
echo "  ./publish.sh"
echo "  cd ~/portfolio/portfolio && pnpm run deploy"
