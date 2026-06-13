// Full genomic provenance traversal for a single patient:
// Patient <-COLLECTED_FROM- Specimen <-DERIVED_FROM- Sample -HAS_VARIANT-> Variant
MATCH (p:Patient {patient_id: $patient_id})<-[:COLLECTED_FROM]-(sp:Specimen)
      <-[:DERIVED_FROM]-(sa:Sample)-[r:HAS_VARIANT]->(v:Variant)
RETURN sp.specimen_id AS specimen_id,
       sa.sample_id AS sample_id,
       v AS variant,
       r AS call
ORDER BY sa.sample_id, v.POS
