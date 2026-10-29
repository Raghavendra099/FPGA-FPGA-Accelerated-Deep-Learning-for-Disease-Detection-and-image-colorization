"""
Model Registry and Modality-Aware Routing Service.
Strictly separates imaging modalities and prevents cross-modality execution errors.
"""
from typing import Dict, Any, List

class ModalityMismatchError(ValueError):
    """Raised when an uploaded medical image modality does not match the requested AI model."""
    pass

# Modality definitions
MODALITIES = {
    "CHEST_XRAY": {
        "display_name": "Chest X-Ray (Radiography)",
        "description": "Standard thoracic PA/AP planar radiographs for pulmonary and cardiac screening.",
        "supported_tasks": ["CHEST_XRAY_CLASSIFICATION", "COLORIZATION"],
    },
    "CHEST_CT": {
        "display_name": "Chest CT (Computed Tomography)",
        "description": "High-resolution cross-sectional thoracic CT slices for lung nodule detection.",
        "supported_tasks": ["LUNG_NODULE_DETECTION", "COLORIZATION"],
    },
    "BRAIN_MRI": {
        "display_name": "Brain MRI (Magnetic Resonance Imaging)",
        "description": "Cranial T1/T2/FLAIR MRI sequences for intracranial tumor localization and segmentation.",
        "supported_tasks": ["BRAIN_TUMOR_SEGMENTATION", "COLORIZATION"],
    },
    "OTHER": {
        "display_name": "General / Unspecified Medical Scan",
        "description": "Unclassified medical scan. Reviewer must verify modality before processing.",
        "supported_tasks": ["COLORIZATION"],
    }
}

# Registered AI Model Profiles
REGISTERED_MODELS = {
    "cxr-resnet18-classifier": {
        "model_id": "cxr-resnet18-classifier",
        "name": "SmartMed Thoracic Pathology ResNet18",
        "version": "1.4.0",
        "modality": "CHEST_XRAY",
        "task": "CHEST_XRAY_CLASSIFICATION",
        "labels": [
            "Normal",
            "Bacterial Pneumonia",
            "Viral Pneumonia",
            "COVID-19",
            "Tuberculosis",
            "Cardiomegaly",
            "Pleural Effusion"
        ],
        "input_resolution": [224, 224],
        "checkpoint_filename": "cxr_resnet18_weights.pt",
        "dataset_info": "Trained on NIH ChestX-ray14 & CheXpert thoracic radiograph benchmarks.",
        "supports_gradcam": True,
        "is_active": True,
    },
    "brain-mri-unet-segmenter": {
        "model_id": "brain-mri-unet-segmenter",
        "name": "SmartMed Brain MRI Tumor U-Net",
        "version": "2.1.0",
        "modality": "BRAIN_MRI",
        "task": "BRAIN_TUMOR_SEGMENTATION",
        "labels": ["Background", "Intracranial Tumor / Lesion"],
        "input_resolution": [256, 256],
        "checkpoint_filename": "brain_mri_unet_weights.pt",
        "dataset_info": "Configured for Brain Tumor Segmentation (BraTS) T1-contrast enhanced & FLAIR MRI sequences.",
        "supports_gradcam": False,
        "is_active": True,
    },
    "lung-ct-nodule-detector": {
        "model_id": "lung-ct-nodule-detector",
        "name": "SmartMed Lung CT Nodule Detector",
        "version": "1.2.0",
        "modality": "CHEST_CT",
        "task": "LUNG_NODULE_DETECTION",
        "labels": ["Non-Nodule", "Suspicious Pulmonary Nodule"],
        "input_resolution": [512, 512],
        "checkpoint_filename": "lung_ct_nodule_weights.pt",
        "dataset_info": "Calibrated on LIDC-IDRI thoracic CT nodule screening benchmarks.",
        "supports_gradcam": False,
        "is_active": True,
    },
    "radiomic-colorizer-v1": {
        "model_id": "radiomic-colorizer-v1",
        "name": "SmartMed Radiomic Colorization Engine",
        "version": "1.1.0",
        "modality": "MULTIMODAL",  # Supports grayscale scans across modalities
        "task": "COLORIZATION",
        "labels": ["Tissue Density False-Color Map"],
        "input_resolution": [512, 512],
        "checkpoint_filename": "colorizer_weights.pt",
        "dataset_info": "Multi-spectral radiomic density calibration mapping tissue attenuation to distinct anatomical palettes.",
        "supports_gradcam": False,
        "is_active": True,
    }
}

class ModelRegistryService:
    @classmethod
    def get_model(cls, model_id: str) -> Dict[str, Any]:
        if model_id not in REGISTERED_MODELS:
            raise KeyError(f"Unknown model identifier: {model_id}")
        return REGISTERED_MODELS[model_id]

    @classmethod
    def list_models_for_modality(cls, modality: str) -> List[Dict[str, Any]]:
        modality = modality.upper()
        return [m for m in REGISTERED_MODELS.values() if m["modality"] in (modality, "MULTIMODAL")]

    @classmethod
    def validate_routing(cls, image_modality: str, requested_task: str):
        """
        Enforces strict modality separation.
        Prevents running Brain MRI through Lung CT or Chest X-Ray models.
        """
        image_modality = image_modality.upper()
        requested_task = requested_task.upper()

        if requested_task == "COLORIZATION":
            return True  # Colorization is multimodal for grayscale medical scans

        if requested_task == "CHEST_XRAY_CLASSIFICATION" and image_modality != "CHEST_XRAY":
            raise ModalityMismatchError(
                f"Modality Mismatch: Cannot run Chest X-Ray pathology model on an image marked as '{image_modality}'. "
                f"Please verify or adjust the image modality during review."
            )

        if requested_task == "LUNG_NODULE_DETECTION" and image_modality != "CHEST_CT":
            raise ModalityMismatchError(
                f"Modality Mismatch: Lung Nodule Detection requires Chest CT input, but image is marked as '{image_modality}'. "
                f"Do not send Brain MRI or planar X-rays to the CT nodule pipeline."
            )

        if requested_task == "BRAIN_TUMOR_SEGMENTATION" and image_modality != "BRAIN_MRI":
            raise ModalityMismatchError(
                f"Modality Mismatch: Brain Tumor Segmentation requires Brain MRI input, but image is marked as '{image_modality}'. "
                f"Do not send Chest X-Rays or CT scans to the cranial MRI pipeline."
            )

        return True
