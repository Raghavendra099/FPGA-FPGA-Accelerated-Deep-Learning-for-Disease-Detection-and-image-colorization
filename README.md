# SmartMed AI
**Intelligent Medical Image Colorization, Lung Disease Detection, and Tumor Analysis Platform Using Deep Learning**

> *For academic research and educational use only. AI-generated outputs are not a confirmed medical diagnosis and must not replace professional medical evaluation.*

---

## Overview
SmartMed AI is a modular, IoT-ready medical image analysis platform built with Django, PyTorch, MongoDB, and vanilla JavaScript. It supports:
- **QR-code-based mobile image upload** with real-time WebSocket transfer
- **Human-in-the-loop review** before AI processing
- **AI Medical Image Colorization** with before/after comparison slider
- **Chest X-Ray Classification** (Normal, Pneumonia, Effusion, Cardiomegaly) using ResNet-18
- **Brain MRI Tumor Segmentation** using U-Net architecture
- **Lung CT Nodule Detection** using Feature Pyramid Network
- **Explainable AI** with Grad-CAM heatmap overlays
- **Prediction Uncertainty** assessment via Monte-Carlo Dropout
- **Image Quality Assessment** (blur, noise, exposure, contrast)
- **PDF Report Generation** with ReportLab (multi-page professional reports)
- **Model Evaluation Workspace** with ROC curves, confusion matrices, cross-dataset analysis
- **IoT Device Management** with REST API for external device integration
- **MongoDB** storage for all application data (10 collections)
- **Audit Trail** logging for compliance tracking

---

## Technology Stack
| Layer | Technology |
| ------------ | ------------------------------------------------------ |
| Frontend | HTML5, CSS3, Vanilla JavaScript, SVG icons |
| Backend | Python, Django, Django REST Framework, Django Channels |
| Database | MongoDB (PyMongo) |
| AI/ML | PyTorch, OpenCV, NumPy, scikit-learn, Grad-CAM |
| Real-time | WebSockets via Django Channels (InMemoryChannelLayer) |
| Reports | ReportLab (PDF generation) |
| QR Codes | Python qrcode library |
| ASGI Server | Daphne |

---

## Project Structure
```text
SmartMed-AI/
├── manage.py                  # Django management
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables
├── .gitignore
├── README.md
│
├── config/                    # Django project settings
│   ├── settings.py            # Main settings (ASGI, MongoDB, apps)
│   ├── urls.py                # Root URL configuration
│   ├── asgi.py                # ASGI application (Daphne + Channels)
│   ├── wsgi.py                # WSGI fallback
│   └── routing.py             # WebSocket routing
│
├── database/                  # MongoDB data access layer
│   ├── mongodb.py             # PyMongo connection manager (10 collections)
│   └── repositories/          # Collection-specific repositories
│       ├── user_repository.py
│       ├── session_repository.py
│       ├── image_repository.py
│       ├── analysis_repository.py
│       ├── colorization_repository.py
│       ├── model_repository.py
│       ├── evaluation_repository.py
│       ├── report_repository.py
│       ├── device_repository.py
│       └── audit_repository.py
│
├── apps/                      # Django applications
│   ├── authentication/        # Login, registration, MongoDB auth backend
│   ├── dashboard/             # Overview dashboard with MongoDB stats
│   ├── uploads/               # QR session creation, mobile upload, WebSocket
│   ├── review/                # Human-in-the-loop review gate
│   ├── colorization/          # AI image colorization studio
│   ├── lung_analysis/         # Lung CT nodule detection
│   ├── brain_tumor/           # Brain MRI tumor segmentation
│   ├── analysis/              # Chest X-ray classification, history
│   ├── reports/               # PDF report generation (ReportLab)
│   ├── evaluations/           # Model evaluation workspace
│   ├── devices/               # IoT device management + REST API
│   └── audit/                 # Audit trail viewer
│
├── ai_engine/                 # AI/ML pipeline
│   ├── preprocessing.py       # Image preprocessing (resize, normalize)
│   ├── quality_assessment.py  # Blur, noise, exposure, contrast scoring
│   ├── model_registry.py      # Model routing + modality validation
│   ├── colorization.py        # CLAHE + spectral colorization
│   ├── brain_segmentation.py  # U-Net tumor segmentation
│   ├── lung_detection.py      # FPN nodule detection
│   ├── inference.py           # Unified inference dispatcher
│   ├── gradcam.py             # Grad-CAM explainability
│   ├── uncertainty.py         # MC-Dropout uncertainty estimation
│   └── evaluation.py          # Evaluation metrics computation
│
├── templates/                 # Django templates (14 sidebar sections)
│   ├── base.html              # Main layout with sidebar navigation
│   ├── base_mobile.html       # Mobile upload layout
│   ├── authentication/        # Login, register pages
│   ├── dashboard/             # Dashboard, audit list
│   ├── uploads/               # QR session, mobile upload
│   ├── review/                # Pending list, review detail
│   ├── colorization/          # Before/after comparison studio
│   ├── lung_analysis/         # CT analysis interface
│   ├── brain_tumor/           # MRI analysis interface
│   ├── analysis/              # Results detail, history
│   ├── reports/               # Reports list
│   ├── evaluations/           # Model evaluation workspace
│   └── devices/               # IoT device management
│
├── static/
│   ├── css/                   # Design system (variables, layout, components)
│   ├── js/                    # Frontend logic (app, websocket, mobile, review)
│   └── images/                # Static images
│
├── media/                     # User-uploaded and generated files
│   ├── uploads/               # Uploaded medical images
│   ├── colorized/             # Colorization outputs
│   ├── brain_masks/           # U-Net segmentation masks
│   ├── lung_nodules/          # Nodule detection overlays
│   ├── gradcam/               # Grad-CAM heatmaps
│   ├── reports/               # Generated PDF reports
│   └── sample_scans/          # Demo/test medical images
│
├── weights/                   # PyTorch model weights (.pt files)
│   ├── cxr_resnet18_weights.pt
│   ├── brain_mri_unet_weights.pt
│   └── colorizer_weights.pt
│
└── scripts/                   # Utility scripts
    ├── create_admin.py        # Create admin user in MongoDB
    ├── init_models.py         # Initialize model weight files
    ├── generate_sample_scans.py # Generate synthetic test scans
    └── simulate_device.py     # IoT device simulator
```

---

## Setup Instructions

### Prerequisites
- Python 3.10+ (tested with 3.14)
- MongoDB 6.0+ running on `localhost:27017`
- Git

### 1. Clone and Install Dependencies
```bash
cd "c:\Users\Raghavendra V M\Desktop\FPGA Project"
python -m pip install -r requirements.txt
```
Or install manually:
```bash
python -m pip install django djangorestframework channels daphne pymongo \
torch torchvision opencv-python Pillow numpy pandas scikit-learn \
matplotlib reportlab qrcode requests
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set your local values. Do not commit `.env`.
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=smartmed_ai
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DJANGO_SECRET_KEY=replace-with-a-random-secret
DEBUG=True
```

### 3. Initialize Database and Models
```bash
# Run Django migrations (for sessions/admin — SQLite)
python manage.py migrate --settings=config.settings

# Initialize MongoDB collections and indexes
python -c "from database.mongodb import MongoDBManager; MongoDBManager().initialize_indexes(); print('OK')"

# Create admin user
python scripts/create_admin.py

# Initialize AI model weights
python scripts/init_models.py

# Generate sample test scans
python scripts/generate_sample_scans.py
```
The admin setup script prompts for a password when one is not supplied as an argument.

### 4. Start the Server
```bash
# Option A: Django development server
python manage.py runserver 0.0.0.0:8000 --settings=config.settings

# Option B: Daphne (ASGI, supports WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 5. Access the Application
Open `http://localhost:8000` or `http://10.18.64.81:8000`

**Login credentials:**
- Username: `admin`
- Password: `adminpassword123`

---

## Feature Walkthrough

### QR Code Mobile Upload
1. Navigate to **New Image Analysis** → create an upload session
2. Scan the generated QR code with your smartphone
3. Upload a medical image from your phone
4. The image transfers to the laptop portal via WebSocket in real time

### Human Review Gate
1. All uploaded images appear in **Pending Image Review**
2. A human reviewer must approve/reject each image before AI processing
3. Reviewers can assign modality (X-Ray, CT, MRI) and processing task

### AI Analysis Pipelines
- **Chest X-Ray:** ResNet-18 classification → Grad-CAM heatmap → uncertainty
- **Brain MRI:** U-Net segmentation → binary tumor mask overlay
- **Lung CT:** FPN detection → nodule bounding boxes with confidence
- **Colorization:** CLAHE + spectral mapping → before/after slider

### PDF Reports
- Multi-page professional reports generated via ReportLab
- Includes patient info, original image, AI predictions, Grad-CAM, quality metrics

### Model Evaluation
- Select a model, dataset, and evaluation mode
- View ROC curves, confusion matrices, per-class metrics
- Cross-dataset generalization comparison charts
- Prediction uncertainty distribution

### IoT Device Management
- Register medical imaging devices with type, modality, location
- REST API for device heartbeat and image ingestion
- Activity log and status monitoring
- Run `python scripts/simulate_device.py` to test IoT ingestion

---

## MongoDB Collections
| Collection | Purpose |
|---|---|
| `users` | User profiles and authentication |
| `upload_sessions` | QR upload session tracking |
| `images` | Image metadata and file references |
| `analyses` | AI analysis results and predictions |
| `colorizations` | Colorization task records |
| `models` | Model registry and metadata |
| `evaluations` | Model evaluation results |
| `reports` | Generated report metadata |
| `devices` | IoT device registrations |
| `audit_events` | System audit trail |

---

## Design System
The UI uses CSS custom properties for consistent theming:
| Variable | Value | Purpose |
|---|---|---|
| `--primary` | `#0A2540` | Navy — navigation |
| `--accent` | `#0284C7` | Teal — highlights |
| `--background` | `#F8FAFC` | Page background |
| `--border-color` | `#E2E8F0` | Card borders |
| `--text-dark` | `#0F172A` | Primary text |
| `--text-muted` | `#64748B` | Secondary text |

---

## Important Notes
- Model weights are randomly initialized — they demonstrate correct architecture and inference pipeline but are not trained on real medical data.
- This is an academic research project — not a clinical diagnostic tool.
- MongoDB must be running before starting the application.
- WebSocket features require Daphne (ASGI) for production use; `runserver` works for basic development.
- Sample scans in `media/sample_scans/` are synthetic test images for demonstration.

---

## License
This project is developed for academic and educational purposes at the MCA level.

## Author
SmartMed AI — Intelligent Medical Imaging. Explainable AI. Reliable Research.
