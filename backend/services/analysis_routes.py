# ============================================================
# SKIN INTELLIGENCE
# AI SKIN ANALYSIS ROUTES
# ============================================================
#
# Handles:
# - Skin image upload
# - Image validation
# - AI classification
# - Saving analysis history
#
# ============================================================

import json
import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from database import get_db
from models import User, SkinAnalysis
from auth import get_current_user

from services.skin_analyzer import (
    analyze_skin_image,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/skin-analysis",
    tags=["AI Skin Analysis"],
)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIRECTORY = "uploads"


# ============================================================
# UPLOAD + AI ANALYSIS
# ============================================================

@router.post("/upload")
async def upload_skin_image(
    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):
    """
    Upload a skin image and run the AI skin classifier.
    """

    # --------------------------------------------------------
    # VALIDATE FILE NAME
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No image file selected."
        )


    # --------------------------------------------------------
    # VALIDATE EXTENSION
    # --------------------------------------------------------

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    extension = os.path.splitext(
        file.filename
    )[1].lower()


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, JPEG, PNG and WEBP "
                "images are allowed."
            )
        )


    # --------------------------------------------------------
    # CREATE UPLOAD DIRECTORY
    # --------------------------------------------------------

    os.makedirs(
        UPLOAD_DIRECTORY,
        exist_ok=True
    )


    # --------------------------------------------------------
    # UNIQUE FILE NAME
    # --------------------------------------------------------

    filename = (
        f"user_{current_user.id}_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        filename
    )


    # --------------------------------------------------------
    # SAVE FILE
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                buffer.write(
                    chunk
                )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to save image: {error}"
            )
        )

    finally:

        await file.close()


    # --------------------------------------------------------
    # VALIDATE IMAGE
    # --------------------------------------------------------

    try:

        validation = analyze_skin_image(
            os.path.abspath(file_path)
        )

    except Exception as error:

        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=(
                f"Image validation failed: {error}"
            )
        )


    # --------------------------------------------------------
    # VALIDATION FAILURE
    # --------------------------------------------------------

    if validation.get("status") == "error":

        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=validation.get(
                "message",
                "Invalid image."
            )
        )


    # --------------------------------------------------------
    # RUN AI MODEL
    # --------------------------------------------------------
    #
    # Imported here intentionally so the model is loaded only
    # when analysis is actually requested.
    #
    # This keeps backend startup faster.
    # --------------------------------------------------------

    try:

        from services.ai_skin_analyzer import (
            analyze_with_ai,
        )

        ai_result = analyze_with_ai(
            os.path.abspath(file_path)
        )

    except Exception as error:

        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=(
                f"AI skin analysis failed: {error}"
            )
        )


    # --------------------------------------------------------
    # TOP PREDICTION
    # --------------------------------------------------------

    top_prediction = (
        ai_result.get(
            "top_prediction"
        )
    )


    primary_concern = None
    primary_confidence = None


    if top_prediction:

        primary_concern = (
            top_prediction.get(
                "label"
            )
        )

        primary_confidence = float(
            top_prediction.get(
                "confidence",
                0
            )
        )


    # --------------------------------------------------------
    # CONFIDENCE-BASED SCORE
    # --------------------------------------------------------
    #
    # This is an application score only.
    # It is NOT a medical diagnosis or medical severity score.
    # --------------------------------------------------------

    confidence_score = (
        primary_confidence * 100
        if primary_confidence is not None
        else 0
    )


    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    if confidence_score >= 80:

        risk_level = "High"

    elif confidence_score >= 50:

        risk_level = "Moderate"

    else:

        risk_level = "Low"


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    analysis_summary = (
        "AI-assisted image classification completed. "
        "The result represents model predictions and "
        "should not be considered a medical diagnosis."
    )


    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = [

        "Use gentle skincare products.",

        "Maintain consistent sun protection.",

        "Avoid introducing several new active ingredients "
        "at the same time.",

        "Consult a qualified dermatologist for persistent "
        "or concerning skin changes.",
    ]


    # --------------------------------------------------------
    # SAVE DATABASE RECORD
    # --------------------------------------------------------

    analysis_record = SkinAnalysis(

        user_id=current_user.id,

        image_path=file_path,

        analysis_type="ai",

        primary_concern=primary_concern,

        primary_confidence=primary_confidence,

        predictions=json.dumps(
            ai_result.get(
                "predictions",
                []
            )
        ),

        skin_health_score=round(
            confidence_score,
            2
        ),

        risk_level=risk_level,

        risk_factors=json.dumps(
            []
        ),

        analysis_summary=analysis_summary,

        recommendations=json.dumps(
            recommendations
        ),

        medical_note=(
            ai_result.get(
                "disclaimer"
            )
            or
            "AI-assisted analysis only. "
            "Not a medical diagnosis."
        ),
    )


    db.add(
        analysis_record
    )

    db.commit()

    db.refresh(
        analysis_record
    )


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "success",

        "message": (
            "Skin image uploaded and "
            "AI analysis completed."
        ),

        "analysis_id": analysis_record.id,

        "user_id": current_user.id,

        "image_path": file_path,

        "ai_analysis": ai_result,

        "primary_concern": primary_concern,

        "confidence": primary_confidence,

        "confidence_percent": round(
            confidence_score,
            2
        ),

        "risk_level": risk_level,

        "analysis_summary": analysis_summary,

        "recommendations": recommendations,

        "medical_note": (
            ai_result.get(
                "disclaimer"
            )
            or
            "AI-assisted analysis only. "
            "Not a medical diagnosis."
        ),
    }


# ============================================================
# GET ANALYSIS HISTORY
# ============================================================

@router.get("")
def get_analysis_history(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):
    """
    Return all previous skin analyses for the current user.
    """

    analyses = (
        db.query(SkinAnalysis)
        .filter(
            SkinAnalysis.user_id
            == current_user.id
        )
        .order_by(
            SkinAnalysis.id.desc()
        )
        .all()
    )


    result = []


    for analysis in analyses:

        predictions = []

        try:

            predictions = json.loads(
                analysis.predictions
            ) if analysis.predictions else []

        except Exception:

            predictions = []


        recommendations = []

        try:

            recommendations = json.loads(
                analysis.recommendations
            ) if analysis.recommendations else []

        except Exception:

            recommendations = []


        result.append({

            "id": analysis.id,

            "user_id": analysis.user_id,

            "image_path": analysis.image_path,

            "analysis_type": (
                analysis.analysis_type
            ),

            "primary_concern": (
                analysis.primary_concern
            ),

            "confidence": (
                analysis.primary_confidence
            ),

            "confidence_percent": (
                round(
                    analysis.primary_confidence * 100,
                    2
                )
                if analysis.primary_confidence
                is not None
                else 0
            ),

            "skin_health_score": (
                analysis.skin_health_score
            ),

            "risk_level": (
                analysis.risk_level
            ),

            "predictions": predictions,

            "analysis_summary": (
                analysis.analysis_summary
            ),

            "recommendations": (
                recommendations
            ),

            "medical_note": (
                analysis.medical_note
            ),

            "created_at": (
                analysis.created_at
            ),
        })


    return {

        "status": "success",

        "user_id": current_user.id,

        "total": len(result),

        "analyses": result,
    }