from unittest.mock import patch
import pytest
from nosograph.models.specimen import Sample


@pytest.fixture
def cli():
    """A NosoGraphCLI whose Neo4j connection is fully mocked (no real DB)."""
    with patch("nosograph.cli.NosoGraph") as MockGraph:
        from nosograph.cli import NosoGraphCLI
        c = NosoGraphCLI()
    # c.neo4j_conn is MockGraph(...) -> a MagicMock; repos are auto-mocked attrs.
    return c


class TestCreateSample:
    def test_creates_new_sample(self, cli):
        cli.neo4j_conn.samples.get.return_value = None
        with patch("builtins.input", return_value="SAM_NEW"):
            cli.create_sample()
        cli.neo4j_conn.samples.create.assert_called_once_with(Sample(sample_id="SAM_NEW"))

    def test_rejects_duplicate(self, cli):
        cli.neo4j_conn.samples.get.return_value = Sample(sample_id="SAM_DUP")
        with patch("builtins.input", return_value="SAM_DUP"):
            with pytest.raises(ValueError, match="already exists"):
                cli.create_sample()
        cli.neo4j_conn.samples.create.assert_not_called()

    def test_rejects_empty_id(self, cli):
        with patch("builtins.input", return_value="   "):
            with pytest.raises(ValueError, match="cannot be empty"):
                cli.create_sample()
        cli.neo4j_conn.samples.create.assert_not_called()


class TestGetSample:
    def test_delegates_to_repository(self, cli):
        cli.neo4j_conn.samples.get.return_value = Sample(sample_id="S1")
        result = cli.get_sample("S1")
        assert result == Sample(sample_id="S1")
        cli.neo4j_conn.samples.get.assert_called_once_with("S1")


class TestPrintSampleInfo:
    def test_none_prints_not_found(self, cli, capsys):
        with patch("nosograph.cli.sleep"):
            cli.print_sample_info(None)
        assert "Not found" in capsys.readouterr().out
        cli.neo4j_conn.variants.get_by_sample.assert_not_called()

    def test_prints_id_and_variant_count(self, cli, capsys):
        cli.neo4j_conn.variants.get_by_sample.return_value = [("v1", {}), ("v2", {})]
        with patch("nosograph.cli.sleep"):
            cli.print_sample_info(Sample(sample_id="S2"))
        out = capsys.readouterr().out
        assert "Sample ID: S2" in out
        assert "Linked variants: 2" in out
