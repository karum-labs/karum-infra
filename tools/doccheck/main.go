// Command doccheck enforces the Karum proto provenance-marker convention.
//
// PLAN.md §1 requires every domain field to be marked as a Qloo fact or a model
// inference so the evidence drawer and the PDF can render the split visually
// distinct (§24, §32, §40). This checker makes the convention machine-checked.
//
// It reads a google.protobuf.FileDescriptorSet (with source info, produced by
// `buf build --as-file-descriptor-set`) and walks every field of the configured
// packages. Each field's leading comment must open with exactly one marker:
//
//	Qloo fact:        the value comes from Qloo.
//	Google fact:      the value comes from Google (Geocoder, Places, Routes).
//	Model inference:  the value is derived by Karum or written by Gemini.
//	Input:            operator-supplied or bookkeeping; never rendered as
//	                  evidence.
//
// The marker must be followed by a non-empty description. Fields of a message
// whose name ends in "Request" must use "Input:" — request payloads are user
// input and booking data, not evidence.
//
// Usage:
//
//	go run ./tools/doccheck gen/descriptor.binpb
//	go run ./tools/doccheck -packages karum.taste.v1 gen/descriptor.binpb
package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/descriptorpb"
)

// Default package filter: the domain packages every field of which must be
// marked. Platform packages such as karum.health.v1 are out of scope.
const defaultPackages = "karum.common.v1,karum.taste.v1,karum.agent.v1"

// Provenance markers, in the canonical spelling the comments must use.
const (
	markerQloo   = "Qloo fact:"
	markerGoogle = "Google fact:"
	markerModel  = "Model inference:"
	markerInput  = "Input:"
)

var allMarkers = []string{markerQloo, markerGoogle, markerModel, markerInput}

// Violation is one field that breaks the marker convention.
type Violation struct {
	// File is the proto file name, e.g. "karum/taste/v1/taste.proto".
	File string
	// Line is the 1-based source line of the field; 0 when source info lacks it.
	Line int
	// Path is the fully qualified field, e.g.
	// "karum.taste.v1.ScoutDoorsRequest.brand_query".
	Path string
	// Msg explains the problem.
	Msg string
}

// String renders a violation as "file:line: path: message".
func (v Violation) String() string {
	return fmt.Sprintf("%s:%d: %s: %s", v.File, v.Line, v.Path, v.Msg)
}

// CheckFileSet walks the given files and returns how many fields were checked
// and every violation found. Only packages matching an entry of packages
// (exact match) are checked.
func CheckFileSet(fds *descriptorpb.FileDescriptorSet, packages []string) (int, []Violation) {
	var checked int
	var violations []Violation

	for _, file := range fds.GetFile() {
		if !packageSelected(file.GetPackage(), packages) {
			continue
		}
		locs := indexLocations(file.GetSourceCodeInfo())
		for i, msg := range file.GetMessageType() {
			walk(file.GetName(), file.GetPackage(), msg, []int32{4, int32(i)}, false, locs, &checked, &violations)
		}
	}
	return checked, violations
}

func packageSelected(pkg string, packages []string) bool {
	for _, p := range packages {
		if pkg == p {
			return true
		}
	}
	return false
}

// walk checks one message and recurses into its nested messages.
//
// Descriptor paths follow the protobuf convention: for the i-th top-level
// message the path starts [4, i]; fields append [2, j], nested types append
// [3, k].
//
// inRequest is inherited: any message nested inside a *Request message is part
// of the request shape, so its fields must also use "Input:".
func walk(
	file string,
	prefix string,
	msg *descriptorpb.DescriptorProto,
	path []int32,
	inRequest bool,
	locs map[string]*descriptorpb.SourceCodeInfo_Location,
	checked *int,
	violations *[]Violation,
) {
	full := prefix + "." + msg.GetName()
	inRequest = inRequest || strings.HasSuffix(msg.GetName(), "Request")

	for j, field := range msg.GetField() {
		*checked++
		fieldPath := appendPath(path, 2, int32(j))
		loc := locs[pathKey(fieldPath)]
		comment := strings.TrimSpace(loc.GetLeadingComments())

		marker, problem := markerOf(comment)
		switch problem {
		case problemMissing:
			*violations = append(*violations, violationAt(file, loc, full+"."+field.GetName(),
				`missing provenance marker; expected one of "`+strings.Join(allMarkers, `", "`)+`"`))
		case problemNoDescription:
			*violations = append(*violations, violationAt(file, loc, full+"."+field.GetName(),
				fmt.Sprintf("provenance marker %q needs a description after it", marker)))
		case "":
			if inRequest && marker != markerInput {
				*violations = append(*violations, violationAt(file, loc, full+"."+field.GetName(),
					fmt.Sprintf(`fields of %s must use %q, got %q`, msg.GetName(), markerInput, marker)))
			}
		}
	}

	for k, nested := range msg.GetNestedType() {
		walk(file, full, nested, appendPath(path, 3, int32(k)), inRequest, locs, checked, violations)
	}
}

const (
	problemMissing       = "missing"
	problemNoDescription = "no-description"
)

// markerOf returns the leading marker of a comment and any problem found.
// An empty problem means the comment is valid.
func markerOf(comment string) (marker string, problem string) {
	for _, m := range allMarkers {
		if strings.HasPrefix(comment, m) {
			if strings.TrimSpace(strings.TrimPrefix(comment, m)) == "" {
				return m, problemNoDescription
			}
			return m, ""
		}
	}
	return "", problemMissing
}

func violationAt(file string, loc *descriptorpb.SourceCodeInfo_Location, path, msg string) Violation {
	v := Violation{File: file, Path: path, Msg: msg}
	if span := loc.GetSpan(); len(span) > 0 {
		v.Line = int(span[0]) + 1
	}
	return v
}

func appendPath(path []int32, parts ...int32) []int32 {
	out := make([]int32, 0, len(path)+len(parts))
	out = append(out, path...)
	return append(out, parts...)
}

func pathKey(path []int32) string {
	var b strings.Builder
	for i, p := range path {
		if i > 0 {
			b.WriteByte(',')
		}
		fmt.Fprintf(&b, "%d", p)
	}
	return b.String()
}

func indexLocations(info *descriptorpb.SourceCodeInfo) map[string]*descriptorpb.SourceCodeInfo_Location {
	locs := make(map[string]*descriptorpb.SourceCodeInfo_Location, len(info.GetLocation()))
	for _, loc := range info.GetLocation() {
		locs[pathKey(loc.GetPath())] = loc
	}
	return locs
}

func main() {
	packages := flag.String("packages", defaultPackages, "comma-separated proto packages to check")
	flag.Parse()

	args := flag.Args()
	if len(args) != 1 {
		fmt.Fprintln(os.Stderr, "usage: doccheck [-packages karum.taste.v1,...] <descriptor-set.binpb>")
		os.Exit(2)
	}

	raw, err := os.ReadFile(args[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "doccheck: read descriptor set: %v\n", err)
		os.Exit(2)
	}
	fds := &descriptorpb.FileDescriptorSet{}
	if err := proto.Unmarshal(raw, fds); err != nil {
		fmt.Fprintf(os.Stderr, "doccheck: parse descriptor set: %v\n", err)
		os.Exit(2)
	}

	pkgs := strings.Split(*packages, ",")
	checked, violations := CheckFileSet(fds, pkgs)
	if len(violations) > 0 {
		for _, v := range violations {
			fmt.Fprintln(os.Stderr, v)
		}
		fmt.Fprintf(os.Stderr, "doccheck: %d violation(s) across %d checked field(s)\n", len(violations), checked)
		os.Exit(1)
	}
	fmt.Printf("doccheck: ok (%d fields checked in %s)\n", checked, strings.Join(pkgs, ", "))
}
