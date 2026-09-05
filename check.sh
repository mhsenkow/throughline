#!/usr/bin/env bash
# Structural checks for the single-file build. Run from the repo root.
# deploy.sh and publish.sh both call this before shipping anything.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "→ JS syntax"
node --check <(python3 -c "
import re,sys
s=open('index.html',encoding='utf-8').read()
sys.stdout.write(re.search(r'<script type=\"module\">(.*)</script>',s,re.S).group(1))
") && echo "  ok"

echo "→ CSS structural audit"
python3 - <<'PY'
"""Walk the <style> block tracking brace depth.

Catches the class of bug where a string-replace / paste nests a desktop rule
inside a @media query — which looks like a mysterious specificity problem and
already once left notebook editor styles applying only below 640px, and undid
the connect panel's one-column mobile override with a trailing copy of the
desktop two-column rule.
"""
import re, sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

html = Path('index.html').read_text(encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
js  = re.search(r'<script type="module">(.*?)</script>', html, re.S).group(1)
issues = []

def walk(css):
    """Yield (event, ...) while tracking structure.
    Events: ('open', sel, line, depth, media_depth, is_at)
            ('close', sel, line, depth, media_depth, is_at, body)
            ('end', depth, media_depth)
    """
    depth = media_depth = 0
    media_close_at = []
    stack = []
    i, n, line = 0, len(css), 1
    sel_buf = []
    in_str = None
    in_comment = False

    def flush():
        return ''.join(sel_buf).strip().lstrip('}').strip()

    while i < n:
        c, nxt = css[i], css[i+1] if i+1 < n else ''
        if in_comment:
            if c == '*' and nxt == '/':
                in_comment = False; i += 2; continue
            if c == '\n': line += 1
            i += 1; continue
        if in_str:
            if c == '\\' and i+1 < n: i += 2; continue
            if c == in_str: in_str = None
            if c == '\n': line += 1
            i += 1; continue
        if c == '/' and nxt == '*':
            in_comment = True; i += 2; continue
        if c in '"\'':
            in_str = c; sel_buf.append(c); i += 1; continue
        if c == '{':
            sel = flush()
            is_at = bool(re.match(r'@(media|supports|container)\b', sel))
            depth += 1
            stack.append({
                'sel': sel, 'line': line, 'depth': depth,
                'media': media_depth, 'is_at': is_at, 'body_start': i+1,
            })
            if is_at:
                media_depth += 1
                media_close_at.append(depth)
            sel_buf = []
            i += 1; continue
        if c == '}':
            if stack and stack[-1]['depth'] == depth:
                top = stack.pop()
                body = css[top['body_start']:i]
                yield ('close', top, body)
                if top['is_at'] and media_close_at and media_close_at[-1] == depth:
                    media_close_at.pop()
                    media_depth -= 1
            depth -= 1
            sel_buf = []
            i += 1; continue
        if c == '\n':
            line += 1
        if c == ';' and depth == 0:
            sel_buf = []; i += 1; continue
        sel_buf.append(c)
        i += 1
    yield ('end', depth, media_depth)

# Collect rules + structural issues
rules = []  # (sel_norm, media_ctx, line, body_norm)
media_stack = []
for ev in walk(css):
    if ev[0] == 'end':
        _, depth, media_depth = ev
        if depth != 0:
            issues.append(f'unbalanced braces: final depth={depth}')
        if media_depth != 0:
            issues.append(f'unclosed media/at-rule: media_depth={media_depth}')
        continue
    top, body = ev[1], ev[2]
    if top['is_at']:
        # push/pop handled via media_depth on open... track label from sel
        # On close of at-rule, pop label
        if media_stack and len(media_stack) >= top['media']:
            # closing an at-rule that had media depth top['media'] when opened
            # when at-rule opened, media was top['media']; after open it became top['media']+1
            pass
        continue
    # Regular rule
    if top['media'] > 0 and len(body) > 800:
        issues.append(
            f"L{top['line']}: large rule nested in media ({len(body)} chars) — {top['sel'][:80]}")
    # media context label: reconstruct from nesting by recording at open
    # Simpler second pass for labels:

# Second pass with media labels for duplicate detection inside media only
depth = media_depth = 0
media_close_at = []
media_label = []
stack = []
i, n, line = 0, len(css), 1
sel_buf = []
in_str = None
in_comment = False

def flush():
    return ''.join(sel_buf).strip().lstrip('}').strip()

while i < n:
    c, nxt = css[i], css[i+1] if i+1 < n else ''
    if in_comment:
        if c == '*' and nxt == '/': in_comment = False; i += 2; continue
        if c == '\n': line += 1
        i += 1; continue
    if in_str:
        if c == '\\' and i+1 < n: i += 2; continue
        if c == in_str: in_str = None
        if c == '\n': line += 1
        i += 1; continue
    if c == '/' and nxt == '*': in_comment = True; i += 2; continue
    if c in '"\'': in_str = c; i += 1; continue
    if c == '{':
        sel = flush()
        is_at = bool(re.match(r'@(media|supports|container)\b', sel))
        depth += 1
        ctx = ' > '.join(media_label) if media_label else 'TOP'
        if is_at:
            media_label.append(re.sub(r'\s+', ' ', sel)[:72])
            media_close_at.append(depth)
            stack.append(('at', None, None, depth, None, None))
        else:
            stack.append(('rule', re.sub(r'\s+', ' ', sel), line, depth, ctx, i+1))
        sel_buf = []
        i += 1; continue
    if c == '}':
        if stack and stack[-1][3] == depth:
            kind, sel, ln, d, ctx, body_start = stack.pop()
            if kind == 'rule':
                body = re.sub(r'\s+', ' ', css[body_start:i]).strip()
                rules.append((sel, ctx, ln, body))
                if ctx != 'TOP' and len(css[body_start:i]) > 800:
                    issues.append(f'L{ln}: large rule nested in media ({len(css[body_start:i])} chars) — {sel[:80]}')
            if kind == 'at' and media_close_at and media_close_at[-1] == depth:
                media_close_at.pop()
                media_label.pop()
        depth -= 1
        sel_buf = []
        i += 1; continue
    if c == '\n': line += 1
    if c == ';' and depth == 0: sel_buf = []; i += 1; continue
    sel_buf.append(c)
    i += 1

if depth != 0:
    issues.append(f'unbalanced braces: final depth={depth}')

# Duplicate selectors inside the SAME media context — the replace-twice smell.
# TOP-level duplicates are normal cascade (progressive property sets).
by = defaultdict(list)
for sel, ctx, ln, body in rules:
    if ctx == 'TOP':
        continue
    by[(sel, ctx)].append((ln, body))
for (sel, ctx), hits in by.items():
    if len(hits) > 1:
        issues.append(f'duplicate selector `{sel[:60]}` in {ctx}: lines {[h[0] for h in hits]}')

# ── CSP drift: every outbound origin the app can hit must be in connect-src ──
def origin_of(url):
    u = urlparse(url)
    if not u.scheme or not u.hostname:
        return None
    return f'{u.scheme}://{u.hostname}' + (f':{u.port}' if u.port else '')

origins = set()
for b in re.findall(r"base:\s*'(https?://[^']+)'", js):
    o = origin_of(b)
    if o: origins.add(o)
# Hardcoded adapter fetches (Ollama, Google, Anthropic, …) that skip `base`
for u in re.findall(r"fetch\(\s*[`'](https?://[^`'\"\s]+)", js):
    # Strip template-literal tails like ${...}
    u = re.split(r'\$\{', u, maxsplit=1)[0].rstrip('/')
    # Keep only the origin-bearing prefix
    m = re.match(r'(https?://[^/]+)', u)
    if m:
        o = origin_of(m.group(1))
        if o: origins.add(o)
# Local providers are often reached as either hostname form
for o in list(origins):
    if 'localhost' in o:
        origins.add(o.replace('localhost', '127.0.0.1'))
    if '127.0.0.1' in o:
        origins.add(o.replace('127.0.0.1', 'localhost'))

def policy_connect_origins(text):
    # Prefer the Header / Content-Security-Policy assignment, not comments.
    blobs = re.findall(
        r'(?:Header set Content-Security-Policy|Content-Security-Policy:)\s*"?([^"]+)"?',
        text, re.I)
    if not blobs:
        # publish.sh embeds the policy in an f-string without Header set
        blobs = re.findall(r"Content-Security-Policy:\s*(.+?)(?:\n\"\"\"|\n)", text)
    found = set()
    for blob in blobs:
        # Collapse Apache line continuations
        blob = re.sub(r'\\\s*\n\s*', ' ', blob)
        m = re.search(r'connect-src\s+([^;]+)', blob)
        if m:
            found.update(m.group(1).split())
    return found

for path in ('.htaccess', 'publish.sh'):
    text = Path(path).read_text(encoding='utf-8')
    allowed = policy_connect_origins(text)
    missing = sorted(o for o in origins if o not in allowed)
    if missing:
        issues.append(f'{path} connect-src missing: ' + ', '.join(missing))
    elif not allowed:
        issues.append(f'{path}: could not find connect-src')

if issues:
    print('  FAIL')
    for x in issues:
        print('   ·', x)
    sys.exit(1)
print(f'  ok — {len(rules)} rules, braces balanced, CSP covers {len(origins)} provider origins')
PY
