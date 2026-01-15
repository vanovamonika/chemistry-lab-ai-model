from fastapi import FastAPI
from contextlib import asynccontextmanager
import time

from .dto import CompoundVisualRequest, ReactionRequest, VisualRequest, ReactionResponse, VisualResponse, HealthResponse

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
        response = predictor.predict_reaction_products(
            reactants=request.reactants,
            reaction_conditions=request.conditions or "",
            temperature=request.temperature or 20.0
        )
        print("Response:", response)
        
        # return ReactionResponse(
        #     success=True,
        #     reactants=request.reactants,
        #     products=products,
        # )
        return response
    except Exception as e:
        return ReactionResponse(
            success=False,
            reactants=request.reactants,
            products=[],
            equation="",
            generated_response="",
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
    
@app.post("/predict/compound_visuals", response_model=VisualResponse)
def predict_compound_visuals(request: CompoundVisualRequest):
    """
    Generate visual description of a chemical compound or reaction
    """
    try:
        predictor = get_predictor()
        visual_description = predictor.predict_compound_visuals(
            compound=request.compound,
            conditions=request.conditions
        )
        print("Visual description generated:", visual_description)
        print(type(visual_description))
        return VisualResponse(
            success=True,
            reaction=request.compound,
            visual_description=visual_description
        )
    except Exception as e:
        return VisualResponse(
            success=False,
            reaction=request.compound,
            visual_description={},
            error=str(e)
        )