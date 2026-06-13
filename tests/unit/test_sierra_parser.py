import json
import os
import pytest
from nosograph.utils.sierra import parse_sierra_records, parse_sierra_json, _unwrap

EXAMPLE_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "sierrapy_result.example.json")


# A trimmed but structurally faithful sierrapy/Stanford HIVdb response.
SIERRA_LIST = [
    {
        "inputSequence": {"header": "patient_seq_1"},
        "drugResistance": [
            {
                "gene": {"name": "RT"},
                "drugScores": [
                    {
                        "drugClass": {"name": "NRTI"},
                        "drug": {"name": "ABC", "displayAbbr": "ABC", "fullName": "abacavir"},
                        "score": 15.0,
                        "text": "Low-Level Resistance",
                        "partialScores": [
                            {"mutations": [{"text": "M184V"}], "score": 15.0},
                        ],
                    },
                    {
                        "drugClass": {"name": "NNRTI"},
                        "drug": {"name": "EFV", "displayAbbr": "EFV", "fullName": "efavirenz"},
                        "score": 0.0,
                        "text": "Susceptible",
                        "partialScores": [],
                    },
                ],
            }
        ],
    }
]


class TestUnwrap:
    def test_bare_list(self):
        assert _unwrap(SIERRA_LIST) == SIERRA_LIST

    def test_sequence_analysis_dict(self):
        assert _unwrap({"sequenceAnalysis": SIERRA_LIST}) == SIERRA_LIST

    def test_graphql_envelope(self):
        assert _unwrap({"data": {"sequenceAnalysis": SIERRA_LIST}}) == SIERRA_LIST

    def test_unknown_shape_raises(self):
        with pytest.raises(ValueError, match="Unrecognized"):
            _unwrap(42)


class TestParseRecords:
    def test_one_record_per_drug(self):
        recs = parse_sierra_records(SIERRA_LIST, "SAMPLE1")
        assert len(recs) == 2
        drugs = {r["drug_name"] for r in recs}
        assert drugs == {"ABC", "EFV"}

    def test_prediction_id_and_provenance(self):
        recs = parse_sierra_records(SIERRA_LIST, "SAMPLE1")
        abc = next(r for r in recs if r["drug_name"] == "ABC")
        assert abc["prediction_id"] == "SAMPLE1:RT:ABC"
        assert abc["sample_id"] == "SAMPLE1"
        assert abc["gene"] == "RT"
        assert abc["drug_class"] == "NRTI"
        assert abc["score"] == 15.0
        assert abc["level"] == "Low-Level Resistance"
        assert abc["drug_full_name"] == "abacavir"

    def test_mutations_flattened_with_score(self):
        recs = parse_sierra_records(SIERRA_LIST, "SAMPLE1")
        abc = next(r for r in recs if r["drug_name"] == "ABC")
        assert abc["mutations"] == [{"gene": "RT", "text": "M184V", "score": 15.0}]

    def test_no_mutations_yields_empty_list(self):
        recs = parse_sierra_records(SIERRA_LIST, "SAMPLE1")
        efv = next(r for r in recs if r["drug_name"] == "EFV")
        assert efv["mutations"] == []

    def test_drug_without_name_skipped(self):
        data = [{"drugResistance": [{"gene": {"name": "RT"}, "drugScores": [
            {"drugClass": {"name": "NRTI"}, "drug": {}, "score": 0, "text": "S", "partialScores": []}
        ]}]}]
        assert parse_sierra_records(data, "S1") == []


class TestParseJson:
    def test_reads_file(self, tmp_path):
        p = tmp_path / "sierra.json"
        p.write_text(json.dumps(SIERRA_LIST), encoding="utf-8")
        recs = parse_sierra_json(str(p), "SAMPLE1")
        assert len(recs) == 2
        assert recs[0]["sample_id"] == "SAMPLE1"

    def test_parses_bundled_example_fixture(self):
        # The fixture referenced by the README must parse cleanly.
        recs = parse_sierra_json(EXAMPLE_JSON, "EX_SAMPLE")
        assert {"ABC", "3TC", "EFV"} <= {r["drug_name"] for r in recs}
        assert "M184V" in {m["text"] for r in recs for m in r["mutations"]}
        assert all(r["sample_id"] == "EX_SAMPLE" for r in recs)
