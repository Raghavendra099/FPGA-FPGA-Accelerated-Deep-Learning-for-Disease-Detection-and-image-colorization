"""
Lung CT Disease and Pulmonary Nodule Analysis Views.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from database.repositories.image_repository import ImageRepository
from database.repositories.analysis_repository import AnalysisRepository

@login_required
def index_view(request):
    """Lung disease analysis workspace."""
    selected_image_id = request.GET.get("image_id")
    selected_image = None
    analysis_record = None

    if selected_image_id:
        selected_image = ImageRepository.get_by_image_id(selected_image_id)
        if selected_image:
            analysis_record = AnalysisRepository.get_by_image_id(selected_image_id)

    # Fetch recent CT images and analyses
    recent_ct_analyses = AnalysisRepository.list_recent(limit=20, task="LUNG_NODULE_DETECTION")
    ct_images = [img for img in ImageRepository.list_recent_images(limit=50) if img.get("modality") == "CHEST_CT"]

    return render(request, "lung_analysis/index.html", {
        "selected_image": selected_image,
        "analysis": analysis_record,
        "recent_ct_analyses": recent_ct_analyses,
        "ct_images": ct_images,
    })
