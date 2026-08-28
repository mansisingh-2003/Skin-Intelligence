import os

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt, JWTError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from database import get_db
from models import User


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# JWT CONFIGURATION
# =========================================================

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "skin-intelligence-secret-key-change-later"
)

ALGORITHM = "HS256"

# Development-friendly session duration.
# The token will remain valid for 24 hours.
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# =========================================================
# HTTP BEARER SECURITY
# =========================================================

security = HTTPBearer(
    auto_error=True
)


# =========================================================
# CREATE ACCESS TOKEN
# =========================================================

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.

    The supplied data is copied and an expiration
    timestamp is added automatically.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# =========================================================
# GET CURRENT USER
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Validate the JWT token and return the logged-in user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    # -----------------------------------------------------
    # Get token from Authorization header
    # -----------------------------------------------------

    token = credentials.credentials

    # -----------------------------------------------------
    # Decode token
    # -----------------------------------------------------

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # User ID stored in "sub"
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        # Convert ID to integer
        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):

        raise credentials_exception

    # -----------------------------------------------------
    # Find user in database
    # -----------------------------------------------------

    current_user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if current_user is None:
        raise credentials_exception

    return current_user