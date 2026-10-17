package main

// Tests for the Go half of the stub contract test.
//
// The checks here are the language-local half of the round-trip: JSON fixture
// -> generated stub -> deterministic binary -> generated stub must be
// loss-less. The cross-language half (Python parses the binaries this package
// emits and re-serializes them) runs in `make contract-test`, and
// TestVerifyCatchesCorruption proves the verifier actually detects drift
// instead of rubber-stamping.

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"google.golang.org/protobuf/proto"

	_ "github.com/karum-labs/karum-infra/gen/go/karum/agent/v1"
	_ "github.com/karum-labs/karum-infra/gen/go/karum/common/v1"
	_ "github.com/karum-labs/karum-infra/gen/go/karum/taste/v1"
)

const testdataDir = "../testdata/campaign"

func TestGoJSONBinaryRoundTrip(t *testing.T) {
	man, err := loadManifest(testdataDir)
	if err != nil {
		t.Fatal(err)
	}
	if len(man.Messages) == 0 {
		t.Fatal("manifest lists no messages")
	}

	for _, entry := range man.Messages {
		t.Run(entry.Name, func(t *testing.T) {
			want, err := parseEntry(testdataDir, entry)
			if err != nil {
				t.Fatal(err)
			}

			first, err := proto.MarshalOptions{Deterministic: true}.Marshal(want)
			if err != nil {
				t.Fatal(err)
			}
			second, err := proto.MarshalOptions{Deterministic: true}.Marshal(want)
			if err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(first, second) {
				t.Fatalf("deterministic marshal is not stable for %s", entry.Type)
			}

			got, err := newMessageOfType(entry.Type)
			if err != nil {
				t.Fatal(err)
			}
			if err := proto.Unmarshal(first, got); err != nil {
				t.Fatal(err)
			}
			if !proto.Equal(want, got) {
				t.Fatalf("binary round-trip changed the message %s", entry.Type)
			}
		})
	}
}

func TestManifestCoversBothServicePackages(t *testing.T) {
	man, err := loadManifest(testdataDir)
	if err != nil {
		t.Fatal(err)
	}

	var taste, agent bool
	for _, entry := range man.Messages {
		switch {
		case strings.HasPrefix(entry.Type, "karum.taste.v1."):
			taste = true
		case strings.HasPrefix(entry.Type, "karum.agent.v1."):
			agent = true
		}
	}
	if !taste || !agent {
		t.Fatalf("manifest must cover both service packages to round-trip a campaign through both stubs (taste=%v agent=%v)", taste, agent)
	}
}

func TestVerifyCatchesCorruption(t *testing.T) {
	out := t.TempDir()
	if err := runEmit(testdataDir, out); err != nil {
		t.Fatal(err)
	}

	man, err := loadManifest(testdataDir)
	if err != nil {
		t.Fatal(err)
	}
	// Stand in for the Python relay: copy the Go artifacts under the .py.bin
	// names so a clean tree verifies.
	for _, entry := range man.Messages {
		raw, err := os.ReadFile(filepath.Join(out, entry.Name+".bin"))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(out, entry.Name+".py.bin"), raw, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	if err := runVerify(testdataDir, out); err != nil {
		t.Fatalf("clean artifacts should verify, got: %v", err)
	}

	// Replace the scout artifact with an empty message of the same type: the
	// verifier must name the scout entry and fail.
	empty, err := newMessageOfType("karum.taste.v1.ScoutDoorsResponse")
	if err != nil {
		t.Fatal(err)
	}
	corrupt, err := proto.Marshal(empty)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "scout.bin"), corrupt, 0o644); err != nil {
		t.Fatal(err)
	}

	err = runVerify(testdataDir, out)
	if err == nil {
		t.Fatal("expected verify to fail on a corrupted artifact")
	}
	if !strings.Contains(err.Error(), "scout") {
		t.Fatalf("verify error should name the scout entry, got: %v", err)
	}
}
