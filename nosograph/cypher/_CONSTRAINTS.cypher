

// Note: The key constraint is for enterprise edition.
// Existance and Uniqueness constraints are required
// to replicate the key constraint in community edition.

// Ward
CREATE CONSTRAINT ward_must_have_id IF NOT EXISTS 
FOR (ward:Ward) REQUIRE ward.ward_id IS NOT NULL;
CREATE CONSTRAINT ward_id_must_be_unique IF NOT EXISTS
FOR (ward:Ward) REQUIRE ward.ward_id IS UNIQUE;

// Department
CREATE CONSTRAINT department_must_have_id IF NOT EXISTS
FOR (department:Department) REQUIRE department.department_id IS NOT NULL;
CREATE CONSTRAINT department_id_must_be_unique IF NOT EXISTS
FOR (department:Department) REQUIRE department.department_id IS UNIQUE;

// Patient
CREATE CONSTRAINT patient_must_have_id IF NOT EXISTS
FOR (patient:Patient) REQUIRE patient.patient_id IS NOT NULL;
CREATE CONSTRAINT patient_id_must_be_unique IF NOT EXISTS
FOR (patient:Patient) REQUIRE patient.patient_id IS UNIQUE;

// OpdVisit
CREATE CONSTRAINT opd_visit_must_have_id IF NOT EXISTS
FOR (v:OpdVisit) REQUIRE v.visit_id IS NOT NULL;
CREATE CONSTRAINT opd_visit_id_must_be_unique IF NOT EXISTS
FOR (v:OpdVisit) REQUIRE v.visit_id IS UNIQUE;

// Admission
CREATE CONSTRAINT admission_must_have_id IF NOT EXISTS
FOR (admission:Admission) REQUIRE admission.admission_id IS NOT NULL;
CREATE CONSTRAINT admission_id_must_be_unique IF NOT EXISTS
FOR (admission:Admission) REQUIRE admission.admission_id IS UNIQUE;

// Specimen
CREATE CONSTRAINT specimen_must_have_id IF NOT EXISTS
FOR (specimen:Specimen) REQUIRE specimen.specimen_id IS NOT NULL;
CREATE CONSTRAINT specimen_id_must_be_unique IF NOT EXISTS
FOR (specimen:Specimen) REQUIRE specimen.specimen_id IS UNIQUE;

// Sample
CREATE CONSTRAINT sample_must_have_id IF NOT EXISTS
FOR (sample:Sample) REQUIRE sample.sample_id IS NOT NULL;
CREATE CONSTRAINT sample_id_must_be_unique IF NOT EXISTS
FOR (sample:Sample) REQUIRE sample.sample_id IS UNIQUE;

//LabResult
/*
The model expects (:LabResult:<Subtype>)

The constrains on :LabResult applies to ALL nodes carrying the :LabResult label, including:
 - :LabResult:CBC
 - :LabResult:BacterialCulture
 - :LabResult:Pathology
 - etc.
*/
CREATE CONSTRAINT lab_result_id_exists IF NOT EXISTS
FOR (lr:LabResult) REQUIRE lr.lab_id IS NOT NULL;
CREATE CONSTRAINT lab_result_id_unique IF NOT EXISTS
FOR (lr:LabResult) REQUIRE lr.lab_id IS UNIQUE;

// HIVViralLoad
CREATE CONSTRAINT hiv_viral_load_must_have_id IF NOT EXISTS
FOR (vl:HIVViralLoad) REQUIRE vl.viral_load_id IS NOT NULL;
CREATE CONSTRAINT hiv_viral_load_id_must_be_unique IF NOT EXISTS
FOR (vl:HIVViralLoad) REQUIRE vl.viral_load_id IS UNIQUE;

// Variant
// Identity: (REF_ACC, POS, REF, ALT, hgvs_c, hgvs_p) — one node per gene-level annotation
CREATE CONSTRAINT variant_ref_acc_must_exist IF NOT EXISTS
FOR (variant:Variant)
REQUIRE variant.REF_ACC IS NOT NULL;

CREATE CONSTRAINT variant_pos_must_exist IF NOT EXISTS
FOR (variant:Variant)
REQUIRE variant.POS IS NOT NULL;

CREATE CONSTRAINT variant_ref_must_exist IF NOT EXISTS
FOR (variant:Variant)
REQUIRE variant.REF IS NOT NULL;

CREATE CONSTRAINT variant_alt_must_exist IF NOT EXISTS
FOR (variant:Variant)
REQUIRE variant.ALT IS NOT NULL;

// NODE KEY enforces uniqueness + NOT NULL on the composite identity key.
// This prevents duplicate Variant nodes under concurrent MERGE.
// Enterprise edition required; Community edition can only approximate this
// with separate existence + uniqueness constraints per property.
CREATE CONSTRAINT variant_identity_key IF NOT EXISTS
FOR (v:Variant)
REQUIRE (v.REF_ACC, v.POS, v.REF, v.ALT, v.hgvs_c, v.hgvs_p) IS NODE KEY;

// Drug resistance (Stanford HIVdb)

// DrugClass
CREATE CONSTRAINT drug_class_must_have_name IF NOT EXISTS
FOR (dc:DrugClass) REQUIRE dc.name IS NOT NULL;
CREATE CONSTRAINT drug_class_name_must_be_unique IF NOT EXISTS
FOR (dc:DrugClass) REQUIRE dc.name IS UNIQUE;

// Drug
CREATE CONSTRAINT drug_must_have_name IF NOT EXISTS
FOR (d:Drug) REQUIRE d.name IS NOT NULL;
CREATE CONSTRAINT drug_name_must_be_unique IF NOT EXISTS
FOR (d:Drug) REQUIRE d.name IS UNIQUE;

// StanfordHIVDRPrediction
CREATE CONSTRAINT hivdr_prediction_must_have_id IF NOT EXISTS
FOR (pred:StanfordHIVDRPrediction) REQUIRE pred.prediction_id IS NOT NULL;
CREATE CONSTRAINT hivdr_prediction_id_must_be_unique IF NOT EXISTS
FOR (pred:StanfordHIVDRPrediction) REQUIRE pred.prediction_id IS UNIQUE;

// Mutation
// Identity: (gene, text) — e.g. (RT, M184V)
CREATE CONSTRAINT mutation_gene_must_exist IF NOT EXISTS
FOR (m:Mutation) REQUIRE m.gene IS NOT NULL;
CREATE CONSTRAINT mutation_text_must_exist IF NOT EXISTS
FOR (m:Mutation) REQUIRE m.text IS NOT NULL;
// NODE KEY (Enterprise) prevents duplicate Mutation nodes under concurrent MERGE.
CREATE CONSTRAINT mutation_identity_key IF NOT EXISTS
FOR (m:Mutation)
REQUIRE (m.gene, m.text) IS NODE KEY;
