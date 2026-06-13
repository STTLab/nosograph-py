# nosograph-py

Python library for [NosoGraph](https://github.com/STTLab/NosoGraph) — a graph database schema and toolchain for integrating clinical, microbiological, and genomic data on Neo4j, with a focus on infectious disease surveillance and antimicrobial resistance (AMR).

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.12+ and a running Neo4j instance (see [docker-compose.yml](https://github.com/STTLab/NosoGraph/blob/main/docker-compose.yml) in the main repo).

## Quick start

```python
from nosograph import NosoGraph, Neo4JAuth, Patient, Specimen, Sample

auth = Neo4JAuth.from_string("neo4j/yourpassword")

with NosoGraph("bolt://localhost:7687", auth=auth) as graph:
    # Create a patient (firstname/lastname; provide date_of_birth OR age)
    graph.patients.create(Patient(
        patient_id="P001", firstname="Jane", lastname="Doe",
        sex="F", date_of_birth="1985-03-12",
    ))
    found = graph.patients.get("P001")

    # Create a specimen and link it to the patient
    graph.specimens.create(Specimen(specimen_id="SP001", specimen_type="plasma"))
    graph.specimens.link_patient("SP001", "P001")

    # A sequenced sample derived from the specimen
    graph.samples.create(Sample(sample_id="HIV_S001"))
    graph.samples.link_specimen("HIV_S001", "SP001")
```

### Genomic & drug-resistance import

The repo ships small example fixtures under [`tests/data/`](tests/data) that you
can import against the `HIV_S001` sample created above:

```python
# Variants from a SnpEff-annotated Medaka VCF (plain .vcf or gzipped .vcf.gz),
# imported per reference accession:
graph.variants.bulk_import_from_vcf(
    "tests/data/hiv64148_HXB2_subset.medaka.annotated.vcf.gz",
    sample_id="HIV_S001", ref_accession="K03455.1", source="medaka",
)

# Stanford HIVdb / sierrapy drug-resistance predictions:
graph.resistance.bulk_import_from_sierra(
    "tests/data/sierrapy_result.example.json", sample_id="HIV_S001",
)

# Cross-domain analytical queries (Patient <- Specimen <- Sample -> Variant)
for pv in graph.analytics.patient_variants("P001"):
    print(pv.sample_id, pv.variant.gene_name, pv.variant.hgvs_p)

clusters = graph.analytics.ward_variant_clusters(min_patients=2)  # outbreak signal
```

## Use case: ingest a full pipeline run

The HIV drug-resistance pipeline writes **one directory per sequenced sample**,
named by the sample ID. Only two artifacts are imported into the graph — the
per-reference annotated VCFs and the sierrapy report:

```
<SID>/                                  # directory named by the sample ID
├── sierrapy_result.0.json              # Stanford HIVdb drug-resistance predictions
└── 05_medaka_variant/
    ├── <REF>/                          # one subdir per reference (e.g. HXB2, CRF01_AE)
    │   └── medaka.annotated.vcf.gz     # SnpEff-annotated variants vs that reference
    └── <REF>/
        └── medaka.annotated.vcf.gz
```

The other directories (assembly, polishing, QC, BLAST, reports) are for human
review and are not imported.

### 1. Load one sample directory

`bulk_import_from_vcf` reads `.vcf.gz` transparently and is called **once per
reference**; the reference subdir name maps to the accession stored on
`Variant.REF_ACC`. The sample ID is taken from the directory name.

```python
import os, glob
from nosograph import NosoGraph, Neo4JAuth, Patient, Specimen, Sample

# Map each 05_medaka_variant/<REF>/ subdir name to its reference accession.
REFERENCE_ACCESSIONS = {
    "HXB2": "K03455.1",
    "CRF01_AE": "AF164485.1",
}

def ingest_sample(graph, sample_dir, patient_id):
    """Load one pipeline output directory and link it to an existing patient."""
    sample_id = os.path.basename(os.path.normpath(sample_dir))   # the <SID> dir name

    # Clinical provenance: Patient <- Specimen <- Sample
    specimen_id = f"{sample_id}_SPECIMEN"
    graph.specimens.create(Specimen(specimen_id=specimen_id))
    graph.specimens.link_patient(specimen_id, patient_id)
    graph.samples.create(Sample(sample_id=sample_id))
    graph.samples.link_specimen(sample_id, specimen_id)

    # Variants — one annotated VCF per reference
    for ref_dir in sorted(glob.glob(os.path.join(sample_dir, "05_medaka_variant", "*"))):
        accession = REFERENCE_ACCESSIONS.get(os.path.basename(ref_dir))
        if accession is None:
            continue   # unknown reference — add it to REFERENCE_ACCESSIONS
        vcf = os.path.join(ref_dir, "medaka.annotated.vcf.gz")
        graph.variants.bulk_import_from_vcf(vcf, sample_id, accession, source="medaka")

    # Drug resistance — Stanford HIVdb / sierrapy report
    sierra = os.path.join(sample_dir, "sierrapy_result.0.json")
    if os.path.exists(sierra):
        graph.resistance.bulk_import_from_sierra(sierra, sample_id)

    return sample_id


auth = Neo4JAuth.from_string("neo4j/yourpassword")
with NosoGraph("bolt://localhost:7687", auth=auth) as graph:
    # The patient comes from your clinical / LIS data and must exist first.
    graph.patients.create(Patient(patient_id="PATIENT_ID", firstname="...", lastname="...", age=40))

    sample_id = ingest_sample(graph, sample_dir="path/to/<SID>", patient_id="PATIENT_ID")
```

### 2. Answer questions for that sample

```python
# Drug-resistance interpretation (one row per gene/drug)
for prediction, drug_class in graph.resistance.get_resistance_by_sample(sample_id):
    print(prediction.gene, prediction.drug_name, drug_class, prediction.level, prediction.score)

# Mutations driving resistance to a given drug
for mutation, score in graph.resistance.get_mutations_for_drug("ABC"):
    print(mutation.gene, mutation.text, score)

# Every variant observed for the patient, with sequencing provenance
for pv in graph.analytics.patient_variants("PATIENT_ID"):
    print(pv.sample_id, pv.variant.REF_ACC, pv.variant.gene_name, pv.variant.hgvs_p)
```

### 3. Surveillance across many runs

Call `ingest_sample(...)` for each new pipeline directory, and load your
ward/admission data (`graph.departments`, `graph.wards`, `graph.admissions`).
Once patients are tied to wards, variants shared across patients on the same
ward flag possible transmission:

```python
# Variants carried by >= N distinct patients admitted to the same ward
for cluster in graph.analytics.ward_variant_clusters(min_patients=2):
    print(cluster.ward_id, cluster.variant.hgvs_p, cluster.patient_count, cluster.patient_ids)
```

## Entities and repositories

| Entity | Repository | Notes |
|---|---|---|
| `Patient` | `graph.patients` | `HAS_ADMISSION`, `HAS_OPD_VISIT` |
| `Admission` | `graph.admissions` | `ADMITTED_TO` Ward |
| `OpdVisit` | `graph.opd_visits` | outpatient encounter |
| `Ward` | `graph.wards` | `IN_DEPARTMENT` |
| `Department` | `graph.departments` | |
| `Specimen` | `graph.specimens` | `COLLECTED_FROM` Patient, `COLLECTED_AT_VISIT`, `TESTED_FOR` LabResult |
| `Sample` | `graph.samples` | `DERIVED_FROM` Specimen, `HAS_ASSEMBLY` |
| `Assembly` | `graph.assemblies` | `HAS_CONTIG`; cascade-deletes Contigs |
| `Organism` | `graph.organisms` | `REFERENCE_GENOME_OF` |
| `ReferenceGenome` | `graph.reference_genomes` | linked to Organism |
| `LabResult` | `graph.lab_results` | |
| `HIVViralLoad` | `graph.hiv_viral_loads` | |
| `Variant` | `graph.variants` | gene-annotation-level nodes; dual-VCF bulk import (plain/`.gz`) |
| `DrugClass`, `Drug`, `Mutation`, `StanfordHIVDRPrediction` | `graph.resistance` | sierrapy (Stanford HIVdb) bulk import |
| cross-domain reads | `graph.analytics` | `patient_variants()`, `ward_variant_clusters()` |

Repositories expose `.create()`, `.get()`, and (where applicable) `.delete()` plus `link_*` methods for relationships. Models are Pydantic v2.

📖 **Full method-level reference: [docs/API.md](docs/API.md)** — every repository method, model field, type, parser, and the relationship/graph schema.

## Testing

```bash
pytest tests/unit/          # no database required
pytest tests/integration/   # requires Docker (testcontainers)
pytest tests/e2e/           # requires Docker — example CSV/VCF → graph, end to end
```

Test fixtures (example CSVs, sample/gzipped VCFs) live in `tests/data/`.

## Part of NosoGraph

This package is maintained as a [git subtree](https://github.com/STTLab/NosoGraph) inside the main NosoGraph monorepo, which also includes the Bash genome assembly pipeline, Docker/Neo4j configuration, and conda environments for bioinformatics tools.
