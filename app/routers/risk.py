"""Risk endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from datetime import date, datetime, timedelta

from app.schemas import RiskResponse, RiskFactors
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.risk import calculate_risk_score, get_seasonal_factor

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/risk", response_model=RiskResponse)
async def get_risk():
    """
    Get current drought risk assessment.
    
    Returns risk level, score, and contributing factors.
    """
    try:
        # Fetch current percentages
        today_data = await cyprus_water_client.get_percentages()
        
        # Parse data date
        date_str = today_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # totalPercentage is a decimal (0.094 = 9.4%), convert to %
        current_percentage = today_data.get("totalPercentage", 0) * 100
        
        # Try to calculate 30-day trend
        trend_30d = None
        try:
            # Get stats from 30 days ago
            thirty_days_ago = date.today() - timedelta(days=30)
            past_data = await cyprus_water_client.get_percentages(thirty_days_ago)
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
            current_date=date.today()
        )
        
        # Get seasonal factor
        seasonal_factor = get_seasonal_factor(date.today())
        
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
