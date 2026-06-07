MATCH (p:Patient {patient_id: $patient_id})
DETACH DELETE p
