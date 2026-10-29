"""
Analysis repository for AI inference, disease detection, and segmentation outputs.
"""
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from database.mongodb import get_collection

class AnalysisRepository:
    @staticmethod
    def _col():
        return get_collection("analysis_records")

    @classmethod
    def create_analysis_record(
        cls,
        image_id: str,
        task: str,
        modality: str,
        model_id: str,
        model_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        analysis_id = f"anl_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        doc = {
            "analysis_id": analysis_id,
            "image_id": image_id,
            "task": task.upper(),  # CHEST_XRAY_CLASSIFICATION, LUNG_NODULE_DETECTION, BRAIN_TUMOR_SEGMENTATION, COLORIZATION
            "modality": modality.upper(),
            "model_id": model_id,
            "model_version": model_version,
            "status": "PROCESSING",  # PROCESSING, COMPLETED, FAILED
            "primary_finding": None,
            "confidence": None,
            "severity": None,
            "predictions": [],
            "detection_results": None,
            "segmentation_results": None,
            "gradcam_path": None,
            "colorized_path": None,
            "uncertainty": None,
            "quality_assessment": None,
            "execution_time_seconds": 0.0,
            "error_message": None,
            "created_at": now,
            "completed_at": None,
        }
        cls._col().insert_one(doc)
        return doc

    @classmethod
    def complete_analysis(
        cls,
        analysis_id: str,
        primary_finding: str,
        confidence: float,
        predictions: list,
        quality_assessment: Optional[dict] = None,
        uncertainty: Optional[dict] = None,
        gradcam_path: Optional[str] = None,
        colorized_path: Optional[str] = None,
        detection_results: Optional[dict] = None,
        segmentation_results: Optional[dict] = None,
        severity: Optional[str] = None,
        execution_time_seconds: float = 0.0
    ) -> bool:
        update_data = {
            "status": "COMPLETED",
            "primary_finding": primary_finding,
            "confidence": confidence,
            "predictions": predictions,
            "quality_assessment": quality_assessment,
            "uncertainty": uncertainty,
            "gradcam_path": gradcam_path,
            "colorized_path": colorized_path,
            "detection_results": detection_results,
            "segmentation_results": segmentation_results,
            "severity": severity or "Low/Normal",
            "execution_time_seconds": round(execution_time_seconds, 3),
            "completed_at": datetime.utcnow()
        }
        result = cls._col().update_one(
            {"analysis_id": analysis_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @classmethod
    def fail_analysis(cls, analysis_id: str, error_message: str) -> bool:
        result = cls._col().update_one(
            {"analysis_id": analysis_id},
            {
                "$set": {
                    "status": "FAILED",
                    "error_message": error_message,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    @classmethod
    def get_by_id(cls, analysis_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"analysis_id": analysis_id})

    @classmethod
    def get_by_image_id(cls, image_id: str) -> Optional[Dict[str, Any]]:
        return cls._col().find_one({"image_id": image_id}, sort=[("created_at", -1)])

    @classmethod
    def list_recent(cls, limit: int = 50, task: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if task:
            query["task"] = task.upper()
        return list(cls._col().find(query).sort("created_at", -1).limit(limit))

    @classmethod
    def count_by_status(cls, status: str) -> int:
        return cls._col().count_documents({"status": status})

    @classmethod
    def count_by_task(cls, task: str) -> int:
        return cls._col().count_documents({"task": task.upper()})

    @classmethod
    def count_total(cls) -> int:
        return cls._col().count_documents({})
