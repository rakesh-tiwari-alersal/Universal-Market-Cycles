import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Same filename and folders
DATA_FILE_PATH = os.path.join('historical_data', 'BTC-USD.csv')

# ----------------------------------------------------------------------
# FUNCTION: Compute Out‑of‑Sample R^2 for AR(2) with custom lags
# ----------------------------------------------------------------------
def compute_ar2_r2(data_path, lag1, lag2):
    df = pd.read_csv(data_path)
    df['Date'] = pd.to_datetime(df['Date'])
    prices = df['close']

    # Build lagged DF
    data = pd.DataFrame({'Yt': prices})
    data[f'Yt-{lag1}'] = data['Yt'].shift(lag1)
    data[f'Yt-{lag2}'] = data['Yt'].shift(lag2)
    data.dropna(inplace=True)

    X = data[[f'Yt-{lag1}', f'Yt-{lag2}']]
    y = data['Yt']

    # 80/20 split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Fit AR(2)
    model = LinearRegression(fit_intercept=False)
    model.fit(X_train, y_train)
    y_pred_test = model.predict(X_test)

    # Out‑of‑sample R^2
    r2 = r2_score(y_test, y_pred_test)
    return r2

# ----------------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------------
if __name__ == '__main__':

    # Plastic lags
    lagA1, lagA2 = 41, 243

    # AIC Benchmark lags
    lagB1, lagB2 = 33, 505

    r2_plastic = compute_ar2_r2(DATA_FILE_PATH, lagA1, lagA2)
    r2_aic = compute_ar2_r2(DATA_FILE_PATH, lagB1, lagB2)

    print(f"Plastic AR({lagA1},{lagA2}) R^2 = {r2_plastic:.6f}")
    print(f"AIC Benchmark AR({lagB1},{lagB2}) R^2 = {r2_aic:.6f}")
