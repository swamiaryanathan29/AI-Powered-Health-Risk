"""
Router: Step 2 – Factor Extraction
POST /api/v1/factors
"""
import logging

from fastapi import APIRouter

from app.models.schemas import FactorExtractionRequest, FactorExtractionResponse
from app.services.factor_service import extract_factors

router = APIRouter(prefix="/api/v1/factors", tags=["Step 2 – Factors"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    summary="Extract risk factors from parsed answers",
    response_model=FactorExtractionResponse,
)
async def factors(body: FactorExtractionRequest):
    """
    Converts the `answers` dict (from Step 1) into a list of named risk factors.
    """
    factor_list, confidence = extract_factors(body.answers)
    return FactorExtractionResponse(factors=factor_list, confidence=confidence)
