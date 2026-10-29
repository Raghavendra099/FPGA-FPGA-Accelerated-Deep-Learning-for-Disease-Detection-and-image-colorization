"""
Grad-CAM (Gradient-weighted Class Activation Mapping) Service.
Generates explainable AI saliency heatmaps for deep learning classification models.
"""
import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, Any, Optional

from .preprocessing import prepare_classification_tensor
from .inference import ChestXRayInferenceService, THORACIC_CLASSES

class GradCAMService:
    @classmethod
    def generate_heatmap(
        cls,
        image_path: str,
        output_dir: str,
        image_id: str,
        target_class_idx: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Computes Grad-CAM saliency map for the target convolutional layer (ResNet layer4).
        Generates overlaid heatmap artifact and saves to media/gradcam/.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        orig_bgr = cv2.imread(image_path)
        if orig_bgr is None:
            raise ValueError("Failed to decode image for Grad-CAM.")

        orig_h, orig_w = orig_bgr.shape[:2]

        model = ChestXRayInferenceService.get_model()
        model.eval()

        # Hooks to capture activations and gradients from ResNet layer4
        gradients = []
        activations = []

        def backward_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0])

        def forward_hook(module, input, output):
            activations.append(output)

        target_layer = model.backbone.layer4
        f_handle = target_layer.register_forward_hook(forward_hook)
        b_handle = target_layer.register_full_backward_hook(backward_hook)

        tensor = prepare_classification_tensor(orig_bgr)
        tensor.requires_grad = True

        model.zero_grad()
        output = model(tensor)

        if target_class_idx is None:
            target_class_idx = int(torch.argmax(output, dim=1).item())

        target_label = THORACIC_CLASSES[target_class_idx]
        target_score = output[0, target_class_idx]

        # Backward pass
        target_score.backward()

        f_handle.remove()
        b_handle.remove()

        if len(gradients) == 0 or len(activations) == 0:
            raise RuntimeError("Failed capturing gradients or activations for Grad-CAM.")

        grads = gradients[0].detach()  # [1, 512, 7, 7]
        acts = activations[0].detach()  # [1, 512, 7, 7]

        # Global average pooling of gradients: alpha_k
        weights = torch.mean(grads, dim=(2, 3), keepdim=True)  # [1, 512, 1, 1]

        # Linear combination of feature maps weighted by alpha_k
        cam = torch.sum(weights * acts, dim=1).squeeze()  # [7, 7]
        cam = F.relu(cam)  # Apply ReLU

        # Normalize CAM to [0, 1]
        cam_np = cam.cpu().numpy()
        cam_max = np.max(cam_np)
        if cam_max > 0:
            cam_np = cam_np / cam_max
        else:
            cam_np = np.zeros_like(cam_np)

        # Resize heatmap to match original image dimensions
        heatmap = cv2.resize(cam_np, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
        heatmap_uint8 = np.uint8(255 * heatmap)

        # Apply JET colormap
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Blend with original grayscale scan
        # 60% original image + 40% heatmap
        overlay = cv2.addWeighted(orig_bgr, 0.60, heatmap_color, 0.40, 0)

        # Save artifact to media/gradcam/
        os.makedirs(output_dir, exist_ok=True)
        gradcam_filename = f"{image_id}_gradcam.png"
        gradcam_save_path = os.path.join(output_dir, gradcam_filename)
        cv2.imwrite(gradcam_save_path, overlay)

        # Find peak saliency region (bounding coordinate of maximum activation)
        peak_y, peak_x = np.unravel_index(np.argmax(heatmap), heatmap.shape)
        activation_centroid = [int(peak_x), int(peak_y)]

        return {
            "gradcam_rel_path": f"gradcam/{gradcam_filename}",
            "target_label": target_label,
            "target_class_idx": target_class_idx,
            "peak_activation_coordinate": activation_centroid,
            "explanation_notes": (
                "Grad-CAM visualizes spatial regions of highest convolutional gradient activation. "
                "Warm red/amber zones indicate regions contributing most positively to the model's prediction. "
                "This is an explanatory visual aid and does not constitute histopathological disease margins."
            )
        }
