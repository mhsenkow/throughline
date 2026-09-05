# Throughline — MVP

Runnable notebooks that make AI capability legible. See
[PRODUCT-BRIEF.md](PRODUCT-BRIEF.md) for the thesis and
[ENGINEERING-BRIEF.md](ENGINEERING-BRIEF.md) for the architecture.

`index.html` is the whole web build: one file, no dependencies, no build step,
no server. It is deliberately path-agnostic — every asset reference is
relative and routing is in-memory — so it can be dropped at any subpath.

## Run locally

```bash
python3 -m http.server 8719
```

## Deploy

**Two hosts, and they are not the same machine.** This tripped up the first
deploy, so it is written down.

| | URL | Served by | How |
|---|---|---|---|
| **Production** | https://ibm.io/notebook/ | `portfolio` Cloudflare Worker (OpenNext/Next.js) | `public/notebook/index.html` in `mhsenkow/portfolio`, then `pnpm run deploy` |
| **Staging** | https://mhsenkow.org/notebook/ | GreenGeeks `chi202` (Apache, direct — no Cloudflare) | `./deploy.sh` over SFTP |

`ibm.io` resolves to Cloudflare and is handled entirely by the Worker. The
`public_html/ibm.io` folder still sitting on GreenGeeks is legacy and serves
nothing. Anything uploaded there is invisible.

### Production

```bash
./publish.sh && (cd ~/portfolio/portfolio && pnpm run deploy)
```

`publish.sh` copies the app into the Worker's static assets **and regenerates
the CSP hash**. Do not copy the file by hand — the policy pins script execution
to a hash of this exact build, so an edited app with a stale hash will not run
at all.

Headers live in that repo's `public/_headers` under `/notebook/*`.

## Marks, and why there is no leaderboard

You can mark a notebook **Worked / Mixed / Didn't**, with a note. A mark captures
the whole setup — brand, language, model, and your input — so opening it from
*Your marks* restores the exact configuration, not just the memory of it.

**Marks are stored on this device and nowhere else.** That is a limitation, not
an oversight: there is no server that could hold them (P3), so you cannot see
anyone else's marks and no aggregate rating exists. What replaces it is the
share link — you mark what worked, and you send the URL. Showing off a
combination is peer-to-peer rather than a platform feature.

Per R9 the browser can clear this without warning, so **Connect → Your marks**
exports them to a file and imports them back. Import merges rather than
replaces, newest wins, so pulling marks from a second device does not delete
what is already here.

A shared rating system would need shared state, and that means a server. It is
buildable — a KV or D1 binding on the existing Worker, holding anonymous counts
and never notebook content — but it narrows P3 and should be a deliberate
decision rather than a drift.

## Security posture

**Keys.** Whatever you paste lives in `S.keys` — a plain object in tab memory.
Never written to IndexedDB or localStorage, never sent to the page's own origin,
sent only to the provider endpoint you chose. Closing the tab discards it.
Nothing is embedded in the shipped file; verified there is no credential-shaped
string in the deployed asset.

**Script execution is pinned to a hash.** `script-src` names a SHA-256 of this
build's inline script rather than `'unsafe-inline'`. This matters specifically
because the app renders model output as rich content: if the escaping in
`outputHTML()` were ever wrong, `'unsafe-inline'` would let the injected script
run — and it could hook `fetch` and read a key out of the `Authorization`
header. Verified in both directions: the app runs under the policy, and a
script injected into the DOM does not execute.

**`style-src` keeps `'unsafe-inline'`, deliberately.** The markup uses `style`
attributes, which hashes cannot cover. Style injection can distort the page but
cannot exfiltrate a credential, so the trade is worth naming rather than hiding.

**Cloudflare's analytics beacon is allowed**, for consistency with the rest of
ibm.io. It carries no page content or user input. Remove the two
`cloudflareinsights` entries from `_headers` to keep `/notebook` beacon-free.

**What this does not protect against.** A key pasted into the page is visible
in that browser's own devtools — that is inherent to any bring-your-own-key
browser app, and it is your key on your machine. Do not paste a shared or
production key into any page, this one included.

### Staging

```bash
./deploy.sh
```

Uploads over **SFTP**, not rsync — GreenGeeks disables shell access on this plan
("Shell access is not enabled on your account") but leaves the SFTP subsystem
open, so key auth works and rsync does not. Syntax-checks before uploading,
since a broken publish here is a broken site with no build step to catch it.

`mhsenkow.org` is not proxied through Cloudflare, so changes are immediate.
The `.htaccess` in this repo ships with it and is live: CSP, `no-cache`
revalidation, and gzip (111 KB → 39 KB).

Nothing else is needed — no base href, no rewrite rules, no origin config. Every
asset reference is relative and routing is in-memory, so the same file works at
any path. Static hosts (Cloudflare Pages, Netlify, S3, GitHub Pages) work unchanged.

## What is real in this MVP

| | Status |
|---|---|
| Cell contract — typed outputs, explicit bindings | **Real** |
| Engine — state machine, variable bag, staleness closure | **Real**, DOM-free |
| Per-cell re-execution; stale as display state, never auto-rerun | **Real** |
| Storage adapter interface + IndexedDB backend with honest `capabilities()` | **Real** |
| Export to file (notebooks and marks) | **Real** |
| Marks: local rating that captures and restores the setup | **Real** |
| Shareable permutations encoded in the URL | **Real** |
| Gate cells — the run can loop back, capped and visible | **Real** |
| Three-tier tokens, **13 brands**, light/dark, zero component edits | **Real** |
| Responsive: fluid type, restructured tables, touch targets | **Real** |
| App shell: fixed chrome, inner scroll canvas, cell rail with scroll spy | **Real** |
| i18n incl. RTL via logical properties; locale interpolated into prompts | **Real** |
| Untrusted-output escaping | **Real** (minimal; swap for `rehype-sanitize` in the monorepo) |
| Auto model resolution against each cell's `requires` class | **Real** |
| Per-cell model override; capability-ceiling notice with upgrade | **Real** |
| Reachability test per provider (operationalises spike #1) | **Real** |
| Chrome built-in model (Gemini Nano) — three-state availability + download | **Real**, download path unrun |
| Ollama / Google / Groq / OpenRouter / Anthropic / OpenAI adapters | **Written and streaming**, none verified against a live key |
| Guided demo provider | Scripted — deliberately, it is the R6 fix |
| T2 File System Access backend | Detected, not implemented |
| Tauri desktop build | Not started |

## Model options

Every cell resolves **Auto** against what you have connected, matching the cell's
declared `requires` class. The footer picker shows the resolution rather than posing
the question; pin a cell only if you want to.

| Option | Setup | Serves | Notes |
|---|---|---|---|
| Guided demo | None | everything | Scripted. No network request at all. |
| Chrome built-in (Gemini Nano) | Download once | `fast` | Free forever, offline, no key. Chrome 138+ on supported hardware. |
| Ollama | Run it locally | `fast` | Needs `OLLAMA_ORIGINS` set for this origin. An https page cannot call `http://localhost` — self-host over http, or use desktop. |
| Google AI Studio | Free key | `fast`, `reasoning` | Best free starting point. |
| Groq | Free key | `fast`, `reasoning` | Very fast, open weights. |
| OpenRouter | Free key | `fast`, `reasoning` | Model ids ending `:free` cost nothing. |
| Anthropic / OpenAI | Paid key | `fast`, `reasoning` | |
| Enterprise gateway | — | — | CORS-blocked from any browser. Desktop or self-hosted only. |

Classes describe the **default model** listed, not the vendor. Point Ollama at a
70B and it serves more than `fast`; the field is editable for exactly that reason.

**Two limits worth knowing before you test:**

- **In the published artifact preview, only the demo and the Chrome built-in model
  can work.** The sandbox blocks `fetch` to every host, so Google, Groq, OpenRouter,
  Anthropic and OpenAI will fail there regardless of key. They are for your own
  deployment. The built-in model works because it makes no network request at all.
- **None of the hosted adapters have been verified against a live key.** They are
  written to each vendor's documented streaming format. Press **Test** in Connect —
  it makes one tiny call and reports exactly what came back. That is spike #1 from
  ENGINEERING-BRIEF §8, wired into the product.

Keys live in the tab, in memory. Never written to storage, never sent to this page's
own origin.

## Try these

1. Open any notebook and press **Run all**. Nothing is connected; nothing needs to be.
2. Edit the input afterwards. Every downstream cell goes **stale** — dashed border,
   result preserved, nothing re-runs. That is the §5.3 contract.
3. **Brand** → thirteen systems, including the ten ported from
   `ibm.io/wordcount`. Same component tree, same markup, zero component edits.
   Wordcount's token vocabulary is `bg/face/ink/mute/rule/hair/accent/mark`;
   each maps one-for-one onto the semantic tier here, which is the argument for
   having a semantic tier at all. Try **Brutal** (every border is a black rule),
   **Contrast** (AAA, black and yellow, square), and **Glass** (translucent with
   a real backdrop blur).
3b. Narrow the window past 640px. Tables stop being tables and become labelled
   rows — three columns of prose cannot be narrowed to 360px, and horizontally
   scrolling the primary content is a worse answer than restructuring it.
4. **Language** → العربية. The layout mirrors. Nothing was flipped by hand.
5. Open **Variables in this run**. The bag is inspectable — that visibility is the
   pedagogy, not a debug affordance.
5b. Watch the **rail** on the left while you scroll and while cells run. It is the
   run's state at a glance: what is done, what went stale when you edited the
   input, what failed, and where you currently are. Below 900px it becomes a
   horizontal strip; below 640px the titles drop and the number plus state dot
   carry it. The **status bar** holds progress, storage durability, and the model
   actually answering.
6. **Connect** → Enterprise gateway. Read the refusal. It is a CORS constraint, not
   a credential one, and it is why the desktop build exists.
7. Paste any free key, then **pin** a cell to a model whose class is below what the
   cell declares. The cell says so, in place, and offers the upgrade there — the only
   moment the ceiling is actually felt.

## The desktop build

Not yet started. When it is, per ENGINEERING-BRIEF §1.2 it should be **Tauri v2**,
consuming the same source, and it exists to lift exactly three browser ceilings:

- **Every provider.** Requests originate outside the webview, so CORS does not
  apply. This is the largest single gain and no amount of client work substitutes.
- **Real files on disk.** Notebooks in a folder the user owns — git-able,
  backup-able, immune to browser eviction (R9).
- **Keys in the OS keychain** rather than held in a tab.

The web build already points at it honestly, naming what the browser cannot fix
rather than implying the desktop version is merely nicer.

## Graduating to the monorepo

The single file is marked with the seams it splits along — `tokens`, `notebooks`,
`storage`, `engine`, `ui`. Split it when a second surface (desktop, CLI) needs the
engine, not before. The rule that carries everything: **`engine` never gains a DOM
or framework dependency.**

## Known gaps

- Runs are held in memory only; the IndexedDB adapter is wired and reporting but
  not yet persisting runs. Export works, which is the load-bearing half (§4.3).
- Live-provider structured output is coerced with a regex fallback. In the monorepo
  this becomes Zod-validated with a retry-on-parse-failure.
- Notebook content is untranslated (§10 L1) — visible in the Arabic build, and
  correct: it needs its own authoring pipeline, not the UI string catalogue.

## Live preview

Published (private) at:
https://claude.ai/code/artifact/fbf7bcc3-26ea-494e-b6f4-e3cdfad6f4c2

Same file, unmodified. The only host-specific branch is in `exportNotebook()`:
inside the claude.ai viewer, saves are mediated by the host, so the page asks
for one; served from your own origin, a blob link is the direct path. Both
paths are live in the same source.
