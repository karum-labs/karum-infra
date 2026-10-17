# karum-infra — protos, local Compose, and toolchain pins for the Karum stack.
#
# This Makefile is the operator surface for the local dev stack. The prewarm and
# eval targets are stubs until the sample-block fixtures and the leave-one-out
# harness land (PLAN.md epics 7 and 5).
#
# Proto tooling: `make generate` emits the Go and Python stubs; `make
# check-protos` runs lint, the provenance-marker check, and the cross-language
# contract test. CI runs the generate step inside Docker (PLAN.md §1.4);
# `make generate-docker` is the local equivalent.

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

.PHONY: help up down logs test prewarm eval lint-proto breaking generate generate-docker check-proto-docs contract-test check-protos spike

## help: list available targets.
help:
	@python -c "import re,sys;print(*re.findall(r'^## (.*)',open(sys.argv[1],encoding='utf-8').read(),re.M),sep=chr(10))" "$(firstword $(MAKEFILE_LIST))"

## up: build and start the full stack in the background, then wait for healthy.
up:
	$(COMPOSE) up --build -d
	@echo "Waiting for services to become healthy..."
	@$(COMPOSE) ps

## down: stop the stack and remove containers (keeps the Postgres volume).
down:
	$(COMPOSE) down

## logs: follow the stack's combined logs.
logs:
	$(COMPOSE) logs -f

## test: run the smoke test against the running stack (fixture mode).
test:
	@echo "TODO(smoke): post the sample vacancy in fixture mode and assert a 5-item shortlist."
	@echo "Stack status:"
	@$(COMPOSE) ps

## prewarm: load the two sample blocks into the taste cache.
prewarm:
	@echo "TODO(prewarm): call the taste prewarm RPC for both sample blocks."
	@echo "Not implemented until the sample-block fixtures land (epic 7)."

## eval: run the leave-one-out harness across ~20 blocks.
eval:
	@echo "TODO(eval): run Karum vs LlmOnlyBaseline on ~20 blocks and write the table."
	@echo "Not implemented until the scoring rubric and baseline land (epic 5)."

## lint-proto: lint the shared protos with buf.
lint-proto:
	cd proto && $(BUF) lint

## breaking: check the protos against origin/main for breaking changes.
breaking:
	@python scripts/breaking.py --buf "$(BUF)"

## generate: emit Go and Python stubs from the shared protos (pinned BSR plugins).
generate:
	cd proto && $(BUF) generate

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

## spike ARGS="key": run the Qloo spike runner (see spike/README.md).
spike:
	python spike/run_spike.py $(ARGS)
