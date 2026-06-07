from nosograph.repositories._base import BaseRepository
from nosograph.models.patient import Admission
import nosograph._txs as txs


class AdmissionRepository(BaseRepository):

    def create(self, admission: Admission) -> str:
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_admission,
                admission.admission_id,
                admission.date_of_admission.isoformat() if admission.date_of_admission else None,
                admission.date_of_discharge.isoformat() if admission.date_of_discharge else None,
            )

    def get(self, admission_id: str) -> Admission | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_admission, admission_id)
        if raw is None:
            return None
        def _to_native(val):
            return val.to_native() if hasattr(val, "to_native") else val

        return Admission.model_validate({
            "admission_id": raw.get("admission_id"),
            "date_of_admission": _to_native(raw.get("date_of_admission")),
            "date_of_discharge": _to_native(raw.get("date_of_discharge")),
            "length_of_stay": raw.get("length_of_stay"),
        })

    def delete(self, admission_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_admission, admission_id)

    def link_ward(
        self,
        admission_id: str,
        ward_id: str,
        room_no: str | None = None,
        bed_no: str | None = None,
    ) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._link_admission_ward, admission_id, ward_id, room_no, bed_no)
