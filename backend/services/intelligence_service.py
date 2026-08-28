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
12. Reports

The existing AI skin-analysis functionality remains untouched.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_intelligence_tables(engine):
    """
    Create all additional intelligence tables if they do not
    already exist.

    This allows us to extend the existing PostgreSQL database
    without replacing the user's current tables.
    """

    statements = [

        # ----------------------------------------------------
        # EXTENDED SKIN PROFILE
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_intelligence_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,

            age_group VARCHAR(50),
            skin_type VARCHAR(100),

            skin_concerns TEXT,
            allergies TEXT,
            sensitivities TEXT,

            lifestyle_habits TEXT,

            sleep_quality VARCHAR(50),
            sleep_hours NUMERIC(4,1),

            water_intake NUMERIC(5,2),

            sun_exposure VARCHAR(50),
            pollution_exposure VARCHAR(50),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # DAILY LIFESTYLE TRACKING
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS lifestyle_tracking (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,

            tracking_date DATE NOT NULL,

            water_intake NUMERIC(5,2) DEFAULT 0,
            sleep_hours NUMERIC(4,1) DEFAULT 0,

            sleep_quality INTEGER DEFAULT 0,

            exercise_minutes INTEGER DEFAULT 0,
            stress_level INTEGER DEFAULT 0,

            sun_exposure INTEGER DEFAULT 0,
            pollution_exposure INTEGER DEFAULT 0,

            routine_completed BOOLEAN DEFAULT FALSE,

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
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            analysis_id INTEGER,

            skin_condition_score NUMERIC(5,2) DEFAULT 0,
            lifestyle_score NUMERIC(5,2) DEFAULT 0,
            sleep_score NUMERIC(5,2) DEFAULT 0,
            routine_score NUMERIC(5,2) DEFAULT 0,
            hydration_score NUMERIC(5,2) DEFAULT 0,

            overall_score NUMERIC(5,2) DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # ROUTINES
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skincare_routines (
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            routine_name VARCHAR(200),

            morning_routine TEXT,
            evening_routine TEXT,
            weekly_treatment TEXT,
            seasonal_recommendation TEXT,

            reason TEXT,

            active BOOLEAN DEFAULT TRUE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # INGREDIENT INTELLIGENCE
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS ingredient_intelligence (
            id SERIAL PRIMARY KEY,

            ingredient_name VARCHAR(150) UNIQUE NOT NULL,

            category VARCHAR(100),

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
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            product_name VARCHAR(200),
            category VARCHAR(100),
            brand VARCHAR(150),

            price NUMERIC(10,2),

            suitability_score NUMERIC(5,2),

            ingredients TEXT,
            benefits TEXT,
            reason TEXT,

            budget_category VARCHAR(50),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # PROGRESS TRACKING
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skin_progress (
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            progress_date DATE NOT NULL,

            skin_score NUMERIC(5,2),
            routine_adherence NUMERIC(5,2),

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
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            notification_type VARCHAR(100),
            title VARCHAR(200),
            message TEXT,

            is_read BOOLEAN DEFAULT FALSE,

            scheduled_for TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # DAILY CHECKLIST
        # ----------------------------------------------------

        """
        CREATE TABLE IF NOT EXISTS skincare_checklist (
            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            checklist_date DATE NOT NULL,

            morning_completed BOOLEAN DEFAULT FALSE,
            evening_completed BOOLEAN DEFAULT FALSE,
            sunscreen_completed BOOLEAN DEFAULT FALSE,
            hydration_completed BOOLEAN DEFAULT FALSE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, checklist_date)
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


# ============================================================
# PROFILE
# ============================================================

def save_extended_profile(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

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
        "skin_concerns": data.get("skin_concerns"),
        "allergies": data.get("allergies"),
        "sensitivities": data.get("sensitivities"),
        "lifestyle_habits": data.get("lifestyle_habits"),
        "sleep_quality": data.get("sleep_quality"),
        "sleep_hours": data.get("sleep_hours"),
        "water_intake": data.get("water_intake"),
        "sun_exposure": data.get("sun_exposure"),
        "pollution_exposure": data.get("pollution_exposure"),
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

    return dict(result)


# ============================================================
# LIFESTYLE TRACKING
# ============================================================

def save_lifestyle_tracking(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    tracking_date = data.get("tracking_date") or date.today()

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

            ON CONFLICT (user_id, tracking_date)

            DO UPDATE SET

                water_intake = EXCLUDED.water_intake,
                sleep_hours = EXCLUDED.sleep_hours,
                sleep_quality = EXCLUDED.sleep_quality,
                exercise_minutes = EXCLUDED.exercise_minutes,
                stress_level = EXCLUDED.stress_level,
                sun_exposure = EXCLUDED.sun_exposure,
                pollution_exposure = EXCLUDED.pollution_exposure,
                routine_completed = EXCLUDED.routine_completed,
                notes = EXCLUDED.notes
            """
        ),
        {
            "user_id": user_id,
            "tracking_date": tracking_date,
            "water_intake": data.get("water_intake", 0),
            "sleep_hours": data.get("sleep_hours", 0),
            "sleep_quality": data.get("sleep_quality", 0),
            "exercise_minutes": data.get("exercise_minutes", 0),
            "stress_level": data.get("stress_level", 0),
            "sun_exposure": data.get("sun_exposure", 0),
            "pollution_exposure": data.get("pollution_exposure", 0),
            "routine_completed": data.get(
                "routine_completed",
                False,
            ),
            "notes": data.get("notes"),
        },
    )

    db.commit()

    return get_lifestyle_tracking(
        db,
        user_id,
    )


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

    skin_condition_score = max(
        0,
        min(100, float(skin_condition_score)),
    )

    lifestyle_score = max(
        0,
        min(100, float(lifestyle_score)),
    )

    sleep_score = max(
        0,
        min(100, float(sleep_score)),
    )

    routine_score = max(
        0,
        min(100, float(routine_score)),
    )

    hydration_score = max(
        0,
        min(100, float(hydration_score)),
    )

    overall = (

        skin_condition_score * 0.35

        + lifestyle_score * 0.20

        + sleep_score * 0.15

        + routine_score * 0.20

        + hydration_score * 0.10
    )

    return round(
        overall,
        2,
    )


def save_skin_health_score(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    overall_score = calculate_skin_health_score(

        data.get(
            "skin_condition_score",
            0,
        ),

        data.get(
            "lifestyle_score",
            0,
        ),

        data.get(
            "sleep_score",
            0,
        ),

        data.get(
            "routine_score",
            0,
        ),

        data.get(
            "hydration_score",
            0,
        ),
    )

    result = db.execute(
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

            RETURNING *
            """
        ),
        {
            "user_id": user_id,

            "analysis_id": data.get(
                "analysis_id"
            ),

            "skin_condition_score": data.get(
                "skin_condition_score",
                0,
            ),

            "lifestyle_score": data.get(
                "lifestyle_score",
                0,
            ),

            "sleep_score": data.get(
                "sleep_score",
                0,
            ),

            "routine_score": data.get(
                "routine_score",
                0,
            ),

            "hydration_score": data.get(
                "hydration_score",
                0,
            ),

            "overall_score": overall_score,
        },
    ).mappings().first()

    db.commit()

    return dict(result)


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

            ORDER BY created_at DESC

            LIMIT 1
            """
        ),
        {
            "user_id": user_id,
        },
    ).mappings().first()

    if not result:
        return None

    return dict(result)


# ============================================================
# ROUTINE GENERATION
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

    concerns = (
        profile.get("skin_concerns")
        or ""
    ).lower()

    routine_reason = []

    morning = [
        "Gentle cleanser",
    ]

    evening = [
        "Gentle cleanser",
    ]

    # --------------------------------------------------------
    # Skin-type based recommendations
    # --------------------------------------------------------

    if "dry" in skin_type.lower():

        morning.append(
            "Hydrating serum"
        )

        morning.append(
            "Moisturizer"
        )

        evening.append(
            "Hydrating serum"
        )

        evening.append(
            "Rich moisturizer"
        )

        routine_reason.append(
            "Hydration-focused routine for dry skin."
        )

    elif "oily" in skin_type.lower():

        morning.append(
            "Lightweight treatment serum"
        )

        morning.append(
            "Oil-free moisturizer"
        )

        evening.append(
            "Lightweight treatment"
        )

        evening.append(
            "Oil-free moisturizer"
        )

        routine_reason.append(
            "Lightweight routine suitable for oily skin."
        )

    elif "sensitive" in skin_type.lower():

        morning.append(
            "Gentle soothing serum"
        )

        morning.append(
            "Fragrance-free moisturizer"
        )

        evening.append(
            "Soothing treatment"
        )

        evening.append(
            "Fragrance-free moisturizer"
        )

        routine_reason.append(
            "Gentle routine designed for sensitive skin."
        )

    else:

        morning.append(
            "Hydrating serum"
        )

        morning.append(
            "Moisturizer"
        )

        evening.append(
            "Treatment serum"
        )

        evening.append(
            "Moisturizer"
        )

    # --------------------------------------------------------
    # Concern-based recommendations
    # --------------------------------------------------------

    if "acne" in concerns:

        evening.insert(
            1,
            "Salicylic-acid treatment"
        )

        routine_reason.append(
            "Acne concern detected."
        )

    if (
        "pigmentation" in concerns
        or "dark spot" in concerns
    ):

        morning.insert(
            1,
            "Vitamin C treatment"
        )

        routine_reason.append(
            "Pigmentation concern detected."
        )

    if condition:

        routine_reason.append(
            f"AI assessment result considered: {condition}."
        )

    # --------------------------------------------------------
    # Sunscreen
    # --------------------------------------------------------

    morning.append(
        "Broad-spectrum sunscreen"
    )

    # --------------------------------------------------------
    # Weekly treatment
    # --------------------------------------------------------

    weekly = [
        "Gentle exfoliation once weekly",
        "Hydrating mask once weekly",
        "Review skin condition and routine adherence",
    ]

    # --------------------------------------------------------
    # Seasonal
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
    }


# ============================================================
# INGREDIENT DATABASE
# ============================================================

DEFAULT_INGREDIENTS = [

    {
        "name": "Niacinamide",
        "category": "Vitamin",
        "description": "A versatile skincare ingredient commonly used for barrier support and oil-control routines.",
        "benefits": "Supports skin barrier, helps manage excess oil and uneven appearance.",
        "suitable_for": "Oily, combination, uneven-looking skin",
        "cautions": "Patch test new products and stop if irritation occurs.",
        "interactions": "Check the complete product formulation when combining multiple active ingredients.",
    },

    {
        "name": "Vitamin C",
        "category": "Antioxidant",
        "description": "An antioxidant ingredient used in many brightening skincare routines.",
        "benefits": "Supports antioxidant protection and brighter-looking skin.",
        "suitable_for": "Uneven tone and pigmentation-focused routines",
        "cautions": "May irritate sensitive skin in some formulations.",
        "interactions": "Introduce active ingredients gradually.",
    },

    {
        "name": "Hyaluronic Acid",
        "category": "Humectant",
        "description": "A hydrating ingredient that helps attract and retain water.",
        "benefits": "Supports hydration and skin comfort.",
        "suitable_for": "Dry, dehydrated and normal skin",
        "cautions": "Use according to product instructions.",
        "interactions": "Generally used alongside many other skincare ingredients.",
    },

    {
        "name": "Salicylic Acid",
        "category": "BHA",
        "description": "A beta-hydroxy acid commonly used in acne and pore-focused skincare.",
        "benefits": "Helps exfoliate and supports acne-focused routines.",
        "suitable_for": "Oily and acne-prone skin",
        "cautions": "Can cause dryness or irritation if overused.",
        "interactions": "Avoid unnecessarily combining several strong exfoliating products.",
    },

    {
        "name": "Ceramides",
        "category": "Barrier Support",
        "description": "Lipids commonly used to support the skin barrier.",
        "benefits": "Supports barrier function and moisture retention.",
        "suitable_for": "Dry and sensitive skin",
        "cautions": "Use according to product instructions.",
        "interactions": "Generally compatible with many routine categories.",
    },

    {
        "name": "Peptides",
        "category": "Skin Support",
        "description": "Short chains of amino acids used in various skincare formulations.",
        "benefits": "Used in routines focused on skin appearance and support.",
        "suitable_for": "Mature-skin and maintenance routines",
        "cautions": "Check the complete product formulation.",
        "interactions": "Follow product-specific instructions.",
    },

    {
        "name": "Retinoids",
        "category": "Vitamin A",
        "description": "Vitamin-A-derived ingredients used in various dermatological and cosmetic routines.",
        "benefits": "Commonly used for acne and signs of skin aging.",
        "suitable_for": "Specific treatment-focused routines",
        "cautions": "Can cause irritation and requires careful use. Professional advice may be appropriate.",
        "interactions": "Avoid combining multiple irritating actives without appropriate guidance.",
    },

    {
        "name": "AHAs/BHAs",
        "category": "Exfoliant",
        "description": "Chemical exfoliating ingredients used to improve skin texture.",
        "benefits": "Supports exfoliation and smoother-looking skin.",
        "suitable_for": "Texture-focused routines",
        "cautions": "Overuse can cause irritation.",
        "interactions": "Avoid excessive stacking of exfoliating actives.",
    },
]


def seed_ingredients(db: Session):

    for ingredient in DEFAULT_INGREDIENTS:

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

                ON CONFLICT (ingredient_name)
                DO NOTHING
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

                WHERE
                    LOWER(ingredient_name)
                    LIKE LOWER(:query)

                    OR

                    LOWER(category)
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
                    'Starter recommendation catalogue',
                    :budget_category
                )
                """
            ),
            product,
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

                WHERE LOWER(category)
                = LOWER(:category)

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


# ============================================================
# PROGRESS
# ============================================================

def save_progress(
    db: Session,
    user_id: int,
    data: Dict[str, Any],
):

    result = db.execute(
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

            RETURNING *
            """
        ),
        {
            "user_id": user_id,
            "progress_date": data.get(
                "progress_date",
                date.today(),
            ),
            "skin_score": data.get(
                "skin_score",
                0,
            ),
            "routine_adherence": data.get(
                "routine_adherence",
                0,
            ),
            "notes": data.get(
                "notes"
            ),
            "image_path": data.get(
                "image_path"
            ),
        },
    ).mappings().first()

    db.commit()

    return dict(result)


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

            ORDER BY progress_date ASC
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

            WHERE
                user_id = :user_id
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

    row = db.execute(
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

            RETURNING *
            """
        ),
        {
            "user_id": user_id,
            "today": today,
        },
    ).mappings().first()

    db.commit()

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
                morning_completed =
                    :morning_completed,

                evening_completed =
                    :evening_completed,

                sunscreen_completed =
                    :sunscreen_completed,

                hydration_completed =
                    :hydration_completed

            WHERE
                user_id = :user_id

                AND

                checklist_date = :today
            """
        ),
        {
            "user_id": user_id,
            "today": today,

            "morning_completed": data.get(
                "morning_completed",
                False,
            ),

            "evening_completed": data.get(
                "evening_completed",
                False,
            ),

            "sunscreen_completed": data.get(
                "sunscreen_completed",
                False,
            ),

            "hydration_completed": data.get(
                "hydration_completed",
                False,
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

    result = db.execute(
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

            RETURNING *
            """
        ),
        {
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
        },
    ).mappings().first()

    db.commit()

    return dict(result)


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

            ORDER BY created_at DESC

            LIMIT 50
            """
        ),
        {
            "user_id": user_id,
        },
    ).mappings().all()

    return [dict(row) for row in results]