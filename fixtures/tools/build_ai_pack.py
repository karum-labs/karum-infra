"""Build the AI fixture pack from the hand-written contract campaign fixtures.

The pack lives in ``fixtures/ai/`` and answers service-ai's fixture-mode
replay (PLAN.md §4, §18). It is derived from
``contract/testdata/campaign/{audit,pitch,baseline}.json`` — the hand-written
Austin-wholesale fixtures the contract round-trip already ships — and not from
a live model session: the model quota was exhausted when this pack was built
(K-01), and inventing new answers would be worse than replaying the ones the
repository already stands behind.

Two adjustments are applied, and only these two:

- the audit's incumbent source title is widened to carry the incumbent's own
  name. §16 keeps an incumbent only when a grounding source or the Qloo
  payload names it, and the contract fixture's generic ``Whisler's — Menu``
  title cannot carry ``Del Maguey Single Village Mezcal``; a live recording
  would have returned a title that does.
- the draft's ``modeParagraph`` is cleared, matching wholesale mode (the
  service clears it on every path anyway).

Everything else — the script, the battlecard, the SKU, the shelf findings,
the menu summaries, the baseline text — is byte-for-byte the contract
fixture's content.

The manifest keys are computed exactly as
:func:`karum_service_ai.vertex.fixtures.request_key` computes them; the
service validates every declared key on load, so drift fails loudly in its
test suite.

Run ``python fixtures/tools/build_ai_pack.py`` to (re)write the pack, and
``python fixtures/tools/build_ai_pack.py --check`` to verify the committed
files match (CI-safe; see the fixtures README).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

#: Repository root (…/karum-infra). The tool sits in ``fixtures/tools/``.
ROOT = Path(__file__).resolve().parents[2]

#: Where the pack is written.
PACK_DIR = ROOT / "fixtures" / "ai"

#: The hand-written campaign fixtures the pack derives from.
CONTRACT_DIR = ROOT / "contract" / "testdata" / "campaign"

#: Schema version carried by the manifest and every envelope. Mirrors
#: ``karum_service_ai.vertex.fixtures.FIXTURE_VERSION``.
FIXTURE_VERSION = 1


def canonical_payload(payload: dict[str, Any]) -> str:
    """The stable JSON rendering used for the request key.

    Mirrors :func:`karum_service_ai.vertex.fixtures.canonical_payload`; the
    service re-computes every key on load and rejects a drifted manifest.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def request_key(method: str, payload: dict[str, Any]) -> str:
    """The deterministic key of one model call: method plus payload digest."""
    digest = hashlib.sha256(canonical_payload(payload).encode("utf-8")).hexdigest()
    return f"{method}:{digest[:16]}"


def _read_contract(name: str) -> dict[str, Any]:
    path = CONTRACT_DIR / name
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit(f"{path} is not an object")
    return document


def audit_response() -> dict[str, Any]:
    """The contract audit, with the incumbent source widened to name it (§16)."""
    response = _read_contract("audit.json")
    incumbent = response["results"][0]["incumbents"][0]
    incumbent["sources"][0]["title"] = (
        "Whisler's menu — Del Maguey Single Village Mezcal"
    )
    return response


def draft_response() -> dict[str, Any]:
    """The contract pitch; wholesale mode carries no mode paragraph."""
    response = _read_contract("pitch.json")
    response["modeParagraph"] = ""
    return response


def baseline_response() -> dict[str, Any]:
    """The contract generic-LLM baseline, unchanged."""
    return _read_contract("baseline.json")


#: One entry per recorded RPC. ``request`` is the representative request the
#: recording is filed under (bookkeeping and the key); ``match`` is the
#: summary the replay path consults when a live request differs in the ids a
#: recording cannot know (see karum_service_ai.vertex.transport.summarize).
ENTRIES: list[dict[str, Any]] = [
    {
        "id": "audit-menu-austin-whislers",
        "method": "audit_menu",
        "file": "audit-menu-austin-whislers.json",
        "source": "audit.json",
        "request": {
            "mode": "wholesale",
            "targets": [
                {
                    "door": {
                        "id": "1F0E9D8C-7B6A-4593-8C2D-1E0F2A3B4C10",
                        "type": "urn:entity:place",
                        "name": "Whisler's",
                        "city": "Austin",
                    }
                },
                {
                    "door": {
                        "id": "2A1B0C3D-4E5F-4A6B-9C8D-7E6F5A4B3C20",
                        "type": "urn:entity:place",
                        "name": "Here Nor There",
                        "city": "Austin",
                    }
                },
            ],
        },
        "match": {"city": "Austin", "door": "Whisler's"},
        "note": (
            "The Austin wholesale shortlist's rank-1 door. The recording "
            "answers with the two doors the contract fixtures cover; any "
            "further door keeps its Qloo row and lands shelf-unknown."
        ),
    },
    {
        "id": "draft-door-pitch-austin-whislers",
        "method": "draft_door_pitch",
        "file": "draft-door-pitch-austin-whislers.json",
        "source": "pitch.json",
        "request": {
            "brand": {"name": "Ilegal Mezcal"},
            "city": "Austin",
            "mode": "wholesale",
            "door": {"audit": {"door": {"name": "Whisler's"}}},
        },
        "match": {"city": "Austin", "brand": "Ilegal Mezcal", "door": "Whisler's"},
        "note": (
            "The demo pitch. It cites ev-0001/ev-0003/ev-0004, which the "
            "Austin replay's evidence set carries, and ev-0006, which it does "
            "not — so the citation filter drops that talking point on replay, "
            "exactly as it would on a live call (§17)."
        ),
    },
    {
        "id": "llm-only-baseline-austin-ilegal",
        "method": "llm_only_baseline",
        "file": "llm-only-baseline-austin-ilegal.json",
        "source": "baseline.json",
        "request": {
            "brand": {"name": "Ilegal Mezcal"},
            "city": "Austin",
            "mode": "wholesale",
        },
        "match": {"city": "Austin", "brand": "Ilegal Mezcal"},
        "note": ("The ungrounded counterfactual; its venue names source no preset run."),
    },
]

_RESponses = {
    "audit.json": audit_response,
    "pitch.json": draft_response,
    "baseline.json": baseline_response,
}


def _envelope(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture_version": FIXTURE_VERSION,
        "source": {
            "recording": f"contract/testdata/campaign/{entry['source']}",
            "derived": "2026-10-21",
            "label": entry["id"],
            "note": entry["note"],
        },
        "response": _RESponses[entry["source"]](),
    }


def manifest() -> dict[str, Any]:
    entries = []
    for entry in ENTRIES:
        request = entry["request"]
        entries.append(
            {
                "id": entry["id"],
                "method": entry["method"],
                "file": entry["file"],
                "key": request_key(entry["method"], request),
                "request": request,
                "match": entry["match"],
                "note": entry["note"],
            }
        )
    return {
        "fixture_version": FIXTURE_VERSION,
        "recorded": "2026-10-21",
        "note": (
            "Derived from contract/testdata/campaign (hand-written fixtures), "
            "not a live model session: the model quota was exhausted when the "
            "pack was built (K-01). Replace with real recordings when quota "
            "returns; keep the manifest's key rule."
        ),
        "entries": entries,
    }


def _render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def planned_files() -> dict[Path, str]:
    files = {PACK_DIR / "manifest.json": _render(manifest())}
    for entry in ENTRIES:
        files[PACK_DIR / entry["file"]] = _render(_envelope(entry))
    return files


def write() -> None:
    for path, text in planned_files().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")


def check() -> int:
    drift = 0
    for path, text in planned_files().items():
        if not path.is_file():
            print(f"missing {path.relative_to(ROOT)}", file=sys.stderr)
            drift += 1
            continue
        if path.read_text(encoding="utf-8") != text:
            print(f"drifted {path.relative_to(ROOT)}", file=sys.stderr)
            drift += 1
    if drift:
        print(
            "the AI pack does not match what the tool derives; run "
            "`python fixtures/tools/build_ai_pack.py`",
            file=sys.stderr,
        )
        return 1
    print(f"AI pack matches ({len(planned_files())} files)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed pack instead of rewriting it",
    )
    args = parser.parse_args()
    if args.check:
        return check()
    write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
