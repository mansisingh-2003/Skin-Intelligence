from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, SkinProfile
from auth import get_current_user

from schemas.skin_profile import (
    SkinProfileCreate,
    SkinProfileUpdate,
)


router = APIRouter(
    prefix="/skin-profile",
    tags=["Skin Profile"],
)


def profile_response(profile: SkinProfile):
    return {
        "status": "success",
        "exists": True,

        "skin_profile_id": profile.id,
        "id": profile.id,
        "user_id": profile.user_id,

        "skin_type": profile.skin_type or "",
        "age_group": profile.age_group or "",

        "concerns": profile.skin_concerns or "",
        "skin_concerns": profile.skin_concerns or "",

        "allergies": profile.allergies or "",
        "sensitivities": profile.sensitivities or "",

        "lifestyle": profile.lifestyle_habits or "",
        "lifestyle_habits": profile.lifestyle_habits or "",

        "sleep_quality": profile.sleep_quality or "",

        "water_intake": (
            profile.water_intake
            if profile.water_intake is not None
            else ""
        ),

        "environmental_exposure": (
            profile.environmental_exposure or ""
        ),

        "additional_notes": (
            profile.additional_notes or ""
        ),
    }


# ============================================================
# GET
# ============================================================

@router.get("")
def get_skin_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(SkinProfile)
        .filter(SkinProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        return {
            "status": "success",
            "exists": False,
            "id": None,
            "skin_profile_id": None,
            "user_id": current_user.id,

            "skin_type": "",
            "age_group": "",
            "concerns": "",
            "skin_concerns": "",
            "allergies": "",
            "sensitivities": "",
            "lifestyle": "",
            "lifestyle_habits": "",
            "sleep_quality": "",
            "water_intake": "",
            "environmental_exposure": "",
            "additional_notes": "",
        }

    return profile_response(profile)


# ============================================================
# CREATE / SAVE
# ============================================================

@router.post("")
def create_skin_profile(
    profile_data: SkinProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(SkinProfile)
        .filter(SkinProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        profile = SkinProfile(
            user_id=current_user.id
        )

        db.add(profile)

    # Save every field
    profile.skin_type = profile_data.skin_type or ""
    profile.age_group = profile_data.age_group or ""
    profile.skin_concerns = profile_data.concerns or ""
    profile.allergies = profile_data.allergies or ""
    profile.sensitivities = profile_data.sensitivities or ""
    profile.lifestyle_habits = profile_data.lifestyle or ""
    profile.sleep_quality = profile_data.sleep_quality or ""
    profile.water_intake = profile_data.water_intake
    profile.environmental_exposure = (
        profile_data.environmental_exposure or ""
    )
    profile.additional_notes = (
        profile_data.additional_notes or ""
    )

    try:
        db.commit()
        db.refresh(profile)

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save skin profile: {str(e)}"
        )

    result = profile_response(profile)

    result["message"] = "Skin profile saved successfully."

    return result


# ============================================================
# UPDATE
# ============================================================

@router.put("")
def update_skin_profile(
    profile_data: SkinProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(SkinProfile)
        .filter(SkinProfile.user_id == current_user.id)
        .first()
    )

    # If it does not exist, create it
    if profile is None:
        profile = SkinProfile(
            user_id=current_user.id
        )

        db.add(profile)

    # Update supplied values
    if profile_data.skin_type is not None:
        profile.skin_type = profile_data.skin_type

    if profile_data.age_group is not None:
        profile.age_group = profile_data.age_group

    if profile_data.concerns is not None:
        profile.skin_concerns = profile_data.concerns

    if profile_data.allergies is not None:
        profile.allergies = profile_data.allergies

    if profile_data.sensitivities is not None:
        profile.sensitivities = profile_data.sensitivities

    if profile_data.lifestyle is not None:
        profile.lifestyle_habits = profile_data.lifestyle

    if profile_data.sleep_quality is not None:
        profile.sleep_quality = profile_data.sleep_quality

    if profile_data.water_intake is not None:
        profile.water_intake = profile_data.water_intake

    if profile_data.environmental_exposure is not None:
        profile.environmental_exposure = (
            profile_data.environmental_exposure
        )

    if profile_data.additional_notes is not None:
        profile.additional_notes = (
            profile_data.additional_notes
        )

    try:
        db.commit()
        db.refresh(profile)

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not update skin profile: {str(e)}"
        )

    result = profile_response(profile)

    result["message"] = "Skin profile updated successfully."

    return result