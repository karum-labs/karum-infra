# Spike recording sheet — QLOO_APIS.md §5

One row per checklist item. When an item settles:

1. fill the row here (observed status/count, one-line verdict);
2. tick the item in [QLOO_APIS.md](../QLOO_APIS.md) §5;
3. close the matching §9 row with the observed answer and the date;
4. carry the result into the PLAN epic that depends on it.

Raw responses live in `spike/out/` (git-ignored) — cite the file name in notes, but
redact before promoting anything into the fixture pack. The key never leaves
`$QLOO_API_KEY`.

| # | Item (QLOO_APIS.md §5) | Probe | Observed (status, count, behaviour) | Verdict | §9 rows | Date |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Brand + location — which location parameter narrows brand results | `brand-location --lat .. --lon .. --city ..` | | | — | |
| 2 | `filter.type` acceptance and scope; `filter.rating` scope | `filter-type` + `raw` for `filter.rating` | | | DI-2, DI-19 | |
| 3 | Heatmap naming and boundary | `heatmap --lat .. --lon ..` | | | DI-12, DI-18 | |
| 4 | `feature.explainability` shape and warning path | `explainability` | | | — | |
| 5 | Radius granularity — 400 m filter, padding, 0 strictness, `filter.exclude.location.radius` | `radius --lat .. --lon ..` | | | — | |
| 6 | Units and geometry — miles vs metres, WKT order, UUID `filter.location` | `radius` + `resolve` | | | — | |
| 7 | 429 behaviour and quota headroom — headers, reset timing vs 10,000/month | any call; inspect `out/*.meta.json` headers | 16 Oct: `X-Second-RateLimit-Limit: 5` (req/s), `X-Month-RateLimit-Limit: 10000`, `X-Month-RateLimit-Reset` ≈ 2,592,000 s counting down in real time (rolling ~30-day window, not a calendar-month reset) | Partial — headers and reset window observed; 429 deliberately unprobed | — | 16 Oct 2026 |
| 8 | Data density — `filter.popularity`, `filter.price_level`, `/search` popularity | `resolve` + `raw` with both filters | 16 Oct: brand `popularity` populated (0.933 on the top Colaba rec); `price_level` empty on that row; Mumbai and Bangalore retail places resolve; brand properties rich (`founded_year`, price bands, `key_markets`) | Partial — the full demo-city pass is still owed | — | 16 Oct 2026 |
| 9 | Per-candidate affinity — `filter.results.entities`, `filter.results.tags` | `variants --entity <uuid>` | | | — | |
| 10 | POST-only surface | `post` | | | DI-3 | |
| 11 | Name-variant parameters — Resy triple, `price_range`, exclude operators, legacy `filter.entities` | `variants --entity <uuid> --tag <urn>` | | | DI-4, DI-5, DI-13, DI-14 | |
| 12 | `bias.quality` / `sort_by=quality` weight strings | `raw "/v2/insights?...&bias.quality=high..."` | | | DI-6 | |
| 13 | `parents.types` / `filter.tag.types` semantics | `raw` on `/v2/tags?...` and `/v2/tags/types` | | | DI-8, DI-9 | |
| 14 | Signal weights — numeric vs string, arrays, `include`, `resolve_to` literals | `raw` with `signal.interests.entities.weight=high` | | | DI-16 | |
| 15 | `diversify.by` scope and `filter.location.metro` | `brand-location --city ..` + `raw` with `diversify.by=subtype` | | | DI-10, DI-11 | |
| 16 | External-ID round trip on `/entities` | `entities --ids .. --resy-id ..` | | | — | |
| 17 | Demographics details — delta sign/range, buckets, audience ids | `filter-type` (demographics) + `raw` | | | DI-7, DI-20 | |
| 18 | Backfill dials — `backfill.cross_domain.take`, `backfill.content_based.take` | `raw` with both dials | | | — | |
| 19 | Compare endpoint — `filter.subtype`, `model`, shape, `take` cap | `raw "/v2/analysis/compare?...a./b. signals"` | | | — | |
| 20 | Trending — cadence, date-window limits, sparse entities | `raw "/v2/trending?...&filter.start_date=..&filter.end_date=.."` | | | — | |
| 21 | Location-page strays — `filter.types`, `filter.distance.max`, `/search` enums | `raw` paired calls + baseline | | | DI-15, DI-17 | |
| 22 | Heatmap extras — `heatmap.dimensions`, `filter.dimensions.hotel_class/.price_level` | `raw` with `heatmap.dimensions=popularity` | | | DI-12 | |

## Summary log

- **Calls spent this session:** 7 (key probe 1 · Mumbai and Bangalore resolves 3 · Leopold Cafe exact 1 · brands 2 · affinity 1)
- **Calls spent total (quota ledger):** 7 — `X-Month-RateLimit-Remaining: 9993` after the last call
- **Items settled:** 0 / 22 (items 7 and 8 carry partial observations)
- **Blockers found:** none

## Coverage probe — India (16 Oct 2026)

Side question, outside the 22 items: are Indian locations available? Seven calls.

- **Places: yes.** `/search` around Mumbai (Colaba / Kala Ghoda: Ground Reality Tours, Booster store, SAMSONITE, ROYAL BUTTON) and Bangalore (Indiranagar: The Mad Teapot Cafe, Glens Bakehouse, Gokyo Outdoor Clothing & Gear, Just Bake, The Cupcake Company) returns real venues. Exact-name search finds "Leopold Cafe" → `68A744F0-1CE7-4C73-9A60-80C7A5713F72`.
- **Brands: mixed.** "Café Coffee Day" resolves (`B6DA90E2-E073-4CE1-83CC-678F089C92EC`); "Amul" returns 0 — brand coverage is thinner than place coverage; record misses honestly.
- **Core flow: works.** A brand-affinity call signalled by the Colaba block (Leopold Cafe plus three block stores) returned 20 brands, India-native fashion labels on top (The Label Life, AND, Shyamal & Bhumika, House of Masaba, Ritu Kumar, Tarun Tahiliani…), `popularity` populated (0.933 on the top record).
- **Trap observed:** with `sort_by=distance` the name query behaves as "nearest venues" rather than a name match — use the default match sort to resolve a named entity.
- Evidence: raw payloads in `spike/out/` (local-only; redact before any fixture use). Not promoted to PRODUCT.md or PLAN epic 10 — demo-city choice stays a product decision.
