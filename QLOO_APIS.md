# Qloo APIs for Karum

Every Qloo endpoint Karum may call, with the exact parameters, mapped to the epics in [PLAN.md](PLAN.md). Sources: the [Qloo Knowledge Center](https://docs.qloo.com) pages (documentation dated 2025-10-27 → 2026-07-20) and the official [Qloo Agentic Hackathon Developer Guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide) (page updated 2026-10-07). **Snapshot: 16 Oct 2026.**

Anything marked **verify** — or listed in the §5 spike checklist — goes through [PLAN.md](PLAN.md) epic 9 before it reaches client code. Every doc-vs-doc conflict carries an ID in §9; when the spike settles one, record the answer here, tick the checklist item, and close the §9 row with a date.

| § | Section | What it covers |
| --- | --- | --- |
| 1 | Access rules | Hosts, auth, limits, failure modes |
| 2 | Endpoint inventory | Every endpoint Karum may call, with status |
| 3 | Call recipes | The exact calls Karum makes, per feature |
| 4 | Do-not-use list | Forbidden endpoints, params, and habits |
| 5 | Spike checklist | The open questions epic 9 settles |
| 6 | Parameter catalogue | Every documented Insights parameter |
| 7 | Entity-type support matrix | Which parameters each `filter.type` allows |
| 8 | Response shapes | Field maps and truncated examples |
| 9 | Documentation inconsistencies register | Every doc-vs-doc conflict, mapped to a spike item |

## 1. Access rules

| Rule | Detail |
| --- | --- |
| Base URL | `https://hackathon.api.qloo.com` **only** — keys get 401 against `api.qloo.com` or `staging.api.qloo.com` |
| Docs-host trap | Every OpenAPI page in the docs lists `https://api.qloo.com` as "Production Qloo API server", and some examples use `staging.api.qloo.com`. Copy-pasted cURL must have its host swapped to the hackathon host. See DI-1. |
| Auth | `X-Api-Key` header (never a query param, never `Authorization: Bearer`) |
| Method | `GET` with query-string params — the hackathon surface is GET-only. The docs describe POST-only parameters (`filter.exclude.entities.query`, `signal.interests.entities.query`) and POST bodies that accept arrays (merged localities, weight arrays); on a GET-only surface those are unavailable until the spike proves otherwise (DI-3, spike item 10). |
| Availability | **All documented endpoints are available** during the hackathon |
| Forbidden | **`/recs` and `/recommendations`** — legacy endpoints, explicitly unsupported |
| Silent failures | Unsupported parameters are **ignored, not rejected**: you get 200 with an empty result. Verify every parameter against §7 (per-entity guide) before assuming a data gap |
| Insights `filter.type` | `urn:entity:{artist, book, brand, locality, movie, person, place, podcast, tv_show, videogame}` + `urn:heatmap` + `urn:entity:audience` (deprecated). Notes: the enum spells `videogame` with no underscore; `urn:entity:destination` has a full §7 table but is **absent** from the enum; `urn:tag` and `urn:demographics` are documented on the use-case pages but **absent** from the enum — all three are 403 risks (DI-2). `urn:entity:locality` is partially supported: only `signal.interests.entities` when the provided entities are localities. A 403 means the type is unsupported |
| `/search` types | Not the same set as Insights `filter.type` — the enum adds search-only legacy types (`actor`, `album`, `author`, `director`, `locality`) and (oddly) `urn:heatmap` and `urn:entity:audience`. Karum searches `urn:entity:place` and `urn:entity:brand` only (DI-17) |
| Error map | 401 wrong base URL or header · 403 unsupported entity type · 400 missing or invalid signal ("at least one valid signal or filter is required") · 429 rate limit |
| Pagination | `take` default 20, **max 50** on every endpoint except `/search` (exclusive max 200). `page` 1–100, default 1. `offset` arbitrary. Docs recommend `page` over `offset` |
| Caching | Private server-side caching is allowed with **no time limit**, but **never store raw Qloo responses in a public repository** — the fixture pack must be redacted because Devpost requires public repos |
| Response fields | The full response is always returned; fields cannot be filtered. Verbose payloads (`akas`, `short_descriptions`) must be trimmed client-side |
| Quotas | **10,000 requests/month** per key (key received 16 Oct 2026). Observed 16 Oct by probe: `X-Second-RateLimit-Limit: 5` (req/s), `X-Month-RateLimit-Limit: 10000`, `X-Month-RateLimit-Reset` counts down ≈ 2,592,000 s — a rolling ~30-day window, not a calendar-month reset; 429 behaviour still unprobed (spike 7). Limits are raisable via Discord `#api-help`; keys are deactivated after the judging period |

## 2. Endpoint inventory

Grouped the way the docs group them (Insights · Lookup APIs · Analysis & Trends APIs). "Docs-confirmed" means the 16 Oct 2026 snapshot shows the full parameter schema.

| # | Endpoint | Karum feature | PLAN epic | Status / notes |
| --- | --- | --- | --- | --- |
| 1 | `GET /search` | Neighbour and shortlist brand resolution | 12 | **Core** — full params §3.1 |
| 2 | `GET /entities` | Hydrate entity cards from IDs | 40, 41 | Recommended — `entity_ids` plus 22 external-ID namespaces (§3.12) |
| 3 | `GET /v2/tags` | Constraint chips → tag URNs | 13 | **Core** — §3.2 |
| 4 | `GET /v2/tags/types` | Tag-type allow-list | 13 | **Core** — §3.2b; response schema not shown in the snapshot |
| 5 | `GET /v2/audiences`, `GET /v2/audiences/types` | Named audience segments | — | ⚠️ OpenAPI `deprecated: true` — do not build on (§4); audience IDs for `signal.demographics.audiences` still come from here (DI-20) |
| 6 | `GET /v2/insights` (`urn:tag`) | Block taste tags | 14 | **Core** — enum-absent, 403 risk (DI-2); §3.3 |
| 7 | `GET /v2/insights` (`urn:entity:brand`) | Brand-affinity candidates | 14 | **Core** — location param **verify** (§3.4) |
| 8 | `GET /v2/insights` (`urn:entity:place`) | Saturation / cannibalisation check | 14 | **Core** — location fully supported (§3.5) |
| 9 | `GET /v2/insights` (`urn:demographics`) | Audience-skew sanity check | 14 | 403 risk — enum-absent (DI-2); §3.6 |
| 10 | `GET /v2/insights` (`urn:heatmap`) | Map heatmap overlay | 16 | Optional, capability flag — enum-confirmed; boundary literals **verify** (§3.7) |
| 11 | `GET /v2/analysis/compare` | Neighbours vs. candidate overlap chart | 16 | Optional, capability flag — §3.10 |
| 12 | `GET /v2/trending` | "Emerging brand" momentum evidence | nice-to-have | Optional add — §3.11 |
| 13 | `GET /` (API info) | Key-validity probe for `GET /health` | 31 | Optional — not covered by this snapshot |

## 3. Call recipes

These are the calls Karum makes, each with the full documented parameter surface. Where the docs disagree with themselves, the §9 ID is cited and the spike settles it.

### 3.1 Resolve neighbours — `GET /search` (epic 12)

```
/search?query=<neighbour name>
        &types=urn:entity:place
        &filter.location=<lat>,<lon>      # bare lat,lon pair ONLY — WKT and Qloo UUIDs are rejected (spike 6, DI-21)
        &filter.radius=<miles>            # default 10, max 100 — MILES, see the unit trap
        &filter.address=<city or street>  # partial match, comma-separated terms
        &take=5                           # exclusive max 200
        &page=1                           # 1–100
        &sort_by=distance                 # match | distance | popularity — default match
```

Shortlist brands: `types=urn:entity:brand`. Other supported parameters: `filter.tags` (+ `operator.filter.tags=union|intersection`, default `union`), `filter.popularity` (min, 0–1), `filter.rating` (min, 0–5), `filter.exists` (e.g. `external.resy`, `external.michelin` — pattern `^external\.\w+$`; `filter.exists=external.resy` returned NYC Resy venues on the first try, 16 Oct).

> **Unit trap:** `/search` radius is `filter.radius` in **miles** (default 10). Insights radius is `filter.location.radius` in **metres** (default 15000). Different names, different units.

### 3.2 Resolve constraints — `GET /v2/tags` (epic 13)

```
/v2/tags?filter.query=<chip text>
         &filter.tag.types=urn:tag:...      # optional namespace restriction
         &feature.typo_tolerance=true       # default false
         &feature.semantic_search=true      # beta; carries free-text constraints
         &filter.popularity.min=&max=       # 0–1 (optional)
         &take=50                           # max 50
         &page=1
```

`feature.semantic_search` handles free-text constraints ("no national chains") that have no exact tag. The response is `results.tags` (§8.6). `filter.parents.types` is documented here too, but its schema enum is contradictory (DI-8, spike 13).

### 3.2b Tag-type allow-list — `GET /v2/tags/types` (epic 13)

```
/v2/tags/types?filter.parents.types=urn:entity:place,urn:entity:brand
              &take=50
              &page=1
```

Documented exactly like that, but the snapshot's schema enum for `filter.parents.types` lists `urn:audience:*` values while the prose and Taste Analysis use `urn:entity:*` parents — **verify** which is accepted (DI-8, spike 13). This list is the epic 13 allow-list of tag types Karum can explain.

### 3.3 Block taste tags — `/v2/insights` (epic 14a)

```
/v2/insights?filter.type=urn:tag
             &signal.interests.entities=<neighbour IDs>
             &filter.tag.types=urn:tag:keyword:media     # optional namespace restriction
             &signal.location.query=<locality>           # optional localisation
             &take=50
```

The Taste Analysis page requires `filter.type=urn:tag` **plus at least one** of: `signal.interests.entities`, `signal.interests.tags`, `signal.demographics.audiences`, `signal.location` / `signal.location.query`, `filter.tag.types`, `filter.parents.types`. Response is `results.tags` (§8.2). `urn:tag` is absent from the Insights enum, but the 403 risk is settled: **it works** (spike 2, 16 Oct — 20 tags for the Colaba block); `urn:demographics` and `urn:entity:destination` work too. `urn:entity:locality` 400s unless signalled by locality entities.

### 3.4 Brand-affinity candidates — `/v2/insights` (epic 14b) — spike-critical

```
/v2/insights?filter.type=urn:entity:brand
             &signal.interests.entities=<neighbour IDs>
             &<LOCATION — see below>
             &feature.explainability=true     # feeds the evidence drawer (§3.8)
             &bias.trends=medium              # off…very_high, default medium
             &filter.popularity.min=          # safe-vs-emerging band, 0–1
             &filter.exclude.entities=<neighbour IDs>
             &take=50
```

**Location conflict inside Qloo's own docs — the spike settles it:**

- The [Entity Type Parameter Guide](https://docs.qloo.com/reference/available-parameters-by-entity-type) Brand table lists **no location parameter at all** (`filter.location`, `.radius`, `.query` are absent).
- The [Location-Based Insights](https://docs.qloo.com/reference/insights-with-location-use-case) use case explicitly advertises `urn:entity:brand` with location, and ships a recipe for "popular brands inside Paris center based on WKT shape".
- **Settled 16 Oct (spike 1):** `signal.location=POINT(<lon> <lat>)` is the only one that changes results — 7 new entities plus a re-rank in the Colaba test (Sabyasachi, Gaurav Gupta, Manish Malhotra); `signal.location.query=<locality>` shifts rankings subtly (1 new entity). `filter.location`, `filter.location.query` and `filter.location.metro` were byte-identical to baseline — silently ignored. Identical repeat responses also proved the API replays deterministically, which makes paired probes trustworthy.
- WKT is **longitude-first**; the `/search` bare pair is **latitude-first**. Easy bug.
- `signal.location.radius` exists (metres, max 800000), but the docs advise against it: it "overrides dynamic density discovery". Untested — not needed.
- The neighbour-entity signal alone is the working base; `signal.location` adds localisation when the block's point is known.

### 3.5 Saturation check — `/v2/insights` (epic 14c)

```
/v2/insights?filter.type=urn:entity:place
             &filter.tags=<category tag URN>
             &filter.location=POINT(<lon> <lat>)   # Insights takes WKT only — a bare pair 400s (spike 6)
             &filter.location.radius=<metres>      # genuine metres (400 m kept max 394 m); omit on a point → 0 results; 0 ≈ 15 km default (spike 5)
             &sort_by=distance                     # requires filter.location
             &take=50
```

Place fully supports location params per the entity guide. **Correction (spike 5, 16 Oct):** for a WKT *point*, an omitted `filter.location.radius` returns **zero results** — always send a radius. `0` falls back to the ~15 km default (max observed distance 13.8 km), not strict containment; positive radii are metres-exact. `filter.exclude.location.radius` is silently ignored.

Optional place refinements, all documented in the snapshot — exact names and ranges in §6.1:

- Price / rent proxies: `filter.price_level.min` / `.max` (1–4), `filter.price_range.from` / `.to` — **spike-confirmed**; the `.min` / `.max` variant is silently ignored (DI-5 closed 16 Oct).
- Quality proxies: `filter.hotel_class.min` / `.max` (1–5), `filter.rating.min` / `.max`, `filter.properties.business_rating.min` / `.max`, `filter.external.tripadvisor.rating.min` / `.max` (+ `.count.min/.max`), `filter.external.exists=michelin,resy`.
- Resy demand: `filter.external.resy.rating.min` / `.max` — **spike-confirmed**; the `filter.properties.resy.*` and `filter.resy.rating_count.*` spellings are silently ignored (DI-4 closed 16 Oct; `.party_size` untested).
- Fit filters: `filter.hours=<weekday>`, `filter.address=<partial>`, `filter.references_brand=<brand IDs>`, `filter.popularity.min` / `.max`.
- For the do-not-lease side, invert with `filter.exclude.tags` plus `operator.exclude.tags=union|intersection` — **spike-confirmed** (include + exclude of the same tag → 0 rows; both operator spellings produced identical results, DI-13 closed 16 Oct).

### 3.6 Demographics — `/v2/insights` (epic 14d)

```
/v2/insights?filter.type=urn:demographics
             &signal.interests.entities=<candidate IDs>
             &signal.interests.tags=<tag URN>        # optional; may be combined
```

Requires `filter.type=urn:demographics` plus at least one of `signal.interests.entities` / `signal.interests.tags`; both may be sent together. Returns `results.demographics`: per `entity_id`, an `age` bucket map and a `gender` map of deltas (positive = stronger-than-average alignment). Sample shapes in §8.3. **Settled 16 Oct (spike 2/17):** no 403 — `urn:demographics` works; observed age buckets are fine-only (`24_and_younger` … `55_and_older`, deltas within ±0.5) and mixed entities+tags returns one profile row per input (DI-7 closed; DI-2 closed).

### 3.7 Heatmap — `/v2/insights` (epic 16, capability flag)

```
/v2/insights?filter.type=urn:heatmap
             &filter.location.query=<locality>   or filter.location=POINT(<lon> <lat>)   # WKT only — a bare pair 400s (spike 6)
             &signal.interests.tags=<URN>        or signal.interests.entities=<id>
             &output.heatmap.boundary=<...>      # geohash cells by default; urn:geohash is a no-op; urn:entity:locality → locality entities with polygons (spike 3)
             &heatmap.dimensions=quality,popularity[,hotel_class][,price_level]
             &filter.dimensions.hotel_class=4,5  # only with hotel_class dimension
             &filter.dimensions.price_level=1,2  # only with price_level dimension
             &take=50
```

Returns geohash cells with `affinity`, `affinity_rank` (0–1) and `popularity` (§8.4). Two corrections to the old brief, still true: **any** entity or tag works as the signal (the "requires a place-genre signal" line is marketing-page copy — `urn:tag:genre:place:restaurant` remains a sensible choice for Karum), and it is part of `/v2/insights`, not a separate route. `heatmap.dimensions` adds `<dim>_affinity_rank` and `<dim>_affinity` per cell and influences the overall ranking; `filter.dimensions.*` additionally adds `<dim>_count_affinity_rank` and `<dim>_count_affinity`. The enum says `urn:heatmap`; the older `urn:entity:heatmap` is a hard 400 — "not supported for filter.type" (DI-18 closed, spike 3). Boundary settled by spike 3: `urn:geohash` is a byte-identical no-op, `urn:entity:locality` switches the result container to `entities` — locality rows carrying polygon geometry (8 rows at the point; 41 with `filter.location.query=Mumbai`). Dimension gating and count columns stay with spike 22 (DI-12 partial).

### 3.8 Explainability — the evidence-drawer source

`feature.explainability=true` on any Insights call adds `query.explainability`:

- **Per result** (observed 16 Oct, spike 4): `query.explainability.signal.interests.entities[]` with `{entity_id, score}` — which input entities contributed, normalized 0–1. Entities scoring ≥ 0.1 are always included; lower-impact entities may be omitted. The ≥ 0.1 rule itself was not exercised (all observed scores were 1.0).
- **Aggregate** (observed): `query.explainability.effect_on_top3/5/10/all_recs[]` with `{entity_id, avg_score}` — average influence of each input entity across top-N subsets.
- **Warning path** (observed 16 Oct): dead signal entities surface in a top-level `warnings` array — `{"type":"not_found","signal.interests.entities":[…ids]}` — while results stay normal. 3 of 4 resolved Colaba store ids failed it; treat `warnings` as the honesty check for neighbour ids.

This gives epic 41's "which neighbour audiences carried the affinity" straight from Qloo instead of inferring it. It is in the Insights OpenAPI spec but absent from the per-entity tables — spike 4 settled 16 Oct: accepted on both brand and place calls.

### 3.9 Scoring inputs (epic 15) — documented params only

| Need | Parameter | Notes |
| --- | --- | --- |
| Popularity band | `filter.popularity.min` / `.max` | 0–1 percentile; "safe vs emerging" separation |
| Price / rent proxy | `filter.price_level.min` / `.max` (1–4) | Place only; `filter.price_range.from` / `.to` as the hotel-style variant |
| Quality bias | `bias.quality` (number or weight string), `sort_by=quality` | Place only; places without a quality score drop out; weight-string sets differ by doc (DI-6) |
| Trends bias | `bias.trends` (`off`…`very_high`, default `medium`) | All types |
| Content-based bias | `bias.content_based` (0–1, default 0.5) | Deep-dive-only; balances metadata vs behavioural signal |
| Backfill dials | `backfill.cross_domain.take` (≤20), `backfill.content_based.take` (≤10) | Deep-dive-only; cap appended filler |
| Direct affinity probe | `filter.results.entities=<candidate>` | Returns just those entities with their affinity (`query.affinity`, observed 0.832) — spike 9 settled 16 Oct; the legacy `filter.entities` spelling works but adds `warnings: deprecated` |
| Tag affinity probe | `filter.results.tags=<tag IDs>` | **No-op** — byte-identical to baseline on the tested place call (spike 9, 16 Oct); do not rely on it |
| Exclude neighbours | `filter.exclude.entities=<ids>` | Stops the vacancy's own neighbours ranking as candidates |
| Signal weights | `signal.interests.entities.weight`, `signal.interests.tags.weight`, `signal.location.weight`, `signal.demographics.*.weight` | Number ≥0 or weight string `very_low`…`very_high`; spike 14 |
| Force-include entities | `signal.interests.entities.include=<ids>` | Deep-dive-only; guarantees an entity contributes to affinity |
| Sort control | `sort_by` = `affinity` / `distance` / `rating` / `quality` | `distance` requires `filter.location`; `quality` is place-only |

Also relevant: the entity guide documents `diversify.by=subtype` + `diversify.take` for `filter.type=urn:tag` only, while the deep dive documents `properties.geocode.city` / `.metro` diversification generally. Observed 16 Oct: `diversify.by=subtype` was a no-op on a brand call and `filter.location.metro` is ignored — the guide's tag-only note holds (DI-10 partial, DI-11 closed).

### 3.10 Compare sets — `GET /v2/analysis/compare` (epic 16, capability flag)

```
/v2/analysis/compare?a.signal.interests.entities=<neighbour IDs>
                     &b.signal.interests.entities=<candidate ID>
                     &filter.type=urn:entity:brand
                     &model=descriptive                  # descriptive | predictive
                     &filter.subtype=urn:tag:genre       # urn:tag:occupation | urn:tag:genre
                     &filter.location.query=<locality>   # optional scoping
                     &filter.location.radius=<metres>    # default 15000, max 800000
                     &filter.exclude.location.query=<locality>
                     &take=50                            # max 50
                     &page=1
```

Both `a.` and `b.` signals are **required**. `filter.type` is an array here. `filter.exclude.entities.query` and merged-locality arrays are POST-only (DI-3). Response reuses the entity shape (§8.7).

### 3.11 Trending — `GET /v2/trending` (nice-to-have)

```
/v2/trending?filter.type=urn:entity:brand
             &signal.interests.entities=<id>
             &filter.start_date=2026-01-01        # required, YYYY-MM-DD
             &filter.end_date=2026-10-01          # required, YYYY-MM-DD
             &take=50
             &page=1
```

Weekly rows, ordered by date descending: `population_percentile`, `population_rank`, `population_rank_velocity`, `velocity_fold_change`, `population_percent_delta` (§8.8). An "emerging vs. established" badge for candidate cards and a momentum line in the outreach email. Cheap, distinct, judge-visible.

### 3.12 Entity hydration — `GET /entities`

```
/entities?entity_ids=<uuid>,<uuid>
/entities?external.resy.ids=<id>          # or any of the namespaces below
```

Full entity records (description, image, properties) by ID, plus lookups by 22 external namespaces: `external.facebook.ids`, `external.goodreads.ids`, `external.goodreads_author.ids`, `external.igdb.ids`, `external.imdb.ids`, `external.instagram.ids`, `external.isbn10.ids`, `external.isbn13.ids`, `external.itunes.ids`, `external.lastfm.ids`, `external.library_of_congress.ids`, `external.metacritic.ids`, `external.michelin.ids`, `external.musicbrainz.ids`, `external.rottentomatoes.ids`, `external.soundcloud.ids`, `external.spotify.ids`, `external.tablet.ids`, `external.twitch.ids`, `external.twitter.ids`, `external.wikidata.ids`, `external.resy.ids`. Misses return a 404-style body, not empty results. Lets candidate and neighbour cards render Qloo-known data even where no Google Places key is set.

## 4. Do-not-use list (honesty rules)

- `/recs` and `/recommendations` — explicitly forbidden for the hackathon.
- The production hosts — never `api.qloo.com` or `staging.api.qloo.com`; the OpenAPI pages default to them (DI-1).
- POST-only parameters on the GET-only surface: `filter.exclude.entities.query`, `signal.interests.entities.query`, POST arrays for `filter.results.entities.query`, and merged-locality arrays. Off the table unless spike 10 proves POST works (DI-3).
- Any parameter not in §6/§7 — it is **silently ignored**, which our honesty rules treat as a defect: replay tests must assert non-empty results **and** that each parameter was honoured.
- `signal.location.radius` where density discovery matters — Qloo advises against it.
- `urn:entity:audience` (deprecated) and search-only legacy types (`actor`, `album`, `author`, `director`) outside `/search`. Use `urn:entity:person`.
- `urn:entity:destination` and `urn:entity:locality` as Insights `filter.type` until spike 2 proves they resolve — `destination` is absent from the enum, `locality` is partial (only `signal.interests.entities` of localities).
- `filter.types` and `filter.distance.max` — they appear only in the location use-case prose, not in any schema (DI-15).
- Raw Qloo JSON in fixtures — redact everything; the fixture pack ships public with the Devpost submission.
- `/v2/audiences` and `/v2/audiences/types` for new code — both carry OpenAPI `deprecated: true`; take demographics from Insights output instead. (Audience IDs for `signal.demographics.audiences` still nominally come from there — DI-20, spike 17.)

## 5. Spike checklist (refines PLAN epic 9)

Work every item against `https://hackathon.api.qloo.com` with the `X-Api-Key` header. Record for each: the exact request, the redacted response, and the observed behaviour. When an item settles, mark it here and close the matching §9 row; the answer then flows into [PLAN.md](PLAN.md) epics 11–16. Expect unsupported parameters to be **silently ignored** — a non-empty result is not proof a parameter was honoured; compare against a no-parameter call.

**Status — 16 Oct 2026 (second item run, 64 calls):** settled — 1, 2, 4, 5, 6, 8, 9, 10, 11, 16, 17, 21. Partial — 3 (boundary settled; count columns with 22), 7 (429 deliberately unprobed), 15 (both variants no-ops on the tested surface). Deferred to build time — 12, 13, 14, 18, 19, 22; 20 (trending) is out of the MVP. Full observations, counts, and evidence filenames live in [spike/RECORDING.md](spike/RECORDING.md); the quota ledger there reads 71 calls spent · 9,929 remaining.

**Original scope:**

1. **Brand + location** — which of `filter.location`, `signal.location`, `signal.location.query`, `filter.location.query`, or `filter.location.metro` actually narrows `urn:entity:brand` results (entity guide says none; use case says yes). Fallback: neighbour-entity signal plus a recorded locality.
2. **`filter.type` acceptance and scope** — `urn:tag` and `urn:demographics` against 403; `urn:entity:destination` despite the enum gap; `urn:entity:locality` partial behaviour; `urn:entity:videogame` spelling; and `filter.rating`'s real entity scope (DI-2, DI-19).
3. **Heatmap naming and boundary** — `urn:heatmap` vs `urn:entity:heatmap`; the accepted `output.heatmap.boundary` literals (docs mention the geohash default, "city or a neighborhood", and show `urn:entity:locality`; dimensions require `urn:geohash`) (DI-12, DI-18).
4. **`feature.explainability`** — accepted on brand and place calls? Per-result and aggregate shape, the ≥0.1 inclusion rule, and the warning path.
5. **Radius granularity** — does `filter.location.radius=400` genuinely filter at 400 m (settles the kill-rule-1 granularity question); confirm the omitted-radius padding rule and `0` strictness; check `filter.exclude.location.radius`.
6. **Units and geometry formats** — `/search` miles vs Insights metres; WKT longitude-first vs bare pair latitude-first; `/search` `filter.location` also accepts a Qloo UUID.
7. **429 behaviour and quota headroom** — rate-limit headers, reset timing, and the observed ceiling against the reported 10,000 requests/month.
8. **Data density** — `filter.popularity` and `filter.price_level` populated for retail brands in the demo cities; popularity present on `/search` results too.
9. **Per-candidate affinity probes** — `filter.results.entities=<candidate>` returns just those entities with their affinity; same for `filter.results.tags`.

**Added with the 16 Oct snapshot:**

10. **POST-only surface** — does a POST with a JSON body work at all on the hackathon host? Test `filter.exclude.entities.query`, `signal.interests.entities.query`, and a merged-locality array. If GET-only stands, DI-3's params are permanently off the table.
11. **Name-variant parameters** — call both spellings and see which changes results: the Resy triple (`filter.external.resy.*` vs `filter.properties.resy.rating.*` vs `filter.resy.rating_count.*`) (DI-4); `filter.price_range.from/.to` vs `.min/.max` (DI-5); `operator.filter.exclude.tags` vs `operator.exclude.tags` (DI-13); legacy `filter.entities` vs `filter.results.entities` (DI-14).
12. **`bias.quality` and `sort_by=quality`** — which weight strings are accepted (`very_low`…`very_high` vs `low/medium/high`, DI-6); confirm places without a quality score drop out and ordering is highest-first.
13. **`parents.types` and `filter.tag.types` semantics** — the schemas enumerate `urn:audience:*` values while the prose and Taste Analysis use `urn:entity:*` parents; find what `/v2/tags`, `/v2/tags/types`, and `urn:tag` insights actually accept (DI-8, DI-9).
14. **Signal weights** — numeric vs string forms on `signal.*.weight`; `{entity|tag, weight}` arrays on POST; `signal.interests.entities.include`; the `resolve_to` literal set (`place` / `self` / `urn:reference:brand` / `both`) (DI-16).
15. **`diversify.by` scope and metro filter** — city/metro diversification on place or brand calls (guide says tag-only), and `filter.location.metro` acceptance (DI-10, DI-11).
16. **External-ID round-trip on `/entities`** — resolve a known place by `external.michelin.ids` / `external.resy.ids`; useful for card enrichment without a Places key.
17. **Demographics details** — delta range and sign; mixing entities + tags; coarse vs fine age buckets; where audience IDs for `signal.demographics.audiences` come from now that the audiences routes are deprecated (DI-7, DI-20).
18. **Backfill dials** — `backfill.cross_domain.take` and `backfill.content_based.take` accepted (deep-dive-only docs)? Worth it only to suppress low-confidence filler.
19. **Compare endpoint** — `filter.subtype` and `model` behaviour, response shape, and the `take` cap.
20. **Trending** — weekly cadence, date-window limits, and whether sparse entities return rows or 404s.
21. **Location-page strays** — `filter.types` and `filter.distance.max` (DI-15); `/search` enum oddities (DI-17). Expect silent-ignore; note it and move on.
22. **Heatmap extras** — `heatmap.dimensions` + `filter.dimensions.hotel_class` / `.price_level` combinations, and the added count columns (DI-12).

## 6. Parameter catalogue

Everything the snapshot documents, in one place. **Guide** = [Entity Type Parameter Guide](https://docs.qloo.com/reference/available-parameters-by-entity-type); rows marked `[deep-dive]` appear only in the Insights OpenAPI spec and are unlisted in the guide; `[param-ref]` marks the [Parameter Reference](https://docs.qloo.com/reference/parameters) only. Two conventions:

- **Entity scope** shorthand: *all* = artist, book, brand, destination, movie, person, place, podcast, tv_show, videogame. Exceptions are stated per row. Per-type exact lists are in §7.
- Doc-vs-doc conflicts carry a `DI-n` ID, resolved by the matching §5 spike item.

### 6.1 Filters — *what kind of results you want*

| Parameter | Type / accepted values | Default | Entity scope | Karum use |
| --- | --- | --- | --- | --- |
| `filter.type` | string enum — see §1 and §7 | required | all | gates every call |
| `filter.address` | partial string match; comma-separated terms OK | — | place | disambiguates `/search` and saturation pins |
| `filter.content_rating` | `G, PG, PG-13, R, NC-17, TV-G, TV-PG, TV-14, TV-MA, TV-Y, TV-Y7, TV-Y7-FV, Not Rated, Unrated, Approved, Passed, X, GP, M, 13+, 16+, 18+` | — | movie, tv_show | — |
| `filter.date_of_birth.min` / `.max` | date `YYYY-MM-DD` | — | person | — |
| `filter.date_of_death.min` / `.max` | date `YYYY-MM-DD` | — | person | — |
| `filter.exclude.entities` | comma-separated entity IDs | — | all | keep neighbours out of results |
| `filter.exclude.entities.query` | **POST-only**; JSON array of `{name, address}` objects or strings; overwrites `filter.exclude.entities`; response path `query.entities.exclude`; 400 when nothing matches | — | all | unavailable on GET (DI-3) |
| `filter.exclude.tags` | comma-separated tag IDs | — | all | do-not-lease category suppression |
| `operator.filter.exclude.tags` | `union` or `intersection` | `union` | all | spelling variant DI-13 |
| `filter.exists` | `properties.image` or `properties.description` | — | [deep-dive] | keep only renderable cards |
| `filter.external.exists` | comma list from `resy`, `michelin`, `tablet` | — | all | quality proxy via Michelin / Resy presence |
| `operator.filter.external.exists` | `union` or `intersection` | `union` | all | — |
| `filter.external.resy.count.min` / `.max` | integer ≥ 0 | — | place | demand proxy; name variants DI-4 |
| `filter.external.resy.rating.min` / `.max` | number 0–5 (1–5 scale) | — | place | quality proxy |
| `filter.external.resy.party_size.min` / `.max` | integer ≥ 1 | — | place | capacity signal |
| `filter.external.tripadvisor.rating.min` / `.max` | number 0–5 | — | place | quality proxy |
| `filter.external.tripadvisor.rating.count.min` / `.max` | integer ≥ 0 | — | place | review volume |
| `filter.finale_year.min` / `.max` | integer | — | tv_show | — |
| `filter.gender` | string (schema example `female`; no enum) | — | person | — |
| `filter.geocode.name` | exact city/town match | — | destination, place | pin to a city |
| `filter.geocode.admin1_region` | exact match, usually state | — | destination, place | — |
| `filter.geocode.admin2_region` | exact match, county/borough | — | destination, place | — |
| `filter.geocode.country_code` | two-letter country code | — | destination, place | — |
| `filter.hotel_class.min` / `.max` | integer 1–5 | — | place | — |
| `filter.dimensions.hotel_class` | array of ints 1–5; requires `hotel_class` in `heatmap.dimensions`; adds `hotel_class_count_affinity_rank` and `hotel_class_count_affinity` | — | heatmap | — |
| `filter.hours` | one weekday: `monday` … `sunday` | — | place | open-on-day checks |
| `filter.latest_known_year.min` / `.max` | integer | — | tv_show | — |
| `filter.location` | lat/lon pair (**latitude first**), WKT (**longitude first**), or a locality UUID | — | destination, place; the use case adds brand (DI-2, §3.4) | the "fits here" gate |
| `filter.exclude.location` | WKT `POINT` / `POLYGON` / `MULTIPOLYGON` or locality UUID; `filter.exclude.location.radius` > 0 fuzzes the boundary | — | destination, place | — |
| `filter.location.query` | fuzzy locality name (GET: one string; POST: array merges shapes); single match returned as `query.locality.signal`; 400 when nothing matches | — | destination, place | locality-by-name with padding rules |
| `filter.exclude.location.query` | fuzzy exclusion by locality name(s); single match returned as `query.locality.exclude.signal`; 400 when nothing matches | — | destination, place | — |
| `filter.location.radius` | integer metres; max 800000; when omitted, pads by min(10% of diameter, ~2414 m); `0` = strictly inside | 15000 | destination, place | saturation radius — settles kill-rule 1 (spike 5) |
| `filter.exclude.location.radius` | integer metres; `0` strict, positive expands the exclusion | — | [deep-dive] | — |
| `filter.location.geohash` | geohash prefix match (pygeohash, precision 12) | — | destination, place | — |
| `filter.exclude.location.geohash` | geohash prefix exclusion | — | destination, place | — |
| `filter.location.metro` | exact metro-area name | — | [deep-dive] | brand-location probe candidate (DI-11, spike 15) |
| `filter.parents.types` | comma-separated parental entity types; schema enum lists `urn:audience:*` (quirk DI-8) | — | all | scope tags by parent entity |
| `filter.popularity.min` / `.max` | number 0–1 percentile | — | all | safe-vs-emerging split |
| `filter.price_level.min` / `.max` | integer 1–4 | — | place | rent-fit proxy |
| `filter.dimensions.price_level` | array of ints 1–4; requires `price_level` in `heatmap.dimensions`; adds `price_level_count_affinity_rank` and `price_level_count_affinity` | — | heatmap | — |
| `filter.price_range.from` / `.to` | integer 0–1,000,000 (hotel-style price); the parameter reference spells `.min` / `.max` (DI-5) | — | place | — |
| `filter.properties.business_rating.min` / `.max` | 1–5 | — | place | business-quality floor |
| `filter.publication_year.min` / `.max` | integer | — | book | — |
| `filter.rating.min` / `.max` | number 0–5; scope mismatch between docs (DI-19) | — | movie, tv_show per the parameter reference; the deep dive says point-of-interest | quality floor |
| `filter.references_brand` | comma-separated brand entity IDs, exact match | — | place | narrow to a specific brand's locations |
| `operator.filter.references_brand` | `union` or `intersection` | `union` | place | — |
| `filter.release_country` | comma-separated countries of original release | — | movie, tv_show | — |
| `operator.filter.release_country` | `union` or `intersection` | `union` | movie, tv_show | — |
| `filter.release_date.min` / `.max` | date `YYYY-MM-DD` | — | [deep-dive] (the guide lists `release_year` only) | — |
| `filter.release_year.min` / `.max` | integer | — | movie, tv_show | — |
| `filter.results.entities` | comma-separated entity IDs | — | all | per-candidate affinity probe (spike 9) |
| `filter.results.entities.query` | GET: single entity name; POST: array | — | all | resolve-then-probe |
| `filter.results.tags` | comma-separated tag IDs | — | [param-ref/deep-dive] | tag affinity probe |
| `filter.tags` | comma-separated tag IDs | — | all | category restriction |
| `operator.filter.tags` | `union` or `intersection` | `union` | all | — |
| `filter.tag.types` | comma-separated tag namespaces (e.g. `urn:tag:keyword:media`); description text is buggy (DI-9) | — | tag (Taste Analysis; not in the tag table) | block-taste namespace scoping |
| `filter.entities.query` | free-text term resolved to entity IDs | — | [deep-dive] | keyword-ish entity filtering |
| `filter.audience.types`, `filter.ids` | audience-type IDs and audience IDs | — | [param-ref] | prefer `signal.demographics.audiences` |

### 6.2 Signals and biases — *what to base recommendations on*

| Parameter | Type / accepted values | Default | Entity scope | Karum use |
| --- | --- | --- | --- | --- |
| `bias.trends` | `off`, `very_low`, `low`, `mid`, `medium`, `high`, `very_high` | `medium` | all | safe-vs-emerging weighting |
| `bias.content_based` | number 0–1 | 0.5 | [deep-dive] | metadata vs behavioural balance |
| `bias.quality` | positive number or weight string; weight sets differ (DI-6) | — | place | quality boost |
| `backfill.cross_domain.take` | integer 1–20 | 20 | [deep-dive] | cap appended filler |
| `backfill.content_based.take` | integer 1–10 | 10 | [deep-dive] | cap content-similarity filler |
| `signal.interests.entities` | comma-separated entity IDs (GET); `{entity, weight}` array (POST) | — | all (Required for destination) | the primary Karum signal |
| `signal.interests.entities.include` | comma-separated entity IDs | — | [deep-dive] | force entities into affinity scoring |
| `signal.interests.entities.query` | **POST-only**; `{name, address, resolve_to}` objects or strings; response path `query.entities.signal`; warnings `not_found` / `could_not_resolve_brand` | — | all | unavailable on GET (DI-3); `resolve_to` variants DI-16 |
| `signal.interests.entities.weight` | number ≥ 0 or weight string | — | all | signal strength |
| `signal.interests.tags` | comma-separated tag IDs (GET); `{tag, weight}` array (POST), weights > 0 and relative | — | all | constraint chips as taste input |
| `operator.signal.interests.tags` | `union` (highest-affinity tag scores) or `intersection` / empty (all tags merged) | empty → intersection | all | — |
| `signal.interests.tags.weight` | number ≥ 0 or weight string | — | all | tag weighting |
| `signal.demographics.age` | `24_and_younger`, `25_to_29`, `30_to_34`, `35_to_44`, `45_to_54`, `55_and_older`; the enum also carries coarse `35_and_younger`, `36_to_55`, `55_and_older` (DI-7) | — | all | audience skew input |
| `signal.demographics.gender` | `male` or `female` | — | all | audience skew input |
| `signal.demographics.audiences` | comma-separated audience IDs (from `/v2/audiences` — deprecated route, DI-20) | — | all | named-segment skew |
| `signal.demographics.age.weight` | number ≥ 0 or weight string | — | [deep-dive] | — |
| `signal.demographics.gender.weight` | number ≥ 0 or weight string | — | [deep-dive] | — |
| `signal.demographics.audiences.weight` | number ≥ 0 or weight string | — | all per guide | — |
| `signal.location` | WKT `POINT` / `POLYGON` (longitude first) or locality UUID; radius ignored for UUID and POLYGON | — | all | geo-weighted ranking |
| `signal.location.query` | fuzzy locality name | — | all | name-based geo signal; response carries the matched locality |
| `signal.location.radius` | integer metres, max 800000 | — | all | avoid — overrides density discovery |
| `signal.location.weight` | number ≥ 0 or weight string | — | [deep-dive] | — |

### 6.3 Output and pagination — *how results are shaped*

| Parameter | Type / accepted values | Default | Entity scope | Karum use |
| --- | --- | --- | --- | --- |
| `take` | integer 1–50 | 20 | all | result count (`/search`: exclusive max 200) |
| `page` | integer 1–100 | 1 | all | recommended pagination |
| `offset` | integer ≥ 0 | — | all | arbitrary skip |
| `sort_by` | `affinity`, `distance`, `rating`, `quality`; `distance` requires `filter.location`; `quality` is place-only and drops places without a score | `affinity` | place per guide; all per the deep-dive enum | rank control |
| `feature.explainability` | boolean | `false` | [deep-dive] | the evidence drawer's source (§3.8) |
| `output.heatmap.boundary` | heatmap boundary selector; literals unclear — docs mention a geohash default, "city or a neighborhood", and show `urn:entity:locality`; dimensions require `urn:geohash` (DI-12) | geohashes | heatmap | — |
| `heatmap.dimensions` | `quality`, `popularity`, `hotel_class`, `price_level`; adds `<dim>_affinity_rank` (0–1) and `<dim>_affinity` (percent rank); influences overall ranking | — | heatmap | richer overlay |
| `diversify.by` | `properties.geocode.city`, `properties.geocode.metro`, `subtype` (`subtype` applies to `urn:tag` only per the guide; city/metro general per the deep dive — DI-10) | — | guide: tag; deep dive: general | spread results across cities |
| `diversify.take` | integer ≥ 1 | — | same scope as `diversify.by` | max per group before paging |

## 7. Entity-type support matrix

Condensed from the [Entity Type Parameter Guide](https://docs.qloo.com/reference/available-parameters-by-entity-type). Names are exact. Where the guide's names differ from the deep-dive spec (Resy, `price_range`), the §9 ID is cited and the spike settles which resolves.

### 7.1 Baseline — artist, book, brand, movie, person, podcast, tv_show, videogame

- **Filters:** `filter.type` (required), `filter.exclude.entities`, `filter.exclude.tags`, `operator.exclude.tags`, `filter.external.exists`, `operator.filter.external.exists`, `filter.parents.types`, `filter.popularity.min` / `.max`, `filter.results.entities`, `filter.results.entities.query`, `filter.tags`, `operator.filter.tags`
- **Signals:** `bias.trends`, `signal.demographics.age`, `signal.demographics.audiences`, `signal.demographics.audiences.weight`, `signal.demographics.gender`, `signal.interests.entities`, `signal.interests.tags`
- **Output:** `offset`, `take`

### 7.2 Deltas on top of the baseline

| Type | Adds |
| --- | --- |
| artist | — |
| book | `filter.publication_year.min` / `.max` |
| brand | — (notably **no location family** — see §3.4, DI-2) |
| movie | `filter.content_rating`, `filter.release_year.min` / `.max`, `filter.release_country`, `operator.filter.release_country`, `filter.rating.min` / `.max` |
| person | `filter.date_of_birth.min` / `.max`, `filter.date_of_death.min` / `.max`, `filter.gender` |
| podcast | — |
| tv_show | `filter.content_rating`, `filter.finale_year.min` / `.max`, `filter.latest_known_year.min` / `.max`, `filter.release_year.min` / `.max`, `filter.release_country`, `operator.filter.release_country`, `filter.rating.min` / `.max` |
| videogame | — |

### 7.3 Destination (replaces the baseline)

- **Filters:** `filter.type` (required), `filter.exclude.entities`, `filter.external.exists`, `operator.filter.external.exists`, `filter.exclude.tags`, `operator.exclude.tags`, `filter.geocode.name`, `filter.geocode.admin1_region`, `filter.geocode.admin2_region`, `filter.geocode.country_code`, `filter.location`, `filter.location.radius`, `filter.location.geohash`, `filter.exclude.location.geohash`, `filter.parents.types`, `filter.popularity.min` / `.max`, `filter.results.entities`, `filter.results.entities.query`, `filter.tags`, `operator.filter.tags`
- **Signals:** `bias.trends`, `signal.demographics.age`, `signal.demographics.audiences`, `signal.demographics.audiences.weight`, `signal.demographics.gender`, **`signal.interests.entities` (Required)**, `signal.interests.tags`
- **Output:** `offset`, `take`
- The only full entity type where a signal is required. `urn:entity:destination` is absent from the Insights enum (DI-2).

### 7.4 Place (replaces the baseline)

- **Filters:** `filter.type` (required), `bias.quality`, `filter.address`, `filter.exclude.entities`, `filter.exclude.tags`, `operator.exclude.tags`, `filter.external.exists`, `operator.filter.external.exists`, `filter.external.tripadvisor.rating.count.min` / `.max`, `filter.external.tripadvisor.rating.min` / `.max`, geocode family (`name`, `admin1_region`, `admin2_region`, `country_code`), `filter.hotel_class.min` / `.max`, `filter.hours`, location family (`filter.location`, `filter.location.geohash`, `filter.exclude.location.geohash`, `filter.location.radius`), `filter.parents.types`, `filter.popularity.min` / `.max`, `filter.price_level.min` / `.max`, `filter.price_range.from` / `.to`, `filter.properties.business_rating.min` / `.max`, `filter.references_brand`, `filter.results.entities`, `filter.results.entities.query`, `filter.tags`, `operator.filter.tags`
- **Guide-only Resy names:** `filter.properties.resy.rating.min` / `.max`, `filter.resy.rating_count.min` / `.max`, `filter.resy.rating.party.min` / `.max` (DI-4)
- **Signals:** baseline set
- **Output:** `offset`, `take`, `sort_by`
- `bias.quality` and `sort_by=quality` apply only to places with a quality score.

### 7.5 Heatmap

- **Filters:** `filter.type` (required), `filter.location`, `filter.location.query`, `filter.location.radius`, `heatmap.dimensions`, `filter.dimensions.hotel_class`, `filter.dimensions.price_level`, `output.heatmap.boundary`
- **Signals:** `signal.demographics.age`, `signal.demographics.audiences`, `signal.demographics.gender`, `signal.interests.entities`, `signal.interests.tags`
- **Output:** `take`
- The guide marks signals optional, but the Heatmap use-case page requires a location plus at least one signal in practice. `heatmap.dimensions` applies only when `output.heatmap.boundary=urn:geohash` per the guide (DI-12).

### 7.6 Tag

- **Filters:** `filter.type` (required)
- **Output:** `diversify.by`, `diversify.take`, `offset`, `take`
- **Taste Analysis adds a requirement:** at least one of `signal.interests.entities`, `signal.interests.tags`, `signal.demographics.audiences`, `signal.location` / `signal.location.query`, `filter.tag.types`, `filter.parents.types`. Use `diversify.by=subtype` + `diversify.take` to cap results per tag subtype before paging.

### 7.7 Deprecated types

`urn:entity:actor`, `urn:entity:author`, `urn:entity:director` are deprecated — use `urn:entity:person` (the author table additionally carried `filter.publication_year.min` / `.max`). The legacy names remain searchable on `/search` only.

## 8. Response shapes

Every endpoint returns the same envelope: `success`, `duration` (ms), and `results` (plus a top-level `query` block on Insights calls where the docs show one). Responses cannot be field-filtered — trim `akas`, `short_descriptions`, and similar verbosity client-side. Snippets below are truncated doc samples.

### 8.1 Insights entity results — `/v2/insights` with an entity `filter.type`

```json
{
  "success": true,
  "results": {
    "entities": [
      {
        "name": "Queen & Slim",
        "entity_id": "9E2FD257-7E23-483A-8276-36FF51A5DD67",
        "type": "urn:entity",
        "subtype": "urn:entity:movie",
        "properties": {
          "release_year": 2019,
          "release_date": "2019-11-27",
          "description": "A couple's first date takes an unexpected turn…",
          "content_rating": "R",
          "duration": 132,
          "image": { "url": "https://…-420x-outside.jpg" },
          "akas": [ { "value": "Queen and Slim", "languages": ["fr", "en"] } ],
          "release_country": ["United States", "Canada"]
        }
      }
    ],
    "duration": 75
  }
}
```

Fields vary by subtype. With `feature.explainability=true`, each result carries `query.explainability` (normalized contributions, ≥0.1 always included) and a top-level aggregate exists — spike 4 confirms the exact shape. With `signal.location.query` / `filter.location.query`, a top-level `query.locality.signal` (or `.exclude.signal`) carries the matched locality entity.

### 8.2 Taste tags — `/v2/insights` with `filter.type=urn:tag`

```json
{
  "success": true,
  "results": {
    "tags": [
      {
        "tag_id": "urn:tag:keyword:media:cultural_clash",
        "name": "Cultural Clash",
        "types": ["urn:entity:tv_show", "urn:entity:movie"],
        "subtype": "urn:tag:keyword:media",
        "tag_value": "urn:tag:keyword:media:cultural_clash",
        "query": {}
      }
    ]
  },
  "duration": 25
}
```

### 8.3 Demographics — `/v2/insights` with `filter.type=urn:demographics`

```json
{
  "success": true,
  "results": {
    "demographics": [
      {
        "entity_id": "urn:tag:genre:media:action",
        "query": {
          "age": {
            "24_and_younger": 0,
            "25_to_29": 0.43,
            "30_to_34": 0.23,
            "45_to_54": -0.28,
            "55_and_older": -0.17
          },
          "gender": { "male": 0.08, "female": -0.08 }
        }
      }
    ]
  },
  "duration": 77
}
```

Positive = stronger-than-average alignment, negative = lower. One block per requested entity/tag signal.

### 8.4 Heatmap — `/v2/insights` with `filter.type=urn:heatmap`

```json
{
  "success": true,
  "results": {
    "heatmap": [
      {
        "location": { "latitude": 40.74005, "longitude": -73.87756, "geohash": "dr5ryb" },
        "query": { "affinity": 0.9992, "affinity_rank": 0.9960, "popularity": 0.5449 }
      }
    ]
  },
  "query": {
    "localities": {
      "filter": {
        "entity_id": "81E61924-6CEE-4AB4-93D3-282A5C784AB8",
        "name": "New York",
        "subtype": "urn:entity:locality",
        "popularity": 1,
        "disambiguation": "New York, New York, United States of America"
      }
    }
  },
  "duration": 75
}
```

With `heatmap.dimensions`, each cell adds `<dim>_affinity_rank` (0–1) and `<dim>_affinity` (percent rank); with `filter.dimensions.*`, it also adds `<dim>_count_affinity(_rank)` (spike 22). With `output.heatmap.boundary=urn:entity:locality` the container is `results.entities` instead of `results.heatmap`: locality rows (name, entity_id, location) carrying polygon geometry — observed 16 Oct, spike 3.

### 8.5 Search and entities-by-ID — `GET /search`, `GET /entities`

```json
{
  "success": true,
  "duration": 0.1,
  "results": [
    { "name": "…", "entity_id": "…", "type": "urn:entity", "subtype": "urn:entity:place", "properties": { "…": "…" } }
  ]
}
```

`/search` supports `sort_by=match|distance|popularity`. Misses return a 404-style body (no empty-success); 429 on rate limits.

### 8.6 Tags lookup — `GET /v2/tags`, `GET /v2/tags/types`

```json
{ "duration": 25, "success": true, "results": { "tags": [ { "tag_id": "…", "name": "…", "types": ["…"], "subtype": "…", "tag_value": "…" } ] } }
```

The tag-types response schema is not shown in the snapshot (spike 13).

### 8.7 Compare — `GET /v2/analysis/compare`

Returns the same envelope as `/search` — a `results` array of entities for the comparison. Both `a.` and `b.` signals are required; `filter.subtype` and `model` shape the analysis (spike 19).

### 8.8 Trending — `GET /v2/trending`

```json
{
  "success": true,
  "duration": 123,
  "results": {
    "trending": [
      {
        "date": "2025-01-03",
        "population_percentile": 85.2,
        "population_rank": 150,
        "population_rank_velocity": 5,
        "velocity_fold_change": 1.15,
        "population_percent_delta": 1.15
      }
    ]
  }
}
```

Weekly rows, delivered in descending date order.

## 9. Documentation inconsistencies register

Every conflict found in the 16 Oct 2026 snapshot, each mapped to the §5 spike item that settles it. When a row closes, replace the action with the observed answer and the date — this register is the honesty trail for "documented parameters only".

| ID | The conflict | Settled by |
| --- | --- | --- |
| DI-1 | OpenAPI specs list `https://api.qloo.com` ("Production Qloo API server") and some examples use `staging.api.qloo.com`; the hackathon guide says hackathon keys 401 there | Rule: use `hackathon.api.qloo.com` everywhere; smoke-check the prod host once and record the 401 |
| DI-2 | Insights `filter.type` enum omits `urn:tag`, `urn:demographics`, and `urn:entity:destination`, yet the use-case pages document the first two and the parameter reference tables the third; `locality` is partial; the enum spells `videogame` without an underscore | **Closed 16 Oct** — no 403s: `urn:tag`, `urn:demographics` and `urn:entity:destination` all returned data; `urn:entity:videogame` spelling confirmed; `urn:entity:locality` 400s unless signalled by locality entities (spike 2) |
| DI-3 | Some parameters are "POST only" (`filter.exclude.entities.query`, `signal.interests.entities.query`) and others accept arrays only via POST (merged localities, weight arrays); the hackathon surface is believed GET-only | **Closed 16 Oct** — POST exists: `POST /v2/insights` 200 with a JSON body; `signal.interests.entities.query` resolved server-side ("Qloo HQ" → "Sonder HQ", score 21.88) and the same body applied `filter.exclude.entities.query`; CORS advertises POST (spike 10) |
| DI-4 | Resy names in three spellings: deep dive `filter.external.resy.{count, rating, party_size}.min/max`; place guide `filter.properties.resy.rating.min/max`, `filter.resy.rating_count.min/max`, `filter.resy.rating.party.min/max` | **Closed 16 Oct** — deep-dive spelling wins: `filter.external.resy.rating.min` honoured (0 rows in Colaba — no Resy data); `filter.properties.resy.rating.min` and `filter.resy.rating_count.min` silently ignored (spike 11) |
| DI-5 | `filter.price_range.from` / `.to` (deep dive + place guide) vs `filter.price_range.min` / `.max` (parameter reference) | **Closed 16 Oct** — `.from` / `.to` honoured (result set changed); `.min` / `.max` silently ignored (spike 11) |
| DI-6 | `bias.quality` weight strings: `very_low`…`very_high` (deep dive) vs `low` / `medium` / `high` (parameter reference) | Spike 12 |
| DI-7 | Age buckets: the deep-dive enum carries both coarse (`35_and_younger`, `36_to_55`, `55_and_older`) and fine buckets; the parameter reference lists fine only; doc samples use fine | **Closed 16 Oct** — responses carry fine buckets only (`24_and_younger` … `55_and_older`), deltas within ±0.5 (spike 17) |
| DI-8 | `filter.parents.types` schema enum lists `urn:audience:*` values while the description says parental entity types (`urn:entity:place`); Taste Analysis uses `urn:entity:movie`, `urn:entity:tv_show` | Spike 13 |
| DI-9 | `filter.tag.types` description on the tags route talks about audience types; actual usage is tag namespaces (`urn:tag:keyword:media`) | Spike 13 |
| DI-10 | `diversify.by` city/metro described generally (deep dive + parameter reference) vs tag-only with `subtype` (entity guide) | **Partial 16 Oct** — `diversify.by=subtype` silently ignored on the brand call tested; the guide's tag-only note holds; tag-scoped use not probed (spike 15) |
| DI-11 | `filter.location.metro` appears only in the deep-dive parameter list, not in any per-entity table | **Closed 16 Oct** — byte-identical to baseline on a brand call: ignored (spike 1) |
| DI-12 | `output.heatmap.boundary`: deep dive says default geohashes, "city or a neighborhood", and shows `urn:entity:locality`; the entity guide requires `urn:geohash` for dimensions; count-column behaviour only in the deep dive | **Partial 16 Oct** — `urn:geohash` is a byte-identical no-op; `urn:entity:locality` accepted and switches the container to `entities`: locality rows with polygon geometry (8 rows; 41 with `filter.location.query=Mumbai`). Count columns remain with spike 22 (spike 3) |
| DI-13 | Exclude-tags operator: `operator.filter.exclude.tags` (deep dive) vs `operator.exclude.tags` (parameter reference + entity guide) | **Closed 16 Oct** — `filter.exclude.tags` honoured (include + exclude of the same tag → 0 rows); both operator spellings produced identical results — no observable difference; prefer `operator.exclude.tags` (spike 11) |
| DI-14 | Parameter reference lists legacy `filter.entities` (mapped from `filter.entity_ids`); the deep dive uses `filter.results.entities` | **Closed 16 Oct** — both work; `filter.entities` returns the entity plus `warnings: deprecated`; `filter.results.entities` is the current, clean spelling (spike 11) |
| DI-15 | `filter.types` and `filter.distance.max` appear only in the location use-case prose — absent from every schema | **Closed 16 Oct** — both silently ignored on `/search` (`filter.types=urn:entity:brand` left results as places; `filter.distance.max` identical to its control) (spike 21) |
| DI-16 | `resolve_to` literals: `place` / `brand` / `both` (deep-dive schema) vs `self` / `urn:reference:brand` / `both` (parameter-reference prose) | Spike 14 |
| DI-17 | `/search` `types` enum includes `urn:heatmap` and `urn:entity:audience`, and legacy names (`actor`, `album`, `author`, `director`, `locality`) exist for search only | **Closed 16 Oct (awareness)** — Karum searches `place` / `brand` only; the legacy enums have no impact (spike 21) |
| DI-18 | Heatmap `filter.type` spelling: `urn:heatmap` (current enum) vs `urn:entity:heatmap` (older material and entrant repos) | **Closed 16 Oct** — `urn:heatmap` is the only accepted spelling; `urn:entity:heatmap` → 400 "not supported for filter.type" (spike 3) |
| DI-19 | `filter.rating`: deep dive describes "Point of Interest", parameter reference scopes it to Movie / TV Show | **Closed 16 Oct** — `filter.rating.min=4.5` accepted and effective on place results (50 → 28 rows): not movie/TV-only (spike 2) |
| DI-20 | `/v2/audiences` and `/v2/audiences/types` are deprecated, yet `signal.demographics.audiences` says IDs come from that route | **Closed 16 Oct (out of scope)** — audiences routes deprecated; Karum does not use `signal.demographics.audiences`; demographics work via entity/tag signals and per-input profile rows (spike 17) |
| DI-21 | Location format: the docs describe `filter.location` as "a lat/lon pair, WKT, or a Qloo UUID" on both surfaces, but each surface accepts only one form | **Closed 16 Oct** — split by surface: `/search` takes the bare `lat,lon` pair only (WKT and UUID rejected: "must be in the form lat,lon"); Insights takes WKT `POINT(<lon> <lat>)` only (bare pair → "WKT format is invalid") (spike 6) |

