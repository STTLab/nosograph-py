MERGE (v:OpdVisit {visit_id: $visit_id})
ON CREATE SET
    v.visit_date = CASE
        WHEN $visit_date IS NOT NULL AND trim($visit_date) <> ""
        THEN date($visit_date)
        ELSE NULL
    END,
    v.clinic = $clinic,
    v.chief_complaint = $chief_complaint,
    v.notes = $notes
