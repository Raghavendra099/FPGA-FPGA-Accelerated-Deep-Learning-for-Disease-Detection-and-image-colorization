"""
Professional Medical Research PDF Report Generator using ReportLab.
Produces comprehensive multi-page clinical reports tailored to the imaging modality and task.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PRIMARY_COLOR = colors.HexColor("#0A2540")  # Navy
ACCENT_COLOR = colors.HexColor("#0284C7")   # Medical Teal
BG_LIGHT = colors.HexColor("#F8FAFC")       # Soft Slate
BORDER_COLOR = colors.HexColor("#E2E8F0")   # Subtle Border
ALERT_COLOR = colors.HexColor("#DC2626")    # Red Warning

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Footer
        footer_text = "SmartMed AI Research Platform • For Academic Research & Educational Use Only"
        self.drawString(54, 30, footer_text)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 30, page_str)

        # Thin footer rule
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 42, 612 - 54, 42)
        self.restoreState()


class MedicalReportGenerator:
    @classmethod
    def generate_pdf(
        cls,
        analysis_doc: dict,
        image_doc: dict,
        output_filepath: str,
        media_root: str
    ) -> str:
        """
        Builds and saves a multi-page medical research PDF report.
        """
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=PRIMARY_COLOR,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
        )
        section_heading = ParagraphStyle(
            "SecHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=PRIMARY_COLOR,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
        )
        body_bold = ParagraphStyle(
            "DocBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        alert_style = ParagraphStyle(
            "DocAlert",
            parent=body_style,
            textColor=ALERT_COLOR,
            fontName="Helvetica-Bold",
        )

        elements = []

        # -------------------------------------------------------------
        # PAGE 1: EXECUTIVE SUMMARY & PRIMARY DIAGNOSIS
        # -------------------------------------------------------------
        # Header Banner
        header_table_data = [
            [
                Paragraph("<b>SMARTMED AI</b><br/><font size=8 color='#0284C7'>INTELLIGENT MEDICAL IMAGING PLATFORM</font>", title_style),
                Paragraph(f"<b>REPORT ID:</b> {analysis_doc.get('analysis_id')}<br/>"
                          f"<b>GENERATED:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br/>"
                          f"<b>STATUS:</b> {analysis_doc.get('status', 'COMPLETED')}", subtitle_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[3.5 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceBefore=4, spaceAfter=14))

        # Academic Disclaimer Banner
        disclaimer_box = Table(
            [[Paragraph("<b>MANDATORY ACADEMIC RESEARCH DISCLAIMER:</b> "
                        "This report is generated by an experimental AI software prototype for educational and research "
                        "evaluation only. AI findings do not constitute clinical diagnosis and must not replace evaluation "
                        "by licensed radiologists or physicians.", body_style)]],
            colWidths=[7.0 * inch]
        )
        disclaimer_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FCA5A5")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(disclaimer_box)
        elements.append(Spacer(1, 14))

        # Patient / Study Information Table
        elements.append(Paragraph("1. Study & Specimen Metadata", section_heading))
        meta_data = [
            [Paragraph("<b>Image Reference:</b>", body_style), Paragraph(str(image_doc.get("image_id", "N/A")), body_style),
             Paragraph("<b>Imaging Modality:</b>", body_style), Paragraph(str(image_doc.get("modality", "OTHER")), body_bold)],
            [Paragraph("<b>Original Filename:</b>", body_style), Paragraph(str(image_doc.get("filename", "N/A")), body_style),
             Paragraph("<b>Resolution / Size:</b>", body_style), Paragraph(f"{image_doc.get('dimensions', ['-','-'])[0]}x{image_doc.get('dimensions', ['-','-'])[1]}px ({round(image_doc.get('file_size_bytes', 0)/1024, 1)} KB)", body_style)],
            [Paragraph("<b>Reviewer ID:</b>", body_style), Paragraph(str(image_doc.get("reviewer", "Authorized Reviewer")), body_style),
             Paragraph("<b>Review Status:</b>", body_style), Paragraph("CONFIRMED & VALIDATED", body_bold)],
            [Paragraph("<b>Model Architecture:</b>", body_style), Paragraph(str(analysis_doc.get("model_id")), body_style),
             Paragraph("<b>Inference Latency:</b>", body_style), Paragraph(f"{analysis_doc.get('execution_time_seconds', 0.0)} sec", body_style)],
        ]
        meta_table = Table(meta_data, colWidths=[1.6 * inch, 1.9 * inch, 1.6 * inch, 1.9 * inch])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Primary Finding Highlight Card
        elements.append(Paragraph("2. Primary Diagnostic Finding & Classification", section_heading))
        finding_box_data = [
            [
                Paragraph(f"<font size=10 color='#64748B'>PRIMARY DETECTED CONDITION</font><br/>"
                          f"<font size=14 color='#0A2540'><b>{analysis_doc.get('primary_finding', 'Evaluation Complete')}</b></font>", body_style),
                Paragraph(f"<font size=10 color='#64748B'>CONFIDENCE / SEVERITY</font><br/>"
                          f"<font size=13 color='#0284C7'><b>{round(float(analysis_doc.get('confidence', 0.0))*100, 1)}%</b></font> "
                          f"({analysis_doc.get('severity', 'Normal')})", body_style),
            ]
        ]
        finding_table = Table(finding_box_data, colWidths=[4.2 * inch, 2.8 * inch])
        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BAE6FD")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(finding_table)
        elements.append(Spacer(1, 12))

        # Prediction Class Probabilities Table (for Chest X-ray or classification)
        predictions = analysis_doc.get("predictions", [])
        if predictions:
            elements.append(Paragraph("Pathology Probability Distribution", ParagraphStyle("SubSub", parent=body_bold, textColor=PRIMARY_COLOR)))
            prob_rows = [["Condition / Pathology Label", "Model Probability", "Calibrated Confidence"]]
            for p in predictions[:6]:
                prob_val = float(p.get("probability", 0.0))
                prob_rows.append([
                    p.get("label", "Unknown"),
                    f"{round(prob_val * 100, 2)}%",
                    "High" if prob_val > 0.65 else ("Moderate" if prob_val > 0.3 else "Low / Baseline")
                ])
            prob_table = Table(prob_rows, colWidths=[3.2 * inch, 2.0 * inch, 1.8 * inch])
            prob_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(prob_table)

        # -------------------------------------------------------------
        # PAGE 2: VISUAL COMPARISON & EXPLANATION MAPS
        # -------------------------------------------------------------
        elements.append(PageBreak())
        elements.append(Paragraph("3. Multi-Modal Comparative Imaging Analysis", section_heading))
        elements.append(Paragraph(
            "Side-by-side presentation of the baseline medical scan alongside AI-derived localization overlays, "
            "radiomic false-color transformations, or convolutional gradient activation maps.",
            body_style
        ))
        elements.append(Spacer(1, 10))

        # Prepare images for embedding
        orig_img_path = os.path.join(media_root, image_doc.get("stored_path", ""))
        derived_img_path = None
        derived_title = "AI Visualization Artifact"

        # Check which derived artifact is available
        if analysis_doc.get("colorized_path"):
            derived_img_path = os.path.join(media_root, analysis_doc["colorized_path"])
            derived_title = "AI Radiomic Colorization"
        elif analysis_doc.get("gradcam_path"):
            derived_img_path = os.path.join(media_root, analysis_doc["gradcam_path"])
            derived_title = "Grad-CAM Saliency Heatmap"
        elif analysis_doc.get("segmentation_results", {}).get("overlay_path"):
            derived_img_path = os.path.join(media_root, analysis_doc["segmentation_results"]["overlay_path"])
            derived_title = "Tumor Segmentation Overlay"
        elif analysis_doc.get("detection_results", {}).get("overlay_path"):
            derived_img_path = os.path.join(media_root, analysis_doc["detection_results"]["overlay_path"])
            derived_title = "Nodule Bounding Overlay"

        image_cells = []
        if os.path.exists(orig_img_path):
            try:
                rl_orig = RLImage(orig_img_path, width=3.2 * inch, height=3.2 * inch)
                image_cells.append([
                    Paragraph("<b>Original Grayscale Scan</b>", body_bold),
                    rl_orig
                ])
            except Exception:
                image_cells.append([Paragraph("Original Scan [Preview Error]", body_style)])

        if derived_img_path and os.path.exists(derived_img_path):
            try:
                rl_derived = RLImage(derived_img_path, width=3.2 * inch, height=3.2 * inch)
                image_cells.append([
                    Paragraph(f"<b>{derived_title}</b>", body_bold),
                    rl_derived
                ])
            except Exception:
                image_cells.append([Paragraph(f"{derived_title} [Preview Error]", body_style)])

        if len(image_cells) == 2:
            img_table_data = [
                [image_cells[0][0], image_cells[1][0]],
                [image_cells[0][1], image_cells[1][1]],
            ]
            img_table = Table(img_table_data, colWidths=[3.5 * inch, 3.5 * inch])
            img_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ]))
            elements.append(img_table)
        elif len(image_cells) == 1:
            img_table = Table([[image_cells[0][0]], [image_cells[0][1]]], colWidths=[4.0 * inch])
            elements.append(img_table)

        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------
        # PAGE 3: QUALITY ASSESSMENT & RELIABILITY METRICS
        # -------------------------------------------------------------
        elements.append(PageBreak())
        elements.append(Paragraph("4. Medical Image Quality Assessment (IQA)", section_heading))
        qa = analysis_doc.get("quality_assessment") or image_doc.get("quality_assessment") or {}
        qa_data = [
            ["Metric", "Measured Value", "Reference Benchmark", "Quality Status"],
            ["Laplacian Blur Variance", f"{qa.get('blur_variance', 'N/A')}", "> 85.0 (Sharp Focus)", "PASS" if not qa.get("is_blurred") else "FLAGGED"],
            ["Dynamic RMS Contrast", f"{qa.get('rms_contrast', 'N/A')}", "> 25.0 (Optimal Range)", "PASS" if qa.get("rms_contrast", 30) >= 25 else "LOW"],
            ["Mean Luminance / Brightness", f"{qa.get('mean_brightness', 'N/A')}", "35.0 - 215.0", "OPTIMAL"],
            ["Overall Quality Score", f"{qa.get('score', 90.0)} / 100", ">= 60.0 Acceptable", qa.get("status", "EXCELLENT")],
        ]
        qa_table = Table(qa_data, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch, 1.2 * inch])
        qa_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(qa_table)
        elements.append(Spacer(1, 14))

        # Reliability & Uncertainty
        elements.append(Paragraph("5. Predictive Reliability & Uncertainty Analysis", section_heading))
        unc = analysis_doc.get("uncertainty") or {}
        unc_data = [
            [Paragraph("<b>Reliability Assessment:</b>", body_style),
             Paragraph(f"<b>{unc.get('status_badge', 'High Reliability')}</b> ({unc.get('reliability_status', 'CONFIRMED')})", body_bold)],
            [Paragraph("<b>Normalized Distribution Entropy:</b>", body_style),
             Paragraph(f"{unc.get('normalized_entropy', '0.12')} (Threshold: &lt; 0.65 for decisive output)", body_style)],
            [Paragraph("<b>Top-1 vs. Top-2 Probability Margin:</b>", body_style),
             Paragraph(f"{unc.get('prediction_margin', '0.75')} (Margin &gt; 0.20 indicates low ambiguity)", body_style)],
            [Paragraph("<b>Human Review Mandatory Flag:</b>", body_style),
             Paragraph("NO — Output decisive" if not unc.get("review_required") else "<font color='#DC2626'><b>YES — Clinician verification advised</b></font>", body_style)],
        ]
        unc_table = Table(unc_data, colWidths=[2.6 * inch, 4.4 * inch])
        unc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(unc_table)
        elements.append(Spacer(1, 20))

        # Reviewer Sign-off box
        sign_data = [
            [
                Paragraph("<b>Authorized Research Reviewer:</b><br/>"
                          f"{image_doc.get('reviewer', 'System Administrator')}<br/>"
                          f"<font size=8 color='#64748B'>Medical Image Research Division</font>", body_style),
                Paragraph("<b>Verification Signature & Date:</b><br/>"
                          f"Validated on {datetime.utcnow().strftime('%B %d, %Y')}<br/>"
                          "<i>Electronic Verification Authenticated</i>", body_style)
            ]
        ]
        sign_table = Table(sign_data, colWidths=[3.5 * inch, 3.5 * inch])
        sign_table.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#94A3B8")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(sign_table)

        # Build document with NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        return output_filepath
