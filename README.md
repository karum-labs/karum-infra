# karum-infra

Shared **protos, local Docker Compose, toolchain pins, and Cloud Run manifests** for [Karum](#readme) — the brand-operated expansion agent: a brand seed and a city go in, and doors, flagship corridors, collab partners, skip reasons, menu audits, and a field route come out.

Karum reads the cultural taste of a city via **Qloo**, scores candidate doors on **affinity, shelf opportunity, and demographic alignment**, then drafts the shopkeeper pitch, battlecard, and field route with **Vertex AI**. A wrong door is a lost account.

## The five-repo layout

| Repo | Role |
| --- | --- |
| **`karum-infra`** (this repo) | Shared protos, Compose, Cloud Run, fixture pack, Makefile, toolchain pins |
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
- **`docker-compose.yml`** — the local stack (gateway, taste, AI, Redis) with healthchecks and a deterministic startup order. Postgres is the `POSTGRES_DSN` URI, not a container.
- **`.env.example`** — every environment variable and which process reads it.
- **`versions.env`** — the single source of truth for Go, Python, Flutter, and buf versions.
- **`Makefile`** — `up`, `down`, `test`, `prewarm`, `eval`, plus proto tooling: `lint-proto`, `breaking`, `generate`, `check-proto-docs`, `contract-test`.
- **`.gitleaks.toml`** — secret-scan rules tuned to catch a committed Qloo key or GCP credential.

## Run path

Requires **Docker** with the Compose plugin. Copy `.env.example` to `.env` and set `POSTGRES_DSN` before starting; Compose refuses to boot without that URI.

```bash
cp .env.example .env

# Build and start the full stack.
make up

# Follow logs.
make logs

# Stop the stack.
make down
```

### Host ports

| Service | Host port | Notes |
| --- | --- | --- |
| **gateway** | `8080` | The only service published to the host. Flutter web points here. |
| service-taste | — | In-stack only (gRPC `8081`) |
| service-ai | — | In-stack only (gRPC `8082`) |
| redis | — | In-stack only (`6379`) |

Confirm the gateway is healthy:

```bash
curl http://localhost:8080/health
```

### Where logs go

`docker compose logs -f` follows the combined stack output. Each service logs structured JSON to stdout, so `docker compose logs -f gateway` (or `service-taste`, `service-ai`) tails one process. Credentials are never logged.

### Pointing Flutter web at the gateway

The client reads its gateway base URL from `--dart-define`, so switching between local Compose and production is a build flag, not a code change:

```bash
cd ../karum-client
flutter run -d chrome --dart-define=GATEWAY_URL=http://localhost:8080
```

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
