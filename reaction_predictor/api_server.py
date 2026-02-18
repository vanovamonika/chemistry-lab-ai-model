from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from .dto import CompleteReactionRequest, CompleteReactionResponse, CompoundVisualRequest, ReactionRequest, VisualRequest, ReactionResponse, VisualResponse, HealthResponse

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        # "http://localhost:3001",  # Alternative port
        # "https://your-production-domain.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
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
        "model": "wizardlm2:7b via Ollama",
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

@app.post("/predict/reaction", response_model=CompleteReactionResponse)
def predict_reaction(request: CompleteReactionRequest):
    print("Received request:", request)
    """
    Predict chemical reaction products, equation and visual description based on reactants, conditions and temperature
    """
    try:
        predictor = get_predictor()
        print("Using predictor:", predictor)
        response = predictor.predict_reaction(
            reactants=request.reactants,
            reactant_visuals=request.reactant_visuals,
            reaction_conditions=request.conditions or "",
            temperature=request.temperature or 20.0
        )
        print("Response:", response)
        
        # Update response with visual description
        
        return CompleteReactionResponse(
            success=True,
            reactants=request.reactants,
            products=response["products"],
            equation=response["equation"],
            # generated_response=response["generated_response"],
            visual_description=response["visual_description"]
        )
    except Exception as e:
        print(f"Error during prediction: {e}")
        return CompleteReactionResponse(
            success=False,
            reactants=request.reactants,
            products=[],
            equation="",
            generated_response="",
            visual_description={},
            error=str(e)
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

@app.options("/predict/reaction")
async def options_route():
    return {"message": "OK"}

@app.options("/predict/compound_visuals")
async def options_route():
    return {"message": "OK"}

@app.options("/predict/reaction_visuals")
async def options_route():
    return {"message": "OK"}

@app.options("/predict/products")
async def options_route():
    return {"message": "OK"}

@app.options("/health")
async def options_route():
    return {"message": "OK"}