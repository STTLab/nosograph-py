MERGE (dc:DrugClass {name: $name})
ON CREATE SET dc.full_name = $full_name
RETURN dc.name AS name
