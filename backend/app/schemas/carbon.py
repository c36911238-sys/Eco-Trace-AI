from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from app.db.models import CategoryEnum

class CarbonLogBase(BaseModel):
    category: CategoryEnum
    emission_amount: float
    source: Optional[str] = "manual"
    description: Optional[str] = None

class CarbonLogCreate(CarbonLogBase):
    pass

class CarbonLogResponse(CarbonLogBase):
    id: int
    user_id: int
    logged_date: datetime

    model_config = ConfigDict(from_attributes=True)

class SHAPExplanation(BaseModel):
    feature: str
    impact: float # Percentage or absolute contribution
    description: str

class CarbonPredictionResponse(BaseModel):
    predicted_emission: float
    target_date: datetime
    explanations: list[SHAPExplanation]

class TwinSimulationRequest(BaseModel):
    category_to_reduce: CategoryEnum
    reduction_percentage: float # e.g., 20.0 for 20%
    days_to_simulate: int = 30
