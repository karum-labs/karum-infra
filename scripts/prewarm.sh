#!/usr/bin/env bash
# Pre-warm the four presets on the running gateway.
#
# POST /api/v1/prewarm?refresh=true refreshes the stored runs so a preset click
# serves the newest ready stored run (PLAN.md §13, §25, §39). Requires
# PREWARM_TOKEN: a judge session token from POST /api/v1/auth/judge (or
# /auth/login) on the target gateway.
#
# The endpoint returns one row per preset. This script fails unless every row is
# both stored and `ready`; a `degraded` row is visible but is not treated as a
# successful prewarm.
#
# Environment:
#   PREWARM_TOKEN  the judge session token (required)
#   GATEWAY_URL    the gateway base URL (default http://localhost:8080)
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
TOKEN="${PREWARM_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
  echo "prewarm: set PREWARM_TOKEN to a judge session token" >&2
  exit 1
fi

echo "Prewarming the four presets on ${GATEWAY_URL} ..."
response="$(curl -fsS -X POST "${GATEWAY_URL}/api/v1/prewarm?refresh=true" \
  -H "Authorization: Bearer ${TOKEN}")"
printf '%s\n' "$response"

if ! printf '%s' "$response" | python3 -c '
import json
import sys

data = json.load(sys.stdin)
presets = data.get("presets", [])
bad = [p for p in presets if p.get("state") != "ready" or not p.get("stored")]
if not presets:
    print("prewarm: the response contained no presets", file=sys.stderr)
    raise SystemExit(1)
for preset in bad:
    name = preset.get("preset", "?")
    state = preset.get("state", "unknown")
    error = preset.get("error", "")
    print(f"prewarm: {name} is {state}" + (f": {error}" if error else ""), file=sys.stderr)
raise SystemExit(1 if bad else 0)
'; then
  echo "prewarm: at least one preset did not reach ready" >&2
  exit 1
fi

echo "Pre-warm complete; all presets are ready."
