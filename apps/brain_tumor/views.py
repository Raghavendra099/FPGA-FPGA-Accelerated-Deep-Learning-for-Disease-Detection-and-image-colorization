"""
Brain MRI Tumor Localization and Segmentation Views.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from database.repositories.image_repository import ImageRepository
from database.repositories.analysis_repository import AnalysisRepository

@login_required
def index_view(request):
    """Brain MRI tumor analysis workspace."""
    selected_image_id = request.GET.get("image_id")
    selected_image = None
    analysis_record = None

    if selected_image_id:
        selected_image = ImageRepository.get_by_image_id(selected_image_id)
        if selected_image:
            analysis_record = AnalysisRepository.get_by_image_id(selected_image_id)

    # Fetch recent MRI analyses and images
    recent_mri_analyses = AnalysisRepository.list_recent(limit=20, task="BRAIN_TUMOR_SEGMENTATION")
    mri_images = [img for img in ImageRepository.list_recent_images(limit=50) if img.get("modality") == "BRAIN_MRI"]

    return render(request, "brain_tumor/index.html", {
        "selected_image": selected_image,
        "analysis": analysis_record,
        "recent_mri_analyses": recent_mri_analyses,
        "mri_images": mri_images,
    })
