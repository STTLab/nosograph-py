# nosograph-py

Python library for [NosoGraph](https://github.com/STTLab/NosoGraph) — a graph database schema and toolchain for integrating clinical, microbiological, and genomic data on Neo4j, with a focus on infectious disease surveillance and antimicrobial resistance (AMR).

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.12+ and a running Neo4j instance (see [docker-compose.yml](https://github.com/STTLab/NosoGraph/blob/main/docker-compose.yml) in the main repo).

## Quick start

```python
from nosograph import NosoGraph, Neo4JAuth, Patient, Specimen, Assembly

auth = Neo4JAuth.from_string("neo4j/yourpassword")

with NosoGraph("bolt://localhost:7687", auth=auth) as graph:
    # Create a patient
    patient = Patient(patient_id="P001", name="Jane Doe", dob="1985-03-12", sex="F")
    graph.patients.create(patient)

    # Retrieve
    found = graph.patients.get("P001")

    # Create a specimen linked to the patient
    specimen = Specimen(specimen_id="S001", type="sputum", collected_at="2026-06-01")
    graph.specimens.create(specimen, patient_id="P001")
```

## Entities and repositories

| Entity | Repository | Notes |
|---|---|---|
| `Patient` | `graph.patients` | |
| `Admission` | `graph.admissions` | linked to Patient + Ward |
| `Ward` | `graph.wards` | linked to Department |
| `Department` | `graph.departments` | |
| `Specimen` | `graph.specimens` | linked to Patient |
| `Sample` | `graph.samples` | linked to Specimen |
| `Assembly` | `graph.assemblies` | linked to Sample; cascade-deletes Contigs |
| `Organism` | `graph.organisms` | |
| `ReferenceGenome` | `graph.reference_genomes` | linked to Organism |
| `Variant` | — | Cypher + model exist; repository not yet implemented |

All repositories expose `.create()`, `.get()`, and `.delete()` where applicable. Models are Pydantic v2.

## Testing

Unit tests require no database:

```bash
pytest tests/unit/
```

Integration tests use [testcontainers](https://testcontainers.com/) and require Docker:

```bash
pytest tests/integration/
```

## Part of NosoGraph

This package is maintained as a [git subtree](https://github.com/STTLab/NosoGraph) inside the main NosoGraph monorepo, which also includes the Bash genome assembly pipeline, Docker/Neo4j configuration, and conda environments for bioinformatics tools.
