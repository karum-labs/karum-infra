"""Unit tests for the redaction projections in fixtures/tools/redact.py."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REDACT_PATH = Path(__file__).with_name("redact.py")
_spec = importlib.util.spec_from_file_location("redact", REDACT_PATH)
redact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redact)


class SearchProjectionTests(unittest.TestCase):
    def test_project_search_keeps_only_consumed_fields(self):
        row = {
            "entity_id": "AAA",
            "name": "Leopold Cafe",
            "types": ["urn:entity:place"],
            "location": {"lat": 18.92, "lon": 72.83, "geohash": "x"},
            "popularity": 0.9,
            "properties": {
                "geocode": {
                    "city": "Mumbai",
                    "name": "Colaba",
                    "metro": "Mumbai",
                    "country": "India",
                    "admin1_region": "Maharashtra",
                    "zip": "400001",
                },
                "image": {"url": "https://example.invalid"},
            },
            "disambiguation": "Colaba Causeway",
            "tags": [{"id": "urn:tag:x"}],
        }
        out = redact.project_search(row)
        self.assertEqual(
            set(out),
            {"entity_id", "name", "types", "location", "geocode", "disambiguation"},
        )
        self.assertEqual(out["location"], {"lat": 18.92, "lon": 72.83})
        self.assertEqual(
            out["geocode"],
            {
                "city": "Mumbai",
                "name": "Colaba",
                "metro": "Mumbai",
                "country": "India",
                "admin1_region": "Maharashtra",
            },
        )


class PlaceProjectionTests(unittest.TestCase):
    def test_project_place_trims_properties_and_explainability(self):
        row = {
            "entity_id": "BBB",
            "name": "Midnight Cowboy",
            "type": "urn:entity",
            "subtype": "urn:entity:place",
            "disambiguation": "Austin",
            "location": {"lat": 30.26, "lon": -97.74, "geohash": "9v6"},
            "popularity": 0.8,
            "tags": [{"id": "urn:tag:a", "name": "Bar", "type": "genre", "weight": 3}],
            "query": {
                "affinity": 0.8575,
                "distance": 301,
                "measurements": {"growth": 1},
                "explainability": {
                    "signal.interests.entities": [
                        {"entity_id": "AAA", "score": 0.35, "junk": True}
                    ]
                },
            },
            "properties": {
                "address": "104 E 6th St",
                "hours": {"monday": ["16:00-02:00"]},
                "business_rating": 4.7,
                "image": {"url": "https://example.invalid"},
                "keywords": {"ambience": ["speakeasy"]},
                "external": {"google_place": "x"},
                "geocode": {"city": "Austin", "country": "United States"},
            },
        }
        out = redact.project_place(row)
        self.assertEqual(set(out["properties"]), {"address", "hours", "business_rating", "geocode"})
        self.assertNotIn("image", out["properties"])
        self.assertEqual(set(out["query"]), {"affinity", "distance", "explainability"})
        self.assertEqual(
            out["query"]["explainability"],
            {"signal.interests.entities": [{"entity_id": "AAA", "score": 0.35}]},
        )
        self.assertEqual(set(out["tags"][0]), {"id", "name", "type", "weight"})
        self.assertEqual(out["location"], {"lat": 30.26, "lon": -97.74})


class CellAndLocalityTests(unittest.TestCase):
    def test_project_cell_flattens_location(self):
        row = {
            "location": {"latitude": 40.7, "longitude": -73.9, "geohash": "dr5"},
            "query": {
                "affinity": 0.8,
                "affinity_rank": 2,
                "popularity": 5,
                "entity_brand_affinity": 0.1,
            },
        }
        out = redact.project_cell(row)
        self.assertEqual(
            set(out), {"geohash", "location", "affinity", "affinity_rank", "popularity"}
        )
        self.assertEqual(out["location"], {"lat": 40.7, "lon": -73.9})
        self.assertEqual(out["affinity_rank"], 2)

    def test_project_locality_keeps_boundary_string(self):
        row = {
            "entity_id": "CCC",
            "name": "Williamsburg",
            "disambiguation": "Brooklyn",
            "query": {"affinity": 0.77},
            "boundary": "MULTIPOLYGON ((0 0, 1 0, 1 1, 0 0))",
            "popularity": 0.5,
        }
        out = redact.project_locality(row)
        self.assertEqual(
            set(out), {"entity_id", "name", "disambiguation", "affinity", "boundary"}
        )
        self.assertEqual(out["boundary"], "MULTIPOLYGON ((0 0, 1 0, 1 1, 0 0))")


class TagAndDemographicsTests(unittest.TestCase):
    def test_project_tag_drops_extra_keys(self):
        out = redact.project_tag(
            {"id": "urn:tag:genre:place:cafe", "name": "Cafe", "type": "genre", "parents": []}
        )
        self.assertEqual(out, {"id": "urn:tag:genre:place:cafe", "name": "Cafe", "type": "genre"})

    def test_project_demographics_keeps_known_buckets_in_order(self):
        row = {
            "entity_id": "DDD",
            "query": {
                "age": {
                    "30_to_34": 0.11,
                    "24_and_younger": 0.51,
                    "mystery_bucket": 1,
                    "25_to_29": -0.2,
                    "35_to_44": 0.33,
                    "45_to_54": -0.61,
                    "55_and_older": -0.55,
                },
                "gender": {"male": -0.16, "female": 0.16, "other": 0},
            },
        }
        out = redact.project_demographics(row)
        self.assertEqual(out["entity_id"], "DDD")
        self.assertEqual(
            list(out["age"]),
            [
                "24_and_younger",
                "25_to_29",
                "30_to_34",
                "35_to_44",
                "45_to_54",
                "55_and_older",
            ],
        )
        self.assertNotIn("mystery_bucket", out["age"])
        self.assertEqual(out["gender"], {"male": -0.16, "female": 0.16})


class CompareProjectionTests(unittest.TestCase):
    def test_project_compare_pulls_count_from_query(self):
        row = {
            "tag_id": "urn:tag:qloo:craft_cocktails",
            "name": "Craft Cocktails",
            "type": "urn:tag:genre",
            "subtype": "urn:tag:genre:place",
            "entity_id": None,
            "query": {"count": 12, "other": 1},
        }
        out = redact.project_compare(row)
        self.assertEqual(out["count"], 12)
        self.assertEqual(set(out), {"tag_id", "name", "type", "subtype", "entity_id", "count"})


class EnvelopeTests(unittest.TestCase):
    def test_unwrap_rows_handles_list_and_dict(self):
        self.assertEqual(redact.unwrap_rows({"results": [1, 2]}), [1, 2])
        self.assertEqual(redact.unwrap_rows({"results": {"tags": [3], "other": 4}}), [3])
        self.assertEqual(redact.unwrap_rows({}), [])

    def test_collect_warnings_merges_top_and_nested(self):
        payload = {
            "warnings": [{"type": "not_found"}],
            "results": {"warnings": [{"type": "deprecated"}]},
        }
        out = redact.collect_warnings(payload)
        self.assertEqual(out, [{"type": "not_found"}, {"type": "deprecated"}])

    def test_stamp_of_formats_filename_stamp(self):
        self.assertEqual(
            redact.stamp_of("20261018-050756-resolve-place-la-condesa.json"),
            "2026-10-18 05:07:56",
        )

    def test_build_document_projects_rows_and_keeps_provenance(self):
        recipe = {
            "dst": "qloo/x/search-la-condesa.json",
            "src": "20261018-050756-resolve-place-la-condesa.json",
            "kind": "search",
            "note": "why",
        }
        meta = {"label": "resolve-place-la-condesa", "status": 200, "path": "/v2/search?query=la+condesa"}
        payload = {
            "results": [{"entity_id": "EEE", "name": "La Condesa", "types": ["urn:entity:place"]}],
            "warnings": [{"type": "not_found"}],
        }
        doc = redact.build_document(recipe, meta, payload)
        self.assertEqual(doc["fixture_version"], 1)
        self.assertEqual(doc["kind"], "search")
        self.assertEqual(doc["source"]["recorded"], "2026-10-18 05:07:56")
        self.assertEqual(doc["source"]["request"], "/v2/search?query=la+condesa")
        self.assertEqual(doc["note"], "why")
        self.assertEqual(doc["warnings"], [{"type": "not_found"}])
        self.assertEqual(len(doc["rows"]), 1)
        self.assertEqual(doc["rows"][0]["entity_id"], "EEE")


class SchemaCheckTests(unittest.TestCase):
    def _preset(self, **overrides):
        document = {
            "preset_id": "x",
            "label": "X",
            "mode": "wholesale",
            "city": "Everywhere",
            "point": {"lat": 1.0, "lon": 2.0},
            "radii_m": {"doors": 8000},
            "category_tags": {"doors": "urn:tag:genre:place:restaurant:bar"},
            "seed_entities": [
                {"entity_id": "32F867B9-E6DF-44C3-BCE4-40160C7ED5E4", "name": "A", "kind": "brand"}
            ],
            "skip_candidates": [],
            "recordings": [],
            "verified": "2026-10-18",
        }
        document.update(overrides)
        return document

    def test_valid_preset_has_no_problems(self):
        self.assertEqual(redact.preset_problems("presets/x.json", self._preset()), [])

    def test_preset_problems_flag_bad_values(self):
        document = self._preset(
            mode="bogus",
            point={"lat": 120.0, "lon": 2.0},
            radii_m={"doors": 5},
            seed_entities=[
                {"entity_id": "nope"},
                {"entity_id": "00000000-0000-0000-0000-000000000001"},
                {"entity_id": "00000000-0000-0000-0000-000000000002"},
                {"entity_id": "00000000-0000-0000-0000-000000000003"},
                {"entity_id": "00000000-0000-0000-0000-000000000004"},
            ],
        )
        problems = redact.preset_problems("presets/x.json", document)
        joined = "\n".join(problems)
        self.assertIn("bad mode", joined)
        self.assertIn("bad point.lat", joined)
        self.assertIn("bad radii_m.doors", joined)
        self.assertIn("seed_entities count", joined)
        self.assertIn("bad seed entity_id", joined)

    def test_preset_problems_check_recordings_on_disk(self):
        with mock.patch.object(redact, "OUT", Path(self.enterContext(_tempdir()))):
            problems = redact.preset_problems(
                "presets/x.json", self._preset(recordings=["qloo/missing.json"])
            )
        self.assertTrue(any("recording missing on disk" in problem for problem in problems))

    def test_qloo_problems_flag_bad_envelope(self):
        problems = redact.qloo_problems("qloo/x.json", {"fixture_version": 2, "kind": "junk"})
        joined = "\n".join(problems)
        self.assertIn("fixture_version", joined)
        self.assertIn("unknown kind", joined)
        self.assertIn("rows is not a list", joined)
        self.assertIn("missing source.recording", joined)

    def test_qloo_problems_accept_valid_envelope(self):
        document = {
            "fixture_version": 1,
            "kind": "search",
            "source": {"recording": "x.json"},
            "rows": [],
        }
        self.assertEqual(redact.qloo_problems("qloo/x.json", document), [])


def _tempdir():
    import tempfile

    return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()
