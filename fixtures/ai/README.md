# AI fixture pack — the recorded model replay for service-ai

This directory is the AI half of the demo data: the model answers `karum-service-ai`
replays in fixture mode (`AI_MODE=fixture`), so a demo run needs **no Gemini
credential, no network call, and no model quota** (PLAN.md §4, §18).

## Provenance

The recordings are **derived from `contract/testdata/campaign/`** — the
hand-written Austin-wholesale campaign fixtures this repository already ships
and the contract round-trip already exercises — and **not** captured from a
live model session: the model quota was exhausted when the pack was built
(K-01), and inventing new answers would be worse than replaying the answers
the repository stands behind. `fixtures/tools/build_ai_pack.py` is the
derivation, and it applies exactly two adjustments:

- the audit's incumbent source title is widened to carry the incumbent's own
  name; §16 keeps an incumbent only when a grounding source or the Qloo
  payload names it, and the contract fixture's generic `Whisler's — Menu`
  title cannot carry `Del Maguey Single Village Mezcal` — a live recording
  would have returned a title that does;
- the draft's `modeParagraph` is cleared, matching wholesale mode.

Everything else — the script, the battlecard, the SKU, the shelf findings,
the menu summaries, the baseline text — is the contract fixture's content.

When model quota returns (K-01), re-record against the live path and replace
the envelopes; the manifest's key rule and the service's replay path do not
change.

## Layout

| Path | What it is |
| --- | --- |
| `manifest.json` | The index: one entry per recording with its RPC method, its file, its request key, a representative request, and the summary `match` spec. |
| `audit-menu-austin-whislers.json` | The menu audit for the Austin wholesale shortlist (Whisler's, Here Nor There). |
| `draft-door-pitch-austin-whislers.json` | The Whisler's pitch: script, battlecard, recommended SKU. |
| `llm-only-baseline-austin-ilegal.json` | The ungrounded generic-LLM counterfactual for Ilegal Mezcal in Austin. |

Envelope shape (read by `karum_service_ai.vertex.fixtures`):

```json
{
  "fixture_version": 1,
  "source": { "recording": "contract/testdata/campaign/audit.json", "derived": "2026-10-21", "label": "…", "note": "…" },
  "response": { … the RPC's JSON response … }
}
```

Manifest keys are computed exactly as the service computes them
(`method:<sha256 of the canonical request payload, first 16 hex>`) and the
service verifies every declared key on load, so a drifted manifest fails
loudly in the AI test suite rather than replaying the wrong answer.

## How a request is matched

The service looks up the exact request key first. A live run's request differs
in the ids the recording cannot know (the door ids the taste replay issued,
the run's evidence set), so the recording's `match` spec — a small set of
summary fields (`city`, `door`, `brand`) — answers a request it fully
describes, but only when **exactly one** recording of that method matches.
Two candidates mean the request cannot be answered by replay, and a guess is
worse than a miss: the miss surfaces as a typed upstream error and the run
degrades visibly.

## Coverage and known gaps

- **Austin wholesale only.** Brooklyn flagship/collab and Mumbai Colaba have
  no recordings; their audits and drafts miss and degrade until recorded.
- The audit recording answers with the two doors the contract fixtures
  cover; any further door in the shortlist keeps its Qloo row and lands
  shelf-unknown.
- The pitch cites `ev-0001`/`ev-0003`/`ev-0004` — which the Austin replay's
  evidence set carries — and `ev-0006`, which it does not, so the citation
  filter drops that talking point on replay exactly as it would on a live
  call (§17). This is the filter working on recorded content, not a pack
  defect.

## Verifying

```sh
python fixtures/tools/build_ai_pack.py --check   # committed pack == the tool's derivation
```

and, with the sibling checkout present, the AI service's own suite:

```sh
cd ../karum-service-ai && uv run pytest tests/test_fixtures.py
```

The service-level tests load this pack through the same `FixturePack` the
replay path uses and assert the Austin audit, pitch, and baseline come back
schema-valid, with the recorded incumbent kept and the recorded script's
sentences surviving the citation filter.
