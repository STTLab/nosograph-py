MATCH (s:Specimen {specimen_id: $specimen_id})
MATCH (v:OpdVisit {visit_id: $visit_id})
MERGE (s)-[:COLLECTED_AT_VISIT]->(v)
