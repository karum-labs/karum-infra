# Karum decision record — 14 Oct 2026 · updated 17 Oct 2026 (brand pivot)

One page that locks the shape of the five-repo build. Sources: [PRODUCT.md](PRODUCT.md) (the product and its must-builds) and [TECH.md](TECH.md) (the five-repo split). Anything not recorded here is out of scope until this page changes.

> **17 Oct 2026 — brand pivot.** The product became the brand-operated expansion agent ([PLAN.md](PLAN.md); [PRODUCT.md](PRODUCT.md) §2). The leasing-era rows below — neighbour confirmation, `ResolveEntities` / `GetBlockProfile` / `ScoreCandidates`, the vacancy / do-not-lease framing, and the Shelfwise fallback — are superseded where they disagree: [PLAN.md](PLAN.md) wins, and Qloo facts live in [QLOO_APIS.md](QLOO_APIS.md). Still current: the two-person split (§5), the spike outcomes and quota (§6), and the stack adaptations (§2).

## 1. Service map

Every PRODUCT.md **must-build** has exactly one owning service. Other repos contribute, but the owner is who gets paged when it breaks.

| Must-build | Owner | Where it lands |
| --- | --- | --- |
| Neighbour resolution with confirmation | `service-taste` | `ResolveEntities` ranks candidates; `server` owns the confirmation pause and `POST` confirm, `client` renders the confirm chips |
| Block taste tags | `service-taste` | `GetBlockProfile` tag fan-out from confirmed neighbour ids |
| Brand-affinity candidate generation under a location filter | `service-taste` | `signal.location=POINT(<lon> <lat>)` — the filter the spike verified 16 Oct (`filter.location*` variants are silent no-ops, DI-11); no undocumented parameters |
| Category saturation check | `service-taste` | category presence within the geocoded radius |
| Three-part score and ranking | `service-taste` | `ScoreCandidates`: catchment fit, co-tenancy complement, cannibalisation penalty, deterministic ties |
| "Do not lease" list | `service-taste` | machine-readable reason codes; `client` renders the column from those codes |
| Evidence drawer and call trace | `server` | taste returns the `EvidenceCall` records, server freezes the snapshot and streams trace events over SSE, `client` renders the drawer |
| Map with pins | `client` | OSM/CARTO tiles, radius ring, optional heatmap and site-visit polyline |
| LLM-only comparison panel | `service-ai` | `LlmOnlyBaseline` on the same inputs; `client` labels it ungrounded |
| Memo PDF and outreach email | `service-ai` | draft text comes from `DraftMemo` / `DraftOutreach` / `DraftListing`; `server` renders the PDF, `client` offers the actions |
| Two pre-warmed sample blocks | `infra` | fixture pack, seed ids, Makefile `prewarm`; `service-taste` serves the prewarm RPC — first block anchored 16 Oct: Mumbai Colaba (carries all spike evidence); the second locks with the Western demo city in epic 10 |
| Public hosting, MIT licence, README with architecture and honesty rules | `infra` | Cloud Run manifests, Compose, shared run path; each repo carries its own `LICENSE` |

Should-build and nice-to-have follow the same map: heatmap and compare are optional RPCs in `service-taste` behind a capability flag, demographics live in `GetBlockProfile`, probes in `service-ai`, saved vacancies and re-run diff in `server`, the leave-one-out CLI in `infra`, and the brand-side view and MCP tool stay in `server` + `client` behind flags that are off by default.

## 2. Stack adaptations

These depart from PRODUCT.md's sketch and are settled:

1. **Flutter web** (not Next.js) as the judge target, with the same screens on desktop.
2. **Server-rendered PDF** for the memo, produced by the Go gateway, not a client-side renderer.
3. **Map tiles in the client** — the Flutter client draws OSM/CARTO tiles directly.
4. **Google Places as pin enrichment only**, and only when a key is set.
5. **Google Routes as an optional broker site visit**, skipped when the key or stop count is insufficient.

## 3. Out of scope

No login wall on the demo, no payments, no footfall feeds, no listing-site scraping, no multi-floor mall planner, no custom ML models, and no undocumented Qloo parameters anywhere in code, fixtures, or prompts. Sample and free-entry analyses run with no account.

## 4. Kill rules and the Shelfwise fallback

Abandon Karum (decide by the coverage gate, before feature work continues) if any of these is true:

1. In 3 of 5 test blocks, brand or place outputs under location do not change meaningfully when the neighbours change — Qloo is not adding block-specific signal. **Preliminary 16 Oct:** the Colaba block passes — membership and rank shift clearly when the signal changes (7 new brand entities when `signal.location` was added; India-native labels surface with the block signal); the formal 3-of-5 pass runs in epic 10.
2. Fewer than 70% of real neighbourhood venues resolve via `/search` in the demo cities. **Mumbai (a demo city), measured 16 Oct: 10 of 10 real Colaba venues resolved by plain name and landed within 2 km of the block point — passes.** The Western demo city is measured in epic 10.
3. Top candidate brands are mostly non-retail or implausible for small units after filtering. **Preliminary 16 Oct:** observed candidate sets skew retail / F&B (India-native fashion labels on Colaba); the filtered test runs after the epic 15 filters.
4. The leave-one-out test beats the LLM-only baseline on fewer than 12 of 20 blocks.
5. Median end-to-end latency stays above 20s after caching and parallelisation.
6. Three non-technical testers cannot explain the recommendation after 60 seconds.
7. The rules page prohibits the approach. **Checked 16 Oct:** the rules were read in full — nothing prohibits it ([PRODUCT.md](PRODUCT.md)).

**Fallback: Shelfwise**, the independent bookstore and record-store buying agent. The pivot keeps the same gRPC boundaries — `ResolveEntities`, `ResolveTags`, `GetBlockProfile`, `ScoreCandidates`, and the AI RPCs keep their shapes; only the Qloo entity types inside `service-taste` change from places and brands to books and artists. The gateway, the client screens, and the evidence rules do not change.

## 5. Two-person split

- **Side A — taste, score, agent, eval:** `karum-service-taste`, `karum-service-ai`, the coverage spike (done 16 Oct — [spike/RECORDING.md](spike/RECORDING.md)), the scoring rubric, the probe loop, and the leave-one-out harness in `karum-infra`.
- **Side B — UI, map, drafts, deploy, Devpost:** `karum-client`, `karum-server`, the Cloud Run and Compose deploy path in `karum-infra`, the memo/outreach copy, and the Devpost text.

Shared surface: `karum-infra/proto` is the contract between the sides — a change there needs a word from both. Each README carries this split as its ownership note.

## 6. Qloo spike outcomes — 16 Oct 2026

The coverage gate ran early and the spike is complete: all 22 items carry verdicts (item 7's 429 deliberately unprobed; the deferred tier closed 12–14, 18–20, 22 and 15's tag half the same day). It already touches kill rules 1–3 (preliminary) and clears rule 7. Evidence: [spike/RECORDING.md](spike/RECORDING.md); parameter verdicts: [QLOO_APIS.md](QLOO_APIS.md) §5 and the closed §9 register (new: DI-21, DI-22, DI-23).

What it locks for this page:

- **Location filter** (§1, row 3): `signal.location=POINT(<lon> <lat>)`; `filter.location` / `.query` / `.metro` are silently ignored.
- **Kill rule 1:** Colaba passes preliminary (see above); the formal 3-of-5 pass runs in epic 10.
- **Kill rule 2:** Mumbai passes 10/10 (see above); the Western city's rate is measured in epic 10.
- **Demo cities:** Mumbai Colaba is the locked second demo city; the Western lead city (NYC / London / Austin) and both sample blocks lock in epic 10 ([PLAN.md](PLAN.md); [PRODUCT.md](PRODUCT.md) §India wedge).
- **Code rules going into `service-taste`:** `/search` takes a bare `lat,lon` pair while Insights takes WKT only (DI-21); Insights point queries always carry an explicit `filter.location.radius` (omitted → zero rows); `warnings[].not_found` is surfaced, never silently scored on; only spike-verified spellings ship — the no-op variants are listed in the DI register.
- **Compare RPC (epic 16):** parse `results.matchEntities` — the envelope is `{tags, a, b, matchEntities}`, not the `/search` array (DI-22); `model` and `filter.subtype` accepted with identical shape.
- **Signal hygiene:** `signal.interests.entities.include` is a boolean (DI-23); `resolve_to` literals limited to `urn:reference:brand` / `both` (DI-16); scalar `weight` accepts number/string but showed no observable effect on the spike call — pair any weighting with a diff test. Trending needs ≥ ~6-month windows and stays out of the MVP (spike 20).
- **Quota:** 144 of the 10,000 monthly requests used (123 spike + 21 extension probes; 9,856 remaining, 17 Oct; the DI-1 prod-host 401 is not metered). The 17 Oct extension verified the brand→place direction and the skip-pool batch probe and found Madre Mezcal absent from Qloo coverage — see [spike/RECORDING.md](spike/RECORDING.md).
