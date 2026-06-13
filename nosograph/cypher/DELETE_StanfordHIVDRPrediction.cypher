MATCH (pred:StanfordHIVDRPrediction {prediction_id: $prediction_id})
DETACH DELETE pred
