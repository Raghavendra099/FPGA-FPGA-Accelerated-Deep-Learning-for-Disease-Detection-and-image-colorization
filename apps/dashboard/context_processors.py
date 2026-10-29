"""
Context processors for global template variables across SmartMed AI.
"""
from database.repositories.image_repository import ImageRepository
from database.repositories.analysis_repository import AnalysisRepository

def smartmed_context(request):
    try:
        pending_review_count = ImageRepository.count_pending()
        total_images_count = ImageRepository.count_total()
        completed_analyses_count = AnalysisRepository.count_by_status("COMPLETED")
    except Exception:
        pending_review_count = 0
        total_images_count = 0
        completed_analyses_count = 0

    user_role = getattr(request, "user_role", "reviewer")
    mongo_user = getattr(request, "mongo_user", None)

    return {
        "APP_NAME": "SmartMed AI",
        "APP_TAGLINE": "Intelligent Medical Imaging. Explainable AI. Reliable Research.",
        "DISCLAIMER_TEXT": "For academic research and educational use only. AI-generated outputs are not a confirmed medical diagnosis and must not replace professional medical evaluation.",
        "pending_review_count": pending_review_count,
        "total_images_count": total_images_count,
        "completed_analyses_count": completed_analyses_count,
        "user_role": user_role,
        "mongo_user": mongo_user,
    }
