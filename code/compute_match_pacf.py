import pandas as pd
import numpy as np
import os
import csv
import sys
import time
from statsmodels.tsa.stattools import pacf

def find_closest_cycle(lag, cycle_table):
    """Find closest reference cycle and absolute delta in days"""
    if lag is None or lag == '':
        return None, None
    
    try:
        lag_int = int(lag)
        closest = min(cycle_table, key=lambda x: abs(x - lag_int))
        delta = abs(lag_int - closest)
        return closest, delta
    except (ValueError, TypeError):
        return None, None

def main():
    # Validate asset class argument
    if len(sys.argv) < 2:
        print("Error: Asset class argument required (eq/ix/cr/co/fx)")
        sys.exit(1)
    
    asset_class = sys.argv[1].lower()
    valid_classes = ['eq', 'ix', 'cr', 'co', 'fx']
    if asset_class not in valid_classes:
        print(f"Error: Invalid asset class '{asset_class}'. Valid options: {', '.join(valid_classes)}")
        sys.exit(1)
    
    # Universal cycle range matching PSD analysis (179-747 days)
    MIN_LAG = 179
    MAX_LAG = 747
    
    # Unified cycle table (53 elements - matches PSD version)
    TABLE_CYCLES = [
        179, 183, 189, 196, 202, 206, 220, 237,
        243, 250, 260, 268, 273, 291, 308, 314,
        322, 331, 345, 355, 362, 368, 385, 403,
        408, 416, 426, 439, 457, 470, 480, 487,
        493, 510, 528, 534, 541, 551, 564, 582,
        605, 622, 636, 645, 653, 659, 676, 694,
        699, 707, 717, 730, 747
    ]   
    
    # Configuration
    DATA_DIR = "historical_data"
    OUTPUT_DIR = "pacf_results"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Output file path
    final_output_path = os.path.join(OUTPUT_DIR, f"match_pacf_results_{asset_class}.csv")
    
    # Initialize final output file with column names matching CAR.py expectations
    with open(final_output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Category', 'Instrument', 'Ticker',
            'Cycle1', 'Cycle1_Match', 'Cycle1_Delta',
            'Cycle2', 'Cycle2_Match', 'Cycle2_Delta'
        ])
        writer.writeheader()
    
    # Load instrument metadata
    instruments = []
    metadata_file = f'instrument_data_{asset_class}.csv'
    try:
        with open(metadata_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                instruments.append(row)
        print(f"Loaded {len(instruments)} instruments from {metadata_file}")
    except FileNotFoundError:
        print(f"Error: Metadata file not found - {metadata_file}")
        sys.exit(1)
    
    print(f"Starting PACF computation and cycle matching for {asset_class.upper()} instruments...")
    print(f"Using universal lag range: {MIN_LAG}-{MAX_LAG} days")
    start_time = time.time()
    processed_count = 0
    
    # 99% confidence level (z=2.576)
    CONFIDENCE_Z = 2.576
    
    # Process each instrument
    for inst in instruments:
        instrument_start = time.time()
        ticker = inst['Ticker']
        category = inst['Category']
        instrument_name = inst['Instrument']
        safe_ticker = ticker.replace('^', '').replace('=', '').replace('/', '_')
        file_path = os.path.join(DATA_DIR, f"{safe_ticker}.csv")
        
        # Initialize result dictionary
        match_result = {
            'Category': category,
            'Instrument': instrument_name,
            'Ticker': ticker,
            'Cycle1': None,
            'Cycle1_Match': None,
            'Cycle1_Delta': None,
            'Cycle2': None,
            'Cycle2_Match': None,
            'Cycle2_Delta': None
        }
        
        status = "SUCCESS"
        print(f"[{processed_count+1}/{len(instruments)}] Processing {ticker}...")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Data file not found: {os.path.abspath(file_path)}")
            
            # Load historical data
            data = pd.read_csv(file_path, parse_dates=['Date'])
            print(f"  Rows: {len(data)} | Period: {data['Date'].min().date()} to {data['Date'].max().date()}")
            
            # Ensure data is sorted chronologically
            data = data.sort_values('Date')
            
            # Check minimum data requirement (need at least 2*MAX_LAG for reliable PACF)
            if len(data) < MAX_LAG * 2:
                raise ValueError(f"Insufficient data ({len(data)} rows < {MAX_LAG*2})")
            
            # Calculate log returns
            closes = data['close'].values
            valid_mask = closes > 0
            valid_closes = closes[valid_mask]
            
            if len(valid_closes) < MAX_LAG * 2:
                raise ValueError("Insufficient positive closing prices")
                
            log_returns = np.log(valid_closes[1:]) - np.log(valid_closes[:-1])
            n = len(log_returns)
            
            # Compute PACF with maximum lag set to MAX_LAG
            pacf_vals = pacf(log_returns, nlags=MAX_LAG, method='ols')
            
            # Calculate 99% confidence threshold
            ci_threshold = CONFIDENCE_Z / np.sqrt(n)
            
            # Find significant lags within our range of interest
            significant_lags = []
            for lag in range(MIN_LAG, min(MAX_LAG + 1, len(pacf_vals))): 
                pacf_val = pacf_vals[lag]
                if not np.isfinite(pacf_val):
                    continue
                if abs(pacf_val) > ci_threshold:
                    significant_lags.append((lag, abs(pacf_val)))
            
            # Sort by significance (absolute PACF value)
            significant_lags.sort(key=lambda x: x[1], reverse=True)
            
            # Get top 2 lags only
            top_lags = [lag for lag, _ in significant_lags[:2]]
            
            # Store and match PACF results
            if top_lags:
                match_result['Cycle1'] = top_lags[0] if len(top_lags) > 0 else None
                match_result['Cycle1_Match'], match_result['Cycle1_Delta'] = find_closest_cycle(
                    match_result['Cycle1'], TABLE_CYCLES)
                
                if len(top_lags) > 1:
                    match_result['Cycle2'] = top_lags[1]
                    match_result['Cycle2_Match'], match_result['Cycle2_Delta'] = find_closest_cycle(
                        match_result['Cycle2'], TABLE_CYCLES)
                        
            print(f"  Found {len(significant_lags)} significant lags, top 2: {top_lags}")
            
        except Exception as e:
            status = f"ERROR: {str(e)}"
            print(f"  {status}")
        
        # Write final matched results directly to output file
        with open(final_output_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=match_result.keys())
            writer.writerow(match_result)
        
        processed_count += 1
        instrument_time = time.time() - instrument_start
        elapsed = time.time() - start_time
        avg_time = elapsed / processed_count
        remaining = avg_time * (len(instruments) - processed_count)
        
        print(f"  Status: {status} | Time: {instrument_time:.2f}s")
        print(f"  Elapsed: {elapsed//60:.0f}m {elapsed%60:.0f}s | ETA: {remaining//60:.0f}m {remaining%60:.0f}s")
    
    print(f"\nPACF computation and cycle matching complete for {asset_class.upper()} instruments!")
    print(f"Final results: {final_output_path}")
    print(f"Total time: {(time.time()-start_time)//60:.0f}m {(time.time()-start_time)%60:.0f}s")

if __name__ == "__main__":
    main()