#!/usr/bin/env python3
"""The Python half of the stub contract test (PLAN.md §1.4).

Reads the Go-emitted binaries (``<name>.bin``) that ``contract/roundtrip
emit`` produced from the hand-written campaign fixtures, parses each one with
the generated Python stubs, asserts a handful of semantic values per message,
then re-serializes to ``<name>.py.bin`` so the Go verifier can prove semantic
equality both ways.

The script never reads the JSON fixtures: Python only ever sees the wire
format, which is the point of the exercise.

Usage:
    python contract/pyrelay/roundtrip.py contract/testdata/campaign contract/.out

Requires protobuf == 7.36.2 (contract/pyrelay/requirements.txt), matching the
pinned buf.build/protocolbuffers/python:v36.2 generator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "gen" / "python"))

try:
    from karum.common.v1 import common_pb2  # noqa: F401  (registers the dependency package)
    from karum.taste.v1 import taste_pb2
    from karum.agent.v1 import agent_pb2
except ModuleNotFoundError as exc:  # pragma: no cover - bootstrap hint
    sys.exit(f"python: cannot import the generated stubs ({exc}); run `make generate` first")


def assert_seed(msg) -> str:
    assert len(msg.candidates) == 3, f"expected 3 seed candidates, got {len(msg.candidates)}"
    assert msg.candidates[0].entity.name == "Ilegal Mezcal"
    assert msg.candidates[0].entity.type == "urn:entity:brand"
    assert not msg.unresolved
    assert len(msg.evidence) == 2
    return f"{len(msg.candidates)} candidates, confidence {msg.confidence:.2f}"


def assert_scout(msg) -> str:
    assert len(msg.doors) == 3, f"expected 3 doors, got {len(msg.doors)}"
    assert len(msg.skip_list) == 2
    assert len(msg.evidence) == 4
    door = msg.doors[0]
    assert door.rank == 1
    assert abs(door.affinity.raw_value - 0.8655) < 1e-9
    assert door.affinity.value == 1.0
    assert door.shared_tags[0].urn == "urn:tag:genre:place:restaurant:bar"
    assert msg.skip_list[0].reason == taste_pb2.SKIP_REASON_CODE_OUTSIDE_CITY
    assert msg.skip_list[1].reason == taste_pb2.SKIP_REASON_CODE_LOW_AFFINITY
    return (
        f"{len(msg.doors)} doors, {len(msg.skip_list)} skips, "
        f"{len(msg.evidence)} evidence calls"
    )


def assert_audit(msg) -> str:
    assert len(msg.results) == 2
    first, second = msg.results
    assert first.succeeded and not first.shelf_unknown
    assert first.incumbents[0].name == "Del Maguey Single Village Mezcal"
    assert first.competitor_count == 1
    assert second.shelf_unknown
    assert msg.attribution.model_id == "gemini-3.8-flash"
    return f"{len(msg.results)} results, model {msg.attribution.model_id}"


def assert_pitch(msg) -> str:
    assert "ev-0001" in msg.script
    assert msg.battlecard.incumbent_name == "Del Maguey Single Village Mezcal"
    assert msg.recommended_sku.name == "Ilegal Mezcal Espadín Joven 750ml"
    assert "ev-0004" in msg.attribution.evidence_ids
    assert not msg.attribution.ungrounded
    return f"{len(msg.script)}-char script, SKU {msg.recommended_sku.id}"


def assert_baseline(msg) -> str:
    assert msg.attribution.ungrounded
    assert len(msg.venue_names) == 3
    assert msg.text
    return f"{len(msg.venue_names)} ungrounded venue names"


def assert_trace(msg) -> str:
    assert msg.stage == agent_pb2.TRACE_STAGE_DOOR_RANKING
    assert msg.status == agent_pb2.TRACE_STATUS_FINISHED
    assert msg.cache_hit and msg.elapsed_ms == 412
    assert msg.sequence == 7
    return f"door ranking finished in {msg.elapsed_ms} ms (cache hit)"


CHECKS = {
    "karum.taste.v1.ResolveBrandSeedResponse": assert_seed,
    "karum.taste.v1.ScoutDoorsResponse": assert_scout,
    "karum.agent.v1.AuditMenuResponse": assert_audit,
    "karum.agent.v1.DraftDoorPitchResponse": assert_pitch,
    "karum.agent.v1.LlmOnlyBaselineResponse": assert_baseline,
    "karum.agent.v1.TraceEvent": assert_trace,
}

TYPES = {
    "karum.taste.v1.ResolveBrandSeedResponse": taste_pb2.ResolveBrandSeedResponse,
    "karum.taste.v1.ScoutDoorsResponse": taste_pb2.ScoutDoorsResponse,
    "karum.agent.v1.AuditMenuResponse": agent_pb2.AuditMenuResponse,
    "karum.agent.v1.DraftDoorPitchResponse": agent_pb2.DraftDoorPitchResponse,
    "karum.agent.v1.LlmOnlyBaselineResponse": agent_pb2.LlmOnlyBaselineResponse,
    "karum.agent.v1.TraceEvent": agent_pb2.TraceEvent,
}

USAGE = "usage: python contract/pyrelay/roundtrip.py <testdata-dir> <artifacts-dir>"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    testdata_dir, artifacts_dir = Path(argv[1]), Path(argv[2])

    index = json.loads((testdata_dir / "manifest.json").read_text(encoding="utf-8"))
    messages = index["messages"]

    for entry in messages:
        name, full_name = entry["name"], entry["type"]
        if full_name not in TYPES:
            print(f"python: {name}: no Python stub registered for {full_name}", file=sys.stderr)
            return 1
        artifact = artifacts_dir / f"{name}.bin"
        if not artifact.exists():
            print(f"python: {artifact} is missing; run the Go emit step first", file=sys.stderr)
            return 1

        msg = TYPES[full_name]()
        msg.ParseFromString(artifact.read_bytes())
        try:
            summary = CHECKS[full_name](msg)
        except AssertionError as exc:
            print(f"python: {name}: assertion failed: {exc}", file=sys.stderr)
            return 1

        (artifacts_dir / f"{name}.py.bin").write_bytes(msg.SerializeToString())
        print(f"python: {name:<12} ok  {summary}")

    print(f"python: round-trip ok - {len(messages)} messages parsed, asserted and re-serialized")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
