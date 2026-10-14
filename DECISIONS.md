# Karum decision record — 14 Oct 2026

One page that locks the shape of the five-repo build. Sources: [PRODUCT.md](PRODUCT.md) (the product and its must-builds) and [TECH.md](TECH.md) (the five-repo split). Anything not recorded here is out of scope until this page changes.

## 1. Service map

Every PRODUCT.md **must-build** has exactly one owning service. Other repos contribute, but the owner is who gets paged when it breaks.

| Must-build | Owner | Where it lands |
| --- | --- | --- |
| Neighbour resolution with confirmation | `service-taste` | `ResolveEntities` ranks candidates; `server` owns the confirmation pause and `POST` confirm, `client` renders the confirm chips |
| Block taste tags | `service-taste` | `GetBlockProfile` tag fan-out from confirmed neighbour ids |
| Brand-affinity candidate generation under a location filter | `service-taste` | the location filter the Qloo spike verified; no undocumented parameters |
| Category saturation check | `service-taste` | category presence within the geocoded radius |
| Three-part score and ranking | `service-taste` | `ScoreCandidates`: catchment fit, co-tenancy complement, cannibalisation penalty, deterministic ties |
| "Do not lease" list | `service-taste` | machine-readable reason codes; `client` renders the column from those codes |
| Evidence drawer and call trace | `server` | taste returns the `EvidenceCall` records, server freezes the snapshot and streams trace events over SSE, `client` renders the drawer |
| Map with pins | `client` | OSM/CARTO tiles, radius ring, optional heatmap and site-visit polyline |
| LLM-only comparison panel | `service-ai` | `LlmOnlyBaseline` on the same inputs; `client` labels it ungrounded |
| Memo PDF and outreach email | `service-ai` | draft text comes from `DraftMemo` / `DraftOutreach` / `DraftListing`; `server` renders the PDF, `client` offers the actions |
| Two pre-warmed sample blocks | `infra` | fixture pack, seed ids, Makefile `prewarm`; `service-taste` serves the prewarm RPC |
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

1. In 3 of 5 test blocks, brand or place outputs under location do not change meaningfully when the neighbours change — Qloo is not adding block-specific signal.
2. Fewer than 70% of real neighbourhood venues resolve via `/search` in the demo cities.
3. Top candidate brands are mostly non-retail or implausible for small units after filtering.
4. The leave-one-out test beats the LLM-only baseline on fewer than 12 of 20 blocks.
5. Median end-to-end latency stays above 20s after caching and parallelisation.
6. Three non-technical testers cannot explain the recommendation after 60 seconds.
7. The rules page prohibits the approach.

**Fallback: Shelfwise**, the independent bookstore and record-store buying agent. The pivot keeps the same gRPC boundaries — `ResolveEntities`, `ResolveTags`, `GetBlockProfile`, `ScoreCandidates`, and the AI RPCs keep their shapes; only the Qloo entity types inside `service-taste` change from places and brands to books and artists. The gateway, the client screens, and the evidence rules do not change.

## 5. Two-person split

- **Side A — taste, score, agent, eval:** `karum-service-taste`, `karum-service-ai`, the coverage spike, the scoring rubric, the probe loop, and the leave-one-out harness in `karum-infra`.
- **Side B — UI, map, drafts, deploy, Devpost:** `karum-client`, `karum-server`, the Cloud Run and Compose deploy path in `karum-infra`, the memo/outreach copy, and the Devpost text.

Shared surface: `karum-infra/proto` is the contract between the sides — a change there needs a word from both. Each README carries this split as its ownership note.
