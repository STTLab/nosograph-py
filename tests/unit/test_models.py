from datetime import date
import pytest
from pydantic import ValidationError
from nosograph.models.patient import Patient, Admission, Ward, Department, OpdVisit
from nosograph.models.specimen import Specimen, Sample
from nosograph.models.genomics import Organism, ReferenceGenome, Assembly, Contig, Variant
from nosograph.models.lab import LabResult, HIVViralLoad


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

class TestPatient:
    def test_valid_with_age(self):
        p = Patient(patient_id="P001", firstname="Alice", lastname="Smith", age=30)
        assert p.age == 30
        assert p.date_of_birth is None

    def test_valid_with_dob(self):
        p = Patient(patient_id="P002", firstname="Bob", lastname="Jones", date_of_birth=date(1990, 1, 1))
        assert p.date_of_birth == date(1990, 1, 1)

    def test_requires_dob_or_age(self):
        with pytest.raises(ValidationError, match="date_of_birth or age"):
            Patient(patient_id="P003", firstname="X", lastname="Y")

    def test_sex_accepts_m_f_other(self):
        for s in ("M", "F", "Other"):
            assert Patient(patient_id="P004", firstname="X", lastname="Y", age=25, sex=s).sex == s

    def test_sex_rejects_unknown_value(self):
        with pytest.raises(ValidationError):
            Patient(patient_id="P004", firstname="X", lastname="Y", age=25, sex="Z")

    def test_sex_optional(self):
        p = Patient(patient_id="P005", firstname="X", lastname="Y", age=25)
        assert p.sex is None


# ---------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------

class TestAdmission:
    def test_valid_minimal(self):
        a = Admission(admission_id="A001")
        assert a.admission_id == "A001"

    def test_valid_with_dates(self):
        a = Admission(
            admission_id="A002",
            date_of_admission=date(2025, 1, 1),
            date_of_discharge=date(2025, 1, 10),
        )
        assert a.length_of_stay is None  # computed by DB, not here

    def test_discharge_before_admission_raises(self):
        with pytest.raises(ValidationError, match="before date_of_admission"):
            Admission(
                admission_id="A003",
                date_of_admission=date(2025, 5, 10),
                date_of_discharge=date(2025, 5, 1),
            )


# ---------------------------------------------------------------------------
# Ward / Department
# ---------------------------------------------------------------------------

class TestWard:
    def test_valid(self):
        w = Ward(ward_id="W1", name="ICU", department_id="D1")
        assert w.ward_id == "W1"

    def test_optional_fields(self):
        w = Ward(ward_id="W2", name="Pediatrics", department_id="D2", ward_type="Inpatient")
        assert w.ward_type == "Inpatient"
        assert w.description is None


class TestDepartment:
    def test_valid(self):
        d = Department(department_id="D1", name="Surgery")
        assert d.description is None


# ---------------------------------------------------------------------------
# OpdVisit
# ---------------------------------------------------------------------------

class TestOpdVisit:
    def test_minimal(self):
        v = OpdVisit(visit_id="OPD001")
        assert v.visit_id == "OPD001"
        assert v.visit_date is None
        assert v.clinic is None
        assert v.chief_complaint is None
        assert v.notes is None

    def test_full(self):
        v = OpdVisit(
            visit_id="OPD002",
            visit_date=date(2025, 6, 1),
            clinic="HIV Clinic",
            chief_complaint="Routine follow-up",
            notes="Viral load stable.",
        )
        assert v.visit_date == date(2025, 6, 1)
        assert v.clinic == "HIV Clinic"
        assert v.chief_complaint == "Routine follow-up"
        assert v.notes == "Viral load stable."

    def test_visit_id_required(self):
        with pytest.raises(ValidationError):
            OpdVisit()


# ---------------------------------------------------------------------------
# Specimen / Sample
# ---------------------------------------------------------------------------

class TestSpecimen:
    def test_valid_minimal(self):
        s = Specimen(specimen_id="SP001")
        assert s.specimen_type is None

    def test_valid_with_type(self):
        s = Specimen(specimen_id="SP002", specimen_type="Blood")
        assert s.specimen_type == "Blood"


class TestSample:
    def test_valid(self):
        s = Sample(sample_id="SAM001")
        assert s.sample_id == "SAM001"


# ---------------------------------------------------------------------------
# Genomics
# ---------------------------------------------------------------------------

class TestOrganism:
    def test_valid(self):
        o = Organism(taxid="1280", sciname="Staphylococcus aureus")
        assert o.taxid == "1280"


class TestReferenceGenome:
    def test_valid_minimal(self):
        r = ReferenceGenome(accession_no="NC_007795.1")
        assert r.name is None

    def test_valid_full(self):
        r = ReferenceGenome(
            accession_no="NC_007795.1",
            name="Staph aureus MRSA252",
            molecular_type="genomic DNA",
            strain="MRSA252",
            annotation_source="RefSeq",
            source_database="NCBI",
        )
        assert r.strain == "MRSA252"


class TestAssembly:
    def test_valid_minimal(self):
        a = Assembly(assembly_id="ASM001")
        assert a.assembler is None


class TestContig:
    def test_valid(self):
        c = Contig(contig_id="c1", length=500, sequence="ATCG", sequence_hash="abc123")
        assert c.hash_algorithm == "md5"


class TestVariant:
    def test_minimal_required_fields(self):
        v = Variant(REF_ACC="NC_000001.11", POS=123456, REF="A", ALT="G")
        assert v.REF_ACC == "NC_000001.11"
        assert v.POS == 123456
        assert v.hgvs_c == ""
        assert v.hgvs_p == ""

    def test_with_annotation_fields(self):
        v = Variant(
            REF_ACC="K03455.1",
            POS=2800,
            REF="A",
            ALT="G",
            hgvs_c="c.480A>G",
            hgvs_p="p.Gly160Gly",
            gene_name="gag",
            EFFECT="synonymous_variant",
            IMPACT="LOW",
        )
        assert v.hgvs_c == "c.480A>G"
        assert v.gene_name == "gag"

    def test_optional_fields_default_none(self):
        v = Variant(REF_ACC="X", POS=1, REF="A", ALT="T")
        assert v.EFFECT is None
        assert v.CHROM is None
        assert v.gene_name is None


# ---------------------------------------------------------------------------
# LabResult
# ---------------------------------------------------------------------------

class TestLabResult:
    def test_minimal(self):
        lr = LabResult(lab_id="LR001")
        assert lr.lab_id == "LR001"
        assert lr.result_type is None
        assert lr.test_date is None

    def test_full(self):
        lr = LabResult(
            lab_id="LR002",
            specimen_id="SP001",
            result_type="CBC",
            test_date=date(2025, 6, 1),
            value="12.5",
            unit="g/dL",
            notes="Mild anaemia",
        )
        assert lr.result_type == "CBC"
        assert lr.test_date == date(2025, 6, 1)
        assert lr.value == "12.5"

    def test_lab_id_required(self):
        with pytest.raises(ValidationError):
            LabResult()


# ---------------------------------------------------------------------------
# HIVViralLoad
# ---------------------------------------------------------------------------

class TestHIVViralLoad:
    def test_minimal(self):
        vl = HIVViralLoad(viral_load_id="VL001")
        assert vl.viral_load_id == "VL001"
        assert vl.value_copies_per_ml is None

    def test_detected(self):
        vl = HIVViralLoad(
            viral_load_id="VL002",
            test_date=date(2025, 3, 15),
            value_copies_per_ml=50000,
            log10_value=4.699,
            detection_limit=50,
            assay_type="Abbott RealTime HIV-1",
            result_status="detected",
        )
        assert vl.result_status == "detected"
        assert vl.value_copies_per_ml == 50000

    def test_undetected(self):
        vl = HIVViralLoad(viral_load_id="VL003", result_status="undetected")
        assert vl.result_status == "undetected"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            HIVViralLoad(viral_load_id="VL004", result_status="positive")

    def test_viral_load_id_required(self):
        with pytest.raises(ValidationError):
            HIVViralLoad()
