# karum-infra

Shared **protos, the laptop run path, the demo VM, and toolchain pins** for [Karum](#readme) — the brand-operated expansion agent: a brand seed and a city go in, and doors, flagship corridors, collab partners, skip reasons, menu audits, and a field route come out.

Karum reads the cultural taste of a city via **Qloo**, scores candidate doors on **affinity, shelf opportunity, and demographic alignment**, then drafts the shopkeeper pitch, battlecard, and field route with **Vertex AI**. A wrong door is a lost account.

## The five-repo layout

| Repo | Role |
| --- | --- |
| **`karum-infra`** (this repo) | Shared protos, demo VM Compose, Firebase deploy, fixture pack, Makefile, toolchain pins |
| [`karum-client`](https://github.com/karum-labs/karum-client) | Flutter UI (web is the judge target; same screens on desktop) |
| [`karum-server`](https://github.com/karum-labs/karum-server) | Go + Gin API gateway — geocoding, job orchestration, SSE, persistence |
| [`karum-service-taste`](https://github.com/karum-labs/karum-service-taste) | Qloo integration, entity resolution, caching, taste scoring |
| [`karum-service-ai`](https://github.com/karum-labs/karum-service-ai) | Vertex AI, Google Search grounding, pitch drafting |

```text
[ Flutter Client ]
        │  POST /api/v1/scout
        ▼
[ Go Gateway (karum-server) ]
        ├── gRPC ──► [ service-taste ] ──► Qloo API
        ├── HTTP ──► Google Places API
        ├── gRPC ──► [ service-ai ] ──► Vertex AI + Search
        └── HTTP ──► Google Routes API
        ▼
  Ranked shortlist, evidence, and drafts back to the client
```

## What lives here

- **`proto/`** — the shared protobuf definitions and buf configuration. `karum.health.v1` is the process health contract; `karum.common.v1`, `karum.taste.v1`, and `karum.agent.v1` are the domain contracts (shared primitives and evidence, taste RPCs, AI RPCs). Every domain field carries a provenance marker — `Qloo fact:`, `Google fact:`, `Model inference:`, or `Input:` — enforced by `make check-proto-docs`.
- **`contract/`** — the stub contract test: the Austin campaign fixtures, the Go round-trip runner, and the Python relay that parses Go-emitted binaries with the Python stubs (see [contract/README.md](contract/README.md)).
- **`tools/doccheck/`** — the provenance-marker checker used by `make check-proto-docs`, with its own tests.
- **`QLOO_APIS.md`** — every Qloo endpoint Karum may call with exact parameters, mapped to PLAN epics, plus the spike checklist for the open questions.
- **`QLOO_USE_CASES.md`** — the plain-language map of where Karum uses Qloo today (each call, its epic, its watch-outs) plus suggested additional use cases, grouped by build cost and spike gates.
- **`spike/`** — the epic-9 probe runner (`run_spike.py`, stdlib-only) and recording sheet that work the QLOO_APIS.md §5 checklist against the hackathon host; raw responses stay local in `spike/out/`.
- **`docker-compose.yml`** — the demo VM only. Caddy, gateway, taste, AI, and Redis. Postgres is the `POSTGRES_DSN` URI, not a container.
- **`scripts/local-up.sh`** — the laptop path: the same processes, no Docker.
- **`scripts/demo.sh`** — start, stop, or refresh the `karum-demo` VM and publish the Flutter web build to Firebase Hosting.
- **`.env.example`** — every environment variable and which process reads it.
- **`versions.env`** — the single source of truth for Go, Python, Flutter, and buf versions.
- **`Makefile`** — `local`, `demo-on`, `demo-off`, `demo-refresh`, plus proto tooling.
- **`.gitleaks.toml`** — secret-scan rules tuned to catch a committed Qloo key or GCP credential.

## Run path

Copy `.env.example` to `.env` and set `POSTGRES_DSN`. The laptop does not use Docker.

```bash
cp .env.example .env

# Taste, AI, the gateway, and Flutter, on this machine.
make local

# Backends only.
make local-api

# Stop them.
make local-down
```

| Process | URL |
| --- | --- |
| gateway | http://127.0.0.1:8080 |
| service-taste | http://127.0.0.1:8081/health |
| service-ai | http://127.0.0.1:8082/health |

Logs are `.local/logs/`. `make local` opens Flutter itself, with `GATEWAY_URL=http://127.0.0.1:8080`.

ADC comes from `~/Projects/Karum/.envrc` (`GOOGLE_APPLICATION_CREDENTIALS`). `make demo-on` also points the gcloud CLI at project `karum-512016` before it touches the VM.

## Demo VM

Project `karum-512016`, zone `asia-south1-a`, instance `karum-demo` (`e2-medium`, Ubuntu 24.04). Firebase Hosting for the client is https://karum-512016.web.app. The API is https://35.244.55.185.sslip.io, served by Caddy on the VM.

```bash
make demo-on       # start the VM
make demo-status
make demo-refresh  # sync this checkout, rebuild containers, publish the client
make demo-off      # stop the CPU charge
```

`docker compose` runs only on that VM. The first refresh copies `karum-infra/.env` up if the VM does not have one yet, and leaves an existing VM `.env` in place.

## Toolchain versions

[`versions.env`](versions.env) pins every toolchain so the five repos read one source of truth:

| Tool | Pin |
| --- | --- |
| Go | `1.27.2` |
| Python | `3.13` |
| uv | `0.13.1` |
| Flutter | `3.47.6` |
| Dart | `3.13.5` |
| buf | `1.73.0` |

## Working with the protos

```bash
make lint-proto       # buf lint (STANDARD + COMMENTS)
make generate         # emit Go + Python stubs into gen/ (pinned BSR plugins)
make check-proto-docs # enforce field provenance markers
make contract-test    # round-trip a campaign through both stub sets
make breaking         # buf breaking against origin/main
```

CI runs `buf lint`, a `buf breaking` check against `main`, and a contract job on every proto change: it regenerates the stubs inside the pinned `bufbuild/buf` container, enforces the provenance markers, and round-trips the Austin campaign through the generated Go and Python stubs. Gitleaks scans every push.

## Honesty rules

These apply across all five repos:

- An `unresolved` or `empty` result is rendered as a miss — never a guessed fill-in.
- Undocumented Qloo parameters stay out of client code, fixtures, and prompts.
- Degraded autopilot is visible both as the job state and in `GET /health`.
- Evidence snapshots are frozen when a run completes; later cache updates do not rewrite history.

## Ownership

Karum is a two-person build — the full record is in [`DECISIONS.md`](DECISIONS.md). **Side A** owns taste, score, agent, and eval; **side B** owns UI, map, drafts, deploy, and Devpost. This repo is shared between them: `proto/` is side A's contract with side B's sign-off, while Compose, Cloud Run, the Makefile, and the fixture pack are side B's. Any change under `proto/` needs a word from both sides first.

## Licence

MIT. See [`LICENSE`](LICENSE).
