"""
IoT Device Registry and Automated Medical Hardware Ingestion Views.
"""
import os
import secrets
from datetime import datetime
from PIL import Image
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from database.repositories.device_repository import DeviceRepository
from database.repositories.image_repository import ImageRepository
from database.repositories.audit_repository import AuditRepository

@login_required
def index_view(request):
    """IoT device management workspace."""
    if request.method == "POST":
        device_name = request.POST.get("name", "").strip()
        device_type = request.POST.get("device_type", "EDGE_AI_GATEWAY")

        if not device_name:
            messages.error(request, "Device name is required.")
            return redirect("devices:index")

        # Generate 32-byte secure API key
        raw_key = f"sm_dev_{secrets.token_urlsafe(32)}"
        device_doc = DeviceRepository.register_device(
            name=device_name,
            device_type=device_type,
            raw_api_key=raw_key,
            registered_by=request.user.username,
            metadata={"ip_origin": request.META.get("REMOTE_ADDR")}
        )

        AuditRepository.record_event(
            actor=request.user.username,
            action="DEVICE_REGISTERED",
            target_id=device_doc["device_id"],
            metadata={"device_type": device_type},
            ip_address=request.META.get("REMOTE_ADDR")
        )

        messages.success(request, f"Device registered successfully! API Key: {raw_key} (Save this key now; it will not be displayed again).")
        return render(request, "devices/index.html", {
            "devices": DeviceRepository.list_devices(),
            "new_api_key": raw_key,
            "new_device_id": device_doc["device_id"],
        })

    devices = DeviceRepository.list_devices()
    return render(request, "devices/index.html", {"devices": devices})

@csrf_exempt
def api_device_ingest(request):
    """
    Automated REST API ingestion endpoint for external IoT gateways,
    digital microscopes, and hospital imaging stations.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    api_key = request.headers.get("X-Device-API-Key") or request.POST.get("api_key")
    if not api_key:
        return JsonResponse({"error": "Missing X-Device-API-Key authorization header."}, status=401)

    device_doc = DeviceRepository.verify_api_key(api_key)
    if not device_doc:
        return JsonResponse({"error": "Invalid or suspended device credentials."}, status=403)

    uploaded_file = request.FILES.get("image")
    if not uploaded_file:
        return JsonResponse({"error": "No image payload attached to request."}, status=400)

    # Validate image format and dimensions
    try:
        img = Image.open(uploaded_file)
        width, height = img.size
        img_format = img.format or "JPEG"
    except Exception:
        return JsonResponse({"error": "Invalid or corrupted image format."}, status=400)

    modality = request.POST.get("modality", "OTHER").upper()

    clean_filename = f"iot_{device_doc['device_id']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name.replace(' ', '_')}"
    save_path = os.path.join(settings.MEDIA_ROOT, "uploads", clean_filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "wb+") as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)

    rel_stored_path = f"uploads/{clean_filename}"

    image_record = ImageRepository.create_image_record(
        filename=uploaded_file.name,
        stored_path=rel_stored_path,
        file_size_bytes=uploaded_file.size,
        format_name=img_format,
        dimensions=[width, height],
        session_id=None,
        modality=modality,
        source="device_api"
    )

    DeviceRepository.update_heartbeat(device_doc["device_id"])

    AuditRepository.record_event(
        actor=device_doc["device_id"],
        action="DEVICE_INGEST_SUCCESS",
        target_id=image_record["image_id"],
        metadata={"modality": modality, "device_name": device_doc["name"]},
        ip_address=request.META.get("REMOTE_ADDR")
    )

    return JsonResponse({
        "status": "success",
        "message": "Medical scan ingested successfully into Pending Review queue.",
        "image_id": image_record["image_id"],
        "device_id": device_doc["device_id"],
        "review_url": f"/review/{image_record['image_id']}/",
    })
