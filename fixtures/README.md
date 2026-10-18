# Fixture pack — redacted Qloo recordings for the four judge presets

This directory is the infra repo's share of the demo data: every Qloo response
the four presets replay in fixture mode, reduced to the fields Karum consumes,
and committed with the sha256 manifest CI verifies. Raw payloads stay local in
`spike/out/` (git-ignored). Public repositories carry only this pack — never
raw Qloo JSON ([QLOO_APIS.md](../QLOO_APIS.md) §1, [PLAN.md](../PLAN.md) §4).

## Layout

| Path | What it is |
| --- | --- |
| `presets/*.json` | The four locked preset payloads (the "fixture seeds"): ids, points, radii, category tags, skip-candidate ids, and the recordings each preset replays. |
| `qloo/<preset>/…` | Redacted recordings per preset: `search`, `insights` (doors, skip pools), `heatmap`, `locality`, `demographics`, `compare`. |
| `qloo/tags/…` | Tag catalogues (`bar`, `cafe`, `ceramics`, `gallery`) that produced the category URNs. |
| `qloo/misses/` | Recorded coverage misses, kept as honesty evidence (PLAN.md §40). |
| `manifest.json` | sha256 + byte size per file, with the source recording name. Generated. |
| `tools/redact.py` | The redactor: regenerates the pack and verifies it (`--verify`). |
| `tools/test_redact.py` | Unit tests for the row projections. |

## Envelope shape

Every `qloo/` file carries the same envelope:

```json
{
  "fixture_version": 1,
  "kind": "search | insights | heatmap | locality | tags | demographics | compare",
  "source": {
    "recording": "20261017-140127-resolve-brand-aesop.json",
    "recorded": "2026-10-17 14:01:27",
    "label": "resolve-brand-aesop",
    "status": 200,
    "request": "/v2/search?query=aesop&types=urn:entity:brand&take=5"
  },
  "note": "why this file exists (optional)",
  "warnings": [{ "type": "not_found", "signal.interests.entities": ["…"] }],
  "rows": [ … ]
}
```

`rows` holds only the consumed fields per kind:

- **search** — `entity_id`, `name`, `types`, `location {lat, lon}`,
  `geocode {city, name, metro, country, admin1_region}`, `disambiguation`.
- **insights** (doors and skip pools) — `entity_id`, `name`, `type`, `subtype`,
  `disambiguation`, `location`, `popularity`, `tags [{id, name, type, weight}]`,
  `query {affinity, distance, explainability {signal.interests.entities [{entity_id, score}]}}`,
  `properties {address, business_rating, good_for, hours, is_closed, phone, price_level, price_range, website, geocode}`.
- **heatmap** — `geohash`, `location {lat, lon}`, `affinity`, `affinity_rank`, `popularity`.
- **locality** — `entity_id`, `name`, `disambiguation`, `affinity`, `boundary` (polygon string).
- **tags** — `id` (URN), `name`, `type`.
- **demographics** — `entity_id`, `age {24_and_younger … 55_and_older}`, `gender {male, female}`.
- **compare** — `tag_id`, `name`, `type`, `subtype`, `entity_id`, `count`.

Dropped everywhere: images, long descriptions, review externals (Google,
Tripadvisor, Resy), keywords, disambiguation trees, and anything else the
services never read. The keep-lists in `tools/redact.py` **are** the redaction
contract — widen one only with a fresh recording.

## The four presets

| preset_id | Mode | Point (lat, lon) | Radius | Category tag | Seed |
| --- | --- | --- | --- | --- | --- |
| `austin-wholesale` | wholesale | 30.2672, -97.7431 | 8 km | `urn:tag:genre:place:restaurant:bar` | Aesop, Ilegal Mezcal, Khruangbin |
| `brooklyn-flagship` | flagship | 40.7172, -73.9566 | 8 km doors / 10 km heatmap | `urn:tag:genre:place:restaurant:cafe` | Muji, Choplet, BKLYN CLAY, Kettl Tea |
| `brooklyn-collab` | collab | 40.7172, -73.9566 | 8 km | `urn:tag:genre:place:art_gallery` (+ ceramics dud) | same as flagship |
| `mumbai-colaba-wholesale` | wholesale | 18.93, 72.83 | 8 km | `urn:tag:genre:place:restaurant:cafe` | Mary Lodge by Subko, Blue Tokai Bandra, Blue Tokai Versova |

Each preset file carries `skip_candidates` (batch-scored naive-list venues),
`notes` (the traps the demo must respect), and `recordings` (the exact files
fixture mode replays). Seed counts respect the four-entity cap (PLAN.md §26);
the Brooklyn recording session used a fifth signal (Kinfolk, now an alternate)
and the divergence is documented in the preset notes.

## Regenerating and verifying

```sh
python fixtures/tools/redact.py            # needs spike/out/ recordings (local only)
python fixtures/tools/redact.py --verify   # CI-safe: hashes + schemas, no recordings
python -m unittest discover -s fixtures/tools -p "test_*.py"
```

`make redact-fixtures`, `make check-fixtures`, and `make test-fixtures` wrap
these. CI runs the verify + tests on every change under `fixtures/**`.

## Provenance

Recorded 16–18 Oct 2026 from the Qloo hackathon host; the call-by-call log,
quota ledger, and the traps each note refers to live in
[spike/RECORDING.md](../spike/RECORDING.md). The pack is deterministic: the
redactor skips byte-identical writes, and the manifest pins every output.
