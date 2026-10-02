"""
Router: Full Pipeline
POST /api/v1/analyze/text   – end-to-end from raw text / JSON
POST /api/v1/analyze/image  – end-to-end from uploaded image
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models.schemas import (
    FactorExtractionResponse,
    FullPipelineResponse,
    ParsedSurvey,
    RecommendationsResponse,
    RiskClassificationResponse,
    SurveyTextInput,
)
from app.services.factor_service import extract_factors
from app.services.parsing_service import parse_survey
from app.services.recommendation_service import generate_recommendations
from app.services.risk_service import classify_risk

router = APIRouter(prefix="/api/v1/analyze", tags=["Full Pipeline"])
logger = logging.getLogger(__name__)


def _run_pipeline(answers: Dict[str, Any], missing: list, confidence: float) -> FullPipelineResponse:
    """Run steps 2-4 on already-parsed answers."""
    # Step 2 – Factors
    factors, factor_conf = extract_factors(answers)

    # Step 3 – Risk
    risk_level, score, rationale = classify_risk(factors, answers)

    # Step 4 – Recommendations
    recs = generate_recommendations(risk_level, factors, answers)

    return FullPipelineResponse(
        parsed=ParsedSurvey(answers=answers, missing_fields=missing, confidence=confidence),
        factors=FactorExtractionResponse(factors=factors, confidence=factor_conf),
        risk=RiskClassificationResponse(risk_level=risk_level, score=score, rationale=rationale),
        recommendations=RecommendationsResponse(
            risk_level=risk_level,
            factors=factors,
            recommendations=recs,
            status="ok",
        ),
    )


@router.post(
    "/text",
    summary="End-to-end pipeline from text / JSON survey",
    response_model=FullPipelineResponse,
)
async def analyze_text(body: SurveyTextInput):
    """
    One-shot endpoint: parse → extract factors → classify risk → recommendations.
    Accepts raw text or JSON dict.
    """
    answers, missing, confidence, error = parse_survey(
        text=body.text,
        json_data=body.json_data,
    )
    if error:
        return JSONResponse(
            status_code=422,
            content={"status": "incomplete_profile", "reason": error},
        )
    return _run_pipeline(answers, missing, confidence)


@router.post(
    "/image",
    summary="End-to-end pipeline from scanned survey image",
    response_model=FullPipelineResponse,
)
async def analyze_image(file: UploadFile = File(...)):
    """
    One-shot endpoint: OCR → parse → extract factors → classify risk → recommendations.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    answers, missing, confidence, error = parse_survey(image_bytes=image_bytes)
    if error:
        return JSONResponse(
            status_code=422,
            content={"status": "incomplete_profile", "reason": error},
        )
    return _run_pipeline(answers, missing, confidence)
