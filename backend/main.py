import os
import json
import uuid

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from services.intelligence_routes import router as intelligence_router
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import text

from database import (
    engine,
    Base,
    get_db,
)

from models import (
    User,
    SkinProfile,
    SkinAnalysis,
)

from schemas.user import (
    UserCreate,
    UserLogin,
    UserProfileUpdate,
)

from schemas.skin_profile import (
    SkinProfileCreate,
)

from security import (
    hash_password,
    verify_password,
)

from auth import (
    create_access_token,
    get_current_user,
)

from services.skin_analyzer import (
    analyze_skin_image,
)

from services.ai_skin_analyzer import (
    analyze_with_ai,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Skin Intelligence & Personalized Skincare Planner",
    description="AI-powered skincare intelligence platform",
    version="1.0.0",
)

app.include_router(intelligence_router)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "status": "success",
        "message": "AI Skin Intelligence API is running",
        "version": "1.0.0",
    }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/db-test")
def database_test(
    db: Session = Depends(get_db),
):

    try:

        result = db.execute(
            text("SELECT 1")
        ).scalar()

        return {
            "status": "success",
            "message": "Database connection successful",
            "result": result,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}",
        )


# ============================================================
# REGISTER USER
# ============================================================

@app.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Check existing email
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.email == user.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    hashed_password = hash_password(
        user.password
    )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        age=user.age,
        gender=user.gender,
    )

    db.add(
        new_user
    )

    db.commit()

    db.refresh(
        new_user
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.email == user.email
        )
        .first()
    )

    if not existing_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_is_correct = verify_password(
        user.password,
        existing_user.password_hash,
    )

    if not password_is_correct:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(
                existing_user.id
            )
        }
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": existing_user.id,
        "name": existing_user.name,
        "email": existing_user.email,
    }


# ============================================================
# GET MY PROFILE
# ============================================================

@app.get("/me")
def get_my_profile(
    current_user: User = Depends(
        get_current_user
    ),
):

    return {
        "status": "success",
        "message": "Authenticated user profile",
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "age": current_user.age,
        "gender": current_user.gender,
    }


# ============================================================
# UPDATE MY PROFILE
# ============================================================

@app.put("/me")
def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Update name
    # --------------------------------------------------------

    if profile_data.name is not None:

        current_user.name = (
            profile_data.name
        )

    # --------------------------------------------------------
    # Update age
    # --------------------------------------------------------

    if profile_data.age is not None:

        current_user.age = (
            profile_data.age
        )

    # --------------------------------------------------------
    # Update gender
    # --------------------------------------------------------

    if profile_data.gender is not None:

        current_user.gender = (
            profile_data.gender
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        current_user
    )

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "age": current_user.age,
        "gender": current_user.gender,
    }


# ============================================================
# CREATE / UPDATE SKIN PROFILE
# ============================================================

@app.post("/skin-profile")
def create_skin_profile(
    profile_data: SkinProfileCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Check existing profile
    # --------------------------------------------------------

    existing_profile = (
        db.query(SkinProfile)
        .filter(
            SkinProfile.user_id
            == current_user.id
        )
        .first()
    )

    # --------------------------------------------------------
    # Update existing profile
    # --------------------------------------------------------

    if existing_profile:

        existing_profile.skin_type = (
            profile_data.skin_type
        )

        existing_profile.acne = (
            profile_data.acne
        )

        existing_profile.pigmentation = (
            profile_data.pigmentation
        )

        existing_profile.dryness = (
            profile_data.dryness
        )

        existing_profile.sensitivity = (
            profile_data.sensitivity
        )

        existing_profile.dark_circles = (
            profile_data.dark_circles
        )

        existing_profile.wrinkles = (
            profile_data.wrinkles
        )

        existing_profile.redness = (
            profile_data.redness
        )

        db.commit()

        db.refresh(
            existing_profile
        )

        profile = existing_profile

        message = (
            "Skin profile updated successfully"
        )

    # --------------------------------------------------------
    # Create new profile
    # --------------------------------------------------------

    else:

        profile = SkinProfile(

            user_id=current_user.id,

            skin_type=profile_data.skin_type,

            acne=profile_data.acne,

            pigmentation=profile_data.pigmentation,

            dryness=profile_data.dryness,

            sensitivity=profile_data.sensitivity,

            dark_circles=profile_data.dark_circles,

            wrinkles=profile_data.wrinkles,

            redness=profile_data.redness,
        )

        db.add(
            profile
        )

        db.commit()

        db.refresh(
            profile
        )

        message = (
            "Skin profile created successfully"
        )

    return {

        "status": "success",

        "message": message,

        "skin_profile_id": profile.id,

        "user_id": profile.user_id,

        "skin_type": profile.skin_type,

        "acne": profile.acne,

        "pigmentation": profile.pigmentation,

        "dryness": profile.dryness,

        "sensitivity": profile.sensitivity,

        "dark_circles": profile.dark_circles,

        "wrinkles": profile.wrinkles,

        "redness": profile.redness,
    }


# ============================================================
# GET SKIN PROFILE
# ============================================================

@app.get("/skin-profile")
def get_skin_profile(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = (
        db.query(SkinProfile)
        .filter(
            SkinProfile.user_id
            == current_user.id
        )
        .first()
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Skin profile not found",
        )

    return {

        "status": "success",

        "message": (
            "Skin profile retrieved successfully"
        ),

        "skin_profile_id": profile.id,

        "user_id": profile.user_id,

        "skin_type": profile.skin_type,

        "acne": profile.acne,

        "pigmentation": profile.pigmentation,

        "dryness": profile.dryness,

        "sensitivity": profile.sensitivity,

        "dark_circles": profile.dark_circles,

        "wrinkles": profile.wrinkles,

        "redness": profile.redness,
    }


# ============================================================
# UPDATE SKIN PROFILE
# ============================================================

@app.put("/skin-profile")
def update_skin_profile(
    profile_data: SkinProfileCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    profile = (
        db.query(SkinProfile)
        .filter(
            SkinProfile.user_id
            == current_user.id
        )
        .first()
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Skin profile not found",
        )

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    profile.skin_type = (
        profile_data.skin_type
    )

    profile.acne = (
        profile_data.acne
    )

    profile.pigmentation = (
        profile_data.pigmentation
    )

    profile.dryness = (
        profile_data.dryness
    )

    profile.sensitivity = (
        profile_data.sensitivity
    )

    profile.dark_circles = (
        profile_data.dark_circles
    )

    profile.wrinkles = (
        profile_data.wrinkles
    )

    profile.redness = (
        profile_data.redness
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        profile
    )

    return {

        "status": "success",

        "message": (
            "Skin profile updated successfully"
        ),

        "skin_profile_id": profile.id,

        "user_id": profile.user_id,

        "skin_type": profile.skin_type,

        "acne": profile.acne,

        "pigmentation": profile.pigmentation,

        "dryness": profile.dryness,

        "sensitivity": profile.sensitivity,

        "dark_circles": profile.dark_circles,

        "wrinkles": profile.wrinkles,

        "redness": profile.redness,
    }


# ============================================================
# SKIN IMAGE UPLOAD + AI ANALYSIS
# ============================================================

@app.post("/skin-analysis/upload")
async def upload_skin_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = (
        db.query(User)
        .order_by(User.id.asc())
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=404,
            detail="No registered user found. Please register a user first.",
        )

    # --------------------------------------------------------
    # 1. Validate filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected",
        )

    # --------------------------------------------------------
    # 2. Allowed extensions
    # --------------------------------------------------------

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, JPEG and PNG "
                "images are allowed"
            ),
        )

    # --------------------------------------------------------
    # 3. Create upload directory
    # --------------------------------------------------------

    upload_directory = "uploads"

    os.makedirs(
        upload_directory,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 4. Generate unique filename
    # --------------------------------------------------------

    unique_filename = (
        f"user_{current_user.id}_"
        f"{uuid.uuid4().hex}"
        f"{file_extension}"
    )

    file_path = os.path.join(
        upload_directory,
        unique_filename,
    )

    # --------------------------------------------------------
    # 5. Save image
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "wb",
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

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save image: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # 6. Validate image
    # --------------------------------------------------------

    try:

        validation_result = (
            analyze_skin_image(
                os.path.abspath(
                    file_path
                )
            )
        )

    except Exception as e:

        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Image validation failed: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # 7. Check image validation result
    # --------------------------------------------------------

    if validation_result.get(
        "status"
    ) == "error":

        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=400,
            detail=validation_result.get(
                "message",
                "Invalid image",
            ),
        )

    # --------------------------------------------------------
    # 8. Run REAL AI skin analysis
    # --------------------------------------------------------

    try:

        ai_result = analyze_with_ai(
            os.path.abspath(
                file_path
            )
        )

    except Exception as e:

        # Remove image if AI analysis fails
        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=500,
            detail=(
                f"AI skin analysis failed: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # 9. Get top prediction
    # --------------------------------------------------------

    top_prediction = (
        ai_result.get(
            "top_prediction"
        )
    )

    # --------------------------------------------------------
    # 10. Get confidence
    # --------------------------------------------------------

    confidence = None

    if top_prediction:

        confidence = float(
            top_prediction.get(
                "confidence",
                0.0
            )
        )

    # --------------------------------------------------------
    # 11. Convert AI result to JSON
    # --------------------------------------------------------

    analysis_json = json.dumps(
        ai_result
    )

    # --------------------------------------------------------
    # 12. Create database record
    #
    # IMPORTANT:
    # We are NOT mapping dermatology model classes
    # incorrectly to acne/pigmentation/etc.
    #
    # Those Boolean fields remain False until we
    # have a model specifically trained for them.
    # --------------------------------------------------------

    analysis_record = SkinAnalysis(

        user_id=current_user.id,

        image_path=file_path,

        acne=False,

        pigmentation=False,

        dryness=False,

        sensitivity=False,

        redness=False,

        dark_circles=False,

        wrinkles=False,

        confidence=confidence,

        analysis_result=analysis_json,
    )

    # --------------------------------------------------------
    # 13. Save to PostgreSQL
    # --------------------------------------------------------

    db.add(
        analysis_record
    )

    db.commit()

    db.refresh(
        analysis_record
    )

    # --------------------------------------------------------
    # 14. Return result
    # --------------------------------------------------------

    return {

        "status": "success",

        "message": (
            "Skin image uploaded and "
            "AI analysis completed"
        ),

        "analysis_id": (
            analysis_record.id
        ),

        "user_id": (
            current_user.id
        ),

        "image_path": (
            file_path
        ),

        "ai_analysis": ai_result,

        "database_record": {

            "confidence": (
                analysis_record.confidence
            ),

            "analysis_result": (
                analysis_record.analysis_result
            ),
        },

        "note": (
            "AI predictions are for "
            "assisted analysis and are "
            "not a medical diagnosis."
        ),
    }