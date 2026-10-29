"""
Audit repository for tracking compliance, security, and medical imaging actions.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class AuditRepository:
    @staticmethod
    def _col():
        return get_collection("audit_events")

    @classmethod
    def record_event(
        cls,
        actor: str,
        action: str,
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        event_id = f"aud_{uuid.uuid4().hex[:12]}"
        doc = {
            "event_id": event_id,
            "actor": actor,
            "action": action,  # LOGIN, LOGOUT, QR_SESSION_CREATED, IMAGE_UPLOADED, REVIEW_CONFIRMED, REVIEW_REJECTED, ANALYSIS_EXECUTED, REPORT_GENERATED, DEVICE_INGEST
            "target_id": target_id,
            "metadata": metadata or {},
            "ip_address": ip_address or "127.0.0.1",
            "created_at": datetime.utcnow(),
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def list_recent(cls, limit: int = 50) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
