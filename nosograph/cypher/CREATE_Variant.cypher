MERGE (v:Variant {variant_key: $variant_key})
ON CREATE SET
    v.REF_ACC = $REF_ACC,
    v.POS = $POS,
    v.REF = $REF,
    v.ALT = $ALT,
    v.CHROM = $CHROM,
    v.TYPE = $TYPE,
    v.DP = $DP,
    v.AO = $AO,
    v.RO = $RO,
    v.QUAL = $QUAL,
    v.GT = $GT,
    v.EFFECT = $EFFECT,
    v.IMPACT = $IMPACT
RETURN v
