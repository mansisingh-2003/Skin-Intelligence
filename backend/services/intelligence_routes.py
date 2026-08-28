# ============================================================
# SKIN INTELLIGENCE ROUTES
# ============================================================
#
# This module provides:
# 1. Skin health score
# 2. Personalized morning/evening routine
# 3. Ingredient intelligence
# 4. Product recommendations
# 5. Progress tracking
# 6. Dashboard summary
#
# These APIs are designed around the modules required in the
# Skin Intelligence & Personalized Skincare Planner PDF.
# ============================================================

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User, SkinProfile, SkinAnalysis
from auth import get_current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/intelligence",
    tags=["Skin Intelligence"],
)


# ============================================================
# INGREDIENT REQUEST SCHEMA
# ============================================================

class IngredientAnalysisRequest(BaseModel):
    ingredient: str


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_skin_profile(
    current_user: User,
    db: Session,
):
    """
    Get the current user's skin profile.
    """

    profile = (
        db.query(SkinProfile)
        .filter(
            SkinProfile.user_id == current_user.id
        )
        .first()
    )

    return profile


def get_latest_analysis(
    current_user: User,
    db: Session,
):
    """
    Get the most recent AI skin analysis.
    """

    analysis = (
        db.query(SkinAnalysis)
        .filter(
            SkinAnalysis.user_id == current_user.id
        )
        .order_by(
            SkinAnalysis.id.desc()
        )
        .first()
    )

    return analysis


def safe_number(value, default=0):
    """
    Convert values safely to numbers.
    """

    try:

        if value is None:
            return default

        return float(value)

    except (ValueError, TypeError):

        return default


def normalize_severity(value):
    """
    Convert skin concern severity into a numeric score.
    """

    if value is None:
        return 0

    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, (int, float)):
        return max(
            0,
            min(
                3,
                float(value)
            )
        )

    text = str(value).lower().strip()

    if text in ["high", "severe", "3"]:
        return 3

    if text in ["medium", "moderate", "2"]:
        return 2

    if text in ["low", "mild", "1"]:
        return 1

    return 0


def get_skin_concerns(profile):
    """
    Extract concerns from the current skin profile.
    """

    concerns = []

    if not profile:
        return concerns

    concern_fields = {
        "acne": "Acne",
        "pigmentation": "Hyperpigmentation",
        "dryness": "Dry Skin",
        "sensitivity": "Sensitive Skin",
        "dark_circles": "Dark Circles",
        "wrinkles": "Wrinkles",
        "redness": "Redness",
    }

    for field, label in concern_fields.items():

        value = getattr(
            profile,
            field,
            None
        )

        if normalize_severity(value) > 0:
            concerns.append(label)

    return concerns


def calculate_condition_score(
    profile,
    analysis,
):
    """
    Calculate the skin-condition component.

    PDF weighting:
    Skin Condition Assessment = 35%
    """

    if not profile and not analysis:
        return 50.0

    score = 100.0

    if profile:

        concern_fields = [
            "acne",
            "pigmentation",
            "dryness",
            "sensitivity",
            "dark_circles",
            "wrinkles",
            "redness",
        ]

        for field in concern_fields:

            value = getattr(
                profile,
                field,
                None
            )

            severity = normalize_severity(
                value
            )

            if severity == 1:
                score -= 4

            elif severity == 2:
                score -= 8

            elif severity == 3:
                score -= 12

    if analysis:

        confidence = safe_number(
            getattr(
                analysis,
                "confidence",
                None
            ),
            0
        )

        # Confidence is not treated as medical accuracy.
        # It only contributes a small consistency signal.
        if confidence > 0:
            score = (
                score * 0.75
                + min(confidence * 100, 100) * 0.25
            )

    return round(
        max(
            0,
            min(
                100,
                score
            )
        ),
        2
    )


def get_score_label(score):

    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Good"

    if score >= 55:
        return "Fair"

    return "Needs Attention"


def get_primary_skin_type(profile):

    if not profile:
        return "Not specified"

    value = getattr(
        profile,
        "skin_type",
        None
    )

    if not value:
        return "Not specified"

    return str(value)


# ============================================================
# 1. SKIN HEALTH SCORE
# ============================================================

@router.get("/health-score")
def get_health_score(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = get_user_skin_profile(
        current_user,
        db
    )

    analysis = get_latest_analysis(
        current_user,
        db
    )

    # --------------------------------------------------------
    # CONDITION SCORE
    # PDF: 35%
    # --------------------------------------------------------

    condition_score = calculate_condition_score(
        profile,
        analysis
    )

    # --------------------------------------------------------
    # LIFESTYLE
    # PDF: 20%
    #
    # Current database may not yet contain dedicated lifestyle
    # tracking fields, therefore use a neutral baseline.
    # --------------------------------------------------------

    lifestyle_score = 70.0

    # --------------------------------------------------------
    # SLEEP
    # PDF: 15%
    # --------------------------------------------------------

    sleep_score = 70.0

    if profile:

        sleep_quality = getattr(
            profile,
            "sleep_quality",
            None
        )

        if sleep_quality is not None:

            text = str(
                sleep_quality
            ).lower()

            if "excellent" in text:
                sleep_score = 95

            elif "good" in text:
                sleep_score = 85

            elif "average" in text:
                sleep_score = 70

            elif "poor" in text:
                sleep_score = 45

    # --------------------------------------------------------
    # ROUTINE CONSISTENCY
    # PDF: 20%
    #
    # Until routine adherence tracking is connected,
    # use a neutral baseline.
    # --------------------------------------------------------

    routine_score = 50.0

    # --------------------------------------------------------
    # HYDRATION
    # PDF: 10%
    # --------------------------------------------------------

    hydration_score = 70.0

    if profile:

        water_intake = getattr(
            profile,
            "water_intake",
            None
        )

        if water_intake is not None:

            water = safe_number(
                water_intake,
                2
            )

            hydration_score = min(
                100,
                max(
                    20,
                    (water / 3.0) * 100
                )
            )

    # --------------------------------------------------------
    # WEIGHTED SCORE
    # --------------------------------------------------------

    overall_score = (

        condition_score * 0.35

        + lifestyle_score * 0.20

        + sleep_score * 0.15

        + routine_score * 0.20

        + hydration_score * 0.10
    )

    overall_score = round(
        max(
            0,
            min(
                100,
                overall_score
            )
        ),
        2
    )

    return {

        "status": "success",

        "user_id": current_user.id,

        "health_score": overall_score,

        "label": get_score_label(
            overall_score
        ),

        "components": {

            "skin_condition": {
                "score": condition_score,
                "weight": 35,
            },

            "lifestyle": {
                "score": lifestyle_score,
                "weight": 20,
            },

            "sleep_quality": {
                "score": sleep_score,
                "weight": 15,
            },

            "routine_consistency": {
                "score": routine_score,
                "weight": 20,
            },

            "hydration": {
                "score": round(
                    hydration_score,
                    2
                ),
                "weight": 10,
            },
        },

        "note": (
            "This is an application-level wellness "
            "score and not a medical diagnosis."
        ),
    }


# ============================================================
# 2. PERSONALIZED ROUTINE
# ============================================================

@router.get("/routine")
def get_personalized_routine(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = get_user_skin_profile(
        current_user,
        db
    )

    skin_type = get_primary_skin_type(
        profile
    )

    concerns = get_skin_concerns(
        profile
    )

    # --------------------------------------------------------
    # BASE MORNING ROUTINE
    # --------------------------------------------------------

    morning = [

        {
            "step": 1,
            "category": "Cleansing",
            "product_type": "Gentle Cleanser",
            "reason": "Remove overnight oil and impurities.",
        },

        {
            "step": 2,
            "category": "Treatment",
            "product_type": "Antioxidant Serum",
            "reason": "Support skin protection and even appearance.",
        },

        {
            "step": 3,
            "category": "Moisturizing",
            "product_type": "Moisturizer",
            "reason": "Maintain the skin barrier.",
        },

        {
            "step": 4,
            "category": "Sun Protection",
            "product_type": "Broad-Spectrum Sunscreen SPF 30+",
            "reason": "Protect against UV exposure.",
        },
    ]

    # --------------------------------------------------------
    # EVENING ROUTINE
    # --------------------------------------------------------

    evening = [

        {
            "step": 1,
            "category": "Cleansing",
            "product_type": "Gentle Cleanser",
            "reason": "Remove sunscreen, oil and impurities.",
        },

        {
            "step": 2,
            "category": "Treatment",
            "product_type": "Targeted Treatment Serum",
            "reason": "Address the user's primary skin concerns.",
        },

        {
            "step": 3,
            "category": "Moisturizing",
            "product_type": "Barrier Moisturizer",
            "reason": "Support overnight skin-barrier care.",
        },
    ]

    # --------------------------------------------------------
    # CONCERN-SPECIFIC ADVICE
    # --------------------------------------------------------

    concern_recommendations = []

    for concern in concerns:

        if concern == "Acne":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Consider gentle, non-comedogenic products "
                    "and avoid over-exfoliation."
                ),
            })

        elif concern == "Hyperpigmentation":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Prioritize daily sunscreen and "
                    "consistent brightening care."
                ),
            })

        elif concern == "Dry Skin":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Prefer gentle cleansing and "
                    "barrier-supporting moisturizers."
                ),
            })

        elif concern == "Sensitive Skin":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Prefer fragrance-free products and "
                    "introduce new products gradually."
                ),
            })

        elif concern == "Wrinkles":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Prioritize sun protection and "
                    "consistent skin-barrier care."
                ),
            })

        elif concern == "Redness":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Use gentle products and avoid "
                    "known irritants."
                ),
            })

        elif concern == "Dark Circles":

            concern_recommendations.append({
                "concern": concern,
                "recommendation": (
                    "Maintain adequate sleep and use "
                    "gentle eye-area skincare."
                ),
            })

    return {

        "status": "success",

        "user_id": current_user.id,

        "skin_type": skin_type,

        "identified_concerns": concerns,

        "morning_routine": morning,

        "evening_routine": evening,

        "weekly_plan": [

            {
                "day": "Monday",
                "focus": "Basic skincare and hydration",
            },

            {
                "day": "Tuesday",
                "focus": "Basic skincare",
            },

            {
                "day": "Wednesday",
                "focus": "Gentle treatment",
            },

            {
                "day": "Thursday",
                "focus": "Basic skincare and hydration",
            },

            {
                "day": "Friday",
                "focus": "Basic skincare",
            },

            {
                "day": "Saturday",
                "focus": "Gentle treatment",
            },

            {
                "day": "Sunday",
                "focus": "Recovery and barrier care",
            },
        ],

        "personalized_recommendations": (
            concern_recommendations
        ),

        "note": (
            "Routine suggestions are informational "
            "and should not replace professional "
            "medical advice."
        ),
    }


# ============================================================
# 3. INGREDIENT INTELLIGENCE
# ============================================================

INGREDIENT_DATABASE = {

    "niacinamide": {

        "name": "Niacinamide",

        "category": "Vitamin B3",

        "benefits": [
            "Supports skin barrier",
            "Helps improve uneven appearance",
            "Can support oil-control routines",
        ],

        "suitable_for": [
            "Oily Skin",
            "Acne",
            "Hyperpigmentation",
            "Uneven Skin Tone",
        ],

        "caution": (
            "Introduce gradually if the skin is highly sensitive."
        ),
    },

    "vitamin c": {

        "name": "Vitamin C",

        "category": "Antioxidant",

        "benefits": [
            "Antioxidant support",
            "Supports brighter-looking skin",
            "Helps protect against environmental stress",
        ],

        "suitable_for": [
            "Hyperpigmentation",
            "Dark Spots",
            "Uneven Skin Tone",
        ],

        "caution": (
            "Patch testing is recommended when introducing "
            "a new active ingredient."
        ),
    },

    "hyaluronic acid": {

        "name": "Hyaluronic Acid",

        "category": "Humectant",

        "benefits": [
            "Helps attract moisture",
            "Supports hydrated-looking skin",
        ],

        "suitable_for": [
            "Dry Skin",
            "Sensitive Skin",
            "Dehydrated Skin",
        ],

        "caution": (
            "Use with a suitable moisturizer to help "
            "support the skin barrier."
        ),
    },

    "salicylic acid": {

        "name": "Salicylic Acid",

        "category": "BHA",

        "benefits": [
            "Helps unclog pores",
            "Supports acne-prone skincare routines",
        ],

        "suitable_for": [
            "Acne",
            "Oily Skin",
        ],

        "caution": (
            "Overuse may cause dryness or irritation."
        ),
    },

    "ceramides": {

        "name": "Ceramides",

        "category": "Skin Barrier",

        "benefits": [
            "Supports the skin barrier",
            "Helps reduce moisture loss",
        ],

        "suitable_for": [
            "Dry Skin",
            "Sensitive Skin",
        ],

        "caution": (
            "Generally used as a barrier-supporting ingredient."
        ),
    },

    "peptides": {

        "name": "Peptides",

        "category": "Skin Conditioning",

        "benefits": [
            "Supports skin-conditioning routines",
            "Commonly used in anti-aging skincare",
        ],

        "suitable_for": [
            "Fine Lines",
            "Wrinkles",
        ],

        "caution": (
            "Product formulation and concentration matter."
        ),
    },

    "retinoids": {

        "name": "Retinoids",

        "category": "Vitamin A Derivatives",

        "benefits": [
            "Commonly used in anti-aging routines",
            "May support acne-focused skincare",
        ],

        "suitable_for": [
            "Acne",
            "Fine Lines",
            "Wrinkles",
        ],

        "caution": (
            "Retinoids can cause irritation and require "
            "careful introduction. Professional guidance "
            "may be appropriate."
        ),
    },

    "aha": {

        "name": "AHAs",

        "category": "Chemical Exfoliant",

        "benefits": [
            "Supports exfoliation",
            "Can improve skin texture appearance",
        ],

        "suitable_for": [
            "Uneven Skin Tone",
            "Texture",
            "Dull-looking Skin",
        ],

        "caution": (
            "Avoid excessive exfoliation, especially "
            "with sensitive skin."
        ),
    },

    "bha": {

        "name": "BHAs",

        "category": "Chemical Exfoliant",

        "benefits": [
            "Supports pore cleansing",
            "Useful in oily-skin routines",
        ],

        "suitable_for": [
            "Acne",
            "Oily Skin",
        ],

        "caution": (
            "Can cause dryness or irritation if overused."
        ),
    },
}


@router.post("/ingredients/analyze")
def analyze_ingredient(
    request: IngredientAnalysisRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    ingredient = (
        request.ingredient
        .lower()
        .strip()
    )

    if not ingredient:

        raise HTTPException(
            status_code=400,
            detail="Ingredient name is required.",
        )

    result = INGREDIENT_DATABASE.get(
        ingredient
    )

    if result is None:

        return {

            "status": "success",

            "found": False,

            "ingredient": request.ingredient,

            "message": (
                "Ingredient is not currently available "
                "in the built-in intelligence database."
            ),

            "recommendation": (
                "Check the complete product ingredient "
                "list and consult a qualified professional "
                "if you have allergies or sensitivities."
            ),
        }

    profile = get_user_skin_profile(
        current_user,
        db
    )

    concerns = get_skin_concerns(
        profile
    )

    suitable = any(
        item in concerns
        for item in result["suitable_for"]
    )

    return {

        "status": "success",

        "found": True,

        "ingredient": result["name"],

        "category": result["category"],

        "benefits": result["benefits"],

        "suitable_for": result["suitable_for"],

        "personalized_match": suitable,

        "caution": result["caution"],

        "user_skin_concerns": concerns,

        "note": (
            "Ingredient suitability is informational "
            "and does not replace professional advice."
        ),
    }


@router.get("/ingredients")
def get_ingredients(
    current_user: User = Depends(
        get_current_user
    ),
):

    return {

        "status": "success",

        "count": len(
            INGREDIENT_DATABASE
        ),

        "ingredients": list(
            INGREDIENT_DATABASE.values()
        ),
    }


# ============================================================
# 4. PRODUCT RECOMMENDATION ENGINE
# ============================================================

PRODUCT_DATABASE = [

    {
        "name": "Gentle Hydrating Cleanser",
        "category": "Face Wash",
        "skin_types": [
            "Dry",
            "Sensitive",
            "Normal",
        ],
        "ingredients": [
            "Ceramides",
            "Hyaluronic Acid",
        ],
        "budget": "Budget",
        "score": 88,
    },

    {
        "name": "Oil Control Cleanser",
        "category": "Face Wash",
        "skin_types": [
            "Oily",
            "Combination",
        ],
        "ingredients": [
            "Salicylic Acid",
            "Niacinamide",
        ],
        "budget": "Budget",
        "score": 90,
    },

    {
        "name": "Barrier Support Moisturizer",
        "category": "Moisturizer",
        "skin_types": [
            "Dry",
            "Sensitive",
            "Normal",
        ],
        "ingredients": [
            "Ceramides",
            "Hyaluronic Acid",
        ],
        "budget": "Mid-range",
        "score": 92,
    },

    {
        "name": "Lightweight Oil Control Moisturizer",
        "category": "Moisturizer",
        "skin_types": [
            "Oily",
            "Combination",
        ],
        "ingredients": [
            "Niacinamide",
        ],
        "budget": "Budget",
        "score": 89,
    },

    {
        "name": "Broad Spectrum Sunscreen SPF 50",
        "category": "Sunscreen",
        "skin_types": [
            "All",
        ],
        "ingredients": [
            "UV Filters",
        ],
        "budget": "Mid-range",
        "score": 95,
    },

    {
        "name": "Brightening Antioxidant Serum",
        "category": "Serum",
        "skin_types": [
            "Normal",
            "Combination",
            "Oily",
        ],
        "ingredients": [
            "Vitamin C",
            "Niacinamide",
        ],
        "budget": "Mid-range",
        "score": 91,
    },

    {
        "name": "Hydration Serum",
        "category": "Serum",
        "skin_types": [
            "Dry",
            "Sensitive",
            "Normal",
        ],
        "ingredients": [
            "Hyaluronic Acid",
        ],
        "budget": "Budget",
        "score": 90,
    },
]


@router.get("/products/recommend")
def recommend_products(
    category: Optional[str] = None,

    budget: Optional[str] = None,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):

    profile = get_user_skin_profile(
        current_user,
        db
    )

    skin_type = get_primary_skin_type(
        profile
    )

    concerns = get_skin_concerns(
        profile
    )

    normalized_skin_type = skin_type.lower()

    recommendations = []

    for product in PRODUCT_DATABASE:

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if category:

            if product["category"].lower() != category.lower():
                continue

        # ----------------------------------------------------
        # Budget filter
        # ----------------------------------------------------

        if budget:

            if product["budget"].lower() != budget.lower():
                continue

        # ----------------------------------------------------
        # Calculate personalized score
        # ----------------------------------------------------

        score = product["score"]

        product_skin_types = [
            item.lower()
            for item in product["skin_types"]
        ]

        if (
            "all" in product_skin_types
            or normalized_skin_type in product_skin_types
        ):
            score += 5

        # ----------------------------------------------------
        # Ingredient match
        # ----------------------------------------------------

        ingredient_text = " ".join(
            product["ingredients"]
        ).lower()

        if (
            "acne" in concerns
            and "salicylic" in ingredient_text
        ):
            score += 5

        if (
            "hyperpigmentation" in concerns
            and "vitamin c" in ingredient_text
        ):
            score += 5

        if (
            "dry skin" in concerns
            and (
                "hyaluronic" in ingredient_text
                or "ceramides" in ingredient_text
            )
        ):
            score += 5

        if (
            "sensitive skin" in concerns
            and "ceramides" in ingredient_text
        ):
            score += 5

        recommendations.append({

            **product,

            "personalized_score": min(
                score,
                100
            ),

            "match_reason": (
                "Recommended based on your "
                "skin profile and identified concerns."
            ),
        })

    recommendations.sort(
        key=lambda item: item[
            "personalized_score"
        ],
        reverse=True
    )

    return {

        "status": "success",

        "user_id": current_user.id,

        "skin_type": skin_type,

        "concerns": concerns,

        "recommendations": recommendations[:10],

        "note": (
            "These are informational product suggestions. "
            "Always review the full ingredient list."
        ),
    }


# ============================================================
# 5. PROGRESS TRACKING
# ============================================================

@router.get("/progress")
def get_progress(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    analyses = (
        db.query(SkinAnalysis)
        .filter(
            SkinAnalysis.user_id
            == current_user.id
        )
        .order_by(
            SkinAnalysis.id.asc()
        )
        .all()
    )

    history = []

    for analysis in analyses:

        confidence = safe_number(
            getattr(
                analysis,
                "confidence",
                None
            ),
            0
        )

        history.append({

            "analysis_id": analysis.id,

            "confidence": round(
                confidence * 100,
                2
            )
            if confidence <= 1
            else round(
                confidence,
                2
            ),

            "image_path": getattr(
                analysis,
                "image_path",
                None
            ),
        })

    latest_score = None

    if history:

        latest_score = history[-1][
            "confidence"
        ]

    return {

        "status": "success",

        "user_id": current_user.id,

        "total_assessments": len(
            history
        ),

        "latest_assessment_score": latest_score,

        "history": history,

        "tracking_features": {

            "skin_progress_monitoring": True,

            "assessment_history": True,

            "trend_analysis": (
                len(history) >= 2
            ),

            "before_after_comparison": (
                len(history) >= 2
            ),

            "routine_adherence_tracking": False,
        },

        "message": (
            "Assessment history is available. "
            "Routine adherence tracking will be "
            "connected when the routine checklist "
            "storage is added."
        ),
    }


# ============================================================
# 6. DASHBOARD SUMMARY
# ============================================================

@router.get("/dashboard")
def get_intelligence_dashboard(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = get_user_skin_profile(
        current_user,
        db
    )

    analysis = get_latest_analysis(
        current_user,
        db
    )

    condition_score = calculate_condition_score(
        profile,
        analysis
    )

    concerns = get_skin_concerns(
        profile
    )

    # Same weighted baseline used by health-score endpoint.
    overall_score = round(
        (
            condition_score * 0.35
            + 70 * 0.20
            + 70 * 0.15
            + 50 * 0.20
            + 70 * 0.10
        ),
        2
    )

    assessment_count = (
        db.query(SkinAnalysis)
        .filter(
            SkinAnalysis.user_id
            == current_user.id
        )
        .count()
    )

    return {

        "status": "success",

        "user": {

            "id": current_user.id,

            "name": getattr(
                current_user,
                "name",
                "User"
            ),

            "email": getattr(
                current_user,
                "email",
                None
            ),
        },

        "skin": {

            "skin_type": get_primary_skin_type(
                profile
            ),

            "concerns": concerns,

            "health_score": overall_score,

            "health_label": get_score_label(
                overall_score
            ),
        },

        "modules": {

            "skin_assessment": True,

            "health_scoring": True,

            "personalized_routine": True,

            "ingredient_intelligence": True,

            "product_recommendations": True,

            "progress_tracking": True,

            "notifications": False,

            "reports": False,
        },

        "assessment_count": assessment_count,

        "latest_analysis_id": (
            analysis.id
            if analysis
            else None
        ),

        "message": (
            "Skin Intelligence dashboard data "
            "generated successfully."
        ),
    }


# ============================================================
# 7. GENERAL RECOMMENDATIONS
# ============================================================

@router.get("/recommendations")
def get_general_recommendations(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = get_user_skin_profile(
        current_user,
        db
    )

    concerns = get_skin_concerns(
        profile
    )

    recommendations = [

        {
            "title": "Daily Sun Protection",
            "priority": "High",
            "description": (
                "Use broad-spectrum sunscreen "
                "during daytime."
            ),
        },

        {
            "title": "Gentle Cleansing",
            "priority": "High",
            "description": (
                "Avoid unnecessarily harsh cleansing "
                "that can disturb the skin barrier."
            ),
        },

        {
            "title": "Stay Hydrated",
            "priority": "Medium",
            "description": (
                "Maintain regular water intake as "
                "part of a healthy lifestyle."
            ),
        },

        {
            "title": "Introduce Products Gradually",
            "priority": "Medium",
            "description": (
                "Add new active ingredients one at "
                "a time and monitor skin response."
            ),
        },
    ]

    if "Acne" in concerns:

        recommendations.append({

            "title": "Acne-Focused Care",

            "priority": "High",

            "description": (
                "Consider non-comedogenic products "
                "and avoid excessive product layering."
            ),
        })

    if "Dry Skin" in concerns:

        recommendations.append({

            "title": "Barrier Support",

            "priority": "High",

            "description": (
                "Prefer moisturizers containing "
                "barrier-supporting ingredients."
            ),
        })

    if "Sensitive Skin" in concerns:

        recommendations.append({

            "title": "Sensitivity Protection",

            "priority": "High",

            "description": (
                "Prefer gentle and fragrance-free "
                "products when appropriate."
            ),
        })

    return {

        "status": "success",

        "user_id": current_user.id,

        "identified_concerns": concerns,

        "recommendations": recommendations,

        "note": (
            "Recommendations are educational and "
            "not a medical diagnosis."
        ),
    }