#!/usr/bin/env python3
"""
Simple runner for the ETF portfolio project.
"""

import subprocess
import sys
import os

def run_etl():
    """Run the ETL pipeline."""
    print("Running ETL Pipeline...")
    try:
        result = subprocess.run([sys.executable, "etl_pipeline.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("ETL Pipeline completed successfully!")
            return True
        else:
            print(f"ETL Pipeline failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"ETL Pipeline error: {str(e)}")
        return False

def start_api():
    """Start the API server."""
    print("Starting API Server...")
    print("API available at: http://localhost:3000")
    print("Endpoints:")
    print("  GET /api/etfs - List all ETFs")
    print("  GET /api/etfs/{symbol} - Get ETF data")
    print("  GET /api/etfs/{symbol}/holdings - Get ETF holdings")
    print("  GET /api/health - Health check")
    print("\nPress Ctrl+C to stop the API server")
    
    try:
        subprocess.run([sys.executable, "api_server.py"])
    except KeyboardInterrupt:
        print("\nAPI server stopped")

def main():
    """Main runner."""
    print("ETF Portfolio Project - Simple Version")
    print("="*50)
    
    # Run ETL pipeline
    if not run_etl():
        print("ETL Pipeline failed. Exiting.")
        return
    
    # Start API server
    print("\nStarting API Server...")
    start_api()

if __name__ == "__main__":
    main() 