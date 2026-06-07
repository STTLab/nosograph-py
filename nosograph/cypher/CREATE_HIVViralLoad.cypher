MERGE (vl:HIVViralLoad {viral_load_id: $viral_load_id})
ON CREATE SET
    vl.test_date = CASE
        WHEN $test_date IS NOT NULL
             AND trim($test_date) <> ""
        THEN date($test_date)
        ELSE NULL
    END,
    vl.value_copies_per_ml = $value_copies_per_ml,
    vl.log10_value = $log10_value,
    vl.detection_limit = $detection_limit,
    vl.assay_type = $assay_type,
    vl.result_status = $result_status,
    vl.created_at = datetime()
RETURN vl.viral_load_id AS id
