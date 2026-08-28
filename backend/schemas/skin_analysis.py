from pydantic import BaseModel
from typing import Optional


class SkinAnalysisResponse(BaseModel):
    id: int
    user_id: int
    image_path: str

    acne: bool
    pigmentation: bool
    dryness: bool
    sensitivity: bool
    redness: bool
    dark_circles: bool
    wrinkles: bool

    confidence: Optional[float] = None
    analysis_result: Optional[str] = None

    class Config:
        from_attributes = True