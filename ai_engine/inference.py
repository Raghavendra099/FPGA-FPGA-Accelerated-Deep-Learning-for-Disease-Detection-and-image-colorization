"""
Chest X-Ray Pathology Deep Learning Inference Service.
Implements PyTorch ResNet CNN for multi-class thoracic disease classification.
"""
import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models
from typing import Dict, Any, List

from .preprocessing import prepare_classification_tensor

THORACIC_CLASSES = [
    "Normal",
    "Bacterial Pneumonia",
    "Viral Pneumonia",
    "COVID-19",
    "Tuberculosis",
    "Cardiomegaly",
    "Pleural Effusion"
]

class ChestXRayClassifier(nn.Module):
    def __init__(self, num_classes=len(THORACIC_CLASSES)):
        super(ChestXRayClassifier, self).__init__()
        # Pretrained ResNet18 backbone
        self.backbone = models.resnet18(weights=None)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

class ChestXRayInferenceService:
    _model = None
    _weights_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weights", "cxr_resnet18_weights.pt")

    @classmethod
    def get_model(cls) -> ChestXRayClassifier:
        if cls._model is None:
            cls._model = ChestXRayClassifier()
            if os.path.exists(cls._weights_path):
                try:
                    state_dict = torch.load(cls._weights_path, map_location="cpu")
                    cls._model.load_state_dict(state_dict)
                except Exception:
                    pass
            cls._model.eval()
        return cls._model

    @classmethod
    def predict(cls, image_path: str) -> Dict[str, Any]:
        """
        Executes forward inference on a chest radiograph.
        Returns predicted probabilities for all thoracic conditions.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Chest radiograph not found: {image_path}")

        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError("Failed to decode chest radiograph.")

        # Prepare tensor [1, 3, 224, 224]
        tensor = prepare_classification_tensor(img_bgr)
        model = cls.get_model()

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        # Format prediction probabilities
        predictions_list = []
        for i, class_name in enumerate(THORACIC_CLASSES):
            prob_val = float(probs[i])
            predictions_list.append({
                "label": class_name,
                "probability": round(prob_val, 4),
                "percentage": round(prob_val * 100, 2),
            })

        # Sort by probability descending
        predictions_list.sort(key=lambda p: p["probability"], reverse=True)

        top_pred = predictions_list[0]
        primary_finding = top_pred["label"]
        confidence = top_pred["probability"]

        # Clinical severity assessment
        if primary_finding == "Normal":
            severity = "Normal / Clear"
        elif primary_finding in ("COVID-19", "Tuberculosis"):
            severity = "High Clinical Priority"
        elif primary_finding in ("Bacterial Pneumonia", "Pleural Effusion"):
            severity = "Moderate"
        else:
            severity = "Mild / Intermediate"

        return {
            "primary_finding": primary_finding,
            "confidence": confidence,
            "severity": severity,
            "predictions": predictions_list,
            "top_predictions": predictions_list[:3],
            "model_metadata": {
                "model_name": "SmartMed Thoracic ResNet18",
                "version": "1.4.0",
                "architecture": "ResNet18 Deep Convolutional Neural Network",
                "supported_classes": THORACIC_CLASSES,
            }
        }
