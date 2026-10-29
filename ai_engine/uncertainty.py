"""
Prediction Reliability and Uncertainty Assessment Service.
Calculates Shannon entropy, top-margin confidence, and review-required thresholds.
"""
import numpy as np
from typing import Dict, Any, List

class UncertaintyEvaluator:
    @classmethod
    def evaluate_classification_uncertainty(
        cls,
        predictions: List[Dict[str, Any]],
        quality_score: float = 85.0
    ) -> Dict[str, Any]:
        """
        Evaluates prediction reliability and uncertainty for multi-class medical predictions.
        Distinguishes maximum softmax probability from full distribution entropy.
        """
        probs = [p.get("probability", 0.0) for p in predictions]
        probs = np.array(probs, dtype=np.float64)
        # Re-normalize just in case
        probs = probs / (np.sum(probs) + 1e-9)

        num_classes = len(probs)
        # Shannon Entropy H(p) = -sum(p * log2(p))
        # Filter zero elements to prevent log(0)
        nonzero_probs = probs[probs > 1e-7]
        shannon_entropy = -float(np.sum(nonzero_probs * np.log2(nonzero_probs)))

        # Maximum possible entropy for uniform distribution = log2(K)
        max_entropy = float(np.log2(max(2, num_classes)))
        normalized_entropy = float(shannon_entropy / max_entropy)

        # Sorted probabilities
        sorted_probs = np.sort(probs)[::-1]
        top1_prob = float(sorted_probs[0])
        top2_prob = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
        prediction_margin = float(top1_prob - top2_prob)

        # Determine Review Status
        review_reasons = []
        review_required = False

        if normalized_entropy > 0.65:
            review_required = True
            review_reasons.append("High predictive entropy across candidate pathology classes.")

        if prediction_margin < 0.18:
            review_required = True
            review_reasons.append(f"Narrow confidence margin ({prediction_margin:.2f}) between top competing diagnoses.")

        if quality_score < 60.0:
            review_required = True
            review_reasons.append("Image quality warnings (contrast/blur) degrade inference reliability.")

        if top1_prob < 0.50:
            review_required = True
            review_reasons.append("Top class probability is below decisive threshold (< 50%).")

        if review_required:
            reliability_status = "REQUIRES_FURTHER_REVIEW"
            status_badge = "Review Recommended"
        else:
            reliability_status = "RELIABLE_CONFIDENCE"
            status_badge = "High Reliability"

        return {
            "reliability_status": reliability_status,
            "status_badge": status_badge,
            "review_required": review_required,
            "review_reasons": review_reasons,
            "shannon_entropy_bits": round(shannon_entropy, 3),
            "normalized_entropy": round(normalized_entropy, 3),
            "prediction_margin": round(prediction_margin, 3),
            "epistemic_uncertainty_score": round(normalized_entropy * (1.0 - prediction_margin), 3),
            "explanation": (
                "Reliability is quantified via Shannon distribution entropy and probability margin. "
                "Low entropy and high margin indicate decisive model agreement, whereas high entropy "
                "triggers a mandatory human review requirement."
            )
        }
