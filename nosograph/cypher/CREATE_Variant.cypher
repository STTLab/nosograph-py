MERGE (v:Variant {REF_ACC: $REF_ACC, POS: $POS, REF: $REF, ALT: $ALT, hgvs_c: $hgvs_c, hgvs_p: $hgvs_p})
ON CREATE SET
    v.CHROM = $CHROM,
    v.TYPE = $TYPE,
    v.EFFECT = $EFFECT,
    v.IMPACT = $IMPACT,
    v.gene_name = $gene_name
RETURN v
