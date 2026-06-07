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


class OpdVisit(BaseModel):
    """A single outpatient (OPD) clinic encounter for a patient.

    OPD visits are same-day encounters; they are distinct from inpatient
    ``Admission`` nodes.  A visit records the clinic, the reason for
    attendance, and free-text notes made by the clinician.  Specimens
    collected during the visit can be linked via the
    ``COLLECTED_AT_VISIT`` relationship.

    Attributes:
        visit_id: Unique identifier for this OPD encounter.
        visit_date: Calendar date of the visit.
        clinic: Name or specialty of the outpatient clinic (e.g. "HIV Clinic",
            "Internal Medicine").
        chief_complaint: The patient's primary reason for attending.
        notes: Free-text clinician notes recorded during the visit.
    """

    visit_id: str
    visit_date: Optional[date] = None
    clinic: Optional[str] = None
    chief_complaint: Optional[str] = None
    notes: Optional[str] = None


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
