from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, POINT
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="operator")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    collections = relationship("Collection", back_populates="operator")


class BinAnalytics(Base):
    __tablename__ = "bin_analytics"

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(String(20), index=True, nullable=False)
    fill_level = Column(Integer, nullable=False)
    detection_count = Column(Integer, default=1)
    collection_count = Column(Integer, default=0)
    detected_at = Column(DateTime, nullable=False, index=True)
    coordinates = Column(POINT, nullable=False)
    waste_type = Column(String(20))
    confidence = Column(Float, nullable=False)
    location_address = Column(String(255))

    # Indexes for performance
    __table_args__ = ({"schema": "public"},)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(String(20), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_time = Column(DateTime, nullable=False)
    fill_before = Column(Integer, nullable=False)
    estimated_capacity = Column(Integer, default=100)
    route_optimized = Column(Boolean, default=False)
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    operator = relationship("User", back_populates="collections")


class CollectionRoute(Base):
    __tablename__ = "collection_routes"

    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String(100), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bin_ids = Column(String(1000), nullable=False)  # JSON array of bin IDs
    planned_time = Column(DateTime, nullable=False)
    actual_time = Column(DateTime)
    status = Column(String(20), default="planned")  # planned, in_progress, completed
    efficiency_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metadata = Column(String(1000))  # JSON metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(String(20), nullable=False, index=True)
    alert_type = Column(
        String(50), nullable=False
    )  # critical_fill, offline, battery_low
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    message = Column(String(500), nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
