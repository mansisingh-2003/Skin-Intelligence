from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func

from database import Base


class SkinProfile(Base):
    __tablename__ = "skin_profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    skin_type = Column(String(50), nullable=True)

    acne = Column(Boolean, default=False)

    pigmentation = Column(Boolean, default=False)

    dryness = Column(Boolean, default=False)

    sensitivity = Column(Boolean, default=False)

    dark_circles = Column(Boolean, default=False)

    wrinkles = Column(Boolean, default=False)

    redness = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )