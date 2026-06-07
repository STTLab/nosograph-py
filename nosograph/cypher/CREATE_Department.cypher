MERGE (d:Department {department_id: $department_id})
ON CREATE SET
    d.name = $name,
    d.description = $description,
    d.created_at = datetime()
RETURN d
