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
| 7 | 429 behaviour and quota headroom — headers, reset timing vs 10,000/month | any call; inspect `out/*.meta.json` headers | | | — | |
| 8 | Data density — `filter.popularity`, `filter.price_level`, `/search` popularity | `resolve` + `raw` with both filters | | | — | |
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

- **Calls spent this session:** —
- **Calls spent total (quota ledger):** —
- **Items settled:** 0 / 22
- **Blockers found:** —
