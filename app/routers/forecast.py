"""Forecast endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from app.schemas import ForecastResponse
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.forecast import calculate_daily_change

router = APIRouter(prefix="/api", tags=["forecast"])


def parse_future_date(date_str: str) -> date:
    """Parse and validate future date from DD.MM.YYYY format."""
    try:
        parsed_date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")
    
    if parsed_date <= date.today():
        raise HTTPException(status_code=400, detail="target_date must be in the future")
    
    return parsed_date


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    target_date: str = Query(..., description="Future target date in DD.MM.YYYY format")
):
    """
    Get projection of total water levels to a future date.
    
    Args:
        target_date: Future date in DD.MM.YYYY format to project to
    
    Uses linear extrapolation based on recent trend (no rain scenario).
    """
    try:
        # Parse and validate future date
        forecast_target = parse_future_date(target_date)
        
        # Fetch current percentages (latest available)
        today_data = await cyprus_water_client.get_percentages()
        
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
        
        # Calculate days until target
        days_ahead = (forecast_target - data_date).days
        
        # Calculate projected percentage
        projected_pct = current_percentage + (daily_change * days_ahead)
        projected_pct = max(0.0, min(100.0, projected_pct))  # Clamp to valid range
        
        return ForecastResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            target_date=forecast_target,
            current_percentage=round(current_percentage, 1),
            projected_percentage=round(projected_pct, 1),
            daily_change=round(daily_change, 3),
            days_ahead=days_ahead,
            methodology="linear_extrapolation"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")
