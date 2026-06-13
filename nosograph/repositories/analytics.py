from __future__ import annotations
from nosograph.repositories._base import BaseRepository
from nosograph.models.genomics import Variant
from nosograph.types import VariantCallProps
import nosograph._txs as txs


def _to_variant(raw: dict) -> Variant:
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


def _to_call(raw: dict) -> VariantCallProps:
    return {
        "DP": raw.get("DP"),
        "GT": raw.get("GT"),
        "QUAL": raw.get("QUAL"),
        "GQ": raw.get("GQ"),
        "AO": raw.get("AO"),
        "RO": raw.get("RO"),
        "FILTER": raw.get("FILTER"),
        "vcf_source": raw.get("vcf_source"),
    }


class PatientVariant:
    """One Variant observed for a patient, with its sequencing provenance."""

    def __init__(self, specimen_id: str, sample_id: str, variant: Variant, call: VariantCallProps):
        self.specimen_id = specimen_id
        self.sample_id = sample_id
        self.variant = variant
        self.call = call


class WardVariantCluster:
    """A Variant shared by multiple patients admitted to the same ward."""

    def __init__(self, ward_id: str, ward_name: str | None, variant: Variant, patient_ids: list[str], patient_count: int):
        self.ward_id = ward_id
        self.ward_name = ward_name
        self.variant = variant
        self.patient_ids = patient_ids
        self.patient_count = patient_count


class AnalyticsRepository(BaseRepository):
    """Cross-domain analytical queries spanning clinical and genomic data."""

    def patient_variants(self, patient_id: str) -> list[PatientVariant]:
        """Return every Variant observed for a patient, traversing
        Patient <- Specimen <- Sample -> Variant, with sequencing provenance
        (specimen_id, sample_id) and per-call metadata.
        """
        with self._driver.session() as session:
            rows = session.execute_read(txs._get_patient_variants, patient_id)
        return [
            PatientVariant(
                specimen_id=row["specimen_id"],
                sample_id=row["sample_id"],
                variant=_to_variant(row["variant"]),
                call=_to_call(row["call"]),
            )
            for row in rows
        ]

    def ward_variant_clusters(self, min_patients: int = 2) -> list[WardVariantCluster]:
        """Return variants shared by at least ``min_patients`` distinct patients
        admitted to the same ward — a candidate outbreak/transmission signal.
        Ordered by patient_count descending.
        """
        if min_patients < 1:
            raise ValueError("min_patients must be >= 1")
        with self._driver.session() as session:
            rows = session.execute_read(txs._get_ward_variant_clusters, min_patients)
        return [
            WardVariantCluster(
                ward_id=row["ward_id"],
                ward_name=row["ward_name"],
                variant=_to_variant(row["variant"]),
                patient_ids=row["patient_ids"],
                patient_count=row["patient_count"],
            )
            for row in rows
        ]
