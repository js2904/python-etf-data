#!/usr/bin/env python3
"""
Simple API server for ETF data.
"""

from flask import Flask, jsonify, request
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_latest_data(symbol: str) -> dict:
    """Get latest data for a symbol."""
    data_lake = Path("data_lake")
    processed_path = data_lake / "processed"
    
    if not processed_path.exists():
        return {}
    
    # Find latest file for symbol
    files = list(processed_path.glob(f"{symbol}_*.json"))
    if not files:
        return {}
    
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {latest_file}: {e}")
        return {}

@app.route('/api/etfs')
def get_etfs():
    """Get list of available ETFs."""
    data_lake = Path("data_lake")
    processed_path = data_lake / "processed"
    
    if not processed_path.exists():
        return jsonify([])
    
    files = list(processed_path.glob("*.json"))
    symbols = set()
    
    for file in files:
        symbol = file.stem.split('_')[0]
        symbols.add(symbol)
    
    return jsonify(list(symbols))

@app.route('/api/etfs/<symbol>')
def get_etf_data(symbol):
    """Get data for a specific ETF."""
    data = get_latest_data(symbol)
    return jsonify(data)

@app.route('/api/etfs/<symbol>/holdings')
def get_etf_holdings(symbol):
    """Get holdings for a specific ETF."""
    data = get_latest_data(symbol)
    return jsonify(data.get('holdings', []))

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, port=3000) 