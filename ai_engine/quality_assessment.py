"""
Medical Image Quality Assessment (IQA) Service.
Measures blur (Laplacian variance), contrast (Michelson & RMS), brightness, and resolution integrity.
"""
import cv2
import numpy as np
from typing import Dict, Any

class ImageQualityAssessment:
    @classmethod
    def evaluate(cls, image_path: str) -> Dict[str, Any]:
        """Runs automated clinical quality checks on a medical image."""
        img = cv2.imread(image_path)
        if img is None:
            return {
                "status": "REJECTED",
                "score": 0.0,
                "blur_variance": 0.0,
                "is_blurred": True,
                "mean_brightness": 0.0,
                "rms_contrast": 0.0,
                "michelson_contrast": 0.0,
                "warnings": ["File could not be decoded. Image is corrupted or invalid."],
                "recommendation": "Please upload an uncorrupted standard medical JPEG or PNG scan."
            }

        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        warnings = []

        # 1. Dimension Check
        if width < 128 or height < 128:
            warnings.append(f"Low resolution ({width}x{height}px). Minimum recommended is 256x256px.")

        # 2. Blur Assessment via Laplacian Variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurred = laplacian_var < 85.0
        if is_blurred:
            warnings.append(f"Motion blur or soft focus detected (Laplacian score: {laplacian_var:.1f}).")

        # 3. Brightness Assessment
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 30.0:
            warnings.append("Image is heavily underexposed (mean brightness < 30). Subtle tissue details may be obscured.")
        elif mean_brightness > 220.0:
            warnings.append("Image is overexposed/saturated (mean brightness > 220). Anatomical structures washed out.")

        # 4. Contrast Assessment
        rms_contrast = float(np.std(gray))
        min_val, max_val = float(np.min(gray)), float(np.max(gray))
        michelson_contrast = float((max_val - min_val) / (max_val + min_val + 1e-6))
        if rms_contrast < 25.0:
            warnings.append("Low dynamic contrast (RMS < 25). Tissue boundaries may lack differentiation.")

        # 5. Pixel Clipping / Saturation
        clipped_high = float(np.sum(gray >= 254) / gray.size) * 100
        clipped_low = float(np.sum(gray <= 1) / gray.size) * 100
        if clipped_high > 15.0:
            warnings.append(f"High pixel clipping ({clipped_high:.1f}% saturated white).")

        # Compute Composite Quality Score (0 to 100)
        score = 100.0
        if is_blurred:
            score -= 30.0
        if rms_contrast < 25.0:
            score -= 20.0
        elif rms_contrast < 40.0:
            score -= 10.0
        if mean_brightness < 35.0 or mean_brightness > 215.0:
            score -= 25.0
        if width < 256 or height < 256:
            score -= 15.0

        score = max(5.0, min(100.0, score))

        if score >= 80.0 and len(warnings) == 0:
            status = "EXCELLENT"
            rec = "Image quality is optimal for deep learning inference and radiological review."
        elif score >= 55.0:
            status = "ACCEPTABLE"
            rec = "Quality is acceptable. Proceed with standard AI inference."
        else:
            status = "WARNING_LOW_QUALITY"
            rec = "Image has quality issues (blur or contrast). Manual clinician verification strongly advised."

        return {
            "status": status,
            "score": round(score, 1),
            "dimensions": [width, height],
            "blur_variance": round(laplacian_var, 2),
            "is_blurred": is_blurred,
            "mean_brightness": round(mean_brightness, 2),
            "rms_contrast": round(rms_contrast, 2),
            "michelson_contrast": round(michelson_contrast, 3),
            "clipped_high_pct": round(clipped_high, 2),
            "clipped_low_pct": round(clipped_low, 2),
            "warnings": warnings,
            "recommendation": rec,
        }
