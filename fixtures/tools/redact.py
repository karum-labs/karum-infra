#!/usr/bin/env python3
"""Redact local Qloo recordings into the committed fixture pack.

The raw payloads in ``spike/out/`` are local-only evidence (git-ignored); the
public repositories must never carry raw Qloo JSON (QLOO_APIS.md §1, PLAN.md
§4 "ship a redacted fixture pack"). This tool projects each recording down to
the fields Karum consumes — the shapes in ``proto/karum/common/v1`` and
``proto/karum/taste/v1`` — writes them under ``fixtures/qloo/``, and rebuilds
``fixtures/manifest.json`` with a sha256 per file.

Usage::

    python fixtures/tools/redact.py            # regenerate (needs spike/out/)
    python fixtures/tools/redact.py --verify   # hashes + schema, no recordings needed

The projections below are the redaction contract: each keep-list is the
consume-list. Anything a service needs that is missing here gets added
deliberately (with a fresh recording), never by widening a copy-everything
fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fixtures"
SPIKE = ROOT / "spike" / "out"

UUID_RE = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")
AGE_BUCKETS = (
    "24_and_younger",
    "25_to_29",
    "30_to_34",
    "35_to_44",
    "45_to_54",
    "55_and_older",
)
KEEP_PLACE_PROPERTIES = (
    "address",
    "business_rating",
    "good_for",
    "hours",
    "is_closed",
    "phone",
    "price_level",
    "price_range",
    "website",
)
KEEP_GEOCODE = ("city", "name", "metro", "country", "admin1_region")


# ---------------------------------------------------------------------------
# Recipes: source recording -> fixture file. Everything the pack ships is
# listed here; nothing is copied implicitly.
# ---------------------------------------------------------------------------


def _r(dst: str, src: str, kind: str, note: str = "") -> dict:
    return {"dst": dst, "src": src, "kind": kind, "note": note}


RECIPES = [
    # --- Austin wholesale (Sola seed; 17-18 Oct) ---
    _r("qloo/austin-wholesale/search-aesop.json", "20261017-140127-resolve-brand-aesop.json", "search"),
    _r("qloo/austin-wholesale/search-khruangbin.json", "20261017-140135-resolve-artist-khruangbin.json", "search"),
    _r("qloo/austin-wholesale/search-franklin-barbecue.json", "20261017-140129-resolve-place-franklin-barbecue.json", "search"),
    _r(
        "qloo/austin-wholesale/search-the-blind-pig-pub.json",
        "20261017-140132-resolve-place-the-blind-pig-pub.json",
        "search",
        "The Austin row is resolve rank 5 of 5; the preset pins the Austin id.",
    ),
    _r("qloo/austin-wholesale/search-maggie-maes.json", "20261017-140134-resolve-place-maggie-mae-s.json", "search"),
    _r("qloo/austin-wholesale/search-uchiko-austin.json", "20261017-140226-resolve-place-uchi.json", "search"),
    _r("qloo/austin-wholesale/search-whislers.json", "20261017-140227-resolve-place-whisler-s.json", "search"),
    _r("qloo/austin-wholesale/search-la-condesa.json", "20261018-050756-resolve-place-la-condesa.json", "search"),
    _r("qloo/austin-wholesale/search-suerte.json", "20261018-050758-resolve-place-suerte.json", "search"),
    _r("qloo/austin-wholesale/search-here-nor-there.json", "20261018-050800-resolve-place-here-nor-there.json", "search"),
    _r("qloo/austin-wholesale/search-kemuri-tatsu-ya.json", "20261018-050825-resolve-place-kemuri-tatsu-ya.json", "search"),
    _r(
        "qloo/austin-wholesale/search-easy-tiger.json",
        "20261018-050826-resolve-place-easy-tiger.json",
        "search",
        "Top row is Bengaluru; the Austin row is rank 2 and the preset pins it.",
    ),
    _r("qloo/austin-wholesale/insights-doors-baseline.json", "20261017-140353-brand-doors-baseline.json", "insights"),
    _r("qloo/austin-wholesale/insights-doors-take50.json", "20261017-140359-brand-doors-take50.json", "insights"),
    _r(
        "qloo/austin-wholesale/insights-doors-control-place-signal.json",
        "20261017-140356-brand-doors-control-place-signal.json",
        "insights",
    ),
    _r(
        "qloo/austin-wholesale/insights-doors-category-bar.json",
        "20261017-140600-brand-doors-category-bar.json",
        "insights",
        "The door-shaped board: filter.tags=urn:tag:genre:place:restaurant:bar narrows the taste anchors away.",
    ),
    _r("qloo/austin-wholesale/insights-skip-ranked.json", "20261017-140501-skip-pool-ranked.json", "insights"),
    _r("qloo/austin-wholesale/insights-skip-batch-probe.json", "20261017-140503-skip-pool-batch-probe.json", "insights"),
    _r(
        "qloo/austin-wholesale/compare-tobala-ilegal.json",
        "20261018-051720-austin-compare-tobala-ilegal.json",
        "compare",
        "Preset-grade pair: Mezcaleria Tobala x Ilegal Mezcal; 12 shared-tag rows.",
    ),
    _r("qloo/austin-wholesale/demographics-seed.json", "20261018-052008-austin-demographics-seed.json", "demographics"),

    # --- Brooklyn flagship (ceramics + matcha; 18 Oct) ---
    _r("qloo/brooklyn-flagship/search-muji.json", "20261018-050842-resolve-brand-muji.json", "search"),
    _r("qloo/brooklyn-flagship/search-kinfolk.json", "20261018-050921-resolve-brand-kinfolk.json", "search"),
    _r("qloo/brooklyn-flagship/search-marimekko.json", "20261018-050920-resolve-brand-marimekko.json", "search"),
    _r("qloo/brooklyn-flagship/search-matchabar.json", "20261018-050922-resolve-place-matchabar.json", "search"),
    _r("qloo/brooklyn-flagship/search-kettl-tea.json", "20261018-050924-resolve-place-kettl-tea.json", "search"),
    _r("qloo/brooklyn-flagship/search-choplet-ceramic-studio.json", "20261018-050840-resolve-place-choplet-ceramic-studio.json", "search"),
    _r("qloo/brooklyn-flagship/search-bklyn-clay.json", "20261018-050842-resolve-place-bklyn-clay.json", "search"),
    _r("qloo/brooklyn-flagship/search-devocion.json", "20261018-050920-resolve-place-devocion.json", "search"),
    _r("qloo/brooklyn-flagship/search-sey-coffee.json", "20261018-050922-resolve-place-sey-coffee.json", "search"),
    _r("qloo/brooklyn-flagship/search-bakeri.json", "20261018-050923-resolve-place-bakeri.json", "search"),
    _r(
        "qloo/brooklyn-flagship/search-butler.json",
        "20261018-050927-resolve-place-butler.json",
        "search",
        "The New York row is resolve rank 4 of 5 (top rows are Moscow/Thessaloniki).",
    ),
    _r("qloo/brooklyn-flagship/search-maison-premiere.json", "20261018-050922-resolve-place-maison-premiere.json", "search"),
    _r("qloo/brooklyn-flagship/search-fresh-kills-bar.json", "20261018-050926-resolve-place-fresh-kills-bar.json", "search"),
    _r("qloo/brooklyn-flagship/search-cafe-mogador.json", "20261018-050928-resolve-place-cafe-mogador.json", "search"),
    _r("qloo/brooklyn-flagship/search-lilia.json", "20261018-050930-resolve-place-lilia.json", "search"),
    _r("qloo/brooklyn-flagship/insights-doors-cafe-tag.json", "20261018-051106-brooklyn-doors-cafe-tag.json", "insights"),
    _r("qloo/brooklyn-flagship/insights-heatmap-cells.json", "20261018-051112-brooklyn-heatmap-seed.json", "heatmap"),
    _r(
        "qloo/brooklyn-flagship/insights-heatmap-cells-geohash.json",
        "20261018-051122-brooklyn-heatmap-seed-geohash.json",
        "heatmap",
        "output.heatmap.boundary=urn:geohash variant; recorded for parity.",
    ),
    _r(
        "qloo/brooklyn-flagship/insights-heatmap-localities.json",
        "20261018-051637-brooklyn-heatmap-seed-localities.json",
        "locality",
        "output.heatmap.boundary=urn:entity:locality; 83 polygon rows for the corridor layer.",
    ),
    _r("qloo/brooklyn-flagship/insights-skip-ranked.json", "20261018-051103-skip-pool-ranked.json", "insights"),
    _r("qloo/brooklyn-flagship/insights-skip-batch-probe.json", "20261018-051107-skip-pool-batch-probe.json", "insights"),
    _r("qloo/brooklyn-flagship/demographics-seed.json", "20261018-052010-brooklyn-demographics-seed.json", "demographics"),
    _r(
        "qloo/brooklyn-flagship/demographics-door-batch-probe.json",
        "20261018-052010-brooklyn-demographics-door-batch-probe.json",
        "demographics",
        "filter.results.entities is ignored by demographics: rows follow the signal inputs, not the requested door ids.",
    ),

    # --- Brooklyn collab (non-competing partner categories) ---
    _r("qloo/brooklyn-collab/insights-collab-galleries.json", "20261018-051103-brooklyn-collab-galleries.json", "insights"),
    _r(
        "qloo/brooklyn-collab/insights-collab-ceramics.json",
        "20261018-051104-brooklyn-collab-ceramics.json",
        "insights",
        "0 rows: the place:ceramics genre tag is too thin at this point; galleries carry the collab grade.",
    ),

    # --- Mumbai Colaba wholesale (cacao + coffee; 16-18 Oct) ---
    _r("qloo/mumbai-colaba-wholesale/search-subko.json", "20261018-051212-resolve-place-subko.json", "search"),
    _r("qloo/mumbai-colaba-wholesale/search-blue-tokai-coffee.json", "20261018-051214-resolve-place-blue-tokai-coffee.json", "search"),
    _r("qloo/mumbai-colaba-wholesale/search-leopold-cafe.json", "20261016-090729-resolve-place-leopold-cafe.json", "search"),
    _r(
        "qloo/mumbai-colaba-wholesale/insights-doors-baseline.json",
        "20261017-140021-brand-doors-baseline.json",
        "insights",
        "17 Oct shape run with the Cafe Coffee Day brand signal; topped out with event venues (trap 15).",
    ),
    _r("qloo/mumbai-colaba-wholesale/insights-doors-take50.json", "20261017-140027-brand-doors-take50.json", "insights"),
    _r(
        "qloo/mumbai-colaba-wholesale/insights-doors-control-place-signal.json",
        "20261017-140024-brand-doors-control-place-signal.json",
        "insights",
    ),
    _r("qloo/mumbai-colaba-wholesale/insights-doors-plus-tags.json", "20261017-140030-brand-doors-plus-tags.json", "insights"),
    _r("qloo/mumbai-colaba-wholesale/insights-doors-untagged.json", "20261018-051307-colaba-doors-untagged.json", "insights"),
    _r("qloo/mumbai-colaba-wholesale/insights-doors-cafe-tag.json", "20261018-051311-colaba-doors-cafe-tag.json", "insights"),
    _r("qloo/mumbai-colaba-wholesale/insights-skip-batch-probe.json", "20261018-051304-colaba-skip-batch.json", "insights"),
    _r(
        "qloo/mumbai-colaba-wholesale/compare-leopold-probe.json",
        "20261016-101324-raw-v2-analysis-compare-a-signal-interests-entities-68a744f0.json",
        "compare",
        "16 Oct probe pair (Leopold Cafe x incumbent brand); the preset-grade pair is recorded at prewarm.",
    ),
    _r("qloo/mumbai-colaba-wholesale/demographics-seed.json", "20261018-052008-colaba-demographics-seed.json", "demographics"),

    # --- Shared tag catalogues ---
    _r("qloo/tags/bar-genre.json", "20261017-140523-tags-bar-genre.json", "tags", "Canary that produced the Austin door category URN."),
    _r("qloo/tags/cafe-genre.json", "20261018-050947-tags-cafe-genre.json", "tags"),
    _r("qloo/tags/ceramics-genre.json", "20261018-050947-tags-ceramics-genre.json", "tags"),
    _r("qloo/tags/gallery-genre.json", "20261018-051001-tags-gallery-genre.json", "tags"),

    # --- Coverage misses (kept as honesty evidence, PLAN.md §40) ---
    _r("qloo/misses/search-madre-mezcal-brand.json", "20261017-140126-resolve-brand-madre-mezcal.json", "search", "Brand-typed search falls back to unrelated mezcal brands."),
    _r("qloo/misses/search-madre-mezcal-any-type.json", "20261017-140224-madre-mezcal-any-type.json", "search", "Any-type search returns same-name places in other cities only."),
    _r("qloo/misses/search-kinto.json", "20261018-050839-resolve-brand-kinto.json", "search", "0 rows: no Kinto brand entity."),
    _r("qloo/misses/search-hasami-porcelain.json", "20261018-050840-resolve-brand-hasami-porcelain.json", "search", "Falls back to Royal Copenhagen."),
    _r("qloo/misses/search-ippodo-tea.json", "20261018-050843-resolve-brand-ippodo-tea.json", "search", "Falls back to unrelated tea brands."),
    _r("qloo/misses/search-kettl-brand.json", "20261018-050845-resolve-brand-kettl.json", "search", "Falls back to kettle retailers."),
    _r("qloo/misses/search-matchaful.json", "20261018-050846-resolve-brand-matchaful.json", "search", "0 rows: no Matchaful brand entity."),
    _r("qloo/misses/search-toby-s-estate-coffee.json", "20261018-050925-resolve-place-toby-s-estate-coffee.json", "search", "All rows are overseas; no New York venue row."),
    _r("qloo/misses/search-the-west.json", "20261018-050924-resolve-place-the-west.json", "search", "Generic name drowned by Westin hotels."),
    _r("qloo/misses/search-subko-brand.json", "20261018-051141-resolve-brand-subko-coffee-roasters.json", "search", "Falls back to US roasters; Subko resolves as places instead."),
    _r("qloo/misses/search-blue-tokai-brand.json", "20261018-051143-resolve-brand-blue-tokai-coffee-roasters.json", "search", "Falls back to Blue Bottle; Blue Tokai resolves as places instead."),
    _r("qloo/misses/search-third-wave-brand.json", "20261018-051145-resolve-brand-third-wave-coffee.json", "search", "Falls back to unrelated brands."),
    _r("qloo/misses/search-dandelion-chocolate.json", "20261018-051146-resolve-brand-dandelion-chocolate.json", "search", "Falls back to Lindt and other large chocolate brands."),
    _r("qloo/misses/search-kocoatrait.json", "20261018-051212-resolve-brand-kocoatrait.json", "search", "0 rows: no Kocoatrait brand entity."),
    _r("qloo/misses/search-paul-and-mike.json", "20261018-051213-resolve-brand-paul-and-mike.json", "search", "Falls back to fashion designers."),
]


# ---------------------------------------------------------------------------
# Row projections (the redaction contract)
# ---------------------------------------------------------------------------


def _latlon(node) -> dict | None:
    if not isinstance(node, dict):
        return None
    lat = node.get("lat", node.get("latitude"))
    lon = node.get("lon", node.get("longitude"))
    if lat is None or lon is None:
        return None
    return {"lat": lat, "lon": lon}


def _geocode(properties) -> dict | None:
    geocode = (properties or {}).get("geocode") or {}
    kept = {key: geocode[key] for key in KEEP_GEOCODE if geocode.get(key) is not None}
    return kept or None


def project_search(row: dict) -> dict:
    return {
        "entity_id": row.get("entity_id"),
        "name": row.get("name"),
        "types": row.get("types") or [],
        "location": _latlon(row.get("location")),
        "geocode": _geocode(row.get("properties")),
        "disambiguation": row.get("disambiguation"),
    }


def project_place(row: dict) -> dict:
    properties = row.get("properties") or {}
    kept = {key: properties[key] for key in KEEP_PLACE_PROPERTIES if properties.get(key) is not None}
    geocode = _geocode(properties)
    if geocode:
        kept["geocode"] = geocode
    query = row.get("query") or {}
    kept_query = {key: query[key] for key in ("affinity", "distance") if query.get(key) is not None}
    explainability = query.get("explainability")
    if isinstance(explainability, dict) and isinstance(explainability.get("signal.interests.entities"), list):
        contributions = [
            {"entity_id": item.get("entity_id"), "score": item.get("score")}
            for item in explainability["signal.interests.entities"]
            if isinstance(item, dict)
        ]
        kept_query["explainability"] = {"signal.interests.entities": contributions}
    tags = [
        {key: tag.get(key) for key in ("id", "name", "type", "weight")}
        for tag in (row.get("tags") or [])
        if isinstance(tag, dict)
    ]
    return {
        "entity_id": row.get("entity_id"),
        "name": row.get("name"),
        "type": row.get("type"),
        "subtype": row.get("subtype"),
        "disambiguation": row.get("disambiguation"),
        "location": _latlon(row.get("location")),
        "popularity": row.get("popularity"),
        "tags": tags,
        "query": kept_query,
        "properties": kept,
    }


def project_cell(row: dict) -> dict:
    location = row.get("location") or {}
    query = row.get("query") or {}
    return {
        "geohash": location.get("geohash"),
        "location": _latlon(location),
        "affinity": query.get("affinity"),
        "affinity_rank": query.get("affinity_rank"),
        "popularity": query.get("popularity"),
    }


def project_locality(row: dict) -> dict:
    query = row.get("query") or {}
    return {
        "entity_id": row.get("entity_id"),
        "name": row.get("name"),
        "disambiguation": row.get("disambiguation"),
        "affinity": query.get("affinity"),
        "boundary": row.get("boundary"),
    }


def project_tag(row: dict) -> dict:
    return {"id": row.get("id"), "name": row.get("name"), "type": row.get("type")}


def project_demographics(row: dict) -> dict:
    query = row.get("query") or {}
    age = query.get("age") or {}
    gender = query.get("gender") or {}
    return {
        "entity_id": row.get("entity_id"),
        "age": {bucket: age[bucket] for bucket in AGE_BUCKETS if bucket in age},
        "gender": {key: gender[key] for key in ("male", "female") if key in gender},
    }


def project_compare(row: dict) -> dict:
    query = row.get("query") or {}
    return {
        "tag_id": row.get("tag_id"),
        "name": row.get("name"),
        "type": row.get("type"),
        "subtype": row.get("subtype"),
        "entity_id": row.get("entity_id"),
        "count": query.get("count"),
    }


PROJECTIONS = {
    "search": project_search,
    "insights": project_place,
    "heatmap": project_cell,
    "locality": project_locality,
    "tags": project_tag,
    "demographics": project_demographics,
    "compare": project_compare,
}


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------


def unwrap_rows(payload) -> list:
    results = payload.get("results") if isinstance(payload, dict) else None
    if isinstance(results, list):
        return results
    if isinstance(results, dict):
        found = []
        for value in results.values():
            if isinstance(value, list):
                found.extend(value)
        return found
    return []


def collect_warnings(payload) -> list:
    warnings = []
    if isinstance(payload, dict):
        if isinstance(payload.get("warnings"), list):
            warnings.extend(payload["warnings"])
        results = payload.get("results")
        if isinstance(results, dict) and isinstance(results.get("warnings"), list):
            warnings.extend(results["warnings"])
    return warnings


def stamp_of(name: str) -> str:
    raw = name[:15]  # "20261018-050756"
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]} {raw[9:11]}:{raw[11:13]}:{raw[13:15]}"


def build_document(recipe: dict, meta: dict, payload) -> dict:
    project = PROJECTIONS[recipe["kind"]]
    rows = [project(row) for row in unwrap_rows(payload) if isinstance(row, dict)]
    document = {
        "fixture_version": 1,
        "kind": recipe["kind"],
        "source": {
            "recording": recipe["src"],
            "recorded": stamp_of(recipe["src"]),
            "label": meta.get("label"),
            "status": meta.get("status"),
            "request": meta.get("path"),
        },
        "rows": rows,
    }
    if recipe.get("note"):
        document["note"] = recipe["note"]
    warnings = collect_warnings(payload)
    if warnings:
        document["warnings"] = warnings
    return document


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def dump_json(document) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def meta_path_for(src: str) -> Path:
    return SPIKE / f"{src[:-5]}.meta.json"


# ---------------------------------------------------------------------------
# Regeneration
# ---------------------------------------------------------------------------


def regenerate() -> int:
    problems = []
    written = skipped = 0
    entries = []
    for recipe in RECIPES:
        source = SPIKE / recipe["src"]
        if not source.exists():
            problems.append(f"missing recording: {recipe['src']}")
            continue
        meta_file = meta_path_for(recipe["src"])
        meta = read_json(meta_file) if meta_file.exists() else {}
        document = build_document(recipe, meta, read_json(source))
        blob = dump_json(document)
        destination = OUT / recipe["dst"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() == blob:
            skipped += 1
        else:
            destination.write_bytes(blob)
            written += 1
        entries.append(
            {
                "path": recipe["dst"],
                "sha256": hashlib.sha256(blob).hexdigest(),
                "bytes": len(blob),
                "kind": recipe["kind"],
                "source": {"recording": recipe["src"], "label": meta.get("label")},
            }
        )
    for path in sorted((OUT / "presets").glob("*.json")):
        blob = path.read_bytes()
        entries.append(
            {
                "path": f"presets/{path.name}",
                "sha256": hashlib.sha256(blob).hexdigest(),
                "bytes": len(blob),
                "kind": "preset",
            }
        )
    manifest = {
        "fixture_version": 1,
        "generated_by": "fixtures/tools/redact.py",
        "generated_from": "spike/out recordings, 16-18 Oct 2026 (see spike/RECORDING.md)",
        "redaction": "fields Karum consumes only; never raw Qloo JSON (QLOO_APIS.md §1, PLAN.md §4)",
        "files": sorted(entries, key=lambda entry: entry["path"]),
    }
    (OUT / "manifest.json").write_bytes(dump_json(manifest))
    print(f"wrote {written}, unchanged {skipped}, manifest {len(entries)} files")
    for problem in problems:
        print(f"problem: {problem}")
    return 1 if problems else 0


# ---------------------------------------------------------------------------
# Verification (CI-safe: no recordings needed)
# ---------------------------------------------------------------------------


def preset_problems(rel: str, document) -> list:
    problems = []
    if not isinstance(document, dict):
        return [f"{rel}: not a JSON object"]
    required = (
        "preset_id",
        "label",
        "mode",
        "city",
        "point",
        "radii_m",
        "category_tags",
        "seed_entities",
        "skip_candidates",
        "recordings",
        "verified",
    )
    for key in required:
        if key not in document:
            problems.append(f"{rel}: missing {key}")
    if document.get("mode") not in ("wholesale", "flagship", "collab"):
        problems.append(f"{rel}: bad mode {document.get('mode')!r}")
    point = document.get("point") or {}
    lat, lon = point.get("lat"), point.get("lon")
    if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
        problems.append(f"{rel}: bad point.lat")
    if not isinstance(lon, (int, float)) or not -180 <= lon <= 180:
        problems.append(f"{rel}: bad point.lon")
    radii = document.get("radii_m") or {}
    if not isinstance(radii.get("doors"), int) or not 100 <= radii["doors"] <= 20000:
        problems.append(f"{rel}: bad radii_m.doors")
    if "heatmap" in radii and (not isinstance(radii["heatmap"], int) or not 100 <= radii["heatmap"] <= 20000):
        problems.append(f"{rel}: bad radii_m.heatmap")
    tags = document.get("category_tags") or {}
    if not tags:
        problems.append(f"{rel}: empty category_tags")
    for value in tags.values():
        values = value if isinstance(value, list) else [value]
        for urn in values:
            if not isinstance(urn, str) or not urn.startswith("urn:"):
                problems.append(f"{rel}: bad tag value {urn!r}")
    seeds = document.get("seed_entities") or []
    if not 1 <= len(seeds) <= 4:
        problems.append(f"{rel}: seed_entities count {len(seeds)} outside 1..4 (PLAN.md §26)")
    for seed in seeds:
        if not UUID_RE.match(str(seed.get("entity_id", ""))):
            problems.append(f"{rel}: bad seed entity_id {seed.get('entity_id')!r}")
    for candidate in document.get("skip_candidates") or []:
        if not UUID_RE.match(str(candidate.get("entity_id", ""))):
            problems.append(f"{rel}: bad skip entity_id {candidate.get('entity_id')!r}")
    for recording in document.get("recordings") or []:
        if not (OUT / recording).exists():
            problems.append(f"{rel}: recording missing on disk: {recording}")
    return problems


def qloo_problems(rel: str, document) -> list:
    problems = []
    if not isinstance(document, dict):
        return [f"{rel}: not a JSON object"]
    if document.get("fixture_version") != 1:
        problems.append(f"{rel}: fixture_version != 1")
    if document.get("kind") not in PROJECTIONS:
        problems.append(f"{rel}: unknown kind {document.get('kind')!r}")
    if not isinstance(document.get("rows"), list):
        problems.append(f"{rel}: rows is not a list")
    if not isinstance(document.get("source"), dict) or not document["source"].get("recording"):
        problems.append(f"{rel}: missing source.recording")
    return problems


def verify() -> int:
    manifest_path = OUT / "manifest.json"
    if not manifest_path.exists():
        print("problem: fixtures/manifest.json is missing (run the redactor)")
        return 1
    manifest = read_json(manifest_path)
    problems = []
    listed = set()
    for entry in manifest.get("files", []):
        rel = entry.get("path", "")
        listed.add(rel)
        path = OUT / rel
        if not path.exists():
            problems.append(f"{rel}: listed in the manifest but missing on disk")
            continue
        blob = path.read_bytes()
        if hashlib.sha256(blob).hexdigest() != entry.get("sha256"):
            problems.append(f"{rel}: sha256 mismatch")
        if len(blob) != entry.get("bytes"):
            problems.append(f"{rel}: byte size mismatch")
        document = read_json(path)
        if rel.startswith("presets/"):
            problems.extend(preset_problems(rel, document))
        else:
            problems.extend(qloo_problems(rel, document))
    for folder in ("presets", "qloo"):
        for path in sorted((OUT / folder).rglob("*.json")):
            rel = path.relative_to(OUT).as_posix()
            if rel not in listed:
                problems.append(f"{rel}: on disk but not in the manifest")
    for problem in problems:
        print(f"problem: {problem}")
    print(f"checked {len(listed)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="check manifest hashes and schemas (no recordings needed)")
    args = parser.parse_args()
    return verify() if args.verify else regenerate()


if __name__ == "__main__":
    raise SystemExit(main())
