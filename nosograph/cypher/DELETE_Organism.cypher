MATCH (o:Organism {taxid: $taxid})
DETACH DELETE o
