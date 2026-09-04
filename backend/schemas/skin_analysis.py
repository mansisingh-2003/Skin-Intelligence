from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# SKIN ANALYSIS SCHEMAS
# ============================================================
# These schemas are used to:
# - receive skin-analysis data from the frontend
# - validate AI/manual analysis data
# - return analysis results to the frontend
# - keep the API response consistent
# ============================================================


class SkinAnalysisBase(BaseModel):
    """
    Base schema containing the common fields used by
    skin analysis requests and responses.
    """

    skin_type: Optional[str] = Field(
        default=None,
        description="Detected or selected skin type."
    )

    skin_concern: Optional[str] = Field(
        default=None,
        description="Main skin concern identified during analysis."
    )

    concerns: Optional[List[str]] = Field(
        default=None,
        description="List of detected skin concerns."
    )

    skin_health_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Overall skin health score from 0 to 100."
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Confidence level of the analysis from 0 to 100."
    )

    recommendations: Optional[List[str]] = Field(
        default=None,
        description="General skincare recommendations generated from the analysis."
    )

    routine_recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommended skincare routine steps."
    )

    ingredient_recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommended skincare ingredients."
    )

    product_recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommended skincare products."
    )

    analysis_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional structured analysis information."
    )

    ai_summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of the skin analysis."
    )


# ============================================================
# CREATE SCHEMA
# ============================================================

class SkinAnalysisCreate(SkinAnalysisBase):
    """
    Schema used when creating a new skin analysis.

    user_id is supplied by the authenticated backend user
    rather than being trusted from the frontend.
    """

    pass


# ============================================================
# UPDATE SCHEMA
# ============================================================

class SkinAnalysisUpdate(BaseModel):
    """
    Schema used when updating an existing skin analysis.
    All fields are optional so individual values can be updated.
    """

    skin_type: Optional[str] = None

    skin_concern: Optional[str] = None

    concerns: Optional[List[str]] = None

    skin_health_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    recommendations: Optional[List[str]] = None

    routine_recommendations: Optional[List[str]] = None

    ingredient_recommendations: Optional[List[str]] = None

    product_recommendations: Optional[List[str]] = None

    analysis_result: Optional[Dict[str, Any]] = None

    ai_summary: Optional[str] = None


# ============================================================
# RESPONSE SCHEMA
# ============================================================

class SkinAnalysisResponse(SkinAnalysisBase):
    """
    Schema returned to the frontend after a skin analysis
    has been created or retrieved.
    """

    id: int

    user_id: int

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# LIST RESPONSE
# ============================================================

class SkinAnalysisListResponse(BaseModel):
    """
    Schema used when returning multiple analyses belonging
    to a user.
    """

    analyses: List[SkinAnalysisResponse]

    total: int


# ============================================================
# AI ANALYSIS REQUEST
# ============================================================

class SkinAnalysisRequest(BaseModel):
    """
    Schema used when the frontend requests a new AI-powered
    skin analysis.
    """

    image_url: Optional[str] = None

    image_path: Optional[str] = None

    skin_type: Optional[str] = None

    reported_concerns: Optional[List[str]] = None

    additional_information: Optional[str] = None


# ============================================================
# AI ANALYSIS RESULT
# ============================================================

class SkinAnalysisResult(BaseModel):
    """
    Standardized result returned by the AI skin-analysis
    service before it is stored in the database.
    """

    skin_type: Optional[str] = None

    skin_health_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    concerns: List[str] = Field(
        default_factory=list
    )

    recommendations: List[str] = Field(
        default_factory=list
    )

    routine_recommendations: List[str] = Field(
        default_factory=list
    )

    ingredient_recommendations: List[str] = Field(
        default_factory=list
    )

    product_recommendations: List[str] = Field(
        default_factory=list
    )

    ai_summary: Optional[str] = None

    additional_data: Dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# DASHBOARD ANALYSIS SUMMARY
# ============================================================

class SkinAnalysisSummary(BaseModel):
    """
    Lightweight analysis information used by the dashboard.
    """

    skin_health_score: Optional[float] = None

    skin_type: Optional[str] = None

    top_concern: Optional[str] = None

    confidence_score: Optional[float] = None

    last_analysis_date: Optional[datetime] = None

    ai_summary: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )