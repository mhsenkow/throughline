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
# Explicit CSP_CONNECT list (Transformers.js / HF CDN origins)
for block in re.findall(r"const CSP_CONNECT\s*=\s*\[(.*?)\]", js, re.S):
    for u in re.findall(r"'(https?://[^']+)'", block):
        o = origin_of(u)
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

echo "→ library validation"
python3 - <<'PY'
import json, re, sys
from pathlib import Path
from collections import Counter

lib_path = Path('library.json')
if not lib_path.exists():
    print('  FAIL — library.json missing')
    sys.exit(1)

lib = json.loads(lib_path.read_text(encoding='utf-8'))
html = Path('index.html').read_text(encoding='utf-8')
issues = []

# Taxonomies from the runtime
def obj_keys(name):
    m = re.search(rf'const {name}\s*=\s*\{{(.*?)\n\}};', html, re.S)
    if not m: return set()
    return set(re.findall(r'^\s*([A-Za-z0-9_]+)\s*:', m.group(1), re.M))

REALMS = obj_keys('REALMS')
CONCEPTS = obj_keys('CONCEPTS')
PERSONAS = obj_keys('PERSONAS')
OUTPUT_TYPES = {'prose','markdown','list','table','gate','score','diff','ranking','timeline','choice'}

if len(lib) < 1:
    issues.append('library is empty')

ids = [n.get('id') for n in lib]
if len(ids) != len(set(ids)):
    issues.append('duplicate notebook ids: ' + ', '.join(i for i,c in Counter(ids).items() if c>1))

def demo_of(cell):
    if cell.get('demoPass'):
        return cell['demoPass'][0]
    return cell.get('demo')

def shape_ok(cell):
    t = cell['output']['type']
    d = demo_of(cell)
    if d is None: return 'missing demo'
    if t == 'list' and not isinstance(d, list): return 'list demo'
    if t == 'table' and not (isinstance(d, dict) and 'cols' in d and 'rows' in d): return 'table demo'
    if t == 'score' and not (isinstance(d, dict) and 'value' in d and 'max' in d): return 'score demo'
    if t == 'diff' and not (isinstance(d, dict) and 'before' in d and 'after' in d): return 'diff demo'
    if t == 'ranking' and not (isinstance(d, dict) and 'items' in d): return 'ranking demo'
    if t == 'timeline' and not (isinstance(d, dict) and 'events' in d): return 'timeline demo'
    if t == 'choice' and not (isinstance(d, dict) and 'options' in d): return 'choice demo'
    if t == 'gate' and not (isinstance(d, dict) and 'verdict' in d): return 'gate demo'
    if t in ('prose','markdown') and not isinstance(d, str): return 'prose demo'
    return None

for nb in lib:
    for req in ('id','title','blurb','teaches','realm','concept','persona','input','cells','schemaVersion'):
        if req not in nb:
            issues.append(f"{nb.get('id','?')}: missing {req}")
            continue
    if nb.get('realm') not in REALMS:
        issues.append(f"{nb.get('id')}: unknown realm {nb.get('realm')}")
    if nb.get('concept') not in CONCEPTS:
        issues.append(f"{nb.get('id')}: unknown concept {nb.get('concept')}")
    if nb.get('persona') not in PERSONAS:
        issues.append(f"{nb.get('id')}: unknown persona {nb.get('persona')}")

    inp = nb.get('input') or {}
    if not inp.get('id'):
        issues.append(f"{nb.get('id')}: input.id missing")
        continue

    cell_ids = [c.get('id') for c in nb.get('cells') or []]
    if len(cell_ids) != len(set(cell_ids)):
        issues.append(f"{nb['id']}: duplicate cell ids")

    produced = {f"input.{inp['id']}"}
    for i, cell in enumerate(nb.get('cells') or []):
        if not isinstance(cell, dict):
            issues.append(f"{nb['id']}: cell {i} not an object"); continue
        out = cell.get('output') or {}
        if out.get('type') not in OUTPUT_TYPES:
            issues.append(f"{nb['id']}/{cell.get('id')}: bad output type {out.get('type')}")
        if 'demo' not in cell and 'demoPass' not in cell:
            issues.append(f"{nb['id']}/{cell.get('id')}: missing demo")
        err = shape_ok(cell)
        if err:
            issues.append(f"{nb['id']}/{cell.get('id')}: {err}")

        for ref in cell.get('inputs') or []:
            if ref not in produced:
                # gate to= is the only legal backward jump; inputs must be earlier outputs
                issues.append(f"{nb['id']}/{cell.get('id')}: unbound input {ref}")

        prompt = cell.get('prompt') or ''
        gate_writes = {c.get('gate',{}).get('writes') for c in (nb.get('cells') or []) if c.get('gate')}
        for var in re.findall(r'\{\{([\w.]+)\}\}', prompt):
            if var == 'locale.outputLanguage':
                continue
            root = var.split('.', 1)[0]
            if var in produced or var in (cell.get('inputs') or []):
                continue
            if root in produced or root in (cell.get('inputs') or []):
                continue
            if var.startswith('input.') and var in produced:
                continue
            if cell.get('map') and root == cell['map'].get('as'):
                continue
            if root in gate_writes:
                continue
            # Nested paths like name.output.rows are authoring noise from
            # alternate template dialects — require the root bag key only.
            if root in {c.get('output',{}).get('name') for c in (nb.get('cells') or [])}:
                continue
            issues.append(f"{nb['id']}/{cell.get('id')}: prompt var {{{{ {var} }}}} not in inputs/bag")

        if cell.get('gate'):
            to = cell['gate'].get('to')
            if to not in cell_ids[:i]:
                issues.append(f"{nb['id']}/{cell.get('id')}: gate.to {to} must be an earlier cell")

        if cell.get('map'):
            over = cell['map'].get('over')
            if over not in produced:
                issues.append(f"{nb['id']}/{cell.get('id')}: map.over {over} not produced yet")

        produced.add(out.get('name'))
        if cell.get('choice', {}) and cell['choice'].get('writes'):
            produced.add(cell['choice']['writes'])
        if cell.get('gate', {}) and cell['gate'].get('writes'):
            produced.add(cell['gate']['writes'])

# Balance — only enforce once the shelf is at the planned size
if len(lib) >= 100:
    pc = Counter(n.get('persona') for n in lib)
    cc = Counter(n.get('concept') for n in lib)
    rc = Counter(n.get('realm') for n in lib)
    for p in PERSONAS:
        if pc[p] < 6:
            issues.append(f'persona {p} has {pc[p]} notebooks (need ≥6)')
    for c in CONCEPTS:
        if cc[c] < 8:
            issues.append(f'concept {c} has {cc[c]} notebooks (need ≥8)')
    for r in REALMS:
        if rc[r] < 1:
            issues.append(f'realm {r} is empty')

# Seed notebooks must be a subset of the library
seed_ids = re.findall(r'"id":\s*"([^"]+)"', re.search(r'const SEED_NOTEBOOKS = (\[.*?\])\.map\(hydrateNotebook\)', html, re.S).group(1) if re.search(r'const SEED_NOTEBOOKS = (\[.*?\])\.map\(hydrateNotebook\)', html, re.S) else '')
# Simpler: extract from SEED by parsing JSON array after SEED_NOTEBOOKS =
m = re.search(r'const SEED_NOTEBOOKS = (\[.*?\])\.map\(hydrateNotebook\)', html, re.S)
if m:
    try:
        seed = json.loads(m.group(1))
        lib_ids = {n['id'] for n in lib}
        for s in seed:
            if s['id'] not in lib_ids:
                issues.append(f'seed notebook {s["id"]} missing from library.json')
    except Exception as e:
        issues.append(f'could not parse SEED_NOTEBOOKS: {e}')

if issues:
    print('  FAIL')
    for x in issues:
        print('   ·', x)
    sys.exit(1)
print(f'  ok — {len(lib)} notebooks, taxonomies match, demos shaped, bindings resolve')
PY
