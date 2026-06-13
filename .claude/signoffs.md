# Signoff sheet

Please log your activities in this file with the format below

---
## date yyyy-mm-dd time hh:mm (commit hash - if applicable)

Action: < Prompt/Read/Plan/Edit >

### Major changes
    - ...
    - ...

### Minor improvements
    - ...
    - ...

### Summary

(You may add callouts, attach link to file, or code block snippets where appropriate)

### Suggestion/Further action (optional)

...
---

## 2026-06-13

Action: Plan + Edit

> Implement FR-05 (drug resistance), FR-03 (analytical queries), and finish half-built surfaces (Canu output check, CLI sample/pipeline stubs). All with tests.

### Major changes
    - **Drug resistance module (FR-05)**: `models/resistance.py` (DrugClass, Drug, Mutation, StanfordHIVDRPrediction), `utils/sierra.py` (Stanford HIVdb/sierrapy JSON parser), `repositories/resistance.py` (`DrugResistanceRepository` with CRUD + `bulk_import_from_sierra`), 13 new Cypher files incl. `BULK_MERGE_HIVDR` (builds PREDICTS_RESISTANCE_TO / CONFERS_RESISTANCE_TO / IN_DRUG_CLASS / HAS_STANFORD_HIVDR_PREDICTION), constraints for the 4 node types.
    - **Analytical queries (FR-03)**: `repositories/analytics.py` (`AnalyticsRepository`) with `patient_variants()` and `ward_variant_clusters()`; new Cypher `MATCH_patient_variants`, `MATCH_ward_variant_clusters`.
    - **Schema fix (enables FR-03/FR-06)**: added the missing `Sample-[:DERIVED_FROM]->Specimen` edge (`SampleRepository.link_specimen`, `ASSOCIATE_Sample_DERIVED_FROM_Specimen.cypher`) — the data carried a `specimen_id` FK with no relationship, breaking patient→variant traversal.
    - **Pipeline (P4)**: implemented `NosoGraphPipelineOutput.check_output_files()` for Canu (was `NotImplementedError`); factored shared file-check loop.
    - **CLI (P4)**: implemented `create_sample()`, `get_sample()`, `print_sample_info()`, and the full `pipeline_prompt()` form (was `pass`/discard stubs).

### Minor improvements
    - `db.py`/`__init__.py`: exposed `graph.analytics`, `graph.resistance`; exported new models + repositories.
    - Docs: synced `nosograph-py/.claude/CLAUDE.md`, monorepo FR table, and `example/csv/README.md` (Sample→Specimen edge now exists).

### Summary

168 tests pass (119 unit + 49 integration). New unit files: `test_pipeline.py`, `test_cli.py`, `test_analytics.py`, `test_sierra_parser.py`. New integration coverage: `TestAnalyticsRepository`, `TestDrugResistanceRepository`, `test_link_specimen`. The HIVDR bulk import uses a single `MERGE`+`FOREACH` Cypher and is idempotent (prediction id = `{sample_id}:{gene}:{drug_name}`).

### Suggestion/Further action

Next: CSV ETL (`cli.load_csv()` via pandas) for FR-01; automate the upstream `sierrapy fasta … -o json` call in `pipeline.py`; FR-07 reporting.

---

## 2026-06-07 (d080b37)

Action: Edit

> Fix integration test failures synced from NosoGraph monorepo.

### Major changes
    - `nosograph/cypher/ASSOCIATE_Admisson_TO_Ward.cypher`: fixed Cypher so ward lookup uses `ward_id` param correctly
    - `nosograph/cypher/DELETE_AssemblyRun_cascade.cypher`: fixed cascade delete to detach-delete contigs before removing assembly
    - `nosograph/repositories/admission.py`: fixed `link_ward` to pass `room_no` / `bed_no` params
    - `nosograph/repositories/genomics.py`: fixed type conversion bug for `created_at` Neo4j datetime

### Minor improvements
    - `tests/integration/conftest.py`: added auth tuple format accepted by testcontainers Neo4j fixture

### Summary

All 19 integration tests pass against a live testcontainers Neo4j instance. No logic changes — fixes only.

---

## 2026-06-07 20:00 (cb7bc54)

Action: Plan + Edit

> Implement LabResult and HIVViralLoad entities (FR-02 / FR-06). Variant deferred due to inter-tool field variance.

### Major changes
    - `nosograph/models/lab.py`: new file — `LabResult` and `HIVViralLoad` Pydantic v2 models
    - 8 new Cypher files: `CREATE_LabResult`, `MATCH_LabResult`, `DELETE_LabResult`, `ASSOCIATE_Specimen_TESTED_FOR_LabResult`, `CREATE_HIVViralLoad`, `MATCH_HIVViralLoad`, `DELETE_HIVViralLoad`, `ASSOCIATE_Patient_HAS_HIV_VIRAL_LOAD_RESULT`
    - `nosograph/_txs.py`: 8 new transaction functions for LabResult and HIVViralLoad CRUD and linking
    - `nosograph/repositories/clinical.py`: `LabResultRepository` and `HIVViralLoadRepository` added
    - `nosograph/db.py`: `lab_results` and `hiv_viral_loads` properties exposed on `NosoGraph`
    - `nosograph/__init__.py`: `LabResult` and `HIVViralLoad` added to public API

### Minor improvements
    - `nosograph/cypher/_CONSTRAINTS.cypher`: added `HIVViralLoad` uniqueness/existence constraints (LabResult constraints were already present)
    - Unit tests: 8 new model tests (30 total)
    - Integration tests: 6 new repository tests (25 total)

### Summary

`LabResult` uses flat property-based polymorphism — `result_type` stored as a string property rather than a Neo4j dynamic label. Dual-label approach (`:LabResult:CBC`) deferred until subtypes are better defined; APOC would be required. `HIVViralLoad` is a dedicated node type per SRS §3.2, not a subtype of LabResult.

### Suggestion/Further action

Implement `VariantRepository` once VCF field normalisation across callers is agreed. Next after that: Stanford HIVDR module (sierrapy).

---

## 2026-06-07 20:00 (d9d6741)

Action: Edit

> Add docstrings to all public repository methods; remove legacy src/ directory.

### Major changes
    - `src/` deleted: legacy monolithic prototype superseded by `nosograph/` package; was excluded from `pyproject.toml` and unreferenced by any current code

### Minor improvements
    - All 5 repository files (`patient.py`, `admission.py`, `specimen.py`, `genomics.py`, `clinical.py`): one-line docstrings added to every class and public method documenting return behaviour, idempotency, and the Neo4j relationship name created by each `link_*` method

### Summary

`src/` contained the original `nosograph_neo4j.py`, `nosograph_neo4j_txs.py`, `nosograph_pipeline.py`, and `cli.py` from before the library was restructured. All functionality has been superseded. Removing it reduces confusion about which code is authoritative.

---
