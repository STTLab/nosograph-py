MERGE (m:Mutation {gene: $gene, text: $text})
ON CREATE SET m.primary_type = $primary_type
RETURN m
