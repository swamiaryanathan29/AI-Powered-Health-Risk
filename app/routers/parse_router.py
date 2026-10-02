"""
Router: Step 1 – OCR / Text Parsing
POST /api/v1/parse/text   – accepts JSON body with text or json_data
POST /api/v1/parse/image  – accepts multipart image upload
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models.schemas import IncompleteProfileError, ParsedSurvey, SurveyTextInput
from app.services.parsing_service import parse_survey

router = APIRouter(prefix="/api/v1/parse", tags=["Step 1 – Parse"])
logger = logging.getLogger(__name__)


@router.post(
    "/text",
    summary="Parse text / JSON survey input",
    response_model=ParsedSurvey,
    responses={422: {"model": IncompleteProfileError}},
)
async def parse_text(body: SurveyTextInput):
    """
    Accepts either:
    - `text`: raw multi-line 'Key: Value' survey text (or a JSON string)
    - `json_data`: pre-parsed JSON dict
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

    return ParsedSurvey(answers=answers, missing_fields=missing, confidence=confidence)


@router.post(
    "/image",
    summary="Parse scanned image (OCR) survey",
    response_model=ParsedSurvey,
    responses={422: {"model": IncompleteProfileError}},
)
async def parse_image(file: UploadFile = File(..., description="PNG/JPG survey image")):
    """
    Upload a scanned survey form image. OCR extracts key-value fields.
    Supported formats: PNG, JPEG, TIFF, BMP.
    """
    allowed = {"image/png", "image/jpeg", "image/tiff", "image/bmp", "image/jpg"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Use PNG or JPEG.",
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    answers, missing, confidence, error = parse_survey(image_bytes=image_bytes)

    if error:
        return JSONResponse(
            status_code=422,
            content={"status": "incomplete_profile", "reason": error},
        )

    return ParsedSurvey(answers=answers, missing_fields=missing, confidence=confidence)
