from sqlalchemy import (
    Column, Integer, String, Date, Boolean,
    JSON, ForeignKey, DateTime,
)
from sqlalchemy.sql import func
from gaia.db.base import Base


class NumerologySubject(Base):
    __tablename__ = "numerology_subjects"
    id              = Column(Integer, primary_key=True, index=True)
    full_birth_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False)
    birth_date      = Column(Date, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class NumerologyChartRecord(Base):
    __tablename__ = "numerology_charts"
    id             = Column(Integer, primary_key=True, index=True)
    subject_id     = Column(Integer, ForeignKey("numerology_subjects.id"), nullable=False)
    system_version = Column(String, nullable=False, default="1.0.0")
    config_json    = Column(JSON, nullable=False)
    computed_at    = Column(DateTime(timezone=True), server_default=func.now())


class NumerologyNumber(Base):
    __tablename__ = "numerology_numbers"
    id               = Column(Integer, primary_key=True, index=True)
    chart_id         = Column(Integer, ForeignKey("numerology_charts.id"), nullable=False)
    number_type      = Column(String, nullable=False)  # life_path, expression, soul_urge, etc.
    raw_value        = Column(Integer, nullable=False)
    reduced_value    = Column(Integer, nullable=False)
    is_master_number = Column(Boolean, default=False)
    reduction_path   = Column(JSON, nullable=False)
