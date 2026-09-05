# Product Brief — Notebooks for AI Capability

**Status:** Draft 1 / thinking document
**Date:** 2026-09-05
**Working title:** Notebook (contested — see §11)

---

## 1. The diagnosis

Chat is a blank box. Blank boxes have no affordances. They teach you nothing about
what the system can do, and they make the user responsible for imagining the
capability before they can use it. Most people cannot imagine what they have never
seen, so most people use a frontier model as a slightly better search engine and
conclude that's what it is.

This is not a model problem. It is an **interface legibility** problem. The
capability is present and unadvertised.

Chat is also structurally bad at *repeatable* work. It is a great medium for
exploration and a terrible medium for reliability: the same request produces a
different shape of answer each time, nothing is inspectable, nothing is re-runnable,
and there is no way to hand the thing you just did to someone else.

## 2. The idea, in one sentence

**A library of short, linear, runnable notebooks — each a sequence of small,
single-purpose cells — that make AI capability visible by showing the shape of the
work, run on whatever models the user already has access to, and store nothing.**

## 3. The reframe that matters

The instinct is to describe this as an orchestration tool. Do not. That category is
crowded, commoditized, and engineer-facing (Zapier, n8n, Dify, Flowise, Gumloop,
LangFlow, and a new one every quarter). Runners are not defensible.

**This is a capability-discovery surface that happens to be executable.**

The notebook's primary job is *pedagogical*: the user reads nine labeled cells and
instantly understands a thing AI can do that they did not know it could do. The run
button is the proof, not the product. If you build a great runner with a thin
library, you have built a demo.

Everything downstream follows from accepting this. The library is the product.
The runtime is the viewer.

## 4. Principles (take these as constraints, not preferences)

**P1 — Linear, not a canvas.**
Top to bottom, one column, like a page. The moment you add a node graph you have
made an engineer's tool and lost the audience the diagnosis in §1 identified. There
will be sustained pressure to add branching and a canvas. Resist it through v1.
Branching, if it ever arrives, is a *cell type* ("pick a path"), not a topology.

**P2 — Bring your own model.**
The user connects what they already have. You are provider-neutral by construction.
This is a positioning moat as much as an architecture: you are not reselling
inference, so you are not competing with the labs, and you cannot be disintermediated
by whoever wins.

**P3 — You hold nothing; they hold everything.**
No account required to run. No content on your servers. No run history on your
infrastructure. Keys never transmitted to your origin. This is a *trust* position
that unlocks regulated and enterprise distribution, and it is only credible if it is
absolute — one exception kills it.

Note this is a statement about **your** infrastructure, not about persistence. The
user's own machine can and should hold a great deal. See §6.

**P4 — The notebook is a file, not a record.**
A notebook is a declarative document (JSON/YAML + prose). It ships as a static
asset. A user's copy lives on their machine and exports to their disk as a real
file. This is how you get sharing, versioning, and forking without ever running a
server — the same trick `.ipynb` pulled off. Local storage makes this principle
*more* important, not less: the file is the durable artifact, and any local database
is a cache in front of it (§6.3).

**P5 — Themeable to invisibility.**
The surface must be able to disappear into someone else's brand system entirely.
Not a logo slot — a full token contract. See §8.

## 5. Anatomy

### 5.1 The cell contract — build this first

This is the actual product. Everything else renders it.

Each cell declares:

| Field | Purpose |
|---|---|
| `id` | Stable reference for variable binding |
| `title` | Human-readable, localizable — this is the pedagogy |
| `intent` | One line: what this step does and why it's here |
| `inputs` | Named, typed. Bound to literals, user input, or `${cell.output}` |
| `outputs` | Named, **typed**. Not "text." |
| `requires` | Capability class needed (reasoning / vision / long-context / fast) |
| `prompt` | Templated, localizable, variable-interpolated |
| `render` | How the output is displayed (prose, table, list, image, file, diff) |

**The single most important decision in this product is that outputs are typed.**
If cell output is freeform prose, chaining is a coin flip and the product feels
broken the third time someone uses it. Text is *one* type among several. Chaining
happens by explicit variable reference, never implicitly by "the previous cell."

### 5.2 Variables and state

Runtime state is a flat, inspectable variable bag scoped to the session. The user
can see it. That visibility is itself part of the pedagogy — it's the difference
between magic and comprehension, and comprehension is what §1 says is missing.

State is ephemeral. Closing the tab ends it. Say this plainly in the UI rather than
hiding it; predictability is worth more than the illusion of persistence.

### 5.3 The run model — design for failure, not the happy path

Models are non-deterministic. Cell 4 of 9 will return garbage, and how the product
behaves in that moment *is* the product.

- Cells run individually and hold their result. Re-run one without re-running all.
- Every cell is independently editable and re-executable, in place.
- A downstream cell whose input changed shows as stale, not as wrong.
- No hidden retries. If it failed, show the failure and the reason.

Jupyter and MATLAB already solved this and the solution is the reason the cell
metaphor is worth borrowing. Take the whole model, not just the visual.

### 5.4 The model picker — demote it

As currently conceived, this is the weakest piece. Putting a model dropdown on every
cell asks the user, repeatedly, a question they are not equipped to answer. Most
people do not know the difference between the models they have access to, and being
asked implies they should.

Instead: the cell declares `requires`. The system auto-selects the best available
match from what the user has connected. The picker exists, one level down, for the
people who care. Default first, control second. Progressive disclosure.

## 6. Where the data lives — local-first

*(Terminology: "local-first" here means data on the user's own machine. Not to be
confused with localization/i18n in §10. Worth keeping the words separate in all
future docs — they will collide constantly otherwise.)*

Yes — and this is the right instinct. It resolves the central tension in draft 1
rather than trading it away.

### 6.1 What it buys you

Statelessness was costing real capability: no run history, no saved forks, no
library of the user's own notebooks, no drafts. Moving the database to the user's
machine returns every one of those **without weakening P3 at all** — in fact it
strengthens it, because "we don't store your data" becomes "we have no server that
could." That is a materially different claim to make to a security reviewer.

For the organizational wedge (§7) this is close to decisive. No data processing
agreement. No residency question. No breach surface. No SOC 2 scope for data you
never touch. The enterprise objection to AI tooling is almost always *where does our
content go*, and the answer becomes "nowhere — it never leaves the device."

### 6.2 Local is a spectrum, not a switch

Do not treat this as "web app vs. desktop app." There are five rungs, and the
storage layer should be an **interface with swappable backends** so you can move
between them without touching the product:

| Tier | Where | Gets you | Costs you |
|---|---|---|---|
| **T0** | Session memory | Total predictability | Nothing survives the tab |
| **T1** | **IndexedDB + OPFS** *(recommended baseline)* | A real structured local database — queryable, gigabytes of quota, history, library, forks. Zero install. | Browser can evict it (§6.3) |
| **T2** | File System Access API | Notebooks as **actual files in a folder the user picked** — visible, backup-able, git-able, Dropbox-able | Chromium-only; must be progressive enhancement, not baseline |
| **T3** | Desktop app (Tauri) | SQLite, OS keychain for keys, real filesystem, cross-app integration | An installer stands in front of your value |
| **T4** | Self-hosted container | Shared org library, IT-controlled | Deployment project; enterprise SKU only |

**Recommendation: build T1 as the baseline and ship T2 as progressive enhancement.**

The argument against opening with a desktop app is R6: this is a *discovery*
product. The entire thesis (§3) is that someone reads a notebook and immediately
sees a capability they didn't know existed. Putting a download-and-install in front
of that insight is fatal, and doubly so on managed enterprise fleets where the user
cannot install anything without a ticket. A URL is the distribution mechanism the
thesis requires.

T3 later is cheap *if and only if* the storage layer was abstracted from day one.
If you do build it, Tauri over Electron — ~5MB against ~100MB, and it uses the OS
webview so the same codebase ships both ways.

### 6.3 The trap: silent local data loss

Local + no account has a specific, ugly failure mode. IndexedDB is evictable. The
browser will clear it under storage pressure, Safari's ITP clears it after ~7 days
without interaction, and "clear browsing data" takes it with no warning. The user
has no account, so there is no recovery and no one to appeal to. They will conclude
your product ate their work, and they will be right.

Three mitigations, all required:

1. Call `navigator.storage.persist()` and surface the granted/denied state honestly.
2. **Export is the trust mechanism, not a feature.** Every notebook downloads as a
   real file, one click, always. The file is durable; the local DB is a cache in
   front of it. This is P4, and local-first makes it load-bearing.
3. T2 (a real folder on disk) upgrades the user out of the trap entirely. Offer it
   the moment they have anything worth losing — not at onboarding.

### 6.4 Keys still need care

"Local" does not mean "plaintext in IndexedDB." Default to session-scoped memory,
with an explicit *"remember on this device"* that encrypts via WebCrypto. On T3, use
the OS keychain — which is one of the better arguments for eventually shipping T3 at
all.

### 6.5 Don't build sync. The answer is the file.

Sync is the request that will come, and it is the request that re-introduces a
server and destroys P3. The answer: users sync by putting their notebook folder in
iCloud, Dropbox, or git. It is free, it is under their control, it is more durable
than anything you'd build, and it keeps you out of the data business permanently.

Hold this line. Sync is where local-first products go to become SaaS.

### 6.6 What this adds to the design surface

Be clear-eyed that this is not free. "Nothing is saved" was a *predictability*
feature with zero interface. "Everything is saved locally" is a capability feature
that demands a whole new surface you didn't have: a library, run history, storage
management, quota and eviction states, delete and its confirmations, import/export,
and the empty states for all of it. That is a real chunk of design work — probably
the second-largest in the product after the cell contract. Budget it.

## 7. Who this is for

"People who don't get AI yet" is a diagnosis, not a user. Two candidate wedges,
and they are different products:

- **The curious individual** — choose-your-own-adventure framing, discovery, delight.
  Consumer distribution, hard monetization, no natural buyer for the theming.
- **The enabled-but-idle employee** *(recommended)* — has AI access at work through
  a corporate license, uses it for email drafts, doesn't know what else to do with
  it. There is a real buyer here: the person inside the organization accountable for
  AI adoption, who currently has no artifact to hand out.

Pick the second. It explains the white-labeling — you are not building a destination
site, you are building a surface that organizations theme and distribute internally.
**The theming isn't a vanity feature; it's the distribution model.** That coherence
is worth more than the larger TAM of the consumer wedge.

## 8. Risk register — the honest version

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Empty shelf.** Shell ships, library is thin, engagement dies in week two. This is the default failure mode of every template-gallery product. | **Critical** | Treat authorship as a funded, ongoing editorial workstream, not a launch task. Make notebook authoring a first-class flow in the product. Dogfood: a notebook that writes notebooks. |
| R2 | **Chaining fragility.** Untyped handoffs make runs feel unreliable and users don't come back. | **Critical** | Typed output contract, §5.1. Non-negotiable. |
| R3 | **"Stateless" becomes a tax.** No history, no sharing, no collaboration, no auth. | ~~High~~ **Resolved** | Local-first (§6). Your infrastructure holds nothing; the user's own machine holds plenty. Replaced by R9. |
| R4 | **Key handling.** Any ambiguity about where credentials live collapses the entire trust position from P3. | High | Never touch a key server-side. Document the data path publicly and make it auditable. This should be a marketing asset, not a footnote. |
| R5 | **Runner commoditization.** Someone ships a better runner in a weekend. | Medium | Correct — and irrelevant, if §3 is right. Compete on library and trust, not on execution. |
| R6 | **Onboarding cliff.** Connecting a model before the first run is a wall in front of the value. | Medium | Every notebook must be *readable and comprehensible without running it*. Reading it should already deliver the §1 insight. The run is the upsell. |
| R7 | **Theming scope creep.** "Match every brand system" is unbounded. | Medium | Bound it with an explicit contract (§9) and a pass/fail test. Brands adopt the semantic tier or they don't adopt. |
| R8 | **Name collision.** "Notebook" is owned by Jupyter and adjacent to NotebookLM. | Low | Borrow the mental model, not the noun. |
| R9 | **Silent local data loss.** Browser evicts IndexedDB; user has no account, no recovery, and concludes the product ate their work. | **Critical** | §6.3 — `storage.persist()`, one-click export as the standing trust mechanism, and an upgrade path to a real folder on disk. |

## 9. Thematic system — target architecture

Goal: swap one file, retheme everything, no exceptions.

### 9.1 Three-tier tokens

- **Tier 1 — Primitive.** Raw values: full palette ramps, type scale, spacing ramp,
  radius ramp, duration scale. *Never referenced by a component.*
- **Tier 2 — Semantic.** The brand contract, and the only tier a brand overrides:
  `surface.{base,raised,sunken}`, `ink.{primary,secondary,inverse}`,
  `accent.{base,hover,pressed}`, `border.{subtle,strong,focus}`,
  `status.{running,stale,error,success}`, `radius.*`, `elevation.*`, `motion.*`.
- **Tier 3 — Component.** `cell.header.bg`, `runbar.button.bg`, etc. Almost all pure
  aliases to Tier 2; exists only as the escape hatch for genuine edge cases.

### 9.2 Delivery

- Source of truth in **DTCG-format JSON**, compiled (Style Dictionary or equivalent)
  to: CSS custom properties, Tailwind config, Figma variables, and native platform
  formats if ever needed.
- Runtime application via CSS custom properties on a **scoped root**, not `:root` —
  the surface must survive being embedded inside a host page with its own cascade.
- Light and dark are a required *pair*, not a mode toggle bolted on. Every brand
  ships both.

### 9.3 Acceptance criteria

1. **Zero literals.** No component contains a hex value, a px font size, or a raw
   duration. Enforce in CI with a lint rule, not with discipline.
2. **One-file swap.** Replacing the semantic token file retheme the entire surface
   with no component edits.
3. **Three-brand proof.** Before shipping, prove it against three deliberately
   incompatible brand systems — e.g. a bank (conservative, serif, tight radii), a
   consumer app (saturated, rounded, playful), and a government service (high
   contrast, WCAG AAA, austere). If all three look native, the system works. If any
   one requires a component change, it doesn't.
4. **Contrast holds.** Automated contrast checking runs against every token pair in
   both modes. A brand cannot ship a combination that fails AA.

## 10. Localization — deeper than strings

Standard requirements — ICU message catalogs with plurals and gendered forms,
logical properties throughout (`padding-inline-start`, never `padding-left`) so RTL
is free, locale-aware number/date/currency formatting, no fixed-width text
containers (German runs ~35% long, and a clipped run button is a broken product).

Two requirements specific to this product that are easy to miss:

**L1 — Notebook content is a separate translation pipeline from UI chrome.**
Cell titles, intents, and prose are authored content, not interface strings. They
need their own authoring, review, and translation workflow. Different cadence,
different reviewers, likely different tooling.

**L2 — Locale must flow into the prompt, not just the interface.**
You can translate the entire UI flawlessly and still have the model answer in
English. Locale is a *runtime variable* that every cell's prompt template consumes.
Output language, formatting conventions, and any locale-dependent reasoning are part
of the cell contract. This is the localization bug this class of product always
ships with.

## 11. Open decisions — needed before build

1. **Wedge:** individual or organizational? (§7 recommends organizational.) Nearly
   everything else keys off this.
2. **What exactly does the first library cover?** "Capabilities in public resources"
   is not yet a content strategy. Which ten notebooks, and who authors them?
   **Resolved in MVP:** 100 notebooks filed on persona × realm × concept, authored
   as content-as-data (`library.json`, schemaVersion up to 1.2.0). Open decision
   becomes ongoing editorial ownership, not first coverage.
3. **Does a user author their own notebook in v1**, or only run and fork ours?
4. **Auth posture:** truly zero-account, or optional account for convenience only?
   (P3 argues zero. Optional accounts have a way of becoming required ones.)
4b. **Storage tier:** confirm T1 baseline + T2 progressive (§6.2). The decision that
   actually matters is committing to a swappable storage interface now, so the tier
   stays a deployment choice rather than a rewrite.
5. **The name.** (§8 R8.)
6. **Business model.** Provider-neutral and storage-free means no usage margin and
   no data lock-in — both deliberate. So: licensed distribution to organizations,
   most likely. Worth confirming before the architecture hardens around it.

## 12. Recommended sequence

1. **Write ten notebooks by hand, as documents, before writing any code.**
   No runtime, no design, just prose and cell definitions in a doc. Show them to ten
   people in the target wedge. If a notebook is not compelling as static text, no
   amount of runtime will save it — and if it *is* compelling as static text, you
   have confirmed §3 and de-risked R1 for the cost of a week.
2. **Specify the cell contract** as a versioned JSON schema. This is the product's
   spine and its most durable artifact.
3. **Build the runtime as a thin viewer over that schema.** Deliberately boring.
4. **Build the token system in parallel** and prove it against the three-brand test
   (§9.3) before the surface is considered done.
5. **Then** the localization pipeline, with L2 designed in from the start rather
   than retrofitted.

## 13. Verdict

The diagnosis in §1 is correct and it is the strongest thing here — most products in
this space are solving for capability when the actual bottleneck is legibility. The
architecture instincts (stateless, provider-neutral, linear, embeddable) are right
and mutually reinforcing.

The idea's weakness is that, as stated, it is a runtime in search of a reason.
Runtimes are commodity. The defensible value is in three places: the **curated
library** of things worth doing, the **trust position** of holding nothing, and the
**embeddability** that turns theming into a distribution channel. Build the runner
and skimp on those three and this is a well-made demo.

Build all three and it's a category.
