MATCH (m:Mutation {gene: $gene, text: $text})
DETACH DELETE m
