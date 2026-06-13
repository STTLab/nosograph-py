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

## Testing

```bash
pytest tests/unit/          # no database required
pytest tests/integration/   # requires Docker (testcontainers)
pytest tests/e2e/           # requires Docker — example CSV/VCF → graph, end to end
```

Test fixtures (example CSVs, sample/gzipped VCFs) live in `tests/data/`.

## Part of NosoGraph

This package is maintained as a [git subtree](https://github.com/STTLab/NosoGraph) inside the main NosoGraph monorepo, which also includes the Bash genome assembly pipeline, Docker/Neo4j configuration, and conda environments for bioinformatics tools.
