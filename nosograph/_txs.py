from importlib.resources import files
from datetime import datetime, UTC
from neo4j import ManagedTransaction
from nosograph.types import (
    AssemblyProps,
    ContigProps,
    NodeCreateOrMatchStats,
    NodeAndRelationshipCreationStats,
)


def _load_cypher() -> dict[str, str]:
    cypher_pkg = files("nosograph.cypher")
    result = {}
    for resource in cypher_pkg.iterdir():
        if resource.name.endswith(".cypher"):
            key = resource.name.removesuffix(".cypher")
            result[key] = resource.read_text(encoding="utf-8")
    return result


CYPHERS: dict[str, str] = _load_cypher()


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

def _get_patient_by_id(tx: ManagedTransaction, patient_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Patient"], patient_id=patient_id).single()
    return dict(record["p"]) if record else None


def _create_patient_tx(
    tx: ManagedTransaction,
    patient_id: str,
    firstname: str,
    lastname: str,
    sex: str | None,
    dob: str | None,
    age: int | None,
) -> str:
    result = tx.run(
        CYPHERS["CREATE_Patient"],
        patient_id=patient_id,
        firstname=firstname,
        lastname=lastname,
        sex=sex,
        dob=dob,
        age=age,
    )
    return result.single()["id"]


def _delete_patient(tx: ManagedTransaction, patient_id: str) -> None:
    tx.run(CYPHERS["DELETE_Patient"], patient_id=patient_id)


# ---------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------

def _create_admission(
    tx: ManagedTransaction,
    admission_id: str,
    date_of_admission: str | None,
    date_of_discharge: str | None,
) -> str:
    tx.run(
        CYPHERS["CREATE_Admission"],
        admission_id=admission_id,
        date_of_admission=date_of_admission,
        date_of_discharge=date_of_discharge,
    )
    return admission_id


def _get_admission(tx: ManagedTransaction, admission_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Admission"], admission_id=admission_id).single()
    return dict(record["a"]) if record else None


def _delete_admission(tx: ManagedTransaction, admission_id: str) -> None:
    tx.run(CYPHERS["DELETE_Admission"], admission_id=admission_id)


def _link_patient_admission(tx: ManagedTransaction, patient_id: str, admission_id: str) -> None:
    tx.run(CYPHERS["ASSOCIATE_Patient_HAS_Admission"], patient_id=patient_id, admission_id=admission_id)


def _link_admission_ward(
    tx: ManagedTransaction,
    admission_id: str,
    ward_id: str,
    room_no: str | None,
    bed_no: str | None,
) -> None:
    tx.run(
        CYPHERS["ASSOCIATE_Admisson_TO_Ward"],
        admission_id=admission_id,
        ward_id=ward_id,
        room_no=room_no,
        bed_no=bed_no,
    )


# ---------------------------------------------------------------------------
# Specimen
# ---------------------------------------------------------------------------

def _create_specimen(tx: ManagedTransaction, specimen_id: str, specimen_type: str | None) -> str:
    tx.run(CYPHERS["CREATE_Specimen"], specimen_id=specimen_id)
    if specimen_type is not None:
        tx.run(
            "MATCH (s:Specimen {specimen_id: $specimen_id}) SET s.specimen_type = $specimen_type",
            specimen_id=specimen_id,
            specimen_type=specimen_type,
        )
    return specimen_id


def _get_specimen(tx: ManagedTransaction, specimen_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Specimen"], specimen_id=specimen_id).single()
    return dict(record["s"]) if record else None


def _delete_specimen(tx: ManagedTransaction, specimen_id: str) -> None:
    tx.run(CYPHERS["DELETE_Specimen"], specimen_id=specimen_id)


def _link_specimen_patient(tx: ManagedTransaction, specimen_id: str, patient_id: str) -> None:
    tx.run(
        CYPHERS["ASSOCIATE_Specimen_COLLECTED_FROM_Patient"],
        specimen_id=specimen_id,
        patient_id=patient_id,
    )


# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------

def _create_sample(tx: ManagedTransaction, sample_id: str) -> str:
    tx.run(CYPHERS["CREATE_Sample"], sample_id=sample_id)
    return sample_id


def _get_sample(tx: ManagedTransaction, sample_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Sample"], sample_id=sample_id).single()
    return dict(record["s"]) if record else None


def _delete_sample(tx: ManagedTransaction, sample_id: str) -> None:
    tx.run(CYPHERS["DELETE_Sample"], sample_id=sample_id)


def _link_sample_assembly(tx: ManagedTransaction, sample_id: str, assembly_id: str) -> None:
    tx.run(CYPHERS["ASSOCIATE_Sample_HAS_Assembly"], sample_id=sample_id, assembly_id=assembly_id)


# ---------------------------------------------------------------------------
# Organism
# ---------------------------------------------------------------------------

def _create_organism(tx: ManagedTransaction, taxid: str, sciname: str | None) -> str:
    tx.run(CYPHERS["CREATE_Organism"], taxid=taxid, sciname=sciname)
    return taxid


def _get_organism(tx: ManagedTransaction, taxid: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Organism"], taxid=taxid).single()
    return dict(record["o"]) if record else None


def _delete_organism(tx: ManagedTransaction, taxid: str) -> None:
    tx.run(CYPHERS["DELETE_Organism"], taxid=taxid)


def _link_organism_reference_genome(tx: ManagedTransaction, taxid: str, accession_no: str) -> None:
    tx.run(
        CYPHERS["ASSOCIATE_ReferenceGenome_OF_A_Organism"],
        taxid=taxid,
        accession_no=accession_no,
    )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def _create_assembly_run(
    tx: ManagedTransaction,
    assembly_id: str,
    assembler: str,
    created_at: datetime | None = None,
) -> NodeCreateOrMatchStats:
    result = tx.run(
        CYPHERS["CREATE_AssemblyRun"],
        assembly_id=assembly_id,
        assembler=assembler,
        created_at=created_at or datetime.now(UTC),
    )
    record = result.single()
    return {
        "nodes_created": record["nodes_created"],
        "nodes_matched": record["nodes_matched"],
    }


def _get_assembly(tx: ManagedTransaction, assembly_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Assembly"], assembly_id=assembly_id).single()
    return dict(record["a"]) if record else None


def _delete_assembly(tx: ManagedTransaction, assembly_id: str) -> None:
    tx.run(CYPHERS["DELETE_AssemblyRun_cascade"], assembly_id=assembly_id)


def _associate_contigs(
    tx: ManagedTransaction,
    assembly_id: str,
    contigs: list[ContigProps],
) -> NodeAndRelationshipCreationStats:
    assembly_exists = tx.run(
        "MATCH (a:Assembly {assembly_id: $assembly_id}) RETURN a LIMIT 1",
        assembly_id=assembly_id,
    ).single()
    if assembly_exists is None:
        raise ValueError(f"Assembly '{assembly_id}' was not found.")
    result = tx.run(CYPHERS["ASSOCIATE_Contig_AssemblyRun"], assembly_id=assembly_id, contigs=contigs)
    summary = result.consume()
    return {
        "nodes_created": summary.counters.nodes_created,
        "relationships_created": summary.counters.relationships_created,
    }


# ---------------------------------------------------------------------------
# ReferenceGenome
# ---------------------------------------------------------------------------

def _create_reference_genome(
    tx: ManagedTransaction,
    accession_no: str,
    name: str | None,
    molecular_type: str | None,
    strain: str | None,
    annotation_source: str | None,
    source_database: str | None,
) -> str:
    tx.run(
        CYPHERS["CREATE_ReferenceGenome"],
        accession_no=accession_no,
        name=name,
        molecular_type=molecular_type,
        strain=strain,
        annotation_source=annotation_source,
        source_database=source_database,
    )
    return accession_no


def _get_reference_genome(tx: ManagedTransaction, accession_no: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_ReferenceGenome"], accession_no=accession_no).single()
    return dict(record["refg"]) if record else None


def _delete_reference_genome(tx: ManagedTransaction, accession_no: str) -> None:
    tx.run(CYPHERS["DELETE_ReferenceGenome"], accession_no=accession_no)


# ---------------------------------------------------------------------------
# Ward
# ---------------------------------------------------------------------------

def _create_ward(
    tx: ManagedTransaction,
    ward_id: str,
    name: str,
    department_id: str,
    ward_type: str | None,
    description: str | None,
) -> str:
    tx.run(
        CYPHERS["CREATE_Ward"],
        ward_id=ward_id,
        name=name,
        department_id=department_id,
        ward_type=ward_type,
        description=description,
    )
    return ward_id


def _get_ward(tx: ManagedTransaction, ward_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Ward"], ward_id=ward_id).single()
    return dict(record["w"]) if record else None


def _link_ward_department(tx: ManagedTransaction, ward_id: str, department_id: str) -> None:
    tx.run(CYPHERS["ASSOCIATE_Ward_IN_Department"], ward_id=ward_id, department_id=department_id)


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------

def _create_department(
    tx: ManagedTransaction,
    department_id: str,
    name: str,
    description: str | None,
) -> str:
    tx.run(
        CYPHERS["CREATE_Department"],
        department_id=department_id,
        name=name,
        description=description,
    )
    return department_id


def _get_department(tx: ManagedTransaction, department_id: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Department"], department_id=department_id).single()
    return dict(record["d"]) if record else None


# ---------------------------------------------------------------------------
# Variant
# ---------------------------------------------------------------------------

def _create_variant(tx: ManagedTransaction, **kwargs) -> str:
    tx.run(CYPHERS["CREATE_Variant"], **kwargs)
    return kwargs["variant_key"]


def _get_variant(tx: ManagedTransaction, variant_key: str) -> dict | None:
    record = tx.run(CYPHERS["MATCH_Variant"], variant_key=variant_key).single()
    return dict(record["v"]) if record else None
