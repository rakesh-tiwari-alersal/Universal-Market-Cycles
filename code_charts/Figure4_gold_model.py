import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Make sure the 'BTC-USD.csv' file is inside a folder named 'historical_data'
DATA_FILE_PATH = os.path.join('historical_data', 'GCF.csv')

# Define the lags to be used in the model
LAG_1 = 47
LAG_2 = 308
LAG_3 = 385
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

    # Calculate the out-of-sample R-squared value
    r_squared = r2_score(y_test, y_pred_test)

    # Get the coefficients from the model fitted on the training data
    coef_lag1 = model.coef_[0]
    coef_lag2 = model.coef_[1]
    coef_lag3 = model.coef_[2]

    # Combine the fitted training data predictions and test data predictions
    y_pred_train = model.predict(X_train)
    y_pred_all = np.concatenate([y_pred_train, y_pred_test])

    # Select the last 1000 data points for plotting to ensure clarity
    plot_data = data.tail(1000).copy()
    plot_data['Yt_fitted'] = y_pred_all[-1000:]
    # === END OF MODIFIED CODE ===

    # Plot the graph
    plt.figure(figsize=(14, 8))

    # Plot the main series and the fitted line
    plt.plot(plot_data['Date'], plot_data['Yt'], label='Current Price ($Y_t$)', color='black', linewidth=1)
    plt.plot(plot_data['Date'], plot_data['Yt_fitted'], label=r'Fitted Model ($\hat{Y_t}$)', color='blue', linestyle='-', linewidth=1)

    # Add R-squared text to the plot with bold formatting
    plt.text(
        0.50,  # x-position 
        0.95,  # y-position (0.95 = near top)
        f'$\\mathbf{{Out-of-Sample\\ R^2}}$ = {r_squared:.4f}',
        fontsize=12,
        ha='right',
        va='top',
        transform=plt.gca().transAxes,
        bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8),
        fontweight='bold'
    )
    
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
    plt.title(f'Illustration: Gold Price Series and Fitted Plastic Model\n', 
              fontsize=18, fontweight='bold', pad=0)
    plt.xlabel('Trading Date →', fontsize=18, fontweight='bold',labelpad=10)
    plt.ylabel('Daily Close Price →', fontsize=18, fontweight='bold',labelpad=10)
    
    # Move legend to upper left
    plt.legend(loc='upper left', fontsize=12)
    
    plt.grid(True, color='gray', alpha=0.5)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('Figure4_gold_model.png')

    print("Plot saved successfully with R-squared value on the chart.")
    print(f"Out-of-sample R-squared: {r_squared:.4f}")
    print(f"Model Coefficients: Lag {lag1} = {coef_lag1:.4f}, Lag {lag2} = {coef_lag2:.4f}, Lag {lag3} = {coef_lag3:.4f}")

# Execute the function
create_model_and_plot(DATA_FILE_PATH, LAG_1, LAG_2, LAG_3)