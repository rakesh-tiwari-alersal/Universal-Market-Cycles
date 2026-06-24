import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Same folder + filename pattern
DATA_FILE_PATH = os.path.join('historical_data', 'GDAXI.csv')

# ----------------------------------------------------------------------
# FUNCTION: Compute Out-of-Sample R^2 for Log Returns (AR3)
# ----------------------------------------------------------------------
def compute_ar3_log_returns_r2(data_path, lag1, lag2, lag3):
    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate stationary log returns first
    log_returns = np.log(df['close']).diff().dropna()
    data = pd.DataFrame({'Yt': log_returns})

    data[f'Yt-{lag1}'] = data['Yt'].shift(lag1)
    data[f'Yt-{lag2}'] = data['Yt'].shift(lag2)
    data[f'Yt-{lag3}'] = data['Yt'].shift(lag3)
    data.dropna(inplace=True)

    X = data[[f'Yt-{lag1}', f'Yt-{lag2}', f'Yt-{lag3}']]
    y = data['Yt']

    # 80/20 split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Fit AR(3)
    model = LinearRegression(fit_intercept=False)
    model.fit(X_train, y_train)
    y_pred_test = model.predict(X_test)

    # Out-of-sample R^2
    r2 = r2_score(y_test, y_pred_test)
    return r2

# ----------------------------------------------------------------------
# FUNCTION: Compute Out-of-Sample R^2 for Price Series (AR3)
# ----------------------------------------------------------------------
def compute_ar3_price_series_r2(data_path, lag1, lag2, lag3):
    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])
    prices = df['close']

    # Build lagged DF directly from absolute prices
    data = pd.DataFrame({'Yt': prices})
    data[f'Yt-{lag1}'] = data['Yt'].shift(lag1)
    data[f'Yt-{lag2}'] = data['Yt'].shift(lag2)
    data[f'Yt-{lag3}'] = data['Yt'].shift(lag3)
    data.dropna(inplace=True)

    X = data[[f'Yt-{lag1}', f'Yt-{lag2}', f'Yt-{lag3}']]
    y = data['Yt']

    # 80/20 split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Fit AR(3)
    model = LinearRegression(fit_intercept=False)
    model.fit(X_train, y_train)
    y_pred_test = model.predict(X_test)

    # Out-of-sample R^2
    r2 = r2_score(y_test, y_pred_test)
    return r2

# ----------------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------------
if __name__ == '__main__':

    # Plastic lags
    p1, p2, p3 = 17, 237, 368

    # AIC Benchmark lags
    a1, a2, a3 = 40, 633, 671

    # Log Returns Calculations
    r2_lr_plastic = compute_ar3_log_returns_r2(DATA_FILE_PATH, p1, p2, p3)
    r2_lr_aic = compute_ar3_log_returns_r2(DATA_FILE_PATH, a1, a2, a3)

    # Price Series Calculations
    r2_price_plastic = compute_ar3_price_series_r2(DATA_FILE_PATH, p1, p2, p3)
    r2_price_aic = compute_ar3_price_series_r2(DATA_FILE_PATH, a1, a2, a3)

    print(f"Plastic AR({p1},{p2},{p3}) OOS-LogReturns R^2   = {r2_lr_plastic:.6f}")
    print(f"Plastic AR({p1},{p2},{p3}) OOS-PriceSeries R^2  = {r2_price_plastic:.6f}")
    print(f"AIC Benchmark AR({a1},{a2},{a3}) OOS-LogReturns R^2   = {r2_lr_aic:.6f}")
    print(f"AIC Benchmark AR({a1},{a2},{a3}) OOS-PriceSeries R^2  = {r2_price_aic:.6f}")