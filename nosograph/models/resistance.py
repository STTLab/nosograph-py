from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DrugClass(BaseModel):
    """An antiretroviral drug class (e.g. NRTI, NNRTI, PI, INSTI)."""

    name: str
    full_name: Optional[str] = None


class Drug(BaseModel):
    """An antiretroviral drug. Identity is the Stanford abbreviation (``name``)."""

    name: str
    full_name: Optional[str] = None
    display_abbr: Optional[str] = None
    drug_class: Optional[str] = None


class Mutation(BaseModel):
    """A resistance-associated mutation, identified by (gene, text).

    ``text`` is the Stanford mutation notation, e.g. ``M184V`` on gene ``RT``.
    """

    gene: str
    text: str
    primary_type: Optional[str] = None


class StanfordHIVDRPrediction(BaseModel):
    """A Stanford HIVdb drug-resistance prediction for one sample/gene/drug.

    ``prediction_id`` is a deterministic composite ``{sample_id}:{gene}:{drug_name}``
    so re-importing the same sierrapy report updates rather than duplicates.
    """

    prediction_id: str
    sample_id: Optional[str] = None
    gene: Optional[str] = None
    drug_name: Optional[str] = None
    score: Optional[float] = None
    level: Optional[str] = None
