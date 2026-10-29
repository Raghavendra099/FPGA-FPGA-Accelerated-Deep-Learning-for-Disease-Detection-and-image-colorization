"""
AI Medical Image Colorization Studio Views.
Provides side-by-side comparison, before-and-after interactive slider, and export tools.
"""
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404

from database.repositories.image_repository import ImageRepository
from database.repositories.colorization_repository import ColorizationRepository
from database.repositories.analysis_repository import AnalysisRepository
from ai_engine.colorization import MedicalColorizationService

@login_required
def studio_view(request):
    """Image Colorization Studio main workspace."""
    selected_image_id = request.GET.get("image_id")
    selected_image = None
    colorization_result = None

    if selected_image_id:
        selected_image = ImageRepository.get_by_image_id(selected_image_id)
        if selected_image:
            colorization_result = ColorizationRepository.get_by_image_id(selected_image_id)

    # Fetch recent candidate images for colorization
    recent_images = ImageRepository.list_recent_images(limit=30)
    colorized_records = ColorizationRepository.list_recent(limit=10)

    return render(request, "colorization/studio.html", {
        "selected_image": selected_image,
        "colorization": colorization_result,
        "recent_images": recent_images,
        "colorized_records": colorized_records,
    })

@login_required
def run_colorization(request, image_id):
    """Executes colorization on the selected image."""
    image_doc = ImageRepository.get_by_image_id(image_id)
    if not image_doc:
        raise Http404("Image not found.")

    palette_mode = request.POST.get("palette_mode", "SPECTRAL_RADIOMIC")
    abs_image_path = os.path.join(settings.MEDIA_ROOT, image_doc["stored_path"])

    try:
        color_res = MedicalColorizationService.colorize_image(
            image_path=abs_image_path,
            output_dir=os.path.join(settings.MEDIA_ROOT, "colorized"),
            image_id=image_id,
            palette_mode=palette_mode
        )
        ColorizationRepository.create_record(
            image_id=image_id,
            colorized_path=color_res["colorized_rel_path"],
            comparison_path=color_res["comparison_rel_path"],
            palette_mode=palette_mode,
            parameters=color_res["parameters"]
        )
        messages.success(request, f"Colorization generated successfully using {palette_mode} palette!")
    except Exception as e:
        messages.error(request, f"Colorization failed: {str(e)}")

    return redirect(f"/colorization/?image_id={image_id}")
