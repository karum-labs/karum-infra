# Qloo APIs for Karum

Every Qloo endpoint Karum may call, with the exact parameters, mapped to the epics in [PLAN.md](PLAN.md). Sources: the [Qloo Knowledge Center](https://docs.qloo.com) and the official [Qloo Agentic Hackathon Developer Guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide) (page updated 2026-10-07). Anything here marked **verify** goes through the spike in PLAN epic 9 before it reaches client code.

## 1. Access rules

| Rule | Detail |
| --- | --- |
| Base URL | `https://hackathon.api.qloo.com` **only** — keys get 401 against `api.qloo.com` or `staging.api.qloo.com` |
| Auth | `X-Api-Key` header (never a query param, never `Authorization: Bearer`) |
| Method | `GET` with query-string params — `/v2/insights` is GET-only; a POST with a JSON body fails |
| Availability | **All documented endpoints are available** during the hackathon |
| Forbidden | **`/recs` and `/recommendations`** — legacy endpoints, explicitly unsupported |
| Silent failures | Unsupported parameters are **ignored, not rejected**: you get 200 with an empty result. Verify every parameter against the [Entity Type Parameter Guide](https://docs.qloo.com/reference/available-parameters-by-entity-type) before assuming a data gap |
| Insights entity types | `urn:entity:{artist, book, brand, destination, movie, person, place, podcast, tv_show, video_game}` — a 403 means the type is unsupported |
| `/search` types | Not the same set as Insights `filter.type` — see the [`/search` docs](https://docs.qloo.com/reference/get-search). Legacy types (`actor`, `album`, `author`, `director`, `locality`) exist for search only |
| Error map | 401 wrong base URL or header · 403 unsupported entity type · 400 missing or invalid signal ("at least one valid signal or filter is required") · 429 rate limit |
| Caching | Private server-side caching is allowed with **no time limit**, but **never store raw Qloo responses in a public repository** — the fixture pack must be redacted because Devpost requires public repos |
| Response fields | The full response is always returned; fields cannot be filtered (verbose `akas` etc. must be trimmed client-side) |
| Quotas | Rate and monthly limits per key, raisable via Discord `#api-help`; keys are deactivated after the judging period |

## 2. Endpoint inventory

| # | Endpoint | Karum feature | PLAN epic | Status |
| --- | --- | --- | --- | --- |
| 1 | `GET /search` | Neighbour and shortlist brand resolution | 12 | **Core** |
| 2 | `GET /v2/tags` | Constraint chips → tag URNs | 13 | **Core** |
| 3 | `GET /v2/tags/types` | Tag-type allow-list | 13 | **Core** |
| 4 | `GET /v2/insights` (`urn:tag`) | Block taste tags | 14 | **Core** |
| 5 | `GET /v2/insights` (`urn:entity:brand`) | Brand-affinity candidates | 14 | **Core** (location param **verify**) |
| 6 | `GET /v2/insights` (`urn:entity:place`) | Saturation / cannibalisation check | 14 | **Core** |
| 7 | `GET /v2/insights` (`urn:demographics`) | Audience-skew sanity check | 14 | **Core** (403 risk **verify**) |
| 8 | `GET /v2/insights` (`urn:heatmap`) | Map heatmap overlay | 16 | Optional, capability flag |
| 9 | `GET /v2/analysis/compare` | Neighbours vs. candidate overlap chart | 16 | Optional, capability flag |
| 10 | `GET /entities` | Hydrate entity cards from IDs | 40, 41 | Recommended |
| 11 | `GET /v2/trending` | "Emerging brand" momentum evidence | nice-to-have | Optional add |
| 12 | `GET /v2/audiences`, `/v2/audiences/types` | Named audience segments | — | ⚠️ OpenAPI `deprecated: true` — do not build on |
| 13 | `GET /` (API info) | Key-validity probe for `GET /health` | 31 | Optional |

## 3. Call recipes

### 3.1 Resolve neighbours — `GET /search` (epic 12)

```
/search?query=<neighbour name>
        &types=urn:entity:place
        &filter.location=<lat>,<lon>      vacancy point
        &filter.radius=<miles>            default 10, max 100
        &filter.address=<city or street>  partial match, disambiguates
        &take=5
        &sort_by=distance
```

Shortlist brands: `types=urn:entity:brand`. Also supports `filter.tags`, `filter.popularity`, `filter.rating`, `take`, `page` (max 100).

> **Unit trap:** `/search` radius is `filter.radius` in **miles** (default 10). Insights radius is `filter.location.radius` in **metres** (default 15000). Different names, different units.

### 3.2 Resolve constraints — `GET /v2/tags` (epic 13)

```
/v2/tags?filter.query=<chip text>
         &feature.typo_tolerance=true
         &feature.semantic_search=true    beta — carries free-text constraints
         &take=50
```

`feature.semantic_search` handles free-text constraints ("no national chains") that have no exact tag. The allow-list in epic 13 comes from `GET /v2/tags/types?filter.parents.types=urn:entity:place,urn:entity:brand`.

### 3.3 Block taste tags — `/v2/insights` (epic 14a)

```
/v2/insights?filter.type=urn:tag
             &signal.interests.entities=<neighbour IDs>
             &take=50
```

Optional namespace restriction: `filter.tag.types=urn:tag:...`.

### 3.4 Brand-affinity candidates — `/v2/insights` (epic 14b) — spike-critical

```
/v2/insights?filter.type=urn:entity:brand
             &signal.interests.entities=<neighbour IDs>
             &<LOCATION — see below>
             &feature.explainability=true   feeds the evidence drawer (§3.8)
             &take=50
```

**Location conflict inside Qloo's own docs — the spike settles it:**

- The [Entity Type Parameter Guide](https://docs.qloo.com/reference/available-parameters-by-entity-type) Brand table lists **no location parameter at all** (`filter.location`, `.radius`, `.query` are absent).
- The [Location-Based Insights](https://docs.qloo.com/reference/insights-with-location-use-case) use case explicitly advertises `urn:entity:brand` with location, and ships a recipe for "popular brands inside Paris center based on WKT shape".
- Candidates to test, in order: `filter.location=POINT(<lon> <lat>)`, `signal.location=POINT(<lon> <lat>)`, `signal.location.query=<locality>`, `filter.location.query=<locality>`.
- WKT is **longitude-first**; a bare `filter.location` pair is **latitude-first**. Easy bug.
- `signal.location.radius` exists, but the docs advise against it: it "overrides dynamic density discovery".
- If none of them narrows brand results, the fallback is the neighbour-entity signal with `filter.location.query=<locality>` recorded in epic 10.

### 3.5 Saturation check — `/v2/insights` (epic 14c)

```
/v2/insights?filter.type=urn:entity:place
             &filter.tags=<category tag URN>
             &filter.location=<lat>,<lon>
             &filter.location.radius=<metres>   e.g. 400; default 15000, max 800000
             &sort_by=distance
             &take=50
```

Place fully supports location params per the entity guide, and `sort_by=distance` requires `filter.location`. For the do-not-lease side, invert with `filter.exclude.tags` plus `operator.filter.exclude.tags=union|intersection`.

### 3.6 Demographics — `/v2/insights` (epic 14d)

```
/v2/insights?filter.type=urn:demographics
             &signal.interests.entities=<candidate IDs>
```

Returns per-entity age buckets and gender deltas as affinity values. **Verify:** `urn:demographics` is documented on the official [Demographic Insights](https://docs.qloo.com/reference/demographics-use-case) page but is missing from the hackathon guide's supported-`filter.type` list — 403 risk.

### 3.7 Heatmap — `/v2/insights` (epic 16, capability flag)

```
/v2/insights?filter.type=urn:heatmap
             &filter.location.query=<locality>   or filter.location=<...>
             &signal.interests.tags=<URN>        or signal.interests.entities=<id>
             &output.heatmap.boundary=urn:geohash
             &heatmap.dimensions=quality,popularity
```

Returns geohash cells with `affinity`, `affinity_rank` (0–1) and `popularity`. Two corrections to the old brief: **any** entity or tag works as the signal (the "requires a place-genre signal" line is marketing-page copy, not a docs requirement — `urn:tag:genre:place:restaurant` remains a sensible choice for Karum), and it is part of `/v2/insights`, not a separate route. Docs use both `urn:heatmap` and `urn:entity:heatmap` — confirm which resolves in the spike.

### 3.8 Explainability — the evidence-drawer source

`feature.explainability=true` on any Insights call adds `query.explainability` to each result: **which input entities contributed to it, normalized 0–1** (entities scoring ≥ 0.1 always included), plus an aggregate top-N view. This gives epic 41's "which neighbour audiences carried the affinity" straight from Qloo instead of inferring it. It is in the Insights OpenAPI spec but absent from the per-entity tables, so it is on the spike list.

### 3.9 Scoring inputs (epic 15) — documented params only

| Need | Parameter | Notes |
| --- | --- | --- |
| Popularity band | `filter.popularity.min` / `max` | 0–1 percentile; **verified** (the old brief had this unverified) |
| Price / rent proxy | `filter.price_level.min` / `max` (1–4) | Place only |
| Quality bias | `bias.quality` (`very_low`…`very_high`), `sort_by=quality` | Place only; places without a quality score drop out |
| Trends bias | `bias.trends` (`off`…`very_high`) | All types |
| Direct affinity probe | `filter.results.entities=<candidate>` | Returns just those entities with their `query.affinity` — a clean per-candidate co-tenancy probe |
| Exclude neighbours | `filter.exclude.entities=<ids>` | Stops the vacancy's own neighbours ranking as candidates |
| Demographic weighting | `signal.demographics.age` / `.gender` / `.audiences` (+ `.weight`) | Input-side weighting, separate from the `urn:demographics` output |

Also relevant: `diversify.by=subtype` + `diversify.take` are documented for `filter.type=urn:tag` only — do not assume them for brands or places.

### 3.10 Compare sets — `GET /v2/analysis/compare` (epic 16, capability flag)

```
/v2/analysis/compare?a.signal.interests.entities=<neighbour IDs>
                     &b.signal.interests.entities=<candidate ID>
                     &filter.type=urn:entity:brand
                     &model=descriptive
                     &take=50
```

`take` max 50, paginate with `page`. `model` is `descriptive` or `predictive`.

### 3.11 Trending — `GET /v2/trending` (nice-to-have)

```
/v2/trending?filter.type=urn:entity:brand
             &signal.interests.entities=<id>
             &filter.start_date=2026-01-01
             &filter.end_date=2026-10-01
```

Weekly `population_percentile`, `population_rank`, rank velocity and fold-change — an "emerging vs. established" badge for candidate cards and a momentum line in the outreach email. Cheap, distinct, judge-visible.

### 3.12 Entity hydration — `GET /entities`

```
/entities?entity_ids=<uuid>,<uuid>
```

Full entity records (description, image, properties) by ID, plus lookups by many external IDs (IMDB, Resy, Michelin…). Lets candidate and neighbour cards render Qloo-known data even where no Google Places key is set.

## 4. Do-not-use list (honesty rules)

- `/recs` and `/recommendations` — explicitly forbidden for the hackathon.
- Any parameter not in the docs — it is **silently ignored**, which our honesty rules treat as a defect: replay tests must assert non-empty results **and** that each parameter was honoured.
- `signal.location.radius` where density discovery matters — Qloo advises against it.
- `urn:entity:audience` (deprecated) and search-only legacy types outside `/search`.
- Raw Qloo JSON in fixtures — redact everything; the fixture pack ships public with the Devpost submission.
- `/v2/audiences` and `/v2/audiences/types` for new code — both carry OpenAPI `deprecated: true`; take demographics from Insights output instead.

## 5. Spike checklist (refines PLAN epic 9)

1. **Brand + location** — which of `filter.location`, `signal.location`, `signal.location.query` actually narrows `urn:entity:brand` results (entity guide says none; use case says yes).
2. **`filter.type` acceptance** — `urn:tag`, `urn:demographics`, `urn:heatmap` against 403 (the hackathon guide's list omits all three).
3. **Heatmap naming** — `urn:heatmap` vs `urn:entity:heatmap`.
4. **`feature.explainability`** — accepted on brand and place calls? What is the response shape?
5. **Radius granularity** — does `filter.location.radius=400` genuinely filter at 400 m? This settles the kill-rule-1 uncertainty.
6. **Unit sanity** — `/search` miles vs Insights metres, and both WKT orders (longitude-first) vs bare pairs (latitude-first).
7. **429 behaviour and quota headroom** — rate-limit headers, reset timing, monthly ceiling.
8. **Data density** — `filter.popularity` and `filter.price_level` populated for retail brands in the demo cities.
