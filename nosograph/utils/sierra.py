from __future__ import annotations
import json
from typing import Any


def _unwrap(data: Any) -> list[dict]:
    """Return the list of sequenceAnalysis objects from any sierrapy shape.

    Accepts a bare list, ``{"sequenceAnalysis": [...]}``, or the GraphQL
    envelope ``{"data": {"sequenceAnalysis": [...]}}``.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "sequenceAnalysis" in data:
            return data["sequenceAnalysis"]
        if "data" in data and isinstance(data["data"], dict):
            return data["data"].get("sequenceAnalysis", [])
    raise ValueError("Unrecognized sierrapy JSON structure")


def _mutations(partial_scores: list[dict], gene: str) -> list[dict]:
    """Flatten partialScores into per-mutation records carrying the partial score."""
    out: list[dict] = []
    for partial in partial_scores or []:
        score = partial.get("score")
        for mut in partial.get("mutations") or []:
            text = mut.get("text")
            if not text:
                continue
            out.append({"gene": gene, "text": text, "score": score})
    return out


def parse_sierra_records(analyses: list[dict], sample_id: str) -> list[dict]:
    """Flatten parsed sierrapy sequenceAnalysis objects into per-(gene, drug)
    records ready for the BULK_MERGE_HIVDR Cypher query.

    All records are attributed to ``sample_id`` (one sample per import).
    """
    records: list[dict] = []
    for analysis in analyses:
        for dr in analysis.get("drugResistance") or []:
            gene = (dr.get("gene") or {}).get("name")
            for ds in dr.get("drugScores") or []:
                drug = ds.get("drug") or {}
                drug_class = (ds.get("drugClass") or {}).get("name")
                drug_name = drug.get("name")
                if not drug_name:
                    continue
                records.append({
                    "prediction_id": f"{sample_id}:{gene}:{drug_name}",
                    "sample_id": sample_id,
                    "gene": gene,
                    "drug_class": drug_class,
                    "drug_name": drug_name,
                    "drug_full_name": drug.get("fullName"),
                    "drug_display_abbr": drug.get("displayAbbr"),
                    "score": ds.get("score"),
                    "level": ds.get("text"),
                    "mutations": _mutations(ds.get("partialScores"), gene),
                })
    return records


def parse_sierra_json(json_path: str, sample_id: str) -> list[dict]:
    """Read a sierrapy/Stanford HIVdb JSON report and flatten it into records
    for one sample. See :func:`parse_sierra_records`.
    """
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)
    return parse_sierra_records(_unwrap(data), sample_id)
