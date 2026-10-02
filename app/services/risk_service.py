"""
Risk Classification service – Step 3.
Computes a 0-100 risk score from extracted factors and classifies into
low / moderate / high buckets.

⚠ Non-diagnostic: scores are illustrative lifestyle-risk indicators only.
"""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ── Factor weight table (points out of 100) ─────────────────────────────────
FACTOR_WEIGHTS: Dict[str, int] = {
    "smoking":                   25,
    "poor diet":                 15,
    "high sodium diet":          10,
    "low exercise":              15,
    "moderate exercise":          5,
    "age ≥ 45":                  10,
    "alcohol use":               10,
    "elevated bmi":              10,
    "obesity":                   18,
    "high stress":               10,
    "sleep deprivation":          8,
    "hypertension":              15,
    "family history of disease": 10,
}

# ── Age-based bonus points ───────────────────────────────────────────────────
def _age_bonus(answers: Dict[str, Any]) -> int:
    age = answers.get("age")
    if not isinstance(age, int):
        return 0
    if age >= 65:
        return 8
    if age >= 55:
        return 5
    if age >= 45:
        return 2
    return 0

# ── Thresholds ────────────────────────────────────────────────────────────────
LOW_THRESHOLD      = 25   # score < 25  → low
MODERATE_THRESHOLD = 50   # score < 50  → moderate
                          # score >= 50 → high


def classify_risk(
    factors: List[str],
    answers: Dict[str, Any],
) -> Tuple[str, int, List[str]]:
    """
    Returns (risk_level, score, rationale).
    """
    score = 0
    rationale: List[str] = []

    for factor in factors:
        weight = FACTOR_WEIGHTS.get(factor, 5)  # unknown factors get minimal weight
        score += weight
        rationale.append(_factor_to_rationale(factor, answers))

    # Age bonus (on top of the age ≥ 45 factor)
    score += _age_bonus(answers)

    # Cap at 100
    score = min(score, 100)

    if score < LOW_THRESHOLD:
        level = "low"
    elif score < MODERATE_THRESHOLD:
        level = "moderate"
    else:
        level = "high"

    logger.info("Risk classification: level=%s score=%d factors=%s", level, score, factors)
    return level, score, rationale


def _factor_to_rationale(factor: str, answers: Dict[str, Any]) -> str:
    """Convert a factor label into a human-readable rationale snippet."""
    mapping = {
        "smoking":                   "active smoker",
        "poor diet":                 f"high sugar / poor diet ({answers.get('diet', '')})",
        "high sodium diet":          "high sodium diet",
        "low exercise":              f"low physical activity ({answers.get('exercise', '')})",
        "moderate exercise":         "only moderate exercise",
        "age ≥ 45":                  f"age {answers.get('age', '≥45')} (elevated baseline risk)",
        "alcohol use":               "regular alcohol use",
        "elevated bmi":              f"elevated BMI ({answers.get('bmi', '')})",
        "obesity":                   f"obesity (BMI {answers.get('bmi', '')})",
        "high stress":               "high stress levels",
        "sleep deprivation":         f"insufficient sleep ({answers.get('sleep_hours', '<6')} hrs/night)",
        "hypertension":              "high blood pressure",
        "family history of disease": "family history of chronic disease",
    }
    return mapping.get(factor, factor)
