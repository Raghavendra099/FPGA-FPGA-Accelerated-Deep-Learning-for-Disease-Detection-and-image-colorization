"""
External IoT Device Simulator for SmartMed AI.
Simulates a hospital imaging station or edge scanner uploading scans to the platform via REST API.
"""
import os
import sys
import requests
import numpy as np
import cv2

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from database.repositories.device_repository import DeviceRepository

def run_simulation(server_url="http://127.0.0.1:8000"):
    print("=== SmartMed AI: IoT Device Simulation Client ===")

    # 1. Fetch or create simulated device in MongoDB
    device_name = "Siemens Mobile X-Ray Terminal (Unit-4)"
    api_key = "sm_dev_simulation_test_key_secure_2026"
    existing = DeviceRepository.verify_api_key(api_key)
    if not existing:
        print("Registering simulation device in MongoDB registry...")
        DeviceRepository.register_device(
            name=device_name,
            device_type="MOBILE_XRAY",
            raw_api_key=api_key,
            registered_by="simulator",
            metadata={"location": "ICU Ward B", "firmware": "v3.4.1"}
        )

    # 2. Synthesize a clean test medical radiograph (Chest X-Ray simulation image)
    print("Synthesizing realistic simulated digital radiograph...")
    test_img = np.zeros((512, 512, 3), dtype=np.uint8)
    # Background soft tissue
    cv2.circle(test_img, (256, 256), 220, (60, 60, 60), -1)
    # Bilateral lung fields (lower attenuation)
    cv2.ellipse(test_img, (180, 260), (70, 140), 10, 0, 360, (25, 25, 25), -1)
    cv2.ellipse(test_img, (332, 260), (70, 140), -10, 0, 360, (25, 25, 25), -1)
    # Cardiac silhouette
    cv2.ellipse(test_img, (250, 310), (65, 80), -25, 0, 360, (140, 140, 140), -1)
    # Rib cage outlines
    for y in range(160, 420, 35):
        cv2.ellipse(test_img, (180, y), (65, 12), 15, 0, 180, (110, 110, 110), 3)
        cv2.ellipse(test_img, (332, y), (65, 12), -15, 0, 180, (110, 110, 110), 3)
    # Vertebral column
    cv2.rectangle(test_img, (244, 100), (268, 450), (160, 160, 160), -1)

    temp_path = os.path.join(os.path.dirname(__file__), "simulated_scan.png")
    cv2.imwrite(temp_path, test_img)
    print(f"Generated test scan: {temp_path}")

    # 3. Transmit payload to SmartMed AI Device Ingestion API
    endpoint = f"{server_url}/devices/api/ingest/"
    headers = {"X-Device-API-Key": api_key}
    data = {"modality": "CHEST_XRAY"}

    print(f"Transmitting to endpoint: {endpoint}")
    with open(temp_path, "rb") as f:
        files = {"image": ("simulated_cxr_unit4.png", f, "image/png")}
        try:
            response = requests.post(endpoint, headers=headers, data=data, files=files, timeout=10)
            print(f"Server Response Code: {response.status_code}")
            print(f"Server Response Payload: {response.json()}")
        except Exception as e:
            print(f"Simulation transmission error: {e}")
            print("Note: Start the Django server first (python manage.py runserver) to receive live HTTP transmission.")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    run_simulation(url)
