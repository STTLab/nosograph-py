import logging
from neo4j import GraphDatabase, Driver
from nosograph.types import Neo4JAuth, AssemblyProps, ContigProps, NodeCreateOrMatchStats, NodeAndRelationshipCreationStats
from nosograph.repositories.patient import PatientRepository
from nosograph.repositories.admission import AdmissionRepository
from nosograph.repositories.specimen import SpecimenRepository, SampleRepository
from nosograph.repositories.genomics import OrganismRepository, AssemblyRepository, ReferenceGenomeRepository
from nosograph.repositories.clinical import WardRepository, DepartmentRepository, LabResultRepository, HIVViralLoadRepository, OpdVisitRepository
import nosograph._txs as _txs


class NosoGraph(GraphDatabase):
    def __init__(self, database_uri: str, auth: Neo4JAuth | None = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing NosoGraph")
        self._driver = super().driver(uri=database_uri, auth=None if not auth else auth)
        self._patients = PatientRepository(self._driver)
        self._admissions = AdmissionRepository(self._driver)
        self._specimens = SpecimenRepository(self._driver)
        self._samples = SampleRepository(self._driver)
        self._organisms = OrganismRepository(self._driver)
        self._assemblies = AssemblyRepository(self._driver)
        self._reference_genomes = ReferenceGenomeRepository(self._driver)
        self._wards = WardRepository(self._driver)
        self._departments = DepartmentRepository(self._driver)
        self._lab_results = LabResultRepository(self._driver)
        self._hiv_viral_loads = HIVViralLoadRepository(self._driver)
        self._opd_visits = OpdVisitRepository(self._driver)

    def __enter__(self) -> "NosoGraph":
        self.verify()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def driver(self) -> Driver:
        return self._driver

    @property
    def patients(self) -> PatientRepository:
        return self._patients

    @property
    def admissions(self) -> AdmissionRepository:
        return self._admissions

    @property
    def specimens(self) -> SpecimenRepository:
        return self._specimens

    @property
    def samples(self) -> SampleRepository:
        return self._samples

    @property
    def organisms(self) -> OrganismRepository:
        return self._organisms

    @property
    def assemblies(self) -> AssemblyRepository:
        return self._assemblies

    @property
    def reference_genomes(self) -> ReferenceGenomeRepository:
        return self._reference_genomes

    @property
    def wards(self) -> WardRepository:
        return self._wards

    @property
    def departments(self) -> DepartmentRepository:
        return self._departments

    @property
    def lab_results(self) -> LabResultRepository:
        return self._lab_results

    @property
    def hiv_viral_loads(self) -> HIVViralLoadRepository:
        return self._hiv_viral_loads

    @property
    def opd_visits(self) -> OpdVisitRepository:
        return self._opd_visits

    def verify(self) -> None:
        try:
            self._logger.info("Verifying database connectivity...")
            self._driver.verify_connectivity()
            self._logger.info("Connection successful")
        except BaseException as e:
            self._logger.error(e)

    def close(self) -> None:
        self._logger.info("Closing driver")
        self._driver.close()

    # ------------------------------------------------------------------
    # Back-compat methods (delegate to repositories)
    # ------------------------------------------------------------------

    def add_assembly(self, **assembly_data: AssemblyProps) -> NodeCreateOrMatchStats:
        from nosograph.models.genomics import Assembly
        assembly = Assembly(
            assembly_id=assembly_data.get("assembly_id"),
            assembler=assembly_data.get("assembler"),
            created_at=assembly_data.get("created_at"),
        )
        stats = self._assemblies.create(assembly)
        self._logger.info(stats)
        return stats

    def add_contigs(self, assembly_id: str, contigs: list[ContigProps]) -> NodeAndRelationshipCreationStats:
        from nosograph.models.genomics import Contig
        contig_models = [Contig(**c) for c in contigs]
        stats = self._assemblies.add_contigs(assembly_id, contig_models)
        self._logger.info(stats)
        return stats
