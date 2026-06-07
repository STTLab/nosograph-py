MATCH (s:Specimen {specimen_id: $specimen_id})
DETACH DELETE s
