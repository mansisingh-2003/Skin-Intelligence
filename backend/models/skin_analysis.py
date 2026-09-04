# ============================================================
# SKIN INTELLIGENCE
# SKIN ANALYSIS DATABASE MODEL
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
)

from datetime import datetime

from database import Base


class SkinAnalysis(Base):
    """
    Stores the results of a skin analysis performed for a user.

    Each analysis represents one assessment and can be used
    later for:
    - Skin health scoring
    - Progress tracking
    - Concern analysis
    - Personalized recommendations
    - Reports
    """

    __tablename__ = "skin_analyses"

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
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Analysis Information
    # --------------------------------------------------------

    image_path = Column(
        String(500),
        nullable=True
    )

    analysis_type = Column(
        String(50),
        nullable=False,
        default="ai"
    )

    # --------------------------------------------------------
    # Main Prediction
    # --------------------------------------------------------

    primary_concern = Column(
        String(100),
        nullable=True
    )

    primary_confidence = Column(
        Float,
        nullable=True
    )

    # --------------------------------------------------------
    # All Predictions
    #
    # Stored as text/JSON string so that multiple detected
    # concerns can be stored in one record.
    # --------------------------------------------------------

    predictions = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Skin Health Score
    # --------------------------------------------------------

    skin_health_score = Column(
        Float,
        nullable=True
    )

    # --------------------------------------------------------
    # Risk Analysis
    # --------------------------------------------------------

    risk_level = Column(
        String(30),
        nullable=True
    )

    risk_factors = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # AI Analysis Explanation
    # --------------------------------------------------------

    analysis_summary = Column(
        Text,
        nullable=True
    )

    recommendations = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Medical Disclaimer / Notes
    # --------------------------------------------------------

    medical_note = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # --------------------------------------------------------
    # Representation
    # --------------------------------------------------------

    def __repr__(self):
        return (
            f"<SkinAnalysis("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"primary_concern='{self.primary_concern}', "
            f"score={self.skin_health_score}"
            f")>"
        )