"""
Device repository for IoT and external medical hardware integrations.
"""
from datetime import datetime
import hashlib
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class DeviceRepository:
    @staticmethod
    def _col():
        return get_collection("device_registry")

    @staticmethod
    def hash_api_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

    @classmethod
    def register_device(
        cls,
        name: str,
        device_type: str,
        raw_api_key: str,
        registered_by: str,
        metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        device_id = f"dev_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow()
        doc = {
            "device_id": device_id,
            "name": name,
            "device_type": device_type,  # MOBILE_XRAY, CT_SCANNER, MRI_CONSOLE, RASPBERRY_PI_GATEWAY, EDGE_AI_NODE
            "api_key_hash": cls.hash_api_key(raw_api_key),
            "status": "ONLINE",
            "registered_by": registered_by,
            "metadata": metadata or {},
            "last_seen": now,
            "created_at": now,
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def verify_api_key(cls, raw_api_key: str) -> Optional[Dict[str, Any]]:
        if not raw_api_key:
            return None
        key_hash = cls.hash_api_key(raw_api_key)
        return cls._col().find_one({"api_key_hash": key_hash, "status": "ONLINE"})

    @classmethod
    def update_heartbeat(cls, device_id: str):
        cls._col().update_one(
            {"device_id": device_id},
            {"$set": {"last_seen": datetime.utcnow(), "status": "ONLINE"}}
        )

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        cursor = cls._col().find({}, {"api_key_hash": 0}).sort("created_at", -1)
        return list(cursor)

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
