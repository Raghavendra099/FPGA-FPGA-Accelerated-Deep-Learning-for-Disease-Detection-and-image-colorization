"""
Human Review & Confirmation Workflow Views.
Mandatory reviewer verification before any deep learning processing pipeline begins.
"""
import os
import time
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from database.repositories.image_repository import ImageRepository
from database.repositories.session_repository import SessionRepository
from database.repositories.analysis_repository import AnalysisRepository
from database.repositories.colorization_repository import ColorizationRepository
from database.repositories.audit_repository import AuditRepository

from ai_engine.quality_assessment import ImageQualityAssessment
from ai_engine.model_registry import ModelRegistryService, ModalityMismatchError
from ai_engine.inference import ChestXRayInferenceService
from ai_engine.gradcam import GradCAMService
from ai_engine.uncertainty import UncertaintyEvaluator
from ai_engine.brain_segmentation import BrainMRISegmentationService
from ai_engine.lung_detection import LungCTNoduleDetector
from ai_engine.colorization import MedicalColorizationService

@login_required
def pending_list_view(request):
    """Lists all uploaded medical images awaiting human review."""
    pending_images = ImageRepository.list_pending_reviews(skip=0, limit=50)
    return render(request, "review/pending_list.html", {
        "pending_images": pending_images,
        "count": len(pending_images)
    })

@login_required
def review_detail_view(request, image_id):
    """
    Two-column review view: original image with pan/zoom inspection,
    automated quality assessment preview, modality verification, and Confirm/Reject controls.
    """
    image_doc = ImageRepository.get_by_image_id(image_id)
    if not image_doc:
        raise Http404("Medical image record not found.")

    abs_image_path = os.path.join(settings.MEDIA_ROOT, image_doc["stored_path"])

    # Run automated quality assessment preview if not already saved
    quality_data = image_doc.get("quality_assessment")
    if not quality_data and os.path.exists(abs_image_path):
        quality_data = ImageQualityAssessment.evaluate(abs_image_path)
        ImageRepository.update_quality_assessment(image_id, quality_data)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "REJECT":
            reason = request.POST.get("rejection_reason", "").strip() or "Rejected by reviewer during visual review."
            ImageRepository.reject_image(image_id, reviewer=request.user.username, reason=reason)
            if image_doc.get("session_id"):
                SessionRepository.update_status(image_doc["session_id"], "REJECTED")

            AuditRepository.record_event(
                actor=request.user.username,
                action="IMAGE_REJECTED",
                target_id=image_id,
                metadata={"reason": reason},
                ip_address=request.META.get("REMOTE_ADDR")
            )
            messages.warning(request, f"Image {image_doc['filename']} has been rejected.")
            return redirect("review:pending_list")

        elif action == "CONFIRM":
            selected_modality = request.POST.get("modality", image_doc.get("modality", "CHEST_XRAY")).upper()
            requested_task = request.POST.get("task", "CHEST_XRAY_CLASSIFICATION").upper()

            # Enforce strict modality routing
            try:
                ModelRegistryService.validate_routing(selected_modality, requested_task)
            except ModalityMismatchError as err:
                messages.error(request, str(err))
                return render(request, "review/review_detail.html", {
                    "image": image_doc,
                    "quality": quality_data,
                    "image_url": f"{settings.MEDIA_URL}{image_doc['stored_path']}",
                    "selected_modality": selected_modality,
                    "selected_task": requested_task,
                })

            # Check duplicate processing prevention
            if image_doc.get("review_status") == "CONFIRMED":
                messages.info(request, "This image has already been confirmed and processed.")
                existing_analysis = AnalysisRepository.get_by_image_id(image_id)
                if existing_analysis:
                    return redirect("analysis:detail", analysis_id=existing_analysis["analysis_id"])
                return redirect("review:pending_list")

            # Mark image confirmed
            ImageRepository.confirm_image(image_id, reviewer=request.user.username, modality=selected_modality)
            if image_doc.get("session_id"):
                SessionRepository.update_status(image_doc["session_id"], "PROCESSING")

            AuditRepository.record_event(
                actor=request.user.username,
                action="IMAGE_CONFIRMED",
                target_id=image_id,
                metadata={"modality": selected_modality, "task": requested_task},
                ip_address=request.META.get("REMOTE_ADDR")
            )

            # Create analysis record and execute appropriate AI pipeline
            start_time = time.time()
            model_id_map = {
                "CHEST_XRAY_CLASSIFICATION": "cxr-resnet18-classifier",
                "BRAIN_TUMOR_SEGMENTATION": "brain-mri-unet-segmenter",
                "LUNG_NODULE_DETECTION": "lung-ct-nodule-detector",
                "COLORIZATION": "radiomic-colorizer-v1",
            }
            model_id = model_id_map.get(requested_task, "cxr-resnet18-classifier")

            analysis_doc = AnalysisRepository.create_analysis_record(
                image_id=image_id,
                task=requested_task,
                modality=selected_modality,
                model_id=model_id,
                model_version="1.0.0"
            )

            try:
                # 1. Pipeline: Chest X-Ray Pathology + Grad-CAM
                if requested_task == "CHEST_XRAY_CLASSIFICATION":
                    pred_res = ChestXRayInferenceService.predict(abs_image_path)
                    gradcam_res = GradCAMService.generate_heatmap(
                        image_path=abs_image_path,
                        output_dir=os.path.join(settings.MEDIA_ROOT, "gradcam"),
                        image_id=image_id
                    )
                    uncertainty_res = UncertaintyEvaluator.evaluate_classification_uncertainty(
                        predictions=pred_res["predictions"],
                        quality_score=quality_data.get("score", 85.0)
                    )
                    elapsed = time.time() - start_time
                    AnalysisRepository.complete_analysis(
                        analysis_id=analysis_doc["analysis_id"],
                        primary_finding=pred_res["primary_finding"],
                        confidence=pred_res["confidence"],
                        predictions=pred_res["predictions"],
                        quality_assessment=quality_data,
                        uncertainty=uncertainty_res,
                        gradcam_path=gradcam_res["gradcam_rel_path"],
                        severity=pred_res["severity"],
                        execution_time_seconds=elapsed
                    )

                # 2. Pipeline: Brain MRI Tumor Segmentation
                elif requested_task == "BRAIN_TUMOR_SEGMENTATION":
                    brain_res = BrainMRISegmentationService.segment_tumor(
                        image_path=abs_image_path,
                        output_dir=os.path.join(settings.MEDIA_ROOT, "brain_masks"),
                        image_id=image_id
                    )
                    elapsed = time.time() - start_time
                    AnalysisRepository.complete_analysis(
                        analysis_id=analysis_doc["analysis_id"],
                        primary_finding=brain_res["primary_finding"],
                        confidence=brain_res["confidence"],
                        predictions=[{"label": "Intracranial Lesion", "probability": brain_res["confidence"]}],
                        quality_assessment=quality_data,
                        segmentation_results={
                            "tumor_pixels": brain_res["tumor_pixels"],
                            "tumor_area_percentage": brain_res["tumor_area_percentage"],
                            "lesion_count": brain_res["lesion_count"],
                            "lesions": brain_res["lesions"],
                            "mask_path": brain_res["mask_rel_path"],
                            "overlay_path": brain_res["overlay_rel_path"],
                        },
                        severity=brain_res["severity"],
                        execution_time_seconds=elapsed
                    )

                # 3. Pipeline: Lung CT Nodule Detection
                elif requested_task == "LUNG_NODULE_DETECTION":
                    lung_res = LungCTNoduleDetector.detect_nodules(
                        image_path=abs_image_path,
                        output_dir=os.path.join(settings.MEDIA_ROOT, "lung_nodules"),
                        image_id=image_id
                    )
                    elapsed = time.time() - start_time
                    AnalysisRepository.complete_analysis(
                        analysis_id=analysis_doc["analysis_id"],
                        primary_finding=lung_res["primary_finding"],
                        confidence=lung_res["confidence"],
                        predictions=[{"label": "Pulmonary Nodule", "probability": lung_res["confidence"]}],
                        quality_assessment=quality_data,
                        detection_results={
                            "nodule_count": lung_res["nodule_count"],
                            "nodules": lung_res["nodules"],
                            "overlay_path": lung_res["overlay_rel_path"],
                        },
                        severity=lung_res["severity"],
                        execution_time_seconds=elapsed
                    )

                # 4. Pipeline: Medical Image Colorization Studio
                elif requested_task == "COLORIZATION":
                    color_res = MedicalColorizationService.colorize_image(
                        image_path=abs_image_path,
                        output_dir=os.path.join(settings.MEDIA_ROOT, "colorized"),
                        image_id=image_id,
                        palette_mode="SPECTRAL_RADIOMIC"
                    )
                    ColorizationRepository.create_record(
                        image_id=image_id,
                        colorized_path=color_res["colorized_rel_path"],
                        comparison_path=color_res["comparison_rel_path"],
                        model_id="radiomic-colorizer-v1",
                        palette_mode=color_res["palette_mode"],
                        parameters=color_res["parameters"]
                    )
                    elapsed = time.time() - start_time
                    AnalysisRepository.complete_analysis(
                        analysis_id=analysis_doc["analysis_id"],
                        primary_finding="Multi-Spectral Radiomic Colorization Enhanced",
                        confidence=0.98,
                        predictions=[{"label": "Spectral Colorization", "probability": 0.98}],
                        quality_assessment=quality_data,
                        colorized_path=color_res["colorized_rel_path"],
                        severity="Normal / Enhanced Visualization",
                        execution_time_seconds=elapsed
                    )

                if image_doc.get("session_id"):
                    SessionRepository.update_status(image_doc["session_id"], "COMPLETED")

                messages.success(request, f"Image confirmed and processed successfully ({requested_task})!")
                return redirect("analysis:detail", analysis_id=analysis_doc["analysis_id"])

            except Exception as e:
                AnalysisRepository.fail_analysis(analysis_doc["analysis_id"], str(e))
                if image_doc.get("session_id"):
                    SessionRepository.update_status(image_doc["session_id"], "FAILED")
                messages.error(request, f"Processing encountered an error: {str(e)}")
                return redirect("review:detail", image_id=image_id)

    return render(request, "review/review_detail.html", {
        "image": image_doc,
        "quality": quality_data,
        "image_url": f"{settings.MEDIA_URL}{image_doc['stored_path']}",
        "selected_modality": image_doc.get("modality", "CHEST_XRAY"),
    })
