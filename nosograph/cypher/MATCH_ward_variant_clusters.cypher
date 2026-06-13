// Outbreak signal: variants shared by >= $min_patients distinct patients
// admitted to the same ward. Traverses
// Ward <-ADMITTED_TO- Admission <-HAS_ADMISSION- Patient
//      <-COLLECTED_FROM- Specimen <-DERIVED_FROM- Sample -HAS_VARIANT-> Variant
MATCH (w:Ward)<-[:ADMITTED_TO]-(:Admission)<-[:HAS_ADMISSION]-(p:Patient)
      <-[:COLLECTED_FROM]-(:Specimen)<-[:DERIVED_FROM]-(:Sample)-[:HAS_VARIANT]->(v:Variant)
WITH w, v, collect(DISTINCT p.patient_id) AS patient_ids
WHERE size(patient_ids) >= $min_patients
RETURN w.ward_id AS ward_id,
       w.name AS ward_name,
       v AS variant,
       patient_ids,
       size(patient_ids) AS patient_count
ORDER BY patient_count DESC, ward_id
