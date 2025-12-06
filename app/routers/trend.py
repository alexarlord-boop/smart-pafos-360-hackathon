"""Trend endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from typing import Optional
from dateutil.relativedelta import relativedelta

from app.schemas import TrendResponse, TrendPoint
from app.services.cyprus_water import cyprus_water_client

router = APIRouter(prefix="/api", tags=["trend"])


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date from DD.MM.YYYY format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    start_date: Optional[str] = Query(default=None, description="Start date in DD.MM.YYYY format (default: 5 years ago)"),
    end_date: Optional[str] = Query(default=None, description="End date in DD.MM.YYYY format (default: today)")
):
    """
    Get historical total percentage timeseries.
    
    Args:
        start_date: Start of period in DD.MM.YYYY format (default: 5 years ago)
        end_date: End of period in DD.MM.YYYY format (default: today)
    
    Returns daily/periodic data points for the specified period.
    """
    try:
        # Parse dates
        parsed_start = parse_date(start_date)
        parsed_end = parse_date(end_date)
        
        # Set defaults
        if parsed_end is None:
            parsed_end = date.today()
        if parsed_start is None:
            parsed_start = parsed_end - relativedelta(years=5)
        
        # Validate date range
        if parsed_start > parsed_end:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")
        
        # Fetch timeseries data from API
        timeseries_data = await cyprus_water_client.get_timeseries()
        
        trend_points = []
        
        # Timeseries has date keys like "2025-12-05" with values containing totalPercentage
        for date_key, day_data in timeseries_data.items():
            # Skip non-date keys like "numOfDams"
            if not isinstance(day_data, dict):
                continue
            
            try:
                # Parse date key (format: YYYY-MM-DD)
                point_date = datetime.strptime(date_key, "%Y-%m-%d").date()
                
                # Filter by date range
                if point_date < parsed_start or point_date > parsed_end:
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
