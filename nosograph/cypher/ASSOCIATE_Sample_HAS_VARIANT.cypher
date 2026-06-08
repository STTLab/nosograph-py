MATCH (s:Sample {sample_id: $sample_id})
MATCH (v:Variant {REF_ACC: $REF_ACC, POS: $POS, REF: $REF, ALT: $ALT, hgvs_c: $hgvs_c, hgvs_p: $hgvs_p})
MERGE (s)-[r:HAS_VARIANT]->(v)
SET r.DP = $DP, r.GT = $GT, r.QUAL = $QUAL,
    r.GQ = $GQ, r.AO = $AO, r.RO = $RO,
    r.FILTER = $FILTER, r.vcf_source = $vcf_source
RETURN r
