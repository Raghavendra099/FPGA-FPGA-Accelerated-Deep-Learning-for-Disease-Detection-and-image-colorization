"""
Report repository for generated PDF research reports.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class ReportRepository:
    @staticmethod
    def _col():
        return get_collection("report_records")

    @classmethod
    def create_report_record(
        cls,
        analysis_id: str,
        pdf_path: str,
        report_title: str,
        generated_by: str,
        file_size_bytes: int,
        page_count: int = 3
    ) -> Dict[str, Any]:
        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        doc = {
            "report_id": report_id,
            "analysis_id": analysis_id,
            "pdf_path": pdf_path,
            "report_title": report_title,
            "generated_by": generated_by,
            "file_size_bytes": file_size_bytes,
            "page_count": page_count,
            "created_at": datetime.utcnow(),
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def get_by_id(cls, report_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"report_id": report_id})

    @classmethod
    def get_by_analysis_id(cls, analysis_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"analysis_id": analysis_id}, sort=[("created_at", -1)])

    @classmethod
    def list_recent(cls, limit: int = 30) -> List[Dict[str, Any]]:
        return list(cls._col().find().sort("created_at", -1).limit(limit))

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
