# Engineering Brief — Stack & Architecture

**Companion to:** [PRODUCT-BRIEF.md](PRODUCT-BRIEF.md)
**Status:** Draft 1
**Date:** 2026-09-05

---

## 0. Constraints inherited from the product brief

| Ref | Constraint | Engineering consequence |
|---|---|---|
| P1 | Linear notebook, not a canvas | No graph layout engine. A list with a dependency check. |
| P2 | Bring your own model | Multi-provider client, no inference of our own |
| P3 | We hold nothing | No app server in the hot path. Static hosting. |
| P4 | Notebook is a file | Versioned, validated, portable document format |
| P5 | Themeable to invisibility | Token-driven CSS, zero literals, scoped cascade |
| §5.1 | Typed cell outputs | Runtime schema validation, not string passing |
| §5.3 | Per-cell re-execution | Cell-level state machine + staleness graph |
| §6.2 | T1 baseline → T2/T3/T4 later | **Storage as a swappable interface, from day one** |
| §10 | ICU / RTL localization | Logical properties, ICU catalogs, locale as runtime var |

---

## 1. Answering the question as asked: Rust or Electron?

**Neither, and the framing hides the real decision.**

Rust and Electron are not alternatives to each other. Electron is a desktop *shell*
around a web UI. Tauri is a desktop shell around a web UI that happens to be written
in Rust. In both cases **your application is a web app**. The desktop question is
downstream and, per §6.2, deliberately deferred.

So there are two separate questions, and only one of them is urgent:

### 1.1 Should the execution engine be Rust/WASM? — **No.**

The tempting version: one Rust core that runs identically in the browser, in a
desktop app, in a CLI, and on a server. It is a genuinely attractive idea and it is
wrong for this product.

- The engine is **I/O-bound, not compute-bound.** It interpolates templates, makes
  HTTP calls, and advances a state machine. Rust buys zero performance here.
- Streaming is the core interaction, and streaming tokens across the WASM↔JS
  boundary is chatty and awkward.
- Network calls from WASM go back out through JS `fetch` anyway.
- It costs you a second language, a second toolchain, a much worse debugging story,
  and a hiring constraint — permanently, on the most-edited part of the codebase.

**TypeScript is the correct language for this engine.** Write it framework-free so
it already runs anywhere JS runs, which is everywhere you need.

Rust may earn its place later, in exactly two spots: the Tauri shell (which is
mostly generated config, not code you write), and local embedding/vector search if
that ever becomes a feature. Neither is v1.

### 1.2 Which desktop shell, when the time comes? — **Tauri v2.**

| | Tauri v2 | Electron |
|---|---|---|
| Bundle | ~5–10 MB | ~100+ MB |
| Renderer | OS webview (WebKit on macOS, WebView2 on Windows) | Bundled Chromium |
| Consistency | **Varies by platform** — the real cost | Identical everywhere |
| Keychain / FS | First-class plugins | Node APIs |
| Ecosystem | Smaller | Vast |

Tauri wins on the thing that matters for a distributable discovery tool: size. The
honest cost is that macOS WKWebView lags Chromium on web platform features — if you
go this route, **test on macOS from the first week**, not at the end.

But per §6.2 this is a T3 decision. Do not build it first. An installer standing in
front of the product's core insight is the failure mode the product brief calls out
directly (R6). Ship a URL.

---

## 2. Recommended stack

### 2.1 The one-line version

**TypeScript + React 19 + Vite, static-hosted, with a framework-free engine package
and a swappable storage adapter. Tauri later, if ever.**

### 2.2 Core

| Layer | Choice | Why |
|---|---|---|
| Language | **TypeScript**, strict | The notebook format is a type system problem |
| Build | **Vite** | Fast, static output, no server assumptions |
| UI | **React 19** | See §2.3 — this is the one genuinely close call |
| Router | **TanStack Router** or React Router (data mode) | Type-safe, no server needed |
| **Not** | ~~Next.js~~ | Pulls you toward RSC, a server, and a host. Directly hostile to P3. Do not reach for it out of habit. |
| State | **Zustand** | Tiny, no ceremony, no provider tree |
| Schema | **Zod v4** | Notebook files are untrusted input. Also emits JSON Schema for the published spec. |
| Styling | **Tailwind v4** | CSS-first `@theme` compiles to custom properties — aligns exactly with §9's token tiers |
| Primitives | **Radix Primitives** or **Base UI** | Unstyled + accessible. Non-negotiable for "themeable to invisibility." |
| Models | **Vercel AI SDK** (`ai` + provider packages) | Multi-provider streaming, works client-side. Wrap it behind your own interface. |
| Local DB | **`idb`** (Jake Archibald) over IndexedDB | Documents are documents. See §4.2 for when to upgrade. |
| Markdown | `react-markdown` + `remark-gfm` + **`rehype-sanitize`** | The sanitizer is mandatory — see §6.1 |
| Highlight | **Shiki** (web worker) | Accurate, themeable via the same tokens |
| i18n | **Lingui** or FormatJS | Real ICU: plurals, gender, RTL |
| Tests | **Vitest** + **Playwright** | Playwright earns its keep on the theming matrix (§7) |
| Hosting | **Cloudflare Pages** (or any static host) | Static output, no origin, near-zero cost |

### 2.3 The close call: React vs. Svelte 5

Svelte 5 is arguably the better technical fit. Runes are a near-perfect model for
the variable bag and the staleness graph, the compiled output is meaningfully
smaller, and there is no server-framework gravity pulling on you.

**I still recommend React**, for two non-technical reasons that dominate at this
stage:

1. **Ecosystem depth for this app's specific needs** — accessible unstyled
   primitives, virtualization, markdown, editors, i18n. All richer in React.
2. **AI-assisted development fluency.** Svelte 5 runes are recent; models are
   markedly more reliable writing React. For a design-led build leaning on AI
   assistance, this is a real velocity difference, not a preference.

Switch to Svelte if bundle size becomes a measured product problem or the team is
already Svelte-native. It is not a decision you'd regret either way — which is why
it should not consume much time.

---

## 3. Repository shape

```
notebook/
├─ packages/
│  ├─ schema/       # THE SPINE. Zod defs + JSON Schema + version migrations.
│  │                # Zero dependencies. Zero framework. Publishable alone.
│  ├─ engine/       # Run loop, variable bag, staleness graph, model adapters.
│  │                # Pure TypeScript. NO REACT. Runs in browser, worker,
│  │                # Node CLI, or Tauri — unchanged.
│  ├─ storage/      # StorageAdapter interface + backends (§4)
│  ├─ tokens/       # DTCG JSON → Style Dictionary → CSS/Tailwind/Figma
│  └─ ui/           # React components. Consumes engine, never reaches past it.
├─ apps/
│  ├─ web/          # Vite SPA. The product. T1/T2.
│  └─ desktop/      # Tauri v2. Empty until T3 is justified.
├─ notebooks/       # THE LIBRARY. Content as data, reviewed like content.
└─ brands/          # One token file per brand. The three-brand proof (§9.3).
```

**The load-bearing rule: `engine` has no React dependency and no DOM dependency.**
That single constraint is what makes T3, T4, a CLI, and headless testing cheap
later. Violate it once and every tier becomes a rewrite.

`schema` is the most durable artifact in the repo. It outlives every UI decision
here. Version it, publish it, treat breaking changes as breaking changes.

---

## 4. Storage architecture

### 4.1 The interface

Everything goes through one narrow interface. Nothing else in the app knows how
persistence works.

```ts
interface StorageAdapter {
  list(): Promise<NotebookMeta[]>
  read(id: string): Promise<NotebookDoc>
  write(id: string, doc: NotebookDoc): Promise<void>
  remove(id: string): Promise<void>
  capabilities(): { durable: boolean; external: boolean; quota?: number }
}
```

`capabilities()` is not decoration — the UI must be able to tell the user honestly
whether their data is durable (§6.3 of the product brief). That state is visible in
the interface, not buried.

| Backend | Tier | Notes |
|---|---|---|
| `MemoryAdapter` | T0 | Default before any opt-in. Also the test double. |
| `IdbAdapter` | **T1 — baseline** | `idb` + `navigator.storage.persist()`. Blobs to OPFS. |
| `FsaAdapter` | T2 | File System Access API. Chromium-only — feature-detect, never assume. |
| `TauriFsAdapter` | T3 | Real filesystem + OS keychain for keys |
| `HttpAdapter` | T4 | Self-hosted org library |

### 4.2 On "a real local database"

`idb` over IndexedDB *is* a real local database — structured, transactional,
gigabytes of quota. It is enough for documents, runs, and history, and it is the
right starting point.

The upgrade, if querying gets serious (full-text search across every run and
notebook): **`@sqlite.org/sqlite-wasm` with the OPFS VFS** — genuine SQLite,
persisted to the origin private filesystem, running in the browser. It's real and
production-viable. It is also ~1MB of WASM and a worker, so don't take it until a
query you actually need is hard without it.

### 4.3 Export is infrastructure, not a feature

Per R9, browser storage is evictable and your users have no accounts. One-click
export to a real `.json` file must work from day one, everywhere, always. The file
is the durable artifact; the local DB is a cache in front of it. Build export
before you build the library UI.

---

## 5. The execution engine

### 5.1 Cell lifecycle

A discriminated union, hand-rolled, in the `engine` package:

```
idle → queued → running → streaming → done
                    ↓                   ↓
                  error              stale  (an upstream input changed)
```

Resist XState. This machine is small and legible; a library would obscure more than
it manages. Revisit only if branching cell types (P1) ever land.

### 5.2 Staleness

Cells declare `inputs` bound to `${cell.output}` references. That's a DAG — but a
trivially small one on a linear list. Compute the transitive closure on change and
mark downstream cells stale. **Stale is a display state, not an auto-re-run.**
Never silently re-execute something the user paid for.

### 5.3 Streaming

`ReadableStream` end to end. Do not buffer a full response before rendering — the
perceived-speed difference is large and this is a product whose whole job is making
capability feel tangible.

---

## 6. The two engineering problems that will actually bite

### 6.1 CORS — the real threat to "no server"

**This is the constraint most likely to force an architecture change, so decide it
early.** Calling provider APIs directly from a browser is not uniformly allowed:

- Some providers permit direct browser calls via an explicit opt-in header or flag
  (Anthropic requires `anthropic-dangerous-direct-browser-access`; OpenAI's SDK has
  `dangerouslyAllowBrowser`).
- **Some providers do not send permissive CORS headers at all.** For those, a
  browser simply cannot reach them, and no amount of client code fixes it.
- Enterprise gateways (Bedrock / Vertex / Azure) have their own auth flows that are
  frequently not browser-friendly.

#### A key does not fix CORS. Neither does client code.

Worth stating explicitly, because the assumption is natural and expensive:

- A **key is authorization** — proof you may use the API.
- **CORS is origin permission** — the provider's server deciding whether browser JS
  from your origin may *read* the response.

They are orthogonal. A valid key, correctly sent, on a request the server happily
processes, still yields nothing if the response omits `Access-Control-Allow-Origin`.
And it usually fails earlier than that: any request carrying `Authorization` or
`x-api-key` triggers a preflight `OPTIONS`, and if the provider doesn't answer the
preflight, **the real request never fires**. The key was never in play.

No client-side code fixes this either — the browser enforces it *against* your code,
on the provider's behalf. **The only fix is changing where the request originates.**

#### Consequence: the tier ladder is also a provider-coverage ladder

| Tier | Request originates | CORS applies | Provider coverage |
|---|---|---|---|
| T1 (IndexedDB) | Browser JS | **Yes** | CORS-permissive providers only |
| T2 (FSA) | Browser JS | **Yes** — FSA is storage, not network | Same as T1 |
| Relay Worker | Server-side | No | All |
| T3 (Tauri) | Native side, outside the webview | **No** | All |
| T4 (self-hosted) | Org's server | No | All |

This is strategic, not incidental. Two consequences to decide deliberately:

1. **The supported-provider matrix is tier-dependent.** T1 launches with a subset.
   Acceptable — but as stated scope, never as a surprise.
2. **The failure mode lands at the worst moment.** "Connect your model" → "not that
   one, not in a browser" is exactly the wall R6 warns about, hit during onboarding.
   Scope the launch library to T1-reachable providers so nobody meets it.

**Enterprise nuance:** corporate access often runs through a gateway (Bedrock /
Vertex / Azure) behind OAuth/SSO. The *login* is browser-native and fine; the
inference endpoint behind it frequently is not CORS-enabled. Test the endpoint, not
the login.

Options, in order of preference:

1. **Support only CORS-capable providers in T1.** Cleanest, preserves P3 absolutely,
   and narrows the launch surface in a defensible way.
2. **A stateless relay** — a Cloudflare Worker that forwards and logs nothing, zero
   storage, publicly auditable source. Preserves the *spirit* of P3 but weakens the
   sentence you get to say. Only if it unblocks a provider you must have.
3. **T3 desktop**, where CORS doesn't apply at all. Note this is a genuine argument
   for Tauri arriving sooner than §6.2 assumes.
4. **T4 self-hosted**, where the org's own deployment does the forwarding.

Verify each intended provider's browser reachability *before* committing to the
provider list. This is a spike for week one.

On key exposure: a user's own key, in their own browser, calling their own provider
is fine — it is visible in their devtools, and it is theirs. This is only
unacceptable if you ever ship a shared key. Never ship a shared key.

### 6.2 Model output is untrusted input

You render model output as rich content, and model output can be influenced by
whatever the notebook ingested. Two consequences:

- **Sanitize before render.** `rehype-sanitize`, strict allowlist. No raw HTML
  passthrough, ever. This is a live XSS path, not a theoretical one.
- **Cell chaining is an injection surface.** Content flowing from cell 3 into cell
  4's prompt is untrusted data, not instruction. Delimit it clearly in the prompt
  template, and never let a notebook's output alter the notebook's own structure.

---

## 7. Theming implementation

- Token source: **DTCG JSON** → **Style Dictionary v4** → CSS custom properties,
  Tailwind v4 `@theme`, and Figma variables from one pipeline.
- Apply on a **scoped root** (`.nb-root`), never `:root` — the surface must survive
  being embedded in a host page with its own cascade.
- **Enforce zero literals in CI.** A `stylelint` allowed-list rule that rejects any
  hex, raw px font size, or raw duration outside `packages/tokens`. Discipline will
  not hold this line; a failing build will.
- **Playwright visual regression across the matrix:** 3 brands × light/dark × LTR/RTL
  = 12 snapshot sets. This is what turns §9.3's three-brand proof from an aspiration
  into a gate.

---

## 8. Week-one spikes (before committing to any of this)

1. **CORS reality check.** For every provider on the candidate list, can a browser
   actually reach it with a user-supplied key? This answer may reorder everything.
2. **Streaming through the adapter.** One provider, one cell, tokens on screen,
   through the real `ModelAdapter` interface. Proves the seam.
3. **Storage swap.** Same notebook, saved and loaded through `MemoryAdapter` and
   `IdbAdapter` with no call-site changes. Proves §4.1 before it's load-bearing.
4. **Token swap.** Two wildly different brand files, one running surface, zero
   component edits. Proves §7 before there are 60 components to retrofit.
5. **macOS WKWebView check** — *only if* T3 looks likely to arrive early because of
   spike 1.

Each is a day or less. Together they de-risk every irreversible decision in this
document.

---

## 9. What not to build

- **No Next.js, no RSC, no server framework.** Habit will pull you here. Resist.
- **No sync.** (Product brief §6.5.) The file is the sync mechanism.
- **No accounts** until something genuinely requires identity. Optional accounts
  become required accounts.
- **No node-graph canvas.** (P1.)
- **No Rust in v1.** (§1.1.)
- **No bespoke design system.** Unstyled primitives + tokens. Every component you
  style opinionatedly is a component that fights P5.
