import pytest
import docker
from testcontainers.neo4j import Neo4jContainer
from nosograph import NosoGraph


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


skip_no_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker daemon not available — skipping integration tests",
)


@pytest.fixture(scope="session")
def neo4j_container():
    if not _docker_available():
        pytest.skip("Docker not available")
    with Neo4jContainer("neo4j:5-community") as container:
        yield container


@pytest.fixture(scope="session")
def graph(neo4j_container):
    with NosoGraph(neo4j_container.get_connection_url()) as g:
        yield g


@pytest.fixture(autouse=True)
def clean_db(graph):
    yield
    with graph.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
