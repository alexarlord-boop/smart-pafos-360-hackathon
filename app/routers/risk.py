"""Risk endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Optional

from app.schemas import RiskResponse, RiskFactors
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.risk import calculate_risk_score, get_seasonal_factor

router = APIRouter(prefix="/api", tags=["risk"])


def parse_target_date(date_str: Optional[str]) -> Optional[date]:
    """Parse target date from DD.MM.YYYY format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")


@router.get("/risk", response_model=RiskResponse)
async def get_risk(
    target_date: Optional[str] = Query(default=None, description="Target date in DD.MM.YYYY format (empty = latest available)")
):
    """
    Get drought risk assessment.
    
    Args:
        target_date: Date in DD.MM.YYYY format (empty = latest available data)
    
    Returns risk level, score, and contributing factors.
    """
    try:
        # Parse target date
        query_date = parse_target_date(target_date)
        
        # Fetch percentages
        today_data = await cyprus_water_client.get_percentages(query_date)
        
        # Parse data date
        date_str = today_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # totalPercentage is a decimal (0.094 = 9.4%), convert to %
        current_percentage = today_data.get("totalPercentage", 0) * 100
        
        # Try to calculate 30-day trend
        trend_30d = None
        try:
            # Get stats from 30 days before the target date
            trend_ref_date = data_date - timedelta(days=30)
            past_data = await cyprus_water_client.get_percentages(trend_ref_date)
            past_percentage = past_data.get("totalPercentage", 0) * 100
            
            if past_percentage is not None:
                trend_30d = round(current_percentage - past_percentage, 1)
        except Exception:
            # If historical data not available, proceed without trend
            pass
        
        # Calculate risk score and level
        score, risk_level = calculate_risk_score(
            current_percentage=current_percentage,
            trend_30d=trend_30d,
            current_date=data_date
        )
        
        # Get seasonal factor
        seasonal_factor = get_seasonal_factor(data_date)
        
        return RiskResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            risk_level=risk_level,
            score=score,
            factors=RiskFactors(
                current_percentage=round(current_percentage, 1),
                trend_30d=trend_30d,
                seasonal_factor=seasonal_factor
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk: {str(e)}")
