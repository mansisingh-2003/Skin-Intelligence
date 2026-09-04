# ============================================================
# SKIN INTELLIGENCE
# AUTHENTICATION + JWT + ROLE-BASED ACCESS
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User

from schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
)

from security import (
    hash_password,
    verify_password,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "skin-intelligence-development-secret-change-this",
)

ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:

    to_encode = data.copy()

    if expires_delta is not None:

        expire = (
            datetime.now(timezone.utc)
            + expires_delta
        )

    else:

        expire = (
            datetime.now(timezone.utc)
            + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


# ============================================================
# DECODE ACCESS TOKEN
# ============================================================

def decode_access_token(
    token: str,
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    credentials: Optional[
        HTTPAuthorizationCredentials
    ] = Depends(security),

    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Check Authorization header
    # --------------------------------------------------------

    if credentials is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Get token
    # --------------------------------------------------------

    token = credentials.credentials

    # --------------------------------------------------------
    # Decode token
    # --------------------------------------------------------

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Get user ID
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Convert ID to integer
    # --------------------------------------------------------

    try:

        user_id = int(user_id)

    except (
        ValueError,
        TypeError,
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    current_user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if current_user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if not current_user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


# ============================================================
# CURRENT ACTIVE USER
# ============================================================

def get_current_active_user(
    current_user: User = Depends(
        get_current_user
    ),
):

    if not current_user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Normalize email
    # --------------------------------------------------------

    email = str(
        user.email
    ).strip().lower()

    # --------------------------------------------------------
    # Check existing user
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
        name=user.name.strip(),
        email=email,
        password_hash=hashed_password,
        role="user",
        is_active=True,
        age=user.age,
        gender=user.gender,
    )

    # --------------------------------------------------------
    # Save user
    # --------------------------------------------------------

    db.add(
        new_user
    )

    db.commit()

    db.refresh(
        new_user
    )

    return new_user


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Normalize email
    # --------------------------------------------------------

    email = str(
        user.email
    ).strip().lower()

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    # --------------------------------------------------------
    # Invalid email
    # --------------------------------------------------------

    if existing_user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if not existing_user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(
                existing_user.id
            ),
            "role": str(
                existing_user.role
            ).lower(),
        }
    )

    # --------------------------------------------------------
    # Return token + user
    # --------------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": existing_user,
    }


# ============================================================
# GET MY PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(
        get_current_active_user
    ),
):

    return current_user


# ============================================================
# UPDATE MY PROFILE
# ============================================================

@router.put(
    "/me",
    response_model=UserResponse,
)
def update_my_profile(
    profile_data: UserUpdate,

    current_user: User = Depends(
        get_current_active_user
    ),

    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Update name
    # --------------------------------------------------------

    if profile_data.name is not None:

        current_user.name = (
            profile_data.name.strip()
        )

    # --------------------------------------------------------
    # Update email
    # --------------------------------------------------------

    if profile_data.email is not None:

        new_email = str(
            profile_data.email
        ).strip().lower()

        existing_user = (
            db.query(User)
            .filter(
                User.email == new_email,
                User.id != current_user.id,
            )
            .first()
        )

        if existing_user:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        current_user.email = new_email

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
    # Save changes
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        current_user
    )

    return current_user


# ============================================================
# ROLE HELPERS
# ============================================================

def _get_role_value(
    user: User
):

    role = getattr(
        user,
        "role",
        None
    )

    if role is None:
        return None

    if hasattr(
        role,
        "value"
    ):

        return str(
            role.value
        ).lower()

    return str(
        role
    ).lower()


# ============================================================
# REQUIRE ROLE
# ============================================================

def require_role(
    *allowed_roles: str
) -> Callable:

    normalized_roles = {
        str(role).lower()
        for role in allowed_roles
    }

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):

        current_role = _get_role_value(
            current_user
        )

        if current_role not in normalized_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access denied. "
                    "Required role: "
                    + ", ".join(
                        normalized_roles
                    )
                ),
            )

        return current_user

    return role_checker


# ============================================================
# ROLE-SPECIFIC DEPENDENCIES
# ============================================================

def require_user(
    current_user: User = Depends(
        get_current_user
    )
):

    if _get_role_value(
        current_user
    ) != "user":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role required",
        )

    return current_user


# ------------------------------------------------------------

def require_consultant(
    current_user: User = Depends(
        get_current_user
    )
):

    if _get_role_value(
        current_user
    ) != "consultant":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Skincare Consultant role required",
        )

    return current_user


# ------------------------------------------------------------

def require_dermatologist(
    current_user: User = Depends(
        get_current_user
    )
):

    if _get_role_value(
        current_user
    ) != "dermatologist":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dermatologist role required",
        )

    return current_user


# ------------------------------------------------------------

def require_admin(
    current_user: User = Depends(
        get_current_user
    )
):

    if _get_role_value(
        current_user
    ) != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )

    return current_user