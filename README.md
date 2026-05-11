<<<<<<< HEAD
# MRFI - Metabolic Resonance Field Intelligence

Advanced AI-powered metabolic monitoring system that leverages quantum-inspired resonance field analysis to predict diabetes risk trajectories. MRFI transforms traditional glucose monitoring into a sophisticated multi-dimensional intelligence platform that detects metabolic patterns before clinical manifestation, utilizing resonance field algorithms to analyze the complex interplay between glucose dynamics, metabolic drift, insulin sensitivity, and lifestyle factors.

## Core Features

- **Resonance Field Analysis**: Advanced quantum-inspired algorithms for metabolic pattern detection
- **Metabolic Stability Score**: Comprehensive 0-100 scale with resonance field weighting
- **Multi-dimensional State Modeling**: `STABLE`, `PREDIABETIC_EARLY`, `PREDIABETIC_LATE`, `DIABETIC` with field resonance mapping
- **Predictive Trajectory Analysis**: Holt linear models enhanced with resonance field dynamics for 30/90-day risk prediction
- **Drift Detection Algorithms**: Real-time monitoring of metabolic field deviations over 90-day windows
- **Physiologic Resonance Validation**: Multi-layer verification system with anomaly detection
- **Intelligent Intervention Engine**: AI-powered recommendations based on resonance field patterns
- **Comprehensive Audit System**: Complete measurement traceability with field resonance logging
- **Real-time Intelligence Dashboard**: Live WebSocket updates with resonance field visualization
- **Quantum-inspired Analytics**: Advanced pattern recognition for early metabolic deterioration detection

## Technology Stack

- **Backend Framework**: Flask with SQLAlchemy ORM and Flask-Migrate for database migrations
- **Resonance Analytics**: NumPy, scikit-learn with custom resonance field algorithms
- **Security Layer**: JWT authentication with bcrypt password hashing
- **Intelligence Frontend**: Vanilla JavaScript with Chart.js for resonance field visualization
- **UI Framework**: Tailwind CSS with custom resonance field theming
- **Database Engine**: SQLite (development) with PostgreSQL/MySQL production support
- **Real-time Communication**: WebSocket for live resonance field updates
- **AI/ML Components**: Custom resonance field analysis with predictive modeling

## Project Structure

```text
.
|-- run.py
|-- models.py
|-- routes/
|-- services/
|-- middleware/
|-- templates/
|-- static/
|-- seed_data.py
|-- requirements.txt
```

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template:

```bash
copy .env.example .env
```

4. Run the server:

```bash
python run.py
```

5. Open [http://localhost:5000](http://localhost:5000)

## Seed Demo Data

Generate realistic demo users and measurement histories:

```bash
python generate_sample_data.py
```

Test credentials:

- `sarah.j@example.com` / `password123`
- `raj.p@example.com` / `password123`
- `maria.g@example.com` / `password123`
- `james.c@example.com` / `password123`
- `amanda.w@example.com` / `password123`
- `chandu10@gmail.com` / `password123`

## Key API Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/measurements`
- `GET /api/measurements`
- `GET /api/measurements/stability`
- `GET /api/measurements/stability/history`
- `POST /api/measurements/food-log`
- `GET /api/recommendations`
- `POST /api/recommendations/<id>/accept`
- `POST /api/recommendations/<id>/feedback`

## MRFI Resonance Field Model

The metabolic stability score utilizes advanced resonance field analysis with weighted field components:

- **Glucose Resonance Field**: `40%` - Dynamic glucose pattern analysis with field harmonics
- **Trend Resonance Stability**: `25%` - Temporal coherence in metabolic field patterns
- **Insulin Sensitivity Resonance**: `20%` - Field interaction analysis for insulin response dynamics
- **Lifestyle Field Coherence**: `15%` - Resonance patterns from activity, sleep, and nutritional inputs

### **Resonance Field Analysis Techniques:**

- **Quantum-inspired Pattern Recognition**: Advanced glucose variability analysis with field decomposition
- **Multi-dimensional Regression**: Temporal slope analysis enhanced with resonance field dynamics
- **HOMA-IR Field Integration**: Insulin resistance proxy with resonance field correction factors
- **Lifestyle Field Synchronization**: Activity, sleep, and meal logging analyzed through resonance field theory
- **Confidence Field Modulation**: Dynamic confidence adjustment based on field coherence and data quality

### **Field Quality Metrics:**
- **Temporal Resonance**: Recency and consistency analysis with field weighting
- **Pattern Coherence**: Completeness metrics enhanced with resonance field validation
- **Predictive Field Strength**: Confidence intervals based on resonance field stability

## Production Hardening Notes

- Debug mode is controlled by `FLASK_DEBUG`
- Production startup requires non-default `SECRET_KEY` and `JWT_SECRET`
- Uploads are capped at `10 MB`
- Meal photo uploads validate image mime types
- Database exceptions trigger rollback and structured error responses
- CORS origins can be restricted with `CORS_ORIGINS`
- Websocket port is configurable through `WEBSOCKET_PORT`

## Important Medical Note

MRFI is an advanced research and engineering system for metabolic monitoring and risk estimation using resonance field analysis. This platform is designed for research, educational, and supplementary monitoring purposes only. It is not a replacement for professional medical diagnosis, medication adjustment, emergency care, or clinical decision-making. Always consult with qualified healthcare professionals for medical advice and treatment decisions.

## Viva Preparation

See [VIVA_NOTES.md](C:/Users/ThatipartiChandu/OneDrive/Dokumen/Diabaties-MRFI/VIVA_NOTES.md) for architecture, algorithm rationale, and likely discussion questions.
=======
# mini-project-MRFI
>>>>>>> 955100e28a21dc306dd08933c911581109535114
