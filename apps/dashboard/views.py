"""
Dashboard views for SmartMed AI main overview.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from database.repositories.image_repository import ImageRepository
from database.repositories.analysis_repository import AnalysisRepository
from database.repositories.colorization_repository import ColorizationRepository
from database.repositories.device_repository import DeviceRepository
from database.repositories.audit_repository import AuditRepository

@login_required
def index(request):
    try:
        total_images = ImageRepository.count_total()
        pending_reviews = ImageRepository.count_pending()
        completed_analyses = AnalysisRepository.count_by_status("COMPLETED")
        failed_jobs = AnalysisRepository.count_by_status("FAILED")
        colorization_jobs = ColorizationRepository.count_total()
        lung_ct_jobs = AnalysisRepository.count_by_task("LUNG_NODULE_DETECTION")
        brain_mri_jobs = AnalysisRepository.count_by_task("BRAIN_TUMOR_SEGMENTATION")
        registered_devices = DeviceRepository.count_total()

        recent_images = ImageRepository.list_recent_images(limit=10)
        recent_analyses = AnalysisRepository.list_recent(limit=10)
        recent_audits = AuditRepository.list_recent(limit=6)

        # Merge recent activity records for clean dashboard view
        analysis_map = {a.get("image_id"): a for a in recent_analyses if a.get("image_id")}
        activity_items = []
        for img in recent_images:
            img_id = img.get("image_id")
            related_analysis = analysis_map.get(img_id)
            activity_items.append({
                "image_id": img_id,
                "filename": img.get("filename"),
                "modality": img.get("modality", "OTHER"),
                "file_size_kb": round(img.get("file_size_bytes", 0) / 1024, 1),
                "review_status": img.get("review_status", "PENDING"),
                "processing_status": related_analysis.get("status") if related_analysis else "NOT_STARTED",
                "analysis_id": related_analysis.get("analysis_id") if related_analysis else None,
                "primary_finding": related_analysis.get("primary_finding") if related_analysis else None,
                "created_at": img.get("created_at"),
            })

    except Exception as e:
        total_images = pending_reviews = completed_analyses = failed_jobs = 0
        colorization_jobs = lung_ct_jobs = brain_mri_jobs = registered_devices = 0
        activity_items = []
        recent_audits = []

    context = {
        "stats": {
            "total_images": total_images,
            "pending_reviews": pending_reviews,
            "completed_analyses": completed_analyses,
            "colorization_jobs": colorization_jobs,
            "lung_ct_jobs": lung_ct_jobs,
            "brain_mri_jobs": brain_mri_jobs,
            "failed_jobs": failed_jobs,
            "registered_devices": registered_devices,
        },
        "activity_items": activity_items,
        "recent_audits": recent_audits,
    }
    return render(request, "dashboard/index.html", context)
