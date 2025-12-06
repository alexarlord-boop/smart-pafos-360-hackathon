"""Dams endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from typing import Optional

from app.schemas import DamsResponse, DamStatus
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.risk import calculate_risk_level

router = APIRouter(prefix="/api", tags=["dams"])


def parse_target_date(date_str: Optional[str]) -> Optional[date]:
    """Parse target date from DD.MM.YYYY format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD.MM.YYYY")


@router.get("/dams", response_model=DamsResponse)
async def get_dams(
    target_date: Optional[str] = Query(default=None, description="Target date in DD.MM.YYYY format (empty = latest available)")
):
    """
    Get status for all dams.
    
    Args:
        target_date: Date in DD.MM.YYYY format (empty = latest available data)
    
    Returns list of dams with capacity, current percentage, and risk level.
    """
    try:
        # Parse target date
        query_date = parse_target_date(target_date)
        
        # Fetch dam metadata and percentages
        dams_data = await cyprus_water_client.get_dams()
        percentages_data = await cyprus_water_client.get_percentages(query_date)
        storage_data = await cyprus_water_client.get_date_statistics(query_date)
        
        # Parse the date from response
        date_str = percentages_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # Build dam status list
        dam_statuses = []
        
        # Create lookup for dam metadata by English name
        dam_lookup = {dam["nameEn"]: dam for dam in dams_data}
        
        # Get percentages - stored in damNamesToPercentage with dam names as keys
        dam_percentages = percentages_data.get("damNamesToPercentage", {})
        storage_mcm = storage_data.get("storageInMCM", {})
        
        for dam_name, percentage in dam_percentages.items():
            dam_info = dam_lookup.get(dam_name)
            
            # Convert percentage from decimal to % (0.08 -> 8.0)
            pct_value = (percentage if isinstance(percentage, (int, float)) else 0) * 100
            
            # Get capacity - in cubic meters, convert to MCM
            capacity_mcm = 0
            if dam_info:
                capacity_mcm = dam_info.get("capacity", 0) / 1_000_000  # Convert to MCM
            
            # Get storage
            storage = storage_mcm.get(dam_name, 0) if storage_mcm else None
            
            dam_statuses.append(DamStatus(
                name=dam_name,
                capacity_mcm=round(capacity_mcm, 2),
                storage_mcm=round(storage, 3) if storage else None,
                percentage=round(pct_value, 1),
                risk_level=calculate_risk_level(pct_value)
            ))
        
        # Sort by percentage (lowest first - most critical)
        dam_statuses.sort(key=lambda d: d.percentage)
        
        return DamsResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            dams=dam_statuses
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dams: {str(e)}")
