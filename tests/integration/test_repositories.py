from datetime import date
import pytest
from nosograph import (
    Patient, Admission, Ward, Department,
    Specimen, Sample,
    Organism, ReferenceGenome, Assembly, Contig,
    LabResult, HIVViralLoad,
)


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
