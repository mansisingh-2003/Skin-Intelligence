# ============================================================
# SKIN INTELLIGENCE
# SKIN PROFILE DATABASE MODEL
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
)

from database import Base


class SkinProfile(Base):
    """
    Stores the personalized skin and lifestyle information
    associated with a user.
    """

    __tablename__ = "skin_profiles"

    # --------------------------------------------------------
    # Primary Key
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # User Relationship
    # --------------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Basic Skin Information
    # --------------------------------------------------------

    skin_type = Column(
        String(50),
        nullable=True
    )

    age_group = Column(
        String(50),
        nullable=True
    )

    # --------------------------------------------------------
    # Skin Concerns
    #
    # Example:
    # acne, dark spots, dryness
    # --------------------------------------------------------

    skin_concerns = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Allergies & Sensitivities
    # --------------------------------------------------------

    allergies = Column(
        Text,
        nullable=True
    )

    sensitivities = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Lifestyle
    # --------------------------------------------------------

    lifestyle_habits = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Sleep
    # --------------------------------------------------------

    sleep_quality = Column(
        String(50),
        nullable=True
    )

    # --------------------------------------------------------
    # Hydration
    # --------------------------------------------------------

    water_intake = Column(
        Float,
        nullable=True
    )

    # --------------------------------------------------------
    # Environmental Exposure
    # --------------------------------------------------------

    environmental_exposure = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Additional Information
    # --------------------------------------------------------

    additional_notes = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Representation
    # --------------------------------------------------------

    def __repr__(self):
        return (
            f"<SkinProfile("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"skin_type='{self.skin_type}'"
            f")>"
        )