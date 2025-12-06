"""Trend endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from app.schemas import TrendResponse, TrendPoint
from app.services.cyprus_water import cyprus_water_client

router = APIRouter(prefix="/api", tags=["trend"])


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    years: int = Query(default=5, ge=1, le=10, description="Number of years of historical data")
):
    """
    Get historical total percentage timeseries.
    
    Returns daily/periodic data points for the specified number of years.
    """
    try:
        # Fetch timeseries data from API
        timeseries_data = await cyprus_water_client.get_timeseries()
        
        # Calculate cutoff date
        cutoff_date = date.today() - relativedelta(years=years)
        
        trend_points = []
        
        # Timeseries has date keys like "2025-12-05" with values containing totalPercentage
        for date_key, day_data in timeseries_data.items():
            # Skip non-date keys like "numOfDams"
            if not isinstance(day_data, dict):
                continue
            
            try:
                # Parse date key (format: YYYY-MM-DD)
                point_date = datetime.strptime(date_key, "%Y-%m-%d").date()
                
                # Filter by cutoff date
                if point_date < cutoff_date:
                    continue
                
                # Get totalPercentage (decimal) and convert to %
                total_pct = day_data.get("totalPercentage", 0)
                pct_value = (total_pct if isinstance(total_pct, (int, float)) else 0) * 100
                
                trend_points.append(TrendPoint(
                    date=point_date,
                    percentage=round(pct_value, 1)
                ))
            except (ValueError, KeyError):
                continue
        
        # Sort by date ascending
        trend_points.sort(key=lambda p: p.date)
        
        return TrendResponse(data=trend_points)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trend: {str(e)}")
