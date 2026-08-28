from pydantic import BaseModel
from typing import Optional


class SkinProfileCreate(BaseModel):
    skin_type: Optional[str] = None

    acne: bool = False

    pigmentation: bool = False

    dryness: bool = False

    sensitivity: bool = False

    dark_circles: bool = False

    wrinkles: bool = False

    redness: bool = False