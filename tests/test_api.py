"""
Pytest test suite covering all 4 pipeline steps.
Run with:  pytest tests/ -v
"""
import json
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 – Parse text
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_text_json_string():
    payload = {"text": '{"age":42,"smoker":true,"exercise":"rarely","diet":"high sugar"}'}
    r = client.post("/api/v1/parse/text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["answers"]["age"] == 42
    assert data["answers"]["smoker"] is True
    assert "missing_fields" in data
    assert data["confidence"] > 0


def test_parse_text_json_data():
    payload = {"json_data": {"age": 42, "smoker": True, "exercise": "rarely", "diet": "high sugar"}}
    r = client.post("/api/v1/parse/text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["answers"]["diet"] == "high sugar"


def test_parse_text_key_value():
    payload = {"text": "Age: 42\nSmoker: yes\nExercise: rarely\nDiet: high sugar"}
    r = client.post("/api/v1/parse/text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["answers"]["age"] == 42
    assert data["answers"]["smoker"] is True


def test_parse_text_guardrail_incomplete():
    """More than 50% required fields missing → 422."""
    payload = {"text": "age: 30"}
    r = client.post("/api/v1/parse/text", json=payload)
    assert r.status_code == 422
    data = r.json()
    assert data["status"] == "incomplete_profile"
    assert ">50%" in data["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 – Factor extraction
# ─────────────────────────────────────────────────────────────────────────────

def test_factor_extraction_high_risk():
    payload = {
        "answers": {
            "age": 42, "smoker": True, "exercise": "rarely", "diet": "high sugar"
        }
    }
    r = client.post("/api/v1/factors", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "smoking" in data["factors"]
    assert "low exercise" in data["factors"]
    assert "poor diet" in data["factors"]
    assert 0 <= data["confidence"] <= 1


def test_factor_extraction_low_risk():
    payload = {
        "answers": {
            "age": 28, "smoker": False, "exercise": "daily", "diet": "balanced"
        }
    }
    r = client.post("/api/v1/factors", json=payload)
    assert r.status_code == 200
    data = r.json()
    # No high-risk factors expected
    assert "smoking" not in data["factors"]


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 – Risk classification
# ─────────────────────────────────────────────────────────────────────────────

def test_risk_high():
    payload = {
        "factors": ["smoking", "poor diet", "low exercise"],
        "answers": {"age": 42, "smoker": True, "exercise": "rarely", "diet": "high sugar"},
    }
    r = client.post("/api/v1/risk", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "high"
    assert data["score"] >= 50
    assert len(data["rationale"]) == 3


def test_risk_low():
    payload = {"factors": [], "answers": {"age": 25}}
    r = client.post("/api/v1/risk", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "low"
    assert data["score"] == 0


def test_risk_moderate():
    payload = {
        "factors": ["low exercise", "poor diet"],
        "answers": {"age": 35},
    }
    r = client.post("/api/v1/risk", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] in ("moderate", "high")


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 – Recommendations
# ─────────────────────────────────────────────────────────────────────────────

def test_recommendations_high():
    payload = {
        "risk_level": "high",
        "factors": ["smoking", "poor diet", "low exercise"],
        "answers": {},
    }
    r = client.post("/api/v1/recommendations", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["risk_level"] == "high"
    recs = data["recommendations"]
    assert any("smoke" in rec.lower() or "smoking" in rec.lower() for rec in recs)
    assert any("walk" in rec.lower() or "activ" in rec.lower() for rec in recs)


def test_recommendations_no_duplicates():
    payload = {
        "risk_level": "moderate",
        "factors": ["low exercise", "low exercise"],  # duplicate factor
        "answers": {},
    }
    r = client.post("/api/v1/recommendations", json=payload)
    data = r.json()
    assert len(data["recommendations"]) == len(set(data["recommendations"]))


# ─────────────────────────────────────────────────────────────────────────────
# Full Pipeline – /analyze/text
# ─────────────────────────────────────────────────────────────────────────────

def test_full_pipeline_text():
    payload = {
        "json_data": {"age": 42, "smoker": True, "exercise": "rarely", "diet": "high sugar"}
    }
    r = client.post("/api/v1/analyze/text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "parsed" in data
    assert "factors" in data
    assert "risk" in data
    assert "recommendations" in data
    assert data["risk"]["risk_level"] == "high"
    assert data["recommendations"]["status"] == "ok"


def test_full_pipeline_incomplete_guardrail():
    payload = {"json_data": {"age": 42}}
    r = client.post("/api/v1/analyze/text", json=payload)
    assert r.status_code == 422
    assert r.json()["status"] == "incomplete_profile"


def test_full_pipeline_text_raw():
    payload = {"text": "Age: 35\nSmoker: no\nExercise: moderate\nDiet: balanced"}
    r = client.post("/api/v1/analyze/text", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["risk"]["risk_level"] in ("low", "moderate", "high")


# ─────────────────────────────────────────────────────────────────────────────
# Plum Insurance UI Portal
# ─────────────────────────────────────────────────────────────────────────────

def test_plum_portal():
    r = client.get("/plum")
    assert r.status_code == 200
    assert "Plum Health Insurance" in r.text
    assert "Underwriting AI" in r.text

