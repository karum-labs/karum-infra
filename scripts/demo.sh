#!/usr/bin/env bash
# Turn the hackathon VM on or off, and publish the Flutter web build.
# Stopping the VM stops the CPU charge. The boot disk and karum-ip still
# bill a small amount until the VM and that address are deleted.
set -euo pipefail

# Product id, not whatever CLOUDSDK_CORE_PROJECT the shell inherited.
PROJECT="${KARUM_PROJECT:-karum-512016}"
ZONE="${KARUM_ZONE:-asia-south1-a}"
REGION="${KARUM_REGION:-asia-south1}"
INSTANCE="${KARUM_INSTANCE:-karum-demo}"
ADDRESS="${KARUM_ADDRESS:-karum-ip}"
CLIENT_URL="${KARUM_CLIENT_URL:-https://karum-512016.web.app}"

env -u CLOUDSDK_CORE_PROJECT gcloud config set project "$PROJECT" >/dev/null
export CLOUDSDK_CORE_PROJECT="$PROJECT"
echo "CLI project: $PROJECT"

api_host() {
  local ip
  ip="$(gcloud compute addresses describe "$ADDRESS" --region="$REGION" --project="$PROJECT" --format='value(address)')"
  echo "${ip}.sslip.io"
}

deploy_client() {
  local infra root client host
  infra="$(cd "$(dirname "$0")/.." && pwd)"
  root="$(cd "$infra/.." && pwd)"
  client="$root/karum-client"
  host="$(api_host)"
  if [[ ! -d "$client" ]]; then
    echo "missing client checkout: $client" >&2
    exit 1
  fi
  local -a flutter
  if [[ -x "$HOME/snap/flutter/common/flutter/bin/flutter" ]]; then
    flutter=("$HOME/snap/flutter/common/flutter/bin/flutter")
  else
    flutter=(flutter)
  fi
  export TMPDIR="${TMPDIR:-$HOME/.cache/karum-tmp/infra}"
  mkdir -p "$TMPDIR"
  (
    cd "$client"
    "${flutter[@]}" build web \
      --dart-define=GATEWAY_URL="https://${host}" \
      --dart-define=SHOW_JUDGES_BANNER=true
    if command -v firebase >/dev/null 2>&1; then
      firebase use "$PROJECT"
      firebase deploy --only hosting --project "$PROJECT"
    else
      npx --yes firebase-tools use "$PROJECT"
      npx --yes firebase-tools deploy --only hosting --project "$PROJECT"
    fi
  )
  echo "Client $CLIENT_URL"
  echo "API    https://${host}"
}

require_env() {
  python3 - "$1" << 'PY'
import sys
from pathlib import Path

# Each entry is a group of accepted spellings: the first one that carries a
# value satisfies the requirement. The model credential accepts both the
# documented AI_GEMINI_API_KEY and the legacy GEMINI_API_KEY.
needed = [
    ("POSTGRES_DSN",),
    ("GOOGLE_PLACES_API_KEY",),
    ("GOOGLE_ROUTES_API_KEY",),
    ("TASTE_QLOO_API_KEY",),
    ("AI_GEMINI_API_KEY", "GEMINI_API_KEY"),
]
vals = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    if not line.strip() or line.strip().startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    vals[key.strip()] = value.strip().strip("\"'")
missing = [group for group in needed if not any(vals.get(key) for key in group)]
if missing:
    print(
        "Fill these in karum-infra/.env before refresh: "
        + ", ".join(" or ".join(group) for group in missing),
        file=sys.stderr,
    )
    sys.exit(1)
PY
}

ensure_running() {
  local status
  status="$(gcloud compute instances describe "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --format='value(status)')"
  if [[ "$status" == "RUNNING" ]]; then
    return
  fi
  echo "VM is $status. Starting it first."
  gcloud compute instances start "$INSTANCE" --zone="$ZONE" --project="$PROJECT"
  for _ in $(seq 1 30); do
    status="$(gcloud compute instances describe "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --format='value(status)')"
    [[ "$status" == "RUNNING" ]] && return
    sleep 5
  done
  echo "VM did not reach RUNNING (last status: $status)" >&2
  exit 1
}

case "${1:-}" in
  on|start)
    gcloud compute instances start "$INSTANCE" --zone="$ZONE" --project="$PROJECT"
    echo "VM is starting. Docker brings the containers back."
    echo "API    https://$(api_host)"
    echo "Client $CLIENT_URL"
    ;;
  off|stop)
    gcloud compute instances stop "$INSTANCE" --zone="$ZONE" --project="$PROJECT"
    echo "VM stopped. CPU billing has stopped."
    echo "The boot disk and the reserved IP $ADDRESS still bill until you delete them."
    ;;
  status)
    gcloud compute instances describe "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --format='value(status)'
    ;;
  refresh)
    ensure_running
    remote_root="${KARUM_ROOT:-/opt/karum}"
    local_root="$(cd "$(dirname "$0")/../.." && pwd)"
    host="$(api_host)"
    if [[ ! -f "$local_root/karum-infra/.env" ]]; then
      echo "Missing $local_root/karum-infra/.env" >&2
      exit 1
    fi
    require_env "$local_root/karum-infra/.env"
    if [[ ! -x "$HOME/snap/flutter/common/flutter/bin/flutter" ]] && ! command -v flutter >/dev/null 2>&1; then
      echo "flutter is not on PATH" >&2
      exit 1
    fi
    if ! command -v firebase >/dev/null 2>&1 && ! command -v npx >/dev/null 2>&1; then
      echo "firebase CLI is not on PATH" >&2
      exit 1
    fi
    sync_tree() {
      local name="$1"
      local src="$local_root/$name"
      local dest="$remote_root/$name"
      if [[ ! -d "$src" ]]; then
        echo "missing local checkout: $src" >&2
        exit 1
      fi
      echo "sync $name"
      gcloud compute ssh "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --command="$(cat <<EOF
set -euo pipefail
dest=$(printf '%q' "$dest")
sudo mkdir -p "\$dest"
sudo find "\$dest" -mindepth 1 -maxdepth 1 ! -name .env -exec rm -rf {} +
EOF
)"
      tar -C "$src" \
        --exclude .git \
        --exclude .env \
        --exclude .local \
        --exclude .venv \
        --exclude __pycache__ \
        --exclude build \
        --exclude .dart_tool \
        --exclude node_modules \
        --exclude contract/.out \
        --exclude spike/out \
        -czf - . \
        | gcloud compute ssh "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --command="sudo tar -xzf - -C $(printf '%q' "$dest")"
    }
    for name in karum-infra karum-server karum-service-taste karum-service-ai; do
      sync_tree "$name"
    done
    remote_env="$remote_root/karum-infra/.env"
    echo "copy .env to the VM"
    gcloud compute scp "$local_root/karum-infra/.env" "$INSTANCE:/tmp/karum.env" --zone="$ZONE" --project="$PROJECT"
    gcloud compute ssh "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --command="sudo mv /tmp/karum.env $(printf '%q' "$remote_env") && sudo chmod 600 $(printf '%q' "$remote_env")"
    gcloud compute ssh "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --command="$(cat <<EOF
set -euo pipefail
envfile=$(printf '%q' "$remote_env")
host=$(printf '%q' "$host")
client_url=$(printf '%q' "$CLIENT_URL")
sudo python3 - "\$envfile" "\$host" "\$client_url" << 'PY'
import sys
from pathlib import Path
path, host, client_url = sys.argv[1:]
lines = Path(path).read_text().splitlines()
kept = [
    line
    for line in lines
    if not line.startswith("KARUM_API_HOST=")
    and not line.startswith("CLIENT_ORIGIN=")
]
kept.append(f"KARUM_API_HOST={host}")
kept.append(f"CLIENT_ORIGIN={client_url}")
Path(path).write_text("\n".join(kept) + "\n")
PY
cd $(printf '%q' "$remote_root/karum-infra")
sudo docker compose up -d --build --force-recreate --wait --wait-timeout 600
EOF
)"
    echo "waiting for https://${host}/health"
    ready=0
    for _ in $(seq 1 36); do
      if curl -fsS -m 10 "https://${host}/health" >/dev/null; then
        ready=1
        break
      fi
      sleep 5
    done
    if [[ "$ready" != 1 ]]; then
      echo "API did not become healthy at https://${host}/health" >&2
      exit 1
    fi
    echo "API    https://${host}"
    deploy_client
    ;;
  *)
    echo "Usage: $0 on|off|status|refresh" >&2
    exit 1
    ;;
esac
