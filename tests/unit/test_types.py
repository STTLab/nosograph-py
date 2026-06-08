import pytest
from nosograph.types import (
    Neo4JAuth,
    AssemblyProps,
    ContigProps,
    NodeCreateOrMatchStats,
    NodeAndRelationshipCreationStats,
    VariantCallProps,
)


class TestNeo4JAuthFromString:
    def test_none_returns_none(self):
        assert Neo4JAuth.from_string(None) is None

    def test_empty_string_returns_none(self):
        assert Neo4JAuth.from_string("") is None

    def test_whitespace_only_returns_none(self):
        assert Neo4JAuth.from_string("   ") is None

    def test_valid_credentials(self):
        auth = Neo4JAuth.from_string("neo4j/secret")
        assert auth == Neo4JAuth(user="neo4j", password="secret")

    def test_password_containing_slashes(self):
        auth = Neo4JAuth.from_string("neo4j/pass/word/extra")
        assert auth.password == "pass/word/extra"

    def test_leading_and_trailing_whitespace_stripped(self):
        auth = Neo4JAuth.from_string("  neo4j/secret  ")
        assert auth is not None
        assert auth.user == "neo4j"

    def test_wrong_username_raises(self):
        with pytest.raises(ValueError, match="username must be 'neo4j'"):
            Neo4JAuth.from_string("admin/password")

    def test_no_slash_raises(self):
        with pytest.raises(ValueError, match="neo4j/password"):
            Neo4JAuth.from_string("neo4jpassword")


class TestNeo4JAuthNamedTuple:
    def test_fields_accessible_by_name(self):
        auth = Neo4JAuth(user="neo4j", password="pw")
        assert auth.user == "neo4j"
        assert auth.password == "pw"

    def test_unpackable(self):
        user, password = Neo4JAuth(user="neo4j", password="pw")
        assert user == "neo4j"
        assert password == "pw"

    def test_indexable(self):
        auth = Neo4JAuth(user="neo4j", password="pw")
        assert auth[0] == "neo4j"
        assert auth[1] == "pw"

    def test_equality(self):
        a = Neo4JAuth(user="neo4j", password="same")
        b = Neo4JAuth(user="neo4j", password="same")
        assert a == b

    def test_inequality(self):
        a = Neo4JAuth(user="neo4j", password="one")
        b = Neo4JAuth(user="neo4j", password="two")
        assert a != b


class TestTypedDicts:
    def test_assembly_props(self):
        props: AssemblyProps = {
            "assembly_id": "ASM001",
            "assembler": "Flye",
            "created_at": "2025-01-01",
        }
        assert props["assembly_id"] == "ASM001"
        assert props["assembler"] == "Flye"

    def test_contig_props(self):
        props: ContigProps = {
            "contig_id": "c1",
            "length": 500,
            "sequence": "ATCG",
            "hash_algorithm": "md5",
            "sequence_hash": "abc123",
        }
        assert props["length"] == 500
        assert props["hash_algorithm"] == "md5"

    def test_node_create_or_match_stats(self):
        stats: NodeCreateOrMatchStats = {"nodes_matched": 1, "nodes_created": 0}
        assert stats["nodes_matched"] == 1
        assert stats["nodes_created"] == 0

    def test_node_and_relationship_creation_stats(self):
        stats: NodeAndRelationshipCreationStats = {
            "nodes_created": 3,
            "relationships_created": 2,
        }
        assert stats["nodes_created"] == 3
        assert stats["relationships_created"] == 2


class TestVariantCallProps:
    def test_medaka_call(self):
        call: VariantCallProps = {"DP": 20, "GT": "1", "QUAL": 35.5, "GQ": 36, "vcf_source": "medaka"}
        assert call["GQ"] == 36
        assert call.get("AO") is None

    def test_snippy_call(self):
        call: VariantCallProps = {"DP": 20, "GT": "1/1", "QUAL": 682.6, "AO": 20, "RO": 0, "vcf_source": "snippy"}
        assert call["AO"] == 20
        assert call.get("GQ") is None

    def test_partial_call_allowed(self):
        call: VariantCallProps = {"GT": "1"}
        assert call["GT"] == "1"
