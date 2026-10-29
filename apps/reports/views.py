"""
Report views for downloading and listing generated PDF research reports.
"""
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, FileResponse
from django.contrib import messages

from database.repositories.analysis_repository import AnalysisRepository
from database.repositories.image_repository import ImageRepository
from database.repositories.report_repository import ReportRepository
from database.repositories.audit_repository import AuditRepository
from .report_generator import MedicalReportGenerator

@login_required
def list_view(request):
    """Lists all saved PDF reports."""
    reports = ReportRepository.list_recent(limit=50)
    return render(request, "reports/list.html", {"reports": reports})

@login_required
def download_report(request, analysis_id):
    """
    Generates and downloads a multi-page PDF medical research report.
    Protected with authentication and access control.
    """
    analysis_doc = AnalysisRepository.get_by_id(analysis_id)
    if not analysis_doc:
        raise Http404("Analysis record not found.")

    image_doc = ImageRepository.get_by_image_id(analysis_doc["image_id"])
    if not image_doc:
        raise Http404("Associated medical image not found.")

    # Check if report already exists in database
    existing_report = ReportRepository.get_by_analysis_id(analysis_id)
    if existing_report and os.path.exists(os.path.join(settings.MEDIA_ROOT, existing_report["pdf_path"])):
        pdf_path = os.path.join(settings.MEDIA_ROOT, existing_report["pdf_path"])
    else:
        # Generate new PDF report
        report_filename = f"SmartMed_Report_{analysis_id}.pdf"
        rel_pdf_path = f"reports/{report_filename}"
        abs_pdf_path = os.path.join(settings.MEDIA_ROOT, rel_pdf_path)

        MedicalReportGenerator.generate_pdf(
            analysis_doc=analysis_doc,
            image_doc=image_doc,
            output_filepath=abs_pdf_path,
            media_root=settings.MEDIA_ROOT
        )

        file_size = os.path.getsize(abs_pdf_path)
        existing_report = ReportRepository.create_report_record(
            analysis_id=analysis_id,
            pdf_path=rel_pdf_path,
            report_title=f"SmartMed AI Report - {analysis_doc.get('primary_finding', 'Analysis')}",
            generated_by=request.user.username,
            file_size_bytes=file_size,
            page_count=3
        )

    AuditRepository.record_event(
        actor=request.user.username,
        action="REPORT_DOWNLOADED",
        target_id=analysis_id,
        metadata={"filename": os.path.basename(existing_report["pdf_path"])},
        ip_address=request.META.get("REMOTE_ADDR")
    )

    pdf_file = open(os.path.join(settings.MEDIA_ROOT, existing_report["pdf_path"]), "rb")
    response = FileResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{os.path.basename(existing_report["pdf_path"])}"'
    return response
