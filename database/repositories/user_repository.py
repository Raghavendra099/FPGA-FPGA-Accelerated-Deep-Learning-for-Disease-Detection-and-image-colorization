"""
User repository for MongoDB users collection.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class UserRepository:
    @staticmethod
    def _col():
        return get_collection("users")

    @classmethod
    def create_user(cls, username: str, email: str, password_hash: str, role: str = "reviewer", full_name: str = "") -> Dict[str, Any]:
        user_doc = {
            "user_id": f"usr_{uuid.uuid4().hex[:12]}",
            "username": username.strip().lower(),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "role": role,  # 'admin' or 'reviewer'
            "full_name": full_name or username,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
        }
        cls._col().insert_one(user_doc)
        return user_doc

    @classmethod
    def get_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        if not username:
            return None
        return cls._col().find_one({"username": username.strip().lower()})

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"user_id": user_id})

    @classmethod
    def update_last_login(cls, username: str):
        cls._col().update_one(
            {"username": username.strip().lower()},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    @classmethod
    def list_users(cls, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = cls._col().find({}, {"password_hash": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return list(cursor)

    @classmethod
    def count_users(cls) -> int:
        return cls._col().count_documents({})
