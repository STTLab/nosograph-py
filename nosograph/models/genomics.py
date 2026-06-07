from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, computed_field


class Organism(BaseModel):
    taxid: str
    sciname: Optional[str] = None


class ReferenceGenome(BaseModel):
    accession_no: str
    name: Optional[str] = None
    molecular_type: Optional[str] = None
    strain: Optional[str] = None
    annotation_source: Optional[str] = None
    source_database: Optional[str] = None


class Assembly(BaseModel):
    assembly_id: str
    assembler: Optional[str] = None
    created_at: Optional[datetime] = None


class Contig(BaseModel):
    contig_id: str
    length: int
    sequence: str
    hash_algorithm: str = "md5"
    sequence_hash: str


class Variant(BaseModel):
    REF_ACC: str
    POS: int
    REF: str
    ALT: str
    CHROM: Optional[str] = None
    TYPE: Optional[str] = None
    DP: Optional[int] = None
    AO: Optional[int] = None
    RO: Optional[int] = None
    QUAL: Optional[float] = None
    GT: Optional[str] = None
    EFFECT: Optional[str] = None
    IMPACT: Optional[str] = None

    @computed_field
    @property
    def variant_key(self) -> str:
        return f"{self.REF_ACC}:{self.POS}:{self.REF}>{self.ALT}"
