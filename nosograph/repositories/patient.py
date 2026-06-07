from nosograph.repositories._base import BaseRepository
from nosograph.models.patient import Patient
import nosograph._txs as txs


class PatientRepository(BaseRepository):
    """CRUD for Patient nodes."""

    def create(self, patient: Patient) -> str:
        """Create a Patient node and return its patient_id. Raises ValueError if the id already exists."""
        with self._driver.session() as session:
            count = session.execute_read(
                lambda tx: tx.run(
                    "MATCH (p:Patient {patient_id: $pid}) RETURN count(p) AS n",
                    pid=patient.patient_id,
                ).single()["n"]
            )
            if count > 0:
                raise ValueError(f"Patient '{patient.patient_id}' already exists")
            return session.execute_write(
                txs._create_patient_tx,
                patient.patient_id,
                patient.firstname,
                patient.lastname,
                patient.sex,
                patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                patient.age,
            )

    def get(self, patient_id: str) -> Patient | None:
        """Return a Patient by patient_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_patient_by_id, patient_id)
        if raw is None:
            return None
        return Patient.model_validate({
            "patient_id": raw.get("patient_id"),
            "firstname": raw.get("firstname"),
            "lastname": raw.get("lastname"),
            "sex": raw.get("sex"),
            "date_of_birth": raw.get("date_of_birth"),
            "age": raw.get("age"),
        })

    def delete(self, patient_id: str) -> None:
        """Delete a Patient node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_patient, patient_id)

    def link_admission(self, patient_id: str, admission_id: str) -> None:
        """Create a HAS_ADMISSION relationship from Patient to an existing Admission node."""
        with self._driver.session() as session:
            session.execute_write(txs._link_patient_admission, patient_id, admission_id)
