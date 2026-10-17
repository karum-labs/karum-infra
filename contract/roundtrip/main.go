// Command roundtrip is the Go half of the stub contract test (PLAN.md §1.4).
//
// The contract test round-trips one campaign — the six recorded payloads under
// contract/testdata/campaign — through both generated stub sets:
//
//  1. `roundtrip emit` parses each fixture with the generated Go stubs and
//     writes deterministic binaries (<name>.bin).
//  2. contract/pyrelay/roundtrip.py parses those binaries with the generated
//     Python stubs, asserts semantic values, and re-serializes (<name>.py.bin).
//     It never reads the JSON fixtures: Python only ever sees the wire format,
//     which is the point of the exercise.
//  3. `roundtrip verify` parses both artifact sets with the Go stubs and
//     asserts semantic equality against the fixtures.
//
// A change that compiles in one language but not the other fails step 2 or 3.
// `make contract-test` runs all three steps; the CI equivalent lives in the
// contract job of .github/workflows/proto.yml, which regenerates the stubs
// inside the pinned buf container first.
//
// Usage:
//
//	go run ./contract/roundtrip emit   contract/testdata/campaign contract/.out
//	go run ./contract/roundtrip verify contract/testdata/campaign contract/.out
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"

	// Blank imports register every generated message type in the global
	// registry so manifest entries resolve by their proto full name.
	_ "github.com/karum-labs/karum-infra/gen/go/karum/agent/v1"
	_ "github.com/karum-labs/karum-infra/gen/go/karum/common/v1"
	_ "github.com/karum-labs/karum-infra/gen/go/karum/taste/v1"
)

// manifestEntry names one fixture: its short name (artifact prefix), the proto
// full name of the message it decodes to, and the JSON file carrying it.
type manifestEntry struct {
	Name string `json:"name"`
	Type string `json:"type"`
	File string `json:"file"`
}

// manifest is the fixture pack index.
type manifest struct {
	Messages []manifestEntry `json:"messages"`
}

func loadManifest(testdataDir string) (*manifest, error) {
	raw, err := os.ReadFile(filepath.Join(testdataDir, "manifest.json"))
	if err != nil {
		return nil, fmt.Errorf("read manifest: %w", err)
	}
	var man manifest
	if err := json.Unmarshal(raw, &man); err != nil {
		return nil, fmt.Errorf("parse manifest: %w", err)
	}
	if len(man.Messages) == 0 {
		return nil, fmt.Errorf("manifest %s lists no messages", testdataDir)
	}
	for _, entry := range man.Messages {
		if entry.Name == "" || entry.Type == "" || entry.File == "" {
			return nil, fmt.Errorf("manifest entry %+v is incomplete", entry)
		}
	}
	return &man, nil
}

func newMessageOfType(fullName string) (proto.Message, error) {
	messageType, err := protoregistry.GlobalTypes.FindMessageByName(protoreflect.FullName(fullName))
	if err != nil {
		return nil, fmt.Errorf("message type %q is not registered by the generated stubs (run `make generate`): %w", fullName, err)
	}
	return messageType.New().Interface(), nil
}

// parseEntry decodes one fixture with protojson. Unknown JSON fields are an
// error on purpose: fixture drift must fail loudly, not decode silently.
func parseEntry(testdataDir string, entry manifestEntry) (proto.Message, error) {
	raw, err := os.ReadFile(filepath.Join(testdataDir, entry.File))
	if err != nil {
		return nil, fmt.Errorf("read fixture %s: %w", entry.File, err)
	}
	msg, err := newMessageOfType(entry.Type)
	if err != nil {
		return nil, err
	}
	if err := (protojson.UnmarshalOptions{DiscardUnknown: false}).Unmarshal(raw, msg); err != nil {
		return nil, fmt.Errorf("decode %s as %s: %w", entry.File, entry.Type, err)
	}
	return msg, nil
}

// runEmit decodes every fixture with the Go stubs and writes <name>.bin.
func runEmit(testdataDir, outDir string) error {
	man, err := loadManifest(testdataDir)
	if err != nil {
		return err
	}
	for _, entry := range man.Messages {
		msg, err := parseEntry(testdataDir, entry)
		if err != nil {
			return err
		}
		raw, err := proto.MarshalOptions{Deterministic: true}.Marshal(msg)
		if err != nil {
			return fmt.Errorf("marshal %s: %w", entry.Name, err)
		}
		if err := os.WriteFile(filepath.Join(outDir, entry.Name+".bin"), raw, 0o644); err != nil {
			return err
		}
		fmt.Printf("emit:   %-12s %6d bytes  %s\n", entry.Name, len(raw), entry.Type)
	}
	return nil
}

// runVerify checks that <name>.bin (Go-emitted) and <name>.py.bin
// (Python-emitted) both decode, with the Go stubs, to the fixture message.
func runVerify(testdataDir, outDir string) error {
	man, err := loadManifest(testdataDir)
	if err != nil {
		return err
	}
	var problems []string
	for _, entry := range man.Messages {
		want, err := parseEntry(testdataDir, entry)
		if err != nil {
			return err
		}
		for _, artifact := range []string{entry.Name + ".bin", entry.Name + ".py.bin"} {
			path := filepath.Join(outDir, artifact)
			raw, err := os.ReadFile(path)
			if err != nil {
				problems = append(problems, fmt.Sprintf("%s: %v", artifact, err))
				continue
			}
			got, err := newMessageOfType(entry.Type)
			if err != nil {
				return err
			}
			if err := proto.Unmarshal(raw, got); err != nil {
				problems = append(problems, fmt.Sprintf("%s: parse: %v", artifact, err))
				continue
			}
			if !proto.Equal(want, got) {
				problems = append(problems, fmt.Sprintf("%s: differs from %s", artifact, entry.File))
				continue
			}
			fmt.Printf("verify: %-12s %6d bytes  ok\n", artifact, len(raw))
		}
	}
	if len(problems) > 0 {
		return fmt.Errorf("contract round-trip failed:\n  %s", strings.Join(problems, "\n  "))
	}
	fmt.Println("go verify: all artifacts match the fixture set")
	return nil
}

const usage = `usage: roundtrip <emit|verify> <testdata-dir> <artifacts-dir>

  emit    decode every fixture with the Go stubs and write <name>.bin
  verify  assert <name>.bin and <name>.py.bin decode to the fixtures
`

func main() {
	if len(os.Args) != 4 {
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "emit":
		err = runEmit(os.Args[2], os.Args[3])
	case "verify":
		err = runVerify(os.Args[2], os.Args[3])
	default:
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "roundtrip:", err)
		os.Exit(1)
	}
}
