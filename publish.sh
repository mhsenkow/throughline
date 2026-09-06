#!/usr/bin/env bash
# Publish Throughline to PRODUCTION (ibm.io/notebook).
#
#   ./publish.sh [path-to-portfolio-repo]
#
# Copies the app into the portfolio Worker's static assets and regenerates the
# CSP with a hash of this exact build, then leaves the deploy to you.
#
# WHY A HASH: script-src 'unsafe-inline' would let ANY injected inline script
# run — including one smuggled through model output, which could hook fetch and
# read an API key out of the Authorization header. A hash pins execution to
# this one script. It changes on every edit, so it must be regenerated here
# rather than written by hand.
set -euo pipefail

PORT_REPO="${1:-$HOME/portfolio/portfolio}"
[ -d "$PORT_REPO/public" ] || { echo "No portfolio repo at $PORT_REPO"; exit 1; }

./check.sh

echo "→ hashing the inline script"
HASH=$(python3 -c "
import re, hashlib, base64
s = open('index.html', encoding='utf-8').read()
m = re.search(r'<script type=\"module\">(.*?)</script>', s, re.S)
print(base64.b64encode(hashlib.sha256(m.group(1).encode('utf-8')).digest()).decode())
")
echo "  sha256-${HASH}"

mkdir -p "$PORT_REPO/public/notebook"
cp index.html "$PORT_REPO/public/notebook/index.html"
cp library.json "$PORT_REPO/public/notebook/library.json"
echo "→ copied to $PORT_REPO/public/notebook/"

python3 - "$PORT_REPO/public/_headers" "$HASH" <<'PY'
import sys, re
path, h = sys.argv[1], sys.argv[2]
s = open(path).read()

# Carry a SHORT ROLLING WINDOW of recent hashes, not just the previous one.
#
# Cloudflare edge nodes do not update in lockstep. For a few seconds after a
# deploy, one node can serve older HTML while another serves the new policy —
# and a visitor landing on that pair gets a page whose script is blocked
# outright. Carrying one predecessor covers a one-version lag; two deploys in
# quick succession can leave a node two versions behind, which is exactly the
# case that got through. Three total costs a few bytes of header and covers it.
KEEP = 3
old = re.findall(r"'(sha256-[^']+)'", s)
window = [f'sha256-{h}'] + [x for x in old if x != f'sha256-{h}']
prev = ''.join(f" '{x}'" for x in window[1:KEEP])

block = f"""/notebook/*
  Cache-Control: public, max-age=60
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()
  Content-Security-Policy: default-src 'self'; script-src 'sha256-{h}'{prev} 'wasm-unsafe-eval' https://static.cloudflareinsights.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; worker-src 'self' blob: https://cdn.jsdelivr.net; connect-src 'self' https://cloudflareinsights.com https://generativelanguage.googleapis.com https://api.groq.com https://openrouter.ai https://api.anthropic.com https://api.openai.com https://router.huggingface.co https://api.cerebras.ai https://api.mistral.ai https://api.deepseek.com https://api.together.xyz https://api.x.ai https://huggingface.co https://cdn.jsdelivr.net https://cdn-lfs.huggingface.co https://cdn-lfs-us-1.huggingface.co https://us.aws.cdn.hf.co https://eu.aws.cdn.hf.co http://localhost:11434 http://127.0.0.1:11434 http://localhost:1234 http://127.0.0.1:1234; base-uri 'none'; object-src 'none'; form-action 'none'
"""
if '/notebook/*' in s:
    s = re.sub(r'/notebook/\*\n(?:  .*\n)*', block, s)
else:
    s = s.rstrip('\n') + '\n\n' + block
open(path, 'w').write(s)
print("→ _headers updated with the build hash")
PY

echo
echo "Staged. To ship:"
echo "  cd $PORT_REPO && pnpm run deploy"
