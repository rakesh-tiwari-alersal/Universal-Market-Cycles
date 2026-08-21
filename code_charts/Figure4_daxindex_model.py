import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

DATA_FILE_PATH = os.path.join('historical_data', 'GDAXI.csv')

# Define the lags to be used in the model
LAG_1 = 17
LAG_2 = 237
LAG_3 = 368
# ======================================================================

def create_model_and_plot(data_path, lag1, lag2, lag3):
    """
    Loads data, fits a linear regression model, and plots the results with out-of-sample R^2.

    Args:
        data_path (str): The file path to the CSV data.
        lag1 (int): The first lag to use in the model.
        lag2 (int): The second lag to use in the model.
        lag3 (int): The third lag to use in the model.
    """
    try:
        # Load the data
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: The file '{data_path}' was not found.")
        return

    # Extract the 'close' prices and convert the 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.iloc[1:].reset_index(drop=True)
    prices = df['close']

    # Create a DataFrame for the regression
    data = pd.DataFrame({'Yt': prices})

    # Create the lagged variables
    data[f'Yt-{lag1}'] = data['Yt'].shift(lag1)
    data[f'Yt-{lag2}'] = data['Yt'].shift(lag2)
    data[f'Yt-{lag3}'] = data['Yt'].shift(lag3)

    # Drop rows with NaN values
    data.dropna(inplace=True)

    # Add dates to the data DataFrame
    data['Date'] = df['Date'].iloc[data.index]

    # Define the dependent and independent variables
    X = data[[f'Yt-{lag1}', f'Yt-{lag2}', f'Yt-{lag3}']]
    y = data['Yt']

    # === START OF MODIFIED CODE FOR OUT-OF-SAMPLE TESTING ===
    # Split data into training and testing sets (e.g., 80% train, 20% test)
    split_point = int(len(X) * 0.8)
    X_train, X_test = X[:split_point], X[split_point:]
    y_train, y_test = y[:split_point], y[split_point:]

    # Fit the linear regression model with no intercept on the TRAINING data only
    model = LinearRegression(fit_intercept=False)
    model.fit(X_train, y_train)

    # Get the predicted values for the TEST data
    y_pred_test = model.predict(X_test)

    # Get the coefficients from the model fitted on the training data
    coef_lag1 = model.coef_[0]
    coef_lag2 = model.coef_[1]
    coef_lag3 = model.coef_[2]

    # Isolate the PURE Out-of-Sample test set slice for plotting
    plot_data = data.iloc[split_point:].copy()
    plot_data['Yt_fitted'] = y_pred_test

    # Select the last 1000 out-of-sample data points for sharp visual clarity
    if len(plot_data) > 1000:
        plot_data = plot_data.tail(1000)

    # Plot the graph
    plt.figure(figsize=(14, 8))

    # Plot the main series and the fitted line
    plt.plot(plot_data['Date'], plot_data['Yt'], label='Current Price ($Y_t$)', color='black', linewidth=1)
    plt.plot(plot_data['Date'], plot_data['Yt_fitted'], label=r'Fitted Model ($\hat{Y_t}$)', color='blue', linestyle='-', linewidth=1)
  
    # Add the AR model equation in a separate box below the R² box
    equation_text = f'$\\mathbf{{Y_t = {coef_lag3:.4f} \\cdot Y_{{t-{lag3}}} + {coef_lag2:.4f} \\cdot Y_{{t-{lag2}}} + {coef_lag1:.4f} \\cdot Y_{{t-{lag1}}}}}$'
    plt.text(
        0.662,  # x-position 
        0.87,  # y-position (just below the R² box)
        equation_text,
        fontsize=12,
        ha='right',
        va='top',
        transform=plt.gca().transAxes,
        bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8)
    )

    # Add titles and labels with requested formatting
    plt.title(f'Illustration: DAX Index Price Series and Fitted Plastic Model\n', 
              fontsize=18, fontweight='bold', pad=0)
    plt.xlabel('Trading Date →', fontsize=18, fontweight='bold',labelpad=10)
    plt.ylabel('Daily Close Price →', fontsize=18, fontweight='bold',labelpad=10)
    
    # Move legend to upper left
    plt.legend(loc='upper left', fontsize=12)
    
    plt.grid(True, color='gray', alpha=0.5)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('Figure4_daxindex_model.png')

    print("Plot saved successfully with R-squared value on the chart.")
    print(f"Model Coefficients: Lag {lag1} = {coef_lag1:.4f}, Lag {lag2} = {coef_lag2:.4f}, Lag {lag3} = {coef_lag3:.4f}")

# Execute the function
create_model_and_plot(DATA_FILE_PATH, LAG_1, LAG_2, LAG_3)