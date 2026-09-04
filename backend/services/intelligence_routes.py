# ============================================================
# SKIN INTELLIGENCE ROUTES
# ============================================================
#
# Personalized intelligence engine for:
# - Health score
# - Personalized routine
# - Ingredient intelligence
# - Product recommendations
# - Progress tracking
# - Dashboard
# - General recommendations
#
# IMPORTANT:
# This file uses the CURRENT SkinProfile database structure:
#
# skin_type
# age_group
# skin_concerns
# allergies
# sensitivities
# lifestyle_habits
# sleep_quality
# water_intake
# environmental_exposure
# additional_notes
#
# Every endpoint uses the currently logged-in user's profile.
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
# REQUEST SCHEMA
# ============================================================

class IngredientAnalysisRequest(BaseModel):
    ingredient: str


# ============================================================
# PROFILE HELPERS
# ============================================================

def get_user_skin_profile(
    current_user: User,
    db: Session,
):
    """
    Get the skin profile belonging to the currently
    authenticated user.
    """

    return (
        db.query(SkinProfile)
        .filter(
            SkinProfile.user_id == current_user.id
        )
        .first()
    )


def get_latest_analysis(
    current_user: User,
    db: Session,
):
    """
    Get the latest AI skin analysis belonging to
    the currently authenticated user.
    """

    return (
        db.query(SkinAnalysis)
        .filter(
            SkinAnalysis.user_id == current_user.id
        )
        .order_by(
            SkinAnalysis.id.desc()
        )
        .first()
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_number(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except (ValueError, TypeError):
        return default


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def text_contains(text, words):
    """
    Check whether any keyword exists in a text field.
    """

    text = clean_text(text).lower()

    return any(
        word.lower() in text
        for word in words
    )


def get_primary_skin_type(profile):
    if not profile:
        return "Not specified"

    value = clean_text(
        getattr(
            profile,
            "skin_type",
            ""
        )
    )

    return value or "Not specified"


# ============================================================
# CONCERN EXTRACTION
# ============================================================

def get_skin_concerns(profile):
    """
    Convert the current database's single skin_concerns
    text field into standardized concern labels.

    Example:

    "Acne, dark spots"

    becomes:

    ["Acne", "Dark Spots"]
    """

    if not profile:
        return []

    raw = clean_text(
        getattr(
            profile,
            "skin_concerns",
            ""
        )
    )

    if not raw:
        return []

    text = raw.lower()

    concerns = []

    concern_keywords = [
        (
            [
                "acne",
                "pimple",
                "pimples",
                "breakout",
                "breakouts",
            ],
            "Acne",
        ),
        (
            [
                "hyperpigmentation",
                "pigmentation",
            ],
            "Hyperpigmentation",
        ),
        (
            [
                "dark spot",
                "dark spots",
            ],
            "Dark Spots",
        ),
        (
            [
                "dry",
                "dryness",
            ],
            "Dry Skin",
        ),
        (
            [
                "oily",
                "oiliness",
                "excess oil",
            ],
            "Oily Skin",
        ),
        (
            [
                "sensitive",
                "sensitivity",
            ],
            "Sensitive Skin",
        ),
        (
            [
                "wrinkle",
                "wrinkles",
            ],
            "Wrinkles",
        ),
        (
            [
                "fine line",
                "fine lines",
            ],
            "Fine Lines",
        ),
        (
            [
                "redness",
                "red",
            ],
            "Redness",
        ),
        (
            [
                "uneven tone",
                "uneven skin tone",
            ],
            "Uneven Skin Tone",
        ),
        (
            [
                "texture",
                "rough skin",
            ],
            "Texture",
        ),
        (
            [
                "dull",
                "dullness",
            ],
            "Dull-looking Skin",
        ),
    ]

    for keywords, label in concern_keywords:

        if any(
            keyword in text
            for keyword in keywords
        ):
            concerns.append(label)

    # Remove duplicates while preserving order.
    return list(
        dict.fromkeys(concerns)
    )


# ============================================================
# LIFESTYLE SCORE
# ============================================================

def calculate_lifestyle_score(profile):
    """
    Calculate lifestyle component.

    Base score = 70.

    Positive signals:
    - exercise
    - active lifestyle
    - healthy habits

    Negative signals:
    - smoking
    - high stress
    - unhealthy lifestyle
    """

    if not profile:
        return 70.0

    lifestyle = clean_text(
        getattr(
            profile,
            "lifestyle_habits",
            ""
        )
    ).lower()

    if not lifestyle:
        return 70.0

    score = 70.0

    if text_contains(
        lifestyle,
        [
            "exercise",
            "exercises",
            "workout",
            "walking",
            "active",
            "yoga",
            "gym",
        ],
    ):
        score += 10

    if text_contains(
        lifestyle,
        [
            "healthy",
            "balanced diet",
            "balanced",
            "fruit",
            "vegetable",
        ],
    ):
        score += 5

    if text_contains(
        lifestyle,
        [
            "smoking",
            "smoke",
            "smoker",
        ],
    ):
        score -= 15

    if text_contains(
        lifestyle,
        [
            "high stress",
            "stress",
            "stressed",
        ],
    ):
        score -= 10

    if text_contains(
        lifestyle,
        [
            "poor diet",
            "junk food",
            "unhealthy",
        ],
    ):
        score -= 8

    return round(
        max(
            0,
            min(
                100,
                score
            )
        ),
        2,
    )


# ============================================================
# SLEEP SCORE
# ============================================================

def calculate_sleep_score(profile):
    if not profile:
        return 70.0

    sleep = clean_text(
        getattr(
            profile,
            "sleep_quality",
            ""
        )
    ).lower()

    if not sleep:
        return 70.0

    if sleep in [
        "excellent",
        "very good",
        "great",
    ]:
        return 95.0

    if sleep in [
        "good",
    ]:
        return 85.0

    if sleep in [
        "average",
        "fair",
        "moderate",
    ]:
        return 70.0

    if sleep in [
        "poor",
        "bad",
    ]:
        return 45.0

    if "excellent" in sleep:
        return 95.0

    if "good" in sleep:
        return 85.0

    if "poor" in sleep:
        return 45.0

    return 70.0


# ============================================================
# HYDRATION SCORE
# ============================================================

def calculate_hydration_score(profile):
    """
    Convert water intake into a simple 0-100 score.

    Around 2.5 L/day is treated as a strong hydration
    signal for this application.

    This is a wellness indicator, not medical advice.
    """

    if not profile:
        return 70.0

    water = safe_number(
        getattr(
            profile,
            "water_intake",
            None
        ),
        0.0,
    )

    if water <= 0:
        return 60.0

    score = (
        water / 2.5
    ) * 100

    return round(
        max(
            20,
            min(
                100,
                score
            )
        ),
        2,
    )


# ============================================================
# CONDITION SCORE
# ============================================================

def calculate_condition_score(
    profile,
    analysis=None,
):
    """
    Calculate the skin-condition component.

    Weight in final score:
    35%

    The current database stores concerns as text,
    so we count recognized concerns rather than trying
    to access nonexistent fields such as profile.acne.
    """

    if not profile and not analysis:
        return 50.0

    score = 100.0

    concerns = get_skin_concerns(
        profile
    )

    # Each recognized concern has a modest impact.
    score -= len(concerns) * 8

    # Extra adjustment for sensitivity.
    if "Sensitive Skin" in concerns:
        score -= 4

    # Environmental exposure can affect the wellness score.
    if profile:

        environment = clean_text(
            getattr(
                profile,
                "environmental_exposure",
                ""
            )
        ).lower()

        if environment:

            if text_contains(
                environment,
                [
                    "high pollution",
                    "heavy pollution",
                    "pollution",
                ],
            ):
                score -= 4

            if text_contains(
                environment,
                [
                    "high sun",
                    "strong sun",
                    "sun exposure",
                ],
            ):
                score -= 3

    # Use the CURRENT SkinAnalysis field.
    if analysis:

        confidence = safe_number(
            getattr(
                analysis,
                "primary_confidence",
                None
            ),
            0.0,
        )

        if confidence > 1:
            confidence = confidence / 100

        confidence = max(
            0,
            min(
                1,
                confidence
            )
        )

        # Small consistency contribution.
        score = (
            score * 0.90
            + (confidence * 100) * 0.10
        )

    return round(
        max(
            0,
            min(
                100,
                score
            )
        ),
        2,
    )


# ============================================================
# ROUTINE CONSISTENCY SCORE
# ============================================================

def calculate_routine_score(profile):
    """
    There is currently no database table for daily
    routine completion.

    Therefore we use a reasonable starting value instead
    of pretending that routine adherence is already tracked.
    """

    if not profile:
        return 50.0

    return 65.0


# ============================================================
# FINAL HEALTH SCORE
# ============================================================

def calculate_health_score(
    profile,
    analysis=None,
):
    """
    Weighted Skin Health Score.

    Skin Condition       35%
    Lifestyle            20%
    Sleep                15%
    Routine Consistency  20%
    Hydration            10%
    """

    condition_score = calculate_condition_score(
        profile,
        analysis,
    )

    lifestyle_score = calculate_lifestyle_score(
        profile
    )

    sleep_score = calculate_sleep_score(
        profile
    )

    routine_score = calculate_routine_score(
        profile
    )

    hydration_score = calculate_hydration_score(
        profile
    )

    overall = (
        condition_score * 0.35
        + lifestyle_score * 0.20
        + sleep_score * 0.15
        + routine_score * 0.20
        + hydration_score * 0.10
    )

    return {
        "overall": round(
            max(
                0,
                min(
                    100,
                    overall
                )
            ),
            2,
        ),

        "condition": round(
            condition_score,
            2,
        ),

        "lifestyle": round(
            lifestyle_score,
            2,
        ),

        "sleep": round(
            sleep_score,
            2,
        ),

        "routine": round(
            routine_score,
            2,
        ),

        "hydration": round(
            hydration_score,
            2,
        ),
    }


# ============================================================
# SCORE LABEL
# ============================================================

def get_score_label(score):

    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Good"

    if score >= 55:
        return "Fair"

    return "Needs Attention"


# ============================================================
# 1. HEALTH SCORE ENDPOINT
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

    scores = calculate_health_score(
        profile,
        analysis,
    )

    concerns = get_skin_concerns(
        profile
    )

    label = get_score_label(
        scores["overall"]
    )

    return {
        "status": "success",

        "user_id": current_user.id,

        "score": scores["overall"],

        "health_score": scores["overall"],

        "overall_score": scores["overall"],

        "label": label,

        "health_label": label,

        "skin_type": get_primary_skin_type(
            profile
        ),

        "concerns": concerns,

        "components": {
            "skin_condition": scores["condition"],
            "lifestyle": scores["lifestyle"],
            "sleep_quality": scores["sleep"],
            "routine_consistency": scores["routine"],
            "hydration": scores["hydration"],
        },

        "weights": {
            "skin_condition": 35,
            "lifestyle": 20,
            "sleep_quality": 15,
            "routine_consistency": 20,
            "hydration": 10,
        },

        "personalization": {
            "profile_used": profile is not None,
            "analysis_used": analysis is not None,
        },

        "note": (
            "This score is a wellness and personalization "
            "indicator. It is not a medical diagnosis."
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

    if not profile:

        return {
            "status": "success",
            "user_id": current_user.id,
            "skin_type": "Not specified",
            "identified_concerns": [],
            "morning_routine": [],
            "evening_routine": [],
            "weekly_plan": [],
            "personalized_recommendations": [
                "Complete your skin profile to receive personalized routine suggestions."
            ],
            "note": (
                "Routine suggestions are informational "
                "and do not replace professional medical advice."
            ),
        }

    skin_type = get_primary_skin_type(
        profile
    )

    concerns = get_skin_concerns(
        profile
    )

    morning = [
        {
            "id": "morning-cleanse",
            "step": 1,
            "category": "Cleansing",
            "title": "Gentle Cleanser",
            "description": (
                "Cleanse the face gently without excessive scrubbing."
            ),
        },
        {
            "id": "morning-moisturize",
            "step": 2,
            "category": "Moisturizing",
            "title": "Moisturizer",
            "description": (
                "Apply a moisturizer suited to your skin type."
            ),
        },
        {
            "id": "morning-sunscreen",
            "step": 3,
            "category": "Sun Protection",
            "title": "Broad-Spectrum Sunscreen",
            "description": (
                "Use sunscreen as the final daytime skincare step."
            ),
        },
    ]

    evening = [
        {
            "id": "evening-cleanse",
            "step": 1,
            "category": "Cleansing",
            "title": "Gentle Evening Cleanse",
            "description": (
                "Remove sunscreen, makeup and daily buildup gently."
            ),
        },
        {
            "id": "evening-treatment",
            "step": 2,
            "category": "Treatment",
            "title": "Targeted Treatment",
            "description": (
                "Use a suitable treatment according to your concerns."
            ),
        },
        {
            "id": "evening-moisturize",
            "step": 3,
            "category": "Night Care",
            "title": "Night Moisturizer",
            "description": (
                "Support the skin barrier with an appropriate moisturizer."
            ),
        },
    ]

    weekly = [
        {
            "day": "Monday",
            "focus": "Barrier Support",
        },
        {
            "day": "Wednesday",
            "focus": "Targeted Treatment",
        },
        {
            "day": "Friday",
            "focus": "Gentle Skin Care",
        },
        {
            "day": "Sunday",
            "focus": "Skin Recovery",
        },
    ]

    recommendations = []

    # Oily skin
    if (
        "oily" in skin_type.lower()
        or "Oily Skin" in concerns
    ):
        recommendations.append(
            "Prefer lightweight, non-greasy skincare products."
        )

    # Dry skin
    if (
        "dry" in skin_type.lower()
        or "Dry Skin" in concerns
    ):
        recommendations.append(
            "Prioritize gentle cleansing and barrier-supporting moisturization."
        )

    # Sensitive skin
    if "Sensitive Skin" in concerns:
        recommendations.append(
            "Introduce new products gradually and consider fragrance-free options."
        )

    # Acne
    if "Acne" in concerns:
        recommendations.append(
            "Consider an acne-focused routine with gentle cleansing and suitable active ingredients."
        )

    # Dark spots
    if "Dark Spots" in concerns:
        recommendations.append(
            "Daily sun protection is especially important in a pigmentation-focused routine."
        )

    # Hyperpigmentation
    if "Hyperpigmentation" in concerns:
        recommendations.append(
            "Consider brightening ingredients such as vitamin C or niacinamide."
        )

    # Wrinkles
    if "Wrinkles" in concerns or "Fine Lines" in concerns:
        recommendations.append(
            "Prioritize sunscreen and a consistent night-care routine."
        )

    # Hydration
    water = safe_number(
        getattr(
            profile,
            "water_intake",
            None
        ),
        0
    )

    if water > 0 and water < 1.5:
        recommendations.append(
            "Your recorded water intake is relatively low; maintain regular hydration."
        )

    if not recommendations:
        recommendations.append(
            "Maintain a simple, consistent routine and introduce new products gradually."
        )

    return {
        "status": "success",

        "user_id": current_user.id,

        "skin_type": skin_type,

        "identified_concerns": concerns,

        "morning_routine": morning,

        "evening_routine": evening,

        "weekly_plan": weekly,

        "personalized_recommendations": recommendations,

        "note": (
            "Routine suggestions are informational "
            "and should not replace professional medical advice."
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
            "Helps improve uneven-looking skin",
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
            "Patch testing is recommended when introducing a new active ingredient."
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
        ],

        "caution": (
            "Use with a suitable moisturizer to support the skin barrier."
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
            "Retinoids can cause irritation and require careful introduction."
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
            "Avoid excessive exfoliation, especially with sensitive skin."
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

    ingredient = clean_text(
        request.ingredient
    ).lower()

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
                "Check the complete product ingredient list "
                "and consult a qualified professional if you "
                "have allergies or sensitivities."
            ),
        }

    profile = get_user_skin_profile(
        current_user,
        db
    )

    concerns = get_skin_concerns(
        profile
    )

    allergies = clean_text(
        getattr(
            profile,
            "allergies",
            ""
        )
    ).lower() if profile else ""

    sensitivities = clean_text(
        getattr(
            profile,
            "sensitivities",
            ""
        ).lower()
    ) if profile else ""

    suitable = any(
        item in concerns
        for item in result["suitable_for"]
    )

    allergy_warning = False

    if allergies and ingredient in allergies:
        allergy_warning = True

    if sensitivities and ingredient in sensitivities:
        allergy_warning = True

    return {
        "status": "success",

        "found": True,

        "ingredient": result["name"],

        "category": result["category"],

        "benefits": result["benefits"],

        "suitable_for": result["suitable_for"],

        "personalized_match": suitable,

        "allergy_or_sensitivity_warning": allergy_warning,

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

    normalized_skin_type = (
        skin_type.lower()
    )

    recommendations = []

    for product in PRODUCT_DATABASE:

        if category:
            if (
                product["category"].lower()
                != category.lower()
            ):
                continue

        if budget:
            if (
                product["budget"].lower()
                != budget.lower()
            ):
                continue

        score = product["score"]

        product_skin_types = [
            item.lower()
            for item in product["skin_types"]
        ]

        if (
            "all" in product_skin_types
            or normalized_skin_type
            in product_skin_types
        ):
            score += 5

        ingredient_text = " ".join(
            product["ingredients"]
        ).lower()

        concern_text = " ".join(
            concerns
        ).lower()

        if (
            "acne" in concern_text
            and "salicylic" in ingredient_text
        ):
            score += 5

        if (
            (
                "hyperpigmentation"
                in concern_text
                or "dark spots"
                in concern_text
            )
            and "vitamin c"
            in ingredient_text
        ):
            score += 5

        if (
            "dry skin" in concern_text
            and (
                "hyaluronic"
                in ingredient_text
                or "ceramides"
                in ingredient_text
            )
        ):
            score += 5

        if (
            "sensitive skin"
            in concern_text
            and "ceramides"
            in ingredient_text
        ):
            score += 5

        recommendations.append(
            {
                **product,

                "personalized_score": min(
                    score,
                    100
                ),

                "match_reason": (
                    "Recommended based on your "
                    "skin profile and identified concerns."
                ),
            }
        )

    recommendations.sort(
        key=lambda item:
        item["personalized_score"],
        reverse=True,
    )

    return {
        "status": "success",

        "user_id": current_user.id,

        "skin_type": skin_type,

        "concerns": concerns,

        "recommendations":
            recommendations[:10],

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
                "primary_confidence",
                None
            ),
            0.0,
        )

        if confidence <= 1:
            confidence *= 100

        health_score = safe_number(
            getattr(
                analysis,
                "skin_health_score",
                None
            ),
            None,
        )

        history.append(
            {
                "analysis_id":
                    analysis.id,

                "date":
                    (
                        analysis.created_at.isoformat()
                        if getattr(
                            analysis,
                            "created_at",
                            None
                        )
                        else None
                    ),

                "score":
                    (
                        round(
                            health_score,
                            2
                        )
                        if health_score is not None
                        else round(
                            confidence,
                            2
                        )
                    ),

                "health_score":
                    (
                        round(
                            health_score,
                            2
                        )
                        if health_score is not None
                        else round(
                            confidence,
                            2
                        )
                    ),

                "confidence":
                    round(
                        confidence,
                        2
                    ),

                "image_path":
                    getattr(
                        analysis,
                        "image_path",
                        None
                    ),
            }
        )

    current_score = (
        history[-1]["score"]
        if history
        else None
    )

    previous_score = (
        history[-2]["score"]
        if len(history) >= 2
        else None
    )

    improvement = None

    if (
        current_score is not None
        and previous_score is not None
    ):
        improvement = round(
            current_score
            - previous_score,
            2,
        )

    return {
        "status": "success",

        "user_id":
            current_user.id,

        "total_assessments":
            len(history),

        "current_score":
            current_score,

        "improvement":
            improvement,

        "latest_assessment_score":
            current_score,

        "history":
            history,

        "tracking_features": {
            "skin_progress_monitoring":
                True,

            "assessment_history":
                True,

            "trend_analysis":
                len(history) >= 2,

            "before_after_comparison":
                len(history) >= 2,

            "routine_adherence_tracking":
                False,
        },

        "message": (
            "Assessment history is available. "
            "Routine adherence will be connected "
            "to persistent checklist storage in a later step."
        ),
    }


# ============================================================
# 6. DASHBOARD
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

    scores = calculate_health_score(
        profile,
        analysis,
    )

    concerns = get_skin_concerns(
        profile
    )

    overall_score = scores["overall"]

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
            "id":
                current_user.id,

            "name":
                getattr(
                    current_user,
                    "name",
                    "User"
                ),

            "email":
                getattr(
                    current_user,
                    "email",
                    None
                ),
        },

        "skin": {
            "skin_type":
                get_primary_skin_type(
                    profile
                ),

            "concerns":
                concerns,

            "health_score":
                overall_score,

            "health_label":
                get_score_label(
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

        "assessment_count":
            assessment_count,

        "latest_analysis_id":
            (
                analysis.id
                if analysis
                else None
            ),

        "message": (
            "Personalized Skin Intelligence dashboard "
            "data generated successfully."
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
            "title":
                "Daily Sun Protection",

            "priority":
                "High",

            "description":
                "Use broad-spectrum sunscreen during daytime.",
        },

        {
            "title":
                "Gentle Cleansing",

            "priority":
                "High",

            "description":
                "Avoid unnecessarily harsh cleansing that can disturb the skin barrier.",
        },

        {
            "title":
                "Stay Hydrated",

            "priority":
                "Medium",

            "description":
                "Maintain regular water intake as part of a healthy lifestyle.",
        },

        {
            "title":
                "Introduce Products Gradually",

            "priority":
                "Medium",

            "description":
                "Add new active ingredients one at a time and monitor skin response.",
        },
    ]

    if "Acne" in concerns:

        recommendations.append(
            {
                "title":
                    "Acne-Focused Care",

                "priority":
                    "High",

                "description":
                    "Consider gentle, non-comedogenic skincare and avoid excessive product layering.",
            }
        )

    if "Dry Skin" in concerns:

        recommendations.append(
            {
                "title":
                    "Barrier Support",

                "priority":
                    "High",

                "description":
                    "Prefer moisturizers containing barrier-supporting ingredients.",
            }
        )

    if "Sensitive Skin" in concerns:

        recommendations.append(
            {
                "title":
                    "Sensitivity Protection",

                "priority":
                    "High",

                "description":
                    "Prefer gentle and fragrance-free products when appropriate.",
            }
        )

    if "Dark Spots" in concerns:

        recommendations.append(
            {
                "title":
                    "Dark Spot Support",

                "priority":
                    "Medium",

                "description":
                    "Prioritize consistent sun protection and suitable brightening ingredients.",
            }
        )

    if "Hyperpigmentation" in concerns:

        recommendations.append(
            {
                "title":
                    "Even Skin Tone Support",

                "priority":
                    "Medium",

                "description":
                    "Consider suitable brightening ingredients such as vitamin C or niacinamide.",
            }
        )

    return {
        "status":
            "success",

        "user_id":
            current_user.id,

        "identified_concerns":
            concerns,

        "recommendations":
            recommendations,

        "note":
            "Recommendations are educational and not a medical diagnosis.",
    }