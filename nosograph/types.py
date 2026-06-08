from typing import Literal, TypedDict, NamedTuple


class Neo4JAuth(NamedTuple):
    user: Literal['neo4j']
    password: str

    @classmethod
    def from_string(cls, value: str | None) -> "Neo4JAuth | None":
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        try:
            user, password = value.split("/", 1)
        except ValueError:
            raise ValueError("Auth string must be in format 'neo4j/password'")
        if user != "neo4j":
            raise ValueError("Neo4j username must be 'neo4j'")
        return cls(user="neo4j", password=password)


class AssemblyProps(TypedDict):
    assembly_id: str
    assembler: str
    created_at: str


class ContigProps(TypedDict):
    contig_id: str
    length: int
    sequence: str
    hash_algorithm: str
    sequence_hash: str


class NodeCreateOrMatchStats(TypedDict):
    nodes_matched: int
    nodes_created: int


class NodeAndRelationshipCreationStats(TypedDict):
    nodes_created: int
    relationships_created: int


class VariantCallProps(TypedDict, total=False):
    DP: int | None
    GT: str | None
    QUAL: float | None
    GQ: int | None
    AO: int | None
    RO: int | None
    FILTER: str | None
    vcf_source: str | None
