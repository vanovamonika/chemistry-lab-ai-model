from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
import time

# Import your ReactionPredictor class
from . import reaction_predictor_class as rp

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
        predictor = rp.ReactionPredictor()
        print(predictor)
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
    products: str
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

# Helper to get the predictor instance
def get_predictor():
    if predictor is None:
        raise RuntimeError("ReactionPredictor not initialized")
    return predictor

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
        status="healthy" if predictor else "initializing",
        uptime_seconds=round(uptime, 2),
        model_loaded=predictor is not None
    )

# Inorganic reaction endpoint  
@app.post("/predict/products", response_model=ReactionResponse)
def predict_products(request: ReactionRequest):
    print("Received request:", request)
    """
    Predict inorganic chemical reaction products
    """
    try:
        predictor = get_predictor()
        print("Using predictor:", predictor)
        products = predictor.predict_reaction_products(
            reactants=request.reactants,
            reaction_conditions=request.conditions or "",
            temperature=request.temperature or 20.0
        )
        print("Predicted products:", products)
        
        return ReactionResponse(
            success=True,
            reactants=request.reactants,
            products=products,
        )
    except Exception as e:
        return ReactionResponse(
            success=False,
            reactants=request.reactants,
            products="",
            error=str(e)
        )

# Visual prediction endpoint
@app.post("/predict/reaction_visuals", response_model=VisualResponse)
def predict_reaction_visuals(request: VisualRequest):
    """
    Generate visual description of a chemical compound or reaction
    """
    try:
        predictor = get_predictor()
        
        visual_description = predictor.predict_reaction_visuals(
            reaction=request.reaction,
            products=request.products,
            reactant_visuals=request.reactant_visuals,
            conditions=request.conditions
        )
        
        return VisualResponse(
            success=True,
            reaction=request.reaction,
            visual_description=visual_description
        )
    except Exception as e:
        return VisualResponse(
            success=False,
            reaction=request.reaction,
            visual_description="",
            error=str(e)
        )