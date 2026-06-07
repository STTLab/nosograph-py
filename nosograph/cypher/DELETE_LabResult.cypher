MATCH (lr:LabResult {lab_id: $lab_id})
DETACH DELETE lr
