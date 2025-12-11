import pandas as pd
import numpy as np
import sys
import os

# --- CONFIGURATION ---
TICKER = "BTC-USD"
# Path to the historical data file
DATA_FILE_PATH = os.path.join('historical_data', f'{TICKER}.csv') 

# --- DUAL-LAG SEARCH WINDOWS ---
P1_MIN, P1_MAX = 17, 54       # Short-term lag window
P2_MIN, P2_MAX = 175, 680     # Long-term lag window
MAX_MODEL_LAG = P2_MAX        # Maximum lag needed for data alignment

# ====================================================================
# OLS REGRESSION AND AIC UTILITIES
# ====================================================================

def fit_ols_non_sequential(series, lag1, lag2, max_lag):
    """
    Constructs the design matrix X (R_{t-p1}, R_{t-p2}, 1) and solves OLS.
    Returns [phi_p1, phi_p2, intercept], SSE, and number of observations.
    """
    
    Y = series[max_lag:]
    N_obs = len(Y)

    if N_obs == 0:
        return np.array([0, 0, 0]), np.inf, 0

    X = np.zeros((N_obs, 3))
    X[:, 0] = series[max_lag - lag1 : N_obs + max_lag - lag1]
    X[:, 1] = series[max_lag - lag2 : N_obs + max_lag - lag2]
    X[:, 2] = 1 

    try:
        coeffs, residuals_sum_of_squares, rank, singular_values = np.linalg.lstsq(X, Y, rcond=None)
        
        if residuals_sum_of_squares.size == 0 or residuals_sum_of_squares.ndim == 0:
             sse = np.sum((Y - X @ coeffs) ** 2)
        else:
             sse = residuals_sum_of_squares[0]
             
        return coeffs, sse, N_obs
    
    except np.linalg.LinAlgError:
        return np.array([0, 0, 0]), np.inf, N_obs

def calculate_aic(n_obs, sse, k=3):
    """
    Calculates the Akaike Information Criterion (AIC).
    k=3 is the number of parameters.
    """
    if n_obs <= k or sse <= 0:
        return np.inf
    
    # AIC Formula: N * log(SSE / N) + 2 * k
    return n_obs * np.log(sse / n_obs) + 2 * k

# ====================================================================
# MAIN SCRIPT LOGIC
# ====================================================================

def main():
    
    # --- 1. Load and Prepare Data ---
    try:
        data = pd.read_csv(DATA_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_FILE_PATH}.")
        sys.exit(1)

    # Calculate Log Returns (ln(P_t / P_{t-1}))
    prices = data['close'].values
    log_returns = np.diff(np.log(prices))
    
    n_full = len(log_returns)
    train_series = log_returns

    print(f"Loaded {TICKER} data ({n_full} observations of Log Returns).")

    # --- 2. AIC Optimization (Find p1*, p2*) on Log Returns ---
    best_aic = np.inf
    best_lag1, best_lag2 = 0, 0
    
    # Iterate through all combinations
    for p2 in range(P2_MIN, P2_MAX + 1):
        for p1 in range(P1_MIN, P1_MAX + 1):
            
            if p1 >= p2: 
                continue
            
            coeffs, sse, N_obs = fit_ols_non_sequential(train_series, p1, p2, MAX_MODEL_LAG)
            
            aic = calculate_aic(N_obs, sse, k=3)
            
            if aic < best_aic:
                best_aic = aic
                best_lag1, best_lag2 = p1, p2

    # --- 3. Output Results (Trimmed Format) ---
    if best_lag1 == 0 or best_lag2 == 0:
        print("Error: AIC optimization failed to find valid lags.")
        sys.exit(1)
    
    print(f"\nData Used: Log Returns (Stationary)")
    print(f"Optimal AR Lags (p1*, p2*): {best_lag1}, {best_lag2}")
    print(f"Minimum AIC Value: {best_aic:.4f}")

if __name__ == "__main__":
    main()