from nosograph.repositories._base import BaseRepository
from nosograph.models.specimen import Specimen, Sample
import nosograph._txs as txs


class SpecimenRepository(BaseRepository):
    """CRUD for Specimen nodes."""

    def create(self, specimen: Specimen) -> str:
        """Create a Specimen node (idempotent) and return its specimen_id."""
        with self._driver.session() as session:
            return session.execute_write(txs._create_specimen, specimen.specimen_id, specimen.specimen_type)

    def get(self, specimen_id: str) -> Specimen | None:
        """Return a Specimen by specimen_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_specimen, specimen_id)
        if raw is None:
            return None
        return Specimen.model_validate({
            "specimen_id": raw.get("specimen_id"),
            "specimen_type": raw.get("specimen_type"),
        })

    def delete(self, specimen_id: str) -> None:
        """Delete a Specimen node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_specimen, specimen_id)

    def link_patient(self, specimen_id: str, patient_id: str) -> None:
        """Create a COLLECTED_FROM relationship from Specimen to an existing Patient node."""
        with self._driver.session() as session:
            session.execute_write(txs._link_specimen_patient, specimen_id, patient_id)


class SampleRepository(BaseRepository):
    """CRUD for Sample nodes."""

    def create(self, sample: Sample) -> str:
        """Create a Sample node (idempotent) and return its sample_id."""
        with self._driver.session() as session:
            return session.execute_write(txs._create_sample, sample.sample_id)

    def get(self, sample_id: str) -> Sample | None:
        """Return a Sample by sample_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_sample, sample_id)
        if raw is None:
            return None
        return Sample.model_validate({"sample_id": raw.get("sample_id")})

    def delete(self, sample_id: str) -> None:
        """Delete a Sample node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_sample, sample_id)

    def link_assembly(self, sample_id: str, assembly_id: str) -> None:
        """Create a HAS_ASSEMBLY relationship from Sample to an existing Assembly node."""
        with self._driver.session() as session:
            session.execute_write(txs._link_sample_assembly, sample_id, assembly_id)
