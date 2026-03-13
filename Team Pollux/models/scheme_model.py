from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class SchemeModel(BaseModel):
    """Pydantic model for scheme data validation"""
    
    # Required fields
    scheme_id: str = Field(..., description="Unique identifier for the scheme")
    scheme_name: str = Field(..., description="Name of the scheme")
    description: str = Field(..., description="Brief description of the scheme")
    ministry: str = Field(..., description="Responsible ministry/department")
    
    # Optional fields with defaults
    category: str = Field("General", description="Scheme category")
    state: str = Field("Central", description="State or Central scheme")
    
    eligibility: Optional[str] = Field(None, description="Eligibility criteria")
    beneficiaries: Optional[str] = Field(None, description="Target beneficiaries")
    benefits: Optional[str] = Field(None, description="Scheme benefits")
    
    documents_required: List[str] = Field(default_factory=list, description="Required documents")
    application_process: Optional[str] = Field(None, description="How to apply")
    
    official_url: Optional[str] = Field(None, description="Official website URL")
    contact_info: Optional[str] = Field(None, description="Contact information")
    helpline: Optional[str] = Field(None, description="Helpline number")
    
    # Age criteria
    min_age: int = Field(0, description="Minimum age required")
    max_age: int = Field(100, description="Maximum age allowed")
    
    # Income criteria
    max_income: Optional[float] = Field(None, description="Maximum income limit")
    
    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @validator('scheme_id')
    def validate_scheme_id(cls, v):
        """Validate scheme ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Scheme ID must contain only letters, numbers, underscores and hyphens')
        return v.lower()
    
    @validator('official_url')
    def validate_url(cls, v):
        """Validate URL format if provided"""
        if v and not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v
    
    @validator('documents_required', pre=True)
    def parse_documents(cls, v):
        """Parse documents from various formats"""
        if isinstance(v, str):
            return [doc.strip() for doc in v.split(',') if doc.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "scheme_id": "pm_kisan_001",
                "scheme_name": "PM Kisan Samman Nidhi",
                "description": "Income support scheme for farmers",
                "ministry": "Ministry of Agriculture",
                "category": "Agriculture",
                "eligibility": "Small and marginal farmers",
                "beneficiaries": "Farmers",
                "benefits": "₹6000 per year",
                "documents_required": ["Aadhaar", "Land records"],
                "application_process": "Online through portal",
                "max_income": 200000
            }
        }

class SchemeResponse(BaseModel):
    """Model for scheme search response"""
    scheme: SchemeModel
    relevance_score: float = Field(..., ge=0, le=1)
    match_details: Dict[str, Any] = Field(default_factory=dict)

class QueryAnalysis(BaseModel):
    """Model for query analysis results"""
    primary_intent: str
    secondary_intents: List[str] = []
    category: str
    keywords: List[str] = []
    entities: Dict[str, Any] = {}
    original_query: str
    
class UserQuery(BaseModel):
    """Model for user query storage"""
    user_email: str
    query: str
    response: str
    schemes_clicked: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    analysis: Optional[QueryAnalysis] = None

class DashboardStats(BaseModel):
    """Model for dashboard statistics"""
    total_schemes: int
    total_users: int
    total_queries: int
    queries_today: int
    schemes_by_category: Dict[str, int] = {}
    queries_by_intent: Dict[str, int] = {}
    top_schemes: List[Dict[str, Any]] = []