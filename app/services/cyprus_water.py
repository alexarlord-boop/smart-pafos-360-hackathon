"""Cyprus Water API client service."""

from __future__ import annotations

import httpx
from datetime import date, datetime
from typing import Optional, List

from app.config import CYPRUS_WATER_BASE_URL


def parse_api_date(date_str: str) -> Optional[date]:
    """
    Parse date from Cyprus Water API format.
    Handles formats like "Dec 5, 2025 12:00:00 AM"
    """
    if not date_str:
        return None
    try:
        # Format: "Dec 5, 2025 12:00:00 AM"
        dt = datetime.strptime(date_str, "%b %d, %Y %I:%M:%S %p")
        return dt.date()
    except ValueError:
        try:
            # Try alternative format: "Dec 5, 2025"
            dt = datetime.strptime(date_str.split(" 12:")[0], "%b %d, %Y")
            return dt.date()
        except ValueError:
            return None


class CyprusWaterClient:
    """Client for cyprus-water.appspot.com API."""

    def __init__(self, base_url: str = CYPRUS_WATER_BASE_URL):
        self.base_url = base_url
        self.timeout = 30.0

    async def get_dams(self) -> list[dict]:
        """
        Fetch static information about all dams.
        
        Returns array of dam objects with:
        - nameEn: English name
        - nameEl: Greek name
        - capacity: capacity in cubic meters (NOT MCM)
        - yearOfConstruction, height, lat, lng, etc.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/dams")
            response.raise_for_status()
            return response.json()

    async def get_date_statistics(self, target_date: Optional[date] = None) -> dict:
        """
        Fetch statistics for a specific date.
        
        Returns:
        - timestamp: timestamp in ms
        - date: formatted date string (e.g., "Dec 5, 2025 12:00:00 AM")
        - storageInMCM: dict with dam names as keys, storage values in MCM
        - inflowInMCM: dict with dam names as keys, inflow values in MCM
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {}
            if target_date:
                params["date"] = target_date.strftime("%Y-%m-%d")
            response = await client.get(
                f"{self.base_url}/api/date-statistics",
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_percentages(self, target_date: Optional[date] = None) -> dict:
        """
        Fetch per-dam percentages for a specific date.
        
        Returns:
        - damNamesToPercentage: dict with dam names as keys, percentage as decimals (0.08 = 8%)
        - date: formatted date string
        - totalPercentage: total percentage as decimal
        - totalCapacityInMCM: total capacity in MCM
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {}
            if target_date:
                params["date"] = target_date.strftime("%Y-%m-%d")
            response = await client.get(
                f"{self.base_url}/api/percentages",
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_timeseries(self) -> dict:
        """
        Fetch historical timeseries of water levels.
        
        Returns dict with:
        - Keys are dates in format "YYYY-MM-DD"
        - Each value contains damNamesToPercentage, date, totalPercentage, totalCapacityInMCM
        - numOfDams: number of dams
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/timeseries")
            response.raise_for_status()
            return response.json()

    async def get_monthly_inflows(self) -> list[dict]:
        """
        Fetch historical monthly inflows.
        Returns array of MonthlyInflows objects.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/monthly-inflows")
            response.raise_for_status()
            return response.json()


# Singleton instance
cyprus_water_client = CyprusWaterClient()
