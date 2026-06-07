MATCH (v:OpdVisit {visit_id: $visit_id})
DETACH DELETE v
