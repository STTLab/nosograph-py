from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Specimen(BaseModel):
    specimen_id: str
    specimen_type: Optional[str] = None


class Sample(BaseModel):
    sample_id: str
