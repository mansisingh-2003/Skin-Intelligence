# ============================================================
# SKIN INTELLIGENCE
# SKIN PROFILE PYDANTIC SCHEMAS
# ============================================================

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# BASE PROFILE
# ============================================================

class SkinProfileBase(BaseModel):
    """
    Fields used by the frontend skin profile form.
    """

    skin_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    age_group: Optional[str] = Field(
        default=None,
        max_length=50
    )

    concerns: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    allergies: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    sensitivities: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    lifestyle: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    sleep_quality: Optional[str] = Field(
        default=None,
        max_length=50
    )

    water_intake: Optional[float] = Field(
        default=None,
        ge=0,
        le=20
    )

    environmental_exposure: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    additional_notes: Optional[str] = Field(
        default=None,
        max_length=2000
    )


# ============================================================
# CREATE
# ============================================================

class SkinProfileCreate(
    SkinProfileBase
):
    """
    Schema for creating a skin profile.
    """

    pass


# ============================================================
# UPDATE
# ============================================================

class SkinProfileUpdate(
    SkinProfileBase
):
    """
    Schema for updating a skin profile.
    """

    pass


# ============================================================
# RESPONSE
# ============================================================

class SkinProfileResponse(
    SkinProfileBase
):
    """
    Profile returned by the backend.
    """

    id: int

    user_id: int

    class Config:
        from_attributes = True