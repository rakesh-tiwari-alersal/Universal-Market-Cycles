import pandas as pd
import numpy as np
import os
import csv
import time
import sys
from scipy.signal import welch, find_peaks, periodogram

# Validate command-line arguments
if len(sys.argv) < 2:
    print("Error: Asset class argument required (eq/ix/cr/co/fx)")
    print("Usage: python compute_match_psd.py <asset_class> [threshold]")
    sys.exit(1)

asset_class = sys.argv[1].lower()
valid_classes = ['eq', 'ix', 'cr', 'co', 'fx']
if asset_class not in valid_classes:
    print(f"Error: Invalid asset class '{asset_class}'. Valid options: {', '.join(valid_classes)}")
    sys.exit(1)

# Constants

THRESHOLD_PER_CLASS = {
    'eq': 0.30,
    'co': 0.60,
    'ix': 0.60,
    'cr': 0.60,
    'fx': 0.60
}

# Set default threshold based on asset class
DEFAULT_THRESHOLD = THRESHOLD_PER_CLASS[asset_class]
threshold = DEFAULT_THRESHOLD

if len(sys.argv) >= 3:
    try:
        threshold = float(sys.argv[2])
        if not 0 < threshold < 1:
            raise ValueError
        print(f"Using custom threshold: {threshold}")
    except ValueError:
        print(f"Invalid threshold value '{sys.argv[2]}'. Using default {DEFAULT_THRESHOLD}")
        threshold = DEFAULT_THRESHOLD

# Asset-specific configuration
PERIOD_RANGES = {
    'eq': (179, 511),
    'co': (249, 511),
    'ix': (342, 718),
    'cr': (179, 511),
    'fx': (179, 511)
}

# Updated unified cycle table (removed first 3 elements, formatted in 8 columns)
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
OUTPUT_DIR = "psd_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set range based on asset class
MIN_PERIOD, MAX_PERIOD = PERIOD_RANGES[asset_class]

# Output files
final_output_path = os.path.join(OUTPUT_DIR, f"match_psd_results_{asset_class}.csv")
log_path = os.path.join(OUTPUT_DIR, "psd_processing_log.csv")  # Single log file

# Initialize log file only if it doesn't exist
if not os.path.exists(log_path):
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'AssetClass', 'Category', 'Instrument', 'Ticker', 'Status', 'Message'])

# Initialize final output CSV
with open(final_output_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Category', 'Instrument', 'Ticker',
        'Cycle1', 'Cycle1_Match', 'Cycle1_Delta',
        'Cycle2', 'Cycle2_Match', 'Cycle2_Delta'
    ])

# Get instrument metadata
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

print(f"Starting PSD computation and cycle matching for {asset_class.upper()} instruments...")
print(f"Period range: {MIN_PERIOD}-{MAX_PERIOD} days | Threshold: {threshold}")
start_time = time.time()
processed_count = 0

def log_entry(timestamp, asset_class, category, instrument, ticker, status, message):
    """Log processing status to file"""
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, asset_class, category, instrument, ticker, status, message])

def find_closest_cycle(period, cycle_table):
    """Find closest cycle and absolute delta in days"""
    if period is None or period == '':
        return None, None
    
    try:
        period_int = int(period)
        closest = min(cycle_table, key=lambda x: abs(x - period_int))
        delta = abs(period_int - closest)
        return closest, delta
    except (ValueError, TypeError):
        return None, None

def find_dominant_cycles(frequencies, psd, min_period=MIN_PERIOD, max_period=MAX_PERIOD, threshold=threshold):
    """Identify dominant cycles in the specified period range (up to 2 cycles)"""
    # Exclude zero frequency
    non_zero_mask = frequencies > 0
    frequencies = frequencies[non_zero_mask]
    psd = psd[non_zero_mask]
    
    if len(frequencies) == 0:
        return []
    
    # Convert to periods
    periods = 1 / frequencies
    
    # Filter for period range
    period_mask = (periods >= min_period) & (periods <= max_period)
    filtered_periods = periods[period_mask]
    filtered_psd = psd[period_mask]
    
    if len(filtered_psd) == 0:
        return []
    
    # Find peaks
    peak_indices, _ = find_peaks(filtered_psd, height=0.001 * np.max(filtered_psd), distance=1)
    
    if len(peak_indices) == 0:
        return []
    
    # Get peak data
    peak_periods = filtered_periods[peak_indices]
    peak_powers = filtered_psd[peak_indices]
    
    # Create DataFrame for sorting
    peaks_df = pd.DataFrame({'period': peak_periods, 'power': peak_powers})
    peaks_df = peaks_df.sort_values('power', ascending=False)
  
    # Get top 10 cycles
    top_10_cycles = peaks_df.head(10)
    
    if top_10_cycles.empty:
        return []
    
    # Calculate total power
    total_power = top_10_cycles['power'].sum()
    
    if total_power == 0:
        return []
    
    
    # Determine how many cycles to include based on threshold (up to 2 cycles)
    n_cycles = len(top_10_cycles)
    cum_power = 0.0
    selected_cycles = []
    
    # Check if we should include cycles based on threshold
    # Case 2: Threshold met by first two cycles
    if n_cycles >= 2:
        if (top_10_cycles.iloc[0]['power'] + top_10_cycles.iloc[1]['power']) >= threshold * total_power:
            selected_cycles.append(top_10_cycles.iloc[0])
            selected_cycles.append(top_10_cycles.iloc[1])

    # Case 3: Threshold met by first cycle alone (treat same as first two)
    elif n_cycles >= 1:
        if top_10_cycles.iloc[0]['power'] >= threshold * total_power:
            selected_cycles.append(top_10_cycles.iloc[0])

    # Return only period values, limited to 2 cycles
    return [int(round(p['period'])) for p in selected_cycles][:2]


for inst in instruments:
    instrument_start = time.time()
    ticker = inst['Ticker']
    category = inst['Category']
    instrument_name = inst['Instrument']
    safe_ticker = ticker.replace('^', '').replace('=', '').replace('/', '_')
    file_path = os.path.join(DATA_DIR, f"{safe_ticker}.csv")
    
    # Initialize result dictionary for final output (only 2 cycles)
    result = {
        'Category': category,
        'Instrument': instrument_name,
        'Ticker': ticker,
        'Cycle1': '',
        'Cycle1_Match': '',
        'Cycle1_Delta': '',
        'Cycle2': '',
        'Cycle2_Match': '',
        'Cycle2_Delta': ''
    }
    
    status = "SUCCESS"
    message = ""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"[{processed_count+1}/{len(instruments)}] Processing {ticker}...")
    
    try:
        # Validate and load data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {os.path.abspath(file_path)}")
        
        data = pd.read_csv(file_path, parse_dates=['Date'])
        print(f"  Rows: {len(data)} | Period: {data['Date'].min().date()} to {data['Date'].max().date()}")
        
        data = data.sort_values('Date')
        
        if len(data) < 1000:
            raise ValueError(f"Insufficient data ({len(data)} rows < 1000)")
        
        # Calculate returns
        closes = data['close'].values
        if np.any(closes <= 0):
            raise ValueError("Non-positive closing prices detected")
        
        log_returns = np.log(closes[1:]) - np.log(closes[:-1])
        
        # Compute PSD
        frequencies, psd = periodogram(log_returns, fs=1, scaling='density', window='hann')
        
        # Find dominant cycles (up to 2)
        peak_periods = find_dominant_cycles(frequencies, psd, threshold=threshold)
        print(f"  Found {len(peak_periods)} cycles: {peak_periods}")
        
        # Store cycles in result
        if peak_periods:
            for i, period in enumerate(peak_periods):
                if i < 2:  # Only store up to 2 cycles
                    result[f'Cycle{i+1}'] = period
                    match, delta = find_closest_cycle(period, TABLE_CYCLES)
                    result[f'Cycle{i+1}_Match'] = match
                    result[f'Cycle{i+1}_Delta'] = delta
        
    except Exception as e:
        status = "ERROR"
        message = str(e)
        print(f"  {status}: {message}")
    
    # Log and save
    log_entry(timestamp, asset_class, category, instrument_name, ticker, status, message)
    
    # Write final results (only 2 cycles)
    with open(final_output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            result['Category'],
            result['Instrument'],
            result['Ticker'],
            result['Cycle1'],
            result['Cycle1_Match'],
            result['Cycle1_Delta'],
            result['Cycle2'],
            result['Cycle2_Match'],
            result['Cycle2_Delta']
        ])
    
    processed_count += 1
    instrument_time = time.time() - instrument_start
    elapsed = time.time() - start_time
    avg_time = elapsed / processed_count
    remaining = avg_time * (len(instruments) - processed_count)
    
    print(f"  Status: {status} | Time: {instrument_time:.2f}s | "
          f"ETA: {remaining//60:.0f}m {remaining%60:.0f}s")

print(f"\nCompleted {asset_class.upper()} instruments!")
print(f"Final results: {final_output_path}")
print(f"Logs: {log_path}")
print(f"Total time: {(time.time()-start_time)//60:.0f}m {(time.time()-start_time)%60:.0f}s")