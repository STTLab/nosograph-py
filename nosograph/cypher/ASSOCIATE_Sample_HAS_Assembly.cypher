MATCH (s:Sample {sample_id: $sample_id})
MATCH (a:Assembly {assembly_id: $assembly_id})
MERGE (s)-[:HAS_ASSEMBLY]->(a)
