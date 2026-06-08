MATCH (a:Admission {admission_id: $admission_id})
MATCH (ward:Ward {ward_id: $ward_id})
MERGE (a)-[to:ADMITTED_TO]->(ward)
ON CREATE SET
    to.room_no = $room_no,
    to.bed_no = $bed_no