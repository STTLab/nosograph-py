import pytest

# Shared Neo4j container/graph fixtures live in tests/conftest.py.


@pytest.fixture(autouse=True)
def clean_db(graph):
    yield
    with graph.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
