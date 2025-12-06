"""SQLAlchemy ORM models for dam data."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Dam(Base):
    """Dam metadata cache."""
    __tablename__ = "dams"

    id = Column(String, primary_key=True)  # Dam ID from API
    name = Column(String, nullable=False)
    name_greek = Column(String, nullable=True)
    capacity_mcm = Column(Float, nullable=False)  # Million Cubic Meters
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    daily_records = relationship("DamDaily", back_populates="dam")


class DailyStats(Base):
    """Daily aggregate statistics for all dams."""
    __tablename__ = "daily_stats"

    date = Column(Date, primary_key=True)
    total_storage_mcm = Column(Float, nullable=False)
    total_capacity_mcm = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DamDaily(Base):
    """Per-dam daily storage data."""
    __tablename__ = "dam_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    dam_id = Column(String, ForeignKey("dams.id"), nullable=False)
    storage_mcm = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    inflow_mcm = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dam = relationship("Dam", back_populates="daily_records")

    class Config:
        # Unique constraint on date + dam_id
        __table_args__ = (
            {"sqlite_autoincrement": True},
        )

