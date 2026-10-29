"""
Evaluation repository for cross-dataset model benchmarking and performance metrics.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class EvaluationRepository:
    @staticmethod
    def _col():
        return get_collection("model_evaluations")

    @classmethod
    def create_evaluation_record(
        cls,
        model_id: str,
        dataset_name: str,
        metrics: Dict[str, Any],
        sample_count: int,
        confusion_matrix: Optional[list] = None,
        labels: Optional[list] = None,
        executed_by: str = "system"
    ) -> Dict[str, Any]:
        eval_id = f"eval_{uuid.uuid4().hex[:12]}"
        doc = {
            "evaluation_id": eval_id,
            "model_id": model_id,
            "dataset_name": dataset_name,
            "sample_count": sample_count,
            "metrics": metrics,
            "confusion_matrix": confusion_matrix or [],
            "labels": labels or [],
            "executed_by": executed_by,
            "created_at": datetime.utcnow(),
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def get_by_id(cls, evaluation_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"evaluation_id": evaluation_id})

    @classmethod
    def list_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
