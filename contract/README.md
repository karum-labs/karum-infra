# Contract test

Proves that the Go and Python stubs generated from `proto/` agree on one
campaign payload set (PLAN.md §1.4). One campaign fixture is round-tripped
through **both** generated stub sets, so a contract change that compiles in one
language but not the other fails CI.

## What is here

| Path | Role |
| --- | --- |
| `testdata/campaign/` | Hand-written fixtures for the Austin wholesale preset: `manifest.json` maps each short name to a proto message and a JSON file (`seed`, `scout`, `audit`, `pitch`, `baseline`, `trace`). |
| `roundtrip/` | Go half: `emit` decodes the fixtures with the Go stubs and writes deterministic binaries; `verify` asserts both the Go-emitted and Python-emitted binaries decode back to the fixtures. |
| `pyrelay/` | Python half: parses the Go-emitted binaries with the Python stubs, asserts semantic values, re-serializes. It never reads the JSON fixtures — Python only ever sees the wire format. |

## Running it

```sh
make generate       # emit stubs into ../gen (pinned BSR plugins)
make contract-test  # go emit -> python relay -> go verify
```

`make check-protos` bundles lint, the provenance-marker check, and this
contract test.

Local Python needs `protobuf==7.36.2` (see `pyrelay/requirements.txt`). CI
generates the stubs inside the pinned `bufbuild/buf` container and runs the
same three steps, so laptop and CI artifacts match.
