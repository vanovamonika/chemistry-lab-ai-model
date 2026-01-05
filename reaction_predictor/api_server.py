from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
import time

# Import your ReactionPredictor class
from . import reaction_predictor

# Global shared instance
predictor = None
start_time = None

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifespan of the ReactionPredictor instance
    """
    global predictor, start_time
    
    # Startup
    print("🚀 Starting Chemical Reaction Predictor API...")
    print("📦 Loading Ollama model (phi3:mini)...")
    
    try:
        predictor = reaction_predictor.ReactionPredictor()
        # Optional: Test the model with a simple query
        print("✅ ReactionPredictor instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create ReactionPredictor: {e}")
        raise RuntimeError(f"Failed to initialize model: {e}")
    
    start_time = time.time()
    print(f"✅ API ready! Model loaded successfully.")
    
    # Yield control to the app
    yield
    
    # Shutdown
    print("🛑 Shutting down ReactionPredictor API...")
    # Add any cleanup here if needed
    print("✅ Cleanup complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Chemical Reaction Predictor API",
    description="Minimal API for predicting chemical reactions and generating visual descriptions",
    version="1.0.0",
    lifespan=lifespan
)

# Request Models
class OrganicReactionRequest(BaseModel):
    reactants: str
    reagents: Optional[str] = ""
    conditions: Optional[str] = ""
    temperature: Optional[float] = 20.0
    format: str = "names"  # "names" or "smiles"

class InorganicReactionRequest(BaseModel):
    reactants: str
    reagents: Optional[str] = ""
    conditions: Optional[str] = ""
    temperature: Optional[float] = 20.0

class VisualRequest(BaseModel):
    type: str  # "compound" or "reaction"
    reaction: str
    conditions: Optional[str] = "standard conditions"

# Response Models
class ReactionResponse(BaseModel):
    success: bool
    reactants: str
    reagents: str
    products: str
    reaction_type: str
    error: Optional[str] = None

class VisualResponse(BaseModel):
    success: bool
    type: str
    reaction: str
    visual_description: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_loaded: bool

# Helper to get the predictor instance
def get_predictor():
    if reaction_predictor is None:
        raise RuntimeError("ReactionPredictor not initialized")
    return reaction_predictor

# Root endpoint
@app.get("/")
def read_root():
    return {
        "api": "Chemical Reaction Predictor",
        "version": "1.0.0",
        "model": "phi3:mini via Ollama",
        "endpoints": {
            "/predict/organic": "POST - Predict organic reaction",
            "/predict/inorganic": "POST - Predict inorganic reaction", 
            "/predict/visual": "POST - Generate visual description",
            "/health": "GET - API health status",
            "/examples": "GET - Example reactions"
        }
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    uptime = time.time() - start_time if start_time else 0
    return HealthResponse(
        status="healthy" if reaction_predictor else "initializing",
        uptime_seconds=round(uptime, 2),
        model_loaded=reaction_predictor is not None
    )

# Organic reaction endpoint
@app.post("/predict/organic", response_model=ReactionResponse)
def predict_organic(request: OrganicReactionRequest):
    """
    Predict organic chemical reaction products
    """
    try:
        predictor = get_predictor()
        
        products = predictor.predict_reaction(
            reaction_type="organic",
            format=request.format,
            reactants=request.reactants,
            reagents=request.reagents,
            conditions=request.conditions,
            temperature=request.temperature
        )
        
        # Handle different return types from your class
        if isinstance(products, list):
            products = products[0] if products else "No products predicted"
        
        return ReactionResponse(
            success=True,
            reactants=request.reactants,
            reagents=request.reagents or "",
            products=products,
            reaction_type="organic"
        )
    except Exception as e:
        return ReactionResponse(
            success=False,
            reactants=request.reactants,
            reagents=request.reagents or "",
            products="",
            reaction_type="organic",
            error=str(e)
        )

# Inorganic reaction endpoint  
@app.post("/predict/inorganic", response_model=ReactionResponse)
def predict_inorganic(request: InorganicReactionRequest):
    """
    Predict inorganic chemical reaction products
    """
    try:
        predictor = get_predictor()
        
        products = predictor.predict_inorganic_reaction(
            reactants=request.reactants,
            reagents=request.reagents,
            reaction_conditions=request.conditions,
            temperature=request.temperature
        )
        
        # Handle different return types
        if isinstance(products, list):
            products = products[0] if products else "No products predicted"
        
        return ReactionResponse(
            success=True,
            reactants=request.reactants,
            reagents=request.reagents or "",
            products=products,
            reaction_type="inorganic"
        )
    except Exception as e:
        return ReactionResponse(
            success=False,
            reactants=request.reactants,
            reagents=request.reagents or "",
            products="",
            reaction_type="inorganic",
            error=str(e)
        )

# Visual prediction endpoint
@app.post("/predict/visual", response_model=VisualResponse)
def predict_visual(request: VisualRequest):
    """
    Generate visual description of a chemical compound or reaction
    """
    try:
        predictor = get_predictor()
        
        visual_description = predictor.predict_visuals(
            type=request.type,
            reaction=request.reaction,
            conditions=request.conditions
        )
        
        return VisualResponse(
            success=True,
            type=request.type,
            reaction=request.reaction,
            visual_description=visual_description
        )
    except Exception as e:
        return VisualResponse(
            success=False,
            type=request.type,
            reaction=request.reaction,
            visual_description="",
            error=str(e)
        )

# Examples endpoint
@app.get("/examples")
def get_examples():
    return {
        "note": "Use these examples with the POST endpoints",
        "organic_example": {
            "endpoint": "POST /predict/organic",
            "body": {
                "reactants": "benzene + nitric acid",
                "reagents": "sulfuric acid",
                "conditions": "50°C",
                "format": "names"
            }
        },
        "inorganic_example": {
            "endpoint": "POST /predict/inorganic", 
            "body": {
                "reactants": "HCl + NaOH",
                "conditions": "aqueous solution"
            }
        },
        "visual_example": {
            "endpoint": "POST /predict/visual",
            "body": {
                "type": "reaction",
                "reaction": "2H2 + O2 → 2H2O",
                "conditions": "combustion"
            }
        }
    }