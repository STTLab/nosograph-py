MATCH (refg:ReferenceGenome {accession_no: $accession_no})
DETACH DELETE refg
