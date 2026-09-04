"""
Skin Intelligence - Additional Intelligence Services

This module provides the backend foundation for:
1. Extended skin profile
2. Lifestyle tracking
3. Sleep tracking
4. Hydration tracking
5. Environmental exposure
6. Skin health scoring
7. Personalized routines
8. Ingredient intelligence
9. Product recommendations
10. Progress tracking
11. Notifications
12. Daily checklist

The existing AI skin-analysis functionality remains untouched.
"""

from datetime import date
from typing import Optional, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session


# ============================================================
# SMALL HELPERS
# ============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def split_values(value: Any) -> List[str]:
    """
    Convert comma-separated profile values into a clean list.
    """
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    return [
        item.strip()
        for item in str(value).replace(";", ",").split(",")
        if item.strip()
    ]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_intelligence_tables(engine):
    """
    Create additional intelligence tables.

    The project currently uses SQLite, so the SQL below is
    intentionally SQLite-compatible.
    """

    statements = [

        # ----------------------------------------------------
        # EXTENDED SKIN PROFILE
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_intelligence_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,

            age_group TEXT,
            skin_type TEXT,

            skin_concerns TEXT,
            allergies TEXT,
            sensitivities TEXT,

            lifestyle_habits TEXT,

            sleep_quality TEXT,
            sleep_hours REAL,

            water_intake REAL,

            sun_exposure TEXT,
            pollution_exposure TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # DAILY LIFESTYLE TRACKING
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS lifestyle_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,

            tracking_date DATE NOT NULL,

            water_intake REAL DEFAULT 0,
            sleep_hours REAL DEFAULT 0,

            sleep_quality INTEGER DEFAULT 0,

            exercise_minutes INTEGER DEFAULT 0,
            stress_level INTEGER DEFAULT 0,

            sun_exposure INTEGER DEFAULT 0,
            pollution_exposure INTEGER DEFAULT 0,

            routine_completed INTEGER DEFAULT 0,

            notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, tracking_date)
        )
        """,

        # ----------------------------------------------------
        # SKIN HEALTH SCORE
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_health_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            analysis_id INTEGER,

            skin_condition_score REAL DEFAULT 0,
            lifestyle_score REAL DEFAULT 0,
            sleep_score REAL DEFAULT 0,
            routine_score REAL DEFAULT 0,
            hydration_score REAL DEFAULT 0,

            overall_score REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # ROUTINES
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skincare_routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            routine_name TEXT,

            morning_routine TEXT,
            evening_routine TEXT,
            weekly_treatment TEXT,
            seasonal_recommendation TEXT,

            reason TEXT,

            active INTEGER DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # INGREDIENT INTELLIGENCE
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS ingredient_intelligence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ingredient_name TEXT UNIQUE NOT NULL,

            category TEXT,

            description TEXT,
            benefits TEXT,
            suitable_for TEXT,

            cautions TEXT,
            interactions TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # PRODUCT RECOMMENDATIONS
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS product_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            product_name TEXT,
            category TEXT,
            brand TEXT,

            price REAL,

            suitability_score REAL,

            ingredients TEXT,
            benefits TEXT,
            reason TEXT,

            budget_category TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # PROGRESS TRACKING
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            progress_date DATE NOT NULL,

            skin_score REAL,
            routine_adherence REAL,

            notes TEXT,

            image_path TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            notification_type TEXT,
            title TEXT,
            message TEXT,

            is_read INTEGER DEFAULT 0,

            scheduled_for TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # DAILY CHECKLIST
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skincare_checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            checklist_date DATE NOT NULL,

            morning_completed INTEGER DEFAULT 0,
            evening_completed INTEGER DEFAULT 0,
            sunscreen_completed INTEGER DEFAULT 0,
            hydration_completed INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, checklist_date)
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


# ============================================================
# EXTENDED PROFILE
# ============================================================

def save_extended_profile(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):
    """
    Save or update the extended intelligence profile.

    This function accepts both the frontend naming convention
    and the database naming convention.
    """

    existing = db.execute(
        text(
            """
            SELECT id
            FROM skin_intelligence_profiles
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchone()

    params = {
        "user_id": user_id,
        "age_group": data.get("age_group"),
        "skin_type": data.get("skin_type"),
        "skin_concerns": (
            data.get("skin_concerns")
            or data.get("concerns")
            or ""
        ),
        "allergies": data.get("allergies") or "",
        "sensitivities": (
            data.get("sensitivities")
            or data.get("sensitivity")
            or ""
        ),
        "lifestyle_habits": (
            data.get("lifestyle_habits")
            or data.get("lifestyle")
            or ""
        ),
        "sleep_quality": data.get("sleep_quality"),
        "sleep_hours": data.get("sleep_hours"),
        "water_intake": data.get("water_intake"),
        "sun_exposure": (
            data.get("sun_exposure")
            or data.get("environmental_exposure")
            or ""
        ),
        "pollution_exposure": data.get("pollution_exposure") or "",
    }

    if existing:

        db.execute(
            text(
                """
                UPDATE skin_intelligence_profiles
                SET
                    age_group = :age_group,
                    skin_type = :skin_type,
                    skin_concerns = :skin_concerns,
                    allergies = :allergies,
                    sensitivities = :sensitivities,
                    lifestyle_habits = :lifestyle_habits,
                    sleep_quality = :sleep_quality,
                    sleep_hours = :sleep_hours,
                    water_intake = :water_intake,
                    sun_exposure = :sun_exposure,
                    pollution_exposure = :pollution_exposure,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id
                """
            ),
            params,
        )

    else:

        db.execute(
            text(
                """
                INSERT INTO skin_intelligence_profiles (
                    user_id,
                    age_group,
                    skin_type,
                    skin_concerns,
                    allergies,
                    sensitivities,
                    lifestyle_habits,
                    sleep_quality,
                    sleep_hours,
                    water_intake,
                    sun_exposure,
                    pollution_exposure
                )
                VALUES (
                    :user_id,
                    :age_group,
                    :skin_type,
                    :skin_concerns,
                    :allergies,
                    :sensitivities,
                    :lifestyle_habits,
                    :sleep_quality,
                    :sleep_hours,
                    :water_intake,
                    :sun_exposure,
                    :pollution_exposure
                )
                """
            ),
            params,
        )

    db.commit()

    return get_extended_profile(db, user_id)


def get_extended_profile(
    db: Session,
    user_id: int,
):
    result = db.execute(
        text(
            """
            SELECT
                id,
                user_id,
                age_group,
                skin_type,
                skin_concerns,
                allergies,
                sensitivities,
                lifestyle_habits,
                sleep_quality,
                sleep_hours,
                water_intake,
                sun_exposure,
                pollution_exposure,
                created_at,
                updated_at
            FROM skin_intelligence_profiles
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not result:
        return None

    profile = dict(result)

    # Also expose frontend-friendly names.
    profile["concerns"] = profile.get("skin_concerns") or ""
    profile["lifestyle"] = profile.get("lifestyle_habits") or ""
    profile["environmental_exposure"] = (
        profile.get("sun_exposure")
        or profile.get("pollution_exposure")
        or ""
    )

    return profile


# ============================================================
# PROFILE → CONCERN INTELLIGENCE
# ============================================================

def get_profile_concerns(
    profile: Optional[Dict[str, Any]]
) -> List[str]:
    """
    Extract the concerns saved in the user's profile.

    Supports values such as:
    acne, dark spots, pigmentation, redness,
    dryness, sensitivity, wrinkles, dark circles.
    """

    if not profile:
        return []

    raw = (
        profile.get("skin_concerns")
        or profile.get("concerns")
        or ""
    )

    concerns = split_values(raw)

    normalized = []

    for concern in concerns:
        value = concern.lower().strip()

        if value and value not in normalized:
            normalized.append(value)

    return normalized


def get_primary_concern(
    profile: Optional[Dict[str, Any]]
) -> Optional[str]:

    concerns = get_profile_concerns(profile)

    if not concerns:
        return None

    return concerns[0].title()


# ============================================================
# LIFESTYLE TRACKING
# ============================================================

def save_lifestyle_tracking(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    tracking_date = data.get("tracking_date") or date.today()

    existing = db.execute(
        text(
            """
            SELECT id
            FROM lifestyle_tracking
            WHERE user_id = :user_id
              AND tracking_date = :tracking_date
            """
        ),
        {
            "user_id": user_id,
            "tracking_date": tracking_date,
        },
    ).fetchone()

    params = {
        "user_id": user_id,
        "tracking_date": tracking_date,
        "water_intake": safe_float(
            data.get("water_intake"),
            0,
        ),
        "sleep_hours": safe_float(
            data.get("sleep_hours"),
            0,
        ),
        "sleep_quality": int(
            safe_float(
                data.get("sleep_quality"),
                0,
            )
        ),
        "exercise_minutes": int(
            safe_float(
                data.get("exercise_minutes"),
                0,
            )
        ),
        "stress_level": int(
            safe_float(
                data.get("stress_level"),
                0,
            )
        ),
        "sun_exposure": int(
            safe_float(
                data.get("sun_exposure"),
                0,
            )
        ),
        "pollution_exposure": int(
            safe_float(
                data.get("pollution_exposure"),
                0,
            )
        ),
        "routine_completed": bool(
            data.get("routine_completed", False)
        ),
        "notes": data.get("notes"),
    }

    if existing:

        db.execute(
            text(
                """
                UPDATE lifestyle_tracking
                SET
                    water_intake = :water_intake,
                    sleep_hours = :sleep_hours,
                    sleep_quality = :sleep_quality,
                    exercise_minutes = :exercise_minutes,
                    stress_level = :stress_level,
                    sun_exposure = :sun_exposure,
                    pollution_exposure = :pollution_exposure,
                    routine_completed = :routine_completed,
                    notes = :notes
                WHERE user_id = :user_id
                  AND tracking_date = :tracking_date
                """
            ),
            params,
        )

    else:

        db.execute(
            text(
                """
                INSERT INTO lifestyle_tracking (
                    user_id,
                    tracking_date,
                    water_intake,
                    sleep_hours,
                    sleep_quality,
                    exercise_minutes,
                    stress_level,
                    sun_exposure,
                    pollution_exposure,
                    routine_completed,
                    notes
                )
                VALUES (
                    :user_id,
                    :tracking_date,
                    :water_intake,
                    :sleep_hours,
                    :sleep_quality,
                    :exercise_minutes,
                    :stress_level,
                    :sun_exposure,
                    :pollution_exposure,
                    :routine_completed,
                    :notes
                )
                """
            ),
            params,
        )

    db.commit()

    return get_lifestyle_tracking(db, user_id)


def get_lifestyle_tracking(
    db: Session,
    user_id: int,
    limit: int = 30,
):

    result = db.execute(
        text(
            """
            SELECT *
            FROM lifestyle_tracking
            WHERE user_id = :user_id
            ORDER BY tracking_date DESC
            LIMIT :limit
            """
        ),
        {
            "user_id": user_id,
            "limit": limit,
        },
    ).mappings().all()

    return [dict(row) for row in result]


# ============================================================
# SKIN HEALTH SCORE
# ============================================================

def calculate_skin_health_score(
    skin_condition_score: float,
    lifestyle_score: float,
    sleep_score: float,
    routine_score: float,
    hydration_score: float,
):

    skin_condition_score = clamp(
        safe_float(skin_condition_score)
    )

    lifestyle_score = clamp(
        safe_float(lifestyle_score)
    )

    sleep_score = clamp(
        safe_float(sleep_score)
    )

    routine_score = clamp(
        safe_float(routine_score)
    )

    hydration_score = clamp(
        safe_float(hydration_score)
    )

    overall = (
        skin_condition_score * 0.35
        + lifestyle_score * 0.20
        + sleep_score * 0.15
        + routine_score * 0.20
        + hydration_score * 0.10
    )

    return round(overall, 2)


def save_skin_health_score(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    overall_score = calculate_skin_health_score(
        data.get("skin_condition_score", 0),
        data.get("lifestyle_score", 0),
        data.get("sleep_score", 0),
        data.get("routine_score", 0),
        data.get("hydration_score", 0),
    )

    db.execute(
        text(
            """
            INSERT INTO skin_health_scores (
                user_id,
                analysis_id,
                skin_condition_score,
                lifestyle_score,
                sleep_score,
                routine_score,
                hydration_score,
                overall_score
            )
            VALUES (
                :user_id,
                :analysis_id,
                :skin_condition_score,
                :lifestyle_score,
                :sleep_score,
                :routine_score,
                :hydration_score,
                :overall_score
            )
            """
        ),
        {
            "user_id": user_id,
            "analysis_id": data.get("analysis_id"),
            "skin_condition_score": safe_float(
                data.get("skin_condition_score")
            ),
            "lifestyle_score": safe_float(
                data.get("lifestyle_score")
            ),
            "sleep_score": safe_float(
                data.get("sleep_score")
            ),
            "routine_score": safe_float(
                data.get("routine_score")
            ),
            "hydration_score": safe_float(
                data.get("hydration_score")
            ),
            "overall_score": overall_score,
        },
    )

    db.commit()

    return get_latest_health_score(db, user_id)


def get_latest_health_score(
    db: Session,
    user_id: int,
):

    result = db.execute(
        text(
            """
            SELECT *
            FROM skin_health_scores
            WHERE user_id = :user_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not result:
        return None

    return dict(result)


def get_score_label(score: float) -> str:

    score = safe_float(score)

    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Good"

    if score >= 55:
        return "Fair"

    return "Needs Attention"


# ============================================================
# PERSONALIZED ROUTINE GENERATION
# ============================================================

def generate_personalized_routine(
    profile: Optional[Dict[str, Any]],
    condition: Optional[str] = None,
):

    profile = profile or {}

    skin_type = (
        profile.get("skin_type")
        or "normal"
    )

    skin_type_lower = str(skin_type).lower()

    concerns = get_profile_concerns(profile)

    concern_text = " ".join(concerns).lower()

    routine_reason = []

    morning = [
        "Gentle cleanser",
    ]

    evening = [
        "Gentle cleanser",
    ]

    # --------------------------------------------------------
    # SKIN TYPE
    # --------------------------------------------------------

    if "dry" in skin_type_lower:

        morning.extend([
            "Hydrating serum",
            "Moisturizer",
        ])

        evening.extend([
            "Hydrating serum",
            "Rich moisturizer",
        ])

        routine_reason.append(
            "Hydration-focused routine for dry skin."
        )

    elif "oily" in skin_type_lower:

        morning.extend([
            "Lightweight treatment serum",
            "Oil-free moisturizer",
        ])

        evening.extend([
            "Lightweight treatment",
            "Oil-free moisturizer",
        ])

        routine_reason.append(
            "Lightweight routine suitable for oily skin."
        )

    elif "combination" in skin_type_lower:

        morning.extend([
            "Balancing serum",
            "Lightweight moisturizer",
        ])

        evening.extend([
            "Gentle treatment",
            "Lightweight moisturizer",
        ])

        routine_reason.append(
            "Balanced routine for combination skin."
        )

    elif "sensitive" in skin_type_lower:

        morning.extend([
            "Gentle soothing serum",
            "Fragrance-free moisturizer",
        ])

        evening.extend([
            "Soothing treatment",
            "Fragrance-free moisturizer",
        ])

        routine_reason.append(
            "Gentle routine designed for sensitive skin."
        )

    else:

        morning.extend([
            "Hydrating serum",
            "Moisturizer",
        ])

        evening.extend([
            "Treatment serum",
            "Moisturizer",
        ])

        routine_reason.append(
            "Balanced maintenance routine."
        )

    # --------------------------------------------------------
    # CONCERNS
    # --------------------------------------------------------

    if (
        "acne" in concern_text
        or "pimple" in concern_text
        or "breakout" in concern_text
    ):

        evening.insert(
            1,
            "Salicylic-acid treatment",
        )

        routine_reason.append(
            "Acne or breakout concern detected."
        )

    if (
        "pigmentation" in concern_text
        or "dark spot" in concern_text
        or "dark spots" in concern_text
        or "uneven tone" in concern_text
    ):

        morning.insert(
            1,
            "Vitamin C treatment",
        )

        routine_reason.append(
            "Pigmentation or uneven-tone concern detected."
        )

    if (
        "redness" in concern_text
        or "sensitivity" in concern_text
        or "sensitive" in concern_text
    ):

        routine_reason.append(
            "Soothing and barrier-support steps are prioritized."
        )

    if (
        "dryness" in concern_text
        or "dehydrated" in concern_text
    ):

        if "Hydrating serum" not in morning:
            morning.insert(
                1,
                "Hydrating serum",
            )

        routine_reason.append(
            "Dryness or dehydration concern detected."
        )

    if (
        "wrinkles" in concern_text
        or "aging" in concern_text
        or "fine lines" in concern_text
    ):

        evening.insert(
            1,
            "Age-support treatment",
        )

        routine_reason.append(
            "Signs-of-aging concern detected."
        )

    if "dark circle" in concern_text:

        routine_reason.append(
            "Eye-area care can be added for dark-circle concerns."
        )

    # --------------------------------------------------------
    # AI CONDITION
    # --------------------------------------------------------

    if condition:

        routine_reason.append(
            f"AI assessment result considered: {condition}."
        )

    # --------------------------------------------------------
    # SUN PROTECTION
    # --------------------------------------------------------

    morning.append(
        "Broad-spectrum sunscreen"
    )

    # --------------------------------------------------------
    # WEEKLY
    # --------------------------------------------------------

    weekly = [
        "Gentle exfoliation once weekly when appropriate",
        "Hydrating mask once weekly",
        "Review skin condition and routine consistency",
    ]

    # --------------------------------------------------------
    # SEASONAL
    # --------------------------------------------------------

    seasonal = (
        "Adjust moisturizer and hydration according "
        "to seasonal dryness or humidity. Maintain "
        "daily sun protection."
    )

    return {
        "morning": morning,
        "evening": evening,
        "weekly": weekly,
        "seasonal": seasonal,
        "reason": routine_reason,
        "skin_type": skin_type,
        "identified_concerns": concerns,
    }


# ============================================================
# INGREDIENT DATABASE
# ============================================================

DEFAULT_INGREDIENTS = [

    {
        "name": "Niacinamide",
        "category": "Vitamin",
        "description": (
            "A versatile skincare ingredient commonly used "
            "for barrier support and oil-control routines."
        ),
        "benefits": (
            "Supports skin barrier, helps manage excess oil "
            "and uneven appearance."
        ),
        "suitable_for": (
            "Oily, combination, uneven-looking skin"
        ),
        "cautions": (
            "Patch test new products and stop if irritation occurs."
        ),
        "interactions": (
            "Check the complete product formulation when "
            "combining multiple active ingredients."
        ),
    },

    {
        "name": "Vitamin C",
        "category": "Antioxidant",
        "description": (
            "An antioxidant ingredient used in many "
            "brightening skincare routines."
        ),
        "benefits": (
            "Supports antioxidant protection and brighter-looking skin."
        ),
        "suitable_for": (
            "Uneven tone and pigmentation-focused routines"
        ),
        "cautions": (
            "May irritate sensitive skin in some formulations."
        ),
        "interactions": (
            "Introduce active ingredients gradually."
        ),
    },

    {
        "name": "Hyaluronic Acid",
        "category": "Humectant",
        "description": (
            "A hydrating ingredient that helps attract and retain water."
        ),
        "benefits": (
            "Supports hydration and skin comfort."
        ),
        "suitable_for": (
            "Dry, dehydrated and normal skin"
        ),
        "cautions": (
            "Use according to product instructions."
        ),
        "interactions": (
            "Generally used alongside many other skincare ingredients."
        ),
    },

    {
        "name": "Salicylic Acid",
        "category": "BHA",
        "description": (
            "A beta-hydroxy acid commonly used in "
            "acne and pore-focused skincare."
        ),
        "benefits": (
            "Helps exfoliate and supports acne-focused routines."
        ),
        "suitable_for": (
            "Oily and acne-prone skin"
        ),
        "cautions": (
            "Can cause dryness or irritation if overused."
        ),
        "interactions": (
            "Avoid unnecessarily combining several strong "
            "exfoliating products."
        ),
    },

    {
        "name": "Ceramides",
        "category": "Barrier Support",
        "description": (
            "Lipids commonly used to support the skin barrier."
        ),
        "benefits": (
            "Supports barrier function and moisture retention."
        ),
        "suitable_for": (
            "Dry and sensitive skin"
        ),
        "cautions": (
            "Use according to product instructions."
        ),
        "interactions": (
            "Generally compatible with many routine categories."
        ),
    },

    {
        "name": "Peptides",
        "category": "Skin Support",
        "description": (
            "Short chains of amino acids used in various "
            "skincare formulations."
        ),
        "benefits": (
            "Used in routines focused on skin appearance and support."
        ),
        "suitable_for": (
            "Mature-skin and maintenance routines"
        ),
        "cautions": (
            "Check the complete product formulation."
        ),
        "interactions": (
            "Follow product-specific instructions."
        ),
    },

    {
        "name": "Retinoids",
        "category": "Vitamin A",
        "description": (
            "Vitamin-A-derived ingredients used in various "
            "dermatological and cosmetic routines."
        ),
        "benefits": (
            "Commonly used for acne and signs of skin aging."
        ),
        "suitable_for": (
            "Specific treatment-focused routines"
        ),
        "cautions": (
            "Can cause irritation and requires careful use. "
            "Professional advice may be appropriate."
        ),
        "interactions": (
            "Avoid combining multiple irritating actives "
            "without appropriate guidance."
        ),
    },

    {
        "name": "AHAs/BHAs",
        "category": "Exfoliant",
        "description": (
            "Chemical exfoliating ingredients used "
            "to improve skin texture."
        ),
        "benefits": (
            "Supports exfoliation and smoother-looking skin."
        ),
        "suitable_for": (
            "Texture-focused routines"
        ),
        "cautions": (
            "Overuse can cause irritation."
        ),
        "interactions": (
            "Avoid excessive stacking of exfoliating actives."
        ),
    },
]


def seed_ingredients(db: Session):

    for ingredient in DEFAULT_INGREDIENTS:

        existing = db.execute(
            text(
                """
                SELECT id
                FROM ingredient_intelligence
                WHERE LOWER(ingredient_name)
                    = LOWER(:ingredient_name)
                """
            ),
            {
                "ingredient_name": ingredient["name"],
            },
        ).fetchone()

        if existing:
            continue

        db.execute(
            text(
                """
                INSERT INTO ingredient_intelligence (
                    ingredient_name,
                    category,
                    description,
                    benefits,
                    suitable_for,
                    cautions,
                    interactions
                )
                VALUES (
                    :ingredient_name,
                    :category,
                    :description,
                    :benefits,
                    :suitable_for,
                    :cautions,
                    :interactions
                )
                """
            ),
            {
                "ingredient_name": ingredient["name"],
                "category": ingredient["category"],
                "description": ingredient["description"],
                "benefits": ingredient["benefits"],
                "suitable_for": ingredient["suitable_for"],
                "cautions": ingredient["cautions"],
                "interactions": ingredient["interactions"],
            },
        )

    db.commit()


def search_ingredients(
    db: Session,
    query: str = "",
):

    if query:

        results = db.execute(
            text(
                """
                SELECT *
                FROM ingredient_intelligence
                WHERE LOWER(ingredient_name)
                    LIKE LOWER(:query)
                   OR LOWER(category)
                    LIKE LOWER(:query)
                   OR LOWER(description)
                    LIKE LOWER(:query)
                ORDER BY ingredient_name
                """
            ),
            {
                "query": f"%{query}%",
            },
        ).mappings().all()

    else:

        results = db.execute(
            text(
                """
                SELECT *
                FROM ingredient_intelligence
                ORDER BY ingredient_name
                """
            )
        ).mappings().all()

    return [dict(row) for row in results]


def analyze_ingredient_for_profile(
    ingredient: Dict[str, Any],
    profile: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    profile = profile or {}

    concerns = get_profile_concerns(profile)

    skin_type = str(
        profile.get("skin_type") or ""
    ).lower()

    suitable_for = str(
        ingredient.get("suitable_for") or ""
    ).lower()

    matched_reasons = []

    if "oily" in skin_type and "oily" in suitable_for:
        matched_reasons.append("Suitable for oily skin")

    if "dry" in skin_type and "dry" in suitable_for:
        matched_reasons.append("Suitable for dry skin")

    if "sensitive" in skin_type and "sensitive" in suitable_for:
        matched_reasons.append("Suitable for sensitive skin")

    concern_mapping = {
        "acne": ["acne", "oily", "pore"],
        "pigmentation": ["pigmentation", "uneven", "tone"],
        "dark spots": ["pigmentation", "uneven", "tone"],
        "dryness": ["dry", "hydration"],
        "redness": ["sensitive", "barrier"],
        "sensitivity": ["sensitive", "barrier"],
        "wrinkles": ["mature", "aging"],
        "fine lines": ["mature", "aging"],
    }

    for concern in concerns:

        keywords = concern_mapping.get(
            concern,
            [concern],
        )

        if any(
            keyword in suitable_for
            for keyword in keywords
        ):
            matched_reasons.append(
                f"Relevant to {concern}"
            )

    match_score = min(
        100,
        50 + (len(matched_reasons) * 15),
    )

    return {
        "personalized_match": match_score >= 65,
        "match_score": match_score,
        "reasons": matched_reasons,
    }


# ============================================================
# PRODUCT RECOMMENDATIONS
# ============================================================

DEFAULT_PRODUCTS = [

    {
        "product_name": "Gentle Hydrating Cleanser",
        "brand": "Skin Intelligence",
        "category": "Face Wash",
        "price": 499,
        "suitability_score": 90,
        "ingredients": "Ceramides, Hyaluronic Acid",
        "benefits": "Gentle cleansing and hydration support",
        "budget_category": "Budget",
    },

    {
        "product_name": "Niacinamide Serum",
        "brand": "Skin Intelligence",
        "category": "Serum",
        "price": 599,
        "suitability_score": 88,
        "ingredients": "Niacinamide",
        "benefits": "Supports oil control and skin barrier",
        "budget_category": "Budget",
    },

    {
        "product_name": "Vitamin C Serum",
        "brand": "Skin Intelligence",
        "category": "Serum",
        "price": 699,
        "suitability_score": 86,
        "ingredients": "Vitamin C",
        "benefits": "Antioxidant and brightening-focused routine",
        "budget_category": "Mid-range",
    },

    {
        "product_name": "Ceramide Moisturizer",
        "brand": "Skin Intelligence",
        "category": "Moisturizer",
        "price": 649,
        "suitability_score": 92,
        "ingredients": "Ceramides",
        "benefits": "Barrier and hydration support",
        "budget_category": "Mid-range",
    },

    {
        "product_name": "Broad Spectrum Sunscreen",
        "brand": "Skin Intelligence",
        "category": "Sunscreen",
        "price": 549,
        "suitability_score": 95,
        "ingredients": "UV filters",
        "benefits": "Daily sun protection",
        "budget_category": "Budget",
    },
]


def seed_products(db: Session):

    count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM product_recommendations
            WHERE user_id = 0
            """
        )
    ).scalar()

    if count and count > 0:
        return

    for product in DEFAULT_PRODUCTS:

        db.execute(
            text(
                """
                INSERT INTO product_recommendations (
                    user_id,
                    product_name,
                    category,
                    brand,
                    price,
                    suitability_score,
                    ingredients,
                    benefits,
                    reason,
                    budget_category
                )
                VALUES (
                    0,
                    :product_name,
                    :category,
                    :brand,
                    :price,
                    :suitability_score,
                    :ingredients,
                    :benefits,
                    :reason,
                    :budget_category
                )
                """
            ),
            {
                **product,
                "reason": "Starter recommendation catalogue",
            },
        )

    db.commit()


def get_products(
    db: Session,
    category: Optional[str] = None,
):

    if category:

        results = db.execute(
            text(
                """
                SELECT *
                FROM product_recommendations
                WHERE LOWER(category) = LOWER(:category)
                ORDER BY suitability_score DESC
                """
            ),
            {
                "category": category,
            },
        ).mappings().all()

    else:

        results = db.execute(
            text(
                """
                SELECT *
                FROM product_recommendations
                ORDER BY suitability_score DESC
                """
            )
        ).mappings().all()

    return [dict(row) for row in results]


def personalize_products(
    products: List[Dict[str, Any]],
    profile: Optional[Dict[str, Any]],
):

    profile = profile or {}

    skin_type = str(
        profile.get("skin_type") or ""
    ).lower()

    concerns = get_profile_concerns(profile)

    results = []

    for product in products:

        score = safe_float(
            product.get("suitability_score"),
            50,
        )

        reasons = []

        ingredients = str(
            product.get("ingredients") or ""
        ).lower()

        benefits = str(
            product.get("benefits") or ""
        ).lower()

        if "dry" in skin_type:

            if (
                "hyaluronic" in ingredients
                or "ceramide" in ingredients
                or "hydration" in benefits
            ):
                score += 5
                reasons.append(
                    "Supports dry-skin hydration."
                )

        if "oily" in skin_type:

            if (
                "niacinamide" in ingredients
                or "oil" in benefits
            ):
                score += 5
                reasons.append(
                    "Suitable for an oil-control routine."
                )

        if "sensitive" in skin_type:

            if "ceramide" in ingredients:
                score += 5
                reasons.append(
                    "Supports a sensitive-skin barrier."
                )

        concern_text = " ".join(concerns)

        if "acne" in concern_text:
            if (
                "niacinamide" in ingredients
                or "salicylic" in ingredients
            ):
                score += 7
                reasons.append(
                    "Relevant to acne-focused care."
                )

        if (
            "pigmentation" in concern_text
            or "dark spots" in concern_text
        ):
            if "vitamin c" in ingredients:
                score += 7
                reasons.append(
                    "Relevant to pigmentation-focused care."
                )

        product_copy = dict(product)

        product_copy["personalized_score"] = round(
            clamp(score),
            2,
        )

        product_copy["personalized_reason"] = (
            reasons
            or [
                "General skincare recommendation "
                "based on the available profile."
            ]
        )

        results.append(product_copy)

    results.sort(
        key=lambda item: item["personalized_score"],
        reverse=True,
    )

    return results


# ============================================================
# PROGRESS
# ============================================================

def save_progress(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    progress_date = (
        data.get("progress_date")
        or date.today()
    )

    db.execute(
        text(
            """
            INSERT INTO skin_progress (
                user_id,
                progress_date,
                skin_score,
                routine_adherence,
                notes,
                image_path
            )
            VALUES (
                :user_id,
                :progress_date,
                :skin_score,
                :routine_adherence,
                :notes,
                :image_path
            )
            """
        ),
        {
            "user_id": user_id,
            "progress_date": progress_date,
            "skin_score": safe_float(
                data.get("skin_score"),
                0,
            ),
            "routine_adherence": safe_float(
                data.get("routine_adherence"),
                0,
            ),
            "notes": data.get("notes"),
            "image_path": data.get("image_path"),
        },
    )

    db.commit()

    return get_progress(db, user_id)


def get_progress(
    db: Session,
    user_id: int,
):

    results = db.execute(
        text(
            """
            SELECT *
            FROM skin_progress
            WHERE user_id = :user_id
            ORDER BY progress_date ASC, id ASC
            """
        ),
        {
            "user_id": user_id,
        },
    ).mappings().all()

    return [dict(row) for row in results]


# ============================================================
# CHECKLIST
# ============================================================

def get_or_create_checklist(
    db: Session,
    user_id: int,
):

    today = date.today()

    row = db.execute(
        text(
            """
            SELECT *
            FROM skincare_checklist
            WHERE user_id = :user_id
              AND checklist_date = :today
            """
        ),
        {
            "user_id": user_id,
            "today": today,
        },
    ).mappings().first()

    if row:
        return dict(row)

    db.execute(
        text(
            """
            INSERT INTO skincare_checklist (
                user_id,
                checklist_date
            )
            VALUES (
                :user_id,
                :today
            )
            """
        ),
        {
            "user_id": user_id,
            "today": today,
        },
    )

    db.commit()

    row = db.execute(
        text(
            """
            SELECT *
            FROM skincare_checklist
            WHERE user_id = :user_id
              AND checklist_date = :today
            """
        ),
        {
            "user_id": user_id,
            "today": today,
        },
    ).mappings().first()

    return dict(row)


def update_checklist(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    today = date.today()

    get_or_create_checklist(
        db,
        user_id,
    )

    db.execute(
        text(
            """
            UPDATE skincare_checklist
            SET
                morning_completed = :morning_completed,
                evening_completed = :evening_completed,
                sunscreen_completed = :sunscreen_completed,
                hydration_completed = :hydration_completed
            WHERE user_id = :user_id
              AND checklist_date = :today
            """
        ),
        {
            "user_id": user_id,
            "today": today,
            "morning_completed": bool(
                data.get(
                    "morning_completed",
                    False,
                )
            ),
            "evening_completed": bool(
                data.get(
                    "evening_completed",
                    False,
                )
            ),
            "sunscreen_completed": bool(
                data.get(
                    "sunscreen_completed",
                    False,
                )
            ),
            "hydration_completed": bool(
                data.get(
                    "hydration_completed",
                    False,
                )
            ),
        },
    )

    db.commit()

    return get_or_create_checklist(
        db,
        user_id,
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
):

    db.execute(
        text(
            """
            INSERT INTO skin_notifications (
                user_id,
                notification_type,
                title,
                message
            )
            VALUES (
                :user_id,
                :notification_type,
                :title,
                :message
            )
            """
        ),
        {
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
        },
    )

    db.commit()

    result = db.execute(
        text(
            """
            SELECT *
            FROM skin_notifications
            WHERE user_id = :user_id
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {
            "user_id": user_id,
        },
    ).mappings().first()

    return dict(result) if result else None


def get_notifications(
    db: Session,
    user_id: int,
):

    results = db.execute(
        text(
            """
            SELECT *
            FROM skin_notifications
            WHERE user_id = :user_id
            ORDER BY created_at DESC, id DESC
            LIMIT 50
            """
        ),
        {
            "user_id": user_id,
        },
    ).mappings().all()

    return [dict(row) for row in results]


# ============================================================
# INTELLIGENCE SUMMARY
# ============================================================

def build_intelligence_summary(
    profile: Optional[Dict[str, Any]],
    health_score: Optional[Dict[str, Any]] = None,
):

    profile = profile or {}

    concerns = get_profile_concerns(profile)

    score = None

    if health_score:
        score = safe_float(
            health_score.get("overall_score"),
            0,
        )

    return {
        "skin_type": profile.get("skin_type"),
        "age_group": profile.get("age_group"),
        "concerns": concerns,
        "primary_concern": (
            concerns[0].title()
            if concerns
            else None
        ),
        "health_score": score,
        "health_label": (
            get_score_label(score)
            if score is not None
            else None
        ),
        "profile_completed": bool(
            profile.get("skin_type")
            or concerns
        ),
    }