import json
import os
from datetime import date
import pytest
from nosograph import (
    Patient, Admission, Ward, Department, OpdVisit,
    Specimen, Sample,
    Organism, ReferenceGenome, Assembly, Contig,
    LabResult, HIVViralLoad,
    Variant, VariantCallProps,
    DrugClass, Drug, Mutation, StanfordHIVDRPrediction,
)


SIERRA_REPORT = [
    {
        "inputSequence": {"header": "seq1"},
        "drugResistance": [
            {
                "gene": {"name": "RT"},
                "drugScores": [
                    {
                        "drugClass": {"name": "NRTI"},
                        "drug": {"name": "ABC", "displayAbbr": "ABC", "fullName": "abacavir"},
                        "score": 15.0,
                        "text": "Low-Level Resistance",
                        "partialScores": [{"mutations": [{"text": "M184V"}], "score": 15.0}],
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

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../../.claude/sample_files")
HIV_VCF = os.path.join(SAMPLE_DIR, "hiv.sample_1_medaka.annotated.vcf")
SNIPPY_VCF = os.path.join(SAMPLE_DIR, "bacterial_samples.snps.vcf")
# Gzipped per-reference subsets cut from real HIV-64148 pipeline output.
HXB2_GZ = os.path.join(SAMPLE_DIR, "hiv64148_HXB2_subset.medaka.annotated.vcf.gz")
CRF01_AE_GZ = os.path.join(SAMPLE_DIR, "hiv64148_CRF01_AE_subset.medaka.annotated.vcf.gz")


# ---------------------------------------------------------------------------
# PatientRepository
# ---------------------------------------------------------------------------

class TestPatientRepository:
    def test_create_get_delete(self, graph):
        p = Patient(patient_id="P001", firstname="Alice", lastname="Smith", age=30)
        graph.patients.create(p)

        fetched = graph.patients.get("P001")
        assert fetched is not None
        assert fetched.firstname == "Alice"
        assert fetched.age == 30

        graph.patients.delete("P001")
        assert graph.patients.get("P001") is None

    def test_create_duplicate_raises(self, graph):
        p = Patient(patient_id="P002", firstname="Bob", lastname="Jones", age=25)
        graph.patients.create(p)
        with pytest.raises(ValueError, match="already exists"):
            graph.patients.create(p)

    def test_get_nonexistent_returns_none(self, graph):
        assert graph.patients.get("DOES_NOT_EXIST") is None

    def test_link_admission(self, graph):
        graph.patients.create(Patient(patient_id="P003", firstname="C", lastname="D", age=40))
        graph.admissions.create(Admission(admission_id="ADM001"))
        graph.patients.link_admission("P003", "ADM001")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (p:Patient {patient_id:'P003'})-[:HAS_ADMISSION]->(a:Admission {admission_id:'ADM001'}) RETURN a"
            ).single()
        assert result is not None


# ---------------------------------------------------------------------------
# AdmissionRepository
# ---------------------------------------------------------------------------

class TestAdmissionRepository:
    def test_create_get_delete(self, graph):
        a = Admission(
            admission_id="ADM002",
            date_of_admission=date(2025, 3, 1),
            date_of_discharge=date(2025, 3, 10),
        )
        graph.admissions.create(a)

        fetched = graph.admissions.get("ADM002")
        assert fetched is not None
        assert fetched.admission_id == "ADM002"

        graph.admissions.delete("ADM002")
        assert graph.admissions.get("ADM002") is None

    def test_link_ward(self, graph):
        graph.admissions.create(Admission(admission_id="ADM003"))
        graph.wards.create(Ward(ward_id="W01", name="ICU", department_id="D01"))
        graph.admissions.link_ward("ADM003", "W01", room_no="101", bed_no="A")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (a:Admission {admission_id:'ADM003'})-[r:ADMITTED_TO]->(w:Ward {ward_id:'W01'}) RETURN r"
            ).single()
        assert result is not None


# ---------------------------------------------------------------------------
# SpecimenRepository / SampleRepository
# ---------------------------------------------------------------------------

class TestSpecimenRepository:
    def test_create_get_delete(self, graph):
        s = Specimen(specimen_id="SP001", specimen_type="Blood")
        graph.specimens.create(s)

        fetched = graph.specimens.get("SP001")
        assert fetched is not None
        assert fetched.specimen_id == "SP001"

        graph.specimens.delete("SP001")
        assert graph.specimens.get("SP001") is None

    def test_link_patient(self, graph):
        graph.patients.create(Patient(patient_id="P010", firstname="E", lastname="F", age=50))
        graph.specimens.create(Specimen(specimen_id="SP002"))
        graph.specimens.link_patient("SP002", "P010")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (sp:Specimen {specimen_id:'SP002'})-[:COLLECTED_FROM]->(p:Patient {patient_id:'P010'}) RETURN sp"
            ).single()
        assert result is not None


class TestSampleRepository:
    def test_create_get_delete(self, graph):
        s = Sample(sample_id="SAM001")
        graph.samples.create(s)

        fetched = graph.samples.get("SAM001")
        assert fetched is not None

        graph.samples.delete("SAM001")
        assert graph.samples.get("SAM001") is None

    def test_link_assembly(self, graph):
        graph.samples.create(Sample(sample_id="SAM002"))
        graph.assemblies.create(Assembly(assembly_id="ASM001", assembler="flye"))
        graph.samples.link_assembly("SAM002", "ASM001")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (s:Sample {sample_id:'SAM002'})-[:HAS_ASSEMBLY]->(a:Assembly {assembly_id:'ASM001'}) RETURN a"
            ).single()
        assert result is not None

    def test_link_specimen(self, graph):
        graph.samples.create(Sample(sample_id="SAM003"))
        graph.specimens.create(Specimen(specimen_id="SP_SAM"))
        graph.samples.link_specimen("SAM003", "SP_SAM")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (sa:Sample {sample_id:'SAM003'})-[:DERIVED_FROM]->(sp:Specimen {specimen_id:'SP_SAM'}) RETURN sp"
            ).single()
        assert result is not None


# ---------------------------------------------------------------------------
# OrganismRepository / AssemblyRepository / ReferenceGenomeRepository
# ---------------------------------------------------------------------------

class TestOrganismRepository:
    def test_create_get_delete(self, graph):
        o = Organism(taxid="1280", sciname="Staphylococcus aureus")
        graph.organisms.create(o)

        fetched = graph.organisms.get("1280")
        assert fetched is not None
        assert fetched.sciname == "Staphylococcus aureus"

        graph.organisms.delete("1280")
        assert graph.organisms.get("1280") is None

    def test_link_reference_genome(self, graph):
        graph.organisms.create(Organism(taxid="1281"))
        graph.reference_genomes.create(ReferenceGenome(accession_no="NC_001"))
        graph.organisms.link_reference_genome("1281", "NC_001")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (refg:ReferenceGenome {accession_no:'NC_001'})-[:REFERENCE_GENOME_OF]->(o:Organism {taxid:'1281'}) RETURN refg"
            ).single()
        assert result is not None


class TestAssemblyRepository:
    def test_create_get_delete(self, graph):
        a = Assembly(assembly_id="ASM010", assembler="flye")
        graph.assemblies.create(a)

        fetched = graph.assemblies.get("ASM010")
        assert fetched is not None
        assert fetched.assembly_id == "ASM010"

        graph.assemblies.delete("ASM010")
        assert graph.assemblies.get("ASM010") is None

    def test_add_contigs(self, graph):
        graph.assemblies.create(Assembly(assembly_id="ASM020", assembler="canu"))
        contigs = [
            Contig(contig_id="c1", length=100, sequence="ATCG" * 25, sequence_hash="hash1"),
            Contig(contig_id="c2", length=200, sequence="GCTA" * 50, sequence_hash="hash2"),
        ]
        stats = graph.assemblies.add_contigs("ASM020", contigs)
        assert stats["nodes_created"] == 2
        assert stats["relationships_created"] == 2


class TestReferenceGenomeRepository:
    def test_create_get_delete(self, graph):
        r = ReferenceGenome(accession_no="NC_007795.1", name="S. aureus MRSA252", strain="MRSA252")
        graph.reference_genomes.create(r)

        fetched = graph.reference_genomes.get("NC_007795.1")
        assert fetched is not None
        assert fetched.name == "S. aureus MRSA252"

        graph.reference_genomes.delete("NC_007795.1")
        assert graph.reference_genomes.get("NC_007795.1") is None


# ---------------------------------------------------------------------------
# WardRepository / DepartmentRepository
# ---------------------------------------------------------------------------

class TestWardRepository:
    def test_create_get(self, graph):
        graph.departments.create(Department(department_id="D001", name="Medicine"))
        w = Ward(ward_id="W001", name="Cardiac ICU", department_id="D001", ward_type="ICU")
        graph.wards.create(w)

        fetched = graph.wards.get("W001")
        assert fetched is not None
        assert fetched.name == "Cardiac ICU"
        assert fetched.ward_type == "ICU"

    def test_link_department(self, graph):
        graph.departments.create(Department(department_id="D002", name="Surgery"))
        graph.wards.create(Ward(ward_id="W002", name="OR", department_id="D002"))
        graph.wards.link_department("W002", "D002")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (w:Ward {ward_id:'W002'})-[:IN_DEPARTMENT]->(d:Department {department_id:'D002'}) RETURN d"
            ).single()
        assert result is not None


class TestDepartmentRepository:
    def test_create_get(self, graph):
        d = Department(department_id="D010", name="Neurology", description="Brain and nerves")
        graph.departments.create(d)

        fetched = graph.departments.get("D010")
        assert fetched is not None
        assert fetched.name == "Neurology"
        assert fetched.description == "Brain and nerves"

    def test_get_nonexistent_returns_none(self, graph):
        assert graph.departments.get("NOPE") is None


# ---------------------------------------------------------------------------
# LabResultRepository
# ---------------------------------------------------------------------------

class TestLabResultRepository:
    def test_create_get_delete(self, graph):
        lr = LabResult(
            lab_id="LR001",
            result_type="CBC",
            test_date=date(2025, 6, 1),
            value="12.5",
            unit="g/dL",
        )
        graph.lab_results.create(lr)

        fetched = graph.lab_results.get("LR001")
        assert fetched is not None
        assert fetched.lab_id == "LR001"
        assert fetched.result_type == "CBC"
        assert fetched.test_date == date(2025, 6, 1)

        graph.lab_results.delete("LR001")
        assert graph.lab_results.get("LR001") is None

    def test_get_nonexistent_returns_none(self, graph):
        assert graph.lab_results.get("DOES_NOT_EXIST") is None

    def test_link_specimen(self, graph):
        graph.specimens.create(Specimen(specimen_id="SP_LR01"))
        graph.lab_results.create(LabResult(lab_id="LR_LINK01"))
        graph.lab_results.link_specimen("LR_LINK01", "SP_LR01")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (sp:Specimen {specimen_id:'SP_LR01'})-[:TESTED_FOR]->(lr:LabResult {lab_id:'LR_LINK01'}) RETURN lr"
            ).single()
        assert result is not None


# ---------------------------------------------------------------------------
# HIVViralLoadRepository
# ---------------------------------------------------------------------------

class TestHIVViralLoadRepository:
    def test_create_get_delete(self, graph):
        vl = HIVViralLoad(
            viral_load_id="VL001",
            test_date=date(2025, 3, 15),
            value_copies_per_ml=50000,
            log10_value=4.699,
            detection_limit=50,
            assay_type="Abbott RealTime HIV-1",
            result_status="detected",
        )
        graph.hiv_viral_loads.create(vl)

        fetched = graph.hiv_viral_loads.get("VL001")
        assert fetched is not None
        assert fetched.viral_load_id == "VL001"
        assert fetched.value_copies_per_ml == 50000
        assert fetched.result_status == "detected"
        assert fetched.test_date == date(2025, 3, 15)

        graph.hiv_viral_loads.delete("VL001")
        assert graph.hiv_viral_loads.get("VL001") is None

    def test_get_nonexistent_returns_none(self, graph):
        assert graph.hiv_viral_loads.get("DOES_NOT_EXIST") is None

    def test_link_patient(self, graph):
        graph.patients.create(Patient(patient_id="P_VL01", firstname="A", lastname="B", age=35))
        graph.hiv_viral_loads.create(HIVViralLoad(viral_load_id="VL_LINK01", result_status="undetected"))
        graph.hiv_viral_loads.link_patient("VL_LINK01", "P_VL01")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (p:Patient {patient_id:'P_VL01'})-[:HAS_HIV_VIRAL_LOAD_RESULT]->(vl:HIVViralLoad {viral_load_id:'VL_LINK01'}) RETURN vl"
            ).single()
        assert result is not None


# ---------------------------------------------------------------------------
# OpdVisitRepository
# ---------------------------------------------------------------------------

class TestOpdVisitRepository:
    def test_create_get_delete(self, graph):
        v = OpdVisit(
            visit_id="OPD001",
            visit_date=date(2025, 6, 1),
            clinic="HIV Clinic",
            chief_complaint="Routine follow-up",
            notes="Stable. Continue ART.",
        )
        graph.opd_visits.create(v)

        fetched = graph.opd_visits.get("OPD001")
        assert fetched is not None
        assert fetched.visit_id == "OPD001"
        assert fetched.visit_date == date(2025, 6, 1)
        assert fetched.clinic == "HIV Clinic"
        assert fetched.chief_complaint == "Routine follow-up"

        graph.opd_visits.delete("OPD001")
        assert graph.opd_visits.get("OPD001") is None

    def test_create_minimal(self, graph):
        graph.opd_visits.create(OpdVisit(visit_id="OPD002"))
        fetched = graph.opd_visits.get("OPD002")
        assert fetched is not None
        assert fetched.visit_date is None
        assert fetched.clinic is None

    def test_get_nonexistent_returns_none(self, graph):
        assert graph.opd_visits.get("DOES_NOT_EXIST") is None

    def test_link_patient(self, graph):
        graph.patients.create(Patient(patient_id="P_OPD01", firstname="A", lastname="B", age=30))
        graph.opd_visits.create(OpdVisit(visit_id="OPD_LINK01", clinic="ANC"))
        graph.opd_visits.link_patient("OPD_LINK01", "P_OPD01")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (p:Patient {patient_id:'P_OPD01'})-[:HAS_OPD_VISIT]->(v:OpdVisit {visit_id:'OPD_LINK01'}) RETURN v"
            ).single()
        assert result is not None

    def test_link_specimen_collected_at_visit(self, graph):
        graph.opd_visits.create(OpdVisit(visit_id="OPD_SP01", clinic="HIV Clinic"))
        graph.specimens.create(Specimen(specimen_id="SP_OPD01", specimen_type="Blood"))
        graph.specimens.link_visit("SP_OPD01", "OPD_SP01")

        with graph.driver.session() as s:
            result = s.run(
                "MATCH (s:Specimen {specimen_id:'SP_OPD01'})-[:COLLECTED_AT_VISIT]->(v:OpdVisit {visit_id:'OPD_SP01'}) RETURN v"
            ).single()
        assert result is not None

    def test_full_opd_workflow(self, graph):
        """Patient → OpdVisit → Specimen → LabResult chain."""
        graph.patients.create(Patient(patient_id="P_WF01", firstname="C", lastname="D", age=45))
        graph.opd_visits.create(OpdVisit(visit_id="OPD_WF01", visit_date=date(2025, 6, 7), clinic="HIV Clinic"))
        graph.opd_visits.link_patient("OPD_WF01", "P_WF01")

        graph.specimens.create(Specimen(specimen_id="SP_WF01", specimen_type="Blood"))
        graph.specimens.link_patient("SP_WF01", "P_WF01")
        graph.specimens.link_visit("SP_WF01", "OPD_WF01")

        graph.lab_results.create(LabResult(lab_id="LR_WF01", result_type="CBC", value="13.0", unit="g/dL"))
        graph.lab_results.link_specimen("LR_WF01", "SP_WF01")

        with graph.driver.session() as s:
            result = s.run("""
                MATCH (p:Patient {patient_id:'P_WF01'})-[:HAS_OPD_VISIT]->(v:OpdVisit {visit_id:'OPD_WF01'})
                      <-[:COLLECTED_AT_VISIT]-(sp:Specimen {specimen_id:'SP_WF01'})
                      -[:TESTED_FOR]->(lr:LabResult {lab_id:'LR_WF01'})
                RETURN lr.value AS val
            """).single()
        assert result is not None
        assert result["val"] == "13.0"


# ---------------------------------------------------------------------------
# VariantRepository
# ---------------------------------------------------------------------------

class TestVariantRepository:
    def test_create_get_delete(self, graph):
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
            TYPE="SNP",
        )
        graph.variants.create(v)
        fetched = graph.variants.get("K03455.1", 2800, "A", "G", "c.480A>G", "p.Gly160Gly")
        assert fetched is not None
        assert fetched.gene_name == "gag"
        assert fetched.hgvs_c == "c.480A>G"

        graph.variants.delete("K03455.1", 2800, "A", "G", "c.480A>G", "p.Gly160Gly")
        assert graph.variants.get("K03455.1", 2800, "A", "G", "c.480A>G", "p.Gly160Gly") is None

    def test_get_nonexistent_returns_none(self, graph):
        result = graph.variants.get("NONE", 1, "A", "G", "", "")
        assert result is None

    def test_link_sample_and_get_by_sample(self, graph):
        graph.samples.create(Sample(sample_id="SVAR_01"))
        v = Variant(REF_ACC="K03455.1", POS=3000, REF="C", ALT="T", hgvs_c="c.600C>T", hgvs_p="", gene_name="pol", TYPE="SNP")
        graph.variants.create(v)
        call: VariantCallProps = {"DP": 20, "GT": "1", "QUAL": 35.5, "GQ": 36, "vcf_source": "medaka"}
        graph.variants.link_sample(v, "SVAR_01", call)

        pairs = graph.variants.get_by_sample("SVAR_01")
        assert len(pairs) == 1
        fetched_v, fetched_c = pairs[0]
        assert fetched_v.hgvs_c == "c.600C>T"
        assert fetched_c["vcf_source"] == "medaka"
        assert fetched_c["GQ"] == 36

    def test_get_by_ref(self, graph):
        v = Variant(REF_ACC="REF_TEST_01", POS=100, REF="A", ALT="T", hgvs_c="c.100A>T", hgvs_p="p.Lys34Ile", gene_name="ORF1")
        graph.variants.create(v)
        results = graph.variants.get_by_ref("REF_TEST_01")
        assert any(r.hgvs_c == "c.100A>T" for r in results)

    @pytest.mark.skipif(not os.path.exists(SNIPPY_VCF), reason="Snippy sample VCF not found")
    def test_bulk_import_snippy(self, graph):
        graph.samples.create(Sample(sample_id="SVAR_SNIPPY"))
        stats = graph.variants.bulk_import_from_vcf(SNIPPY_VCF, "SVAR_SNIPPY", "ref_bac_001", "snippy", batch_size=50)
        assert stats["nodes_created"] > 0
        assert stats["relationships_created"] > 0
        pairs = graph.variants.get_by_sample("SVAR_SNIPPY")
        assert len(pairs) > 0

    @pytest.mark.skipif(not os.path.exists(HIV_VCF), reason="HIV sample VCF not found")
    def test_bulk_import_medaka_hiv(self, graph):
        graph.samples.create(Sample(sample_id="SVAR_HIV"))
        stats = graph.variants.bulk_import_from_vcf(HIV_VCF, "SVAR_HIV", "K03455.1", "medaka", batch_size=100)
        assert stats["nodes_created"] > 0
        pairs = graph.variants.get_by_sample("SVAR_HIV")
        pos_counts: dict[int, int] = {}
        for v, _ in pairs:
            pos_counts[v.POS] = pos_counts.get(v.POS, 0) + 1
        assert max(pos_counts.values()) > 1, "HIV overlapping ORFs should produce multiple Variant nodes per position"


# ---------------------------------------------------------------------------
# AnalyticsRepository (cross-domain multi-hop traversals)
# ---------------------------------------------------------------------------

class TestAnalyticsRepository:
    def _seed_patient_chain(self, graph, *, pid, spid, said, variant, call, ward_id=None, adm_id=None):
        """Patient <- Specimen <- Sample -> Variant, optionally admitted to a ward."""
        graph.patients.create(Patient(patient_id=pid, firstname="x", lastname="y", age=40))
        graph.specimens.create(Specimen(specimen_id=spid, specimen_type="plasma"))
        graph.specimens.link_patient(spid, pid)
        graph.samples.create(Sample(sample_id=said))
        graph.samples.link_specimen(said, spid)
        graph.variants.link_sample(variant, said, call)
        if ward_id and adm_id:
            graph.admissions.create(Admission(admission_id=adm_id))
            graph.patients.link_admission(pid, adm_id)
            graph.admissions.link_ward(adm_id, ward_id, room_no="1", bed_no="A")

    def test_patient_variants(self, graph):
        v = Variant(REF_ACC="K03455.1", POS=2800, REF="A", ALT="G",
                    hgvs_c="c.1A>G", hgvs_p="", gene_name="gag", TYPE="SNP")
        graph.variants.create(v)
        self._seed_patient_chain(
            graph, pid="PA1", spid="SPA1", said="SAA1", variant=v,
            call={"DP": 30, "vcf_source": "medaka"},
        )

        rows = graph.analytics.patient_variants("PA1")
        assert len(rows) == 1
        assert rows[0].specimen_id == "SPA1"
        assert rows[0].sample_id == "SAA1"
        assert rows[0].variant.gene_name == "gag"
        assert rows[0].call["DP"] == 30

    def test_patient_variants_empty_for_unknown(self, graph):
        assert graph.analytics.patient_variants("NOPE") == []

    def test_ward_variant_clusters(self, graph):
        graph.departments.create(Department(department_id="D1", name="Medicine"))
        graph.wards.create(Ward(ward_id="W1", name="ICU", department_id="D1"))
        shared = Variant(REF_ACC="K03455.1", POS=5000, REF="C", ALT="T",
                         hgvs_c="c.9C>T", hgvs_p="", gene_name="pol", TYPE="SNP")
        graph.variants.create(shared)

        self._seed_patient_chain(graph, pid="PW1", spid="SPW1", said="SAW1",
                                 variant=shared, call={"vcf_source": "medaka"},
                                 ward_id="W1", adm_id="ADW1")
        self._seed_patient_chain(graph, pid="PW2", spid="SPW2", said="SAW2",
                                 variant=shared, call={"vcf_source": "medaka"},
                                 ward_id="W1", adm_id="ADW2")

        clusters = graph.analytics.ward_variant_clusters(min_patients=2)
        assert len(clusters) == 1
        c = clusters[0]
        assert c.ward_id == "W1"
        assert c.ward_name == "ICU"
        assert c.patient_count == 2
        assert set(c.patient_ids) == {"PW1", "PW2"}
        assert c.variant.POS == 5000

        # Raising the threshold above the cluster size excludes it.
        assert graph.analytics.ward_variant_clusters(min_patients=3) == []

    def test_ward_variant_clusters_rejects_zero(self, graph):
        with pytest.raises(ValueError, match="min_patients"):
            graph.analytics.ward_variant_clusters(min_patients=0)


# ---------------------------------------------------------------------------
# DrugResistanceRepository (Stanford HIVdb)
# ---------------------------------------------------------------------------

class TestDrugResistanceRepository:
    def test_mutation_crud(self, graph):
        graph.resistance.create_mutation(Mutation(gene="RT", text="M184V", primary_type="NRTI"))
        fetched = graph.resistance.get_mutation("RT", "M184V")
        assert fetched is not None
        assert fetched.primary_type == "NRTI"
        graph.resistance.delete_mutation("RT", "M184V")
        assert graph.resistance.get_mutation("RT", "M184V") is None

    def test_drug_and_class_crud(self, graph):
        graph.resistance.create_drug_class(DrugClass(name="NRTI", full_name="Nucleoside RT Inhibitor"))
        graph.resistance.create_drug(Drug(name="ABC", full_name="abacavir", display_abbr="ABC"))
        assert graph.resistance.get_drug_class("NRTI").full_name == "Nucleoside RT Inhibitor"
        assert graph.resistance.get_drug("ABC").full_name == "abacavir"

    def test_prediction_crud(self, graph):
        graph.resistance.create_prediction(StanfordHIVDRPrediction(
            prediction_id="S1:RT:ABC", sample_id="S1", gene="RT",
            drug_name="ABC", score=15.0, level="Low-Level Resistance",
        ))
        fetched = graph.resistance.get_prediction("S1:RT:ABC")
        assert fetched is not None
        assert fetched.score == 15.0
        graph.resistance.delete_prediction("S1:RT:ABC")
        assert graph.resistance.get_prediction("S1:RT:ABC") is None

    def test_bulk_import_missing_sample_raises(self, graph, tmp_path):
        p = tmp_path / "sierra.json"
        p.write_text(json.dumps(SIERRA_REPORT), encoding="utf-8")
        with pytest.raises(ValueError, match="not found"):
            graph.resistance.bulk_import_from_sierra(str(p), "NO_SUCH_SAMPLE")

    def test_bulk_import_and_reads(self, graph, tmp_path):
        graph.samples.create(Sample(sample_id="HIV_S1"))
        p = tmp_path / "sierra.json"
        p.write_text(json.dumps(SIERRA_REPORT), encoding="utf-8")

        stats = graph.resistance.bulk_import_from_sierra(str(p), "HIV_S1")
        assert stats["nodes_created"] > 0
        assert stats["relationships_created"] > 0

        # Two predictions (ABC, EFV) linked to the sample.
        predictions = graph.resistance.get_resistance_by_sample("HIV_S1")
        by_drug = {pred.drug_name: (pred, cls) for pred, cls in predictions}
        assert set(by_drug) == {"ABC", "EFV"}
        abc_pred, abc_class = by_drug["ABC"]
        assert abc_pred.level == "Low-Level Resistance"
        assert abc_pred.score == 15.0
        assert abc_class == "NRTI"

        # M184V confers resistance to ABC (score on the edge); EFV had no mutations.
        muts = graph.resistance.get_mutations_for_drug("ABC")
        assert [(m.text, s) for m, s in muts] == [("M184V", 15.0)]
        assert graph.resistance.get_mutations_for_drug("EFV") == []

    def test_bulk_import_is_idempotent(self, graph, tmp_path):
        graph.samples.create(Sample(sample_id="HIV_S2"))
        p = tmp_path / "sierra.json"
        p.write_text(json.dumps(SIERRA_REPORT), encoding="utf-8")
        graph.resistance.bulk_import_from_sierra(str(p), "HIV_S2")
        graph.resistance.bulk_import_from_sierra(str(p), "HIV_S2")  # second import

        # Re-import must not duplicate predictions.
        assert len(graph.resistance.get_resistance_by_sample("HIV_S2")) == 2

    def test_get_resistance_empty_for_unknown(self, graph):
        assert graph.resistance.get_resistance_by_sample("NOPE") == []


# ---------------------------------------------------------------------------
# Gzipped VCF import — functional, end-to-end against real HIV-64148 data
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not (os.path.exists(HXB2_GZ) and os.path.exists(CRF01_AE_GZ)),
    reason="HIV-64148 gzipped VCF fixtures not found",
)
class TestVcfGzipImportFunctional:
    def test_bulk_import_gzipped_medaka(self, graph):
        graph.samples.create(Sample(sample_id="GZ_S1"))
        stats = graph.variants.bulk_import_from_vcf(HXB2_GZ, "GZ_S1", "K03455.1", "medaka")
        assert stats["nodes_created"] > 0
        assert stats["relationships_created"] > 0

        pairs = graph.variants.get_by_sample("GZ_S1")
        assert len(pairs) > 0
        # Gene-annotation-level design survives the full gz → graph path.
        pos_counts: dict[int, int] = {}
        for v, _ in pairs:
            pos_counts[v.POS] = pos_counts.get(v.POS, 0) + 1
        assert max(pos_counts.values()) > 1

        by_ref = graph.variants.get_by_ref("K03455.1")
        assert len(by_ref) > 0
        assert all(v.REF_ACC == "K03455.1" for v in by_ref)

    def test_per_reference_gzip_import(self, graph):
        # The spec emits one annotated VCF per reference; importing both under
        # their own accessions must keep the variant sets cleanly separated.
        graph.samples.create(Sample(sample_id="GZ_TWO"))
        graph.variants.bulk_import_from_vcf(HXB2_GZ, "GZ_TWO", "K03455.1", "medaka")
        graph.variants.bulk_import_from_vcf(CRF01_AE_GZ, "GZ_TWO", "AF164485.1", "medaka")

        hxb2 = graph.variants.get_by_ref("K03455.1")
        crf = graph.variants.get_by_ref("AF164485.1")
        assert len(hxb2) > 0 and len(crf) > 0
        assert all(v.REF_ACC == "K03455.1" for v in hxb2)
        assert all(v.REF_ACC == "AF164485.1" for v in crf)

        # The sample links to the union of both references' variants, no overlap.
        pairs = graph.variants.get_by_sample("GZ_TWO")
        assert {v.REF_ACC for v, _ in pairs} == {"K03455.1", "AF164485.1"}
        assert len(pairs) == len(hxb2) + len(crf)

    def test_gzip_matches_plaintext(self, graph, tmp_path):
        # Importing a gz file and its decompressed twin must yield identical graphs.
        import gzip as _gzip
        plain = tmp_path / "hxb2.vcf"
        with _gzip.open(HXB2_GZ, "rb") as src:
            plain.write_bytes(src.read())

        graph.samples.create(Sample(sample_id="GZ_A"))
        graph.samples.create(Sample(sample_id="GZ_B"))
        graph.variants.bulk_import_from_vcf(HXB2_GZ, "GZ_A", "K03455.1", "medaka")
        graph.variants.bulk_import_from_vcf(str(plain), "GZ_B", "K03455.1", "medaka")

        a = sorted((v.POS, v.REF, v.ALT, v.hgvs_c, v.hgvs_p) for v, _ in graph.variants.get_by_sample("GZ_A"))
        b = sorted((v.POS, v.REF, v.ALT, v.hgvs_c, v.hgvs_p) for v, _ in graph.variants.get_by_sample("GZ_B"))
        assert a == b and len(a) > 0
