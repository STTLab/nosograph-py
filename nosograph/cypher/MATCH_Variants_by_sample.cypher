MATCH (s:Sample {sample_id: $sample_id})-[r:HAS_VARIANT]->(v:Variant)
RETURN v, r
