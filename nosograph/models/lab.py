from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel


class LabResult(BaseModel):
    lab_id: str
    specimen_id: Optional[str] = None
    result_type: Optional[str] = None
    test_date: Optional[date] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class HIVViralLoad(BaseModel):
    viral_load_id: str
    test_date: Optional[date] = None
    value_copies_per_ml: Optional[int] = None
    log10_value: Optional[float] = None
    detection_limit: Optional[int] = None
    assay_type: Optional[str] = None
    result_status: Optional[Literal["detected", "undetected", "pending"]] = None
