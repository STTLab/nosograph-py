from unittest.mock import MagicMock, patch, call
import pytest
from nosograph.db import NosoGraph
from nosograph.types import Neo4JAuth
from nosograph.repositories.patient import PatientRepository
from nosograph.repositories.admission import AdmissionRepository
from nosograph.repositories.specimen import SpecimenRepository, SampleRepository
from nosograph.repositories.genomics import (
    OrganismRepository,
    AssemblyRepository,
    ReferenceGenomeRepository,
)
from nosograph.repositories.clinical import (
    WardRepository,
    DepartmentRepository,
    LabResultRepository,
    HIVViralLoadRepository,
    OpdVisitRepository,
)


URI = "bolt://localhost:7687"


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def graph(mock_driver):
    with patch("neo4j.GraphDatabase.driver", return_value=mock_driver):
        g = NosoGraph(URI)
    return g


@pytest.fixture
def graph_with_auth(mock_driver):
    auth = Neo4JAuth(user="neo4j", password="secret")
    with patch("neo4j.GraphDatabase.driver", return_value=mock_driver) as mock_gdb_driver:
        g = NosoGraph(URI, auth=auth)
    return g, mock_driver, mock_gdb_driver


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestNosoGraphInit:
    def test_driver_created_with_uri(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver) as mock_gdb:
            NosoGraph(URI)
        mock_gdb.assert_called_once_with(uri=URI, auth=None)

    def test_driver_created_with_auth(self, mock_driver):
        auth = Neo4JAuth(user="neo4j", password="pw")
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver) as mock_gdb:
            NosoGraph(URI, auth=auth)
        mock_gdb.assert_called_once_with(uri=URI, auth=auth)

    def test_no_auth_passes_none_to_driver(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver) as mock_gdb:
            NosoGraph(URI, auth=None)
        _, kwargs = mock_gdb.call_args
        assert kwargs["auth"] is None


# ---------------------------------------------------------------------------
# Repository properties
# ---------------------------------------------------------------------------

class TestRepositoryProperties:
    def test_patients_property(self, graph):
        assert isinstance(graph.patients, PatientRepository)

    def test_admissions_property(self, graph):
        assert isinstance(graph.admissions, AdmissionRepository)

    def test_specimens_property(self, graph):
        assert isinstance(graph.specimens, SpecimenRepository)

    def test_samples_property(self, graph):
        assert isinstance(graph.samples, SampleRepository)

    def test_organisms_property(self, graph):
        assert isinstance(graph.organisms, OrganismRepository)

    def test_assemblies_property(self, graph):
        assert isinstance(graph.assemblies, AssemblyRepository)

    def test_reference_genomes_property(self, graph):
        assert isinstance(graph.reference_genomes, ReferenceGenomeRepository)

    def test_wards_property(self, graph):
        assert isinstance(graph.wards, WardRepository)

    def test_departments_property(self, graph):
        assert isinstance(graph.departments, DepartmentRepository)

    def test_lab_results_property(self, graph):
        assert isinstance(graph.lab_results, LabResultRepository)

    def test_hiv_viral_loads_property(self, graph):
        assert isinstance(graph.hiv_viral_loads, HIVViralLoadRepository)

    def test_opd_visits_property(self, graph):
        assert isinstance(graph.opd_visits, OpdVisitRepository)

    def test_driver_property(self, graph, mock_driver):
        assert graph.driver is mock_driver


# ---------------------------------------------------------------------------
# verify / close
# ---------------------------------------------------------------------------

class TestVerifyAndClose:
    def test_verify_calls_driver_verify_connectivity(self, graph, mock_driver):
        graph.verify()
        mock_driver.verify_connectivity.assert_called_once()

    def test_close_calls_driver_close(self, graph, mock_driver):
        graph.close()
        mock_driver.close.assert_called_once()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class TestContextManager:
    def test_enter_returns_self(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver):
            g = NosoGraph(URI)
        result = g.__enter__()
        assert result is g

    def test_enter_calls_verify(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver):
            g = NosoGraph(URI)
        g.__enter__()
        mock_driver.verify_connectivity.assert_called_once()

    def test_exit_calls_close(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver):
            g = NosoGraph(URI)
        g.__exit__(None, None, None)
        mock_driver.close.assert_called_once()

    def test_context_manager_protocol(self, mock_driver):
        with patch("neo4j.GraphDatabase.driver", return_value=mock_driver):
            with NosoGraph(URI) as g:
                assert isinstance(g, NosoGraph)
        mock_driver.close.assert_called_once()


# ---------------------------------------------------------------------------
# Back-compat methods
# ---------------------------------------------------------------------------

class TestAddAssembly:
    def test_delegates_to_assemblies_create(self, graph):
        expected: dict = {"nodes_matched": 0, "nodes_created": 1}
        graph._assemblies = MagicMock()
        graph._assemblies.create.return_value = expected

        result = graph.add_assembly(
            assembly_id="ASM001", assembler="Flye", created_at="2025-01-01"
        )

        graph._assemblies.create.assert_called_once()
        assert result == expected

    def test_passes_correct_assembly_model(self, graph):
        from nosograph.models.genomics import Assembly

        graph._assemblies = MagicMock()
        graph._assemblies.create.return_value = {"nodes_matched": 0, "nodes_created": 1}

        graph.add_assembly(assembly_id="ASM002", assembler="Canu", created_at="2025-06-01")

        passed_assembly = graph._assemblies.create.call_args[0][0]
        assert isinstance(passed_assembly, Assembly)
        assert passed_assembly.assembly_id == "ASM002"
        assert passed_assembly.assembler == "Canu"

    def test_returns_stats(self, graph):
        graph._assemblies = MagicMock()
        graph._assemblies.create.return_value = {"nodes_matched": 1, "nodes_created": 0}

        result = graph.add_assembly(assembly_id="ASM003")

        assert result["nodes_matched"] == 1
        assert result["nodes_created"] == 0


class TestAddContigs:
    def test_delegates_to_assemblies_add_contigs(self, graph):
        expected: dict = {"nodes_created": 2, "relationships_created": 2}
        graph._assemblies = MagicMock()
        graph._assemblies.add_contigs.return_value = expected

        contigs = [
            {
                "contig_id": "c1",
                "length": 500,
                "sequence": "ATCG",
                "hash_algorithm": "md5",
                "sequence_hash": "abc",
            }
        ]
        result = graph.add_contigs("ASM001", contigs)

        graph._assemblies.add_contigs.assert_called_once()
        assert result == expected

    def test_passes_contig_models(self, graph):
        from nosograph.models.genomics import Contig

        graph._assemblies = MagicMock()
        graph._assemblies.add_contigs.return_value = {"nodes_created": 1, "relationships_created": 1}

        contigs = [
            {
                "contig_id": "c1",
                "length": 100,
                "sequence": "AAAA",
                "hash_algorithm": "md5",
                "sequence_hash": "xyz",
            }
        ]
        graph.add_contigs("ASM001", contigs)

        assembly_id_arg, contig_list_arg = graph._assemblies.add_contigs.call_args[0]
        assert assembly_id_arg == "ASM001"
        assert len(contig_list_arg) == 1
        assert isinstance(contig_list_arg[0], Contig)
        assert contig_list_arg[0].contig_id == "c1"

    def test_multiple_contigs(self, graph):
        graph._assemblies = MagicMock()
        graph._assemblies.add_contigs.return_value = {"nodes_created": 3, "relationships_created": 3}

        contigs = [
            {"contig_id": f"c{i}", "length": i * 100, "sequence": "ATCG",
             "hash_algorithm": "md5", "sequence_hash": f"h{i}"}
            for i in range(1, 4)
        ]
        result = graph.add_contigs("ASM001", contigs)

        _, contig_list_arg = graph._assemblies.add_contigs.call_args[0]
        assert len(contig_list_arg) == 3
        assert result["nodes_created"] == 3
