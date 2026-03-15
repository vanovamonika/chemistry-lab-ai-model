# Request Models
from pydantic import BaseModel
from typing import Optional

class ChemicalVisualRequest(BaseModel):
    formula: str
    name: str
    conditions: Optional[str] = "standard conditions"
    temperature: Optional[float] = 20.0


class ChemicalBatchItem(BaseModel):
    formula: str
    name: Optional[str] = None
    conditions: Optional[str] = "standard conditions"


class ChemicalBatchRequest(BaseModel):
    chemicals: list[ChemicalBatchItem]

class ChemicalVisualDescription(BaseModel):
    color_hex: str
    color: str
    state: str
    soluble_in_water: bool
    density: Optional[float] = None
    molar_mass: Optional[float] = None

class ChemicalVisualResponse(BaseModel):
    success: bool
    formula: str
    name: str
    visual_description: ChemicalVisualDescription
    error: Optional[str] = None

class CompleteReactionRequest(BaseModel):
    reactants: str
    conditions: Optional[str] = ""
    temperature: Optional[float] = 20.0
    reactant_visuals: str

class SolidElements(BaseModel):
    color_hex: str
    color: str

class Precipitation(BaseModel):
    color_hex: str
    color: str

class ReactionState(BaseModel):
    color_hex: str
    color: str
    state: str
    solid_elements: SolidElements
    bubbles: bool
    precipitation: Precipitation

class ReactionVisualDescription(BaseModel):
    middle_of_reaction: ReactionState
    final_state: ReactionState
    timing: str

class CompleteReactionResponse(BaseModel):
    success: bool
    reactants: str
    products: list[str]
    equation: str
    visual_description: ReactionVisualDescription
    error: Optional[str] = None



class ReactionRequest(BaseModel):
    reactants: str
    conditions: Optional[str] = ""
    temperature: Optional[float] = 20.0

class VisualRequest(BaseModel):
    reaction: str
    products: str 
    reactant_visuals: str
    conditions: Optional[str] = "standard conditions"

class ProductsRequest(BaseModel):
    reactants: str
    conditions: str
    temperature: float


# Response Models
class ProductsResponse(BaseModel):
    success: bool
    reactants: str
    products: list[str]
    equation: str
    error: Optional[str] = None

class VisualResponse(BaseModel):
    success: bool
    reaction: str
    visual_description: dict
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_loaded: bool


