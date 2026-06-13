from __future__ import annotations
from nosograph.repositories._base import BaseRepository
from nosograph.models.resistance import DrugClass, Drug, Mutation, StanfordHIVDRPrediction
from nosograph.types import NodeAndRelationshipCreationStats
import nosograph._txs as txs


class DrugResistanceRepository(BaseRepository):
    """CRUD and sierrapy bulk import for the Stanford HIVdb drug-resistance schema.

    Node types: ``DrugClass``, ``Drug``, ``Mutation``, ``StanfordHIVDRPrediction``.
    Relationships built by :meth:`bulk_import_from_sierra`:
    ``HAS_STANFORD_HIVDR_PREDICTION`` (Sample→prediction),
    ``PREDICTS_RESISTANCE_TO`` (prediction→drug),
    ``IN_DRUG_CLASS`` (drug→class),
    ``CONFERS_RESISTANCE_TO`` (mutation→drug, ``score`` on the edge).
    """

    # -- DrugClass -----------------------------------------------------------
    def create_drug_class(self, drug_class: DrugClass) -> str:
        """Create a DrugClass node (idempotent) and return its name."""
        with self._driver.session() as session:
            return session.execute_write(txs._create_drug_class, drug_class.name, drug_class.full_name)

    def get_drug_class(self, name: str) -> DrugClass | None:
        """Return a DrugClass by name, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_drug_class, name)
        if raw is None:
            return None
        return DrugClass.model_validate({"name": raw.get("name"), "full_name": raw.get("full_name")})

    # -- Drug ----------------------------------------------------------------
    def create_drug(self, drug: Drug) -> str:
        """Create a Drug node (idempotent) and return its name."""
        with self._driver.session() as session:
            return session.execute_write(txs._create_drug, drug.name, drug.full_name, drug.display_abbr)

    def get_drug(self, name: str) -> Drug | None:
        """Return a Drug by name, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_drug, name)
        if raw is None:
            return None
        return Drug.model_validate({
            "name": raw.get("name"),
            "full_name": raw.get("full_name"),
            "display_abbr": raw.get("display_abbr"),
        })

    # -- Mutation ------------------------------------------------------------
    def create_mutation(self, mutation: Mutation) -> Mutation:
        """Create or match a Mutation node (idempotent)."""
        with self._driver.session() as session:
            raw = session.execute_write(txs._create_mutation, mutation.gene, mutation.text, mutation.primary_type)
        return Mutation.model_validate({
            "gene": raw.get("gene"),
            "text": raw.get("text"),
            "primary_type": raw.get("primary_type"),
        })

    def get_mutation(self, gene: str, text: str) -> Mutation | None:
        """Return a Mutation by (gene, text), or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_mutation, gene, text)
        if raw is None:
            return None
        return Mutation.model_validate({
            "gene": raw.get("gene"),
            "text": raw.get("text"),
            "primary_type": raw.get("primary_type"),
        })

    def delete_mutation(self, gene: str, text: str) -> None:
        """Delete a Mutation node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_mutation, gene, text)

    # -- StanfordHIVDRPrediction ---------------------------------------------
    def create_prediction(self, prediction: StanfordHIVDRPrediction) -> str:
        """Create a StanfordHIVDRPrediction node (idempotent) and return its id."""
        with self._driver.session() as session:
            return session.execute_write(
                txs._create_hivdr_prediction,
                prediction_id=prediction.prediction_id,
                sample_id=prediction.sample_id,
                gene=prediction.gene,
                drug_name=prediction.drug_name,
                score=prediction.score,
                level=prediction.level,
            )

    def get_prediction(self, prediction_id: str) -> StanfordHIVDRPrediction | None:
        """Return a StanfordHIVDRPrediction by id, or None if not found."""
        with self._driver.session() as session:
            raw = session.execute_read(txs._get_hivdr_prediction, prediction_id)
        if raw is None:
            return None
        return StanfordHIVDRPrediction.model_validate({
            "prediction_id": raw.get("prediction_id"),
            "sample_id": raw.get("sample_id"),
            "gene": raw.get("gene"),
            "drug_name": raw.get("drug_name"),
            "score": raw.get("score"),
            "level": raw.get("level"),
        })

    def delete_prediction(self, prediction_id: str) -> None:
        """Delete a StanfordHIVDRPrediction node and all its relationships."""
        with self._driver.session() as session:
            session.execute_write(txs._delete_hivdr_prediction, prediction_id)

    # -- Bulk import & reads -------------------------------------------------
    def bulk_import_from_sierra(self, json_path: str, sample_id: str) -> NodeAndRelationshipCreationStats:
        """Parse a sierrapy/Stanford HIVdb JSON report and import all predictions,
        drugs, drug classes and resistance mutations for an existing Sample node.

        Raises ValueError if the Sample does not exist. Returns aggregate node and
        relationship creation counts.
        """
        from nosograph.utils.sierra import parse_sierra_json

        records = parse_sierra_json(json_path, sample_id)

        with self._driver.session() as session:
            exists = session.execute_read(
                lambda tx: tx.run(
                    "MATCH (s:Sample {sample_id: $id}) RETURN s LIMIT 1", id=sample_id
                ).single()
            )
        if exists is None:
            raise ValueError(f"Sample '{sample_id}' not found")

        if not records:
            return {"nodes_created": 0, "relationships_created": 0}

        with self._driver.session() as session:
            return session.execute_write(txs._bulk_merge_hivdr, sample_id, records)

    def get_resistance_by_sample(self, sample_id: str) -> list[tuple[StanfordHIVDRPrediction, str | None]]:
        """Return all resistance predictions for a sample as (prediction, drug_class) pairs."""
        with self._driver.session() as session:
            rows = session.execute_read(txs._get_resistance_by_sample, sample_id)
        result: list[tuple[StanfordHIVDRPrediction, str | None]] = []
        for row in rows:
            p = row["prediction"]
            prediction = StanfordHIVDRPrediction.model_validate({
                "prediction_id": p.get("prediction_id"),
                "sample_id": p.get("sample_id"),
                "gene": p.get("gene"),
                "drug_name": p.get("drug_name"),
                "score": p.get("score"),
                "level": p.get("level"),
            })
            result.append((prediction, row["drug_class"]))
        return result

    def get_mutations_for_drug(self, drug_name: str) -> list[tuple[Mutation, float | None]]:
        """Return mutations conferring resistance to a drug as (mutation, score) pairs."""
        with self._driver.session() as session:
            rows = session.execute_read(txs._get_mutations_for_drug, drug_name)
        return [
            (
                Mutation.model_validate({
                    "gene": row["mutation"].get("gene"),
                    "text": row["mutation"].get("text"),
                    "primary_type": row["mutation"].get("primary_type"),
                }),
                row["score"],
            )
            for row in rows
        ]
