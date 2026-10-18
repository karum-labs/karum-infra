#!/usr/bin/env bash
set -euo pipefail

INFRA="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$INFRA/.." && pwd)"
PIDS="$INFRA/.local/pids"
stopped=0

if [[ -f "$PIDS" ]]; then
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    stopped=1
  done <"$PIDS"
  rm -f "$PIDS"
fi

# go run and uvicorn can outlive the pid file. Only stop listeners whose
# working directory is this Karum checkout.
for port in 8080 8081 8082; do
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
    if [[ "$cwd" != "$ROOT"* ]]; then
      continue
    fi
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    stopped=1
  done < <(ss -ltnpH "sport = :$port" 2>/dev/null | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u)
done

rm -rf "$HOME/.cache/karum-tmp/infra"

if [[ "$stopped" == 1 ]]; then
  echo "Stopped local stack."
else
  echo "Local stack is not running."
fi
