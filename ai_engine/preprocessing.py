"""
Medical Image Preprocessing Service.
Provides contrast enhancement, adaptive CLAHE, normalization, and tensor conversions.
"""
import os
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

def load_medical_image_bgr(image_path: str) -> np.ndarray:
    """Loads an image safely using OpenCV in BGR format."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Medical scan file not found: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Unable to decode image file at: {image_path}")
    return img

def load_medical_image_gray(image_path: str) -> np.ndarray:
    """Loads image as a single-channel grayscale 8-bit array."""
    img_bgr = load_medical_image_bgr(image_path)
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

def apply_clahe_contrast(gray_img: np.ndarray, clip_limit: float = 2.5, tile_grid_size=(8, 8)) -> np.ndarray:
    """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(gray_img)

def prepare_classification_tensor(img_bgr: np.ndarray, target_size=(224, 224)) -> torch.Tensor:
    """Transforms image to PyTorch normalized tensor suitable for CNN backbones."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    transform = transforms.Compose([
        transforms.Resize(target_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(pil_img).unsqueeze(0)  # [1, 3, H, W]

def prepare_segmentation_tensor(gray_img: np.ndarray, target_size=(256, 256)) -> torch.Tensor:
    """Transforms grayscale medical scan to 1-channel tensor [1, 1, 256, 256]."""
    resized = cv2.resize(gray_img, target_size, interpolation=cv2.INTER_AREA)
    norm = resized.astype(np.float32) / 255.0
    tensor = torch.from_numpy(norm).unsqueeze(0).unsqueeze(0)
    return tensor
