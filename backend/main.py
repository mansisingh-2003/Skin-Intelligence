# ============================================================
# SKIN INTELLIGENCE
# MAIN FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import (
    Base,
    engine,
)

# Import models so SQLAlchemy knows about all tables
from models import (
    User,
    SkinProfile,
    SkinAnalysis,
)

from auth import (
    router as auth_router,
)

from services.intelligence_routes import (
    router as intelligence_router,
)

from services.profile_routes import (
    router as profile_router,
)

from services.analysis_routes import (
    router as analysis_router,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Skin Intelligence API",

    description=(
        "AI-powered skin analysis and "
        "personalized skincare intelligence platform."
    ),

    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "status": "online",

        "service": "Skin Intelligence Backend",

        "version": "1.0.0",

        "message": (
            "Skin Intelligence API is running."
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    return {

        "status": "healthy",

        "service": (
            "Skin Intelligence Backend"
        ),
    }


# ============================================================
# AUTHENTICATION
# ============================================================

app.include_router(
    auth_router
)


# ============================================================
# SKIN PROFILE
# ============================================================

app.include_router(
    profile_router
)


# ============================================================
# AI SKIN ANALYSIS
# ============================================================

app.include_router(
    analysis_router
)


# ============================================================
# SKIN INTELLIGENCE
# ============================================================

app.include_router(
    intelligence_router
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print("=" * 60)

    print(
        "SKIN INTELLIGENCE BACKEND"
    )

    print("=" * 60)

    print(
        "API:      http://127.0.0.1:8000"
    )

    print(
        "Docs:     http://127.0.0.1:8000/docs"
    )

    print(
        "Health:   http://127.0.0.1:8000/health"
    )

    print(
        "Frontend: http://localhost:5173"
    )

    print("=" * 60)

    print(
        "Application startup complete."
    )