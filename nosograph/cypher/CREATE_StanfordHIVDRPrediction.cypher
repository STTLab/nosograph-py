MERGE (pred:StanfordHIVDRPrediction {prediction_id: $prediction_id})
ON CREATE SET
    pred.sample_id = $sample_id,
    pred.gene = $gene,
    pred.drug_name = $drug_name,
    pred.score = $score,
    pred.level = $level,
    pred.created_at = datetime()
RETURN pred.prediction_id AS prediction_id
