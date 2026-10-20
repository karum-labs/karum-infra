# Technical architecture

Karum is the brand-operated retail expansion agent in [PRODUCT.md](PRODUCT.md). A brand supplies its identity — a resolved Qloo brand, or a composite cultural seed of two to four reference entities and lifestyle tags — a target city, and a mode. The system ranks the doors to pitch, the blocks for a flagship or pop-up, and the non-competing partners, then audits live menus, scores each door, writes the pitch, and sequences the field route.

Five repositories keep that work parallel: Qloo access in one service, Vertex grounding and drafts in another, orchestration in the Go gateway, and the judge UI in Flutter. [PLAN.md](PLAN.md) is the build checklist. Every Qloo parameter below is a spike-settled recipe in [QLOO_APIS.md](QLOO_APIS.md).

## The 5-repository layout

```text
├── karum-infra/          # This repo: shared Protobufs, Docker Compose, Cloud Run manifests
├── karum-client/         # Flutter web UI (judge target; same screens on desktop)
├── karum-server/         # Go + Gin API gateway (jobs, Places, Routes, score assembly, PDF)
├── karum-service-taste/  # Qloo access, caching, cultural affinity, demographics, heatmap
└── karum-service-ai/     # Vertex AI, Google Search grounding, SKU choice, pitches
```

## What each service does

### service-taste

Python (uv-managed) gRPC service. Stubs come from `karum-infra/proto/` via buf. It is the only process that holds the Qloo `X-Api-Key`, and the only one that speaks to `https://hackathon.api.qloo.com`.

- **Seed resolution.** `ResolveBrandSeed` turns a brand name, or the fallback vibe queries, into ranked entity candidates via `GET /search` (`urn:entity:brand`, `urn:entity:place`, `urn:entity:artist`). Confidence is derived from rank and name match, because `/search` publishes no score. A miss is an `unresolved` error.
- **Tag resolution.** `ResolveTags` maps a venue-category or lifestyle chip onto tag URNs via `GET /v2/tags`. A chip with no confident hit comes back unresolved for the UI to show.
- **Door scouting.** `ScoutDoors` ranks places for the confirmed seed inside an explicit metre radius. Each door carries affinity, shared taste tags, `feature.explainability` contributions, and demographic alignment. Doors under the affinity floor are returned on the skip list with a machine-readable reason. The evidence payload lists every Qloo call.
- **Flagship heatmap.** `GetLocalityHeatmap` returns heatmap cells, and locality polygons when the caller asks for the `urn:entity:locality` boundary, so the map can name the top corridors and their anchor neighbours.
- **Conquest overlap.** `CompareAudiences` calls `/v2/analysis/compare` for a door against the emerging brand and an incumbent found on the menu. The chart uses the `tags` overlap. `matchEntities` is parsed and treated as empty when the payload has none.
- **Caching.** Redis, keyed by a canonical hash of the request, with an in-process fallback, so repeated taste calls do not burn the 10,000 request monthly quota. Fixture files are redacted; raw Qloo JSON never lands in a repo.

### service-ai

Python (uv-managed) gRPC service using `google-genai` — Gemini AI Studio when `AI_GEMINI_API_KEY` is set, Vertex AI (`vertexai=True`) otherwise — on `gemini-3.8-flash`, with Pydantic response models. Every response carries `model_id`, `prompt_version`, and cited evidence ids.

- **Menu audit.** `AuditMenu` attaches Google Search grounding and reads the venue's live menu, shelf, or delivery listings. It returns whether the audit succeeded, whether an incumbent competitor is stocked, the competitor names, a short menu summary, the shelf-opportunity inputs, and the grounding URLs. Grounding runs on the working shortlist, not on every raw candidate.
- **Pitch.** `DraftDoorPitch` writes the shopkeeper script, the displacement battlecard when an incumbent is present, the SKU picked from the brand's own list using the door's taste tags, and the collab proposal or site-brief paragraph when the mode asks for it. Numbers in the prose cite evidence ids.
- **Counterfactual.** `LlmOnlyBaseline` answers the same brand, city, and mode with no Qloo payload. The client labels that panel ungrounded.
- **Fallback.** If Vertex errors, times out, or breaks the schema, the gateway still has the taste ranking. Prose that would invent a reason is skipped, and the run is marked `degraded`.

### server

Go 1.22+ Gin gateway. It is the only public HTTP surface.

- `POST /api/v1/scout` creates a job from the confirmed seed, the city, the mode, and the SKU list, and returns a job id; a request that names a preset serves the newest ready stored run and replays its recorded trace, and only free entry runs the live pipeline. `GET` returns state and the campaign payload. `GET /events` is an SSE stream with a cursor.
- Geocodes the city once and reuses that lat/lng for the map, the scout radius, the heatmap, and Places. The three judge presets send coordinates and already-resolved seed ids.
- Calls taste, then Google Places API (New) for address, hours, website, and open status on the working set, then service-ai, then Google Routes with `optimizeWaypointOrder` across the qualified doors.
- Assembles the door score (below) after both microservices have reported. Persists the run, its trace-event stream, and the frozen evidence snapshot, so a stored preset can replay its recorded trace and a later cache refresh cannot rewrite the snapshot.
- Renders the PDF run-sheet (wholesale and collab) and the site-selection brief (flagship).

### client

Flutter web is the judge target; the same screens run on desktop. There is no login. The gateway base URL is `--dart-define=GATEWAY_URL`.

The screen is a mode switcher and three preset buttons, a seed builder with a live trace, a map, and a door board. The map has three layers: numbered field-route stops, the heatmap, and red skip pins. The board shows the top recommended doors with three sub-score bars, the SKU badge, menu citations, the evidence drawer, the skip list, and the LLM-only toggle. The client draws OSM or CARTO tiles itself; the gateway supplies the pins, the cells, and the route legs, with Google attribution on Places and Routes data.

## Campaign modes

The mode pills are `Wholesale Doors`, `Flagship & Pop-Up`, and `Brand Collabs`.

| Mode | Taste query | What the brand leaves with |
| --- | --- | --- |
| Wholesale | Places ranked from the seed, inside the city radius, in the venue categories the brand sells through | Top doors, skip list, per-door SKU, pitch, field route, PDF run-sheet |
| Flagship | `urn:heatmap` for the same seed, plus anchor neighbours in the strongest cells | Top corridors, site-selection brief |
| Collab | The wholesale query with `filter.tags` restricted to non-competing lifestyle categories | Partner venues and a co-branded activation proposal |

Conquest and SKU assortment are wholesale outputs, not extra pills. When the menu audit finds an incumbent, that door's card carries a displacement battlecard backed by `CompareAudiences`. The SKU badge is the brand SKU whose palette matches the door's taste tags.

Judge presets, each pre-warmed end-to-end and stored:

- Austin — Sola yuzu mezcal (Ilegal Mezcal, Aesop, Khruangbin — Madre Mezcal is absent from Qloo coverage; 17 Oct extension) — wholesale
- Brooklyn — minimalist ceramics and matcha — flagship, plus a stored collab run so the mode toggle is instant
- Mumbai, Colaba — specialty cacao and coffee — wholesale

## The door score

`service-taste` returns cultural affinity and demographic alignment. `service-ai` returns shelf opportunity and the competitor count from the menu audit. The gateway computes the composite from 0–1 sub-scores, displays it as a 0–100 number, and writes the formula and the inputs into the evidence payload:

`S_door = 0.50 · A_taste + 0.30 · O_shelf + 0.20 · D_demo` (sub-scores 0–1; the card shows `100 · S_door`)

- **A_taste** — Qloo affinity between the seed and the venue, displayed as a percentile inside the returned shortlist (raw affinity bands move with the seed and the city — Austin: brand seed 0.85 vs place 0.97; Colaba: both ~0.94–0.97 on 17 Oct), with explainability contributions attached and the raw value kept in the evidence.
- **O_shelf** — starts at 1.0 when grounding finds a complementary menu and no exclusive lock from a direct peer; each direct niche competitor found on the live menu takes a quarter off (1.0, 0.75, 0.50, 0.25), and four or more skip the door instead of scoring it.
- **D_demo** — alignment between the venue's `urn:demographics` age buckets and the brand's target cohort, mapped onto 0–1, plus heatmap intensity for the block.
- **P_saturation** — the skip rule, applied after scoring and never a term in the composite: a door whose affinity falls below the returned shortlist's floor (its minimum or bottom decile — the absolute 0.45 threshold was retired 17 Oct; ranked sets observed 0.83–0.98), or whose audit finds four or more direct niche competitors, is returned on the skip list with its reason code and keeps its sub-scores in the evidence.

Ties break deterministically. The client renders server rank and does not re-sort. When grounding is unavailable, `O_shelf` is unknown, the composite renormalizes over `A_taste` and `D_demo`, and the card says the menu was not verified.

## Qloo calls the spike settled

All requests use `https://hackathon.api.qloo.com` and the `X-Api-Key` header. A 200 does not prove a parameter was honoured. The client in `service-taste` implements only spellings the 16 Oct spike and the 17 Oct extension verified.

| Step | Call | Settled constraint |
| --- | --- | --- |
| Resolve the seed | `GET /search` | Bare `filter.location=<lat>,<lon>` and `filter.radius` in miles. WKT is rejected here. Leave `sort_by` at the default for name lookup. Types `place`/`brand`/`artist` all resolve (17 Oct); the top row is not necessarily the right city — check the geocode city. |
| Resolve a chip | `GET /v2/tags` | `feature.typo_tolerance=true`. Namespace restriction via `filter.tag.types` works. Rows key the URN as `id` (not `tag_id` — DI-24). |
| Rank doors | `GET /v2/insights` with `filter.type=urn:entity:place` | `filter.location=POINT(<lon> <lat>)` plus an explicit `filter.location.radius` in metres. Omitting the radius on a point returns zero rows. `feature.explainability=true`. A brand (or mixed brand/place/artist) seed ranks venue rows (17 Oct). Send `filter.tags=<category>` — unfiltered top slots are landmarks and retail, not doors. |
| Score skip candidates | Same call plus `filter.results.entities=<id>,<id>,…` | Batch-verified 17 Oct: one call returns every candidate with `query.affinity`, so the skip list compares the naive-plan venues against the returned shortlist's floor (relative, not absolute). |
| Localise a brand-type insights call | `signal.location=POINT(<lon> <lat>)` | `filter.location`, `filter.location.query`, and `filter.location.metro` are silent no-ops on `urn:entity:brand` (DI-11). Door ranking itself is a place call, so it uses the place filter above. |
| Door fingerprint | `GET /v2/insights` with `filter.type=urn:tag` | Returns data. The type is absent from the Insights enum (DI-2). Signal with the venue id. |
| Flagship heatmap | `GET /v2/insights` with `filter.type=urn:heatmap` | `urn:heatmap` is the only spelling. `output.heatmap.boundary=urn:entity:locality` returns locality polygons instead of cells. |
| Demographics | `GET /v2/insights` with `filter.type=urn:demographics` | Works. Request it for the top doors, not the full candidate pool. |
| Conquest overlap | `GET /v2/analysis/compare` | Body is `{tags, a, b, matchEntities}`. `matchEntities` was empty on the probed pairs (DI-22). |

`take` maxes at 50 on Insights. The scout asks for 25 and the board shows the top six plus the skip list. Independent calls run in parallel under a fan-out cap; the observed per-second limit is 5. `POST /v2/insights` accepts a JSON body, and GET remains the default.

## End-to-end flow

```text
[ karum-client — Flutter web ]
        │  POST /api/v1/scout  (seed, city, mode, SKUs)
        ▼
[ Go gateway (karum-server) ]
        │  geocodes the city once → one lat/lng reused by the map,
        │  the scout radius, the heatmap, and Places
        │
        ├── 1. gRPC ──► [ service-taste ] ──► Qloo
        │              ResolveBrandSeed → ScoutDoors
        │              (+ GetLocalityHeatmap in flagship,
        │               CompareAudiences when an incumbent is found)
        │
        ├── 2. HTTP ──► Google Places API (New)
        │              address, hours, website, open status
        │
        ├── 3. gRPC ──► [ service-ai ] ──► Vertex AI + Search grounding
        │              menu audit, SKU, pitch, battlecard, LLM-only baseline
        │
        ├── 4. assemble S_door, then HTTP ──► Google Routes API
        │              optimal stop order across the qualified doors
        │
        ▼  job state, SSE trace, campaign payload, PDF
[ karum-client — Flutter web ]
```

Each process boots in `live`, `fixture`, or `degraded` mode (`*_MODE` in [.env.example](.env.example)). Fixture mode replays the redacted recordings and makes no outbound calls, so the stack runs with no keys present. Stored preset runs are the judge path: the prewarm runs each preset end-to-end once — `LlmOnlyBaseline` included — and stores the completed run, so a preset click serves the newest ready stored run and its recorded trace — under a second, no live pipeline. A live free-entry scout targets under eight seconds, and the trace keeps emitting on that path.
