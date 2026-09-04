# ============================================================
# SKIN INTELLIGENCE
# USER DATABASE MODEL
# ============================================================

from sqlalchemy import Boolean, Column, Integer, String
from database import Base


class User(Base):
    """
    Database model for application users.

    Supported roles:
    - user
    - consultant
    - dermatologist
    - admin
    """

    __tablename__ = "users"

    # --------------------------------------------------------
    # Primary Key
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # Basic User Information
    # --------------------------------------------------------

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    password_hash = Column(
        String(255),
        nullable=False
    )

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    role = Column(
        String(30),
        nullable=False,
        default="user"
    )

    # --------------------------------------------------------
    # Account Status
    # --------------------------------------------------------

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    # --------------------------------------------------------
    # Optional Profile Information
    # --------------------------------------------------------

    age = Column(
        Integer,
        nullable=True
    )

    gender = Column(
        String(30),
        nullable=True
    )

    # --------------------------------------------------------
    # Representation
    # --------------------------------------------------------

    def __repr__(self):
        return (
            f"<User("
            f"id={self.id}, "
            f"email='{self.email}', "
            f"role='{self.role}'"
            f")>"
        )