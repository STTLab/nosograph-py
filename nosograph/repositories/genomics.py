from __future__ import annotations
from typing import Literal
from nosograph.repositories._base import BaseRepository
from nosograph.models.genomics import Organism, ReferenceGenome, Assembly, Contig, Variant
from nosograph.types import NodeCreateOrMatchStats, NodeAndRelationshipCreationStats, ContigProps, VariantCallProps
import nosograph._txs as txs


class OrganismRepository(BaseRepository):
    """CRUD for Organism nodes."""

    def create(self, organism: Organism) -> str:
        """Create an Organism node (idempotent) and return its taxid."""
        with self._driver.session() as session:
            return session.execute_write(txs._create_organism, organism.taxid, organism.sciname)

    def get(self, taxid: str) -> Organism | None:
        """Return an Organism by NCBI taxid, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_organism, taxid)
        if raw is None:
            return None
        return Organism.model_validate({"taxid": raw.get("taxid"), "sciname": raw.get("sciname")})

    def delete(self, taxid: str) -> None:
        """Delete an Organism node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_organism, taxid)

    def link_reference_genome(self, taxid: str, accession_no: str) -> None:
        """Create a REFERENCE_GENOME_OF relationship from ReferenceGenome to an existing Organism node."""
        with self._driver.session() as session:
            session.execute_write(txs._link_organism_reference_genome, taxid, accession_no)


class AssemblyRepository(BaseRepository):
    """CRUD for Assembly nodes."""

    def create(self, assembly: Assembly) -> NodeCreateOrMatchStats:
        """Create or match an Assembly node; returns node creation/match stats."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_assembly_run,
                assembly_id=assembly.assembly_id,
                assembler=assembly.assembler or "",
                created_at=assembly.created_at,
            )

    def get(self, assembly_id: str) -> Assembly | None:
        """Return an Assembly by assembly_id, or None if not found."""
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
        """Delete an Assembly node and all its relationships, including linked Contig nodes."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_assembly, assembly_id)

    def add_contigs(self, assembly_id: str, contigs: list[Contig]) -> NodeAndRelationshipCreationStats:
        """Bulk-create Contig nodes and link them to an Assembly via HAS_CONTIG. Raises ValueError if assembly not found."""
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
    """CRUD for ReferenceGenome nodes."""

    def create(self, ref_genome: ReferenceGenome) -> str:
        """Create a ReferenceGenome node (idempotent) and return its accession_no."""
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
        """Return a ReferenceGenome by NCBI accession number, or None if not found."""
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
        """Delete a ReferenceGenome node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_reference_genome, accession_no)


class VariantRepository(BaseRepository):
    """CRUD and bulk import for Variant nodes.

    Each Variant node represents a single gene-level annotation of a genomic
    variant. The identity key is (REF_ACC, POS, REF, ALT, hgvs_c, hgvs_p),
    so one VCF record can produce multiple Variant nodes when multiple gene
    annotations are present (e.g. HIV overlapping ORFs).

    Call-quality metadata (DP, GT, QUAL, GQ, AO, RO, FILTER, vcf_source) is
    stored on the HAS_VARIANT relationship between Sample and Variant.
    """

    def create(self, variant: Variant) -> None:
        """Create or match a Variant node (idempotent)."""
        with self._driver.session() as session:
            session.execute_write(
                txs._create_variant,
                REF_ACC=variant.REF_ACC,
                POS=variant.POS,
                REF=variant.REF,
                ALT=variant.ALT,
                hgvs_c=variant.hgvs_c,
                hgvs_p=variant.hgvs_p,
                CHROM=variant.CHROM,
                TYPE=variant.TYPE,
                EFFECT=variant.EFFECT,
                IMPACT=variant.IMPACT,
                gene_name=variant.gene_name,
            )

    def get(
        self,
        ref_acc: str,
        pos: int,
        ref: str,
        alt: str,
        hgvs_c: str = "",
        hgvs_p: str = "",
    ) -> Variant | None:
        """Return a Variant by its 6-property identity, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_variant, REF_ACC=ref_acc, POS=pos, REF=ref, ALT=alt, hgvs_c=hgvs_c, hgvs_p=hgvs_p)
        if raw is None:
            return None
        return Variant.model_validate({
            "REF_ACC": raw.get("REF_ACC"),
            "POS": raw.get("POS"),
            "REF": raw.get("REF"),
            "ALT": raw.get("ALT"),
            "CHROM": raw.get("CHROM"),
            "TYPE": raw.get("TYPE"),
            "EFFECT": raw.get("EFFECT"),
            "IMPACT": raw.get("IMPACT"),
            "hgvs_c": raw.get("hgvs_c", ""),
            "hgvs_p": raw.get("hgvs_p", ""),
            "gene_name": raw.get("gene_name"),
        })

    def delete(
        self,
        ref_acc: str,
        pos: int,
        ref: str,
        alt: str,
        hgvs_c: str = "",
        hgvs_p: str = "",
    ) -> None:
        """Delete a Variant node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_variant, REF_ACC=ref_acc, POS=pos, REF=ref, ALT=alt, hgvs_c=hgvs_c, hgvs_p=hgvs_p)

    def link_sample(self, variant: Variant, sample_id: str, call_props: VariantCallProps) -> None:
        """Create or update a HAS_VARIANT relationship from an existing Sample to this Variant."""
        with self._driver.session() as session:
            session.execute_write(
                txs._link_sample_variant,
                sample_id=sample_id,
                REF_ACC=variant.REF_ACC,
                POS=variant.POS,
                REF=variant.REF,
                ALT=variant.ALT,
                hgvs_c=variant.hgvs_c,
                hgvs_p=variant.hgvs_p,
                DP=call_props.get("DP"),
                GT=call_props.get("GT"),
                QUAL=call_props.get("QUAL"),
                GQ=call_props.get("GQ"),
                AO=call_props.get("AO"),
                RO=call_props.get("RO"),
                FILTER=call_props.get("FILTER"),
                vcf_source=call_props.get("vcf_source"),
            )

    def get_by_sample(self, sample_id: str) -> list[tuple[Variant, VariantCallProps]]:
        """Return all Variants linked to a Sample, together with their call metadata."""
        with self._driver.session() as session:
            pairs = session.execute_read(txs._get_variants_by_sample, sample_id)
        result = []
        for v_raw, r_raw in pairs:
            variant = Variant.model_validate({
                "REF_ACC": v_raw.get("REF_ACC"),
                "POS": v_raw.get("POS"),
                "REF": v_raw.get("REF"),
                "ALT": v_raw.get("ALT"),
                "CHROM": v_raw.get("CHROM"),
                "TYPE": v_raw.get("TYPE"),
                "EFFECT": v_raw.get("EFFECT"),
                "IMPACT": v_raw.get("IMPACT"),
                "hgvs_c": v_raw.get("hgvs_c", ""),
                "hgvs_p": v_raw.get("hgvs_p", ""),
                "gene_name": v_raw.get("gene_name"),
            })
            call: VariantCallProps = {
                "DP": r_raw.get("DP"),
                "GT": r_raw.get("GT"),
                "QUAL": r_raw.get("QUAL"),
                "GQ": r_raw.get("GQ"),
                "AO": r_raw.get("AO"),
                "RO": r_raw.get("RO"),
                "FILTER": r_raw.get("FILTER"),
                "vcf_source": r_raw.get("vcf_source"),
            }
            result.append((variant, call))
        return result

    def get_by_ref(self, ref_accession: str) -> list[Variant]:
        """Return all Variants for a given reference accession."""
        with self._driver.session() as session:
            raws = session.execute_read(txs._get_variants_by_ref, REF_ACC=ref_accession)
        return [
            Variant.model_validate({
                "REF_ACC": r.get("REF_ACC"),
                "POS": r.get("POS"),
                "REF": r.get("REF"),
                "ALT": r.get("ALT"),
                "CHROM": r.get("CHROM"),
                "TYPE": r.get("TYPE"),
                "EFFECT": r.get("EFFECT"),
                "IMPACT": r.get("IMPACT"),
                "hgvs_c": r.get("hgvs_c", ""),
                "hgvs_p": r.get("hgvs_p", ""),
                "gene_name": r.get("gene_name"),
            })
            for r in raws
        ]

    def bulk_import_from_vcf(
        self,
        vcf_path: str,
        sample_id: str,
        ref_accession: str,
        source: Literal["medaka", "snippy"],
        batch_size: int = 500,
    ) -> NodeAndRelationshipCreationStats:
        """Parse a VCF file and bulk-import variants linked to an existing Sample node.

        Each ANN annotation entry in the VCF produces a separate Variant node.
        Records are committed in batches to handle large Snippy VCFs (>10k rows).
        Returns aggregate node and relationship creation counts.
        """
        from nosograph.utils.vcf import parse_medaka_vcf, parse_snippy_vcf

        if source == "medaka":
            records = parse_medaka_vcf(vcf_path, ref_accession, sample_id)
        else:
            records = parse_snippy_vcf(vcf_path, ref_accession, sample_id)

        with self._driver.session() as session:
            exists = session.execute_read(
                lambda tx: tx.run(
                    "MATCH (s:Sample {sample_id: $id}) RETURN s LIMIT 1", id=sample_id
                ).single()
            )
        if exists is None:
            raise ValueError(f"Sample '{sample_id}' not found")

        total_nodes = 0
        total_rels = 0

        with self._driver.session() as session:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                stats = session.execute_write(txs._bulk_merge_variants, batch)
                total_nodes += stats["nodes_created"]
                total_rels += stats["relationships_created"]

        return {"nodes_created": total_nodes, "relationships_created": total_rels}
