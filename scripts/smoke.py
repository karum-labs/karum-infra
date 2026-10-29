"""Smoke the running stack and assert the judge journey still works.

The smoke posts the Austin preset, waits for the run to reach a terminal
state, and asserts the four outputs the product promises: a ranked door
board, a skip list with reasons, a per-door pitch, and a field route. It
exits non-zero on the first missing output, so ``make test`` fails loudly
when the core journey breaks.

By default the request carries ``rerun: true`` so the smoke exercises the
pipeline instead of replaying the newest stored preset run. Set
``SMOKE_RERUN=0`` to exercise the replay shortcut deliberately.

On a live stack, set ``SMOKE_LIVE=1`` to assert the coverage a live run must
have: a ``ready`` state, a shelf read on the top five doors, a demographics
profile on the top eight, no template pitch, and a grounded source for every
menu that names an incumbent. The minimum counts can be relaxed with
``SMOKE_MIN_SHELF`` and ``SMOKE_MIN_DEMOGRAPHICS`` when a venue legitimately
has no readable menu or no Qloo profile; the report still prints the counts.

Usage:
    python scripts/smoke.py [gateway-base] [--preset austin-wholesale]

Environment:
    GATEWAY_URL             the gateway base URL (default http://127.0.0.1:8080)
    SMOKE_PRESET            the preset to scout (default austin-wholesale)
    SMOKE_RERUN             true to run the pipeline, false to replay (default true)
    SMOKE_LIVE              true to require live coverage (default false)
    SMOKE_MIN_SHELF         top-five shelf reads required in live mode
    SMOKE_MIN_DEMOGRAPHICS  top-eight profiles required in live mode
    SMOKE_OUT               where to write the JSON report (default contract/.out/smoke.json)
    SMOKE_TIMEOUT           seconds to wait for a terminal state (default 180)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8080").rstrip("/")
PRESET = os.environ.get("SMOKE_PRESET", "austin-wholesale")
OUT = Path(os.environ.get("SMOKE_OUT", "contract/.out/smoke.json"))
TIMEOUT = int(os.environ.get("SMOKE_TIMEOUT", "180"))
RERUN = os.environ.get("SMOKE_RERUN", "1").strip().lower() not in {"0", "false", "no"}
LIVE = os.environ.get("SMOKE_LIVE", "").strip().lower() in {"1", "true", "yes"}


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


# A negative value means "use the live-mode default for this run's door count".
MIN_SHELF = _int_env("SMOKE_MIN_SHELF", -1)
MIN_DEMOGRAPHICS = _int_env("SMOKE_MIN_DEMOGRAPHICS", -1)
TERMINAL = {"ready", "degraded", "failed"}


def call(method: str, path: str, body: dict | None = None, headers: dict | None = None):
    """One JSON request. Returns (status, payload)."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method, headers=headers or {}
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        try:
            return err.code, json.loads(err.read() or b"{}")
        except json.JSONDecodeError:
            return err.code, {}
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return 0, {"error": str(err)}


def main() -> int:
    failures: list[str] = []
    report: dict[str, Any] = {"base": BASE, "preset": PRESET}

    status, health = call("GET", "/health")
    report["health_status"] = status
    if status != 200:
        failures.append(f"GET /health returned {status}")
    else:
        dependencies = health.get("dependencies") or {}
        report["dependencies"] = dependencies
        for name in ("taste", "ai"):
            state = dependencies.get(name)
            if isinstance(state, dict):
                state = state.get("status")
            if state in {"down", "unreachable"}:
                failures.append(f"dependency {name} is {state}")

    key = f"smoke-{int(time.time())}"
    body = {
        "preset_id": PRESET,
        "city": "Austin, TX, US",
        "mode": "wholesale",
        "radius_meters": 8000,
        "category_tags": ["urn:tag:genre:place:restaurant:bar"],
        "rerun": RERUN,
    }
    headers = {"Content-Type": "application/json", "Idempotency-Key": key}

    status, job = call("POST", "/api/v1/scout", body, headers)
    report["scout_status"] = status
    if status not in {200, 201, 202}:
        failures.append(f"POST /api/v1/scout returned {status}: {json.dumps(job)[:200]}")
        _write(report, failures)
        return 1
    job_id = job.get("id") or job.get("job_id")
    report["job_id"] = job_id
    if not job_id:
        failures.append("the scout response carried no job id")
        _write(report, failures)
        return 1

    # The same key with the same body must replay the same job.
    replay_status, replay = call("POST", "/api/v1/scout", body, headers)
    report["replay_status"] = replay_status
    replay_id = replay.get("id") or replay.get("job_id")
    if replay_status not in {200, 201, 202} or replay_id != job_id:
        failures.append(
            f"the idempotent replay returned {replay_status} for job {replay_id} (expected {job_id})"
        )

    deadline = time.time() + TIMEOUT
    state = ""
    run: dict[str, Any] = {}
    while time.time() < deadline:
        status, run = call("GET", f"/api/v1/scout/{job_id}")
        state = str(run.get("state", ""))
        if state in TERMINAL:
            break
        time.sleep(2)
    report["state"] = state
    if state not in TERMINAL:
        failures.append(f"the run did not reach a terminal state within {TIMEOUT}s (last: {state!r})")

    # The gateway returns the campaign fields at the top level of the run
    # payload; older payloads nested them under "campaign".
    campaign = run.get("campaign") or run
    doors = campaign.get("doors") or []
    skips = campaign.get("skip_list") or []
    route = campaign.get("route") or {}
    pitches = [door for door in doors if door.get("pitch")]
    top_five = doors[:5]
    top_eight = doors[:8]
    shelf_top = [door for door in top_five if _has_score(door, "shelf_opportunity")]
    demo_top = [
        door for door in top_eight if _has_score(door, "demographic_alignment")
    ]
    profiles = [door for door in doors if isinstance(door.get("demographics"), dict)]
    templated = [
        door for door in pitches if (door.get("pitch") or {}).get("template") is True
    ]
    sourced = [door for door in doors if (door.get("menu") or {}).get("sources")]
    report["doors"] = len(doors)
    report["skips"] = len(skips)
    report["pitches"] = len(pitches)
    report["shelf_top5"] = len(shelf_top)
    report["demographics_top8"] = len(demo_top)
    report["demographic_profiles"] = len(profiles)
    report["templated_pitches"] = len(templated)
    report["sourced_menus"] = len(sourced)
    report["route"] = {"skipped": route.get("skipped"), "failed": route.get("failed")}

    if not doors:
        failures.append("the campaign returned no doors")
    if not skips:
        failures.append("the campaign returned no skip list")
    for skip in skips:
        if not skip.get("reason"):
            failures.append(f"a skip row has no reason: {json.dumps(skip)[:160]}")
            break
    if not pitches:
        failures.append("no door carries a pitch")
    if route.get("failed"):
        failures.append(f"the field route failed: {route.get('error')}")
    if campaign.get("error_code"):
        failures.append(
            f"the run carries an error: {campaign.get('error_code')} {campaign.get('error_message')}"
        )

    if LIVE:
        if state != "ready":
            failures.append(f"a live run must reach ready, not {state!r}")
        required_shelf = MIN_SHELF if MIN_SHELF >= 0 else min(5, len(doors))
        if len(shelf_top) < required_shelf:
            failures.append(
                f"only {len(shelf_top)} of the top {len(top_five)} doors have a "
                f"shelf read; live mode requires {required_shelf} "
                "(set SMOKE_MIN_SHELF to relax a known miss)"
            )
        required_demo = (
            MIN_DEMOGRAPHICS if MIN_DEMOGRAPHICS >= 0 else min(8, len(doors))
        )
        if len(demo_top) < required_demo:
            failures.append(
                f"only {len(demo_top)} of the top {len(top_eight)} doors have a "
                f"demographic profile; live mode requires {required_demo} "
                "(set SMOKE_MIN_DEMOGRAPHICS to relax a known miss)"
            )
        if len(profiles) > min(8, len(doors)):
            failures.append(
                f"the demographics batch returned {len(profiles)} profiles, "
                "above the top-eight cap"
            )
        if len(pitches) < len(doors):
            failures.append(
                f"only {len(pitches)} of {len(doors)} doors carry a pitch"
            )
        if templated:
            failures.append(
                f"{len(templated)} pitch(es) are still templates in a live run"
            )
        if not sourced:
            failures.append("no door carries a grounded menu source")
        for door in doors:
            menu = door.get("menu") or {}
            if menu.get("incumbents") and not menu.get("sources"):
                failures.append(
                    f"{door.get('name') or door.get('id')} names an incumbent "
                    "without a grounding source"
                )
                break

    _write(report, failures)
    if failures:
        print("smoke: FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        f"smoke: ok - state={state} doors={len(doors)} skips={len(skips)} "
        f"pitches={len(pitches)} shelf={len(shelf_top)}/{len(top_five)} "
        f"demo={len(demo_top)}/{len(top_eight)} templated={len(templated)} "
        f"sources={len(sourced)} "
        f"route={'skipped' if route.get('skipped') else 'built'}"
    )
    return 0


def _has_score(door: dict[str, Any], name: str) -> bool:
    """True when the door carries that sub-score object."""
    scores = door.get("scores")
    return isinstance(scores, dict) and isinstance(scores.get(name), dict)


def _write(report: dict[str, Any], failures: list[str]) -> None:
    report["failures"] = failures
    report["ok"] = not failures
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        BASE = sys.argv[1].rstrip("/")
    raise SystemExit(main())
