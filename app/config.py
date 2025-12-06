"""Application configuration and constants."""

# External API
CYPRUS_WATER_BASE_URL = "https://cyprus-water.appspot.com"

# Database
DATABASE_URL = "sqlite:///./cyprus_dams.db"

# Risk thresholds (percentage)
RISK_THRESHOLDS = {
    "severe": 20,
    "high": 35,
    "moderate": 50,
}

# Dry season months (1-indexed)
DRY_SEASON_MONTHS = [6, 7, 8, 9]  # June - September

# Cache TTL in seconds
CACHE_TTL_SECONDS = 3600  # 1 hour

