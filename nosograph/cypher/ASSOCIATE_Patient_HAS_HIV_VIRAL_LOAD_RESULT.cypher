MATCH (p:Patient {patient_id: $patient_id})
MATCH (vl:HIVViralLoad {viral_load_id: $viral_load_id})
MERGE (p)-[:HAS_HIV_VIRAL_LOAD_RESULT]->(vl)
