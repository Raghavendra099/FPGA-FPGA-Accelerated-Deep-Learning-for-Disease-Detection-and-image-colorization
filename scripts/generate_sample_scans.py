"""
Generate synthetic research medical scans for testing and demonstration.
Creates Chest X-Ray, Chest CT, and Brain MRI sample images.
"""
import os
import cv2
import numpy as np

def generate_samples():
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "sample_scans")
    os.makedirs(samples_dir, exist_ok=True)

    # 1. Sample Chest X-Ray (512x512)
    cxr = np.zeros((512, 512), dtype=np.uint8)
    cv2.circle(cxr, (256, 256), 220, 70, -1)
    # Lungs
    cv2.ellipse(cxr, (175, 250), (65, 135), 10, 0, 360, 25, -1)
    cv2.ellipse(cxr, (337, 250), (65, 135), -10, 0, 360, 25, -1)
    # Heart
    cv2.ellipse(cxr, (245, 305), (65, 80), -25, 0, 360, 140, -1)
    # Ribs
    for y in range(160, 420, 35):
        cv2.ellipse(cxr, (175, y), (65, 12), 15, 0, 180, 105, 3)
        cv2.ellipse(cxr, (337, y), (65, 12), -15, 0, 180, 105, 3)
    # Spine
    cv2.rectangle(cxr, (245, 100), (267, 450), 160, -1)
    # Add slight Gaussian noise to simulate digital detector sensor
    noise = np.random.normal(0, 4, cxr.shape).astype(np.int16)
    cxr = np.clip(cxr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    cxr_path = os.path.join(samples_dir, "sample_chest_xray.png")
    cv2.imwrite(cxr_path, cxr)
    print(f"Generated: {cxr_path}")

    # 2. Sample Chest CT Slice (512x512)
    ct = np.zeros((512, 512), dtype=np.uint8)
    # Thoracic body contour
    cv2.ellipse(ct, (256, 256), (220, 180), 0, 0, 360, 95, -1)
    # Spine & sternum
    cv2.rectangle(ct, (246, 380), (266, 420), 220, -1)
    cv2.rectangle(ct, (246, 90), (266, 110), 210, -1)
    # Lung cavities (air attenuation ~ very dark)
    cv2.ellipse(ct, (165, 250), (75, 120), 0, 0, 360, 15, -1)
    cv2.ellipse(ct, (347, 250), (75, 120), 0, 0, 360, 15, -1)
    # Pulmonary vessels (small white branches)
    for pt in [(150, 220), (180, 260), (330, 240), (360, 280), (170, 310)]:
        cv2.circle(ct, pt, 4, 160, -1)
    # Focal pulmonary nodule (7mm spherical density in right lung field)
    cv2.circle(ct, (155, 270), 8, 195, -1)
    ct_path = os.path.join(samples_dir, "sample_chest_ct.png")
    cv2.imwrite(ct_path, ct)
    print(f"Generated: {ct_path}")

    # 3. Sample Brain MRI Axial Slice (512x512)
    mri = np.zeros((512, 512), dtype=np.uint8)
    # Skull / cranium outer contour
    cv2.ellipse(mri, (256, 256), (195, 230), 0, 0, 360, 220, 4)
    # Brain parenchyma (cerebral hemispheres)
    cv2.ellipse(mri, (256, 256), (185, 220), 0, 0, 360, 115, -1)
    # Ventricular system (CSF filled lateral ventricles ~ dark on T1)
    cv2.ellipse(mri, (235, 250), (18, 55), 10, 0, 360, 35, -1)
    cv2.ellipse(mri, (277, 250), (18, 55), -10, 0, 360, 35, -1)
    # Interhemispheric fissure
    cv2.line(mri, (256, 45), (256, 465), 55, 2)
    # Hyperintense contrast-enhancing intracranial tumor lesion (left temporal-parietal lobe)
    cv2.circle(mri, (325, 290), 28, 245, -1)
    cv2.circle(mri, (335, 280), 16, 215, -1)  # Irregular tumor core
    mri_path = os.path.join(samples_dir, "sample_brain_mri.png")
    cv2.imwrite(mri_path, mri)
    print(f"Generated: {mri_path}")

if __name__ == "__main__":
    generate_samples()
