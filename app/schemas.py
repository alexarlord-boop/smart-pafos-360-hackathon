"""Pydantic response schemas."""

from __future__ import annotations

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


# Summary schemas
class SummaryResponse(BaseModel):
    """Response for /api/summary/today endpoint."""
    data_date: date  # When the data was recorded (from source API)
    fetched_at: datetime  # When we retrieved it
    total_percentage: float
    last_year_percentage: Optional[float] = None
    delta: Optional[float] = None
    total_storage_mcm: float
    total_capacity_mcm: float


# Dam schemas
class DamStatus(BaseModel):
    """Individual dam status."""
    name: str
    capacity_mcm: float
    storage_mcm: Optional[float] = None
    percentage: float
    risk_level: str


class DamsResponse(BaseModel):
    """Response for /api/dams-today endpoint."""
    data_date: date  # When the data was recorded (from source API)
    fetched_at: datetime  # When we retrieved it
    dams: list[DamStatus]


# Trend schemas
class TrendPoint(BaseModel):
    """Single data point in trend."""
    date: date
    percentage: float


class TrendResponse(BaseModel):
    """Response for /api/trend endpoint."""
    data: list[TrendPoint]


# Risk schemas
class RiskFactors(BaseModel):
    """Factors contributing to risk assessment."""
    current_percentage: float
    trend_30d: Optional[float] = None
    seasonal_factor: str


class RiskResponse(BaseModel):
    """Response for /api/risk endpoint."""
    data_date: date  # When the data was recorded (from source API)
    fetched_at: datetime  # When we retrieved it
    risk_level: str
    score: int
    factors: RiskFactors


# Forecast schemas
class ForecastPoint(BaseModel):
    """Single projection point."""
    date: date
    projected_percentage: float


class ForecastResponse(BaseModel):
    """Response for /api/forecast endpoint."""
    data_date: date  # When the base data was recorded
    fetched_at: datetime  # When we retrieved it
    horizon_months: int
    projections: list[ForecastPoint]
    methodology: str = "linear_extrapolation"


# Narrative schema
class NarrativeResponse(BaseModel):
    """Response for /api/narrative endpoint."""
    data_date: date  # When the data was recorded
    fetched_at: datetime  # When we retrieved it
    narrative: str
    current_percentage: float
    last_year_percentage: float
    risk_level: str
    trend_30d: float
    seasonal_factor: str

