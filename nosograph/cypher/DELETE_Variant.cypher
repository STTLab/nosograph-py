MATCH (v:Variant {REF_ACC: $REF_ACC, POS: $POS, REF: $REF, ALT: $ALT, hgvs_c: $hgvs_c, hgvs_p: $hgvs_p})
DETACH DELETE v
