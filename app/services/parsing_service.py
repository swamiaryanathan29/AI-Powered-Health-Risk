"""
Parsing service – Step 1.
Ingests text, JSON dict, or raw image bytes and returns a ParsedSurvey.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.utils.ocr_utils import extract_text_from_image_bytes, parse_key_value_text

logger = logging.getLogger(__name__)

# ── Required and optional survey fields ────────────────────────────────────
REQUIRED_FIELDS = ["age", "smoker", "exercise", "diet"]
OPTIONAL_FIELDS = [
    "gender", "bmi", "blood_pressure", "cholesterol",
    "alcohol", "stress", "sleep_hours", "family_history",
]
ALL_KNOWN_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# Threshold: if more than 50 % of required fields are missing → guardrail
MISSING_THRESHOLD = 0.5


def parse_survey(
    *,
    text: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    image_bytes: Optional[bytes] = None,
) -> Tuple[Optional[Dict[str, Any]], List[str], float, Optional[str]]:
    """
    Returns (answers, missing_fields, confidence, error_reason).
    error_reason is non-None when the guardrail fires (>50 % fields missing).
    """
    raw_answers: Dict[str, Any] = {}
    confidence: float = 1.0

    # ── 1. Determine source ─────────────────────────────────────────────────
    if json_data:
        raw_answers = _normalize_keys(json_data)
        confidence = 0.95  # structured JSON – very reliable

    elif text:
        raw_answers = _parse_text(text)
        confidence = 0.92

    elif image_bytes:
        ocr_text = extract_text_from_image_bytes(image_bytes)
        raw_answers = _parse_text(ocr_text)
        confidence = 0.82  # OCR introduces uncertainty

    else:
        return None, REQUIRED_FIELDS, 0.0, ">50% fields missing (no input)"

    # ── 2. Normalise boolean / numeric fields ───────────────────────────────
    raw_answers = _coerce_known_fields(raw_answers)

    # ── 3. Identify missing required fields ─────────────────────────────────
    missing = [f for f in REQUIRED_FIELDS if f not in raw_answers or raw_answers[f] is None]

    # ── 4. Guardrail check ──────────────────────────────────────────────────
    missing_ratio = len(missing) / len(REQUIRED_FIELDS)
    if missing_ratio > MISSING_THRESHOLD:
        return None, missing, confidence, f">50% fields missing ({len(missing)}/{len(REQUIRED_FIELDS)} required fields absent)"

    # Penalise confidence for each missing optional field
    optional_missing = sum(1 for f in OPTIONAL_FIELDS if f not in raw_answers)
    confidence -= optional_missing * 0.01
    confidence = max(round(confidence, 2), 0.0)

    return raw_answers, missing, confidence, None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_text(text: str) -> Dict[str, Any]:
    """Try JSON parse first; fall back to key:value line parsing."""
    text = text.strip()
    if text.startswith("{"):
        try:
            data = json.loads(text)
            return _normalize_keys(data)
        except json.JSONDecodeError:
            pass
    return parse_key_value_text(text)


def _normalize_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """Lowercase + underscore-ify all keys."""
    return {k.lower().replace(" ", "_").replace("-", "_"): v for k, v in data.items()}


def _coerce_known_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Type-coerce well-known fields for consistent downstream processing."""
    out = dict(data)

    # age → int
    if "age" in out:
        try:
            out["age"] = int(float(str(out["age"])))
        except (ValueError, TypeError):
            out["age"] = None

    # smoker / alcohol / family_history → bool
    for bool_field in ("smoker", "alcohol", "family_history"):
        if bool_field in out:
            v = out[bool_field]
            if isinstance(v, bool):
                pass
            elif isinstance(v, str):
                out[bool_field] = v.lower() in ("yes", "true", "1")
            elif isinstance(v, (int, float)):
                out[bool_field] = bool(v)

    # exercise / diet / stress / sleep_hours → lowercase str
    for str_field in ("exercise", "diet", "stress", "blood_pressure", "gender"):
        if str_field in out and isinstance(out[str_field], str):
            out[str_field] = out[str_field].lower().strip()

    return out
