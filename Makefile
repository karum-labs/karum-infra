# karum-infra — protos, local Compose, and toolchain pins for the Karum stack.
#
# This Makefile is the operator surface for the local dev stack. The prewarm and
# eval targets are stubs until the sample-block fixtures and the leave-one-out
# harness land (PLAN.md epics 7 and 5).

COMPOSE ?= docker compose
BUF ?= buf

.PHONY: help up down logs test prewarm eval lint-proto breaking generate

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

## generate: emit Go and Python stubs from the shared protos.
generate:
	cd proto && $(BUF) generate
