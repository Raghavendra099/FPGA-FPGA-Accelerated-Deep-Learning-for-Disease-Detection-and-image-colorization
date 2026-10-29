"""
Colorization repository for AI Medical Image Colorization Studio.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class ColorizationRepository:
    @staticmethod
    def _col():
        return get_collection("colorization_records")

    @classmethod
    def create_record(
        cls,
        image_id: str,
        colorized_path: str,
        comparison_path: Optional[str] = None,
        model_id: str = "smartmed-radiomic-colorizer-v1",
        palette_mode: str = "SPECTRAL_RADIOMIC",
        parameters: Optional[dict] = None
    ) -> Dict[str, Any]:
        colorization_id = f"col_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        doc = {
            "colorization_id": colorization_id,
            "image_id": image_id,
            "model_id": model_id,
            "colorized_path": colorized_path,
            "comparison_path": comparison_path,
            "palette_mode": palette_mode,
            "parameters": parameters or {},
            "status": "COMPLETED",
            "created_at": now,
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def get_by_id(cls, colorization_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"colorization_id": colorization_id})

    @classmethod
    def get_by_image_id(cls, image_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"image_id": image_id}, sort=[("created_at", -1)])

    @classmethod
    def list_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
