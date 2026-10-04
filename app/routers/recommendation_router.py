"""
Router: Step 4 – Recommendations
POST /api/v1/recommendations
"""
import logging

from fastapi import APIRouter

from app.models.schemas import RecommendationsRequest, RecommendationsResponse
from app.services.recommendation_service import generate_recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["Step 4 – Recommendations"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    summary="Generate actionable lifestyle recommendations",
    response_model=RecommendationsResponse,
)
async def recommendations(body: RecommendationsRequest):
    """
    Generates actionable, non-diagnostic lifestyle guidance based on
    risk level and identified factors.
    """
    recs = generate_recommendations(body.risk_level, body.factors, body.answers or {})
    return RecommendationsResponse(
        risk_level=body.risk_level,
        factors=body.factors,
        recommendations=recs,
        status="ok",
    )
