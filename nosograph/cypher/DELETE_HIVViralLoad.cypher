MATCH (vl:HIVViralLoad {viral_load_id: $viral_load_id})
DETACH DELETE vl
