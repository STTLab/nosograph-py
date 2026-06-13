// Mutations that confer resistance to a given drug, with their partial scores.
MATCH (m:Mutation)-[cr:CONFERS_RESISTANCE_TO]->(d:Drug {name: $drug_name})
RETURN m AS mutation, cr.score AS score
ORDER BY m.gene, m.text
