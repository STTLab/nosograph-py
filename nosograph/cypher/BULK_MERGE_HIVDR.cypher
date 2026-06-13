// Bulk-import Stanford HIVdb drug-resistance predictions for one Sample.
// Builds, per record:
//   (Sample)-[:HAS_STANFORD_HIVDR_PREDICTION]->(StanfordHIVDRPrediction)-[:PREDICTS_RESISTANCE_TO]->(Drug)-[:IN_DRUG_CLASS]->(DrugClass)
//   (Mutation)-[:CONFERS_RESISTANCE_TO]->(Drug)   (per partial-score mutation)
MATCH (s:Sample {sample_id: $sample_id})
UNWIND $records AS rec
MERGE (dc:DrugClass {name: rec.drug_class})
MERGE (d:Drug {name: rec.drug_name})
    ON CREATE SET d.full_name = rec.drug_full_name, d.display_abbr = rec.drug_display_abbr
MERGE (d)-[:IN_DRUG_CLASS]->(dc)
MERGE (pred:StanfordHIVDRPrediction {prediction_id: rec.prediction_id})
    ON CREATE SET pred.sample_id = $sample_id, pred.gene = rec.gene, pred.drug_name = rec.drug_name
SET pred.score = rec.score, pred.level = rec.level
MERGE (s)-[:HAS_STANFORD_HIVDR_PREDICTION]->(pred)
MERGE (pred)-[:PREDICTS_RESISTANCE_TO]->(d)
FOREACH (mut IN rec.mutations |
    MERGE (m:Mutation {gene: mut.gene, text: mut.text})
    MERGE (m)-[cr:CONFERS_RESISTANCE_TO]->(d)
    SET cr.score = mut.score
)
