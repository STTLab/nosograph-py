MATCH (w:Ward {ward_id: $ward_id})
MATCH (d:Department {department_id: $department_id})
MERGE (w)-[:IN_DEPARTMENT]->(d)
