#!/usr/bin/env bash
# Start taste, AI, the gateway, and the Flutter client on this machine.
# No Docker. Postgres is POSTGRES_DSN from .env. Redis is the in-process cache.
set -euo pipefail

INFRA="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$INFRA/.." && pwd)"
RUN="$INFRA/.local"
# /tmp is a small RAM disk; go run and the Flutter compiler overflow it.
# Keep the path short: Chrome puts a Unix socket in TMPDIR, capped at 108 bytes.
TMP_ROOT="$HOME/.cache/karum-tmp/infra"
mkdir -p "$RUN/logs" "$TMP_ROOT"
export TMPDIR="$TMP_ROOT"

if [[ -f "$RUN/pids" ]]; then
  echo "Local stack is already running. Stop it with Ctrl+C in that terminal, or: make local-down" >&2
  exit 1
fi

if [[ ! -f "$INFRA/.env" ]]; then
  echo "Missing $INFRA/.env — copy .env.example and set POSTGRES_DSN." >&2
  exit 1
fi

python3 - "$INFRA/.env" "$RUN/env" << 'PY'
import shlex
import sys
from pathlib import Path

src, dest = sys.argv[1:]
lines = Path(src).read_text().splitlines()
pairs = []
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip() or line.strip().startswith("#") or "=" not in line:
        i += 1
        continue
    key, value = line.split("=", 1)
    key = key.strip()
    if value.startswith('"') and not (len(value) > 1 and value.endswith('"')):
        i += 1
        while i < len(lines) and not lines[i].rstrip().endswith('"'):
            i += 1
        value = ""
    elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    pairs.append((key, value))
    i += 1

# Laptop addresses. The demo VM's Compose file points these at service names.
overrides = {
    "GATEWAY_PORT": "8080",
    "TASTE_ADDR": "127.0.0.1:8081",
    "AI_ADDR": "127.0.0.1:8082",
    "TASTE_PORT": "8081",
    "TASTE_HOST": "127.0.0.1",
    "AI_PORT": "8082",
    "AI_HOST": "127.0.0.1",
    "TASTE_REDIS_ADDR": "",
}
seen = set()
out = []
for key, value in pairs:
    if key in overrides:
        value = overrides[key]
        seen.add(key)
    out.append(f"export {key}={shlex.quote(value)}")
for key, value in overrides.items():
    if key not in seen:
        out.append(f"export {key}={shlex.quote(value)}")
Path(dest).write_text("\n".join(out) + "\n")
Path(dest).chmod(0o600)
PY

set -a
# shellcheck disable=SC1091
source "$RUN/env"
set +a

# Flutter web dev server port. Override with WEB_PORT=8091 if 8090 is in use.
WEB_PORT="${WEB_PORT:-8090}"

if [[ -z "${POSTGRES_DSN:-}" ]]; then
  echo "POSTGRES_DSN is empty in $INFRA/.env" >&2
  exit 1
fi

if [[ "$(command -v flutter)" == /snap/bin/flutter && -x "$HOME/snap/flutter/common/flutter/bin/flutter" ]]; then
  FLUTTER=("$HOME/snap/flutter/common/flutter/bin/flutter")
elif command -v flutter >/dev/null 2>&1; then
  FLUTTER=(flutter)
else
  echo "flutter is not on PATH" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not on PATH" >&2
  exit 1
fi
if ! command -v go >/dev/null 2>&1; then
  echo "go is not on PATH" >&2
  exit 1
fi

busy=()
for port in 8080 8081 8082; do
  if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
    busy+=("$port")
  fi
done
if [[ ${#busy[@]} -gt 0 ]]; then
  echo "Ports already in use: ${busy[*]}. Run: make local-down" >&2
  exit 1
fi

cleaned=0
cleanup() {
  if [[ "$cleaned" == 1 ]]; then
    return
  fi
  cleaned=1
  trap - INT TERM HUP EXIT
  if [[ -f "$RUN/pids" ]]; then
    while read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    done <"$RUN/pids"
    rm -f "$RUN/pids"
  fi
  rm -rf "$TMP_ROOT"
}
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
trap 'cleanup; exit 129' HUP
trap cleanup EXIT

launch() {
  local name="$1" dir="$2"
  shift 2
  python3 - "$dir" "$RUN/logs/$name.log" "$@" << 'PY' &
import os, sys
directory, log, *cmd = sys.argv[1:]
os.setsid()
os.chdir(directory)
fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
os.dup2(fd, 1)
os.dup2(fd, 2)
os.execvp(cmd[0], cmd)
PY
  echo $! >>"$RUN/pids"
  echo "started $name (pid $!, log .local/logs/$name.log)"
}

launch taste "$ROOT/karum-service-taste" uv run python -m karum_service_taste
launch ai "$ROOT/karum-service-ai" uv run python -m karum_service_ai
launch gateway "$ROOT/karum-server" go run ./cmd/gateway
GATEWAY_PID=$(tail -n 1 "$RUN/pids")

echo "waiting for http://127.0.0.1:8080/health"
ready=0
for _ in $(seq 1 180); do
  if ! kill -0 "$GATEWAY_PID" 2>/dev/null; then
    break
  fi
  if curl -sf -m 2 http://127.0.0.1:8080/health >/dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "Gateway did not become healthy. See .local/logs/gateway.log" >&2
  exit 1
fi

echo
echo "Gateway    http://127.0.0.1:8080"
echo "Taste      http://127.0.0.1:8081/health"
echo "AI         http://127.0.0.1:8082/health"
echo

if [[ "${NO_CLIENT:-0}" == 1 ]]; then
  echo "Client skipped (NO_CLIENT=1). Ctrl+C stops the backends."
  wait
  exit 0
fi

echo "This terminal stays attached. Ctrl+C stops the client and the backends."
cd "$ROOT/karum-client"
maps_define=()
if [[ -n "${GOOGLE_MAPS_WEB_KEY:-}" ]]; then
  maps_define+=(--dart-define=GOOGLE_MAPS_WEB_KEY="$GOOGLE_MAPS_WEB_KEY")
fi
# Google's referrer check does not treat a port wildcard as a port, so the
# Maps key allows this fixed origin. Gateway stays on 8080.
"${FLUTTER[@]}" run -d chrome \
  --web-hostname=localhost \
  --web-port="$WEB_PORT" \
  --dart-define=GATEWAY_URL=http://127.0.0.1:8080 \
  "${maps_define[@]}"
