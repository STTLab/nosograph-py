MATCH (s:Specimen {specimen_id: $specimen_id})
MATCH (lr:LabResult {lab_id: $lab_id})
MERGE (s)-[:TESTED_FOR]->(lr)
