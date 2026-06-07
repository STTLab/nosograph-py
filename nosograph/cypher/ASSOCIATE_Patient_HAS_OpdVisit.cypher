MATCH (p:Patient {patient_id: $patient_id})
MATCH (v:OpdVisit {visit_id: $visit_id})
MERGE (p)-[:HAS_OPD_VISIT]->(v)
