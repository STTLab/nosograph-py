MERGE (w:Ward {ward_id: $ward_id})
ON CREATE SET
    w.name = $name,
    w.department_id = $department_id,
    w.ward_type = $ward_type,
    w.description = $description,
    w.created_at = datetime()
RETURN w
