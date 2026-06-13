from unittest.mock import MagicMock
import pytest
from nosograph.models.genomics import Variant
from nosograph.repositories.analytics import AnalyticsRepository, _to_variant, _to_call


class TestHelpers:
    def test_to_variant_builds_model(self):
        raw = {
            "REF_ACC": "K03455.1", "POS": 2800, "REF": "A", "ALT": "G",
            "hgvs_c": "c.1A>G", "hgvs_p": "p.Met1?", "gene_name": "gag",
            "CHROM": "chr1", "TYPE": "SNP", "EFFECT": "missense", "IMPACT": "MODERATE",
        }
        v = _to_variant(raw)
        assert isinstance(v, Variant)
        assert v.POS == 2800
        assert v.gene_name == "gag"
        assert v.hgvs_c == "c.1A>G"

    def test_to_variant_defaults_hgvs_to_empty(self):
        v = _to_variant({"REF_ACC": "R", "POS": 1, "REF": "A", "ALT": "T"})
        assert v.hgvs_c == ""
        assert v.hgvs_p == ""

    def test_to_call_extracts_known_keys(self):
        raw = {"DP": 30, "GT": "1", "QUAL": 35.5, "GQ": 36,
               "AO": 10, "RO": 20, "FILTER": "PASS", "vcf_source": "medaka", "extra": "ignored"}
        call = _to_call(raw)
        assert call["DP"] == 30
        assert call["vcf_source"] == "medaka"
        assert "extra" not in call


class TestValidation:
    def test_ward_variant_clusters_rejects_below_one(self):
        repo = AnalyticsRepository(MagicMock())
        with pytest.raises(ValueError, match="min_patients"):
            repo.ward_variant_clusters(min_patients=0)
        # Validation must happen before any session is opened.
        repo._driver.session.assert_not_called()
