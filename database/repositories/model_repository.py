"""
Model repository for registered medical deep learning models and modality routing.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class ModelRepository:
    @staticmethod
    def _col():
        return get_collection("model_registry")

    @classmethod
    def register_model(cls, model_doc: Dict[str, Any]) -> Dict[str, Any]:
        model_doc["updated_at"] = datetime.utcnow()
        cls._col().update_one(
            {"model_id": model_doc["model_id"]},
            {"$set": model_doc},
            upsert=True
        )
        return model_doc

    @classmethod
    def get_by_id(cls, model_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"model_id": model_id})

    @classmethod
    def get_active_model_for_task(cls, modality: str, task: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({
            "modality": modality.upper(),
            "task": task.upper(),
            "is_active": True
        })

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("modality", 1))

    @classmethod
    def update_checkpoint_status(cls, model_id: str, verified: bool):
        cls._col().update_one(
            {"model_id": model_id},
            {"$set": {"is_checkpoint_verified": verified, "updated_at": datetime.utcnow()}}
        )
