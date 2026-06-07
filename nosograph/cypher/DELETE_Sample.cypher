MATCH (s:Sample {sample_id: $sample_id})
DETACH DELETE s
