MATCH (sa:Sample {sample_id: $sample_id})
MATCH (sp:Specimen {specimen_id: $specimen_id})
MERGE (sa)-[:DERIVED_FROM]->(sp)
