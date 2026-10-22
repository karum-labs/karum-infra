# karum-infra — protos, the laptop stack, and the demo VM.
#
# `make local` starts taste, AI, the gateway, and Flutter on this machine.
# Docker Compose is only what `make demo-refresh` runs on the demo VM.
#
# The eval target is a stub until the leave-one-out harness lands (PLAN.md
# §40); `make prewarm` is real and posts the gateway's /api/v1/prewarm on the
# target host (PREWARM_TOKEN required).
#
# Proto tooling: `make generate` emits the Go and Python stubs; `make
# check-protos` runs lint, the provenance-marker check, and the cross-language
# contract test. CI runs the generate step inside Docker (PLAN.md §4);
# `make generate-docker` is the local equivalent.
#
# Fixture tooling: `make redact-fixtures` regenerates the redacted pack from
# local recordings (spike/out/, git-ignored); `make check-fixtures` verifies
# hashes, preset schemas, and the AI pack's derivation; `make test-fixtures`
# runs the projection tests.

include versions.env

COMPOSE ?= docker compose
BUF ?= buf
GO ?= go
CONTRACT_OUT ?= contract/.out
BUF_DOCKER_IMAGE ?= bufbuild/buf:$(BUF_VERSION)

# Prefer the repo venv for the Python half of the contract test when it exists
# (protobuf==7.36.2 lives there; see contract/pyrelay/requirements.txt).
#
# The venv is host-specific: .venv/Scripts/python.exe is a Windows venv and
# .venv/bin/python is a POSIX one. Under WSL and on Linux the repo venv may
# not be usable, so `make venv` builds one under KARUM_VENV with the pinned
# protobuf.
KARUM_VENV ?= $(HOME)/.cache/karum-infra-venv

ifeq ($(OS),Windows_NT)
  VENV_PYTHON := $(firstword $(wildcard .venv/Scripts/python.exe))
  DEFAULT_PYTHON := python
else
  VENV_PYTHON := $(firstword $(wildcard $(KARUM_VENV)/bin/python) $(wildcard .venv/bin/python))
  # python3 is the name on Linux and WSL; python is the fallback for hosts
  # that only ship the unversioned one.
  DEFAULT_PYTHON := $(firstword $(shell command -v python3 2>/dev/null) $(shell command -v python 2>/dev/null) python3)
endif

PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),$(DEFAULT_PYTHON))

# The shell scripts run under WSL when make runs on Windows. WSL carries the
# whole laptop toolchain (bash, uv, go, flutter), so `make local` starts the
# same stack on either host. On a POSIX host (Linux, WSL, macOS) they run under
# the local shell.
#
# WSL_RUN holds the command prefix; POSIX_PYTHON is the interpreter the
# delegated commands use (a WSL-side python, not the Windows one).
ifeq ($(OS),Windows_NT)
  WSL ?= wsl.exe
  WSL_RUN = $(WSL) --cd "$(CURDIR)" -- bash -lc
  POSIX_PYTHON ?= python3
  # Windows environment variables do not cross into WSL unless WSLENV lists
  # them; the prewarm target needs the judge token on the WSL side. A
  # trailing ";" in WSLENV makes WSL drop the whole list, so the value is
  # replaced rather than appended to.
  WSL_ENV = set "WSLENV=PREWARM_TOKEN" &&
else
  WSL_RUN = bash -lc
  POSIX_PYTHON ?= $(PYTHON)
  WSL_ENV =
endif

# The toolchain lives on the user's PATH: a login shell (bash -lc) picks up
# ~/.profile, which is where uv (~/.local/bin) and Flutter are installed.

.PHONY: help up down logs local local-api local-down local-status venv demo-on demo-off demo-status demo-refresh test prewarm eval lint-proto breaking generate generate-docker generate-stubs check-proto-docs contract-test check-protos redact-fixtures check-fixtures test-fixtures check-presets spike

## help: list available targets.
# A target's description may span several `## ` lines; they are merged into one
# entry so the list reads as a list of targets, not as a list of fragments.
help:
	@$(PYTHON) scripts/help.py $(firstword $(MAKEFILE_LIST))

## local: start taste, AI, the gateway, and Flutter on this machine (no Docker).
local:
	$(WSL_RUN) "bash ./scripts/local-up.sh"

## local-api: same backends, without opening the Flutter client.
local-api:
	$(WSL_RUN) "NO_CLIENT=1 bash ./scripts/local-up.sh"

## local-down: stop the processes `make local` started.
local-down:
	$(WSL_RUN) "bash ./scripts/local-down.sh"

## local-status: print the state of the local stack and its health endpoints.
local-status:
	$(WSL_RUN) "bash ./scripts/local-status.sh"

## venv: build the Python environment the proto contract test needs.
# On a POSIX host (Linux, WSL, macOS) this creates KARUM_VENV with the pinned
# protobuf, using uv when it is installed and the stdlib venv otherwise. The
# Windows repo venv (.venv/Scripts) already has it.
ifeq ($(OS),Windows_NT)
venv:
	@echo "The Windows repo venv (.venv/Scripts/python.exe) already carries protobuf==7.36.2."
else
venv:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv --python 3.13 $(KARUM_VENV); \
		uv pip install --python $(KARUM_VENV)/bin/python -r contract/pyrelay/requirements.txt; \
	else \
		$(DEFAULT_PYTHON) -m venv $(KARUM_VENV); \
		$(KARUM_VENV)/bin/python -m pip install --quiet -r contract/pyrelay/requirements.txt; \
	fi
endif

## demo-on: start the demo VM. Docker brings the containers back.
demo-on:
	$(WSL_RUN) "bash ./scripts/demo.sh on"

## demo-off: stop the demo VM. CPU billing stops; the disk and IP remain.
demo-off:
	$(WSL_RUN) "bash ./scripts/demo.sh off"

## demo-status: print RUNNING or STOPPED.
demo-status:
	$(WSL_RUN) "bash ./scripts/demo.sh status"

## demo-refresh: sync this checkout and .env onto the VM, rebuild containers, publish the client.
demo-refresh:
	$(WSL_RUN) "bash ./scripts/demo.sh refresh"

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

## test: smoke the running stack (fixture mode) and assert the judge journey.
# Posts the Austin preset, waits for a terminal state, and asserts a ranked
# door board, a skip list with reasons, a per-door pitch, and a route. The
# JSON report lands in contract/.out/smoke.json. Point GATEWAY_URL at the
# stack under test; the default is the laptop gateway on port 8080.
#
# The smoke runs next to the stack: inside WSL on Windows, so it reaches the
# gateway on 127.0.0.1.
test:
	@$(WSL_RUN) "$(POSIX_PYTHON) scripts/smoke.py $(GATEWAY_URL)"

## routes-check: prove the field route works on this host. Fixture mode does
## not call Google, so this is the only way to verify the key, that the Routes
## API is enabled on it, and the timeout budget before the demo.
routes-check:
	cd ../karum-server && $(GO) run ./cmd/routescheck

## prewarm: run all four presets end-to-end on the deployed gateway and refresh
## the stored runs so a preset click serves the newest ready stored run
## (PLAN.md §13, §25, and §39). Requires PREWARM_TOKEN: a judge session
## token from POST /api/v1/auth/judge (or /auth/login) on the target gateway.
## Set GATEWAY_URL for the deployed host; the laptop default is localhost:8080.
prewarm:
	@$(WSL_ENV) $(WSL_RUN) "bash ./scripts/prewarm.sh"

## eval: run the leave-one-out harness across ~20 blocks.
eval:
	@echo "TODO(eval): run Karum vs LlmOnlyBaseline on ~20 blocks and write the table."
	@echo "Not implemented until the scoring rubric and baseline land (PLAN.md §40)."

## lint-proto: lint the shared protos with buf.
lint-proto:
	cd proto && $(BUF) lint

## breaking: check the protos against origin/main for breaking changes.
breaking:
	@$(PYTHON) scripts/breaking.py --buf "$(BUF)"

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
	@$(PYTHON) scripts/mkdir_p.py gen
	cd proto && $(BUF) build --as-file-descriptor-set -o ../gen/descriptor.binpb
	$(GO) run ./tools/doccheck gen/descriptor.binpb

## contract-test: round-trip the sample campaign through the Go and Python stubs (needs `make generate`).
contract-test:
	@$(PYTHON) scripts/mkdir_p.py $(CONTRACT_OUT)
	$(GO) run ./contract/roundtrip emit contract/testdata/campaign $(CONTRACT_OUT)
	$(PYTHON) contract/pyrelay/roundtrip.py contract/testdata/campaign $(CONTRACT_OUT)
	$(GO) run ./contract/roundtrip verify contract/testdata/campaign $(CONTRACT_OUT)

## check-protos: lint, doc markers, and the stub contract test (run `make generate` first).
check-protos: lint-proto check-proto-docs contract-test

## redact-fixtures: regenerate the fixture pack from local recordings (needs spike/out/).
redact-fixtures:
	$(PYTHON) fixtures/tools/redact.py

## check-fixtures: verify fixture hashes, preset schemas, and the AI pack (CI-safe; no recordings needed).
check-fixtures:
	$(PYTHON) fixtures/tools/redact.py --verify
	$(PYTHON) fixtures/tools/build_ai_pack.py --check

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
	$(PYTHON) spike/run_spike.py $(ARGS)
