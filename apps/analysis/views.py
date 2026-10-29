"""
Unified AI Analysis Results and Analysis History Views.
"""
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404

from database.repositories.analysis_repository import AnalysisRepository
from database.repositories.image_repository import ImageRepository
from database.repositories.report_repository import ReportRepository

@login_required
def detail_view(request, analysis_id):
    """
    Unified multi-modal results viewer.
    Adapts seamlessly to Chest X-ray, Brain MRI, Lung CT, or Colorization outputs.
    """
    analysis_doc = AnalysisRepository.get_by_id(analysis_id)
    if not analysis_doc:
        raise Http404("Analysis record not found.")

    image_doc = ImageRepository.get_by_image_id(analysis_doc["image_id"])
    report_doc = ReportRepository.get_by_analysis_id(analysis_id)

    context = {
        "analysis": analysis_doc,
        "image": image_doc,
        "report": report_doc,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "analysis/detail.html", context)

@login_required
def history_view(request):
    """Historical records of all completed and pending analyses."""
    task_filter = request.GET.get("task", "")
    query_task = task_filter if task_filter else None

    analyses = AnalysisRepository.list_recent(limit=100, task=query_task)

    # Attach related images
    image_ids = [a.get("image_id") for a in analyses if a.get("image_id")]
    image_map = {img["image_id"]: img for img in ImageRepository.list_recent_images(limit=150)}

    enriched_analyses = []
    for a in analyses:
        item = dict(a)
        item["image"] = image_map.get(a.get("image_id"))
        enriched_analyses.append(item)

    return render(request, "analysis/history.html", {
        "analyses": enriched_analyses,
        "selected_task": task_filter,
    })
