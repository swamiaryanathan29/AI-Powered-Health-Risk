"""
Router: Step 3 – Risk Classification
POST /api/v1/risk
"""
import logging

from fastapi import APIRouter

from app.models.schemas import RiskClassificationRequest, RiskClassificationResponse
from app.services.risk_service import classify_risk

router = APIRouter(prefix="/api/v1/risk", tags=["Step 3 – Risk"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    summary="Classify health risk level from factors",
    response_model=RiskClassificationResponse,
)
async def risk(body: RiskClassificationRequest):
    """
    Computes a 0–100 risk score from the extracted factors and answers,
    returning **low**, **moderate**, or **high** classification with rationale.

    ⚠️ For informational / lifestyle purposes only. Not a medical diagnosis.
    """
    level, score, rationale = classify_risk(body.factors, body.answers or {})
    return RiskClassificationResponse(
        risk_level=level,
        score=score,
        rationale=rationale,
    )
