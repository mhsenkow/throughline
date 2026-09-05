#!/usr/bin/env bash
# Deploy Throughline to GreenGeeks over SSH.
#
#   ./deploy.sh <ssh-host> <cpanel-user> [remote-path]
#
# Example:
#   ./deploy.sh s123.greengeeks.com myuser public_html/notebook
#
# Uses the SSH key already in your agent — no password is handled here.
# Deploys one file. There is no build step because there is nothing to build.
set -euo pipefail

HOST="${1:?ssh host required, e.g. s123.greengeeks.com}"
USER="${2:?cpanel username required}"
REMOTE="${3:-public_html/notebook}"

echo "→ verifying the file parses before it leaves this machine"
node --check <(python3 -c "
import re,sys
s=open('index.html').read()
sys.stdout.write(re.search(r'<script type=\"module\">(.*)</script>',s,re.S).group(1))
") && echo "  syntax ok"

echo "→ ensuring ${REMOTE} exists on ${HOST}"
ssh "${USER}@${HOST}" "mkdir -p ~/${REMOTE}"

echo "→ uploading index.html"
rsync -avz --checksum index.html "${USER}@${HOST}:~/${REMOTE}/index.html"

echo
echo "Deployed. https://ibm.io/notebook"
echo
echo "The domain is proxied through Cloudflare, so purge the cache to see it:"
echo "  Cloudflare dashboard → Caching → Configuration → Purge Everything"
echo "  (or purge just https://ibm.io/notebook/index.html)"
