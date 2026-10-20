# karum-infra — protos, the laptop stack, and the demo VM.
#
# `make local` starts taste, AI, the gateway, and Flutter on this machine.
# Docker Compose is only what `make demo-refresh` runs on the demo VM.
#
# The prewarm and eval targets are stubs until the sample-block fixtures and
# the leave-one-out harness land (PLAN.md §39 and §40).
#
# Proto tooling: `make generate` emits the Go and Python stubs; `make
# check-protos` runs lint, the provenance-marker check, and the cross-language
# contract test. CI runs the generate step inside Docker (PLAN.md §4);
# `make generate-docker` is the local equivalent.
#
# Fixture tooling: `make redact-fixtures` regenerates the redacted pack from
# local recordings (spike/out/, git-ignored); `make check-fixtures` verifies
# hashes and preset schemas without recordings; `make test-fixtures` runs the
# projection tests.

include versions.env

COMPOSE ?= docker compose
BUF ?= buf
GO ?= go
CONTRACT_OUT ?= contract/.out
BUF_DOCKER_IMAGE ?= bufbuild/buf:$(BUF_VERSION)

# Prefer the repo venv for the Python half of the contract test when it exists
# (protobuf==7.36.2 lives there; see contract/pyrelay/requirements.txt).
VENV_PYTHON := $(firstword $(wildcard .venv/Scripts/python.exe) $(wildcard .venv/bin/python))
PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python)

.PHONY: help up down logs local local-api local-down demo-on demo-off demo-status demo-refresh test prewarm eval lint-proto breaking generate generate-docker generate-stubs check-proto-docs contract-test check-protos redact-fixtures check-fixtures test-fixtures check-presets spike

## help: list available targets.
help:
	@python -c "import re,sys;print(*re.findall(r'^## (.*)',open(sys.argv[1],encoding='utf-8').read(),re.M),sep=chr(10))" "$(firstword $(MAKEFILE_LIST))"

## local: start taste, AI, the gateway, and Flutter on this machine (no Docker).
local:
	./scripts/local-up.sh

## local-api: same backends, without opening the Flutter client.
local-api:
	NO_CLIENT=1 ./scripts/local-up.sh

## local-down: stop the processes `make local` started.
local-down:
	./scripts/local-down.sh

## demo-on: start the demo VM. Docker brings the containers back.
demo-on:
	./scripts/demo.sh on

## demo-off: stop the demo VM. CPU billing stops; the disk and IP remain.
demo-off:
	./scripts/demo.sh off

## demo-status: print RUNNING or STOPPED.
demo-status:
	./scripts/demo.sh status

## demo-refresh: sync this checkout and .env onto the VM, rebuild containers, publish the client.
demo-refresh:
	./scripts/demo.sh refresh

## up: build the demo Compose stack. Used on the VM, not for laptop development.
up:
	$(COMPOSE) up --build -d
	@echo "Waiting for services to become healthy..."
	@$(COMPOSE) ps

## down: stop the demo Compose stack and remove its containers.
down:
	$(COMPOSE) down

## logs: follow the demo Compose stack's combined logs.
logs:
	$(COMPOSE) logs -f

## test: run the smoke test against the running stack (fixture mode).
test:
	@echo "TODO(smoke): post the Austin preset in fixture mode and assert a door list, a skip list, and a route."
	@echo "Stack status:"
	@$(COMPOSE) ps

## prewarm: run all four presets end-to-end on the deployed gateway and refresh
## the stored runs so a preset click serves the newest ready stored run
## (PLAN.md §13, §25, and §39). Requires PREWARM_TOKEN: a judge session
## token from POST /api/v1/auth/judge (or /auth/login) on the target gateway.
## Set GATEWAY_URL for the deployed host; the laptop default is localhost:8080.
prewarm:
	@test -n "$(PREWARM_TOKEN)" || { echo "prewarm: set PREWARM_TOKEN to a judge session token"; exit 1; }
	@echo "Prewarming the four presets on ${GATEWAY_URL:-http://localhost:8080} ..."
	@curl -fsS -X POST "${GATEWAY_URL:-http://localhost:8080}/api/v1/prewarm?refresh=true" \
		-H "Authorization: Bearer $(PREWARM_TOKEN)"
	@echo "Pre-warm complete; preset clicks serve the newest ready stored run."

## eval: run the leave-one-out harness across ~20 blocks.
eval:
	@echo "TODO(eval): run Karum vs LlmOnlyBaseline on ~20 blocks and write the table."
	@echo "Not implemented until the scoring rubric and baseline land (PLAN.md §40)."

## lint-proto: lint the shared protos with buf.
lint-proto:
	cd proto && $(BUF) lint

## breaking: check the protos against origin/main for breaking changes.
breaking:
	@python scripts/breaking.py --buf "$(BUF)"

## generate: emit Go and Python stubs from the shared protos (pinned BSR plugins).
generate:
	cd proto && $(BUF) generate

## generate-stubs: refresh the committed stubs in the sibling repos.
# The stubs that ship in karum-server/internal/pb, karum-service-ai/src, and
# karum-service-taste/src come from karum-server/buf.gen.yaml, so the command
# runs from that checkout. `make generate` in this repo writes a throwaway
# copy under gen/ for the contract test.
generate-stubs:
	cd ../karum-server && $(BUF) generate

## generate-docker: emit stubs inside the pinned buf container (the CI path).
generate-docker:
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace/proto $(BUF_DOCKER_IMAGE) generate

## check-proto-docs: enforce the Qloo-fact / model-inference markers on every domain field.
check-proto-docs:
	@python -c "import pathlib; pathlib.Path('gen').mkdir(exist_ok=True)"
	cd proto && $(BUF) build --as-file-descriptor-set -o ../gen/descriptor.binpb
	$(GO) run ./tools/doccheck gen/descriptor.binpb

## contract-test: round-trip the sample campaign through the Go and Python stubs (needs `make generate`).
contract-test:
	@python -c "import pathlib; pathlib.Path('$(CONTRACT_OUT)').mkdir(parents=True, exist_ok=True)"
	$(GO) run ./contract/roundtrip emit contract/testdata/campaign $(CONTRACT_OUT)
	$(PYTHON) contract/pyrelay/roundtrip.py contract/testdata/campaign $(CONTRACT_OUT)
	$(GO) run ./contract/roundtrip verify contract/testdata/campaign $(CONTRACT_OUT)

## check-protos: lint, doc markers, and the stub contract test (run `make generate` first).
check-protos: lint-proto check-proto-docs contract-test

## redact-fixtures: regenerate the fixture pack from local recordings (needs spike/out/).
redact-fixtures:
	$(PYTHON) fixtures/tools/redact.py

## check-fixtures: verify fixture hashes and preset schemas (CI-safe; no recordings needed).
check-fixtures:
	$(PYTHON) fixtures/tools/redact.py --verify

## test-fixtures: unit-test the redaction projections.
# Invoke a script (fixtures/tools/run_tests.py) instead of `python -c "..."`:
# make's Windows shell (cmd.exe) mangles `python -c "..."` with a leading
# `.venv` segment, treating `.venv` as a separate command. A script path --
# the same shape `make check-fixtures` already uses for `redact.py` -- works.
# The venv python is still required for the pinned protobuf (see versions.env).
test-fixtures:
	$(PYTHON) fixtures/tools/run_tests.py

## check-presets: compare the three copies of the locked presets (local; needs the siblings).
# The recorded scenarios, the gateway's catalogue, and the client's mirror must
# agree. A source that is not checked out is skipped, never guessed.
check-presets:
	$(PYTHON) fixtures/tools/check_presets.py

## spike ARGS="key": run the Qloo spike runner (see spike/README.md).
spike:
	python spike/run_spike.py $(ARGS)
