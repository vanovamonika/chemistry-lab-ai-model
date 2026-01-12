# Request Models
from pydantic import BaseModel
from typing import Optional

class ReactionRequest(BaseModel):
    reactants: str
    conditions: Optional[str] = ""
    temperature: Optional[float] = 20.0

class VisualRequest(BaseModel):
    reaction: str
    products: str 
    reactant_visuals: str
    conditions: Optional[str] = "standard conditions"

# Response Models
class ReactionResponse(BaseModel):
    success: bool
    reactants: str
    products: list[str]
    reaction: str
    generated_response: str
    error: Optional[str] = None

class VisualResponse(BaseModel):
    success: bool
    reaction: str
    visual_description: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_loaded: bool
