from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RecommendationBase(BaseModel):
    action_title: str
    action_description: Optional[str] = None
    potential_impact: float
    status: str = "pending"

class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
