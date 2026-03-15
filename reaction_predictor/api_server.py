from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from fastapi.middleware.cors import CORSMiddleware
from .dto import ChemicalBatchRequest, ChemicalVisualDescription, ChemicalVisualRequest, ChemicalVisualResponse, CompleteReactionRequest, CompleteReactionResponse, HealthResponse, ProductsRequest, ProductsResponse, ReactionRequest

# Import your ReactionPredictor class
from . import ollama_reaction_predictor as rp
from . import ollama_test
import time
import os
from typing import Any, Optional
from dotenv import load_dotenv
load_dotenv()


def _property_response(success: bool, value: Optional[float] = None, message: Optional[str] = None):
    """
    Stable response shape consumed by backend/frontend:
    { success: bool, value: number | null, message?: string }
    """
    payload = {
        "success": success,
        "value": value,
    }
    if message:
        payload["message"] = message
    return payload


def _normalize_numeric_property(raw_value: Any, property_name: str):
    """
    Normalize model output into a positive float or return (None, error_message).
    """
    if raw_value is None:
        return None, f"{property_name} prediction returned null"

    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        return None, f"Invalid {property_name} value type: {type(raw_value).__name__}"

    if numeric_value <= 0:
        return None, f"Invalid {property_name} value: must be > 0"

    return numeric_value, None

# Global shared instance
predictor = None
start_time = None

# Lifespan context manager for startup/shutdown
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Manage the lifespan of the ReactionPredictor instance
#     """
#     global predictor, start_time
    
#     # Startup
#     print("🚀 Starting Chemical Reaction Predictor API...")
#     print("📦 Loading Ollama model (phi3:mini)...")
    
#     try:
#         # predictor = rp.OllamaReactionPredictor()
#         print(predictor)
#         # Optional: Test the model with a simple query
#         print("✅ OllamaReactionPredictor instance created successfully")
#     except Exception as e:
#         print(f"❌ Failed to create OllamaReactionPredictor: {e}")
#         raise RuntimeError(f"Failed to initialize model: {e}")
    
#     start_time = time.time()
#     print(f"✅ API ready! Model loaded successfully.")
    
#     # Yield control to the app
#     yield
    
#     # Shutdown
#     print("🛑 Shutting down OllamaReactionPredictor API...")
#     # Add any cleanup here if needed
#     print("✅ Cleanup complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Chemical Reaction Predictor API",
    description="Minimal API for predicting chemical reactions and generating visual descriptions",
    version="1.0.0",
    # lifespan=lifespan
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
# def get_predictor():
#     if predictor is None:
#         raise RuntimeError("OllamaReactionPredictor not initialized")
#     return predictor

# Root endpoint
@app.get("/")
def read_root():
    return {
        "api": "Chemical Reaction Predictor",
        "version": "1.0.0",
        # "model": "wizardlm2:7b via Ollama",
        "endpoints": {
            "/predict/organic": "POST - Predict organic reaction",
            "/predict/inorganic": "POST - Predict inorganic reaction", 
            "/predict/visual": "POST - Generate visual description",
            "/health": "GET - API health status",
            "/examples": "GET - Example reactions"
        }
    }

# Health check endpoint
# @app.get("/health", response_model=HealthResponse)
# def health_check():
#     uptime = time.time() - start_time if start_time else 0
#     return HealthResponse(
#         status="healthy" if predictor else "initializing",
#         uptime_seconds=round(uptime, 2),
#         model_loaded=predictor is not None
#     )

@app.post("/predict/compound_visuals", response_model=ChemicalVisualResponse)
async def predict_compound_visuals(request: ChemicalVisualRequest):
    """
    Generate visual description of a chemical compound or reaction
    """
    try:
        print("Received request:", request)
        # predictor = get_predictor()
        response = await ollama_test.predict_compound_visuals(
            formula=request.formula,
            name=request.name,
            conditions=request.conditions
        )
        print("Visual description generated:", response.visual_description)
        return response
    except Exception as e:
        return ChemicalVisualResponse(
            success=False,
            formula=request.formula,
            name=request.name,
            visual_description=ChemicalVisualDescription(
                color_hex="#ffffff",
                color="unknown",
                state="unknown",
                soluble_in_water=False,
                density=None,
                molar_mass=None,
            ),
            error=str(e)
        )


@app.post("/predict/compound_visuals/batch", response_model=list[ChemicalVisualResponse])
async def predict_compound_visuals_batch(request: ChemicalBatchRequest):
    """
    Generate visual descriptions (including resolved name and density)
    for multiple chemicals concurrently.
    """
    try:
        payload = [chemical.model_dump() for chemical in request.chemicals]
        responses = await ollama_test.get_all_chemical_data(payload)
        return responses
    except Exception as e:
        # Keep response shape predictable even on top-level failure
        return [
            ChemicalVisualResponse(
                success=False,
                formula="unknown",
                name="unknown",
                visual_description=ChemicalVisualDescription(
                    color_hex="#ffffff",
                    color="unknown",
                    state="unknown",
                    soluble_in_water=False,
                    density=None,
                    molar_mass=None,
                ),
                error=str(e),
            )
        ]

@app.get("/predict/density")
async def predict_density(formula: str, name: str = None, conditions: str = "standard conditions"):
    """
    Predict the density of a chemical compound
    Query parameters:
    - formula: Chemical formula (e.g., "H2O")
    - name: Common name (optional, e.g., "water")
    - conditions: Environmental conditions (optional, default: "standard conditions")
    
    Returns: { "success": bool, "value": float | null, "message": str }
    """
    try:
        print(f"📏 Predicting density for {name or formula}...")
        density_raw = await ollama_test.predict_density(
            formula=formula,
            name=name or formula,
            conditions=conditions
        )
        density, validation_error = _normalize_numeric_property(density_raw, "density")

        if validation_error:
            print(f"⚠️ Density prediction validation failed: {validation_error}")
            return _property_response(False, None, validation_error)

        print(f"✅ Density prediction: {density}")
        return _property_response(True, density, "Density prediction succeeded")
    except Exception as e:
        print(f"❌ Error predicting density: {e}")
        return _property_response(False, None, str(e))

@app.get("/predict/molar-mass")
async def predict_molar_mass(formula: str, name: str = None, conditions: str = "standard conditions"):
    """
    Predict the molar mass of a chemical compound
    Query parameters:
    - formula: Chemical formula (e.g., "H2O")
    - name: Common name (optional, e.g., "water")
    - conditions: Environmental conditions (optional, default: "standard conditions")
    
    Returns: { "success": bool, "value": float | null, "message": str }
    """
    try:
        print(f"⚗️ Predicting molar mass for {name or formula}...")
        molar_mass_raw = await ollama_test.predict_molar_mass(
            formula=formula,
            name=name or formula,
            conditions=conditions
        )
        molar_mass, validation_error = _normalize_numeric_property(molar_mass_raw, "molar mass")

        if validation_error:
            print(f"⚠️ Molar mass prediction validation failed: {validation_error}")
            return _property_response(False, None, validation_error)

        print(f"✅ Molar mass prediction: {molar_mass}")
        return _property_response(True, molar_mass, "Molar mass prediction succeeded")
    except Exception as e:
        print(f"❌ Error predicting molar mass: {e}")
        return _property_response(False, None, str(e))

@app.post("/predict/products", response_model=ProductsResponse)
async def predict_products(request: ProductsRequest):
    print("Received request:", request)
    """
    Predict inorganic chemical reaction products
    """
    try:
        # predictor = get_predictor()
        # print("Using predictor:", predictor)
        response = await ollama_test.predict_products(
            reactants=request.reactants,
            conditions=request.conditions or "",
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
        return ProductsResponse(
            success=False,
            reactants=request.reactants,
            products=[],
            equation="",
            error=str(e)
        )
    
@app.options("/predict/compound_visuals")
async def options_route():
    return {"message": "OK"}


@app.options("/predict/compound_visuals/batch")
async def options_compound_visuals_batch():
    return {"message": "OK"}

@app.options("/predict/density")
async def options_density():
    return {"message": "OK"}

@app.options("/predict/molar-mass")
async def options_molar_mass():
    return {"message": "OK"}

@app.options("/predict/products")
async def options_route():
    return {"message": "OK"}

# @app.options("/health")
# async def options_route():
#     return {"message": "OK"}