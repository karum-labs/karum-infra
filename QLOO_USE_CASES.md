# Qloo use cases for Karum

> **What this document is.** A plain-language companion to three Karum planning files: [PRODUCT.md](PRODUCT.md) (what the product is), [PLAN.md](PLAN.md) (how it gets built), and [QLOO_APIS.md](QLOO_APIS.md) (every Qloo call, verified against the 16 Oct 2026 docs snapshot). It lists the use cases where Karum uses Qloo today (as designed) and additional use cases worth adding — each with the exact call, where it plugs in, and what must be verified before it ships. **Snapshot: 16 Oct 2026.**
>
> **Status.** A planning aid, not a contract; [QLOO_APIS.md](QLOO_APIS.md) remains the authority for parameters and doc conflicts.
>
> **Reality check.** The Qloo spike ([PLAN.md](PLAN.md) epic 9) is **complete** — 16 Oct 2026, 123 calls, plus the 17 Oct extension probes (21 calls; 9,856 of the 10,000 monthly quota remaining), and every call below settled against [QLOO_APIS.md](QLOO_APIS.md) §5 and the evidence in [spike/RECORDING.md](spike/RECORDING.md). All calls use the single hackathon host `https://hackathon.api.qloo.com` with an `X-Api-Key` header.

---

## 0. The 60-second background

**Karum** is an agent for retail landlords and leasing brokers. Give it one empty storefront (the "vacancy") and its neighbouring businesses. It reads what the area's people love (via Qloo), ranks candidate tenant brands, produces a shortlist of 5 and a "do not lease" list of 3, then writes the leasing memo and the outreach emails. The decision it supports — which tenant gets a multi-year lease — is expensive and currently made on broker intuition.

**Qloo** is the taste graph. It knows what brands, places, and topics go together across categories, and it can answer that for a specific location. Karum cannot work without it: remove Qloo and the product collapses into a generic LLM answer like "open a café or a plant shop."

**Who calls what.** A Python microservice (`service-taste`) holds the Qloo client. The Flutter client and the Go gateway never call Qloo directly; the API key stays server-side.

**The shape of one Karum run** (this is the sequence the current design follows):

1. Geocode the vacancy address (not Qloo — this comes from the geocoder).
2. Resolve each neighbour name to a canonical Qloo place entity — `GET /search`.
3. Resolve shortlisted brands and constraint chips — `GET /search` and `GET /v2/tags`.
4. Read the block's taste descriptors ("what defines this block") — Insights with `filter.type=urn:tag`.
5. Pull the brands the neighbours' audiences show affinity for, narrowed to the location — Insights with `filter.type=urn:entity:brand` plus `feature.explainability=true`.
6. Check whether candidate categories already exist within walking distance (cannibalisation) — Insights with `filter.type=urn:entity:place`.
7. Sanity-check the audience skew of top candidates — Insights with `filter.type=urn:demographics`.
8. Optionally: heatmap overlay, neighbours-vs-candidate compare chart, card hydration — Insights `urn:heatmap`, `GET /v2/analysis/compare`, `GET /entities`.
9. Score and rank (Qloo fields only), then the LLM writes the memo and outreach, citing evidence IDs.

**Simple glossary.**

- **Entity** — a thing in Qloo's catalogue (a place, a brand, a tag, a locality...). Each has a permanent `entity_id` (a UUID) and a type like `urn:entity:place`.
- **Tag** — a descriptive label such as `urn:tag:genre:place:restaurant` or `urn:tag:keyword:media:cultural_clash`.
- **Signal** — "what to base recommendations on." Karum's primary signal is the set of resolved neighbour entities.
- **Filter** — "what results you want back." E.g. only places, only inside a radius, only this category.
- **Insights** — Qloo's core recommendation endpoint (`GET /v2/insights`); its behaviour is steered by `filter.type` plus signals and filters.
- **Spike** — the short, hands-on testing session (epic 9) that settles every open parameter question before code uses it.
- **Capability flag** — an internal on/off switch so the app hides a feature (e.g. the heatmap) when an endpoint turned out to be unavailable.
- **DI-n** — an ID in [QLOO_APIS.md](QLOO_APIS.md) §9 for a place where Qloo's own docs contradict themselves. Each DI row is resolved by a specific spike item, then closed with a date.

## 1. The rules every use case must follow

This is the short version of [QLOO_APIS.md](QLOO_APIS.md) §1 and §4 — it applies to everything in this document.

1. **One host only**: `https://hackathon.api.qloo.com`. Keys 401 against the production and staging hosts (DI-1).
2. **GET with query-string parameters by default; POST works where documented.** Spike 10 settled 16 Oct that `POST /v2/insights` honours JSON bodies (DI-3 closed) — the `*.entities.query` parameters are usable via POST and stay off GET. Merged-locality arrays and weight arrays remain unverified or rejected (400) and are not used.
3. **Never use** `/recs` or `/recommendations` (explicitly forbidden), the deprecated `/v2/audiences` routes (DI-20), or `urn:entity:audience`. `urn:entity:destination` works but is enum-absent and unused (spike 2); `urn:entity:locality` 400s as a `filter.type` unless signalled by locality entities.
4. **Unsupported parameters are silently ignored** — you get a 200 with unchanged results, not an error. So every parameter must be tested against a no-parameter baseline. A 200 is not proof.
5. **Documented parameters only.** Every parameter in code must map to a row in [QLOO_APIS.md](QLOO_APIS.md) §6 or §7.
6. **Fixtures are redacted, never raw.** Qloo's terms forbid storing raw response data in a public repository, and the Devpost submission requires public repos.
7. **Numbers shown to a judge are traceable.** Anything that is not a Qloo output is labelled as a model inference. Misses are labelled as misses — never guessed.

---

## 2. Current use cases — where Qloo is used in Karum today (as designed)

Summary first, details after.

| # | Use case (user-visible feature) | Qloo call | Where it lives | Status |
|---|---|---|---|---|
| 1 | Neighbour + shortlist resolution ("that ramen place on Bedford") | `GET /search` | PLAN 12, 36 | Core |
| 2 | Constraint chips → tag IDs ("no F&B", "eyewear") | `GET /v2/tags`, `GET /v2/tags/types` | PLAN 13 | Core |
| 3 | Block taste descriptors ("what defines this block") | Insights `filter.type=urn:tag` | PLAN 14 | Core — works; no 403 (DI-2 closed, spike 2) |
| 4 | Candidate brand generation (the core ranking input) | Insights `filter.type=urn:entity:brand` + location + explainability | PLAN 14 | Core — location settled: `signal.location` is the localiser (spike 1, DI-11 closed) |
| 5 | Saturation / cannibalisation check ("a café is already here") | Insights `filter.type=urn:entity:place` + tags + location radius | PLAN 14, 15 | Core — radius settled as genuine metres (spike 5) |
| 6 | Audience-skew sanity check | Insights `filter.type=urn:demographics` | PLAN 14 | Should-build — works; no 403 (DI-2 closed, spike 2) |
| 7 | Scoring inputs (popularity, price band, trends bias, exclusions, probes, weights) | Parameter set on the Insights calls | PLAN 15 | Core — names settled (DI-4/5/6/13 closed) |
| 8 | Evidence drawer ("which neighbour audiences carried this") | `feature.explainability=true` | PLAN 14, 41 | Core — shape settled (spike 4) |
| 9 | Map heatmap overlay | Insights `filter.type=urn:heatmap` | PLAN 16, 39 | Optional, capability-flagged |
| 10 | Neighbours-vs-candidate overlap chart | `GET /v2/analysis/compare` | PLAN 16 | Optional, capability-flagged |
| 11 | Card hydration (images, descriptions) | `GET /entities` (id or external-ID namespaces) | PLAN 40 | Planned — round-trip settled (spike 16) |
| 12 | Operational plumbing (key probe, quota, cache, prewarm, fixtures, health) | `GET /` + response headers + everything cached | PLAN 9, 11, 17, 31 | Core |

### 2.1 Neighbour and shortlist resolution — `GET /search`

- **What it does:** turns messy human input ("the natural-wine bar on Bedford") into one canonical Qloo entity. Everything downstream keys off that entity ID.
- **How users see it:** type-ahead suggestions while adding neighbours, and a confirmation screen when two matches are similarly plausible — the user picks, Karum never guesses silently.
- **The call:** `GET /search?query=<name>&types=urn:entity:place&filter.location=<lat>,<lon>&filter.radius=<miles>&filter.address=<partial>&take=5` — keep the default match sort for name lookups (`sort_by=distance` degenerates into "nearest venues" — trap 7). For a user shortlist: `types=urn:entity:brand`. Documented extras on this endpoint: `filter.tags` (+ `operator.filter.tags`), `filter.popularity`, `filter.rating`, `filter.exists` (e.g. `external.resy`, pattern `^external\.\w+$`).
- **Where it lives:** [PLAN.md](PLAN.md) epics 12 (service-taste) and 36 (client type-ahead); [PRODUCT.md](PRODUCT.md) workflow step 3.
- **Why it matters:** auditability. A recommendation is only as good as the IDs it is built from; the confirmation pause is what makes the evidence chain honest.
- **Watch-outs:** `/search` radius is **miles** (`filter.radius`, default 10) while Insights radius is **metres** (`filter.location.radius`) — same-sounding parameter, different unit. `filter.location` takes the bare `lat,lon` pair only: WKT and Qloo UUIDs are rejected (DI-21). A miss must be an explicit `unresolved` error, not an empty success. `take` is exclusive max 200 here.

### 2.2 Constraint chips → tag IDs — `GET /v2/tags` and `GET /v2/tags/types`

- **What it does:** converts product chips and free text ("no F&B", "fitness", "eyewear", "no national chains") into Qloo tag IDs that the rest of the pipeline can use as filters or signals.
- **The call:** `GET /v2/tags?filter.query=<chip text>&feature.typo_tolerance=true&feature.semantic_search=true&filter.tag.types=<optional namespace>&take=50`. The beta `feature.semantic_search` carries free-text constraints that have no exact match. `GET /v2/tags/types` returns the allow-list of tag namespaces (what Karum is able to explain in the UI).
- **Where it lives:** [PLAN.md](PLAN.md) epic 13; [PRODUCT.md](PRODUCT.md) workflow step 4.
- **Why it matters:** the user's constraints shape both the candidate set (as filters) and the ranking (as signals) — without this step the agent can only take plain addresses and neighbour names.
- **Watch-outs:** the tag response carries **no confidence score** — Karum derives one (typo/semantic hit + name similarity) and labels it as an inference. A constraint with no confident match is returned as "unresolved" for the UI to show, not silently dropped. The `/v2/tags/types` schema is now known (`results.tag_types[]`); it takes `urn:entity:*` parents and `filter.tag.types` works as a namespace restriction — settled in spike 13 (DI-8, DI-9 closed).

### 2.3 Block taste descriptors — Insights with `filter.type=urn:tag`

- **What it does:** answers "what does this block feel like" in readable descriptors (e.g. classic, craft, design-forward). These tags appear in the shortlist cards, the memo, and the evidence drawer.
- **The call:** `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=<neighbour IDs>&filter.tag.types=<optional namespace>`.
- **Where it lives:** [PLAN.md](PLAN.md) epic 14 (first call of `GetBlockProfile`); [PRODUCT.md](PRODUCT.md) call sequence #2.
- **Why it matters:** it gives the agent and the user shared vocabulary, and doubles as the fallback explanation when richer signals are unavailable.
- **Watch-outs:** `urn:tag` is missing from the Insights `filter.type` enum, but the 403 risk is settled: it works — 20 block tags for Colaba (spike 2, DI-2 closed). The derived-descriptor path stays as a degrade guard: derive descriptors from the resolved entities' own payloads and label them as inference; never fail the whole run for this panel.

### 2.4 Candidate brand generation — Insights with `filter.type=urn:entity:brand`

- **What it does:** the heart of the product. Given the neighbours (and a location), returns the brands those neighbours' audiences show affinity for — the pool from which the shortlist is scored. This is what an LLM cannot fake: cross-domain, location-aware, behaviour-based affinity.
- **The call:** `GET /v2/insights?filter.type=urn:entity:brand&signal.interests.entities=<neighbour IDs>&signal.location=POINT(<lon> <lat>)&feature.explainability=true&bias.trends=medium&filter.popularity.min=<optional>&filter.exclude.entities=<neighbour IDs>&take=50`.
- **Where it lives:** [PLAN.md](PLAN.md) epic 14 (the spike-critical call); [PRODUCT.md](PRODUCT.md) call sequence #3.
- **Why it matters:** it produces the non-obvious picks — the eyewear or stationery brand that beats the obvious "another café" — which is the product's core insight and the demo's magic moment.
- **Watch-outs:** the biggest documentation conflict in the whole project — settled 16 Oct (spike 1, DI-11 closed): `signal.location=POINT(<lon> <lat>)` is the **only** working localiser (7 new entities plus a re-rank in the Colaba test); `filter.location`, `filter.location.query` and `filter.location.metro` are silently ignored, and `signal.location.query=<locality>` only shifts rankings subtly. WKT is **longitude-first**; a bare `lat,lon` pair is latitude-first. The neighbour signal plus `signal.location` is the base; a recorded locality via `signal.location.query` is the degrade path, so the location story degrades visibly instead of silently.

### 2.5 Saturation / cannibalisation check — Insights with `filter.type=urn:entity:place`

- **What it does:** "is a coffee shop already within walking distance?" — the check that stops Karum recommending what the block already has. It feeds both the cannibalisation penalty in scoring and the "do not lease: third coffee concept" card.
- **The call:** `GET /v2/insights?filter.type=urn:entity:place&filter.tags=<category tag>&filter.location=POINT(<lon> <lat>)&filter.location.radius=<metres>&sort_by=distance&take=50` — Insights takes WKT only (longitude-first); always send an explicit radius (a WKT point without one returns 0 results). Documented refinements for later: `filter.price_level`, `filter.price_range.from/.to`, `filter.hotel_class`, ratings (`filter.rating`, TripAdvisor, business_rating), `filter.external.exists=resy,michelin,tablet` plus the Resy triple (count/rating/party_size), `filter.hours`, `filter.references_brand`, and `filter.exclude.tags` (+ operator) for the inverse "what to avoid" queries.
- **Where it lives:** [PLAN.md](PLAN.md) epics 14 and 15; [PRODUCT.md](PRODUCT.md) call sequence #4.
- **Why it matters:** it is the product's negative space ("do not lease") and the tie-breaker between two otherwise plausible candidates.
- **Watch-outs:** radius here is **metres** and spike-settled (16 Oct): 400 m genuinely filters (max observed 394 m), `0` behaves like the ~15 km default rather than strict containment, and a WKT point without a radius returns **zero** rows — always send one (spike 5; DI-21). The docs' padding/`0`-strictness claims are false, so kill-rule 1's granularity question is answered: the block story holds at 400 m.

### 2.6 Audience-skew sanity check — Insights with `filter.type=urn:demographics`

- **What it does:** reports the age/gender skew of the top candidates' audiences, so the memo can say "this pick's audience aligns with (or is a stretch for) the catchment."
- **The call:** `GET /v2/insights?filter.type=urn:demographics&signal.interests.entities=<top candidate IDs>` (may combine with `signal.interests.tags`). Positive values mean stronger-than-average alignment with the taste profile.
- **Where it lives:** [PLAN.md](PLAN.md) epic 14 (should-build); [PRODUCT.md](PRODUCT.md) call sequence #5.
- **Why it matters:** it turns demographics into a **result** of taste rather than an input (Qloo's key difference from demographic targeting), and it adds a second human-readable evidence layer next to the tags.
- **Watch-outs:** enum-absent like `urn:tag`, but no 403 in practice — it returned data (DI-2 closed, spike 2). The age buckets are fine-only (DI-7 closed, spike 17). If it fails, the mismatch warning is simply omitted; nothing else breaks.

### 2.7 Scoring inputs — documented Qloo dials that feed the three-part score

- **What it does:** the score has three parts (catchment fit, co-tenancy complement, cannibalisation penalty). These documented parameters shape all three:
  - **Popularity band** — `filter.popularity.min/max` (0–1): the "safe vs emerging" split.
  - **Price / rent proxy** — `filter.price_level.min/max` (1–4); hotel-style variant `filter.price_range.from/.to` (name conflict DI-5).
  - **Trends bias** — `bias.trends` (`off` … `very_high`, default `medium`): how much current momentum weighs.
  - **Quality bias** — `bias.quality` + `sort_by=quality` (place only; accepted set `very_low…very_high` + `mid`, drops no-quality places — DI-6 closed, spike 12).
  - **Exclusions** — `filter.exclude.entities` (keep the vacancy's own neighbours out of the candidate list), `filter.exclude.tags` + operator (spike 11, DI-13).
  - **Per-candidate probes** — `filter.results.entities`: ask "what is the affinity for exactly these candidates?" in one call (spike 9). Same idea for tags: `filter.results.tags`.
  - **Signal weights** — `signal.interests.entities.weight`, `.tags.weight`, etc. (numeric or `very_low`…`very_high`; both accepted, but pair any weighting with a diff test — spike 14, DI-16 closed).
- **Where it lives:** [PLAN.md](PLAN.md) epic 15; [QLOO_APIS.md](QLOO_APIS.md) §3.9.
- **Why it matters:** this is what makes the ranking explainable and tunable without inventing numbers — every input is a documented field, and the formula is written into the evidence payload.
- **Watch-outs:** several of these have multiple spellings across Qloo's docs, and the wrong spelling is silently ignored, not rejected. Spike 11 settles the names before any of them appears in code.

### 2.8 Evidence drawer — `feature.explainability=true`

- **What it does:** every Insights call can return, per result, **which input entities contributed** to the recommendation (normalised 0–1, contributions ≥ 0.1 always included) plus a top-N aggregate. Karum shows this as the "which neighbour audiences carried the affinity" panel — direct from Qloo, not inferred.
- **The call:** the same brand/place calls from 2.4–2.5 with `feature.explainability=true`.
- **Where it lives:** [PLAN.md](PLAN.md) epics 14 and 41; [PRODUCT.md](PRODUCT.md) call sequence #3 and the "How we know" panel.
- **Why it matters:** it is the honesty backbone of the demo and the hardest thing for a judge to dismiss: the recommendation decomposes into named inputs.
- **Watch-outs:** settled 16 Oct (spike 4): accepted on brand and place calls — per result `query.explainability.signal.interests.entities[].{entity_id, score}` plus top-level `effect_on_top3/5/10/all_recs` aggregates; observed scores were all 1.0, so the ≥0.1 inclusion rule is untested. Dead signal entities surface in a top-level `warnings` array (`not_found`), not a `query.explainability.warning` field — 3 of 4 Colaba ids failed it, so treat `warnings` as the honesty check and keep the derived-attribution fallback, labelled as inference.

### 2.9 Map heatmap overlay — Insights with `filter.type=urn:heatmap`

- **What it does:** returns geohash cells with affinity/popularity values; the client renders them as the map overlay showing where taste concentrates around the vacancy. PRODUCT.md calls it "the strongest demo asset."
- **The call:** `GET /v2/insights?filter.type=urn:heatmap&filter.location.query=<locality>&signal.interests.tags=urn:tag:genre:place:restaurant&output.heatmap.boundary=<selector>`. Important correction from the docs: **any** entity or tag works as the signal — the restaurant-genre tag is Karum's deliberate choice for interpretability, not a requirement ([QLOO_APIS.md](QLOO_APIS.md) §3.7).
- **Where it lives:** [PLAN.md](PLAN.md) epics 16 and 39; [PRODUCT.md](PRODUCT.md) call sequence #6. Optional, behind the capability flag.
- **Why it matters:** it makes the "location is where Qloo is hardest to fake" argument visible in one glance.
- **Watch-outs:** settled 16 Oct (spikes 3 + 22, DI-12/DI-18 closed): `urn:heatmap` is the only accepted spelling (`urn:entity:heatmap` → 400); `urn:entity:locality` returns locality polygons instead of cells; `heatmap.dimensions` adds `*_affinity(_rank)` columns and `filter.dimensions.*` adds `*_count_affinity(_rank)` plus undocumented `*_total_count` (cells 230 → 265/232) with no explicit boundary needed. Off by default: the map still works with pins + the competitor radius ring.

### 2.10 Neighbours-vs-candidate overlap chart — `GET /v2/analysis/compare`

- **What it does:** compares the neighbours' audience set against a candidate and shows overlap/difference — the "why does this candidate fit (or not)" chart.
- **The call:** `GET /v2/analysis/compare?a.signal.interests.entities=<neighbour IDs>&b.signal.interests.entities=<candidate ID>&filter.type=urn:entity:brand&model=descriptive&filter.subtype=urn:tag:genre&filter.location.query=<locality>`.
- **Where it lives:** [PLAN.md](PLAN.md) epic 16; [PRODUCT.md](PRODUCT.md) call sequence #7. Optional, capability-flagged.
- **Why it matters:** a second angle of proof for the top pick, and a natural bridge to the brand-side view later.
- **Watch-outs:** both `a.` and `b.` signals are **required** (a one-sided call errors). `take` max 50. `model` and `filter.subtype` settled in spike 19 — parse `results.matchEntities`: the envelope is `{tags, a, b, matchEntities}`, not the `/search` array (DI-22).

### 2.11 Card hydration — `GET /entities`

- **What it does:** the Insights payload is deliberately plain — hydration fills the card gaps (image, description, properties) for already-known IDs, by `entity_ids` or through one of 22 external-ID namespaces (`external.resy.ids`, `external.michelin.ids`, `external.instagram.ids`, …). It also lets cards render Qloo-known data when no Google Places key is configured.
- **Where it lives:** [PLAN.md](PLAN.md) epic 40; [QLOO_APIS.md](QLOO_APIS.md) §3.12.
- **Why it matters:** demo polish and trust — a judge sees recognisable, verifiable cards instead of bare names.
- **Watch-outs:** settled 16 Oct (spike 16): `/entities?entity_ids=` round-trips a full record (Leopold: 173 tags, full properties) and `external.resy.ids` returned the same entity `/search` found — card enrichment without a Places key is viable. Misses return a 404-style body, not an empty success — handle the miss explicitly.

### 2.12 Operational plumbing (invisible but load-bearing)

- **Key-liveness probe** — the hackathon key is in hand (16 Oct 2026) and its monthly quota is recorded as 10,000 requests; `GET /` against the hackathon host confirms it stays live ([PLAN.md](PLAN.md) epic 9, first checklist item).
- **Quota and 429 handling** — rate-limit headers and the rolling ~30-day reset window are recorded (spike 7; 429 deliberately unprobed — zero 429s across 144 calls). Estimated remaining internal use (city choice, prewarm, and the 20-block eval) fits comfortably inside the 9,856 left — keep the ledger and check it before the eval run and the judging window.
- **Caching** — private server-side caching is allowed with no time limit. Karum caches by canonical parameter hash for 24h with a single-flight lock, plus an in-process fallback if Redis is down (epic 17).
- **Prewarm** — the two sample blocks are loaded on deploy and refreshed inside the cache TTL so a judge's first click is fast (epic 47).
- **Fixtures** — the spike's redacted responses become the first fixture files; replay tests assert the typed client structures with no live network (epics 7, 11, 50).
- **Health reporting** — `GET /health` reports Qloo mode (`live`, `fixture`, `degraded`) so the UI can show a banner when the run is not on live data (epic 31).
- **The evaluation harness** — the leave-one-out harness (epic 33) drives the full Qloo chain on ~20 blocks; the LLM-only baseline is the Qloo-free control it is measured against.

### 2.13 Deliberately not used (keep it that way)

These are decisions, not oversights — each is recorded in [QLOO_APIS.md](QLOO_APIS.md) §4:

- `/recs` and `/recommendations` — explicitly forbidden for the hackathon.
- `/v2/audiences` and `/v2/audiences/types` — OpenAPI `deprecated: true`; demographic output comes from Insights instead (DI-20).
- POST bodies for `*.entities.query` work (spike 10, DI-3 closed) but stay off GET; merged-locality arrays and weight arrays are unverified/rejected (400) — not used.
- `urn:entity:audience` (deprecated) and search-only legacy types (`actor`, `album`, `author`, `director`) outside `/search`.
- `urn:entity:locality` as an Insights `filter.type` — 400s unless signalled by locality entities. (`urn:entity:destination` works but is enum-absent and unused — spike 2, DI-2 closed.)
- `GET /v2/trending` — deliberately out of the MVP (it returns below, as suggestion A1).
- `signal.location.radius` where density discovery matters — Qloo advises against overriding it.
- Any parameter without a §6/§7 catalogue row.

---

## 3. Suggested additional use cases

Three groups: **A** = cheap additions to the pipeline that already exists (same endpoints, small build), **B** = product extensions for the v1/v2 roadmap (same API, new screens and buyers), **C** = ideas that need spike verification before they can be planned. Each entry says what it does, the call, where it plugs in, and the gates.

### Group A — Quick additions that reuse the existing pipeline

#### A1. Momentum badge + "why now" line — `/v2/trending`

- **What it does:** for each shortlisted brand, fetch weekly momentum (population rank velocity, fold change) and show an "emerging vs established" badge on the card, plus an urgency sentence in the outreach email ("this brand's audience is climbing — the terms will not stay this cheap").
- **The call:** `GET /v2/trending?filter.type=urn:entity:brand&signal.interests.entities=<brand ID>&filter.start_date=<YYYY-MM-DD>&filter.end_date=<YYYY-MM-DD>` — both dates are required; rows are weekly, newest first.
- **Where it plugs in:** [PLAN.md](PLAN.md) epic 16's deliberately-out nice-to-have; card UI in epic 40; outreach draft text in epic 23. This is the strongest story-per-call of any addition.
- **Why it's worth it:** adds a time dimension to a product judges will otherwise see as a snapshot — "sign now" is a broker's real instinct, and Qloo is the only source in the stack that can back it.
- **Gates:** spike 20 settled 16 Oct — weekly rows, `population_rank` is a string, windows under ~6 months return an empty list, sparse entities return 0 rows. Only build it after the must-build list is green — it is on the cut line, not above it.

#### A2. "Probe any brand" — `filter.results.entities`

- **What it does:** the judge names a brand they would have picked ("why not Blue Bottle?"). Karum fires one on-demand affinity probe under the block's signal and shows the candidate's score next to the shortlist, live in the trace.
- **The call:** the existing brand insights call with `filter.results.entities=<judge's brand ID>` (resolve the name via `/search` first).
- **Where it plugs in:** the shortlist board (epic 40) and evidence drawer (epic 41); reuses the probe machinery already in scoring (epic 15, spike 9).
- **Why it's worth it:** it makes the agent feel genuinely interactive and answers the single most common judge reflex — "did you check the obvious one?" — with Qloo evidence instead of assertion.
- **Gates:** none beyond spike 9 (settled 16 Oct — `filter.results.entities` works; `filter.results.tags` is a no-op). Resolve-then-probe needs a confident `/search` hit, and a miss must be labelled a miss.

#### A3. Safe ↔ bold mode — `bias.trends` + popularity bands

- **What it does:** one toggle on the shortlist screen. "Safe" = high-popularity, low-trends-bias anchors; "bold" = low-popularity, high-trends-bias breakout picks. Same block, two visibly different shortlists.
- **The call:** the same brand insights call with different dial values: `bias.trends=off|low` + high `filter.popularity.min` for safe; `bias.trends=high|very_high` + low popularity band for bold.
- **Where it plugs in:** scoring/tuning layer (epic 15) and the board (epic 40). No new endpoint, no new infrastructure.
- **Why it's worth it:** it demonstrates deep, deliberate use of the API's weighting surface (Technological Implementation), and it matches how brokers actually present options to owners: the safe rent and the upside bet.
- **Gates:** values are documented (`off`…`very_high`, default `medium`); the demo must state that the two lists share the same evidence pipeline.

#### A4. Constraint-as-signal weighting — `signal.interests.tags` (+ `.weight`)

- **What it does:** today, constraint chips map to filters (restrict results). This adds the second use: stated preferences ("premium", "design-led", "eyewear-adjacent") also go in as a **positive signal**, so they bias candidate generation, not just the output filter.
- **The call:** add `signal.interests.tags=<tag IDs>` (and optional `.weight`) to the brand insights call; `operator.signal.interests.tags=union` to score by highest-affinity tags.
- **Where it plugs in:** tag resolution (epic 13) feeds scoring's call assembly (epic 15).
- **Why it's worth it:** it is the difference between "filter out what you don't want" and "tell me more like what you do" — a genuinely better answer from the same endpoint.
- **Gates:** documented on all entity types; both numeric and string weight forms accepted, but neither showed an observable effect in the spike's single-signal test — pair any weighting with a diff test (spike 14, DI-16 closed).

#### A5. Quality-credibility badges — `filter.external.exists` + Resy/rating fields

- **What it does:** annotates candidates and neighbours with real-world markers: "already on Resy", "Michelin-listed nearby", plus Resy rating/count and TripAdvisor scores as backup quality proxies.
- **The call:** `filter.external.exists=resy,michelin,tablet` (and the Resy triple / ratings filters from [QLOO_APIS.md](QLOO_APIS.md) §3.5) on the place-side calls; surface what comes back on cards and in the memo.
- **Where it plugs in:** saturation/enrichment calls (epic 14) and cards (epic 40).
- **Why it's worth it:** for a landlord audience it is the "these are real venues, not hallucinated names" proof — important in a domain with six-figure decisions.
- **Gates:** Resy spelling settled — `filter.external.resy.*` is the working one; Colaba carries no Resy data (0 rows), but `/entities` resy externals do return rating/cuisine fields (spikes 11 + 16, DI-4 closed).

#### A6. Price centre-of-gravity read — `filter.price_level`

- **What it does:** aggregates the `price_level` (1–4) of places inside the saturation radius and reports where the block's pricing actually sits. It feeds two things: the memo's rent-tier guidance, and the default answer to the "mid or premium?" clarifying question.
- **The call:** the existing place-side saturation call, plus reading `price_level` from the returned properties.
- **Where it plugs in:** block profile (epic 14), scoring (epic 15), memo (epic 23), clarifying defaults (epic 28).
- **Why it's worth it:** grounds "premium tier" in data instead of the user's self-assessment, with zero extra calls.
- **Gates:** spike 8 settled density (`price_level`/`price_range`/`business_rating`/`hours`/`images` present); demo-city rows get spot-checked at build time — extend that to confirm `price_level` reads back on results.

#### A7. Geohash block definition — `filter.location.geohash`

- **What it does:** an alternative way to define "this block": a geohash-prefix cell instead of a radius circle. If spike 5 shows the radius granularity is too coarse (kill-rule 1 risk), the saturation check switches from "within 400 m" to "inside the same geohash cell(s)", which is still a real, documented location surface.
- **The call:** `filter.location.geohash=<prefix>` on place-side Insights (documented, pygeohash precision 12).
- **Where it plugs in:** the saturation call (epic 14) as the fallback recorded in epic 10's city-choice decisions.
- **Why it's worth it:** it protects the "block-level, not city-level" story — the exact thing the product's differentiation depends on — with a documented parameter instead of a hand-wave.
- **Gates:** spike 5 settled radius granularity (genuine metres — 400 m filters at max 394 m), so the geohash fallback is not needed; prefix behaviour was never probed — verify it first if this idea is ever adopted.

#### A8. Demographic memo section — reuse the existing `urn:demographics` output

- **What it does:** renders the audience-skew data already fetched for the sanity check as a short "who this pick serves" section in the memo and brand outreach (aggregates only, never personal data).
- **The call:** no new call — the epic-14 demographics response, reformatted.
- **Where it plugs in:** memo/outreach drafting (epic 23) and the evidence drawer (epic 41).
- **Why it's worth it:** a second, human-readable layer of evidence for free; it also quietly demonstrates Qloo's "demographics as output of taste, not input" philosophy.
- **Gates:** none — demographics works (spike 2, DI-2 closed); if a call ever fails, the section is omitted.

#### A9. External-ID card links — `/entities` namespaces

- **What it does:** extends hydration beyond images: add tappable real-world links (Instagram, Twitter, Resy, Michelin) to candidate and neighbour cards, resolved through the external-ID namespaces.
- **The call:** `GET /entities?external.instagram.ids=…` etc. (22 documented namespaces).
- **Where it plugs in:** `GET /entities` hydration (epic 40, spike 16).
- **Why it's worth it:** lets a judge verify the shortlist in one click against the real world — the strongest possible answer to "is this real?"
- **Gates:** only the namespaces that resolve for the demo cities; a miss is shown as a miss.

### Group B — Product extensions for v1/v2 (same API, new buyer surfaces)

These are not hackathon-week features. They are the roadmap [PRODUCT.md](PRODUCT.md) already sketches (broker workspace, brand-side matching, BID/council licences) — each one is enabled by API surface Karum already uses.

#### B1. Brand-side workspace — "where is my audience already?"

- **What it does:** deepen the flag-off brand-side view (PLAN epic 48) into a real surface: rank saved vacancies for a brand with the same rubric, show a city heatmap whose signal is the **brand's own entity** (or its genre tag), and show the brand's existing footprint via `filter.references_brand` ("you already run three stores within 2 km").
- **The calls:** Insights `urn:entity:brand` with `signal.interests.entities=<vacancy block entities>` (existing), Insights `urn:heatmap` with `signal.interests.entities=<brand ID>` (new, allowed — any entity works as the signal), and place-side `filter.references_brand=<brand ID>` (footprint).
- **Why it's worth it:** it is the product's stated two-sided marketplace: the same data answers the landlord's question and the brand's question.
- **Gates:** keep the framing as **inverse matching** ("which of my vacancies fit you"), not "where should you open" — that is GeoTaste's lane, and copying it loses the novelty argument.

#### B2. District / BID compare reports — `GET /v2/analysis/compare`

- **What it does:** compares two high streets or districts — each proxied by its venue set — and shows how their audiences overlap or differ, plus their tag profiles. A sellable artifact for business improvement districts and councils (PRODUCT.md's named secondary buyer).
- **The call:** `CompareSets` with `a.`/`b.` signals = each district's resolved venues; pair with `urn:tag` descriptor calls for the written summary.
- **Why it's worth it:** the same engine, a second paying audience, and a report nobody else in the field is producing.
- **Gates:** merged-locality arrays remain unverified (spike 10 settled POST bodies, not arrays — DI-3 closed) — districts must be represented by their venues, not by locality arrays.

#### B3. Portfolio cannibalisation guard

- **What it does:** for a broker with several saved vacancies, checks each new recommendation's category against the **other** units' radii, so one broker does not fill three blocks with the same concept.
- **The call:** the existing place + tags + location query per saved vacancy (epic 29 rows), plus `filter.exclude.location` semantics where helpful.
- **Why it's worth it:** it turns saved vacancies (epic 43) from a convenience into a defensible multi-site product — exactly the "workflow lock-in" PRODUCT.md names as the moat.
- **Gates:** cost control — it multiplies saturation calls by the number of saved vacancies; cache aggressively.

#### B4. Watch mode with momentum alerts — diff (epic 30) + trending

- **What it does:** the monthly re-run diff already planned ("affinity for X rose since last month") gains a momentum trigger: alert when a shortlisted brand's trending velocity spikes or the recommended pick changes.
- **The calls:** epic 30's re-run + `/v2/trending` (A1's call, reused on a schedule).
- **Why it's worth it:** this is the recurring-revenue story — PRODUCT.md prices it at $199–499/month for brokers. "Sign before the ask rises" is a broker's language.
- **Gates:** keep scheduled re-run **off** in the public demo (epic 30's rule) — alerts are a product feature, not a demo feature.

#### B5. Pop-up / food-hall mode

- **What it does:** a packaged variant of the same pipeline tuned for short-term lets: shorter radius, trends-biased ranking, and a bias toward concepts that are already proven nearby (lower risk for a 3-month lease). Covers PRODUCT.md's merged pop-up and food-hall ideas.
- **The call:** no new endpoint — parameter profiles of the existing calls.
- **Why it's worth it:** a second productized entry point with near-zero new engineering; pop-up operators are an easier first customer than full-time tenants.
- **Gates:** none beyond the existing spike items; keep it out of the hackathon build.

#### B6. MCP depth — `taste_of_block` and `probe_brand`

- **What it does:** beyond the single shortlist tool (epic 49), expose two agent-facing tools: `taste_of_block(address, neighbours)` and `probe_brand(brand, block)`. Same gateway calls, documented behind flags.
- **Why it's worth it:** makes Karum's Qloo layer callable by other agents — a plausible agent-economy distribution channel later.
- **Gates:** quota policy and a demo token (epic 49 already plans both); flag off until the core demo is green. Bare Qloo MCP wrappers are crowded in 2026 — the value here is the *scored, evidenced* output, not the raw API.

### Group C — Spike-gated ideas (verify before planning)

These use documented parameters, but only in the "deep-dive" spec or with open conflicts. The epic-9 session (16 Oct) settled the affordable ones — the answers are inline below; anything still untested needs a small follow-up probe before adoption.

- **C1. `model=predictive` on compare** — a forward-looking overlap chart next to the descriptive one (spike 19 settled: both models accepted with identical shape; the chart must parse `matchEntities` — DI-22).
- **C2. `bias.content_based` (0–1) + backfill dials** — a "novel vs expected" dial and suppression of low-confidence filler; both are deep-dive-only — spike 18 settled the backfill dials as silently ignored on this surface.
- **C3. POST-only surface** — spike 10 settled 16 Oct: POST works (DI-3 closed), so `signal.interests.entities.query` and `filter.exclude.entities.query` are usable via JSON bodies; weight-array shapes were rejected in spike 14 probes (400), so merged-locality arrays stay unverified.
- **C4. Trending beyond brands** — `/v2/trending` with tags or localities (e.g. "is this district's scene rising?") — enum coverage is unspecified in the snapshot; spike 20 settled brand trending only (weekly, ≥ ~6-month windows, empty under that).
- **C5. `diversify.by=properties.geocode.city|metro`** — spread a broker's results across markets. Spike 15 settled `diversify.by=subtype` on tag calls only (DI-10 closed); the city/metro form remains untested — treat as speculative.
- **C6. `filter.exists=properties.image|description`** — a renderability guard so every card has visuals (deep-dive parameter; cheap to test).
- **C7. Demographics as input** — `signal.demographics.age` / `.gender` (± weights) to steer candidate generation toward the catchment's skew. Deep-dive weights; audience IDs have no live source while `/v2/audiences` is deprecated (DI-7, DI-20).

### Group D — Rules for adding anything new

Unchanged from the current discipline; restated so new ideas do not drift:

1. Every new parameter must map to a [QLOO_APIS.md](QLOO_APIS.md) §6/§7 row before it reaches client code.
2. A new doc-vs-doc conflict gets a new DI row; when the spike settles it, the row is closed with the observed answer and a date.
3. New endpoints/parameters go through the epic-9 session (or a small follow-up probe) before any UI depends on them.
4. Anything risky ships behind a capability flag, and the UI hides it cleanly when unavailable.
5. Nothing jumps the cut order: MCP (49) → brand-side (48) → saved vacancies (43) → compare (16) → routes (32) → diff/watch (30). The must-builds and the three-minute judge path come first, always.
6. Fixtures stay redacted; raw Qloo JSON never enters a public repo.
7. Derived numbers (confidence scores, fallback descriptors) are labelled as inferences everywhere they appear.

---

## 4. Summary table — suggested additions at a glance

| # | Idea | Qloo call | Effort | Judge-visible | Gate |
|---|---|---|---|---|---|
| A1 | Momentum badge + "why now" line | `/v2/trending` | S | Yes, high | Spike 20 settled — after must-builds |
| A2 | Probe any brand on demand | `filter.results.entities` | S | Yes, high | Spike 9 settled |
| A3 | Safe ↔ bold toggle | `bias.trends` + popularity bands | S | Yes, high | Documented; demo wording |
| A4 | Constraints as positive signal | `signal.interests.tags` (+weight) | S | Indirect | Spike 14 closed — weights inert on the test call; diff-test any use |
| A5 | Quality-credibility badges | `filter.external.exists`, Resy/rating fields | S–M | Yes, medium | DI-4 closed (spike 11); field read-back |
| A6 | Price centre-of-gravity for rent guidance | `filter.price_level` read-back | S | Indirect (memo) | Spike 8 settled — extend to field read-back |
| A7 | Geohash block definition (fallback) | `filter.location.geohash` | S | Protects demo | Spike 5 settled — fallback unneeded |
| A8 | Demographic memo section | reuse `urn:demographics` | S | Yes, medium | DI-2 closed (spike 2) |
| A9 | External-ID card links | `/entities` namespaces | S | Yes, medium | Spike 16 settled |
| B1 | Brand-side workspace (deepened) | heatmap w/ brand signal; `filter.references_brand` | M | Post-hackathon | Epic 48; framing rule |
| B2 | District / BID compare reports | `CompareSets` on venue sets | M | Post-hackathon | DI-3 closed — no locality arrays; use venue sets |
| B3 | Portfolio cannibalisation guard | place + tags per saved vacancy | M | Post-hackathon | Epic 29/43; caching |
| B4 | Watch mode + momentum alerts | diff + `/v2/trending` | M | Post-hackathon | Epics 30/43 |
| B5 | Pop-up / food-hall mode | parameter profiles only | S–M | Post-hackathon | None new |
| B6 | MCP depth (`taste_of_block`, `probe_brand`) | gateway calls via MCP | M | Post-hackathon | Epic 49; quota policy |
| C1 | Predictive compare | `model=predictive` | ? | Maybe | Spike 19 settled — same shape as descriptive |
| C2 | Novel-vs-expected dial + filler caps | `bias.content_based`, backfill dials | ? | Maybe | Spike 18 settled — backfill dials are no-ops |
| C3 | Merged localities / weight arrays | POST surface | ? | No | DI-3 closed — POST works; arrays unverified/rejected |
| C4 | Trending for tags/localities | `/v2/trending` | ? | Maybe | Spike 20 settled for brands; tags/localities untested |
| C5 | City/metro diversification | `diversify.by` | ? | No | DI-10 closed — subtype is tag-scope only; city/metro untested |
| C6 | Renderability guard | `filter.exists=properties.image` | ? | Indirect | Untested deep-dive param — cheap probe first |
| C7 | Demographics as input weights | `signal.demographics.*.weight` | ? | Maybe | DI-7 closed; DI-20 — audiences route deprecated, deep-dive weights untested |

Effort: S = a day or less on top of an existing epic; M = a small feature slice; "?" = effort sized only after a follow-up probe. "Judge-visible" means it shows up in the three-minute demo script.

## 5. Practical adoption order (if you only do a few)

1. **A2 — Probe any brand.** Smallest build, biggest interaction upgrade; directly answers the judge's most common challenge. Do it once the shortlist board exists.
2. **A3 — Safe ↔ bold toggle.** A parameter change plus one UI control; two distinct outputs from one demo block, and it showcases API depth honestly.
3. **A1 — Momentum badge.** Best story per call; add only after the must-build list is green (it sits on the cut line today).
4. **A8 + A6 — memo sections.** Nearly free: they reuse data already fetched and make the memo feel researched rather than generated.
5. **Everything in Group B** is the post-hackathon roadmap — PRODUCT.md's v1/v2 in concrete form. Do not pull it forward before the judge path ships.
6. **Group C items** — the epic-9 session answered the affordable ones (inline above); anything still open costs one small follow-up probe before adoption.

---

*Parameters, DI IDs, and spike items are owned by [QLOO_APIS.md](QLOO_APIS.md) — 16 Oct 2026 snapshot; epics are owned by [PLAN.md](PLAN.md).*
