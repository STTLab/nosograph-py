from nosograph.repositories._base import BaseRepository
from nosograph.models.genomics import Organism, ReferenceGenome, Assembly, Contig
from nosograph.types import NodeCreateOrMatchStats, NodeAndRelationshipCreationStats, ContigProps
import nosograph._txs as txs


class OrganismRepository(BaseRepository):

    def create(self, organism: Organism) -> str:
        with self._driver.session() as session:
            return session.execute_write(txs._create_organism, organism.taxid, organism.sciname)

    def get(self, taxid: str) -> Organism | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_organism, taxid)
        if raw is None:
            return None
        return Organism.model_validate({"taxid": raw.get("taxid"), "sciname": raw.get("sciname")})

    def delete(self, taxid: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_organism, taxid)

    def link_reference_genome(self, taxid: str, accession_no: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._link_organism_reference_genome, taxid, accession_no)


class AssemblyRepository(BaseRepository):

    def create(self, assembly: Assembly) -> NodeCreateOrMatchStats:
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_assembly_run,
                assembly_id=assembly.assembly_id,
                assembler=assembly.assembler or "",
                created_at=assembly.created_at,
            )

    def get(self, assembly_id: str) -> Assembly | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_assembly, assembly_id)
        if raw is None:
            return None
        created_at = raw.get("created_at")
        return Assembly.model_validate({
            "assembly_id": raw.get("assembly_id"),
            "assembler": raw.get("assembler"),
            "created_at": created_at.to_native() if hasattr(created_at, "to_native") else created_at,
        })

    def delete(self, assembly_id: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_assembly, assembly_id)

    def add_contigs(self, assembly_id: str, contigs: list[Contig]) -> NodeAndRelationshipCreationStats:
        contig_dicts: list[ContigProps] = [
            {
                "contig_id": c.contig_id,
                "length": c.length,
                "sequence": c.sequence,
                "hash_algorithm": c.hash_algorithm,
                "sequence_hash": c.sequence_hash,
            }
            for c in contigs
        ]
        with self._driver.session() as session:
            return session.execute_write(txs._associate_contigs, assembly_id, contig_dicts)


class ReferenceGenomeRepository(BaseRepository):

    def create(self, ref_genome: ReferenceGenome) -> str:
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_reference_genome,
                accession_no=ref_genome.accession_no,
                name=ref_genome.name,
                molecular_type=ref_genome.molecular_type,
                strain=ref_genome.strain,
                annotation_source=ref_genome.annotation_source,
                source_database=ref_genome.source_database,
            )

    def get(self, accession_no: str) -> ReferenceGenome | None:
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_reference_genome, accession_no)
        if raw is None:
            return None
        return ReferenceGenome.model_validate({
            "accession_no": raw.get("accession_no"),
            "name": raw.get("name"),
            "molecular_type": raw.get("molecular_type"),
            "strain": raw.get("strain"),
            "annotation_source": raw.get("annotation_source"),
            "source_database": raw.get("source_database"),
        })

    def delete(self, accession_no: str) -> None:
        with self._driver.session() as session:
            session.execute_write(txs._delete_reference_genome, accession_no)
