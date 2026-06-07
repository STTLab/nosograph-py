MATCH (a:Assembly {assembly_id: $assembly_id})
OPTIONAL MATCH (a)-[:HAS_CONTIG]->(c:Contig)
DETACH DELETE a, c