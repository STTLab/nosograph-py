// All Stanford HIVdb resistance predictions for a sample, with the drug
// they predict resistance to and that drug's class.
MATCH (s:Sample {sample_id: $sample_id})-[:HAS_STANFORD_HIVDR_PREDICTION]->(pred:StanfordHIVDRPrediction)
      -[:PREDICTS_RESISTANCE_TO]->(d:Drug)
OPTIONAL MATCH (d)-[:IN_DRUG_CLASS]->(dc:DrugClass)
RETURN pred AS prediction,
       d.name AS drug_name,
       dc.name AS drug_class
ORDER BY pred.gene, drug_name
