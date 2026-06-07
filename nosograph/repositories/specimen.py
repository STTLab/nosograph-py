from nosograph.repositories._base import BaseRepository
from nosograph.models.specimen import Specimen, Sample
import nosograph._txs as txs


class SpecimenRepository(BaseRepository):

    def create(self, specimen: Specimen) -> str:
        with self._driver.session() as session:
            return session.execute_write(txs._create_specimen, specimen.specimen_id, specimen.specimen_type)

    def get(self, specimen_id: str) -> Specimen | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_specimen, specimen_id)
        if raw is None:
            return None
        return Specimen.model_validate({
            "specimen_id": raw.get("specimen_id"),
            "specimen_type": raw.get("specimen_type"),
        })

    def delete(self, specimen_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_specimen, specimen_id)

    def link_patient(self, specimen_id: str, patient_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._link_specimen_patient, specimen_id, patient_id)


class SampleRepository(BaseRepository):

    def create(self, sample: Sample) -> str:
        with self._driver.session() as session:
            return session.execute_write(txs._create_sample, sample.sample_id)

    def get(self, sample_id: str) -> Sample | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_sample, sample_id)
        if raw is None:
            return None
        return Sample.model_validate({"sample_id": raw.get("sample_id")})

    def delete(self, sample_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_sample, sample_id)

    def link_assembly(self, sample_id: str, assembly_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._link_sample_assembly, sample_id, assembly_id)
