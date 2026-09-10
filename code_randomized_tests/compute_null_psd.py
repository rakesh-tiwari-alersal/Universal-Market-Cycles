"""
compute_null_psd.py

Monte Carlo null-model check for the PSD cycle-detection pipeline.

Purpose:
  Runs the EXACT SAME detection logic as compute_match_psd.py (periodogram
  settings, peak-finding parameters, period filter, top-2-by-power selection,
  nearest-cycle matching) but against synthetic data that is calibrated to
  match each real instrument's length and log-return volatility and contains
  NO real cycles by construction (i.i.d. Gaussian log returns == GBM).

  This produces an empirically-measured chance-rate CAR ceiling: how often
  the detector "finds" a Table-3 match in pure noise that merely has the
  same volatility/length fingerprint as the real data. Compare this directly
  against the real-data CAR (Table 4 in the paper) at the same tolerances
  (+-1, +-2, +-3) to see whether the real result clears the noise floor.

  find_dominant_cycles() and find_closest_cycle() below are copied verbatim
  from compute_match_psd.py -- do not edit them separately from that file,
  or this stops being a fair comparison.

Usage:
  python compute_null_psd.py <asset_class> [--n-panels 50] [--seed 42]

  <asset_class> reuses the same instrument_data_<asset_class>.csv metadata
  file and historical_data/<ticker>.csv files as compute_match_psd.py --
  real data is used ONLY to read each instrument's actual length and
  volatility for calibration, never to detect cycles from real prices.

  IMPORTANT: this writes one row PER INSTRUMENT per panel (identical
  schema/row-count to compute_match_psd.py's real output), and produces
  --n-panels separate panel files rather than one file with multiple rows
  per instrument. Feeding CAR.py a file with multiple rows per instrument
  will make it miscount "instruments" (e.g. 240 instruments x 50 sims in
  one file reads as ~12,000 instruments to a script built for one row per
  instrument) -- run CAR.py once per panel file instead, unmodified, and
  build a null distribution from the resulting set of CAR%% values.
"""

import pandas as pd
import numpy as np
import os
import csv
import sys
import time
import argparse
from scipy.signal import find_peaks, periodogram

# ====================================================================
# Copied verbatim from compute_match_psd.py -- keep identical
# ====================================================================

TABLE_CYCLES = [
    219, 237, 243, 250, 259, 267, 273,
    290, 308, 314, 322, 332, 344, 354,
    362, 368, 385, 403, 408, 416, 426,
    440, 456, 469, 479, 487, 493, 510,
    528, 534, 541, 551, 565, 622, 635,
    645, 653, 659, 676
]

MIN_PERIOD = 215
MAX_PERIOD = 680


def find_closest_cycle(period, cycle_table):
    """Find closest reference cycle and calculate delta"""
    if period is None or period == '':
        return None, None
    try:
        period_int = int(period)
        closest = min(cycle_table, key=lambda x: abs(x - period_int))
        delta = abs(period_int - closest)
        return closest, delta
    except (ValueError, TypeError):
        return None, None


def find_dominant_cycles(frequencies, psd, min_period=MIN_PERIOD, max_period=MAX_PERIOD):
    non_zero_mask = frequencies > 0
    frequencies = frequencies[non_zero_mask]
    psd = psd[non_zero_mask]

    if len(frequencies) == 0:
        return []

    periods = 1 / frequencies
    period_mask = (periods >= min_period) & (periods <= max_period)
    filtered_periods = periods[period_mask]
    filtered_psd = psd[period_mask]

    if len(filtered_psd) == 0:
        return []

    peak_indices, _ = find_peaks(filtered_psd, height=0.001 * np.max(filtered_psd), distance=1)

    if len(peak_indices) == 0:
        return []

    peak_periods = filtered_periods[peak_indices]
    peak_powers = filtered_psd[peak_indices]

    peaks_df = pd.DataFrame({'period': peak_periods, 'power': peak_powers})
    peaks_df = peaks_df.sort_values('power', ascending=False)

    top_10_cycles = peaks_df.head(10)
    if top_10_cycles.empty:
        return []

    all_peaks = []
    for _, row in top_10_cycles.iterrows():
        all_peaks.append({'period': row['period'], 'power': row['power']})

    return [int(round(p['period'])) for p in all_peaks[:2]]


# ====================================================================
# Null-model additions
# ====================================================================

def calibrate_from_real_data(file_path):
    """
    Read a real instrument CSV ONLY to extract (n_returns, mu, sigma) of its
    daily log returns, for calibrating a matched synthetic GBM series.
    Mirrors compute_match_psd.py's own loading/filtering logic exactly
    (same >1000-row floor, same positive-close filter) so the synthetic
    series faces the same eligibility bar the real pipeline does.
    """
    data = pd.read_csv(file_path, parse_dates=['Date'])
    data = data.sort_values('Date')
    if len(data) < 1000:
        return None

    closes = data['close'].values
    valid_closes = closes[closes > 0]
    if len(valid_closes) < 1000:
        return None

    log_returns = np.log(valid_closes[1:]) - np.log(valid_closes[:-1])
    n = len(log_returns)
    mu = float(np.mean(log_returns))
    sigma = float(np.std(log_returns, ddof=1))
    return n, mu, sigma


def synthetic_log_returns(n, mu, sigma, rng):
    """
    i.i.d. Gaussian log returns with the same length/mean/std as the real
    series == GBM with matching drift and volatility. No autocorrelation,
    no cycles, by construction -- this is the null.
    """
    return rng.normal(loc=mu, scale=sigma, size=n)


def run_one_detection(log_returns):
    """Identical periodogram call and detection path as compute_match_psd.py."""
    frequencies, psd = periodogram(log_returns, fs=1, scaling='density', window='hann')
    return find_dominant_cycles(frequencies, psd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_class", choices=['eq', 'ix', 'cr', 'co', 'fx'])
    parser.add_argument("--n-panels", type=int, default=50,
                         help="number of independent full synthetic panels to generate "
                              "(each panel = one row per instrument, matching the real "
                              "output schema exactly -- run CAR.py once per panel; default 50)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    DATA_DIR = "historical_data"
    OUTPUT_DIR = "psd_results"
    NULL_DIR = os.path.join(OUTPUT_DIR, "null_panels")
    os.makedirs(NULL_DIR, exist_ok=True)

    metadata_file = f'instrument_data_{args.asset_class}.csv'
    try:
        with open(metadata_file, 'r') as f:
            instruments = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Error: Metadata file not found - {metadata_file}")
        sys.exit(1)

    print(f"Loaded {len(instruments)} instruments from {metadata_file}")

    # Calibrate once per instrument -- (n, mu, sigma) don't change across panels,
    # only the random draw does. Real data is read here ONLY for this calibration.
    calibrated = []
    n_skipped = 0
    for inst in instruments:
        ticker = inst['Ticker']
        instrument_name = inst['Instrument']
        category = inst['Category']
        safe_ticker = ticker.replace('^', '').replace('=', '').replace('/', '_')
        file_path = os.path.join(DATA_DIR, f"{safe_ticker}.csv")
        if not os.path.exists(file_path):
            n_skipped += 1
            continue
        calib = calibrate_from_real_data(file_path)
        if calib is None:
            n_skipped += 1
            continue
        n, mu, sigma = calib
        calibrated.append((category, instrument_name, ticker, n, mu, sigma))

    print(f"Calibrated {len(calibrated)} instruments ({n_skipped} skipped -- "
          f"no file or insufficient history, same as the real pipeline would skip them)")
    print(f"Generating {args.n_panels} independent full panels, seed={args.seed}")
    print(f"Each panel file has EXACTLY the same schema as compute_match_psd.py's output: "
          f"one row per instrument -- rename it to match the real filename and run CAR.py "
          f"unmodified against it, once per panel.\n")

    start_time = time.time()
    for panel_idx in range(args.n_panels):
        panel_path = os.path.join(NULL_DIR, f"null_panel_{args.asset_class}_{panel_idx:03d}.csv")
        with open(panel_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Category', 'Instrument', 'Ticker',
                'Cycle1', 'Cycle1_Match', 'Cycle1_Delta',
                'Cycle2', 'Cycle2_Match', 'Cycle2_Delta'
            ])
            for category, instrument_name, ticker, n, mu, sigma in calibrated:
                synth_returns = synthetic_log_returns(n, mu, sigma, rng)
                peak_periods = run_one_detection(synth_returns)

                c1 = c1m = c1d = c2 = c2m = c2d = ''
                if len(peak_periods) > 0:
                    c1 = peak_periods[0]
                    c1m, c1d = find_closest_cycle(c1, TABLE_CYCLES)
                if len(peak_periods) > 1:
                    c2 = peak_periods[1]
                    c2m, c2d = find_closest_cycle(c2, TABLE_CYCLES)

                writer.writerow([category, instrument_name, ticker,
                                  c1, c1m, c1d, c2, c2m, c2d])

        if (panel_idx + 1) % 10 == 0 or panel_idx == args.n_panels - 1:
            elapsed = time.time() - start_time
            print(f"  panel {panel_idx+1}/{args.n_panels} written -> {panel_path}  "
                  f"({elapsed:.1f}s elapsed)")

    print(f"\nDone. {args.n_panels} panels written to {NULL_DIR}/")
    print("Each file has exactly one row per instrument -- identical row count and schema")
    print("to your real compute_match_psd.py output, so CAR.py needs zero changes.")

if __name__ == "__main__":
    main()