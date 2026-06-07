MERGE (lr:LabResult {lab_id: $lab_id})
ON CREATE SET
    lr.specimen_id = $specimen_id,
    lr.result_type = $result_type,
    lr.test_date = CASE
        WHEN $test_date IS NOT NULL
             AND trim($test_date) <> ""
        THEN date($test_date)
        ELSE NULL
    END,
    lr.value = $value,
    lr.unit = $unit,
    lr.notes = $notes,
    lr.created_at = datetime()
RETURN lr.lab_id AS id
