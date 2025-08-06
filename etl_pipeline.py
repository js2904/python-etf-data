"""
ETF Portfolio ETL Pipeline - Clean and minimal implementation.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from etf_scraper import scrape_etf

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLake:
    """Simple data lake manager."""
    
    def __init__(self, base_path: str = "data_lake"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"
        
        # Create directories
        for path in [self.raw_path, self.processed_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, symbol: str, data: Dict, data_type: str) -> None:
        """Save data to appropriate location."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{timestamp}.json"
        
        if data_type == "raw":
            filepath = self.raw_path / filename
        else:
            filepath = self.processed_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {data_type} data for {symbol}")

class ETLPipeline:
    """Simple ETL pipeline."""
    
    def __init__(self, config_path: str = "etl_config.yaml"):
        self.data_lake = DataLake()
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration."""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            # Default config
            return {
                "etf_symbols": ["VTI", "VOO", "QQQ", "SPY"],
                "max_holdings": 100,
                "max_workers": 3
            }
    
    def extract_etf_data(self, symbol: str) -> Optional[Dict]:
        """Extract data for a single ETF."""
        try:
            logger.info(f"Extracting data for {symbol}")
            summary, holdings = scrape_etf(symbol, self.config.get("max_holdings", 100))
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "holdings": holdings
            }
        except Exception as e:
            logger.error(f"Failed to extract {symbol}: {e}")
            return None
    
    def transform_data(self, raw_data: Dict) -> Dict:
        """Transform raw data."""
        if not raw_data:
            return {}
        
        # Clean and structure data
        holdings = raw_data.get("holdings", [])
        
        # Add calculated fields to holdings
        for holding in holdings:
            if isinstance(holding, dict):
                # Add market value in millions
                market_value = holding.get('market_value_usd', 0)
                holding['market_value_millions'] = market_value / 1e6 if market_value else 0
                
                # Add weight in basis points
                weight = holding.get('weight_pct', 0)
                holding['weight_bps'] = weight * 10000 if weight else 0
        
        return {
            "symbol": raw_data["symbol"],
            "timestamp": raw_data["timestamp"],
            "summary": raw_data["summary"],
            "holdings": holdings
        }
    
    def run_pipeline(self, symbols: Optional[List[str]] = None) -> Dict:
        """Run the ETL pipeline."""
        start_time = time.time()
        
        if symbols is None:
            symbols = self.config.get("etf_symbols", ["VTI", "VOO"])
        
        logger.info(f"Starting ETL pipeline for {len(symbols)} symbols")
        
        # Extract phase
        raw_data_list = []
        with ThreadPoolExecutor(max_workers=self.config.get("max_workers", 3)) as executor:
            future_to_symbol = {executor.submit(self.extract_etf_data, symbol): symbol for symbol in symbols}
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    raw_data = future.result()
                    if raw_data:
                        raw_data_list.append(raw_data)
                        # Save raw data
                        self.data_lake.save_data(symbol, raw_data, "raw")
                except Exception as e:
                    logger.error(f"Failed to extract {symbol}: {e}")
        
        # Transform phase
        processed_data = []
        for raw_data in raw_data_list:
            try:
                transformed_data = self.transform_data(raw_data)
                if transformed_data:
                    processed_data.append(transformed_data)
                    # Save processed data
                    self.data_lake.save_data(transformed_data["symbol"], transformed_data, "processed")
            except Exception as e:
                logger.error(f"Failed to transform {raw_data.get('symbol', 'unknown')}: {e}")
        
        end_time = time.time()
        
        return {
            "duration_seconds": end_time - start_time,
            "symbols_processed": len(symbols),
            "successful_extractions": len(raw_data_list),
            "successful_transformations": len(processed_data)
        }

def main():
    """Run the ETL pipeline."""
    pipeline = ETLPipeline()
    stats = pipeline.run_pipeline()
    
    print("\n" + "="*50)
    print("ETL PIPELINE RESULTS")
    print("="*50)
    print(f"Symbols processed: {stats['symbols_processed']}")
    print(f"Successful extractions: {stats['successful_extractions']}")
    print(f"Successful transformations: {stats['successful_transformations']}")
    print(f"Duration: {stats['duration_seconds']:.2f} seconds")
    print("="*50)

if __name__ == "__main__":
    main() 