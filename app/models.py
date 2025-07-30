from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MerchantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    INACTIVE = "inactive"

class IssueType(str, Enum):
    CONVERSION_RATE_DROP = "conversion_rate_drop"
    MISSING_LOCATION = "missing_location"
    HIGH_ERROR_RATE = "high_error_rate"
    LOW_TRANSACTION_VOLUME = "low_transaction_volume"
    MONTHLY_DECLINE = "monthly_decline"

class Merchant(BaseModel):
    """Merchant data model"""
    merchant_id: str = Field(..., description="Unique merchant identifier")
    merchant_name: str = Field(..., description="Merchant business name")
    country: Optional[str] = Field(None, description="Merchant country")
    city: Optional[str] = Field(None, description="Merchant city")
    conversion_rate: float = Field(..., ge=0, le=1, description="Current conversion rate")
    error_rate: float = Field(..., ge=0, le=1, description="Current error rate")
    transaction_count: int = Field(..., ge=0, description="Total transaction count")
    timestamp: datetime = Field(..., description="Data timestamp")
    status: MerchantStatus = Field(..., description="Merchant status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversionRateAnalysis(BaseModel):
    """Conversion rate analysis results"""
    merchant_id: str
    merchant_name: str
    current_rate: float
    previous_rate: float
    change_percentage: float
    is_issue: bool
    severity: str  # "low", "medium", "high"
    recommendation: str

class LocationIssue(BaseModel):
    """Location data issue"""
    merchant_id: str
    merchant_name: str
    missing_fields: List[str]
    impact_level: str  # "low", "medium", "high"
    recommendation: str

class MonthlyComparison(BaseModel):
    """Month-to-month comparison data"""
    merchant_id: str
    merchant_name: str
    current_month: Dict[str, Any]
    previous_month: Dict[str, Any]
    changes: Dict[str, float]
    trend: str  # "improving", "declining", "stable"

class TroubleshootingRequest(BaseModel):
    """AI troubleshooting request"""
    merchant_id: Optional[str] = None
    issue_type: Optional[IssueType] = None
    date_range: Optional[str] = None
    include_recommendations: bool = True

class TroubleshootingResponse(BaseModel):
    """AI troubleshooting response"""
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    priority_actions: List[str]
    risk_score: float
    next_steps: List[str]

class AnalyticsResponse(BaseModel):
    """Generic analytics response"""
    total_merchants: int
    issues_found: int
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None 