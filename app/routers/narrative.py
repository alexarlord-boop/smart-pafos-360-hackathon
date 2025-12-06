"""Narrative endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Optional
from dateutil.relativedelta import relativedelta

from app.schemas import NarrativeResponse
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.risk import calculate_risk_score, get_seasonal_factor

router = APIRouter(prefix="/api", tags=["narrative"])


def generate_narrative_text(
    current_percentage: float,
    last_year_percentage: Optional[float],
    risk_level: str,
    trend_30d: Optional[float],
    seasonal_factor: str
) -> str:
    """Generate a templated narrative summary."""
    
    parts = []
    
    # Current status
    parts.append(f"Cyprus reservoirs are currently at {current_percentage:.1f}% capacity.")
    
    # Year-over-year comparison
    if last_year_percentage is not None:
        delta = current_percentage - last_year_percentage
        if delta > 0:
            parts.append(f"This is {abs(delta):.1f}% higher than the same time last year.")
        elif delta < 0:
            parts.append(f"This is {abs(delta):.1f}% lower than the same time last year.")
        else:
            parts.append("This is the same as last year at this time.")
    
    # Risk assessment
    risk_descriptions = {
        "Low": "The current drought risk level is Low, indicating adequate water reserves.",
        "Moderate": "The current drought risk level is Moderate. Water conservation is advised.",
        "High": "The current drought risk level is High. Significant water conservation measures are recommended.",
        "Severe": "The current drought risk level is Severe. Immediate water conservation action is critical."
    }
    parts.append(risk_descriptions.get(risk_level, f"Current drought risk is {risk_level}."))
    
    # Trend information
    if trend_30d is not None:
        if trend_30d < -3:
            parts.append(f"Water levels have dropped {abs(trend_30d):.1f}% over the past 30 days.")
        elif trend_30d < 0:
            parts.append(f"Water levels have slightly decreased by {abs(trend_30d):.1f}% over the past month.")
        elif trend_30d > 3:
            parts.append(f"Water levels have increased by {trend_30d:.1f}% over the past 30 days.")
        elif trend_30d > 0:
            parts.append(f"Water levels have slightly increased by {trend_30d:.1f}% over the past month.")
    
    # Seasonal context
    seasonal_messages = {
        "dry_season": "We are currently in the dry season when water demand is typically highest.",
        "wet_season": "We are currently in the wet season when rainfall typically replenishes reservoirs.",
        "transition": "We are in a transition period between wet and dry seasons."
    }
    parts.append(seasonal_messages.get(seasonal_factor, ""))
    
    return " ".join(filter(None, parts))


@router.get("/narrative", response_model=NarrativeResponse)
async def get_narrative(
    days_ago: int = Query(default=0, ge=0, description="Number of days in the past (0 = latest available)")
):
    """
    Get a templated narrative summary.
    
    Args:
        days_ago: Number of days in the past (0 = latest available data)
    
    Returns a human-readable summary of water situation.
    """
    try:
        # Calculate target date
        target_date = date.today() - timedelta(days=days_ago) if days_ago > 0 else None
        
        # Fetch percentages
        today_data = await cyprus_water_client.get_percentages(target_date)
        
        # Parse data date
        date_str = today_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # totalPercentage is decimal, convert to %
        current_percentage = today_data.get("totalPercentage", 0) * 100
        
        # Get last year's data (same day, one year before data_date)
        last_year_date = data_date - relativedelta(years=1)
        last_year_percentage = None
        try:
            last_year_data = await cyprus_water_client.get_percentages(last_year_date)
            last_year_percentage = last_year_data.get("totalPercentage", 0) * 100
        except Exception:
            pass
        
        # Get 30-day trend (relative to data_date)
        trend_30d = None
        try:
            thirty_days_before = data_date - timedelta(days=30)
            past_data = await cyprus_water_client.get_percentages(thirty_days_before)
            past_percentage = past_data.get("totalPercentage", 0) * 100
            if past_percentage is not None:
                trend_30d = current_percentage - past_percentage
        except Exception:
            pass
        
        # Calculate risk
        _, risk_level = calculate_risk_score(
            current_percentage=current_percentage,
            trend_30d=trend_30d,
            current_date=data_date
        )
        
        # Get seasonal factor
        seasonal_factor = get_seasonal_factor(data_date)
        
        # Generate narrative
        narrative = generate_narrative_text(
            current_percentage=current_percentage,
            last_year_percentage=last_year_percentage,
            risk_level=risk_level,
            trend_30d=trend_30d,
            seasonal_factor=seasonal_factor
        )
        
        return NarrativeResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            narrative=narrative,
            current_percentage=current_percentage,
            last_year_percentage=last_year_percentage,
            risk_level=risk_level,
            trend_30d=trend_30d,
            seasonal_factor=seasonal_factor
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate narrative: {str(e)}")
