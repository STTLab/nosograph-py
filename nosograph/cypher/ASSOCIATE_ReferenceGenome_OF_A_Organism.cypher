MATCH (refg: ReferenceGenome {accession_no: $accession_no})
MATCH (o:Organism {taxid:$taxid})
MERGE (refg)-[:REFERENCE_GENOME_OF]->(o)