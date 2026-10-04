# 🏥 AI-Powered Health Risk Profiler

> **Disclaimer**: This service is for informational / lifestyle-risk purposes only. It does **not** constitute medical advice or diagnosis.

A FastAPI backend that analyzes lifestyle survey responses (typed text or scanned forms) and produces a structured health risk profile through a 4-step AI pipeline.

---

## 📐 Architecture

```
Survey Input (text/JSON/image)
        │
        ▼
┌───────────────────┐
│  Step 1 – Parse   │  OCR (pytesseract) + key-value parser + JSON parser
│  /api/v1/parse    │  Guardrail: >50% required fields missing → 422
└────────┬──────────┘
         │ ParsedSurvey {answers, missing_fields, confidence}
         ▼
┌──────────────────────────┐
│  Step 2 – Factor Extract │  Rule-based factor detection (13 risk rules)
│  /api/v1/factors         │
└────────┬─────────────────┘
         │ [smoking, poor diet, low exercise, …]
         ▼
┌──────────────────────────┐
│  Step 3 – Risk Classify  │  Weighted scoring → low / moderate / high
│  /api/v1/risk            │  Score 0–100; thresholds: <30 low, <60 moderate
└────────┬─────────────────┘
         │ {risk_level, score, rationale}
         ▼
┌──────────────────────────┐
│  Step 4 – Recommend      │  Factor → actionable guidance mapping
│  /api/v1/recommendations │  Non-diagnostic lifestyle advice
└──────────────────────────┘
         │
         ▼
  {risk_level, factors, recommendations, status}

One-shot endpoint: POST /api/v1/analyze/text  or  /api/v1/analyze/image
```

### Tech Stack
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.111+ |
| Server | Uvicorn |
| Validation | Pydantic v2 |
| OCR | pytesseract + Tesseract-OCR |
| Image processing | Pillow |
| Testing | pytest + HTTPX |
| Containerisation | Docker + Docker Compose |
| Tunnelling (demo) | ngrok |

---

## 🚀 Quick Start

### Option A – Local (no Docker)

**Prerequisites**: Python 3.11+

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/health-risk-profiler.git
cd health-risk-profiler

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install Tesseract for real image OCR
#    macOS:   brew install tesseract
#    Ubuntu:  sudo apt install tesseract-ocr
#    Without tesseract, image endpoints return a mock OCR response.

# 5. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API is now live at **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**  
🟣 **Plum Health Insurance Portal UI**: **http://localhost:8000/plum** (or `/ui`)

---

### Option B – Docker

```bash
docker compose up --build
```

---

### Option C – Public URL with ngrok

```bash
# Terminal 1 – start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 – expose it
ngrok http 8000
```

Use the `https://<id>.ngrok-free.app` URL as the base URL for all requests below.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output: **17 tests passed**.

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info & links |
| GET | `/health` | Health check |
| GET | `/plum` (or `/ui`) | 🟣 Plum Health Insurance Underwriting Portal (Web UI) |
| POST | `/api/v1/parse/text` | Step 1 – Parse text/JSON survey |
| POST | `/api/v1/parse/image` | Step 1 – Parse scanned image (OCR) |
| POST | `/api/v1/factors` | Step 2 – Extract risk factors |
| POST | `/api/v1/risk` | Step 3 – Classify risk level |
| POST | `/api/v1/recommendations` | Step 4 – Generate recommendations |
| POST | `/api/v1/analyze/text` | 🔀 Full pipeline (text/JSON) |
| POST | `/api/v1/analyze/image` | 🔀 Full pipeline (image) |


---

## 🔌 Sample curl Requests

> Replace `http://localhost:8000` with your ngrok URL if running remotely.

---

### ✅ Step 1a — Parse JSON survey

```bash
curl -s -X POST http://localhost:8000/api/v1/parse/text \
  -H "Content-Type: application/json" \
  -d '{"json_data": {"age":42,"smoker":true,"exercise":"rarely","diet":"high sugar"}}' \
  | python3 -m json.tool
```

**Expected response:**
```json
{
  "answers": {"age": 42, "smoker": true, "exercise": "rarely", "diet": "high sugar"},
  "missing_fields": [],
  "confidence": 0.87
}
```

---

### ✅ Step 1b — Parse raw text survey

```bash
curl -s -X POST http://localhost:8000/api/v1/parse/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Age: 42\nSmoker: yes\nExercise: rarely\nDiet: high sugar"}' \
  | python3 -m json.tool
```

---

### ⚠️ Step 1c — Guardrail (incomplete survey)

```bash
curl -s -X POST http://localhost:8000/api/v1/parse/text \
  -H "Content-Type: application/json" \
  -d '{"json_data": {"age": 42}}' \
  | python3 -m json.tool
```

**Expected response (HTTP 422):**
```json
{
  "status": "incomplete_profile",
  "reason": ">50% fields missing (3/4 required fields absent)"
}
```

---

### ✅ Step 1d — Parse image (OCR)

```bash
# First, generate a test image:
python3 sample_inputs/generate_test_image.py

curl -s -X POST http://localhost:8000/api/v1/parse/image \
  -F "file=@sample_inputs/survey_form.png" \
  | python3 -m json.tool
```

---

### ✅ Step 2 — Extract factors

```bash
curl -s -X POST http://localhost:8000/api/v1/factors \
  -H "Content-Type: application/json" \
  -d '{"answers": {"age":42,"smoker":true,"exercise":"rarely","diet":"high sugar"}}' \
  | python3 -m json.tool
```

**Expected response:**
```json
{
  "factors": ["smoking", "poor diet", "low exercise"],
  "confidence": 0.88
}
```

---

### ✅ Step 3 — Risk classification

```bash
curl -s -X POST http://localhost:8000/api/v1/risk \
  -H "Content-Type: application/json" \
  -d '{
    "factors": ["smoking", "poor diet", "low exercise"],
    "answers": {"age":42,"smoker":true,"exercise":"rarely","diet":"high sugar"}
  }' \
  | python3 -m json.tool
```

**Expected response:**
```json
{
  "risk_level": "high",
  "score": 78,
  "rationale": ["active smoker", "high sugar / poor diet (high sugar)", "low physical activity (rarely)"]
}
```

---

### ✅ Step 4 — Recommendations

```bash
curl -s -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "risk_level": "high",
    "factors": ["smoking", "poor diet", "low exercise"],
    "answers": {}
  }' \
  | python3 -m json.tool
```

**Expected response:**
```json
{
  "risk_level": "high",
  "factors": ["smoking", "poor diet", "low exercise"],
  "recommendations": [
    "Quit smoking — consider nicotine replacement therapy or counselling.",
    "Reduce sugar and processed food intake.",
    "Add more fruits, vegetables, and whole grains to your diet.",
    "Walk at least 30 minutes daily.",
    "Aim for 150 minutes of moderate aerobic activity per week.",
    "We strongly recommend booking an appointment with a healthcare provider soon.",
    "Do not ignore persistent symptoms — seek timely medical advice."
  ],
  "status": "ok"
}
```

---

### 🔀 Full Pipeline (one shot) — Text input

```bash
curl -s -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"json_data": {"age":42,"smoker":true,"exercise":"rarely","diet":"high sugar"}}' \
  | python3 -m json.tool
```

---

### 🔀 Full Pipeline (one shot) — Image input

```bash
curl -s -X POST http://localhost:8000/api/v1/analyze/image \
  -F "file=@sample_inputs/survey_form.png" \
  | python3 -m json.tool
```

---

### 🔥 Extended high-risk profile

```bash
curl -s -X POST http://localhost:8000/api/v1/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "json_data": {
      "age": 55, "smoker": true, "exercise": "never", "diet": "junk food",
      "alcohol": true, "bmi": 32, "stress": "high",
      "sleep_hours": 5, "blood_pressure": "high", "family_history": true
    }
  }' \
  | python3 -m json.tool
```

---

## 📁 Project Structure

```
health-risk-profiler/
├── app/
│   ├── main.py                        # FastAPI app, CORS, middleware
│   ├── models/
│   │   └── schemas.py                 # Pydantic request/response models
│   ├── routers/
│   │   ├── parse_router.py            # Step 1 – Parse
│   │   ├── factor_router.py           # Step 2 – Factors
│   │   ├── risk_router.py             # Step 3 – Risk
│   │   ├── recommendation_router.py   # Step 4 – Recommendations
│   │   └── pipeline_router.py         # Full pipeline
│   ├── services/
│   │   ├── parsing_service.py         # OCR + text/JSON parsing logic
│   │   ├── factor_service.py          # Rule-based factor extraction
│   │   ├── risk_service.py            # Weighted risk scoring
│   │   └── recommendation_service.py  # Factor → guidance mapping
│   └── utils/
│       └── ocr_utils.py               # pytesseract wrapper + mock fallback
├── tests/
│   └── test_api.py                    # 17 pytest tests (full coverage)
├── sample_inputs/
│   ├── sample_surveys.json            # Sample survey payloads
│   └── generate_test_image.py         # Script to create test PNG
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🛡️ Guardrails

| Condition | Behaviour |
|-----------|-----------|
| > 50% required fields missing | HTTP 422 `{"status":"incomplete_profile","reason":"..."}` |
| Empty file upload | HTTP 400 |
| Unsupported image format | HTTP 400 |
| OCR engine unavailable | Graceful mock fallback |

---

## 🔍 Risk Scoring

| Factor | Weight (pts) |
|--------|-------------|
| Smoking | 25 |
| Low exercise | 15 |
| Poor diet | 15 |
| Hypertension | 15 |
| Obesity | 18 |
| Age ≥ 45 | 10 |
| Alcohol use | 10 |
| High stress | 10 |
| Elevated BMI | 10 |
| Family history | 10 |
| Sleep deprivation | 8 |
| High sodium diet | 10 |

**Thresholds**: Score < 30 → `low` | Score 30–59 → `moderate` | Score ≥ 60 → `high`

---

## 🌐 Postman Collection

Import this into Postman:

1. **New Collection** → "Health Risk Profiler"
2. Set variable `base_url` = `http://localhost:8000`
3. Add requests from the curl examples above

---

*Built for the AI-Powered Health Risk Profiler internship challenge.*
