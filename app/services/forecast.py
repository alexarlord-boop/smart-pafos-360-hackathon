"""Forecast/projection service."""

from __future__ import annotations

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Tuple


def calculate_daily_change(percentages: list[tuple[date, float]], days: int = 30) -> Optional[float]:
    """
    Calculate average daily percentage change over the specified period.
    
    Args:
        percentages: List of (date, percentage) tuples, sorted by date ascending
        days: Number of days to look back
        
    Returns:
        Average daily change in percentage points, or None if insufficient data
    """
    if len(percentages) < 2:
        return None
    
    # Get data from last N days
    cutoff_date = date.today() - timedelta(days=days)
    recent_data = [(d, p) for d, p in percentages if d >= cutoff_date]
    
    if len(recent_data) < 2:
        # Fall back to all available data
        recent_data = percentages[-min(len(percentages), 30):]
    
    if len(recent_data) < 2:
        return None
    
    # Calculate average daily change
    first_date, first_pct = recent_data[0]
    last_date, last_pct = recent_data[-1]
    
    days_diff = (last_date - first_date).days
    if days_diff == 0:
        return None
    
    return (last_pct - first_pct) / days_diff


def generate_projection(
    current_percentage: float,
    daily_change: float,
    horizon_months: int,
    start_date: Optional[date] = None
) -> list[tuple[date, float]]:
    """
    Generate simple linear projection of water levels.
    
    Args:
        current_percentage: Current total percentage
        daily_change: Average daily change in percentage points
        horizon_months: Number of months to project forward
        start_date: Starting date for projection (defaults to today)
        
    Returns:
        List of (date, projected_percentage) tuples for each month
    """
    if start_date is None:
        start_date = date.today()
    
    projections = []
    
    for month in range(1, horizon_months + 1):
        projection_date = start_date + relativedelta(months=month)
        days_ahead = (projection_date - start_date).days
        
        # Linear extrapolation
        projected_pct = current_percentage + (daily_change * days_ahead)
        
        # Clamp to valid range
        projected_pct = max(0.0, min(100.0, projected_pct))
        
        projections.append((projection_date, round(projected_pct, 1)))
    
    return projections


def calculate_days_until_critical(
    current_percentage: float,
    daily_change: float,
    critical_threshold: float = 20.0
) -> Optional[int]:
    """
    Estimate days until reaching critical threshold (if declining).
    
    Returns:
        Number of days until critical, or None if not declining or already critical
    """
    if current_percentage <= critical_threshold:
        return 0  # Already critical
    
    if daily_change >= 0:
        return None  # Not declining
    
    days = int((critical_threshold - current_percentage) / daily_change)
    return abs(days)

