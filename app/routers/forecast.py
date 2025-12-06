"""Forecast endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from typing import Optional

from app.schemas import ForecastResponse, ForecastPoint
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.forecast import calculate_daily_change, generate_projection

router = APIRouter(prefix="/api", tags=["forecast"])


def parse_target_date(date_str: Optional[str]) -> Optional[date]:
    """Parse target date from DD.MM.YYYY format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    months: int = Query(default=3, ge=1, le=12, description="Projection horizon in months"),
    target_date: Optional[str] = Query(default=None, description="Start date in DD.MM.YYYY format (empty = latest available)")
):
    """
    Get simple forward projection of total water levels.
    
    Args:
        months: Number of months to project forward
        target_date: Start date in DD.MM.YYYY format (empty = latest available)
    
    Uses linear extrapolation based on recent trend (no rain scenario).
    """
    try:
        # Parse target date
        query_date = parse_target_date(target_date)
        
        # Fetch percentages
        today_data = await cyprus_water_client.get_percentages(query_date)
        
        # Parse data date
        date_str = today_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # totalPercentage is decimal, convert to %
        current_percentage = today_data.get("totalPercentage", 0) * 100
        
        # Fetch timeseries to calculate trend
        timeseries_data = await cyprus_water_client.get_timeseries()
        
        # Parse timeseries data - keys are dates like "2025-12-05"
        data_points = []
        for date_key, day_data in timeseries_data.items():
            if not isinstance(day_data, dict):
                continue
            try:
                point_date = datetime.strptime(date_key, "%Y-%m-%d").date()
                # Convert decimal to percentage
                total_pct = day_data.get("totalPercentage", 0)
                pct_value = (total_pct if isinstance(total_pct, (int, float)) else 0) * 100
                data_points.append((point_date, pct_value))
            except (ValueError, KeyError):
                continue
        
        # Sort by date
        data_points.sort(key=lambda x: x[0])
        
        # Calculate daily change from recent data
        daily_change = calculate_daily_change(data_points, days=90)
        
        if daily_change is None:
            # Fall back to a conservative estimate if not enough data
            daily_change = -0.05  # Assume slight decline
        
        # Generate projections starting from data date
        projections = generate_projection(
            current_percentage=current_percentage,
            daily_change=daily_change,
            horizon_months=months,
            start_date=data_date
        )
        
        # Convert to response format
        forecast_points = [
            ForecastPoint(date=proj_date, projected_percentage=proj_pct)
            for proj_date, proj_pct in projections
        ]
        
        return ForecastResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            horizon_months=months,
            projections=forecast_points,
            methodology="linear_extrapolation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")
