# Secrets and the judge account

The public demo never needs a login. `HACKATHON_MODE=true` only adds an
automatic judge session on top of the anonymous demo; `/login` stays available
and an anonymous visitor can still build a seed, run a scout, open a door, and
download the run sheet.

## Local development

`karum-infra/.env` is git-ignored and is the only place the plaintext password
should live on a laptop.

```dotenv
HACKATHON_MODE=true
JUDGE_EMAIL=judge@karum.demo
JUDGE_PASSWORD=replace-me
JUDGE_DISPLAY_NAME=Karum Judge
```

The gateway hashes `JUDGE_PASSWORD` with bcrypt at startup and stores only the
hash in `accounts.password_hash`. It never writes the plaintext to Postgres or
to a log. `POST /api/v1/auth/judge` is enabled only while the flag is true.

## Production: Secret Manager

The production deployment is the Compute Engine VM described in
[README.md](README.md). Use Google Secret Manager as the source of truth and
hydrate the VM's `.env` at deploy time; do not commit the values.

### 1. Create the secrets

Run these once in the project that owns the demo VM. The commands read values
from your local environment so the plaintext does not appear in shell history.

```bash
export PROJECT=karum-512016

gcloud services enable secretmanager.googleapis.com --project "$PROJECT"

printf '%s' "$JUDGE_EMAIL" |
  gcloud secrets create karum-judge-email \
    --data-file=- --replication-policy=automatic --project "$PROJECT"

printf '%s' "$JUDGE_PASSWORD" |
  gcloud secrets create karum-judge-password \
    --data-file=- --replication-policy=automatic --project "$PROJECT"
```

If a secret already exists, add a new version instead of creating it again:

```bash
printf '%s' "$JUDGE_PASSWORD" |
  gcloud secrets versions add karum-judge-password \
    --data-file=- --project "$PROJECT"
```

Grant the identity that runs the deploy access to both secrets:

```bash
for secret in karum-judge-email karum-judge-password; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:YOUR_DEPLOY_SERVICE_ACCOUNT@$PROJECT.iam.gserviceaccount.com" \
    --role=roles/secretmanager.secretAccessor \
    --project "$PROJECT"
done
```

### 2. Hydrate `.env` before a deploy

```bash
export JUDGE_EMAIL="$(gcloud secrets versions access latest \
  --secret=karum-judge-email --project "$PROJECT")"
export JUDGE_PASSWORD="$(gcloud secrets versions access latest \
  --secret=karum-judge-password --project "$PROJECT")"

# Put the values into the local .env that demo-refresh copies to the VM.
python - "$JUDGE_EMAIL" "$JUDGE_PASSWORD" <<'PY'
import sys
from pathlib import Path

path = Path("karum-infra/.env")
email, password = sys.argv[1:]
lines = [
    line for line in path.read_text().splitlines()
    if not line.startswith(("JUDGE_EMAIL=", "JUDGE_PASSWORD=", "HACKATHON_MODE="))
]
lines += [f"JUDGE_EMAIL={email}", f"JUDGE_PASSWORD={password}", "HACKATHON_MODE=true"]
path.write_text("\n".join(lines) + "\n")
PY

make demo-refresh
```

`scripts/demo.sh` copies the assembled `.env` over SSH, stores it mode `600` on
the VM, and never sends it to Git or the browser. The plaintext exists only in
Secret Manager, the operator's environment, and that protected VM file.

### 3. Rotate the password

1. Add a new Secret Manager version with `gcloud secrets versions add`.
2. Re-run `make demo-refresh`.
3. On startup the gateway's `EnsureJudge` updates `accounts.password_hash` to the
   new bcrypt hash. Existing opaque sessions remain valid until `SESSION_TTL`;
   to revoke them immediately, delete the judge's rows from `sessions` (or bump
   the account id).

The active account in this development environment cannot read project
`karum-512016` (the Secret Manager API is also disabled there), so the secrets
above still need to be created by an operator with project access. The local
demo uses `.env` and is fully functional.

## Prewarm token

`POST /api/v1/prewarm` requires a judge session. Obtain one from the target
gateway; never put a long-lived token in a checked-in file.

```bash
TOKEN="$(curl -fsS -X POST https://YOUR_GATEWAY/api/v1/auth/judge | jq -r .token)"
make prewarm GATEWAY_URL=https://YOUR_GATEWAY PREWARM_TOKEN="$TOKEN"
```

The Make target calls `POST /api/v1/prewarm?refresh=true` once, which runs all
four locked presets end-to-end. The stored run keeps its trace, evidence,
heatmap, and route so a later preset click serves it without re-running Qloo.
