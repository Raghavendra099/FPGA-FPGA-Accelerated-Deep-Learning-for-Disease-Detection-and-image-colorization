"""
Upload Session repository for QR-code mobile image uploads.
"""
from datetime import datetime, timedelta
import hashlib
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class SessionRepository:
    @staticmethod
    def _col():
        return get_collection("upload_sessions")

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @classmethod
    def create_session(cls, raw_token: str, created_by: str, expires_in_minutes: int = 30, requested_modality: str = "AUTO") -> Dict[str, Any]:
        token_hash = cls.hash_token(raw_token)
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=expires_in_minutes)

        session_doc = {
            "session_id": session_id,
            "token_hash": token_hash,
            "status": "WAITING_FOR_UPLOAD",  # WAITING_FOR_UPLOAD, IMAGE_UPLOADED, PENDING_REVIEW, PROCESSING, COMPLETED, REJECTED, EXPIRED, FAILED
            "created_by": created_by,
            "requested_modality": requested_modality,
            "image_id": None,
            "upload_count": 0,
            "max_uploads": 1,
            "created_at": now,
            "expires_at": expires_at,
            "updated_at": now,
        }
        cls._col().insert_one(session_doc)
        return session_doc

    @classmethod
    def get_by_session_id(cls, session_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"session_id": session_id})

    @classmethod
    def get_by_raw_token(cls, raw_token: str) -> Optional[Dict[str, Any]]:
        token_hash = cls.hash_token(raw_token)
        return cls._col().find_one({"token_hash": token_hash})

    @classmethod
    def update_status(cls, session_id: str, new_status: str, image_id: Optional[str] = None) -> bool:
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        if image_id is not None:
            update_data["image_id"] = image_id
            update_data["upload_count"] = 1

        result = cls._col().update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @classmethod
    def mark_image_uploaded(cls, session_id: str, image_id: str) -> bool:
        result = cls._col().update_one(
            {
                "session_id": session_id,
                "status": {"$in": ["WAITING_FOR_UPLOAD", "CREATED"]},
                "upload_count": {"$lt": 1}
            },
            {
                "$set": {
                    "status": "IMAGE_UPLOADED",
                    "image_id": image_id,
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"upload_count": 1}
            }
        )
        return result.modified_count > 0

    @classmethod
    def is_expired(cls, session_doc: Dict[str, Any]) -> bool:
        if not session_doc:
            return True
        expires_at = session_doc.get("expires_at")
        if not expires_at:
            return True
        return datetime.utcnow() > expires_at

    @classmethod
    def list_recent_sessions(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))
