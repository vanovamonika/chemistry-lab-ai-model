#!/usr/bin/env python3
import argparse
import threading
import time
import reaction_predictor
import uvicorn
from reaction_predictor.api_server import app  # Import your FastAPI app

def run_api_server():
    """Run the FastAPI server in a separate thread"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def main():
    # parser = argparse.ArgumentParser(
    #     description="A chemical reaction predictor",
    #     epilog="Example: python reaction_predictor.py --reactants 'CCO.C(=O)O' --model sagawa/ReactionTransformer"
    # )
    
    # # Required arguments
    # parser.add_argument('--reactants', 
    #                    required=True,
    #                    help='SMILES string of reactants')
    
    # parser.add_argument('--reagents', 
    #                    default='',
    #                    help='SMILES string of reagents')
    
    
    # parser.add_argument('--temperature', '-t',
    #                    type=float,
    #                    default=20.0,
    #                    help='Temperature of the reaction in Celsius')
    
    # parser.add_argument('--conditions', '-c',
    #                    type=str,
    #                    default='',
    #                    help='Chemical reaction conditions description')
    
    # parser.add_argument('--type',
    #                    type=str,
    #                    default='inorganic',
    #                    help='Type of chemical reaction (e.g., organic, inorganic)')
        
    # # Choices
    # parser.add_argument('--format',
    #                    choices=['smiles', 'names'],
    #                    default='smiles',
    #                    help='Output format')
    
    # # Multiple values
    # # parser.add_argument('--reagents', nargs='+',
    # #                    help='List of reagents')
    
    # args = parser.parse_args()
    # reactants = args.reactants
    # reagents = args.reagents
    # predictor = reaction_predictor.ReactionPredictor()
    # reaction = predictor.predict_reaction(args.type, args.format, reactants, reagents, args.conditions, args.temperature)
    # # appearance_predictor = visual_prediction.AppearancePredictor()
    # visuals = predictor.predict_visuals(
    #     type='reaction',
    #     reaction=reaction,
    #     conditions=args.conditions)
    # print("Predicted visuals:\n", visuals)
    print("Starting Chemical Reaction Predictor...")
    
    # Run API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    print("API server started at http://localhost:8000")
    print("Interactive docs: http://localhost:8000/docs")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()