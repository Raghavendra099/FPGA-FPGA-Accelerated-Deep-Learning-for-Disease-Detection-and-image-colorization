"""
Image repository for uploaded medical images.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class ImageRepository:
    @staticmethod
    def _col():
        return get_collection("image_records")

    @classmethod
    def create_image_record(
        cls,
        filename: str,
        stored_path: str,
        file_size_bytes: int,
        format_name: str,
        dimensions: list,
        session_id: Optional[str] = None,
        modality: str = "OTHER",
        source: str = "mobile_qr"
    ) -> Dict[str, Any]:
        image_id = f"img_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        doc = {
            "image_id": image_id,
            "session_id": session_id,
            "source": source,  # mobile_qr, web_direct, device_api
            "filename": filename,
            "stored_path": stored_path,
            "file_size_bytes": file_size_bytes,
            "format": format_name.upper(),
            "dimensions": dimensions,  # [width, height]
            "modality": modality.upper(),  # CHEST_XRAY, CHEST_CT, BRAIN_MRI, OTHER
            "review_status": "PENDING",  # PENDING, CONFIRMED, REJECTED
            "reviewer": None,
            "reviewed_at": None,
            "rejection_reason": None,
            "quality_assessment": None,
            "created_at": now,
            "updated_at": now,
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def get_by_image_id(cls, image_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"image_id": image_id})

    @classmethod
    def get_by_session_id(cls, session_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"session_id": session_id})

    @classmethod
    def list_pending_reviews(cls, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = cls._col().find({"review_status": "PENDING"}).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    @classmethod
    def count_pending(cls) -> int:
        return cls._col().count_documents({"review_status": "PENDING"})

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})

    @classmethod
    def confirm_image(cls, image_id: str, reviewer: str, modality: Optional[str] = None) -> bool:
        update_data = {
            "review_status": "CONFIRMED",
            "reviewer": reviewer,
            "reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        if modality:
            update_data["modality"] = modality.upper()

        result = cls._col().update_one(
            {"image_id": image_id, "review_status": "PENDING"},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @classmethod
    def reject_image(cls, image_id: str, reviewer: str, reason: str = "") -> bool:
        result = cls._col().update_one(
            {"image_id": image_id, "review_status": "PENDING"},
            {
                "$set": {
                    "review_status": "REJECTED",
                    "reviewer": reviewer,
                    "rejection_reason": reason or "Rejected during human review",
                    "reviewed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    @classmethod
    def update_quality_assessment(cls, image_id: str, quality_data: Dict[str, Any]):
        cls._col().update_one(
            {"image_id": image_id},
            {"$set": {"quality_assessment": quality_data, "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def list_recent_images(cls, limit: int = 50) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))
