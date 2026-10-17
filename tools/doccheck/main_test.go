package main

// Tests for the proto provenance-marker checker.
//
// The checker reads a google.protobuf.FileDescriptorSet (produced by
// `buf build --as-file-descriptor-set`) and asserts two rules on every field of
// the domain packages (karum.common.v1, karum.taste.v1, karum.agent.v1):
//
//  1. The field's leading comment opens with exactly one provenance marker:
//     "Qloo fact:", "Google fact:", "Model inference:", or "Input:", followed by
//     a non-empty description.
//  2. Fields of a message whose name ends in "Request" use "Input:".
//
// The tests build descriptor protos with hand-written SourceCodeInfo so the
// checker is exercised without running buf.

import (
	"strings"
	"testing"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/descriptorpb"
)

// fieldSpec is one field under test: its name and the raw leading comment.
type fieldSpec struct {
	name    string
	comment string
}

// newFile builds a FileDescriptorProto with one top-level message per entry.
// Each message is named by the map key; fields carry the given comments. The
// paths in SourceCodeInfo follow the protobuf descriptor convention:
// message_type -> 4, field -> 2, nested_type -> 3.
func newFile(pkg string, messages map[string][]fieldSpec) *descriptorpb.FileDescriptorProto {
	f := &descriptorpb.FileDescriptorProto{
		Name:    proto.String(strings.ReplaceAll(pkg, ".", "/") + "/test.proto"),
		Package: proto.String(pkg),
	}
	var locations []*descriptorpb.SourceCodeInfo_Location

	line := int32(10)
	names := make([]string, 0, len(messages))
	for name := range messages {
		names = append(names, name)
	}
	// Deterministic order for readable failures.
	sortStrings(names)

	for i, name := range names {
		msg := &descriptorpb.DescriptorProto{Name: proto.String(name)}
		for j, fs := range messages[name] {
			msg.Field = append(msg.Field, &descriptorpb.FieldDescriptorProto{
				Name:   proto.String(fs.name),
				Number: proto.Int32(int32(j + 1)),
				Type:   descriptorpb.FieldDescriptorProto_TYPE_STRING.Enum(),
			})
			locations = append(locations, &descriptorpb.SourceCodeInfo_Location{
				Path:            []int32{4, int32(i), 2, int32(j)},
				Span:            []int32{line, 0, line + 1, 0},
				LeadingComments: proto.String(fs.comment),
			})
			line += 2
		}
		f.MessageType = append(f.MessageType, msg)
	}

	f.SourceCodeInfo = &descriptorpb.SourceCodeInfo{Location: locations}
	return f
}

func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}

// newNestedFile builds a file with one outer message containing one nested
// message, so the recursive walker is exercised.
func newNestedFile(pkg, outer, nested string, outerField, nestedField fieldSpec) *descriptorpb.FileDescriptorProto {
	f := &descriptorpb.FileDescriptorProto{
		Name:    proto.String(strings.ReplaceAll(pkg, ".", "/") + "/nested.proto"),
		Package: proto.String(pkg),
		MessageType: []*descriptorpb.DescriptorProto{{
			Name: proto.String(outer),
			Field: []*descriptorpb.FieldDescriptorProto{{
				Name:   proto.String(outerField.name),
				Number: proto.Int32(1),
				Type:   descriptorpb.FieldDescriptorProto_TYPE_STRING.Enum(),
			}},
			NestedType: []*descriptorpb.DescriptorProto{{
				Name: proto.String(nested),
				Field: []*descriptorpb.FieldDescriptorProto{{
					Name:   proto.String(nestedField.name),
					Number: proto.Int32(1),
					Type:   descriptorpb.FieldDescriptorProto_TYPE_STRING.Enum(),
				}},
			}},
		}},
		SourceCodeInfo: &descriptorpb.SourceCodeInfo{Location: []*descriptorpb.SourceCodeInfo_Location{
			{
				Path:            []int32{4, 0, 2, 0},
				Span:            []int32{10, 0, 11, 0},
				LeadingComments: proto.String(outerField.comment),
			},
			{
				Path:            []int32{4, 0, 3, 0, 2, 0},
				Span:            []int32{12, 0, 13, 0},
				LeadingComments: proto.String(nestedField.comment),
			},
		}},
	}
	return f
}

var testPackages = []string{"karum.common.v1", "karum.taste.v1", "karum.agent.v1"}

func TestValidMarkersPass(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.common.v1", map[string][]fieldSpec{
			"Tag": {
				{name: "urn", comment: "Qloo fact: the tag URN."},
				{name: "score", comment: "Model inference: derived confidence."},
				{name: "city", comment: "Google fact: geocoded city label."},
				{name: "note", comment: "Input: operator note."},
			},
		}),
	}}

	checked, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 0 {
		t.Fatalf("expected no violations, got %+v", violations)
	}
	if checked != 4 {
		t.Fatalf("expected 4 fields checked, got %d", checked)
	}
}

func TestMissingMarkerFails(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.taste.v1", map[string][]fieldSpec{
			"Tag": {{name: "urn", comment: "the tag URN."}},
		}),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	v := violations[0]
	if !strings.Contains(v.Msg, "missing provenance marker") {
		t.Fatalf("unexpected message: %q", v.Msg)
	}
	if !strings.Contains(v.Path, "karum.taste.v1.Tag.urn") {
		t.Fatalf("unexpected path: %q", v.Path)
	}
	if v.Line != 11 {
		t.Fatalf("expected line 11 (1-based from a 0-based span), got %d", v.Line)
	}
}

func TestEmptyCommentFails(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.taste.v1", map[string][]fieldSpec{
			"Tag": {{name: "urn", comment: ""}},
		}),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
}

func TestMarkerNeedsDescription(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.taste.v1", map[string][]fieldSpec{
			"Tag": {{name: "urn", comment: "Qloo fact:"}},
		}),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	if !strings.Contains(violations[0].Msg, "description") {
		t.Fatalf("unexpected message: %q", violations[0].Msg)
	}
}

func TestMarkerMustOpenTheComment(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.taste.v1", map[string][]fieldSpec{
			"Tag": {{name: "urn", comment: " Amplifies: Qloo fact: the tag URN."}},
		}),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	if !strings.Contains(violations[0].Msg, "missing provenance marker") {
		t.Fatalf("unexpected message: %q", violations[0].Msg)
	}
}

func TestRequestFieldsMustUseInput(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.taste.v1", map[string][]fieldSpec{
			"ScoutDoorsRequest": {
				{name: "brand_query", comment: "Input: the query text."},
				{name: "seed", comment: "Qloo fact: the confirmed seed."},
			},
		}),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	if !strings.Contains(violations[0].Msg, `must use "Input:"`) {
		t.Fatalf("unexpected message: %q", violations[0].Msg)
	}
}

func TestNestedMessagesAreChecked(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newNestedFile(
			"karum.agent.v1",
			"MenuAuditResult",
			"Incumbent",
			fieldSpec{name: "door", comment: "Qloo fact: the audited door."},
			fieldSpec{name: "name", comment: "no marker here"},
		),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	if !strings.Contains(violations[0].Path, "MenuAuditResult.Incumbent.name") {
		t.Fatalf("unexpected path: %q", violations[0].Path)
	}
}

func TestNestedRequestFieldsMustUseInput(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newNestedFile(
			"karum.agent.v1",
			"OuterRequest",
			"Target",
			fieldSpec{name: "query", comment: "Input: ok."},
			fieldSpec{name: "door", comment: "Qloo fact: nested request target."},
		),
	}}

	_, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 1 {
		t.Fatalf("expected 1 violation, got %+v", violations)
	}
	if !strings.Contains(violations[0].Msg, `must use "Input:"`) {
		t.Fatalf("unexpected message: %q", violations[0].Msg)
	}
}

func TestPackageFilterSkipsUnlistedPackages(t *testing.T) {
	fds := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{
		newFile("karum.health.v1", map[string][]fieldSpec{
			"HealthCheckRequest": {{name: "service", comment: "no marker; health is platform, not domain."}},
		}),
	}}

	checked, violations := CheckFileSet(fds, testPackages)
	if len(violations) != 0 {
		t.Fatalf("expected no violations, got %+v", violations)
	}
	if checked != 0 {
		t.Fatalf("expected 0 fields checked, got %d", checked)
	}
}
