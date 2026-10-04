"""
OCR utilities: extract text from images using pytesseract (Tesseract-OCR).
Falls back gracefully if tesseract is not installed.
"""
import logging
import re
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)

TESSERACT_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available.")
except Exception:
    logger.warning(
        "Tesseract / pytesseract not available. Image OCR will use mock extraction."
    )


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    Run OCR on raw image bytes and return extracted text.
    Falls back to a deterministic mock if tesseract is absent.
    """
    if TESSERACT_AVAILABLE:
        try:
            image = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            logger.info("OCR succeeded, extracted %d chars.", len(text))
            return text
        except Exception as exc:
            logger.error("OCR failed: %s", exc)
            raise RuntimeError(f"OCR processing failed: {exc}") from exc
    else:
        # ── Mock fallback: read any text embedded in PNG comment or return demo text ──
        logger.warning("Returning mock OCR output (tesseract unavailable).")
        return _mock_ocr_output()


def _mock_ocr_output() -> str:
    """Return a deterministic demo OCR string for testing without tesseract."""
    return (
        "Age: 42\n"
        "Smoker: yes\n"
        "Exercise: rarely\n"
        "Diet: high sugar\n"
    )


def parse_key_value_text(text: str) -> dict:
    """
    Parse 'Key: Value' style text into a dict.
    Handles noisy lines, extra whitespace, and varied separators (: or =).
    """
    result: dict = {}
    lines = text.strip().splitlines()
    for line in lines:
        # Skip blank / noisy lines
        line = line.strip()
        if not line or len(line) < 3:
            continue
        # Match  key: value  or  key = value
        match = re.match(r'^([A-Za-z _\-]+)\s*[:=]\s*(.+)$', line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            result[key] = _coerce_value(value)
    return result


def _coerce_value(raw: str):
    """Attempt to coerce string to bool / int / float; fallback to str."""
    lower = raw.lower()
    if lower in ("yes", "true", "1"):
        return True
    if lower in ("no", "false", "0"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return lower  # normalise to lowercase string
