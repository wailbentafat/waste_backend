from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class WasteType(str, Enum):
    ORGANIC = "organic"
    PLASTIC = "plastic"
    GLASS = "glass"
    METAL = "metal"
    MIXED = "mixed"


class DetectionStatus(str, Enum):
    ACTIVE = "active"
    COLLECTED = "collected"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


# MongoDB Models
class BinLocation(BaseModel):
    address: str
    coordinates: List[float] = Field(..., min_items=2, max_items=2)


class BinMetadata(BaseModel):
    device_id: str
    firmware_version: str
    battery_level: int
    last_heartbeat: datetime


class BinDetection(BaseModel):
    fill_level: int = Field(..., ge=0, le=100)
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    image_path: Optional[str] = None


class BinStatus(BaseModel):
    fill_level: int
    last_detection: datetime
    detection_confidence: float


class Bin(BaseModel):
    id: str = Field(..., alias="_id")
    bin_id: str
    location: BinLocation
    status: BinStatus
    metadata: BinMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class ESP32SensorData(BaseModel):
    ultrasonic_distance: float
    battery_level: int
    wifi_signal: int
    temperature: float
    humidity: int
    timestamp: datetime


class ESP32Message(BaseModel):
    device_id: str
    timestamp: datetime
    data: ESP32SensorData


class ESP32Command(BaseModel):
    command: str
    quality: str = "medium"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class YOLODetection(BaseModel):
    fill_level: int
    confidence: float
    objects_detected: int
    bounding_boxes: List[Dict[str, Any]]
    image_processed: str
    detection_time: datetime = Field(default_factory=datetime.utcnow)


class CollectionRecord(BaseModel):
    id: Optional[str] = None
    bin_id: str
    operator_id: int
    collection_time: datetime
    fill_before: int
    estimated_capacity: int = 100
    route_optimized: bool = False
    notes: Optional[str] = None


class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BinAnalytics(BaseModel):
    id: Optional[int] = None
    bin_id: str
    fill_level: int
    detection_count: int = Field(default=1)
    collection_count: int = Field(default=0)
    detected_at: datetime
    coordinates: List[float]
    waste_type: Optional[str] = None
    confidence: float
    location_address: str


class DashboardStats(BaseModel):
    total_bins: int
    active_bins: int
    critical_bins: int
    avg_fill_level: float
    collections_today: int
    efficiency_rate: float


class MQTTTopic(BaseModel):
    bin_id: str
    topic: str


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
