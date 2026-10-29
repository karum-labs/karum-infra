"""Check that the recorded presets and the gateway catalogue agree.

The presets used to be written down three times. Since PLAN.md §52 the client
fetches the catalogue from ``GET /api/v1/presets`` instead of carrying a mirror,
so there are now two owners:

- ``fixtures/presets/<id>.json`` — the scenario of record. It carries the seed
  the recording session used, the point, the radii, the tags, and the outcome
  that was recorded (the door board's range, the skip list, the heatmap
  counts). The pack is hash-pinned against this file;
- ``karum-server/internal/presets/presets.go`` — the catalogue the gateway
  runs and serves to the client.

Nothing kept them in step, so a preset could drift: the gateway runs one
scenario while the pack replays another. This tool compares the record and the
gateway catalogue and reports every difference. The obsolete client mirror is
reported as skipped, not silently treated as agreement.

Usage::

    python fixtures/tools/check_presets.py            # check the sibling checkouts
    python fixtures/tools/check_presets.py --repo-root ../karum-server

A source that is not checked out is reported as missing and skipped; the tool
never guesses.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[2]

_UUID = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"


def _preset_files(pack: Path) -> dict[str, dict[str, Any]]:
    """The recorded scenarios, keyed by preset id."""
    out: dict[str, dict[str, Any]] = {}
    for file in sorted((pack / "presets").glob("*.json")):
        document = json.loads(file.read_text(encoding="utf-8"))
        out[str(document["preset_id"])] = document
    return out


def _gateway_catalogue(root: Path) -> dict[str, dict[str, Any]]:
    """The gateway's locked catalogue, parsed from the Go source."""
    source = (root / "internal" / "presets" / "presets.go").read_text(encoding="utf-8")
    out: dict[str, dict[str, Any]] = {}
    for block in re.split(r"(?m)^\t\t\{\n", source):
        ident = re.search(r'ID:\s*"([a-z0-9-]+)"', block)
        if ident is None:
            continue
        seed_block = re.search(r"Seed: \[\]Entity\{(.*?)\n\t\t\t\}", block, re.S)
        skip_block = re.search(r"SkipCandidateIDs: \[\]string\{(.*?)\}", block, re.S)
        tags_block = re.search(r"CategoryTags: \[\]string\{(.*?)\}", block, re.S)
        point = re.search(r"Lat:\s*([-\d.]+),\s*Lng:\s*([-\d.]+)", block)
        radius = re.search(r"RadiusMeters:\s*(\d+)", block)
        mode = re.search(r'Mode:\s*"([^"]+)"', block)
        label = re.search(r'Label:\s*"([^"]*)"', block)
        brand = re.search(r'Brand:\s*"([^"]*)"', block)
        city = re.search(r'City:\s*"([^"]*)"', block)
        out[ident.group(1)] = {
            "seed": [
                {"id": i, "name": n, "type": t}
                for i, n, t in re.findall(
                    rf'ID:\s*"({_UUID})",\s*Name:\s*"([^"]*)",\s*Type:\s*"([^"]*)"',
                    seed_block.group(1) if seed_block else "",
                )
            ],
            "skip": re.findall(rf'"({_UUID})"', skip_block.group(1)) if skip_block else [],
            "tags": re.findall(r'"([^"]+)"', tags_block.group(1)) if tags_block else [],
            "point": (
                {"lat": float(point.group(1)), "lon": float(point.group(2))}
                if point
                else None
            ),
            "radius": int(radius.group(1)) if radius else None,
            "mode": mode.group(1) if mode else None,
            "label": label.group(1) if label else None,
            "brand": brand.group(1) if brand else None,
            "city": city.group(1) if city else None,
        }
    return out


def _recorded(preset: dict[str, Any]) -> dict[str, Any]:
    """The scenario of record, in the shape the catalogues use."""
    tags = preset["category_tags"]
    tag_list = tags["doors"] if "doors" in tags else tags["collab"]
    if isinstance(tag_list, str):
        tag_list = [tag_list]
    return {
        "seed": [
            {"id": item["entity_id"], "name": item.get("name", ""), "type": ""}
            for item in preset["seed_entities"]
        ],
        "tags": list(tag_list),
        "point": {
            "lat": float(preset["point"]["lat"]),
            "lon": float(preset["point"]["lon"]),
        },
        "radius": int(preset["radii_m"]["doors"]),
        "mode": str(preset["mode"]),
        "city": str(preset["city"]),
    }


def _compare(
    name: str,
    recorded: dict[str, Any],
    other: dict[str, Any],
    required: set[str] | None = None,
) -> list[str]:
    """The differences between the record and one catalogue.

    The record's ``label`` and ``brand`` are prose — "composite seed — Muji
    (design brand) plus ceramics-studio and matcha vibes" — where the
    catalogues carry a short display name, so they are not comparable and are
    not checked.

    A field in ``required`` must be present in the catalogue. A catalogue that
    leaves one out is reported rather than skipped: a mirror that stops
    pinning the radius must not pass the check by saying nothing.
    """
    problems: list[str] = []
    for field in ("seed", "tags", "point", "radius", "mode", "city"):
        want = recorded.get(field)
        got = other.get(field)
        if required and field in required and got is None:
            problems.append(f"{name}: the catalogue does not pin the {field}")
            continue
        if want is None or got is None:
            continue
        if field == "seed":
            want_ids = [item["id"] for item in want]
            got_ids = [item["id"] for item in got]
            if want_ids != got_ids:
                problems.append(
                    f"{name}: seed entities differ\n"
                    f"      recorded: {want_ids}\n"
                    f"      other:    {got_ids}"
                )
            else:
                for want_item, got_item in zip(want, got):
                    if want_item["name"] and got_item["name"] and want_item["name"] != got_item["name"]:
                        problems.append(
                            f"{name}: the seed entity {want_item['id']} is named "
                            f"{want_item['name']!r} in the record and "
                            f"{got_item['name']!r} in the catalogue"
                        )
        elif want != got:
            problems.append(f"{name}: {field} differs\n      recorded: {want}\n      other:    {got}")
    return problems


def _recorded_request(pack: Path, preset: str) -> dict[str, Any]:
    """What the pack recorded for this preset: the seed and the skip batch.

    The pack is the authority for the *request*: a recording's
    ``source.request`` is the call that was actually made. The presets are
    allowed to trim the seed — the product caps a scout at four seed
    entities — so a request may carry fewer signals than the recording, but
    never a signal the recording never had.
    """
    seed: set[str] = set()
    skip: set[str] = set()
    directory = pack / "qloo" / preset
    if not directory.exists():
        return {"seed": seed, "skip": skip}
    for file in sorted(directory.glob("*.json")):
        document = json.loads(file.read_text(encoding="utf-8"))
        request = str((document.get("source") or {}).get("request", ""))
        if "signal.interests.entities=" not in request:
            continue
        query = request.partition("?")[2]
        for pair in query.split("&"):
            name, _, value = pair.partition("=")
            value = unquote(value)
            if name == "signal.interests.entities":
                seed.update(value.split(","))
            elif name == "filter.results.entities":
                skip.update(value.split(","))
    return {"seed": seed, "skip": skip}


def _skip_coverage(name: str, document: dict[str, Any], catalogue: dict[str, Any]) -> list[str]:
    """The gateway must score the batch the pack recorded, and every skip.

    The record lists the candidates that fell below the floor; the gateway
    sends the batch it scores. Every recorded skip must be in that batch, or
    the replay cannot reproduce the recorded skip list.
    """
    recorded = {item["entity_id"] for item in document.get("skip_candidates", [])}
    if not recorded:
        return []
    sent = set(catalogue.get("skip") or [])
    missing = sorted(recorded - sent)
    if not missing:
        return []
    return [
        f"gateway {name}: the skip batch does not score every recorded skip\n"
        f"      missing: {missing}"
    ]


def _request_fits_the_pack(
    name: str, pack: Path, catalogue: dict[str, Any]
) -> list[str]:
    """The gateway's request must be the recorded one, or a trim of it.

    The seed may carry fewer signals than the recording — the product caps a
    scout at four seed entities — but never a signal the recording never had.
    The skip batch is not trimmed: it is the batch the recording scored, so
    it must match exactly.
    """
    recorded = _recorded_request(pack, name)
    problems: list[str] = []
    sent_seed = {item["id"] for item in catalogue.get("seed") or []}
    extra = sorted(sent_seed - recorded["seed"]) if recorded["seed"] else []
    if extra:
        problems.append(
            f"gateway {name}: the seed holds signals the recording never had\n"
            f"      extra: {extra}"
        )
    if recorded["skip"]:
        sent_skip = set(catalogue.get("skip") or [])
        if sent_skip != recorded["skip"]:
            problems.append(
                f"gateway {name}: the skip batch is not the recorded batch\n"
                f"      recorded: {sorted(recorded['skip'])}\n"
                f"      sent:     {sorted(sent_skip)}"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT.parent,
        help="the directory holding the sibling checkouts",
    )
    args = parser.parse_args()
    root: Path = args.repo_root

    pack = REPO_ROOT / "fixtures"
    recorded = _preset_files(pack)
    gateway_root = root / "karum-server"

    problems: list[str] = []
    checked: list[str] = []
    missing: list[str] = []
    if not gateway_root.exists():
        missing.append(f"gateway: {gateway_root} is not checked out")
    else:
        catalogue = _gateway_catalogue(gateway_root)
        for name, document in recorded.items():
            if name not in catalogue:
                problems.append(f"gateway: the preset {name} is missing from the catalogue")
                continue
            problems.extend(
                _compare(
                    f"gateway {name}",
                    _recorded(document),
                    catalogue[name],
                )
            )
            problems.extend(_skip_coverage(name, document, catalogue[name]))
            problems.extend(_request_fits_the_pack(name, pack, catalogue[name]))
        checked.append(f"gateway: {len(catalogue)} presets")

    client_root = root / "karum-client"
    if client_root.exists():
        missing.append(
            "client: no static preset mirror to compare; the client fetches "
            "GET /api/v1/presets (PLAN.md §52)"
        )

    for line in missing:
        print(f"skipped {line}")
    for line in checked:
        print(f"checked {line}")
    for problem in problems:
        print(f"problem: {problem}")
    print(f"checked {len(recorded)} recorded presets, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
