"""
Pydantic schemas for request/response models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ─── Step 1: OCR / Text Parsing ────────────────────────────────────────────

class SurveyTextInput(BaseModel):
    """Raw text or JSON survey input."""
    text: Optional[str] = Field(None, description="Raw text survey (key:value lines)")
    json_data: Optional[Dict[str, Any]] = Field(None, description="Pre-parsed JSON survey")


class ParsedSurvey(BaseModel):
    answers: Dict[str, Any] = Field(..., description="Extracted key-value answers")
    missing_fields: List[str] = Field(..., description="Required fields not found")
    confidence: float = Field(..., ge=0.0, le=1.0)


class IncompleteProfileError(BaseModel):
    status: str = "incomplete_profile"
    reason: str


# ─── Step 2: Factor Extraction ─────────────────────────────────────────────

class FactorExtractionRequest(BaseModel):
    answers: Dict[str, Any]


class FactorExtractionResponse(BaseModel):
    factors: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


# ─── Step 3: Risk Classification ───────────────────────────────────────────

class RiskClassificationRequest(BaseModel):
    factors: List[str]
    answers: Optional[Dict[str, Any]] = {}


class RiskClassificationResponse(BaseModel):
    risk_level: str  # low | moderate | high
    score: int = Field(..., ge=0, le=100)
    rationale: List[str]


# ─── Step 4: Recommendations ───────────────────────────────────────────────

class RecommendationsRequest(BaseModel):
    risk_level: str
    factors: List[str]
    answers: Optional[Dict[str, Any]] = {}


class RecommendationsResponse(BaseModel):
    risk_level: str
    factors: List[str]
    recommendations: List[str]
    status: str = "ok"


# ─── Full Pipeline ──────────────────────────────────────────────────────────

class FullPipelineResponse(BaseModel):
    parsed: ParsedSurvey
    factors: FactorExtractionResponse
    risk: RiskClassificationResponse
    recommendations: RecommendationsResponse
