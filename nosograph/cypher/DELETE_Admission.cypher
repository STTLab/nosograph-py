MATCH (a:Admission {admission_id: $admission_id})
DETACH DELETE a
