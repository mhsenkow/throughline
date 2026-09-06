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
| Media outputs: image, scene (3D), diagram, chart — same typed contract | **Real** |
| `map` × media — one cell, N pictures / scenes / charts, numbered to inputs | **Real** |
| 3D scenes render and export to `.obj` / `.stl` from the same triangles | **Real**, no library |
| Image inputs: drop, paste or choose a picture; vision cells read it | **Real** |
| Chains — send a finished value into another notebook, with provenance | **Real** |
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
| Vision adapters (Google, Anthropic, OpenAI-compatible, Ollama) | **Written**, not verified against a live key |
| Image adapters (Pollinations, Google, OpenAI, Together, Hugging Face) | **Written**, not verified against a live key |
| Guided demo provider | Scripted — deliberately, it is the R6 fix |
| T2 File System Access backend | Detected, not implemented |
| Tauri desktop build | **Shipped** (macOS DMG; Windows/Linux via CI) |

## The library

**112 notebooks across 13 personas, 9 realms, and 8 concepts.** The home page
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

The shelf is content-as-data in `library.json` (`schemaVersion` up to **1.3.0**).
`1.2.0` adds choice / map / ask behavioural cells and the score / diff /
ranking / timeline / choice output types. `1.3.0` adds the media types —
`image`, `scene`, `diagram`, `chart` — plus `input.accepts: "image"` with a
`seedImage`, the `vision` and `image` capability classes, and `cell.image.aspect`. Every notebook still ships with
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

**Eighteen providers**, grouped by what they cost you rather than by vendor.
In the browser, nothing in the "ready now" column generates images; on desktop,
**Local image engine** does, with weights you downloaded and no key at all:

| Ready now, or nearly | Free, with a key | Paid |
|---|---|---|
| Guided demo · Your browser (Gemini Nano) · Ollama · LM Studio · **Local image engine** (desktop) | Google AI Studio · OpenRouter · Groq · Hugging Face · Cerebras · Mistral · **Pollinations** | DeepSeek · Together · xAI · Anthropic · OpenAI |

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

## Pictures, geometry, diagrams and charts

The cell contract said typed outputs from the start. Four more types finish the
sentence: **image**, **scene**, **diagram**, **chart**. None of them is a new
mechanism — each is a value in the bag with a renderer, exactly like `table`.

**A picture is bytes, never a link.** Every image adapter ends the same way:
fetch the bytes, turn them into a `data:` URL, put that in the bag. No adapter
may return a remote `src`. That one rule is why `img-src` stays `'self' data:`,
why an exported run still has its pictures in it when the provider is gone, and
why nobody's CDN learns who is looking at what. The cost is a fatter export,
paid deliberately. A value that is not `data:image/` is refused at render and
shown as text — a model that returns a URL is a bug, not a picture.

**A 3D result is geometry, not a picture of geometry.** `scene` is a list of
typed primitives — shape, label, position, size, colour, in real units, with
y=0 as the floor. The canvas draws it with an ~80-line painter's-algorithm
rasteriser (no library: `script-src` is pinned to a hash of this one inline
script, so a 3D library could not execute here even if it were bundled). `.obj`
and `.stl` export the **same triangles the canvas drew**, so the view and the
file cannot disagree, and a downstream text cell reads the same objects.

**Charts obey one rule that had to be enforced in the prompt.** All series share
one vertical scale. The shape instruction forbids rescaling a series to make it
fit alongside another — if two measures have different magnitudes, the model
must return one of them or index both to a common base and say so in the unit.
Bars are anchored at zero because a bar's length *is* its value; lines may start
where the data does, and the chart then prints "the vertical axis starts at X,
not zero" underneath. Series colours are a fixed, never-cycled categorical
order (Okabe–Ito, stepped separately for light and dark) checked with a palette
validator for adjacent-pair separation under protanopia, deuteranopia and
tritanopia — not by eye. They live in tokens (`--series-1` … `--series-5`), so
they re-theme with everything else. Do not nudge one without re-running that check.

**Attaching a picture.** A notebook whose `input.accepts` is `image` shows a
drop zone that also takes a paste or a file, and ships a hand-authored
`seedImage` so the first run needs no file at all (R6). Attachments are scaled
to 1280px on the way in and held in the tab:

- **A picture never travels in a share link.** The note goes; the image does not.
  A screenshot is the last thing that should land in a chat by accident, and a
  data URL would make an unusable URL anyway.
- **A mark never stores the bytes.** Marks persist to IndexedDB, and the UI
  promises the picture stays in the tab, so a mark keeps the note and the fact
  that there was a picture.
- **An export does embed it**, because an export is a file you deliberately
  asked for and a run without its pictures is not the run.

**Only a cell that declares `requires: vision` receives the bytes.** Any other
cell reading an image variable gets its description through `bagText()` — so a
reasoning cell downstream of a photograph still runs on a text-only model
instead of dead-ending. `check.sh` enforces both halves: a vision cell must read
the picture input, and a notebook that takes a picture must have a vision cell.

### Mapping over media

A `map` cell runs its prompt once per item in a list. Until the media types
landed it then **joined the results into one string** — which was right for
prose and quietly wrong for everything else: a cell declaring `image` would
end up holding text, and the renderer would print that text under a heading
still claiming a picture. A typed contract lying about itself is the exact
failure the contract exists to prevent, so it is worth naming rather than
quietly fixing.

Now a map over a media type keeps the **values**, one per item, and the cell
holds a list of them: four prompts, four pictures, numbered to the routes that
produced them. Same for scenes and charts — small multiples, each with its own
camera and its own `.obj` export. Text maps keep the joined behaviour, because
joined prose is what a prose map means.

*Four Ways It Could Look* is the notebook that demonstrates it: write four
routes that disagree, draw all four in one cell, then hold each against the
brief.

## Chains — sending a result onward

**Send on** takes any value this run produced and makes it the input of another
notebook. The target says where it came from, and everything it had already
produced goes **stale** — the state the engine already had for "this answers an
older question".

That is deliberately one hop and not a graph. P1 says the unit is a linear
notebook read top to bottom; a saved pipeline that drew itself as a canvas would
be the same mistake one level up, and a scheduler for it would need a server
(P3). What people actually want after a good run is to keep going, and this is
the smallest honest version of that. A picture crosses as a picture when the
next notebook takes one, and as its description when it does not.

## Model options

Every cell resolves **Auto** against what you have connected, matching the cell's
declared `requires` class. The footer picker shows the resolution rather than posing
the question; pin a cell only if you want to.

| Option | Setup | Serves | Notes |
|---|---|---|---|
| Guided demo | None | everything | Scripted. No network request at all. |
| Chrome built-in (Gemini Nano) | Download once | `fast` | Free forever, offline, no key. Chrome 138+ on supported hardware. |
| Ollama | Run it locally | `fast` | Needs `OLLAMA_ORIGINS` set for this origin. An https page cannot call `http://localhost` — self-host over http, or use desktop. |
| Local image engine | Desktop + a running engine | `image` | FLUX/SDXL/SD1.5 on your own machine, offline, no key. Weights download from Connect. Speaks the A1111 API (Forge, SD.Next, Draw Things). Adapter unverified — no engine was running here to test against. |
| Pollinations | Free token | `image` | **Tested, and it failed keyless:** anonymous requests are refused with `403 {"error":"Missing Turnstile token"}` — a bot check, not a rate limit. Shipped as a token provider; the token path is unverified. |
| Google AI Studio | Free key | `fast`, `reasoning`, `vision`, `image` | Best free starting point, and the only free key that both sees and draws. |
| Groq | Free key | `fast`, `reasoning`, `vision` | Very fast, open weights. |
| OpenRouter | Free key | `fast`, `reasoning`, `vision` | Model ids ending `:free` cost nothing. |
| Hugging Face | Free token | `fast`, `reasoning`, `vision`, `image` | FLUX and the open image world behind one token. |
| Together | Paid key | `fast`, `reasoning`, `image` | FLUX.1-schnell has a free tier. |
| Anthropic | Paid key | `fast`, `reasoning`, `vision` | Sees, does not draw. |
| OpenAI | Paid key | `fast`, `reasoning`, `vision`, `image` | |
| Enterprise gateway | — | — | CORS-blocked from any browser. Desktop or self-hosted only. |

`vision` and `image` are **modalities, not tiers**. A provider can be excellent
at reasoning and unable to see a picture at all, so they sit in the same
`requires` list and the same one rule routes every cell: pick the best connected
provider that serves this class. A drawing model is a **separate choice from a
text model at the same provider** — one key, two catalogues — because picking a
drawing model should not quietly change which model writes your prose.

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
  ENGINEERING-BRIEF §8, wired into the product. An image-only provider is tested
  the only way that means anything: by asking it for the smallest real picture.

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
8. **Lay Out a Room** → run it, then drag the result. It is geometry, not a
   picture: orbit it, switch to wireframe, and export `.obj` or `.stl` — the same
   triangles you are looking at. Then open **Variables in this run** and watch the
   scene sit in the bag beside the text, as `scene[8]`.
9. **Read a Screenshot** → drop or paste a picture of your own over the sample.
   Cell 01 declares `requires: vision`, so it is the only one that receives the
   bytes; everything downstream works from its inventory and still runs on a
   text-only model.
10. **Moodboard from a Brief** → two directions, drawn. On the guided demo the
   pictures are hand-authored and say so under each one; connect a provider that
   draws — Google AI Studio is the cheapest route — and the same cells draw for real.
11. Finish any run and press **Send on**. Pick a value, pick another notebook — it
   arrives as that notebook's input, with a line saying where it came from.

## The desktop build

**Ships as Throughline Desktop (Tauri v2)** in
[`desktop/`](desktop/) — free forever, same notebooks as the web, three powers
the browser cannot have:

| Ceiling | Web / phone | Desktop |
|---|---|---|
| Providers | CORS-permissive only | **Every OpenAI-compatible gateway** (Azure, Bedrock proxies, LiteLLM, company relays) via native HTTP |
| Image models | Someone else's API, always | **FLUX on your own machine** — 17 GB of weights downloaded to a folder you own, drawn by a local engine, offline and keyless |
| Storage | IndexedDB (browser may clear) | **`~/Documents/Throughline/`** — git-able JSON on disk |
| Keys | Held in the tab | **OS keychain** |

Download: **https://github.com/mhsenkow/throughline/releases/latest**

**Installers:** macOS `.dmg` (Apple Silicon + Intel), Windows NSIS `.exe`,
Linux `.deb` + `.AppImage`. Built by [`.github/workflows/desktop-release.yml`](.github/workflows/desktop-release.yml)
on tag push. Local Mac builds sign with Developer ID; notarization needs
`APPLE_ID` / app-specific password / `APPLE_TEAM_ID=WC44W2QVE4` — see
[`desktop/README.md`](desktop/README.md).

**Mac App Store (in progress):** sandboxed entitlements, Info.plist export
compliance, MAS config merge, and `desktop/scripts/build-mas.sh` are in the
repo. You still need Apple Distribution + Mac Installer certificates, a Mac App
Store Connect provisioning profile, and an App Store Connect listing — walkthrough
in [`desktop/README.md`](desktop/README.md#mac-app-store) and
[`desktop/macos/APP_STORE_CONNECT.md`](desktop/macos/APP_STORE_CONNECT.md).

**First open on macOS (if not yet notarized):** Gatekeeper may say the app is
“damaged.” It isn’t — quarantine on the download. Fix once:

```bash
xattr -cr /Applications/Throughline.app
open /Applications/Throughline.app
```

### Getting big models

The desktop build downloads image-model weights straight to
`~/Documents/Throughline/models/`. This is the clearest case yet of a ceiling
the browser cannot lift: a tab cannot stream seventeen gigabytes to a folder
you own, resume it after the wifi drops, or leave it somewhere another program
can read. `download_model` in the Rust shell does all three — streamed to disk
through a 1 MB buffer, `Range`-resumed from a `.part` file, cancellable, and
renamed into place only once the byte count matches. A half-finished file keeps
its `.part` name, so it can never be loaded as if it were a model.

Three entries, each a **single complete file**, ungated, checked against the
Hugging Face API for existence, size and licence:

| Model | Size | Licence | For |
|---|---|---|---|
| **FLUX.1 schnell** (`Comfy-Org/flux1-schnell`, fp8) | 17.2 GB | Apache 2.0 | The one people mean by FLUX. Transformer, both text encoders and the VAE in one file. ~12 GB VRAM, or 24 GB unified. |
| **SDXL Turbo** (`stabilityai/sdxl-turbo`, fp16) | 6.9 GB | Stability non-commercial | A third the size, several times faster, weaker at text in pictures. |
| **Stable Diffusion 1.5** (`Comfy-Org/…-archive`, fp16) | 2.1 GB | CreativeML OpenRAIL-M | Runs on 4 GB of VRAM. A download nobody can run is not a feature. |

Split checkpoints are deliberately absent. The low-VRAM GGUF route for FLUX
(6.8 GB) needs a VAE that lives in a gated repo, and a download that ends in
"now find four more files, one of which needs an account" is not the easy link
it was asked to be.

**Throughline does not run these files.** It fetches them and gets out of the
way; the engine that loads them is a separate program you already trust,
reached over localhost. **Local image engine** in Connect speaks the
Automatic1111 HTTP API — which Forge, SD.Next, Draw Things and A1111 itself all
implement — and names the checkpoint in the request, so picking a downloaded
file here actually switches the model over there. Start yours with its API
enabled (`--api` for Forge and A1111).

Embedding an inference runtime instead would mean shipping GPU kernels for
hardware we cannot test, and would make this app the thing that breaks the week
a model format changes. Downloading is a problem with one correct answer;
inference is not.

The desktop bridge also carries **raw image bytes** now: `native_fetch` takes a
`binary` flag and returns a `data:` URL, because the streaming path decodes as
text (right for SSE, fatal for a PNG). Providers that answer with bytes rather
than JSON — Pollinations, Hugging Face — need a rebuilt binary to work on
desktop; they already work in the browser.

Develop / rebuild:

```bash
./scripts/sync-desktop.sh
cd desktop && cargo tauri dev      # iterate
cd desktop && cargo tauri build    # macOS .app + .dmg (signed when cert present)
# Windows / Linux: push a v* tag, or Actions → Desktop release
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

- **The image and vision adapters are unrun, with one exception that was run and
  failed.** They are written to each vendor's documented request shape, and the
  image endpoints differ more between vendors than the chat ones do (`gpt-image-1`
  rejects `response_format`; FLUX wants pixels and a step count; Hugging Face
  returns raw bytes). Press **Test**. Anything that returns a link rather than
  bytes is refused on purpose.
- **Pollinations no longer works without a token, and this was found by testing
  it rather than by reading the docs.** An anonymous request from this build
  returns `403 {"error":"Missing Turnstile token"}`. A bot check is not something
  a key or a retry fixes, and solving one is not something this app will ever do,
  so the provider moved out of the no-setup group and the copy that called it
  "the only keyless way to draw for real" is gone. **In the browser there is now
  no keyless way to generate an image** — the guided demo's pictures are
  hand-authored and say so. On desktop there is: download weights and point at a
  local engine. That test also caught a second bug: `humanError()`
  mapped the 403 to "That key was not accepted", which for a provider that takes
  no key is an answer pointing at nothing. It now names the bot check.
- **Some crossings are not supported, deliberately or not.** `ask` pauses for
  typed text and cannot take a picture from a person mid-run; `choice` options
  are text only; there is no audio, video, PDF or spreadsheet input. A `gate`
  judging a media value reads its description through `bagText()` — that path
  is written but untested.
- **The local image engine adapter is unverified.** It is written to the
  documented Automatic1111 `/sdapi/v1/txt2img` shape, and no engine was running
  on this machine to test against (ports 7860 and 8188 were both silent).
  The downloader underneath it *is* tested — `cargo test -- --ignored` in
  `desktop/src-tauri` runs a real transfer and a real resume against a local
  server and asserts the resumed file is byte-identical.
- **ComfyUI is not supported yet.** It is the most common FLUX runner, but its
  `/prompt` API takes a full workflow graph rather than a prompt, and authoring
  one blind is exactly the kind of thing that ships broken. Forge, SD.Next and
  Draw Things all run FLUX and all speak the A1111 API, so that is the door
  this build knocks on.
- The 3D renderer is a painter's algorithm over convex primitives. Interpenetrating
  or concave shapes can sort wrongly; a depth buffer is the fix if scenes ever get
  more ambitious than a room or a shelf.
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
