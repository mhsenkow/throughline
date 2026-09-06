# Throughline — MVP

Runnable notebooks that make AI capability legible. See
[PRODUCT-BRIEF.md](PRODUCT-BRIEF.md) for the thesis and
[ENGINEERING-BRIEF.md](ENGINEERING-BRIEF.md) for the architecture.

`index.html` plus `library.json` are the whole web build: no dependencies, no
build step, no server. The app is deliberately path-agnostic — every asset
reference is relative and routing is in-memory — so the pair can be dropped at
any subpath. A small seed of notebooks is inlined so first paint does not wait
on the network; `library.json` is fetched relatively and merged in.

## Run locally

```bash
python3 -m http.server 8719
```

Before deploy, `./check.sh` (also run by `deploy.sh` / `publish.sh`) syntax-checks the
inline script, walks the CSS for brace balance and large rules accidentally nested
inside `@media`, verifies every provider `base` origin is listed in `connect-src`,
and validates `library.json` (bindings, demo shapes, taxonomies, shelf balance).
The CSS check catches a whole class of bug that looks like a mysterious
specificity problem; the library check catches the class that made live gate
runs throw.

## Deploy

**Two hosts, and they are not the same machine.** This tripped up the first
deploy, so it is written down.

| | URL | Served by | How |
|---|---|---|---|
| **Production** | https://ibm.io/notebook/ | `portfolio` Cloudflare Worker (OpenNext/Next.js) | `public/notebook/{index.html,library.json}` via `./publish.sh`, then `pnpm run deploy` |
| **Staging** | https://mhsenkow.org/notebook/ | GreenGeeks `chi202` (Apache, direct — no Cloudflare) | `./deploy.sh` over SFTP |

`ibm.io` resolves to Cloudflare and is handled entirely by the Worker. The
`public_html/ibm.io` folder still sitting on GreenGeeks is legacy and serves
nothing. Anything uploaded there is invisible.

### Production

```bash
./publish.sh && (cd ~/portfolio/portfolio && pnpm run deploy)
```

`publish.sh` copies the app **and** `library.json` into the Worker's static
assets **and regenerates the CSP hash**. Do not copy by hand — the policy pins
script execution to a hash of this exact build, so an edited app with a stale
hash will not run at all.

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

### Why a static page cannot count anything

A browser can only *read* a static file over HTTP. `GET` returns bytes; it does
not change them, and no request leaves a trace in the file. Writing needs
something on the other end that accepts a write, and that is a server whatever
it is called.

But ibm.io is **not** a static site — it is a Next.js app on a Cloudflare
Worker, so compute already runs on every request. A shared counter is a KV
binding on infrastructure that exists, not new infrastructure. It still narrows
P3 and should be a deliberate decision rather than a drift.

Free option that already exists: Cloudflare Web Analytics logs URLs, and share
links encode the permutation in the query string. Which combinations get opened
is therefore already recorded — it just cannot be displayed in the app.

### Query vs fragment — the split matters

A share link puts the **permutation** in the query string and the **input** in
the fragment:

```
https://ibm.io/notebook/?n=pre-mortem&b=wcPaper&l=es#i=<base64>
```

A query string is transmitted with every request: it reaches the server, the
access log, the analytics pipeline, and any `Referer` header the page emits.
A fragment is never sent at all — it exists only in the recipient's browser.

So which notebook, brand, language and model someone shared is legible, and is
exactly the aggregate signal worth having. What they typed into it is not.
Anyone holding the link can still read the input, which is the point of
sharing; the page says so when it copies one.

Links using the old `?i=` form still work and are rewritten to the fragment on
arrival, because leaving the input in the query keeps feeding it to history and
to any onward `Referer`.

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
open, so key auth works and rsync does not. Runs `./check.sh` before uploading,
since a broken publish here is a broken site with no build step to catch it.

`mhsenkow.org` is not proxied through Cloudflare, so changes are immediate.
The `.htaccess` in this repo ships with it and is live: CSP, `no-cache`
revalidation, and gzip (111 KB → 39 KB).

Nothing else is needed — no base href, no rewrite rules, no origin config. Every
asset reference is relative and routing is in-memory, so the same pair of files
works at any path. Static hosts (Cloudflare Pages, Netlify, S3, GitHub Pages)
work unchanged as long as both `index.html` and `library.json` are published
together.

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
| Choice / map / ask cells — pick a path, map over a list, mid-run human input | **Real** |
| Typed outputs: prose, markdown, list, table, gate, score, diff, ranking, timeline, choice | **Real** |
| Three-tier tokens, **13 brands**, light/dark, zero component edits | **Real** |
| Faceted browse: persona × realm × concept, search, sort, windowed grid | **Real** |
| Editing a template forks it: skip cells, change output type, rewrite prompts | **Real** |
| Responsive: fluid type, restructured tables, touch targets | **Real** |
| App shell: fixed chrome, inner scroll canvas, cell rail with scroll spy | **Real** |
| Appearance menu: 13 themes × 7 typefaces × 3 densities × mode × language | **Real** |
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

## The library

**103 notebooks across 13 personas, 9 realms, and 8 concepts.** The home page
filters on three axes, because they answer different questions:

- **Persona** — whose job: manager, product, engineer, designer, marketer,
  customer lead, analyst, operator, people partner, founder, scholar, maker,
  householder.
- **Realm** — the world you work in: business, technology, design, writing,
  craft & media, home & body, learning, money & legal, science.
- **Concept** — the move the notebook makes: critique, extract, diagnose,
  generate, compare, plan, translate, teach.

A curated shelf (featured) sits above the grid: gate, choice, ask, map, money,
teaching, and the dogfood authoring notebook (*Write a Notebook*). Sparse hobby
realms were merged into **Craft & Media** and **Home & Body** so facets stay
intentional. Financial work pulled out of a bloated business realm into
**Money & Legal** (runway, contracts, pricing, renewal risk). `check.sh` rejects
prompts that declare an `input.*` and never interpolate it — live runs must see
what the user pasted.

Filing by domain alone would hide half the library from everyone. A gardener
and a CFO both want *find the hole in this plan* — same concept, different
realm. Persona answers the remaining question: *notebooks for someone with my
job*. Facet counts come from the current result set, so a chip never offers a
filter that returns nothing, and a selected chip stays visible even at zero so
there is always a step back rather than only a full reset.

The shelf is content-as-data in `library.json` (`schemaVersion` up to **1.2.0**).
`1.2.0` adds choice / map / ask behavioural cells and the score / diff /
ranking / timeline / choice output types. Every notebook still ships with
hand-written `demo` output so it can be run before you connect anything (R6).
Thin filler would violate the thing the brief cares most about — the library
*is* the product. Editorial tooling lives in `scripts/editorial_pass.py`,
`scripts/deep_pass.py`, and `scripts/deep_pass2.py` as history — prefer hand
edits to `library.json` going forward.

Scaling honestly: the surface window-renders the card grid and handles
hundreds. The constraint remains authorship quality, not UI capacity.

## Editing a template

A template you cannot change is a demo. **Customise** on any notebook lets you:

- **Skip a cell.** Downstream cells that read its output then cannot run, and
  say so — the existing readiness rule does that work, no special case.
- **Change an output type.** Ask for a table instead of prose. Under a live
  model this changes the instruction; under the guided demo the scripted value
  is **re-presented** in the new shape, never regenerated — a demo that invented
  content to fill a table you asked for would be lying about what a model does.
- **Rewrite the prompt.** Changes what a connected model is asked. The demo
  replays its script regardless, which is what makes it a demo, and the editor
  says so rather than letting you wonder.

Edits are stored as a **sparse diff** against the shipped notebook, not a full
copy — so when a shipped notebook improves, your changes still apply to the new
version instead of pinning you to the old one. They persist on this device,
travel in the export, and **Reset to the original** removes them.

This is open decision #3 from the product brief answered: run *and* fork, with
the fork staying local and file-shaped (P4).

## Connecting a model

**Sixteen providers**, grouped by what they cost you rather than by vendor:

| Ready now, or nearly | Free, with a key | Paid |
|---|---|---|
| Guided demo · Your browser (Gemini Nano) · Ollama · LM Studio | Google AI Studio · OpenRouter · Groq · Hugging Face · Cerebras · Mistral | DeepSeek · Together · xAI · Anthropic · OpenAI |

The panel is master-detail: pick one on the left, follow numbered steps on the
right — open the key page, paste, pick a model. **The key is tested
automatically** a moment after you paste it, so nobody has to know a Test
button exists or what a 401 means; errors are rewritten into sentences
("That key was not accepted. Check you copied all of it, with no spaces.").
Model names come from a list rather than a text field you have to already know
the answer to. Below 640px it is one column with the steps above the list.

Two entries worth knowing: **OpenRouter** reaches almost every model through
one key and anything ending `:free` costs nothing; **Hugging Face** opens the
open-model world with a free token. Both speak the OpenAI wire format, which is
the reason this list could grow at all.

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
3. **Appearance** → thirteen colour systems, seven typefaces, three densities,
   mode and language in one menu. Type is a **separate axis** from colour, so
   Braun can be read in a serif or the editorial theme set in a grotesque
   without either brand being edited. Thirteen systems, including the ten ported from
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

**Ships as Throughline Desktop (Tauri v2)** in
[`desktop/`](desktop/) — free forever, same notebooks as the web, three powers
the browser cannot have:

| Ceiling | Web / phone | Desktop |
|---|---|---|
| Providers | CORS-permissive only | **Every OpenAI-compatible gateway** (Azure, Bedrock proxies, LiteLLM, company relays) via native HTTP |
| Storage | IndexedDB (browser may clear) | **`~/Documents/Throughline/`** — git-able JSON on disk |
| Keys | Held in the tab | **OS keychain** |

Download: **https://github.com/mhsenkow/throughline/releases/latest**

**First open on macOS (unsigned build):** Gatekeeper may say the app is
“damaged.” It isn’t — Chrome/Safari marked the download. Fix once:

```bash
xattr -cr /Applications/Throughline.app
open /Applications/Throughline.app
```

(Or: System Settings → Privacy & Security → Open Anyway, after a failed open.)

Develop / rebuild:

```bash
./scripts/sync-desktop.sh
cd desktop && cargo tauri dev      # iterate
cd desktop && cargo tauri build    # ships .app + .dmg under src-tauri/target/release/bundle/
```

The website keeps a download strip and Connect refusal for "Work account" that
points here — the desktop app unlocks that row instead of apologizing.

## Graduating to the monorepo

The single file is marked with the seams it splits along — `tokens`, `notebooks`,
`storage`, `engine`, `ui`. Split it when a second surface (desktop, CLI) needs the
engine, not before. The rule that carries everything: **`engine` never gains a DOM
or framework dependency.**

## Phones (Android / iPhone)

On-device downloads via Transformers.js work in mobile Chrome — including Pixel —
but **Run all with a downloaded model can freeze the tab** because WASM generation
blocks the main thread across every cell (worse with gates and maps).

Mitigations shipping in the viewer:

- **Phone-friendly filter** is on by default on phones: ≤4 cells, no gate, no map
  (~87 notebooks). Toggle **All** to see the full shelf.
- **Run all** on a phone with a downloaded model offers the **guided demo for that
  run** first — explore the shape without a freeze; keep the model for cell-by-cell.
- On-device generation uses shorter completions, yields between cells, skips gate
  re-loops on phone+local model, and caps map iterations.
- Android defaults to **SmolLM2 135M** for responsiveness (larger models stay in Connect).

## Known gaps

- Runs are held in memory only; the IndexedDB adapter is wired and reporting but
  not yet persisting runs. Export works, which is the load-bearing half (§4.3).
- Live-provider structured output is coerced with a regex fallback. In the monorepo
  this becomes Zod-validated with a retry-on-parse-failure.
- Notebook content is untranslated (§10 L1) — visible in the Arabic build, and
  correct: it needs its own authoring pipeline, not the UI string catalogue.
- Phone on-device Run all is still slower than demo or a free cloud key; the demo
  offer is intentional, not a bug.

## Live preview

Published (private) at:
https://claude.ai/code/artifact/fbf7bcc3-26ea-494e-b6f4-e3cdfad6f4c2

Same file, unmodified. The only host-specific branch is in `exportNotebook()`:
inside the claude.ai viewer, saves are mediated by the host, so the page asks
for one; served from your own origin, a blob link is the direct path. Both
paths are live in the same source.
