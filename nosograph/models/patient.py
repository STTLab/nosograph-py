from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, model_validator


class Patient(BaseModel):
    patient_id: str
    firstname: str
    lastname: str
    sex: Optional[Literal["M", "F"]] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None

    @model_validator(mode="after")
    def _dob_or_age_required(self) -> "Patient":
        if self.date_of_birth is None and self.age is None:
            raise ValueError("Either date_of_birth or age must be provided")
        return self


class Admission(BaseModel):
    admission_id: str
    date_of_admission: Optional[date] = None
    date_of_discharge: Optional[date] = None
    length_of_stay: Optional[int] = None

    @model_validator(mode="after")
    def _discharge_after_admission(self) -> "Admission":
        if self.date_of_admission and self.date_of_discharge:
            if self.date_of_discharge < self.date_of_admission:
                raise ValueError("date_of_discharge cannot be before date_of_admission")
        return self


class Ward(BaseModel):
    ward_id: str
    name: str
    department_id: str
    ward_type: Optional[str] = None
    description: Optional[str] = None


class Department(BaseModel):
    department_id: str
    name: str
    description: Optional[str] = None
