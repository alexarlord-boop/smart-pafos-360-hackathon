"""Dam detail endpoint router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Literal, Optional
from dateutil.relativedelta import relativedelta

from app.schemas import DamDetailResponse, DamDetail, DamComparison
from app.services.cyprus_water import cyprus_water_client, parse_api_date
from app.services.risk import calculate_risk_level

router = APIRouter(prefix="/api", tags=["dam"])

# Valid dam names from Cyprus Water API
DAM_NAMES = Literal[
    "Kouris", "Asprokremmos", "Evretou", "Kannaviou", "Kalavasos",
    "Dipotamos", "Lefkara", "Germasoyeia", "Achna", "Arminou",
    "Polemidia", "Mavrokolympos", "Vyzakia", "Xyliatos", "Argaka",
    "Pomos", "Kalopanagiotis"
]


def generate_dam_narrative(
    name: str,
    percentage: float,
    storage_mcm: Optional[float],
    capacity_mcm: float,
    risk_level: str,
    last_year_percentage: Optional[float]
) -> str:
    """Generate narrative for a specific dam."""
    parts = []
    
    # Current status
    if storage_mcm is not None:
        parts.append(
            f"{name} dam is currently at {percentage:.1f}% capacity, "
            f"holding {storage_mcm:.2f} MCM of its {capacity_mcm:.1f} MCM total capacity."
        )
    else:
        parts.append(
            f"{name} dam is currently at {percentage:.1f}% capacity "
            f"(total capacity: {capacity_mcm:.1f} MCM)."
        )
    
    # Year-over-year comparison
    if last_year_percentage is not None:
        delta = percentage - last_year_percentage
        if delta > 0:
            parts.append(f"This is {abs(delta):.1f}% higher than the same time last year.")
        elif delta < 0:
            parts.append(f"This is {abs(delta):.1f}% lower than the same time last year.")
        else:
            parts.append("This is unchanged from the same time last year.")
    
    # Risk level
    risk_messages = {
        "Low": f"The risk level for {name} is Low.",
        "Moderate": f"The risk level for {name} is Moderate. Conservation advised.",
        "High": f"The risk level for {name} is High. Significant conservation needed.",
        "Severe": f"The risk level for {name} is Severe. Critical water shortage."
    }
    parts.append(risk_messages.get(risk_level, f"Risk level: {risk_level}."))
    
    return " ".join(parts)


@router.get("/dam", response_model=DamDetailResponse)
async def get_dam_detail(
    name: DAM_NAMES = Query(..., description="Dam name"),
    days_ago: int = Query(default=0, ge=0, description="Number of days in the past (0 = latest available)")
):
    """
    Get detailed information and narrative for a specific dam.
    
    Args:
        name: Dam name (from fixed list)
        days_ago: Number of days in the past (0 = latest available data)
    
    Returns detailed dam info, year-over-year comparison, and narrative.
    """
    try:
        # Calculate target date
        target_date = date.today() - timedelta(days=days_ago) if days_ago > 0 else None
        
        # Fetch all data
        dams_metadata = await cyprus_water_client.get_dams()
        percentages_data = await cyprus_water_client.get_percentages(target_date)
        storage_data = await cyprus_water_client.get_date_statistics(target_date)
        
        # Parse data date
        date_str = percentages_data.get("date", "")
        data_date = parse_api_date(date_str) or date.today()
        
        # Find dam metadata
        dam_meta = None
        for dam in dams_metadata:
            if dam.get("nameEn") == name:
                dam_meta = dam
                break
        
        if dam_meta is None:
            raise HTTPException(status_code=404, detail=f"Dam '{name}' not found")
        
        # Get current percentage (decimal to %)
        dam_percentages = percentages_data.get("damNamesToPercentage", {})
        percentage = dam_percentages.get(name, 0) * 100
        
        # Get storage
        storage_mcm_dict = storage_data.get("storageInMCM", {})
        storage_mcm = storage_mcm_dict.get(name)
        
        # Get capacity (convert from cubic meters to MCM)
        capacity_mcm = dam_meta.get("capacity", 0) / 1_000_000
        
        # Calculate risk level
        risk_level = calculate_risk_level(percentage)
        
        # Get last year's data for comparison
        last_year_date = data_date - relativedelta(years=1)
        last_year_percentage = None
        try:
            last_year_data = await cyprus_water_client.get_percentages(last_year_date)
            last_year_pcts = last_year_data.get("damNamesToPercentage", {})
            if name in last_year_pcts:
                last_year_percentage = last_year_pcts[name] * 100
        except Exception:
            pass
        
        # Calculate delta
        delta = None
        if last_year_percentage is not None:
            delta = round(percentage - last_year_percentage, 1)
        
        # Build dam detail
        dam_detail = DamDetail(
            name=name,
            name_greek=dam_meta.get("nameEl"),
            capacity_mcm=round(capacity_mcm, 2),
            storage_mcm=round(storage_mcm, 3) if storage_mcm is not None else None,
            percentage=round(percentage, 1),
            risk_level=risk_level,
            year_of_construction=dam_meta.get("yearOfConstruction"),
            height=dam_meta.get("height"),
            lat=dam_meta.get("lat"),
            lng=dam_meta.get("lng"),
            image_url=dam_meta.get("imageUrl"),
            wikipedia_url=dam_meta.get("wikipediaUrl") or None
        )
        
        # Build comparison
        comparison = DamComparison(
            last_year_percentage=round(last_year_percentage, 1) if last_year_percentage else None,
            delta=delta
        )
        
        # Generate narrative
        narrative = generate_dam_narrative(
            name=name,
            percentage=percentage,
            storage_mcm=storage_mcm,
            capacity_mcm=capacity_mcm,
            risk_level=risk_level,
            last_year_percentage=last_year_percentage
        )
        
        return DamDetailResponse(
            data_date=data_date,
            fetched_at=datetime.utcnow(),
            dam=dam_detail,
            comparison=comparison,
            narrative=narrative
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dam details: {str(e)}")

