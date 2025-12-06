"""Risk calculation service."""

from datetime import date
from typing import Optional

from app.config import RISK_THRESHOLDS, DRY_SEASON_MONTHS


def calculate_risk_level(percentage: float) -> str:
    """
    Calculate risk level based on current percentage.
    Returns: "Low", "Moderate", "High", or "Severe"
    """
    if percentage < RISK_THRESHOLDS["severe"]:
        return "Severe"
    elif percentage < RISK_THRESHOLDS["high"]:
        return "High"
    elif percentage < RISK_THRESHOLDS["moderate"]:
        return "Moderate"
    else:
        return "Low"


def calculate_risk_score(
    current_percentage: float,
    trend_30d: Optional[float] = None,
    current_date: Optional[date] = None
) -> tuple[int, str]:
    """
    Calculate comprehensive risk score (0-100, higher = more risk).
    
    Scoring:
    - Base score from current percentage (0-50 points)
    - Trend adjustment (-10 to +20 points)
    - Seasonal adjustment (0 to +15 points)
    
    Returns: (score, risk_level)
    """
    if current_date is None:
        current_date = date.today()
    
    # Base score from current percentage (inverted: lower % = higher score)
    # 0% -> 50 points, 100% -> 0 points
    base_score = max(0, min(50, int((100 - current_percentage) * 0.5)))
    
    # Trend adjustment
    trend_score = 0
    if trend_30d is not None:
        if trend_30d < -5:
            trend_score = 20  # Rapidly declining
        elif trend_30d < -2:
            trend_score = 15  # Declining
        elif trend_30d < 0:
            trend_score = 10  # Slightly declining
        elif trend_30d > 5:
            trend_score = -10  # Rapidly increasing (good)
        elif trend_30d > 2:
            trend_score = -5  # Increasing (good)
    
    # Seasonal adjustment
    seasonal_score = 0
    if current_date.month in DRY_SEASON_MONTHS:
        seasonal_score = 15  # Higher risk during dry season
    
    # Calculate total score (0-100)
    total_score = max(0, min(100, base_score + trend_score + seasonal_score))
    
    # Determine risk level from score
    if total_score >= 75:
        risk_level = "Severe"
    elif total_score >= 55:
        risk_level = "High"
    elif total_score >= 35:
        risk_level = "Moderate"
    else:
        risk_level = "Low"
    
    return total_score, risk_level


def get_seasonal_factor(current_date: Optional[date] = None) -> str:
    """Get seasonal factor description."""
    if current_date is None:
        current_date = date.today()
    
    if current_date.month in DRY_SEASON_MONTHS:
        return "dry_season"
    elif current_date.month in [12, 1, 2, 3]:
        return "wet_season"
    else:
        return "transition"

