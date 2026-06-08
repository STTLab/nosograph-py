UNWIND $variants AS v
MERGE (var:Variant {REF_ACC: v.REF_ACC, POS: v.POS, REF: v.REF, ALT: v.ALT, hgvs_c: v.hgvs_c, hgvs_p: v.hgvs_p})
ON CREATE SET
    var.CHROM = v.CHROM,
    var.TYPE = v.TYPE,
    var.EFFECT = v.EFFECT,
    var.IMPACT = v.IMPACT,
    var.gene_name = v.gene_name
WITH var, v
MATCH (s:Sample {sample_id: v.sample_id})
MERGE (s)-[r:HAS_VARIANT]->(var)
SET r.DP = v.DP, r.GT = v.GT, r.QUAL = v.QUAL,
    r.GQ = v.GQ, r.AO = v.AO, r.RO = v.RO,
    r.FILTER = v.FILTER, r.vcf_source = v.vcf_source
RETURN count(var) AS processed
