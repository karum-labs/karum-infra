#!/usr/bin/env python3
"""Qloo hackathon spike runner — PLAN epic 9, QLOO_APIS.md §5.

Works the 22-item spike checklist against https://hackathon.api.qloo.com.

Rules this script enforces:
  - only the hackathon host is called (plus the opt-in DI-1 prod-host 401 check)
  - the key comes from $QLOO_API_KEY and is never printed, saved, or committed
  - raw responses land in spike/out/ (git-ignored): redact before promoting
    anything into the fixture pack — raw Qloo JSON never gets committed
  - parameter variants are always printed next to a no-parameter baseline,
    because unsupported parameters are silently ignored (QLOO_APIS.md §1)

Typical flow (see spike/README.md and spike/RECORDING.md):
  python spike/run_spike.py key
  python spike/run_spike.py resolve --lat 30.2672 --lon -97.7431 --name "Franklin Barbecue" --name "Uchi"
  python spike/run_spike.py brand-location --lat 30.2672 --lon -97.7431 --city Austin
  python spike/run_spike.py filter-type
  python spike/run_spike.py explainability
  python spike/run_spike.py radius --lat 30.2672 --lon -97.7431
  python spike/run_spike.py variants --entity <brand uuid> --tag <tag urn>
  python spike/run_spike.py entities --resy-id <id>
  python spike/run_spike.py post
  python spike/run_spike.py heatmap --lat 30.2672 --lon -97.7431
  python spike/run_spike.py raw "/v2/trending?filter.type=urn:entity:brand&..."
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://hackathon.api.qloo.com"
PROD = "https://api.qloo.com"
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
STATE = HERE / "state.json"
LIST_KEYS = ("entities", "tags", "demographics", "heatmap", "trending", "places")


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def fail(message: str) -> None:
    sys.exit(f"error: {message}")


def api_key() -> str:
    key = os.environ.get("QLOO_API_KEY", "").strip()
    if not key:
        fail(
            "QLOO_API_KEY is not set. PowerShell: $env:QLOO_API_KEY=\"...\" / "
            "bash: export QLOO_API_KEY=... — the key is never written to disk."
        )
    return key


def qs(params: dict) -> str:
    clean = {k: v for k, v in params.items() if v is not None}
    return urllib.parse.urlencode(clean, quote_via=urllib.parse.quote)


def slug(text: str) -> str:
    kept = [c if (c.isalnum() or c in "-_") else "-" for c in text.lower()]
    return "".join(kept).strip("-")[:60]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"places": {}, "brands": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"state -> {STATE.name} ({len(state['places'])} places, {len(state['brands'])} brands)")


def place_ids(state: dict, override: str | None) -> list[str]:
    if override:
        ids = [chunk.strip() for chunk in override.split(",") if chunk.strip()]
    else:
        ids = [row.get("entity_id") for row in state.get("places", {}).values() if row.get("entity_id")]
    if not ids:
        fail("no resolved places yet — run `resolve` first, or pass --ids a,b,c")
    return ids


def row_label(row) -> str:
    if isinstance(row, dict):
        for key in ("name", "tag_id", "subtype", "entity_id", "date"):
            if row.get(key):
                return str(row[key])
    return "?"


def result_rows(payload) -> list:
    results = payload.get("results") if isinstance(payload, dict) else None
    if isinstance(results, list):
        return results
    if isinstance(results, dict):
        for key in LIST_KEYS:
            if isinstance(results.get(key), list):
                return results[key]
    return []


def result_count(payload):
    results = payload.get("results") if isinstance(payload, dict) else None
    if results is None:
        return None
    if isinstance(results, list):
        return len(results)
    if isinstance(results, dict):
        for key in LIST_KEYS:
            if isinstance(results.get(key), list):
                return len(results[key])
        return {k: v for k, v in results.items() if isinstance(v, (int, float, str))}
    return None


def collect_points(node, depth: int = 0):
    """Yield (lat, lon) pairs found anywhere in a response, a few levels deep."""
    if depth > 4:
        return
    if isinstance(node, dict):
        lat = node.get("lat") or node.get("latitude")
        lon = node.get("lon") or node.get("lng") or node.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            yield (float(lat), float(lon))
        for value in node.values():
            yield from collect_points(value, depth + 1)
    elif isinstance(node, list):
        for value in node:
            yield from collect_points(value, depth + 1)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def call(label: str, path: str, method: str = "GET", body: dict | None = None, host: str = BASE):
    """Send one request, print a compact summary, save payload + metadata to out/."""
    url = host + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("X-Api-Key", api_key())
    if data is not None:
        request.add_header("Content-Type", "application/json")

    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status, headers, raw = response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        status, headers, raw = exc.code, dict(exc.headers), exc.read()
    except urllib.error.URLError as exc:
        fail(f"{label}: cannot reach {url} — {exc.reason}")
    duration_ms = round((time.monotonic() - started) * 1000)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {"unparsed": raw.decode("utf-8", errors="replace")[:4000]}

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stem = OUT / f"{stamp}-{slug(label)}"
    stem.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    stem.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "label": label,
                "method": method,
                "path": path,
                "host": host,
                "status": status,
                "duration_ms": duration_ms,
                "headers": headers,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[{label}] {method} {path} -> {status} in {duration_ms} ms, results={result_count(payload)}")
    labels = [row_label(row) for row in result_rows(payload)[:3]]
    if labels:
        print(f"    top: {', '.join(labels)}")
    if isinstance(payload, dict) and payload.get("message"):
        print(f"    message: {payload['message']}")
    limit_headers = {k: v for k, v in headers.items() if any(s in k.lower() for s in ("rate", "limit", "quota"))}
    if limit_headers:
        print(f"    limit headers: {json.dumps(limit_headers)}")
    return payload, status


def report_explanations(payload) -> None:
    if not isinstance(payload, dict):
        return
    explanations = payload.get("explanations")
    if isinstance(explanations, list) and explanations:
        first = explanations[0]
        keys = sorted(first.keys()) if isinstance(first, dict) else []
        print(f"    explanations: {len(explanations)} rows, first-row keys: {keys}")
    else:
        print("    explanations: absent — check the count against baseline (silent-ignore risk)")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_key(args) -> None:
    call("key-probe", "/")
    if args.check_prod_host:
        call("di1-prod-host-check", "/", host=PROD)
        print("DI-1: record the production-host status (401 expected with this key) and close the row.")


def cmd_resolve(args) -> None:
    state = load_state()
    bucket = "places" if args.type == "place" else "brands"
    for name in args.names:
        params = {"query": name, "types": f"urn:entity:{args.type}", "take": 5, "page": 1}
        if args.type == "place" and args.lat is not None and args.lon is not None:
            params["filter.location"] = f"{args.lat},{args.lon}"  # bare pair is latitude-first
            params["filter.radius"] = args.radius  # MILES here — /search rule (QLOO_APIS.md §6)
            params["sort_by"] = "distance"
        payload, _ = call(f"resolve-{args.type}-{slug(name)}", "/search?" + qs(params))
        rows = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            print(f"    !! no match for {name!r} — record the miss honestly")
            continue
        for row in rows[:5]:
            if isinstance(row, dict):
                print(f"    candidate: {row.get('name')} | {row.get('entity_id')} | {row.get('subtype')}")
        top = rows[0]
        state.setdefault(bucket, {})[name] = {
            "entity_id": top.get("entity_id"),
            "name": top.get("name"),
            "subtype": top.get("subtype"),
        }
    save_state(state)
    print("verify the picks above; edit state.json if the preferred match is not the top row.")


def cmd_brand_location(args) -> None:
    if (args.lat is None) != (args.lon is None):
        fail("pass --lat and --lon together (WKT is longitude-first)")
    state = load_state()
    ids = place_ids(state, args.ids)
    base = {
        "filter.type": "urn:entity:brand",
        "signal.interests.entities": ",".join(ids),
        "take": 25,
    }
    call("brand-location-baseline", "/v2/insights?" + qs(base))

    variants = []
    if args.lat is not None:
        point = f"POINT({args.lon} {args.lat})"  # WKT is longitude-first
        variants.append(("filter-location-point", {"filter.location": point}))
        variants.append(("signal-location-point", {"signal.location": point}))
    if args.city:
        variants.append(("signal-location-query", {"signal.location.query": args.city}))
        variants.append(("filter-location-query", {"filter.location.query": args.city}))
        variants.append(("filter-location-metro", {"filter.location.metro": args.city}))
    if not variants:
        fail("brand-location needs --lat/--lon (WKT probes) and/or --city (query / metro probes)")
    for label, extra in variants:
        call(f"brand-location-{label}", "/v2/insights?" + qs({**base, **extra}))
    print("same count and same top names as baseline = silently ignored. Record which variant moved the set (spike 1).")


def cmd_filter_type(args) -> None:
    state = load_state()
    signal = ",".join(place_ids(state, args.ids))
    probes = (
        ("urn-tag", {"filter.type": "urn:tag"}),
        ("urn-demographics", {"filter.type": "urn:demographics"}),
        ("urn-destination", {"filter.type": "urn:entity:destination", "take": 10}),
        ("urn-locality", {"filter.type": "urn:entity:locality", "take": 10}),
        ("urn-videogame", {"filter.type": "urn:entity:videogame", "take": 10}),
    )
    for label, params in probes:
        call(f"filter-type-{label}", "/v2/insights?" + qs({"signal.interests.entities": signal, **params}))
    print("403 = unsupported enum (record it); 200 with results = accepted. Also probe `filter.rating` scope via `raw` (DI-2, DI-19).")


def cmd_explainability(args) -> None:
    state = load_state()
    common = {
        "signal.interests.entities": ",".join(place_ids(state, args.ids)),
        "feature.explainability": "true",
        "take": 10,
    }
    payload, _ = call("explain-brand", "/v2/insights?" + qs({**common, "filter.type": "urn:entity:brand"}))
    report_explanations(payload)
    payload, _ = call("explain-place", "/v2/insights?" + qs({**common, "filter.type": "urn:entity:place"}))
    report_explanations(payload)
    print("inspect the saved JSON: per-result contributions, the aggregate breakdown, and the warning path.")


def cmd_radius(args) -> None:
    if args.lat is None or args.lon is None:
        fail("radius needs --lat and --lon (bare pair, latitude-first)")
    base = {
        "filter.type": "urn:entity:place",
        "filter.location": f"{args.lat},{args.lon}",
        "take": 50,
    }
    if args.tag:
        base["filter.tags"] = args.tag
    cases = (
        ("default", {}),
        ("400m", {"filter.location.radius": 400}),
        ("0m", {"filter.location.radius": 0}),
        ("20000m", {"filter.location.radius": 20000}),
    )
    for label, extra in cases:
        payload, _ = call(f"radius-{label}", "/v2/insights?" + qs({**base, **extra}))
        points = list(collect_points(payload))
        if points:
            distances = [haversine_m(args.lat, args.lon, lat, lon) for lat, lon in points]
            print(f"    coordinates found: {len(points)}, max {max(distances):.0f} m from the point")
        else:
            print("    no coordinates in this payload — judge by counts across the radius values")
    print("Insights radius is METRES; /search filter.radius is MILES. Default pads by min(10% of diameter, ~2.4 km); 0 = strictly inside.")


def cmd_variants(args) -> None:
    if not args.entity:
        fail("variants needs --entity <uuid> (a brand or place id from earlier output)")
    if (args.lat is None) != (args.lon is None):
        fail("pass --lat and --lon together")
    base = {"filter.type": "urn:entity:place", "take": 10}
    if args.lat is not None:
        base["filter.location"] = f"{args.lat},{args.lon}"
    call("variants-baseline", "/v2/insights?" + qs(base))

    def place_probe(label: str, extra: dict) -> None:
        call(f"variants-{label}", "/v2/insights?" + qs({**base, **extra}))

    place_probe("resy-external-rating", {"filter.external.resy.rating.min": 4})
    place_probe("resy-properties-rating", {"filter.properties.resy.rating.min": 4})
    place_probe("resy-rating-count", {"filter.resy.rating_count.min": 10})
    place_probe("price-range-from-to", {"filter.price_range.from": 2, "filter.price_range.to": 4})
    place_probe("price-range-min-max", {"filter.price_range.min": 2, "filter.price_range.max": 4})
    if args.tag:
        place_probe("exclude-tags-filter-operator", {"filter.exclude.tags": args.tag, "operator.filter.exclude.tags": "union"})
        place_probe("exclude-tags-plain-operator", {"filter.exclude.tags": args.tag, "operator.exclude.tags": "union"})
    else:
        print("variants: --tag not given, skipping the operator.exclude pair")
    brand_base = {"filter.type": "urn:entity:brand", "take": 10}
    call("variants-entities-baseline", "/v2/insights?" + qs(brand_base))
    call("variants-filter-entities", "/v2/insights?" + qs({**brand_base, "filter.entities": args.entity}))
    call("variants-filter-results-entities", "/v2/insights?" + qs({**brand_base, "filter.results.entities": args.entity}))
    print("count unchanged from baseline = parameter ignored. Closes DI-4, DI-5, DI-13, DI-14 (spike 11); spike 9 rides along.")


def cmd_entities(args) -> None:
    state = load_state()
    ids = place_ids(state, args.ids)
    payload, _ = call("entities-by-id", "/entities?" + qs({"entity_ids": ",".join(ids)}))
    if isinstance(payload, dict) and isinstance(payload.get("results"), list) and payload["results"]:
        first = payload["results"][0]
        if isinstance(first, dict):
            print(f"    entity keys: {sorted(first.keys())}")
    if args.resy_id:
        call("entities-by-resy", "/entities?" + qs({"external.resy.ids": args.resy_id}))
        print("external-id round trip: check that the returned entity_id is the UUID the stack keys on (spike 16).")
    else:
        print("pass --resy-id <id> (or --ids) to probe the external-ID round trip")


def cmd_post(args) -> None:
    body = {
        "signal": {"interests": {"entities": {"query": ["Qloo HQ"]}}},
        "filter": {"type": "urn:entity:place", "exclude": {"entities": {"query": ["Qloo HQ"]}}},
    }
    call("di3-post-attempt", "/v2/insights", method="POST", body=body)
    print("DI-3: any 2xx/400/404 reply = POST surface exists; 405/501 = GET-only stands.")


def cmd_heatmap(args) -> None:
    if args.lat is None or args.lon is None:
        fail("heatmap needs --lat and --lon")
    base = {
        "filter.type": "urn:heatmap",
        "filter.location": f"{args.lat},{args.lon}",
        "take": 50,
    }
    if args.tag:
        base["signal.interests.tags"] = args.tag
    else:
        base["signal.interests.entities"] = ",".join(place_ids(load_state(), None))
    call("heatmap-default-boundary", "/v2/insights?" + qs(base))
    call("heatmap-urn-geohash", "/v2/insights?" + qs({**base, "output.heatmap.boundary": "urn:geohash"}))
    print("compare against the no-boundary call; try `urn:entity:locality` and a city name via `raw` (DI-12, DI-18 — spike 3).")


def cmd_raw(args) -> None:
    path = args.path if args.path.startswith("/") else "/" + args.path
    call("raw-" + slug(path), path)


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("key", help="GET / — key liveness (first call of the spike)")
    p.add_argument("--check-prod-host", action="store_true", help="also probe the production host once for the DI-1 401")
    p.set_defaults(fn=cmd_key)

    p = sub.add_parser("resolve", help="resolve place/brand names to entity ids via /search; writes state.json")
    p.add_argument("--name", action="append", required=True, dest="names", help="repeat per name")
    p.add_argument("--type", choices=("place", "brand"), default="place")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--radius", type=float, default=3.0, help="filter.radius in MILES (/search rule)")
    p.set_defaults(fn=cmd_resolve)

    p = sub.add_parser("brand-location", help="spike 1 — which location parameter narrows brand results")
    p.add_argument("--ids", help="comma-separated place ids (defaults to state.json)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--city")
    p.set_defaults(fn=cmd_brand_location)

    p = sub.add_parser("filter-type", help="spike 2 — urn:tag, urn:demographics, destination, locality, videogame")
    p.add_argument("--ids")
    p.set_defaults(fn=cmd_filter_type)

    p = sub.add_parser("explainability", help="spike 4 — feature.explainability on brand and place calls")
    p.add_argument("--ids")
    p.set_defaults(fn=cmd_explainability)

    p = sub.add_parser("radius", help="spike 5/6 — filter.location.radius granularity and units")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--tag", help="optional filter.tags value (real tag urn)")
    p.set_defaults(fn=cmd_radius)

    p = sub.add_parser("variants", help="spikes 11 and 9 — paired parameter-name probes")
    p.add_argument("--entity", help="uuid for the filter.entities vs filter.results.entities pair")
    p.add_argument("--tag", help="real tag urn for the operator.exclude pair")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.set_defaults(fn=cmd_variants)

    p = sub.add_parser("entities", help="spike 16 — /entities by id and external.resy.ids round trip")
    p.add_argument("--ids")
    p.add_argument("--resy-id")
    p.set_defaults(fn=cmd_entities)

    p = sub.add_parser("post", help="spike 10 — one POST attempt against the hackathon host")
    p.set_defaults(fn=cmd_post)

    p = sub.add_parser("heatmap", help="spike 3 — urn:heatmap and output.heatmap.boundary literals")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_heatmap)

    p = sub.add_parser("raw", help="generic GET, e.g. raw \"/v2/trending?...\"")
    p.add_argument("path")
    p.set_defaults(fn=cmd_raw)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
