# karum-infra

Shared **protos, local Docker Compose, toolchain pins, and Cloud Run manifests** for [Karum](#readme) — a tenant-mix leasing agent that tells retail landlords what an empty storefront should become.

Karum reads the cultural taste of a surrounding block via **Qloo**, scores candidate tenants on **catchment fit** and **co-tenancy complement**, then drafts the leasing memo and outreach with **Vertex AI**. A wrong tenant is a multi-year mistake.

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
        │  POST /api/v1/analyses
        ▼
[ Go Gateway (karum-server) ]
        ├── gRPC ──► [ service-taste ] ──► Qloo API
        ├── HTTP ──► Google Places API
        ├── gRPC ──► [ service-ai ] ──► Vertex AI + Search
        └── HTTP ──► Google Routes API
        ▼
  Complete campaign run-sheet back to the client
```

## What lives here

- **`proto/`** — the shared protobuf definitions and buf configuration. `karum.health.v1` is the placeholder contract the two microservices implement; the domain protos (vacancy, tags, scoring, taste RPCs, AI RPCs) land in a later pass.
- **`docker-compose.yml`** — the full local stack (gateway, taste, AI, Redis, Postgres) with healthchecks and a deterministic startup order.
- **`.env.example`** — every environment variable and which process reads it.
- **`versions.env`** — the single source of truth for Go, Python, Flutter, and buf versions.
- **`Makefile`** — `up`, `down`, `test`, `prewarm`, `eval`, plus proto `lint-proto`, `breaking`, and `generate`.
- **`.gitleaks.toml`** — secret-scan rules tuned to catch a committed Qloo key or GCP credential.

## Run path

Requires **Docker** with the Compose plugin. All services boot in **fixture mode** with no credentials, so the whole stack starts with no `.env` file.

```bash
# Optional: create a .env to override defaults (e.g. to go live).
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
| postgres | — | In-stack only (`5432`) |

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
| Go | `1.26.0` |
| Python | `3.13` |
| uv | `0.13.1` |
| Flutter | `3.47.6` |
| Dart | `3.13.5` |
| buf | `1.73.0` |

## Working with the protos

```bash
make lint-proto   # buf lint
make generate     # emit Go + Python stubs into proto/gen/
make breaking     # buf breaking against origin/main
```

CI runs `buf lint` and a `buf breaking` check against `main` on every proto change, plus a gitleaks secret scan on every push.

## Honesty rules

These apply across all five repos:

- An `unresolved` or `empty` result is rendered as a miss — never a guessed fill-in.
- Undocumented Qloo parameters stay out of client code, fixtures, and prompts.
- Degraded autopilot is visible both as the job state and in `GET /health`.
- Evidence snapshots are frozen when a run completes; later cache updates do not rewrite history.

## Licence

MIT. See [`LICENSE`](LICENSE).
