"""Summary endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from typing import Optional
from dateutil.relativedelta import relativedelta

from app.schemas import SummaryResponse
from app.services.cyprus_water import cyprus_water_client, parse_api_date

router = APIRouter(prefix="/api", tags=["summary"])


def parse_target_date(date_str: Optional[str]) -> Optional[date]:
    """Parse target date from DD.MM.YYYY format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    target_date: Optional[str] = Query(default=None, description="Target date in DD.MM.YYYY format (empty = latest available)")
):
    """
    Get reservoir summary with comparison to last year.
    
    Args:
        target_date: Date in DD.MM.YYYY format (empty = latest available data)
    
    Returns total percentage, storage, capacity, and year-over-year delta.
    """
    try:
        # Parse target date
        query_date = parse_target_date(target_date)
        
        # Fetch percentages (contains totalPercentage, totalCapacityInMCM)
        today_data = await cyprus_water_client.get_percentages(query_date)
        
        # Also get storage data
        today_stats = await cyprus_water_client.get_date_statistics(query_date)
        
        # Parse the date from response
        date_str = today_data.get("date", "")
        today_date = parse_api_date(date_str) or date.today()
        
        # Get values - percentages are decimals (0.094 = 9.4%)
        total_percentage = today_data.get("totalPercentage", 0) * 100  # Convert to %
        total_capacity = today_data.get("totalCapacityInMCM", 0)
        
        # Calculate total storage from storageInMCM
        storage_dict = today_stats.get("storageInMCM", {})
        total_storage = sum(storage_dict.values()) if storage_dict else 0
        
        # Get last year's same day
        last_year_date = today_date - relativedelta(years=1)
        last_year_percentage = None
        
        try:
            last_year_data = await cyprus_water_client.get_percentages(last_year_date)
            last_year_percentage = last_year_data.get("totalPercentage", 0) * 100  # Convert to %
        except Exception:
            # If last year data not available, set to None
            pass
        
        # Calculate delta
        delta = None
        if last_year_percentage is not None:
            delta = round(total_percentage - last_year_percentage, 1)
        
        return SummaryResponse(
            data_date=today_date,
            fetched_at=datetime.utcnow(),
            total_percentage=round(total_percentage, 1),
            last_year_percentage=round(last_year_percentage, 1) if last_year_percentage else None,
            delta=delta,
            total_storage_mcm=round(total_storage, 2),
            total_capacity_mcm=round(total_capacity, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")
