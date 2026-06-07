from nosograph.repositories._base import BaseRepository
from nosograph.models.patient import Ward, Department
from nosograph.models.lab import LabResult, HIVViralLoad
import nosograph._txs as txs


class WardRepository(BaseRepository):
    """CRUD for Ward nodes."""

    def create(self, ward: Ward) -> str:
        """Create a Ward node (idempotent) and return its ward_id."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_ward,
                ward_id=ward.ward_id,
                name=ward.name,
                department_id=ward.department_id,
                ward_type=ward.ward_type,
                description=ward.description,
            )

    def get(self, ward_id: str) -> Ward | None:
        """Return a Ward by ward_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_ward, ward_id)
        if raw is None:
            return None
        return Ward.model_validate({
            "ward_id": raw.get("ward_id"),
            "name": raw.get("name"),
            "department_id": raw.get("department_id"),
            "ward_type": raw.get("ward_type"),
            "description": raw.get("description"),
        })

    def link_department(self, ward_id: str, department_id: str) -> None:
        """Create an IN_DEPARTMENT relationship from Ward to an existing Department node."""
        with self._driver.session() as session:
            session.execute_write(txs._link_ward_department, ward_id, department_id)


class DepartmentRepository(BaseRepository):
    """CRUD for Department nodes."""

    def create(self, dept: Department) -> str:
        """Create a Department node (idempotent) and return its department_id."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_department,
                department_id=dept.department_id,
                name=dept.name,
                description=dept.description,
            )

    def get(self, department_id: str) -> Department | None:
        """Return a Department by department_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_department, department_id)
        if raw is None:
            return None
        return Department.model_validate({
            "department_id": raw.get("department_id"),
            "name": raw.get("name"),
            "description": raw.get("description"),
        })


class LabResultRepository(BaseRepository):
    """CRUD for LabResult nodes. result_type is stored as a property (e.g. 'CBC', 'BacterialCulture')."""

    def create(self, lab_result: LabResult) -> str:
        """Create a LabResult node (idempotent) and return its lab_id."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_lab_result,
                lab_result.lab_id,
                lab_result.specimen_id,
                lab_result.result_type,
                lab_result.test_date.isoformat() if lab_result.test_date else None,
                lab_result.value,
                lab_result.unit,
                lab_result.notes,
            )

    def get(self, lab_id: str) -> LabResult | None:
        """Return a LabResult by lab_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_lab_result, lab_id)
        if raw is None:
            return None
        def _to_native(val):
            return val.to_native() if hasattr(val, "to_native") else val

        return LabResult.model_validate({
            "lab_id": raw.get("lab_id"),
            "specimen_id": raw.get("specimen_id"),
            "result_type": raw.get("result_type"),
            "test_date": _to_native(raw.get("test_date")),
            "value": raw.get("value"),
            "unit": raw.get("unit"),
            "notes": raw.get("notes"),
        })

    def delete(self, lab_id: str) -> None:
        """Delete a LabResult node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_lab_result, lab_id)

    def link_specimen(self, lab_id: str, specimen_id: str) -> None:
        """Create a TESTED_FOR relationship from an existing Specimen node to this LabResult."""
        with self._driver.session() as session:
            session.execute_write(txs._link_specimen_lab_result, specimen_id, lab_id)


class HIVViralLoadRepository(BaseRepository):
    """CRUD for HIVViralLoad nodes."""

    def create(self, vl: HIVViralLoad) -> str:
        """Create a HIVViralLoad node (idempotent) and return its viral_load_id."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_hiv_viral_load,
                vl.viral_load_id,
                vl.test_date.isoformat() if vl.test_date else None,
                vl.value_copies_per_ml,
                vl.log10_value,
                vl.detection_limit,
                vl.assay_type,
                vl.result_status,
            )

    def get(self, viral_load_id: str) -> HIVViralLoad | None:
        """Return a HIVViralLoad by viral_load_id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_hiv_viral_load, viral_load_id)
        if raw is None:
            return None
        def _to_native(val):
            return val.to_native() if hasattr(val, "to_native") else val

        return HIVViralLoad.model_validate({
            "viral_load_id": raw.get("viral_load_id"),
            "test_date": _to_native(raw.get("test_date")),
            "value_copies_per_ml": raw.get("value_copies_per_ml"),
            "log10_value": raw.get("log10_value"),
            "detection_limit": raw.get("detection_limit"),
            "assay_type": raw.get("assay_type"),
            "result_status": raw.get("result_status"),
        })

    def delete(self, viral_load_id: str) -> None:
        """Delete a HIVViralLoad node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_hiv_viral_load, viral_load_id)

    def link_patient(self, viral_load_id: str, patient_id: str) -> None:
        """Create a HAS_HIV_VIRAL_LOAD_RESULT relationship from an existing Patient node to this HIVViralLoad."""
        with self._driver.session() as session:
            session.execute_write(txs._link_patient_hiv_viral_load, patient_id, viral_load_id)
