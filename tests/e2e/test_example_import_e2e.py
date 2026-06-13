"""End-to-end import tests driven by the bundled example data.

Random records are pulled from tests/data/example_csv/*.csv and the gzipped
HIV-64148 VCF fixtures, pushed through the real repositories / bulk-import
functions against a testcontainers Neo4j, and read back to confirm the graph
was built correctly. Requires Docker (shared fixture in tests/conftest.py).
"""
import csv
import os
import random
from datetime import date

import pytest
from nosograph import (
    Patient, Admission, Ward, Department, OpdVisit,
    Specimen, Sample, Organism, ReferenceGenome,
    LabResult, HIVViralLoad, Variant,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_DIR = os.path.join(DATA_DIR, "example_csv")
HXB2_GZ = os.path.join(DATA_DIR, "hiv64148_HXB2_subset.medaka.annotated.vcf.gz")


# --------------------------------------------------------------------------
# CSV helpers + type coercion
# --------------------------------------------------------------------------

def _read_csv(name: str) -> list[dict]:
    with open(os.path.join(CSV_DIR, f"{name}.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _find(name: str, **match) -> dict:
    for row in _read_csv(name):
        if all(row[k] == v for k, v in match.items()):
            return row
    raise KeyError(f"No {name} row matching {match}")


def _s(v):
    v = (v or "").strip()
    return v or None


def _date(v):
    v = (v or "").strip()
    return date.fromisoformat(v.split("T")[0]) if v else None


def _int(v):
    v = (v or "").strip()
    return int(v) if v else None


def _float(v):
    v = (v or "").strip()
    return float(v) if v else None


# --------------------------------------------------------------------------
# Row -> model builders
# --------------------------------------------------------------------------

def _patient(r):
    return Patient(patient_id=r["patient_id"], firstname=r["firstname"], lastname=r["lastname"],
                   sex=_s(r["sex"]), date_of_birth=_date(r["date_of_birth"]))


def _department(r):
    return Department(department_id=r["department_id"], name=r["name"], description=_s(r["description"]))


def _ward(r):
    return Ward(ward_id=r["ward_id"], name=r["name"], department_id=r["department_id"],
                ward_type=_s(r["ward_type"]), description=_s(r["description"]))


def _admission(r):
    return Admission(admission_id=r["admission_id"], date_of_admission=_date(r["date_of_admission"]),
                     date_of_discharge=_date(r["date_of_discharge"]))


def _opd_visit(r):
    return OpdVisit(visit_id=r["visit_id"], visit_date=_date(r["visit_date"]), clinic=_s(r["clinic"]),
                    chief_complaint=_s(r["chief_complaint"]), notes=_s(r["notes"]))


def _specimen(r):
    return Specimen(specimen_id=r["specimen_id"], specimen_type=_s(r["specimen_type"]))


def _sample(r):
    return Sample(sample_id=r["sample_id"])


def _lab_result(r):
    return LabResult(lab_id=r["lab_id"], specimen_id=_s(r["specimen_id"]), result_type=_s(r["result_type"]),
                     test_date=_date(r["test_date"]), value=_s(r["value"]), unit=_s(r["unit"]), notes=_s(r["notes"]))


def _hiv_viral_load(r):
    return HIVViralLoad(viral_load_id=r["viral_load_id"], test_date=_date(r["test_date"]),
                        value_copies_per_ml=_int(r["value_copies_per_ml"]), log10_value=_float(r["log10_value"]),
                        detection_limit=_int(r["detection_limit"]), assay_type=_s(r["assay_type"]),
                        result_status=_s(r["result_status"]))


def _organism(r):
    return Organism(taxid=r["taxid"], sciname=_s(r["sciname"]))


def _reference_genome(r):
    return ReferenceGenome(accession_no=r["accession_no"], name=_s(r["name"]),
                           molecular_type=_s(r["molecular_type"]), strain=_s(r["strain"]),
                           annotation_source=_s(r["annotation_source"]), source_database=_s(r["source_database"]))


def _variant_from_snp(r):
    v = Variant(REF_ACC=r["REF_ACC"], POS=int(r["POS"]), REF=r["REF"], ALT=r["ALT"], CHROM=_s(r["CHROM"]),
                TYPE=_s(r["TYPE"]), EFFECT=_s(r["EFFECT"]), IMPACT=_s(r["IMPACT"]),
                hgvs_c=_s(r["HGVS_C"]) or "", hgvs_p=_s(r["HGVS_P"]) or "", gene_name=_s(r["LOCUS_TAG"]))
    call = {"DP": _int(r["DP"]), "AO": _int(r["AO"]), "RO": _int(r["RO"]),
            "QUAL": _float(r["QUAL"]), "GT": _s(r["GT"]), "vcf_source": "snippy"}
    return v, call


# --------------------------------------------------------------------------
# Per-entity round-trip from a random example record
# --------------------------------------------------------------------------

ENTITY_SPECS = [
    ("Patients", _patient, lambda g, m: g.patients.create(m), lambda g, m: g.patients.get(m.patient_id), "patient_id"),
    ("Departments", _department, lambda g, m: g.departments.create(m), lambda g, m: g.departments.get(m.department_id), "department_id"),
    ("Wards", _ward, lambda g, m: g.wards.create(m), lambda g, m: g.wards.get(m.ward_id), "ward_id"),
    ("OpdVisits", _opd_visit, lambda g, m: g.opd_visits.create(m), lambda g, m: g.opd_visits.get(m.visit_id), "visit_id"),
    ("Specimens", _specimen, lambda g, m: g.specimens.create(m), lambda g, m: g.specimens.get(m.specimen_id), "specimen_id"),
    ("Samples", _sample, lambda g, m: g.samples.create(m), lambda g, m: g.samples.get(m.sample_id), "sample_id"),
    ("LabResults", _lab_result, lambda g, m: g.lab_results.create(m), lambda g, m: g.lab_results.get(m.lab_id), "lab_id"),
    ("HIVViralLoads", _hiv_viral_load, lambda g, m: g.hiv_viral_loads.create(m), lambda g, m: g.hiv_viral_loads.get(m.viral_load_id), "viral_load_id"),
    ("Organisms", _organism, lambda g, m: g.organisms.create(m), lambda g, m: g.organisms.get(m.taxid), "taxid"),
    ("ReferenceGenomes", _reference_genome, lambda g, m: g.reference_genomes.create(m), lambda g, m: g.reference_genomes.get(m.accession_no), "accession_no"),
    ("Admissions", _admission, lambda g, m: g.admissions.create(m), lambda g, m: g.admissions.get(m.admission_id), "admission_id"),
]


@pytest.mark.parametrize("name,build,create,get,id_attr", ENTITY_SPECS, ids=[s[0] for s in ENTITY_SPECS])
def test_entity_roundtrip_from_random_record(graph, name, build, create, get, id_attr):
    row = random.choice(_read_csv(name))
    model = build(row)
    create(graph, model)
    fetched = get(graph, model)
    assert fetched is not None, f"{name} record {getattr(model, id_attr)} not found after create"
    assert getattr(fetched, id_attr) == getattr(model, id_attr)


def test_patient_fields_roundtrip(graph):
    row = random.choice(_read_csv("Patients"))
    graph.patients.create(_patient(row))
    fetched = graph.patients.get(row["patient_id"])
    assert fetched.firstname == row["firstname"]
    assert fetched.lastname == row["lastname"]
    assert fetched.sex == _s(row["sex"])
    assert fetched.date_of_birth == _date(row["date_of_birth"])


def test_hiv_viral_load_numeric_roundtrip(graph):
    row = random.choice(_read_csv("HIVViralLoads"))
    graph.hiv_viral_loads.create(_hiv_viral_load(row))
    fetched = graph.hiv_viral_loads.get(row["viral_load_id"])
    assert fetched.value_copies_per_ml == _int(row["value_copies_per_ml"])
    assert fetched.log10_value == _float(row["log10_value"])
    assert fetched.result_status == _s(row["result_status"])


def test_specimen_type_roundtrip(graph):
    row = random.choice([r for r in _read_csv("Specimens") if _s(r["specimen_type"])])
    graph.specimens.create(_specimen(row))
    fetched = graph.specimens.get(row["specimen_id"])
    assert fetched.specimen_type == _s(row["specimen_type"])


# --------------------------------------------------------------------------
# Connected, cross-domain end-to-end chains
# --------------------------------------------------------------------------

def test_clinical_admission_graph(graph):
    # Patient -> Admission -> Ward -> Department, all linked from the CSV FKs.
    adm = random.choice([r for r in _read_csv("Admissions")
                         if r["date_of_admission"] and r["date_of_discharge"]])
    pat = _find("Patients", patient_id=adm["patient_id"])
    ward = _find("Wards", ward_id=adm["ward_id"])
    dept = _find("Departments", department_id=ward["department_id"])

    graph.departments.create(_department(dept))
    graph.wards.create(_ward(ward))
    graph.wards.link_department(ward["ward_id"], dept["department_id"])
    graph.patients.create(_patient(pat))
    graph.admissions.create(_admission(adm))
    graph.patients.link_admission(pat["patient_id"], adm["admission_id"])
    graph.admissions.link_ward(adm["admission_id"], ward["ward_id"],
                               room_no=_s(adm["room_no"]), bed_no=_s(adm["bed_no"]))

    with graph.driver.session() as s:
        rec = s.run(
            "MATCH (p:Patient {patient_id:$pid})-[:HAS_ADMISSION]->(a:Admission)"
            "-[:ADMITTED_TO]->(w:Ward)-[:IN_DEPARTMENT]->(d:Department) "
            "RETURN d.department_id AS dept, a.length_of_stay AS los",
            pid=pat["patient_id"],
        ).single()
    assert rec is not None
    assert rec["dept"] == dept["department_id"]
    # length_of_stay is computed by Cypher from the admission dates.
    expected_los = (_date(adm["date_of_discharge"]) - _date(adm["date_of_admission"])).days
    assert rec["los"] == expected_los


def test_bacterial_variants_from_snps_csv(graph):
    # P002 <- SP003 <- BAC_S001 -> Variant, variants imported from SNPs.csv.
    sample_row = _find("Samples", sample_id="BAC_S001")
    spec = _find("Specimens", specimen_id=sample_row["specimen_id"])
    pat = _find("Patients", patient_id=spec["patient_id"])

    graph.patients.create(_patient(pat))
    graph.specimens.create(_specimen(spec))
    graph.specimens.link_patient(spec["specimen_id"], pat["patient_id"])
    graph.samples.create(_sample(sample_row))
    graph.samples.link_specimen(sample_row["sample_id"], spec["specimen_id"])

    snps = _read_csv("SNPs")
    for r in snps:
        v, call = _variant_from_snp(r)
        graph.variants.create(v)
        graph.variants.link_sample(v, sample_row["sample_id"], call)

    expected = len({
        (r["REF_ACC"], int(r["POS"]), r["REF"], r["ALT"], _s(r["HGVS_C"]) or "", _s(r["HGVS_P"]) or "")
        for r in snps
    })
    pairs = graph.variants.get_by_sample("BAC_S001")
    assert len(pairs) == expected

    # Cross-domain analytics traversal returns the same variants for the patient.
    pv = graph.analytics.patient_variants(pat["patient_id"])
    assert len(pv) == expected
    assert {p.sample_id for p in pv} == {"BAC_S001"}
    assert all(p.variant.REF_ACC == "NZ_CP023401.1" for p in pv)

    assert len(graph.variants.get_by_ref("NZ_CP023401.1")) == expected


@pytest.mark.skipif(not os.path.exists(HXB2_GZ), reason="HXB2 gz fixture not found")
def test_hiv_variants_from_gzipped_vcf(graph):
    # P005 -> SP001 (visit V001) -> HIV_S001; variants bulk-imported from gz VCF.
    pat = _find("Patients", patient_id="P005")
    visit = _find("OpdVisits", visit_id="V001")
    spec = _find("Specimens", specimen_id="SP001")
    sample_row = _find("Samples", sample_id="HIV_S001")

    graph.patients.create(_patient(pat))
    graph.opd_visits.create(_opd_visit(visit))
    graph.opd_visits.link_patient(visit["visit_id"], pat["patient_id"])
    graph.specimens.create(_specimen(spec))
    graph.specimens.link_patient(spec["specimen_id"], pat["patient_id"])
    graph.specimens.link_visit(spec["specimen_id"], visit["visit_id"])
    graph.samples.create(_sample(sample_row))
    graph.samples.link_specimen(sample_row["sample_id"], spec["specimen_id"])

    stats = graph.variants.bulk_import_from_vcf(HXB2_GZ, "HIV_S001", "K03455.1", "medaka")
    assert stats["nodes_created"] > 0 and stats["relationships_created"] > 0

    pv = graph.analytics.patient_variants("P005")
    assert len(pv) > 0
    assert all(p.variant.REF_ACC == "K03455.1" for p in pv)
    assert all(p.sample_id == "HIV_S001" for p in pv)


def test_variant_from_random_snp_record(graph):
    graph.samples.create(Sample(sample_id="SNP_SAMPLE"))
    row = random.choice(_read_csv("SNPs"))
    v, call = _variant_from_snp(row)
    graph.variants.create(v)
    graph.variants.link_sample(v, "SNP_SAMPLE", call)

    pairs = graph.variants.get_by_sample("SNP_SAMPLE")
    assert len(pairs) == 1
    fv, fc = pairs[0]
    assert fv.POS == int(row["POS"])
    assert fv.REF == row["REF"] and fv.ALT == row["ALT"]
    assert fc["DP"] == _int(row["DP"])
    assert fc["vcf_source"] == "snippy"


def test_reference_genome_links_to_organism(graph):
    rg = random.choice([r for r in _read_csv("ReferenceGenomes") if _s(r["taxid"])])
    org_row = next((r for r in _read_csv("Organisms") if r["taxid"] == rg["taxid"]), None)
    if org_row:
        graph.organisms.create(_organism(org_row))
    else:
        graph.organisms.create(Organism(taxid=rg["taxid"]))
    graph.reference_genomes.create(_reference_genome(rg))
    graph.organisms.link_reference_genome(rg["taxid"], rg["accession_no"])

    with graph.driver.session() as s:
        rec = s.run(
            "MATCH (rg:ReferenceGenome {accession_no:$a})-[:REFERENCE_GENOME_OF]->(o:Organism {taxid:$t}) RETURN o",
            a=rg["accession_no"], t=rg["taxid"],
        ).single()
    assert rec is not None
