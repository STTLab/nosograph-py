from nosograph.repositories._base import BaseRepository
from nosograph.models.patient import Ward, Department
import nosograph._txs as txs


class WardRepository(BaseRepository):

    def create(self, ward: Ward) -> str:
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
        with self._driver.session() as session:
            session.execute_write(txs._link_ward_department, ward_id, department_id)


class DepartmentRepository(BaseRepository):

    def create(self, dept: Department) -> str:
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_department,
                department_id=dept.department_id,
                name=dept.name,
                description=dept.description,
            )

    def get(self, department_id: str) -> Department | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_department, department_id)
        if raw is None:
            return None
        return Department.model_validate({
            "department_id": raw.get("department_id"),
            "name": raw.get("name"),
            "description": raw.get("description"),
        })
