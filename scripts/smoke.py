"""Smoke the running stack and assert the judge journey still works.

The smoke posts the Austin preset, waits for the run to reach a terminal
state, and asserts the four outputs the product promises: a ranked door
board, a skip list with reasons, a per-door pitch, and a field route. It
exits non-zero on the first missing output, so ``make test`` fails loudly
when the core journey breaks.

Usage:
    python scripts/smoke.py [gateway-base] [--preset austin-wholesale]

Environment:
    GATEWAY_URL     the gateway base URL (default http://127.0.0.1:8080)
    SMOKE_PRESET    the preset to scout (default austin-wholesale)
    SMOKE_OUT       where to write the JSON report (default contract/.out/smoke.json)
    SMOKE_TIMEOUT   seconds to wait for a terminal state (default 180)
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
    report["doors"] = len(doors)
    report["skips"] = len(skips)
    report["pitches"] = len(pitches)
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

    _write(report, failures)
    if failures:
        print("smoke: FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        f"smoke: ok - state={state} doors={len(doors)} skips={len(skips)} "
        f"pitches={len(pitches)} route={'skipped' if route.get('skipped') else 'built'}"
    )
    return 0


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
