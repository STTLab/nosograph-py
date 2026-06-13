MERGE (d:Drug {name: $name})
ON CREATE SET
    d.full_name = $full_name,
    d.display_abbr = $display_abbr
RETURN d.name AS name
