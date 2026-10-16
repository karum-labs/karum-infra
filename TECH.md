# Technical architecture

The system is five repositories, split so two people can build the backend in parallel — one on Qloo data wrangling and taste scoring, one on LLM prompting and drafts, with a shared protobuf contract between them. This is the shape [PLAN.md](PLAN.md) executes and [DECISIONS.md](DECISIONS.md) §2 records.

## The 5-repository layout

```text
├── karum-infra/          # This repo: shared Protobufs, Docker Compose, Cloud Run manifests
├── karum-client/         # Flutter web UI (judge target; same screens on desktop — no mobile app)
├── karum-server/         # Go + Gin API gateway (routes traffic, orchestrates jobs)
├── karum-service-taste/  # Microservice 1: Qloo API integration, caching, & taste scoring
└── karum-service-ai/     # Microservice 2: Vertex AI, Google Search Grounding, & draft generation
```

## What each microservice does

### 1. service-taste (The Taste & Correlation Service)

- **Primary tech:** Python (uv-managed) + gRPC; stubs generated from `karum-infra/proto/` with buf.
- **Role:** The data abstraction layer for Qloo. It isolates Qloo's API quirks, `X-Api-Key` auth, rate limits, and silently-ignored parameters from the rest of the app.
- **Endpoint:** `https://hackathon.api.qloo.com` only — every endpoint and parameter is catalogued in [QLOO_APIS.md](QLOO_APIS.md).

**What it does:**

- **Entity resolution:** Resolves raw input (an address, a neighbour name, a shortlisted brand) into Qloo entity IDs via `GET /search`, flagging low-confidence hits so the gateway pauses for confirmation instead of guessing.
- **Constraint resolution:** Maps product chips ("no F&B", "fitness", "eyewear") to tag URNs via `GET /v2/tags`.
- **Block profile:** Fans out the documented `/v2/insights` calls for a block — taste tags, brand affinities (with the spike-settled location filter and `feature.explainability=true`), category saturation, and demographics.
- **Scoring:** Computes catchment fit, co-tenancy complement, and cannibalisation from documented Qloo fields only, returning the ranked shortlist, the do-not-lease list, and the evidence bundle.
- **Caching:** Private server-side cache (Redis) so replay runs do not burn hackathon quota. Recorded fixtures are redacted — raw Qloo JSON never lands in a repo (QLOO_APIS.md §1).
- **gRPC RPC:** `ResolveEntities`, `ResolveTags`, `GetBlockProfile`, `ScoreCandidates`, plus optional `GetHeatmap` and `CompareSets` behind a capability flag (PLAN epics 5, 12–16).

### 2. service-ai (The Agent & Synthesis Service)

- **Primary tech:** Python (uv-managed) + gRPC using `google-genai` and Pydantic.
- **Role:** Grounded reasoning and the judge-facing texts. Every response carries `model_id`, `prompt_version`, and cited evidence ids so the gateway persists provenance without parsing prose.

**What it does:**

- **Shortlist probe:** `ProbeShortlist` checks the ranked set for contradictions (e.g. high catchment fit in a saturated category) using entity ids, tags, and scores — never raw user text — with a bounded budget for follow-up taste calls.
- **Counterfactual baseline:** `LlmOnlyBaseline` answers the same inputs with no Qloo payload and is labeled ungrounded, powering the LLM-only toggle.
- **Drafts:** `DraftMemo`, `DraftOutreach`, and `DraftListing` — the one-page memo, the outreach email, and the listing blurb, each number citing an evidence id.
- **Grounded retail check:** `CheckRetailPresence` uses Google Search grounding to test whether a shortlisted brand has physical stores, attaching the grounding source to the evidence.
- **gRPC RPC:** `ProbeShortlist`, `LlmOnlyBaseline`, `DraftMemo`, `DraftOutreach`, `DraftListing`, `CheckRetailPresence` (PLAN epic 6).

## End-to-End Execution Flow

```text
[ karum-client — Flutter web ]
        │  POST /api/v1/analyses  (address, neighbour text, constraints)
        ▼
[ Go Gateway (karum-server) ]
        │  geocodes the vacancy first → one lat/lng reused by the map pin,
        │  the saturation radius, and the Qloo location filter
        │
        ├── 1. gRPC call ──► [ service-taste ] ──► Qloo API
        │                     (resolve → block profile → score; explainability + evidence)
        │
        ├── 2. HTTP call ──► Google Places API
        │                     (optional pin enrichment: address, hours, website)
        │
        ├── 3. gRPC call ──► [ service-ai ] ──► Vertex AI + Search
        │                     (probe, LLM-only baseline, memo / outreach / listing)
        │
        ├── 4. HTTP call ──► Google Routes API
        │                     (optional broker site-visit route)
        │
        ▼  Returns job state, SSE trace, and the ranked shortlist
[ karum-client — Flutter web ]
```

Each process boots in `live`, `fixture`, or `degraded` mode (`*_MODE` in [.env.example](.env.example)). Fixture mode replays the redacted recordings and makes no outbound calls, so the whole stack runs green with no keys present.
