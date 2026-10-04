"""
Factor Extraction service – Step 2.
Converts parsed answers into a list of named health risk factors.
"""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ── Rule table: (field, condition_fn) → factor_label ───────────────────────
# Each rule is evaluated; matching rules contribute to the factor list.
_RULES: List[Tuple] = [
    # Smoking
    ("smoker",          lambda v: v is True,                    "smoking"),

    # Diet quality
    ("diet",            lambda v: isinstance(v, str) and any(
                            kw in v for kw in ("sugar", "junk", "processed", "fast food", "fatty")
                        ),                                       "poor diet"),
    ("diet",            lambda v: isinstance(v, str) and any(
                            kw in v for kw in ("high sodium", "salty", "salt")
                        ),                                       "high sodium diet"),

    # Physical activity
    ("exercise",        lambda v: isinstance(v, str) and v in (
                            "rarely", "never", "sedentary", "none", "low"
                        ),                                       "low exercise"),
    ("exercise",        lambda v: isinstance(v, str) and v in (
                            "moderate", "sometimes", "occasional"
                        ),                                       "moderate exercise"),  # mild factor

    # Age risk
    ("age",             lambda v: isinstance(v, int) and v >= 45,  "age ≥ 45"),

    # Alcohol
    ("alcohol",         lambda v: v is True,                    "alcohol use"),

    # BMI
    ("bmi",             lambda v: isinstance(v, (int, float)) and v >= 25.0, "elevated bmi"),
    ("bmi",             lambda v: isinstance(v, (int, float)) and v >= 30.0, "obesity"),  # overrides elevated

    # Stress
    ("stress",          lambda v: isinstance(v, str) and v in ("high", "very high", "extreme"),
                                                                 "high stress"),

    # Sleep
    ("sleep_hours",     lambda v: isinstance(v, (int, float)) and v < 6, "sleep deprivation"),

    # Blood pressure
    ("blood_pressure",  lambda v: isinstance(v, str) and "high" in v, "hypertension"),

    # Family history
    ("family_history",  lambda v: v is True,                    "family history of disease"),
]

# Factors that indicate mild-level risk
MILD_FACTORS = {"moderate exercise"}

# ─────────────────────────────────────────────────────────────────────────────

def extract_factors(answers: Dict[str, Any]) -> Tuple[List[str], float]:
    """
    Returns (factors, confidence).
    Confidence is reduced when several fields are absent.
    """
    factors: List[str] = []
    seen: set = set()  # deduplicate

    for field, condition, label in _RULES:
        value = answers.get(field)
        if value is not None:
            try:
                if condition(value) and label not in seen:
                    factors.append(label)
                    seen.add(label)
            except Exception:
                pass  # defensive: never crash on a rule evaluation error

    # ── Remove lower-priority duplicates (e.g. elevated bmi when obesity also matched)
    if "obesity" in factors and "elevated bmi" in factors:
        factors.remove("elevated bmi")

    # ── Confidence: penalise for missing key fields ───────────────────────
    known_fields = {"smoker", "exercise", "diet", "age", "bmi", "alcohol"}
    provided = known_fields & set(answers.keys())
    missing_ratio = 1 - len(provided) / len(known_fields)
    confidence = round(max(0.5, 0.95 - missing_ratio * 0.3), 2)

    logger.info("Extracted factors: %s (confidence=%.2f)", factors, confidence)
    return factors, confidence
