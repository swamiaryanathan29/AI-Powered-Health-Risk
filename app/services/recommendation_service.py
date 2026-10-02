"""
Recommendations service – Step 4.
Maps risk factors to actionable, non-diagnostic lifestyle guidance.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── Factor → recommendation(s) mapping ────────────────────────────────────
FACTOR_RECOMMENDATIONS: Dict[str, List[str]] = {
    "smoking": [
        "Quit smoking — consider nicotine replacement therapy or counselling.",
    ],
    "poor diet": [
        "Reduce sugar and processed food intake.",
        "Add more fruits, vegetables, and whole grains to your diet.",
    ],
    "high sodium diet": [
        "Limit salt intake to < 5 g/day.",
        "Choose low-sodium alternatives when shopping.",
    ],
    "low exercise": [
        "Walk at least 30 minutes daily.",
        "Aim for 150 minutes of moderate aerobic activity per week.",
    ],
    "moderate exercise": [
        "Increase weekly activity — aim for at least 150 minutes of moderate exercise.",
    ],
    "age ≥ 45": [
        "Schedule annual health check-ups with your GP.",
        "Monitor blood pressure and cholesterol regularly.",
    ],
    "alcohol use": [
        "Reduce alcohol to ≤ 14 units/week (men) or ≤ 11 units/week (women).",
        "Consider at least 2 alcohol-free days per week.",
    ],
    "elevated bmi": [
        "Work towards a healthy BMI (18.5–24.9) through diet and exercise.",
    ],
    "obesity": [
        "Seek nutritional guidance to work towards a healthy weight.",
        "Incorporate daily physical activity gradually, starting with 15-minute walks.",
    ],
    "high stress": [
        "Practice mindfulness or meditation for at least 10 minutes daily.",
        "Explore stress management techniques such as yoga or breathing exercises.",
    ],
    "sleep deprivation": [
        "Aim for 7–9 hours of sleep per night.",
        "Maintain a consistent sleep schedule and limit screen time before bed.",
    ],
    "hypertension": [
        "Monitor blood pressure regularly.",
        "Reduce sodium intake and manage stress to support healthy blood pressure.",
    ],
    "family history of disease": [
        "Discuss your family medical history with your doctor.",
        "Consider proactive screenings as advised by a healthcare professional.",
    ],
}

# ── General recommendations by risk level ───────────────────────────────────
GENERAL_RECOMMENDATIONS: Dict[str, List[str]] = {
    "low": [
        "Maintain your healthy lifestyle habits.",
        "Stay hydrated and keep up with routine health check-ups.",
    ],
    "moderate": [
        "Consider consulting a healthcare provider to review your lifestyle factors.",
        "Track your progress with a health journal.",
    ],
    "high": [
        "We strongly recommend booking an appointment with a healthcare provider soon.",
        "Do not ignore persistent symptoms — seek timely medical advice.",
    ],
}


def generate_recommendations(
    risk_level: str,
    factors: List[str],
    answers: Dict[str, Any],
) -> List[str]:
    """
    Return a deduplicated, ordered list of actionable recommendations.
    """
    seen: set = set()
    recs: List[str] = []

    def _add(items: List[str]) -> None:
        for item in items:
            if item not in seen:
                recs.append(item)
                seen.add(item)

    # Factor-specific recommendations first
    for factor in factors:
        _add(FACTOR_RECOMMENDATIONS.get(factor, []))

    # General level-based recommendations
    _add(GENERAL_RECOMMENDATIONS.get(risk_level, []))

    logger.info("Generated %d recommendations for risk_level=%s", len(recs), risk_level)
    return recs
