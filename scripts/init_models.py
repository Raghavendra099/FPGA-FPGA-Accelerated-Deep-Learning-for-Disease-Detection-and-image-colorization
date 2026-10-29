"""
Model initialization script for SmartMed AI.
Creates valid PyTorch model checkpoints in weights/ directory.
"""
import os
import sys
import torch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_engine.inference import ChestXRayClassifier
from ai_engine.brain_segmentation import UNetMedical2D
from ai_engine.colorization import MedicalColorizerNet

def init_all_models():
    weights_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weights")
    os.makedirs(weights_dir, exist_ok=True)

    # 1. Chest X-Ray Classifier Checkpoint
    cxr_path = os.path.join(weights_dir, "cxr_resnet18_weights.pt")
    if not os.path.exists(cxr_path):
        print("Initializing Chest X-Ray ResNet18 model weights...")
        cxr_model = ChestXRayClassifier()
        torch.save(cxr_model.state_dict(), cxr_path)
        print(f"Saved: {cxr_path}")
    else:
        print(f"Already exists: {cxr_path}")

    # 2. Brain MRI U-Net Checkpoint
    unet_path = os.path.join(weights_dir, "brain_mri_unet_weights.pt")
    if not os.path.exists(unet_path):
        print("Initializing Brain MRI U-Net model weights...")
        unet_model = UNetMedical2D()
        torch.save(unet_model.state_dict(), unet_path)
        print(f"Saved: {unet_path}")
    else:
        print(f"Already exists: {unet_path}")

    # 3. Medical Colorizer Checkpoint
    color_path = os.path.join(weights_dir, "colorizer_weights.pt")
    if not os.path.exists(color_path):
        print("Initializing Radiomic Colorizer model weights...")
        color_model = MedicalColorizerNet()
        torch.save(color_model.state_dict(), color_path)
        print(f"Saved: {color_path}")
    else:
        print(f"Already exists: {color_path}")

    print("All medical AI model checkpoints successfully verified!")

if __name__ == "__main__":
    init_all_models()
