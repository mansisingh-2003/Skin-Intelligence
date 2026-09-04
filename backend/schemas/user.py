# ============================================================
# SKIN INTELLIGENCE
# USER PYDANTIC SCHEMAS
# ============================================================

from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


# ============================================================
# ROLE VALUES
# ============================================================

ALLOWED_ROLES = {
    "user",
    "consultant",
    "dermatologist",
    "admin",
}


# ============================================================
# REGISTER USER
# ============================================================

class UserCreate(BaseModel):
    """
    Data required when creating a new user account.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="User account password",
    )

    age: Optional[int] = Field(
        default=None,
        ge=1,
        le=120,
    )

    gender: Optional[str] = Field(
        default=None,
        max_length=30,
    )


# ============================================================
# LOGIN
# ============================================================

class UserLogin(BaseModel):
    """
    Data required for user login.
    """

    email: EmailStr

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):
    """
    Safe user information returned by the backend.

    Passwords and password hashes are never returned.
    """

    id: int

    name: str

    email: EmailStr

    role: str

    is_active: bool

    age: Optional[int] = None

    gender: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):
    """
    Authentication response returned after successful login.
    """

    access_token: str

    token_type: str = "bearer"

    user: UserResponse


# ============================================================
# USER UPDATE
# ============================================================

class UserUpdate(BaseModel):
    """
    Optional fields that can be updated in a user's account.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    email: Optional[EmailStr] = None

    age: Optional[int] = Field(
        default=None,
        ge=1,
        le=120,
    )

    gender: Optional[str] = Field(
        default=None,
        max_length=30,
    )


# ============================================================
# ROLE UPDATE
# ============================================================

class RoleUpdate(BaseModel):
    """
    Used by authorized administrators to change a user's role.
    """

    role: str = Field(
        ...,
        description=(
            "Allowed roles: user, consultant, "
            "dermatologist, admin"
        ),
    )

    def validate_role(self) -> str:
        """
        Validate the requested role.
        """

        normalized_role = self.role.strip().lower()

        if normalized_role not in ALLOWED_ROLES:
            raise ValueError(
                "Invalid role. Allowed roles are: "
                "user, consultant, dermatologist, admin."
            )

        return normalized_role