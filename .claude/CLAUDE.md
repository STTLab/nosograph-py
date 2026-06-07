# nosograph-py — Library Context for Claude

## What This Package Is

`nosograph` is a pip-installable Python library that provides models, repositories, a CLI, and a pipeline wrapper for [NosoGraph](https://github.com/STTLab/NosoGraph) — a Neo4j-backed knowledge graph for clinical, microbiological, and genomic data integration.

This directory is also published as a standalone repo at **[STTLab/nosograph-py](https://github.com/STTLab/nosograph-py)**. It is maintained as a git subtree inside `STTLab/NosoGraph`. After changes here, sync upstream:

```bash
# from the NosoGraph monorepo root
git subtree push --prefix=nosograph-py nosograph-py main
```

Install: `pip install -e ".[dev]"` (Python 3.12+)

---

## Package Layout

```
nosograph-py/
├── pyproject.toml
├── nosograph/
│   ├── __init__.py          ← public API exports
│   ├── db.py                ← NosoGraph class (driver + repository properties)
│   ├── types.py             ← Neo4JAuth, AssemblyProps, ContigProps, Stats TypedDicts
│   ├── pipeline.py          ← NosoGraphPipeline / NosoGraphPipelineOutput
│   ├── cli.py               ← interactive terminal UI (prompt_toolkit)
│   ├── _txs.py              ← private transaction functions (internal)
│   ├── models/
│   │   ├── patient.py       ← Patient, Admission, OpdVisit, Ward, Department (Pydantic v2)
│   │   ├── specimen.py      ← Specimen, Sample
│   │   ├── genomics.py      ← Organism, ReferenceGenome, Assembly, Contig, Variant
│   │   └── lab.py           ← LabResult, HIVViralLoad
│   ├── repositories/
│   │   ├── _base.py         ← BaseRepository(driver)
│   │   ├── patient.py       ← PatientRepository
│   │   ├── admission.py     ← AdmissionRepository
│   │   ├── specimen.py      ← SpecimenRepository, SampleRepository
│   │   ├── genomics.py      ← OrganismRepository, AssemblyRepository, ReferenceGenomeRepository
│   │   └── clinical.py      ← WardRepository, DepartmentRepository, LabResultRepository, HIVViralLoadRepository, OpdVisitRepository
│   └── cypher/              ← all .cypher files (loaded via importlib.resources)
└── tests/
    ├── unit/
    │   ├── test_models.py   ← 25 tests (models only, no DB required)
    │   ├── test_types.py    ← 17 tests (Neo4JAuth, TypedDicts)
    │   └── test_db.py       ← 28 tests (NosoGraph, mocked driver)
    └── integration/
        ├── conftest.py           ← testcontainers Neo4j fixture (skips if Docker unavailable)
        └── test_repositories.py  ← 25 tests, requires Docker
```

---

## Key Architectural Patterns

- **Cypher loading**: `_txs.py` uses `importlib.resources.files("nosograph.cypher")` at import time. Dict keys = filename without `.cypher` (case-sensitive). New queries → new `.cypher` file, key must match exactly.
- **Repository pattern**: Each entity has a repository class. All repositories take a `neo4j.Driver` (via `BaseRepository`). Each method calls `session.execute_read/write` with a transaction function from `_txs.py`.
- **Transaction functions** (`_txs.py`): return plain `dict | None` or primitives. Repositories convert to Pydantic models via `Model.model_validate(raw)`.
- **NosoGraph** (`db.py`): extends `neo4j.GraphDatabase`, exposes all repositories as properties (`graph.patients`, `graph.assemblies`, etc.), plus back-compat `add_assembly()` / `add_contigs()` methods.
- **Models** (Pydantic v2): field validation + cross-field `model_validator`. `Variant.variant_key` is a `@computed_field`.

---

## Entity CRUD Status

| Entity | CREATE | GET | DELETE | Relationships | Repository |
|---|---|---|---|---|---|
| Patient | ✅ | ✅ | ✅ | HAS_ADMISSION, HAS_OPD_VISIT | ✅ PatientRepository |
| Admission | ✅ | ✅ | ✅ | ADMITTED_TO | ✅ AdmissionRepository |
| OpdVisit | ✅ | ✅ | ✅ | HAS_OPD_VISIT, COLLECTED_AT_VISIT | ✅ OpdVisitRepository |
| Specimen | ✅ | ✅ | ✅ | COLLECTED_FROM, TESTED_FOR, COLLECTED_AT_VISIT | ✅ SpecimenRepository |
| Sample | ✅ | ✅ | ✅ | HAS_ASSEMBLY | ✅ SampleRepository |
| Assembly | ✅ | ✅ | ✅ (cascade) | HAS_CONTIG | ✅ AssemblyRepository |
| Organism | ✅ | ✅ | ✅ | REFERENCE_GENOME_OF | ✅ OrganismRepository |
| ReferenceGenome | ✅ | ✅ | ✅ | — | ✅ ReferenceGenomeRepository |
| Ward | ✅ | ✅ | — | IN_DEPARTMENT | ✅ WardRepository |
| Department | ✅ | ✅ | — | — | ✅ DepartmentRepository |
| LabResult | ✅ | ✅ | ✅ | TESTED_FOR | ✅ LabResultRepository |
| HIVViralLoad | ✅ | ✅ | ✅ | HAS_HIV_VIRAL_LOAD_RESULT | ✅ HIVViralLoadRepository |
| Variant | ✅ (Cypher) | ✅ (Cypher) | — | — | ❌ no repository yet |

---

## Known Bugs — All Fixed

All 8 bugs from the initial audit (2026-06-07) are resolved.

---

## What Is Still Missing

- `VariantRepository` — Cypher files and transaction functions exist; repository class missing
- Stanford HIVDR module — `sierrapy` conda env exists in the monorepo, no Python code yet
- `cli.py` stubs: `create_sample()`, `print_sample_info()`, `load_csv()`, `pipeline_prompt()` (full form)
- `NosoGraphPipelineOutput.check_output_files()` for Canu assembler (`NotImplementedError`)
- `nosograph-py/utils/` is empty

---

## Recommended Next Actions

### Priority 3 — Variant repository
1. Add `VariantRepository` in `repositories/genomics.py`

### Priority 4 — HIV/Drug resistance module
2. Implement sierrapy integration (`conda/sierrapy.yaml` in the monorepo)
3. Add `StanfordHIVDRPrediction` Cypher + repository
4. Add `PREDICTS_RESISTANCE_TO` relationship

### Priority 5 — CLI & ETL completion
5. Complete `cli.py` stubs for sample and pipeline upload
6. Implement `load_csv()` for bulk import via pandas
7. Implement Canu output checker in `pipeline.py`

### Priority 6 — Analytical queries & reporting
8. Add `MATCH_` queries for multi-hop traversals (patient → OpdVisit/Admission → specimens → assemblies)
9. Implement FR-07 reporting output

---

## Testing

```bash
pytest tests/unit/          # no database required
pytest tests/integration/   # requires Docker (testcontainers)
```
