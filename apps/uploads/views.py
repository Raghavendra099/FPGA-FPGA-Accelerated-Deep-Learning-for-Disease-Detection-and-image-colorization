"""
Views for QR upload session generation and mobile upload processing.
"""
import io
import base64
import os
import secrets
from datetime import datetime
from PIL import Image
import qrcode
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from database.repositories.session_repository import SessionRepository
from database.repositories.image_repository import ImageRepository
from database.repositories.audit_repository import AuditRepository

def generate_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A2540", back_color="#FFFFFF")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@login_required
def create_session_view(request):
    if request.method == "POST":
        requested_modality = request.POST.get("modality", "AUTO").upper()
        raw_token = secrets.token_urlsafe(24)

        session_doc = SessionRepository.create_session(
            raw_token=raw_token,
            created_by=request.user.username,
            expires_in_minutes=settings.QR_SESSION_EXPIRE_MINUTES,
            requested_modality=requested_modality
        )

        AuditRepository.record_event(
            actor=request.user.username,
            action="QR_SESSION_CREATED",
            target_id=session_doc["session_id"],
            metadata={"modality": requested_modality},
            ip_address=request.META.get("REMOTE_ADDR")
        )

        # Build Mobile Upload URL using local host / IP
        # Always use the auto-detected LAN IP so the phone can reach the server
        host = settings.SERVER_HOST
        port = settings.SERVER_PORT
        mobile_url = f"http://{host}:{port}/mobile/upload/{raw_token}/"

        qr_base64 = generate_qr_base64(mobile_url)

        return render(request, "uploads/session_qr.html", {
            "session": session_doc,
            "raw_token": raw_token,
            "mobile_url": mobile_url,
            "qr_base64": qr_base64,
        })

    # GET request renders session creation form
    recent_sessions = SessionRepository.list_recent_sessions(limit=10)
    return render(request, "uploads/session_create.html", {
        "recent_sessions": recent_sessions,
        "default_modality": "AUTO",
    })

def mobile_upload_page(request, token):
    session_doc = SessionRepository.get_by_raw_token(token)
    if not session_doc:
        return render(request, "uploads/mobile_upload.html", {
            "error_message": "Invalid or expired upload session token."
        }, status=404)

    if SessionRepository.is_expired(session_doc):
        SessionRepository.update_status(session_doc["session_id"], "EXPIRED")
        return render(request, "uploads/mobile_upload.html", {
            "error_message": "This QR upload session has expired. Please request a new session from the laptop portal."
        }, status=410)

    if session_doc.get("status") in ("IMAGE_UPLOADED", "COMPLETED", "PENDING_REVIEW"):
        return render(request, "uploads/mobile_upload.html", {
            "already_uploaded": True,
            "session": session_doc,
        })

    return render(request, "uploads/mobile_upload.html", {
        "session": session_doc,
        "token": token,
        "max_size_mb": settings.UPLOAD_MAX_MB,
    })

@csrf_exempt
def api_upload_image(request, token):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    session_doc = SessionRepository.get_by_raw_token(token)
    if not session_doc:
        return JsonResponse({"error": "Invalid session token."}, status=403)

    if SessionRepository.is_expired(session_doc):
        SessionRepository.update_status(session_doc["session_id"], "EXPIRED")
        return JsonResponse({"error": "Upload session has expired."}, status=410)

    if session_doc.get("upload_count", 0) >= session_doc.get("max_uploads", 1):
        return JsonResponse({"error": "This session has already received an image upload."}, status=409)

    uploaded_file = request.FILES.get("image")
    if not uploaded_file:
        return JsonResponse({"error": "No image file provided in request."}, status=400)

    # Validate file size
    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        return JsonResponse({"error": f"Image exceeds maximum size limit of {settings.UPLOAD_MAX_MB}MB."}, status=413)

    # Validate image integrity and format using PIL
    try:
        img_temp = Image.open(uploaded_file)
        img_temp.verify()
        # Reset file pointer after verify()
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        width, height = img.size
        img_format = img.format or "JPEG"
    except Exception as e:
        return JsonResponse({"error": "Corrupted or invalid image file. Please choose a valid JPEG or PNG medical scan."}, status=400)

    # Store file to media/uploads/
    clean_filename = f"{session_doc['session_id']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name.replace(' ', '_')}"
    save_path = os.path.join(settings.MEDIA_ROOT, "uploads", clean_filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    rel_stored_path = f"uploads/{clean_filename}"

    # Determine modality
    modality = session_doc.get("requested_modality", "OTHER")
    if modality == "AUTO":
        modality = "OTHER"

    # Create image record in MongoDB
    image_record = ImageRepository.create_image_record(
        filename=uploaded_file.name,
        stored_path=rel_stored_path,
        file_size_bytes=uploaded_file.size,
        format_name=img_format,
        dimensions=[width, height],
        session_id=session_doc["session_id"],
        modality=modality,
        source="mobile_qr"
    )

    # Update session status atomically
    SessionRepository.mark_image_uploaded(session_doc["session_id"], image_record["image_id"])

    # Broadcast event via Django Channels WebSockets
    try:
        channel_layer = get_channel_layer()
        event_payload = {
            "type": "session_event",
            "event": "IMAGE_UPLOADED",
            "data": {
                "session_id": session_doc["session_id"],
                "image_id": image_record["image_id"],
                "filename": uploaded_file.name,
                "image_url": f"{settings.MEDIA_URL}{rel_stored_path}",
                "dimensions": [width, height],
                "file_size_kb": round(uploaded_file.size / 1024, 1),
                "review_url": f"/review/{image_record['image_id']}/",
            },
            "message": "Image received successfully from mobile phone."
        }
        # Notify session listener
        async_to_sync(channel_layer.group_send)(f"session_{session_doc['session_id']}", event_payload)
        # Notify review queue listener
        async_to_sync(channel_layer.group_send)("review_updates", {
            "type": "review_event",
            "event": "NEW_PENDING_IMAGE",
            "data": event_payload["data"]
        })
    except Exception as ws_err:
        # Graceful degradation if channel layer has issues
        pass

    AuditRepository.record_event(
        actor="mobile_client",
        action="IMAGE_UPLOADED",
        target_id=image_record["image_id"],
        metadata={"session_id": session_doc["session_id"], "size_bytes": uploaded_file.size},
        ip_address=request.META.get("REMOTE_ADDR")
    )

    return JsonResponse({
        "status": "success",
        "image_id": image_record["image_id"],
        "message": "Your image has been received and is awaiting review.",
        "image_url": f"{settings.MEDIA_URL}{rel_stored_path}",
    })

def api_session_status(request, session_id):
    session_doc = SessionRepository.get_by_session_id(session_id)
    if not session_doc:
        return JsonResponse({"error": "Session not found"}, status=404)

    image_doc = None
    if session_doc.get("image_id"):
        image_doc = ImageRepository.get_by_image_id(session_doc["image_id"])

    return JsonResponse({
        "session_id": session_doc["session_id"],
        "status": session_doc.get("status"),
        "is_expired": SessionRepository.is_expired(session_doc),
        "image_id": session_doc.get("image_id"),
        "image_url": f"{settings.MEDIA_URL}{image_doc['stored_path']}" if image_doc else None,
        "review_url": f"/review/{session_doc.get('image_id')}/" if session_doc.get("image_id") else None,
    })

@login_required
def direct_upload_view(request):
    """Direct desktop upload workflow from laptop portal."""
    if request.method == "POST":
        uploaded_file = request.FILES.get("image")
        modality = request.POST.get("modality", "CHEST_XRAY").upper()
        if not uploaded_file:
            return JsonResponse({"error": "No file chosen"}, status=400)

        try:
            img = Image.open(uploaded_file)
            width, height = img.size
            img_format = img.format or "JPEG"
        except Exception:
            return JsonResponse({"error": "Invalid image file format."}, status=400)

        clean_filename = f"direct_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name.replace(' ', '_')}"
        save_path = os.path.join(settings.MEDIA_ROOT, "uploads", clean_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        rel_stored_path = f"uploads/{clean_filename}"
        image_record = ImageRepository.create_image_record(
            filename=uploaded_file.name,
            stored_path=rel_stored_path,
            file_size_bytes=uploaded_file.size,
            format_name=img_format,
            dimensions=[width, height],
            session_id=None,
            modality=modality,
            source="web_direct"
        )

        AuditRepository.record_event(
            actor=request.user.username,
            action="DIRECT_DESKTOP_UPLOAD",
            target_id=image_record["image_id"],
            metadata={"modality": modality},
            ip_address=request.META.get("REMOTE_ADDR")
        )

        return redirect("review:detail", image_id=image_record["image_id"])

    return render(request, "uploads/session_create.html")
