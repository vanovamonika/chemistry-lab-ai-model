from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from fastapi.middleware.cors import CORSMiddleware
from .dto import ChemicalVisualRequest, ChemicalVisualResponse, CompleteReactionRequest, CompleteReactionResponse, HealthResponse, ProductsRequest, ProductsResponse, ReactionRequest

# Import your ReactionPredictor class
from . import ollama_reaction_predictor as rp
from . import ollama_test
import time
import os
from dotenv import load_dotenv
load_dotenv()

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
            visual_description={},
            error=str(e)
        )

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

# @app.post("/predict/reaction", response_model=CompleteReactionResponse)
# async def predict_reaction(request: CompleteReactionRequest):
#     print("Received request:", request)
#     """
#     Predict chemical reaction products, equation and visual description based on reactants, conditions and temperature
#     """
#     try:
#         predictor = get_predictor()
#         print("Using predictor:", predictor)
#         response = await predictor.predict_reaction(
#             reactants=request.reactants,
#             reactant_visuals=request.reactant_visuals,
#             reaction_conditions=request.conditions or "",
#             temperature=request.temperature or 20.0
#         )
#         print("Response:", response)
        
#         return response
#     except Exception as e:
#         print(f"Error during prediction: {e}")
#         return CompleteReactionResponse(
#             success=False,
#             reactants=request.reactants,
#             products=[],
#             equation="",
#             generated_response="",
#             visual_description={},
#             error=str(e)
#         )



# # Visual prediction endpoint
# @app.post("/predict/reaction_visuals", response_model=VisualResponse)
# def predict_reaction_visuals(request: VisualRequest):
#     """
#     Generate visual description of a chemical compound or reaction
#     """
#     try:
#         predictor = get_predictor()
        
#         visual_description = predictor.predict_reaction_visuals(
#             reaction=request.reaction,
#             products=request.products,
#             reactant_visuals=request.reactant_visuals,
#             conditions=request.conditions
#         )
        
#         return VisualResponse(
#             success=True,
#             reaction=request.reaction,
#             visual_description=visual_description
#         )
#     except Exception as e:
#         return VisualResponse(
#             success=False,
#             reaction=request.reaction,
#             visual_description="",
#             error=str(e)
#         )

# @app.options("/predict/reaction")
# async def options_route():
#     return {"message": "OK"}

@app.options("/predict/compound_visuals")
async def options_route():
    return {"message": "OK"}

# @app.options("/predict/reaction_visuals")
# async def options_route():
#     return {"message": "OK"}

@app.options("/predict/products")
async def options_route():
    return {"message": "OK"}

# @app.options("/health")
# async def options_route():
#     return {"message": "OK"}