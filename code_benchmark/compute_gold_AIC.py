import pandas as pd
import numpy as np
import sys
import os

# --- CONFIGURATION ---
TICKER = "GCF"
# Corrected Path to the historical data file
DATA_FILE_PATH = os.path.join('historical_data', f'{TICKER}.csv') 

# --- LAG SEARCH WINDOWS ---
P1_MIN, P1_MAX = 17, 54           # Short-term lag window (p1)
P_LONG_MIN, P_LONG_MAX = 175, 680 # Long-term lag window (p2 and p3)
MAX_MODEL_LAG = P_LONG_MAX        # Maximum lag needed for data alignment (680)

# ====================================================================
# OLS REGRESSION AND AIC UTILITIES (Flexible AR(p) Model)
# ====================================================================

def fit_ols(series, lags, max_lag):
    """
    Fits an AR(p) model where p = len(lags).
    Returns coefficients, SSE, and number of observations.
    """
    
    Y = series[max_lag:]
    N_obs = len(Y)
    k = len(lags) + 1 # Number of parameters (lags + intercept)

    if N_obs == 0:
        return np.zeros(k), np.inf, 0

    # Design Matrix X: Columns are R_{t-lag_i} and a final column of 1s (intercept)
    X = np.zeros((N_obs, k))
    
    for i, lag in enumerate(lags):
        X[:, i] = series[max_lag - lag : N_obs + max_lag - lag]
        
    X[:, k - 1] = 1 # Intercept

    try:
        # lstsq returns coefficients, sum of squared residuals, rank, and singular values
        coeffs, residuals_sum_of_squares, rank, singular_values = np.linalg.lstsq(X, Y, rcond=None)
        
        if residuals_sum_of_squares.size == 0 or residuals_sum_of_squares.ndim == 0:
             sse = np.sum((Y - X @ coeffs) ** 2)
        else:
             sse = residuals_sum_of_squares[0]
             
        return coeffs, sse, N_obs
    
    except np.linalg.LinAlgError:
        return np.zeros(k), np.inf, N_obs

def calculate_aic(n_obs, sse, k):
    """
    Calculates the Akaike Information Criterion (AIC) for k parameters.
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
        print(f"Error: Data file not found at {DATA_FILE_PATH}. Check if file is named {TICKER}.csv")
        sys.exit(1)

    # Calculate Log Returns (ln(P_t / P_{t-1}))
    prices = data['close'].values
    log_returns = np.diff(np.log(prices))
    
    n_full = len(log_returns)
    train_series = log_returns

    print(f"Loaded {TICKER} data ({n_full} observations of Log Returns).")

    # Generate full range of long lag candidates
    long_lags = list(range(P_LONG_MIN, P_LONG_MAX + 1))

    # ====================================================================
    # STEP 1: AR(2) Optimization (Find p1* and p2*) - Full Brute Force
    # ====================================================================
    
    best_aic_ar2 = np.inf
    best_lag1, best_lag2 = 0, 0
    
    print("\n--- Step 1: AR(2) Optimization (p1* and p2*) ---")

    for p1 in range(P1_MIN, P1_MAX + 1):
        for p2 in long_lags:
            
            if p1 >= p2: 
                continue
            
            lags = [p1, p2]
            
            # Fit the AR(2) model (k=3 parameters)
            coeffs, sse, N_obs = fit_ols(train_series, lags, MAX_MODEL_LAG)
            aic = calculate_aic(N_obs, sse, k=3)
            
            if aic < best_aic_ar2:
                best_aic_ar2 = aic
                best_lag1, best_lag2 = p1, p2

    p1_star = best_lag1
    p2_star = best_lag2
    
    print(f"Optimal Lags (p1*, p2*) from AR(2) search: {p1_star}, {p2_star}")
    print(f"Minimum AIC (AR(2)): {best_aic_ar2:.4f}")

    # Check if Step 1 succeeded
    if p1_star == 0 or p2_star == 0:
        print("Error: Step 1 failed to find valid AR(2) lags.")
        sys.exit(1)

    # ====================================================================
    # STEP 2: AR(3) Refinement (Find p3*) - Full Brute Force
    # ====================================================================
    
    best_aic_ar3 = np.inf
    best_lag3 = 0
    
    print("\n--- Step 2: AR(3) Refinement (p3*) ---")
    
    # p1* and p2* are fixed anchors for the AR(3) model
    fixed_lags = [p1_star, p2_star] 
    
    # Iterate through every possible long lag (p3)
    for p3 in long_lags:
        
        # Constraint: p3 must be greater than p2*
        if p3 <= p2_star: 
            continue
            
        lags = fixed_lags + [p3]
        
        # Fit the AR(3) model (k=4 parameters)
        coeffs, sse, N_obs = fit_ols(train_series, lags, MAX_MODEL_LAG)
        aic = calculate_aic(N_obs, sse, k=4)
        
        if aic < best_aic_ar3:
            best_aic_ar3 = aic
            best_lag3 = p3

    # --- 3. Final Output ---
    p3_star = best_lag3

    if p3_star == 0:
        print("Error: Step 2 failed to find a valid third lag (p3*).")
        sys.exit(1)
        
    # Sort the final lags for clear presentation (p1 < p2 < p3)
    final_lags = sorted([p1_star, p2_star, p3_star])

    print(f"Optimal Lags (p1*, p2*, p3*) from AR(3) refinement: {p1_star}, {p2_star}, {p3_star}")
    print(f"Minimum AIC (Final AR(3)): {best_aic_ar3:.4f}")
    
    print(f"\nOptimization Method: Two-Step Full Precision Search")
    print(f"Data Used: Log Returns (Stationary)")
    print(f"Optimal AR Lags (p1*, p2*, p3*) [Sorted]: {final_lags[0]}, {final_lags[1]}, {final_lags[2]}")
    print(f"Minimum AIC Value (Final AR(3)): {best_aic_ar3:.4f}")

if __name__ == "__main__":
    main()