# nosograph API reference

Full reference for the public API exported by `nosograph`. For a guided
introduction and end-to-end use cases, see the [README](../README.md).

- [Conventions](#conventions)
- [Connecting: `NosoGraph` and `Neo4JAuth`](#connecting)
- [Repositories](#repositories)
  - [Clinical](#clinical-repositories)
  - [Specimen / Sample](#specimen--sample)
  - [Genomics](#genomics-repositories)
  - [Drug resistance](#drug-resistance)
  - [Analytics](#analytics)
- [Models](#models)
- [Bulk import & parsers](#bulk-import--parsers)
- [Types](#types)
- [Pipeline wrapper](#pipeline-wrapper)
- [Graph schema](#graph-schema)

---

## Conventions

- **Repository pattern.** Every entity is reached through a property on a
  connected `NosoGraph` instance (e.g. `graph.patients`, `graph.variants`).
  Repositories take a `neo4j.Driver` internally; you never construct them
  directly.
- **`create(model)`** is idempotent (`MERGE`) and returns the node's id —
  **except `patients.create`**, which uses `CREATE` and raises `ValueError`
  if the `patient_id` already exists.
- **`get(id)`** returns a Pydantic model instance or `None`.
- **`delete(id)`** does a `DETACH DELETE` (removes the node and its relationships).
- **`link_*(...)`** methods `MERGE` a relationship between two **already-existing**
  nodes; create both endpoints first.
- **Models** are Pydantic v2. Date fields accept ISO‑8601 strings or `datetime.date`.
- All methods are synchronous and open their own session per call.

---

## Connecting

```python
from nosograph import NosoGraph, Neo4JAuth

auth = Neo4JAuth.from_string("neo4j/password")          # or None for no auth
with NosoGraph("bolt://localhost:7687", auth=auth) as graph:
    ...   # graph is verified on __enter__ and closed on __exit__
```

### `class NosoGraph(database_uri: str, auth: Neo4JAuth | None = None)`

Extends `neo4j.GraphDatabase`. Use as a context manager (verifies connectivity
on enter, closes the driver on exit) or call `verify()` / `close()` yourself.

**Repository properties** (each returns the repository of the same name):

| Property | Repository | Property | Repository |
|---|---|---|---|
| `patients` | PatientRepository | `organisms` | OrganismRepository |
| `admissions` | AdmissionRepository | `reference_genomes` | ReferenceGenomeRepository |
| `opd_visits` | OpdVisitRepository | `assemblies` | AssemblyRepository |
| `wards` | WardRepository | `variants` | VariantRepository |
| `departments` | DepartmentRepository | `lab_results` | LabResultRepository |
| `specimens` | SpecimenRepository | `hiv_viral_loads` | HIVViralLoadRepository |
| `samples` | SampleRepository | `resistance` | DrugResistanceRepository |
| | | `analytics` | AnalyticsRepository |

**Other members**

| Member | Signature | Description |
|---|---|---|
| `driver` | property → `neo4j.Driver` | The underlying driver. |
| `verify()` | → `None` | Verify connectivity (logs result). |
| `close()` | → `None` | Close the driver. |
| `add_assembly(**assembly_data)` | → `NodeCreateOrMatchStats` | Back-compat: create an Assembly from kwargs. |
| `add_contigs(assembly_id, contigs)` | `contigs: list[ContigProps]` → `NodeAndRelationshipCreationStats` | Back-compat: bulk-add contigs. |

### `class Neo4JAuth(NamedTuple)`

`Neo4JAuth(user: Literal["neo4j"], password: str)` — passed as `auth=` to `NosoGraph`.

- `Neo4JAuth.from_string(value: str | None) -> Neo4JAuth | None` — parse `"neo4j/password"`. Returns `None` for `None`/empty; raises `ValueError` on a malformed string or non-`neo4j` user.

---

## Repositories

### Clinical repositories

#### `graph.patients` — PatientRepository
| Method | Returns | Notes |
|---|---|---|
| `create(patient: Patient)` | `str` | **Raises `ValueError`** if `patient_id` exists (not idempotent). |
| `get(patient_id: str)` | `Patient \| None` | |
| `delete(patient_id: str)` | `None` | |
| `link_admission(patient_id, admission_id)` | `None` | `HAS_ADMISSION` → Admission |

#### `graph.admissions` — AdmissionRepository
| Method | Returns | Notes |
|---|---|---|
| `create(admission: Admission)` | `str` | `length_of_stay` is computed in Cypher from the dates. |
| `get(admission_id: str)` | `Admission \| None` | |
| `delete(admission_id: str)` | `None` | |
| `link_ward(admission_id, ward_id, room_no=None, bed_no=None)` | `None` | `ADMITTED_TO` → Ward (`room_no`/`bed_no` on the edge) |

#### `graph.opd_visits` — OpdVisitRepository
| Method | Returns | Notes |
|---|---|---|
| `create(visit: OpdVisit)` | `str` | |
| `get(visit_id: str)` | `OpdVisit \| None` | |
| `delete(visit_id: str)` | `None` | |
| `link_patient(visit_id, patient_id)` | `None` | Patient `HAS_OPD_VISIT` → this visit |

#### `graph.wards` — WardRepository
| Method | Returns | Notes |
|---|---|---|
| `create(ward: Ward)` | `str` | |
| `get(ward_id: str)` | `Ward \| None` | |
| `link_department(ward_id, department_id)` | `None` | `IN_DEPARTMENT` → Department |

#### `graph.departments` — DepartmentRepository
| Method | Returns |
|---|---|
| `create(dept: Department)` | `str` |
| `get(department_id: str)` | `Department \| None` |

#### `graph.lab_results` — LabResultRepository
| Method | Returns | Notes |
|---|---|---|
| `create(lab_result: LabResult)` | `str` | |
| `get(lab_id: str)` | `LabResult \| None` | |
| `delete(lab_id: str)` | `None` | |
| `link_specimen(lab_id, specimen_id)` | `None` | Specimen `TESTED_FOR` → this LabResult |

#### `graph.hiv_viral_loads` — HIVViralLoadRepository
| Method | Returns | Notes |
|---|---|---|
| `create(vl: HIVViralLoad)` | `str` | |
| `get(viral_load_id: str)` | `HIVViralLoad \| None` | |
| `delete(viral_load_id: str)` | `None` | |
| `link_patient(viral_load_id, patient_id)` | `None` | Patient `HAS_HIV_VIRAL_LOAD_RESULT` → this load |

### Specimen / Sample

#### `graph.specimens` — SpecimenRepository
| Method | Returns | Notes |
|---|---|---|
| `create(specimen: Specimen)` | `str` | |
| `get(specimen_id: str)` | `Specimen \| None` | |
| `delete(specimen_id: str)` | `None` | |
| `link_patient(specimen_id, patient_id)` | `None` | `COLLECTED_FROM` → Patient |
| `link_visit(specimen_id, visit_id)` | `None` | `COLLECTED_AT_VISIT` → OpdVisit |

#### `graph.samples` — SampleRepository
| Method | Returns | Notes |
|---|---|---|
| `create(sample: Sample)` | `str` | |
| `get(sample_id: str)` | `Sample \| None` | |
| `delete(sample_id: str)` | `None` | |
| `link_specimen(sample_id, specimen_id)` | `None` | `DERIVED_FROM` → Specimen |
| `link_assembly(sample_id, assembly_id)` | `None` | `HAS_ASSEMBLY` → Assembly |

### Genomics repositories

#### `graph.organisms` — OrganismRepository
| Method | Returns | Notes |
|---|---|---|
| `create(organism: Organism)` | `str` | |
| `get(taxid: str)` | `Organism \| None` | |
| `delete(taxid: str)` | `None` | |
| `link_reference_genome(taxid, accession_no)` | `None` | ReferenceGenome `REFERENCE_GENOME_OF` → Organism |

#### `graph.reference_genomes` — ReferenceGenomeRepository
| Method | Returns |
|---|---|
| `create(ref_genome: ReferenceGenome)` | `str` |
| `get(accession_no: str)` | `ReferenceGenome \| None` |
| `delete(accession_no: str)` | `None` |

#### `graph.assemblies` — AssemblyRepository
| Method | Returns | Notes |
|---|---|---|
| `create(assembly: Assembly)` | `NodeCreateOrMatchStats` | |
| `get(assembly_id: str)` | `Assembly \| None` | |
| `delete(assembly_id: str)` | `None` | Cascade-deletes linked Contig nodes. |
| `add_contigs(assembly_id, contigs: list[Contig])` | `NodeAndRelationshipCreationStats` | `HAS_CONTIG`; raises `ValueError` if assembly missing. |

#### `graph.variants` — VariantRepository

A `Variant` node is a **gene-annotation-level** record; identity is the 6-tuple
`(REF_ACC, POS, REF, ALT, hgvs_c, hgvs_p)`. Per-call quality lives on the
`HAS_VARIANT` edge (`VariantCallProps`), not the node.

| Method | Returns | Notes |
|---|---|---|
| `create(variant: Variant)` | `None` | Idempotent `MERGE` on the 6-tuple. |
| `get(ref_acc, pos, ref, alt, hgvs_c="", hgvs_p="")` | `Variant \| None` | |
| `delete(ref_acc, pos, ref, alt, hgvs_c="", hgvs_p="")` | `None` | |
| `link_sample(variant: Variant, sample_id, call_props: VariantCallProps)` | `None` | Sample `HAS_VARIANT` → Variant; sets call props on the edge. |
| `get_by_sample(sample_id)` | `list[tuple[Variant, VariantCallProps]]` | |
| `get_by_ref(ref_accession)` | `list[Variant]` | |
| `bulk_import_from_vcf(vcf_path, sample_id, ref_accession, source, batch_size=500)` | `NodeAndRelationshipCreationStats` | `source: Literal["medaka","snippy"]`; `.vcf` or `.vcf.gz`; Sample must exist. See [parsers](#bulk-import--parsers). |

### Drug resistance

#### `graph.resistance` — DrugResistanceRepository

Node types: `DrugClass`, `Drug`, `Mutation` (identity `(gene, text)`),
`StanfordHIVDRPrediction` (id `"{sample_id}:{gene}:{drug_name}"`).

| Method | Returns | Notes |
|---|---|---|
| `create_drug_class(drug_class: DrugClass)` | `str` | |
| `get_drug_class(name)` | `DrugClass \| None` | |
| `create_drug(drug: Drug)` | `str` | |
| `get_drug(name)` | `Drug \| None` | |
| `create_mutation(mutation: Mutation)` | `Mutation` | |
| `get_mutation(gene, text)` | `Mutation \| None` | |
| `delete_mutation(gene, text)` | `None` | |
| `create_prediction(prediction: StanfordHIVDRPrediction)` | `str` | |
| `get_prediction(prediction_id)` | `StanfordHIVDRPrediction \| None` | |
| `delete_prediction(prediction_id)` | `None` | |
| `bulk_import_from_sierra(json_path, sample_id)` | `NodeAndRelationshipCreationStats` | Builds the full subgraph; Sample must exist. |
| `get_resistance_by_sample(sample_id)` | `list[tuple[StanfordHIVDRPrediction, str \| None]]` | `(prediction, drug_class)` pairs |
| `get_mutations_for_drug(drug_name)` | `list[tuple[Mutation, float \| None]]` | `(mutation, score)` pairs |

Relationships built by `bulk_import_from_sierra`: `HAS_STANFORD_HIVDR_PREDICTION`
(Sample→prediction), `PREDICTS_RESISTANCE_TO` (prediction→Drug), `IN_DRUG_CLASS`
(Drug→DrugClass), `CONFERS_RESISTANCE_TO` (Mutation→Drug, `score` on the edge).

### Analytics

#### `graph.analytics` — AnalyticsRepository

| Method | Returns | Description |
|---|---|---|
| `patient_variants(patient_id)` | `list[PatientVariant]` | Every Variant for a patient via `Patient ← Specimen ← Sample → Variant`. |
| `ward_variant_clusters(min_patients=2)` | `list[WardVariantCluster]` | Variants shared by ≥ `min_patients` distinct patients on the same ward (ordered by `patient_count` desc). Raises `ValueError` if `min_patients < 1`. |

**Result objects**

```python
class PatientVariant:
    specimen_id: str
    sample_id: str
    variant: Variant
    call: VariantCallProps

class WardVariantCluster:
    ward_id: str
    ward_name: str | None
    variant: Variant
    patient_ids: list[str]
    patient_count: int
```

---

## Models

All models are Pydantic v2. **Required** fields have no default; everything else
defaults to `None` unless noted.

### Patient
| Field | Type | Required |
|---|---|---|
| `patient_id` | `str` | ✅ |
| `firstname` | `str` | ✅ |
| `lastname` | `str` | ✅ |
| `sex` | `Literal["M","F","Other"] \| None` | |
| `date_of_birth` | `date \| None` | |
| `age` | `int \| None` | |

> Cross-field rule: **at least one** of `date_of_birth` or `age` is required.

### Admission
| Field | Type | Required |
|---|---|---|
| `admission_id` | `str` | ✅ |
| `date_of_admission` | `date \| None` | |
| `date_of_discharge` | `date \| None` | |
| `length_of_stay` | `int \| None` | (computed on import) |

> Rule: `date_of_discharge` may not precede `date_of_admission`.

### OpdVisit
`visit_id` (✅ `str`), `visit_date` (`date`), `clinic`, `chief_complaint`, `notes` (`str`).

### Ward
`ward_id` ✅, `name` ✅, `department_id` ✅, `ward_type`, `description` (`str`).

### Department
`department_id` ✅, `name` ✅, `description`.

### Specimen
`specimen_id` ✅, `specimen_type` (`str`).

### Sample
`sample_id` ✅.

### Organism
`taxid` ✅ (`str`, NCBI taxid), `sciname`.

### ReferenceGenome
`accession_no` ✅, `name`, `molecular_type`, `strain`, `annotation_source`, `source_database`.

### Assembly
`assembly_id` ✅, `assembler`, `created_at` (`datetime`).

### Contig
`contig_id` ✅, `length` ✅ (`int`), `sequence` ✅, `sequence_hash` ✅, `hash_algorithm` (`str`, default `"md5"`).

### Variant
| Field | Type | Required |
|---|---|---|
| `REF_ACC` | `str` | ✅ |
| `POS` | `int` | ✅ |
| `REF` | `str` | ✅ |
| `ALT` | `str` | ✅ |
| `hgvs_c` | `str` | default `""` |
| `hgvs_p` | `str` | default `""` |
| `CHROM`, `TYPE`, `EFFECT`, `IMPACT`, `gene_name` | `str \| None` | |

> Identity key = `(REF_ACC, POS, REF, ALT, hgvs_c, hgvs_p)`.

### LabResult
`lab_id` ✅, `specimen_id`, `result_type`, `test_date` (`date`), `value`, `unit`, `notes`.

### HIVViralLoad
| Field | Type |
|---|---|
| `viral_load_id` | `str` ✅ |
| `test_date` | `date \| None` |
| `value_copies_per_ml` | `int \| None` |
| `log10_value` | `float \| None` |
| `detection_limit` | `int \| None` |
| `assay_type` | `str \| None` |
| `result_status` | `Literal["detected","undetected","pending"] \| None` |

### DrugClass
`name` ✅, `full_name`.

### Drug
`name` ✅ (Stanford abbreviation), `full_name`, `display_abbr`, `drug_class`.

### Mutation
`gene` ✅, `text` ✅ (e.g. `M184V`), `primary_type`. Identity = `(gene, text)`.

### StanfordHIVDRPrediction
`prediction_id` ✅ (`"{sample_id}:{gene}:{drug_name}"`), `sample_id`, `gene`, `drug_name`, `score` (`float`), `level` (`str`, e.g. `"Susceptible"`).

---

## Bulk import & parsers

The bulk-import repository methods wrap these stateless parsers in
`nosograph.utils`. The parsers return plain `list[dict]` records and require no
database — handy for previewing or custom ETL.

### `nosograph.utils.vcf`
- `parse_medaka_vcf(vcf_path, ref_accession, sample_id) -> list[dict]` — SnpEff-annotated Medaka VCF (VCFv4.1). One record per (row × `ANN` annotation).
- `parse_snippy_vcf(vcf_path, ref_accession, sample_id) -> list[dict]` — SnpEff-annotated Snippy/freebayes VCF (VCFv4.2).

Both accept plain `.vcf` or gzipped `.vcf.gz` (detected by extension).
Consumed by `graph.variants.bulk_import_from_vcf(...)`.

### `nosograph.utils.sierra`
- `parse_sierra_json(json_path, sample_id) -> list[dict]` — read a sierrapy / Stanford HIVdb JSON report (bare list, `{"sequenceAnalysis": [...]}`, or GraphQL `{"data": {...}}`). One record per (gene × drug).
- `parse_sierra_records(analyses: list[dict], sample_id) -> list[dict]` — same, on an already-parsed object.

Consumed by `graph.resistance.bulk_import_from_sierra(...)`.

---

## Types

`from nosograph.types import ...`

| Type | Shape |
|---|---|
| `Neo4JAuth` | `NamedTuple(user: Literal["neo4j"], password: str)` + `from_string()` |
| `VariantCallProps` | `TypedDict(total=False)`: `DP:int`, `GT:str`, `QUAL:float`, `GQ:int`, `AO:int`, `RO:int`, `FILTER:str`, `vcf_source:str` (all `\| None`) |
| `AssemblyProps` | `TypedDict`: `assembly_id`, `assembler`, `created_at` (`str`) |
| `ContigProps` | `TypedDict`: `contig_id:str`, `length:int`, `sequence:str`, `hash_algorithm:str`, `sequence_hash:str` |
| `NodeCreateOrMatchStats` | `TypedDict`: `nodes_matched:int`, `nodes_created:int` |
| `NodeAndRelationshipCreationStats` | `TypedDict`: `nodes_created:int`, `relationships_created:int` |

`Neo4JAuth` and `VariantCallProps` are re-exported from the top-level `nosograph` package.

---

## Pipeline wrapper

`from nosograph.pipeline import NosoGraphPipeline, NosoGraphPipelineOutput, NosoGraphPipelineError`

A thin wrapper around the monorepo Bash assembly pipeline (`micromamba`/conda).
Not part of the graph API; used to run assembly and check its on-disk output.

### `NosoGraphPipeline(script_path, long_reads, short_r1, short_r2, assembler, technology, outdir, genome_size=None, threads=1, racon_iter=0, pilon_iter=0, detach_shell=False)`
- `build_command() -> list[str]` — the argv it will run.
- `run(cwd=None, env=None) -> int` — run it, streaming logs; raises `NosoGraphPipelineError` on non-zero exit.
- `get_output() -> NosoGraphPipelineOutput`

Validates inputs on construction (`assembler ∈ {canu, flye}`, `technology ∈ {pacbio, nanopore}`, `genome_size` required for canu).

### `NosoGraphPipelineOutput(assembler: Literal["canu","flye"], outdir)`
- `check_output_directory() -> bool` — `01_assembly/` and `02_polish/` exist.
- `check_output_files() -> bool` — expected per-assembler files exist (Flye and Canu supported).

---

## Graph schema

**Node labels:** Patient, Admission, OpdVisit, Ward, Department, Specimen,
Sample, Organism, ReferenceGenome, Assembly, Contig, Variant, LabResult,
HIVViralLoad, DrugClass, Drug, Mutation, StanfordHIVDRPrediction.

**Relationship types** (source → target):

| Relationship | From → To | Created by |
|---|---|---|
| `HAS_ADMISSION` | Patient → Admission | `patients.link_admission` |
| `ADMITTED_TO` | Admission → Ward | `admissions.link_ward` (`room_no`, `bed_no` on edge) |
| `HAS_OPD_VISIT` | Patient → OpdVisit | `opd_visits.link_patient` |
| `IN_DEPARTMENT` | Ward → Department | `wards.link_department` |
| `COLLECTED_FROM` | Specimen → Patient | `specimens.link_patient` |
| `COLLECTED_AT_VISIT` | Specimen → OpdVisit | `specimens.link_visit` |
| `TESTED_FOR` | Specimen → LabResult | `lab_results.link_specimen` |
| `HAS_HIV_VIRAL_LOAD_RESULT` | Patient → HIVViralLoad | `hiv_viral_loads.link_patient` |
| `DERIVED_FROM` | Sample → Specimen | `samples.link_specimen` |
| `HAS_ASSEMBLY` | Sample → Assembly | `samples.link_assembly` |
| `HAS_CONTIG` | Assembly → Contig | `assemblies.add_contigs` |
| `REFERENCE_GENOME_OF` | ReferenceGenome → Organism | `organisms.link_reference_genome` |
| `HAS_VARIANT` | Sample → Variant | `variants.link_sample` / VCF import (call props on edge) |
| `HAS_STANFORD_HIVDR_PREDICTION` | Sample → StanfordHIVDRPrediction | sierra import |
| `PREDICTS_RESISTANCE_TO` | StanfordHIVDRPrediction → Drug | sierra import |
| `IN_DRUG_CLASS` | Drug → DrugClass | sierra import |
| `CONFERS_RESISTANCE_TO` | Mutation → Drug | sierra import (`score` on edge) |

Uniqueness / key constraints (Enterprise `NODE KEY`, approximated on Community)
are defined in `nosograph/cypher/_CONSTRAINTS.cypher`; apply them once per
database before bulk loading.
