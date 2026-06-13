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
│   ├── types.py             ← Neo4JAuth, AssemblyProps, ContigProps, NodeCreateOrMatchStats, NodeAndRelationshipCreationStats, VariantCallProps
│   ├── pipeline.py          ← NosoGraphPipeline / NosoGraphPipelineOutput
│   ├── cli.py               ← interactive terminal UI (prompt_toolkit)
│   ├── _txs.py              ← private transaction functions (internal)
│   ├── models/
│   │   ├── patient.py       ← Patient, Admission, OpdVisit, Ward, Department (Pydantic v2)
│   │   ├── specimen.py      ← Specimen, Sample
│   │   ├── genomics.py      ← Organism, ReferenceGenome, Assembly, Contig, Variant
│   │   ├── lab.py           ← LabResult, HIVViralLoad
│   │   └── resistance.py    ← DrugClass, Drug, Mutation, StanfordHIVDRPrediction
│   ├── repositories/
│   │   ├── _base.py         ← BaseRepository(driver)
│   │   ├── patient.py       ← PatientRepository
│   │   ├── admission.py     ← AdmissionRepository
│   │   ├── specimen.py      ← SpecimenRepository, SampleRepository
│   │   ├── genomics.py      ← OrganismRepository, AssemblyRepository, ReferenceGenomeRepository
│   │   ├── clinical.py      ← WardRepository, DepartmentRepository, LabResultRepository, HIVViralLoadRepository, OpdVisitRepository
│   │   ├── analytics.py     ← AnalyticsRepository (cross-domain multi-hop traversals)
│   │   └── resistance.py    ← DrugResistanceRepository (+ sierrapy bulk import)
│   │   (genomics.py also defines VariantRepository)
│   ├── cypher/              ← all .cypher files (loaded via importlib.resources)
│   └── utils/
│       ├── vcf.py           ← parse_medaka_vcf / parse_snippy_vcf (SnpEff-annotated VCF parsers)
│       └── sierra.py        ← parse_sierra_json (Stanford HIVdb / sierrapy report parser)
└── tests/
    ├── unit/
    │   ├── test_models.py       ← models only, no DB required
    │   ├── test_types.py        ← Neo4JAuth, TypedDicts
    │   ├── test_db.py           ← NosoGraph, mocked driver
    │   ├── test_vcf_parser.py   ← Medaka/Snippy VCF parsing
    │   ├── test_sierra_parser.py ← Stanford HIVdb / sierrapy parsing
    │   ├── test_analytics.py    ← AnalyticsRepository helpers/validation (mocked driver)
    │   ├── test_pipeline.py     ← NosoGraphPipelineOutput file/dir checks (Canu + Flye)
    │   └── test_cli.py          ← CLI sample methods (mocked connection)
    │   (119 unit tests total)
    └── integration/
        ├── conftest.py           ← testcontainers Neo4j fixture (skips if Docker unavailable)
        └── test_repositories.py  ← 52 tests, requires Docker (incl. VariantRepository, AnalyticsRepository, DrugResistanceRepository, gzipped-VCF functional import)
```

---

## Key Architectural Patterns

- **Cypher loading**: `_txs.py` uses `importlib.resources.files("nosograph.cypher")` at import time. Dict keys = filename without `.cypher` (case-sensitive). New queries → new `.cypher` file, key must match exactly.
- **Repository pattern**: Each entity has a repository class. All repositories take a `neo4j.Driver` (via `BaseRepository`). Each method calls `session.execute_read/write` with a transaction function from `_txs.py`.
- **Transaction functions** (`_txs.py`): return plain `dict | None` or primitives. Repositories convert to Pydantic models via `Model.model_validate(raw)`.
- **NosoGraph** (`db.py`): extends `neo4j.GraphDatabase`, exposes all repositories as properties (`graph.patients`, `graph.assemblies`, etc.), plus back-compat `add_assembly()` / `add_contigs()` methods.
- **Models** (Pydantic v2): field validation + cross-field `model_validator`. `Variant` identity is the 6-tuple `(REF_ACC, POS, REF, ALT, hgvs_c, hgvs_p)` enforced at the Cypher/repository layer (gene-annotation-level nodes), not a computed model field.
- **VCF import**: `utils/vcf.py` parses SnpEff-annotated Medaka and Snippy VCFs (plain `.vcf` or gzipped `.vcf.gz`, via `_open_vcf`) into per-annotation records; `VariantRepository.bulk_import_from_vcf()` batches them into `MERGE`d Variant nodes plus `HAS_VARIANT` relationships carrying call metadata (`VariantCallProps`). Per the HIV-64148 spec, import once per reference (e.g. `K03455.1` HXB2, `AF164485.1` CRF01_AE).
- **Drug-resistance import**: `utils/sierra.py` flattens a Stanford HIVdb / sierrapy JSON report into per-(gene, drug) records; `DrugResistanceRepository.bulk_import_from_sierra()` builds the `DrugClass`/`Drug`/`Mutation`/`StanfordHIVDRPrediction` subgraph in one `MERGE`+`FOREACH` query (`PREDICTS_RESISTANCE_TO`, `CONFERS_RESISTANCE_TO`, `IN_DRUG_CLASS`, `HAS_STANFORD_HIVDR_PREDICTION`). Prediction identity is `{sample_id}:{gene}:{drug_name}` (idempotent re-import).
- **Analytics**: `AnalyticsRepository` (`graph.analytics`) holds cross-domain multi-hop reads — `patient_variants()` (Patient ← Specimen ← Sample → Variant) and `ward_variant_clusters()` (variants shared by ≥N patients in a ward). These rely on the `Sample-[:DERIVED_FROM]->Specimen` edge (`SampleRepository.link_specimen`).

---

## Entity CRUD Status

| Entity | CREATE | GET | DELETE | Relationships | Repository |
|---|---|---|---|---|---|
| Patient | ✅ | ✅ | ✅ | HAS_ADMISSION, HAS_OPD_VISIT | ✅ PatientRepository |
| Admission | ✅ | ✅ | ✅ | ADMITTED_TO | ✅ AdmissionRepository |
| OpdVisit | ✅ | ✅ | ✅ | HAS_OPD_VISIT, COLLECTED_AT_VISIT | ✅ OpdVisitRepository |
| Specimen | ✅ | ✅ | ✅ | COLLECTED_FROM, TESTED_FOR, COLLECTED_AT_VISIT | ✅ SpecimenRepository |
| Sample | ✅ | ✅ | ✅ | HAS_ASSEMBLY, DERIVED_FROM (→Specimen) | ✅ SampleRepository |
| Assembly | ✅ | ✅ | ✅ (cascade) | HAS_CONTIG | ✅ AssemblyRepository |
| Organism | ✅ | ✅ | ✅ | REFERENCE_GENOME_OF | ✅ OrganismRepository |
| ReferenceGenome | ✅ | ✅ | ✅ | — | ✅ ReferenceGenomeRepository |
| Ward | ✅ | ✅ | — | IN_DEPARTMENT | ✅ WardRepository |
| Department | ✅ | ✅ | — | — | ✅ DepartmentRepository |
| LabResult | ✅ | ✅ | ✅ | TESTED_FOR | ✅ LabResultRepository |
| HIVViralLoad | ✅ | ✅ | ✅ | HAS_HIV_VIRAL_LOAD_RESULT | ✅ HIVViralLoadRepository |
| Variant | ✅ | ✅ | ✅ | HAS_VARIANT (Sample→Variant, carries call props) | ✅ VariantRepository (+ dual-VCF bulk import) |
| DrugClass | ✅ | ✅ | — | IN_DRUG_CLASS (Drug→DrugClass) | ✅ DrugResistanceRepository |
| Drug | ✅ | ✅ | — | PREDICTS_RESISTANCE_TO, CONFERS_RESISTANCE_TO, IN_DRUG_CLASS | ✅ DrugResistanceRepository |
| Mutation | ✅ | ✅ | ✅ | CONFERS_RESISTANCE_TO (Mutation→Drug, score on edge) | ✅ DrugResistanceRepository |
| StanfordHIVDRPrediction | ✅ | ✅ | ✅ | HAS_STANFORD_HIVDR_PREDICTION (Sample→pred), PREDICTS_RESISTANCE_TO (→Drug) | ✅ DrugResistanceRepository (+ sierrapy bulk import) |

**Cross-domain reads** (`AnalyticsRepository`, `graph.analytics`): `patient_variants(patient_id)`, `ward_variant_clusters(min_patients=2)`.

---

## Known Bugs — All Fixed

All 8 bugs from the initial audit (2026-06-07) are resolved.

---

## What Is Still Missing

- `cli.py` `load_csv()` stub — CSV ETL still unimplemented (FR-01); example CSVs in `example/csv/` have no loader
- FR-07 reporting — not started
- Resistance module: sierrapy is wired (parser + repository + bulk import); the upstream `sierrapy` invocation itself (FASTA → JSON) is not yet automated in `pipeline.py`
- Clinical-terminology domain (SNOMED/Disorder/Finding) from the SRS — not modeled

---

## Recommended Next Actions

### Priority 5 — CSV ETL completion
1. Implement `cli.py` `load_csv()` for bulk CSV import via pandas (dispatch the `example/csv/` files to existing repositories); add `Antibiotic` + transfer relationships for the orphaned CSVs
2. Automate the `sierrapy fasta … -o report.json` invocation in `pipeline.py` to feed `bulk_import_from_sierra`

### Priority 6 — Reporting & terminology
3. Implement FR-07 reporting output (e.g. per-patient resistance + genomic summary)
4. Model the SRS clinical-terminology domain (SNOMED/Disorder) if required for the target use cases

---

## Testing

```bash
pytest tests/unit/          # no database required
pytest tests/integration/   # requires Docker (testcontainers)
```

---

## HIV-64148 Pipeline Output Spec

The HIV drug-resistance pipeline emits **one directory per sample**, named by sample ID (e.g. `03D1/`). A reference sample tree lives at `.claude/sample_files/sample_pipeline_output/03D1/`. The library's ETL/import code should treat the layout below as the contract.

### Top-level files (per sample `<SID>/`)

| Path | Producer | Content |
|---|---|---|
| `<SID>.filtered.fq.gz` | filtlong/NanoFilt | quality/length-filtered reads |
| `<SID>.dedup.fq.gz` | dedup step | deduplicated reads (input to assembly) |
| `<SID>_HIV64148_report.html` | report builder | final human-readable report (`<h1>HIV-64148 Report`; sections: Patient information, Sequencing info, Analyses) |
| `sierrapy_result.0.json` | sierrapy (Stanford HIVdb) | drug-resistance interpretation — **primary HIVDR import source** |

### Numbered stage directories

| Dir | Stage / tool | Key files |
|---|---|---|
| `00_nanostat/<SID>` | NanoStat | plain-text read-QC summary (mean/median len & qual, N50, total bases, `>Qn` cutoff table) |
| `00_qualimap/` | Qualimap BamQC | `genome_results.txt` (coverage/mapping stats), `qualimapReport.html`, `raw_data_qualimapReport/`, `images_qualimapReport/` |
| `01_flye/` | Flye assembly | `assembly.fasta`, `assembly_info.txt` (`#seq_name length cov. circ. repeat mult. alt_group graph_path`), `assembly_graph.{gfa,gv}`, intermediate `NN-*/` subdirs |
| `02_racon/` | Racon polishing | `racon_iter_{1,2,3}.fa`, `overlap_iter_N.paf`, `final_polished.fa` |
| `03_medaka_consensus/` | Medaka consensus | `consensus.fasta` (contigs named `contig_N`), `consensus.contig_renamed.fa` (renamed `<SID>_contig_N`), `calls_to_draft.bam`, `<SID>_consensus_to_01AE.{paf,bam}`; subdirs `msa/`, `mummer/`, `chimera_detection/{de_novo,reference_based,reads_backed}/` |
| `04_quast/` | QUAST | `report.{txt,tsv,html,pdf}`, `transposed_report.*`, `basic_stats/`, `contigs_reports/`, `reads_stats/` |
| `05_blast/` | BLAST+ | per-DB hits `medaka_consensus.fa.<db>.blast.{tsv,json,asn}` for `core_nt` and `los_alamos` (HIV64148_LosAlamos). TSV has commented `# Fields:` header; JSON is NCBI `BlastOutput2` |
| `05_medaka_variant/<REF>/` | Medaka variant + SnpEff | one subdir **per reference**: `HXB2` (K03455.1) and `CRF01_AE`. Each has `medaka.annotated.vcf.gz`(+`.gzi`), `sample_1_medaka.annotated.vcf`, `calls_to_ref.bam`(+`.bai`), `snpEff_summary.html`, `snpeff.stats.csv`, `snpEff_summary.genes.txt` |
| `06_multiqc/` | MultiQC | `multiqc_report.html`, `06_multiqc_data/` (per-tool tables + `multiqc_data.json`) |

### Import-relevant formats

- **Annotated VCF** (`05_medaka_variant/<REF>/sample_1_medaka.annotated.vcf`): VCFv4.1, SnpEff-annotated. `INFO/ANN` is the standard pipe-delimited SnpEff field (`Allele|Annotation|Impact|Gene_Name|Gene_ID|...|HGVS.c|HGVS.p|...`); `INFO/GENE` lists affected genes; `INFO/TYPE` ∈ {SNP, MNP, INDEL, OTHER}. Sample column `FORMAT=GT:GQ`. This is parsed by `utils/vcf.parse_medaka_vcf` → `VariantRepository.bulk_import_from_vcf` (REF accession e.g. `K03455.1`). Note variants are emitted against **multiple references** — import per-reference.
- **sierrapy JSON** (`sierrapy_result.0.json`): top-level **list**, one element per input contig/sequence. Each element: `inputSequence{header, SHA512}`, `strain`, `subtypeText` (e.g. `"CRF01_AE (1.61%)"`), `validationResults`, `alignedGeneSequences`, `drugResistance[]`. Each `drugResistance` entry: `gene{name}` (PR/RT/IN), `drugScores[]` with `drugClass{name}`, `drug{name,displayAbbr}`, `score`, `level`, `text` (e.g. `"Susceptible"`), `partialScores[]`. Parsed by `utils/sierra.parse_sierra_json` → `DrugResistanceRepository.bulk_import_from_sierra`.

### Notes for ETL

- Sample ID is recoverable from the directory name and the `<SID>_` contig-rename prefix in `03_medaka_consensus/consensus.contig_renamed.fa`.
- The two genomics import paths from one sample run: **variants** (per-reference annotated VCFs under `05_medaka_variant/`) and **drug resistance** (`sierrapy_result.0.json`).
- HTML/PDF/BAM/HDF artifacts are for human review and provenance, not graph import.
