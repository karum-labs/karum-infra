# Qloo spike runner — PLAN epic 9

`run_spike.py` works through the [QLOO_APIS.md](../QLOO_APIS.md) §5 checklist against
`https://hackathon.api.qloo.com`. Stdlib-only Python 3.13 — no dependencies. The
17 Oct extension commands (`brand-doors`, `skip-pool`) verify the brand→place
direction and the Doors-to-Skip mechanism (see the extension section of
[RECORDING.md](RECORDING.md)).

## Safety rules

- **The key lives in `$QLOO_API_KEY` only.** Never in a file, never in git — the script
  reads it from the environment and never prints or saves it.
- **The only host the script calls is `https://hackathon.api.qloo.com`** (plus the
  opt-in DI-1 production-host check, which is expected to return 401).
- **Every raw response is saved to `spike/out/` (git-ignored).** Raw Qloo JSON never
  gets committed: redact before promoting anything into the fixture pack.
- **Unsupported parameters are silently ignored.** The script always prints a
  no-parameter baseline next to each variant, so a no-op is visible as an unchanged
  count and unchanged top names.

## Setup

The runner reads the key from `$QLOO_API_KEY`; if that is unset it falls back to
`TASTE_QLOO_API_KEY` (or `QLOO_API_KEY`) in the git-ignored `karum-infra/.env`.
With `.env` in place:

```powershell
python spike/run_spike.py key
```

Or set the env var explicitly for one session (PowerShell
`$env:QLOO_API_KEY="..."`, bash `export QLOO_API_KEY=...`). The key is never
printed, saved, or committed.

`raw`-only escape hatch — no `spike/`, plain inline call:

```powershell
curl.exe -s "https://hackathon.api.qloo.com/" -H "X-Api-Key: $env:QLOO_API_KEY"
```

## Run order

1. `key` — liveness of the hackathon key. Add `--check-prod-host` once to record the
   DI-1 401 from `api.qloo.com` — **done 16 Oct: 401 confirmed**.
2. `resolve` — turn a few real places in a dense retail block into entity ids
   (writes `state.json`; every later command reads it). `/search` takes miles and a
   latitude-first bare pair.
3. The gate items: `brand-location`, `filter-type`, `explainability`, `radius`,
   `variants`, `entities`, `post`. These settle spike items 1, 2, 4–8, 10, 11 —
   **all run 16 Oct, verdicts in [RECORDING.md](RECORDING.md)**.
4. Deferred tier: `heatmap` (item 3) and `entities --resy-id` (item 16) ran 16 Oct,
   then the feature-gated items 12–22 through `raw` — **all run 16 Oct; every item now
   carries a verdict** (item 7's 429 deliberately unprobed).
5. Extension (17 Oct): `brand-doors` proves the brand→place direction (baseline,
   place-signal control, take-50 distribution, optional mixed tag signal) and
   `skip-pool` calibrates the skip floor (ranked set vs a candidate batch) —
   **both verified 17 Oct**, 21 calls.

Record every answer in [RECORDING.md](RECORDING.md), then tick the item in
QLOO_APIS.md §5, close the matching §9 row with the observed answer and a date, and
let the result flow into the PLAN epic that depends on it.

## Commands

| Command | Spike item(s) | What it does |
| --- | --- | --- |
| `key [--check-prod-host]` | — | `GET /` liveness; optional DI-1 prod-host 401 check |
| `resolve --name X [--name Y] [--type place|brand|artist] [--lat .. --lon ..]` | 6, 8 | `/search` name → entity id; saves to `state.json`; prints each candidate's geocode city — check it for chains and common names |
| `brand-location [--ids a,b] [--lat .. --lon ..] [--city C]` | 1, 15 | Baseline brand call + each location variant, side by side |
| `filter-type` | 2 | `urn:tag`, `urn:demographics`, `urn:entity:destination`, `urn:entity:locality`, `urn:entity:videogame` |
| `explainability` | 4 | `feature.explainability=true` on brand and place calls; reports shape |
| `radius [--lat .. --lon ..] [--tag urn]` | 5, 6 | Default vs 400 m vs 0 vs 20 km; computes max distance when coordinates are present |
| `variants --entity <uuid> [--tag urn] [--lat .. --lon ..] [--radius N] [--skip-brand]` | 9, 11 | Resy triple, `price_range` from/to vs min/max, exclude operators, legacy `filter.entities`; place probes need `--radius` (a WKT point without one returns 0 rows) |
| `entities [--ids a,b] [--resy-id <id>]` | 16 | `/entities` by id and `external.resy.ids` round trip |
| `post` | 10 | One GET→POST attempt with a JSON body |
| `heatmap [--lat .. --lon ..] [--tag urn]` | 3, 22 | `urn:heatmap` default boundary vs `urn:geohash` |
| `brand-doors [--brands a,b] [--control-ids a,b] --lat .. --lon .. [--radius M] [--tag urn]` | ext. R1 | Brand/mixed seed ranking `urn:entity:place` rows (the ScoutDoors direction): baseline + place-signal control + take-50 distribution + optional tag signal; prints subtype mix, affinity quantiles, overlap |
| `skip-pool [--seeds a,b] --candidates a,b --lat .. --lon .. [--radius M] [--tag urn]` | ext. R2 | Ranks the seed (take 50) then scores the candidate venues in one `filter.results.entities` batch; prints each candidate's affinity, percentile vs the ranked set, and the relative floor |
| `raw "/path?params" [--post <json> / --post-file <path>]` | 12–23 | Anything else (POST bodies; `--post-file` is quoting-safe on Windows); still saved and summarized |

Every call writes `<stamp>-<label>.json` plus `<stamp>-<label>.meta.json` (status,
duration, and all response headers — that is where item 7's rate-limit headers show
up) into `spike/out/`.

## Notes

- `403` bodies are findings, not failures — `urn:tag` / `urn:demographics` against 403
  is exactly what spike 2 checks (DI-2).
- Insights `filter.location.radius` is **metres**; `/search` `filter.radius` is
  **miles**. WKT is longitude-first (`POINT(lon lat)`); the `/search` bare pair is
  latitude-first.
- **Format split (DI-21):** `/search` takes the bare `lat,lon` pair only — WKT and
  Qloo UUIDs are rejected. Insights takes WKT `POINT(lon lat)` only — a bare pair
  400s. A WKT point **without** `filter.location.radius` returns 0 results, and
  `radius=0` is the ~15 km default, not strict containment.
- All observed traps and verdicts, with counts, are in [RECORDING.md](RECORDING.md) —
  read it before adding probes.
- The script never bursts calls to watch a 429. If a rate-limit response shows up,
  record the headers and the reset timing by hand (item 7) — whether the quota resets
  before judging (Nov 2–16) matters.
- Quota: 10,000 requests/month. The full spike used 123 calls, the 17 Oct extension
  21 more (144 total; 9,856 remaining on 17 Oct; the DI-1 prod-host 401 is not metered) —
  keep it that way: baseline-paired probes only.
- **Affinity bands shift with seed type** (brand-seeded sets sat near 0.85, place-seeded
  near 0.97 on 17 Oct): score percentiles within the returned set and cut against the
  relative floor `skip-pool` prints — no fixed raw threshold (0.45 retired).
- **`filter.tags=<category>` keeps door lists door-shaped** — unfiltered brand-seeded
  rankings surface landmarks and retail instead of venues (17 Oct, trap 15).
- **Validated vs silently ignored (16 Oct):** some parameters reject bad input loudly
  (`bias.quality=bogus`, `include=<uuid>`, bad `resolve_to` → 400 with the reason) while
  others no-op byte-identically (`backfill.*` dials). New traps 8–13 in RECORDING.md:
  `include` is boolean (DI-23); `resolve_to` accepts `urn:reference:brand` / `both` only
  (DI-16); compare returns `{tags, a, b, matchEntities}` (DI-22); trending windows under
  ~6 months are empty.
