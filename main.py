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
    print("Starting Chemical Reaction Predictor...")
    
    # Run API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    # run_api_server()
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