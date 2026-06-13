import gzip
import os
import pytest
from nosograph.utils.vcf import _parse_ann, parse_medaka_vcf, parse_snippy_vcf

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../../.claude/sample_files")
HIV_VCF = os.path.join(SAMPLE_DIR, "hiv.sample_1_medaka.annotated.vcf")
SNIPPY_VCF = os.path.join(SAMPLE_DIR, "bacterial_samples.snps.vcf")

# Gzipped per-reference subsets cut from the real HIV-64148 pipeline output
# (05_medaka_variant/<REF>/medaka.annotated.vcf.gz). (accession, path) pairs.
HXB2_GZ = os.path.join(SAMPLE_DIR, "hiv64148_HXB2_subset.medaka.annotated.vcf.gz")
CRF01_AE_GZ = os.path.join(SAMPLE_DIR, "hiv64148_CRF01_AE_subset.medaka.annotated.vcf.gz")
GZ_FIXTURES = [("K03455.1", HXB2_GZ), ("AF164485.1", CRF01_AE_GZ)]


class TestParseAnn:
    def test_single_annotation(self):
        ann = "G|synonymous_variant|LOW|FPKKOBOA_00001|GENE_FPKKOBOA_00001|transcript|TR_001|protein_coding|1/1|c.480A>G|p.Gly160Gly|480/1455|480/1455|160/484||"
        result = _parse_ann(ann)
        assert len(result) == 1
        assert result[0]["effect"] == "synonymous_variant"
        assert result[0]["impact"] == "LOW"
        assert result[0]["gene_name"] == "FPKKOBOA_00001"
        assert result[0]["hgvs_c"] == "c.480A>G"
        assert result[0]["hgvs_p"] == "p.Gly160Gly"

    def test_multiple_annotations(self):
        ann = (
            "A|upstream_gene_variant|MODIFIER|gag|Gene_789|transcript|AAB|protein_coding||c.-240C>A|||||240|,"
            "A|intergenic_region|MODIFIER|CHR_START-gag|CHR_START-Gene_789|intergenic_region|CHR_START-Gene_789|||n.550C>A||||||"
        )
        result = _parse_ann(ann)
        assert len(result) == 2
        assert result[0]["hgvs_c"] == "c.-240C>A"
        assert result[1]["hgvs_c"] == "n.550C>A"

    def test_empty_ann(self):
        result = _parse_ann("")
        assert result == []


@pytest.mark.skipif(not os.path.exists(HIV_VCF), reason="HIV sample VCF not found")
class TestMedakaParser:
    def test_returns_list(self):
        records = parse_medaka_vcf(HIV_VCF, "K03455.1", "S001")
        assert isinstance(records, list)
        assert len(records) > 0

    def test_record_has_required_fields(self):
        records = parse_medaka_vcf(HIV_VCF, "K03455.1", "S001")
        r = records[0]
        assert r["REF_ACC"] == "K03455.1"
        assert isinstance(r["POS"], int)
        assert r["sample_id"] == "S001"
        assert r["vcf_source"] == "medaka"
        assert "hgvs_c" in r
        assert "hgvs_p" in r

    def test_one_row_produces_multiple_records_for_overlapping_orfs(self):
        records = parse_medaka_vcf(HIV_VCF, "K03455.1", "S001")
        pos_counts: dict[int, int] = {}
        for r in records:
            pos_counts[r["POS"]] = pos_counts.get(r["POS"], 0) + 1
        assert max(pos_counts.values()) > 1, "Expected at least one position with multiple gene annotations"

    def test_gq_present_ao_ro_absent(self):
        records = parse_medaka_vcf(HIV_VCF, "K03455.1", "S001")
        r = records[0]
        assert r.get("GQ") is not None
        assert r.get("AO") is None

    def test_parses_gzipped_vcf(self, tmp_path):
        # The HIV-64148 pipeline emits per-reference VCFs as .vcf.gz; parsing a
        # gzipped file must yield the same records as the uncompressed input.
        gz = tmp_path / "hiv.vcf.gz"
        with open(HIV_VCF, "rb") as src, gzip.open(gz, "wb") as dst:
            dst.write(src.read())
        assert parse_medaka_vcf(str(gz), "K03455.1", "S001") == \
            parse_medaka_vcf(HIV_VCF, "K03455.1", "S001")


@pytest.mark.parametrize("ref_acc,path", GZ_FIXTURES)
class TestGzippedMedakaFixtures:
    """Functional parse checks against real gzipped HIV-64148 per-reference VCFs."""

    def test_parses_to_records(self, ref_acc, path):
        records = parse_medaka_vcf(path, ref_acc, "03D1")
        assert isinstance(records, list)
        assert len(records) > 0

    def test_ref_acc_and_source_passthrough(self, ref_acc, path):
        records = parse_medaka_vcf(path, ref_acc, "03D1")
        assert all(r["REF_ACC"] == ref_acc for r in records)
        assert all(r["vcf_source"] == "medaka" for r in records)
        assert all(r["sample_id"] == "03D1" for r in records)

    def test_all_variant_types_present(self, ref_acc, path):
        records = parse_medaka_vcf(path, ref_acc, "03D1")
        assert {r["TYPE"] for r in records} == {"SNP", "MNP", "INDEL", "OTHER"}

    def test_multiple_annotations_per_position(self, ref_acc, path):
        # Gene-annotation-level design: a row with several SnpEff ANN entries
        # yields several records sharing one POS — must survive gzip decoding.
        records = parse_medaka_vcf(path, ref_acc, "03D1")
        pos_counts: dict[int, int] = {}
        for r in records:
            pos_counts[r["POS"]] = pos_counts.get(r["POS"], 0) + 1
        assert max(pos_counts.values()) > 1

    def test_annotation_and_format_fields_populated(self, ref_acc, path):
        records = parse_medaka_vcf(path, ref_acc, "03D1")
        assert all(r["gene_name"] and r["EFFECT"] and r["IMPACT"] for r in records)
        assert all("hgvs_c" in r and "hgvs_p" in r for r in records)
        assert any(r.get("GQ") is not None for r in records)  # FORMAT=GT:GQ


@pytest.mark.skipif(not os.path.exists(SNIPPY_VCF), reason="Snippy sample VCF not found")
class TestSnippyParser:
    def test_returns_list(self):
        records = parse_snippy_vcf(SNIPPY_VCF, "ref_acc_001", "S002")
        assert isinstance(records, list)
        assert len(records) > 0

    def test_record_has_required_fields(self):
        records = parse_snippy_vcf(SNIPPY_VCF, "ref_acc_001", "S002")
        r = records[0]
        assert r["REF_ACC"] == "ref_acc_001"
        assert r["vcf_source"] == "snippy"
        assert "hgvs_c" in r

    def test_ao_ro_present_gq_absent(self):
        records = parse_snippy_vcf(SNIPPY_VCF, "ref_acc_001", "S002")
        r = records[0]
        assert r.get("GQ") is None
        assert r.get("AO") is not None

    def test_hgvs_c_populated_from_ann(self):
        records = parse_snippy_vcf(SNIPPY_VCF, "ref_acc_001", "S002")
        with_hgvs = [r for r in records if r["hgvs_c"]]
        assert len(with_hgvs) > 0
