import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

# Make sure the 'BTC-USD.csv' file is inside a folder named 'historical_data'
DATA_FILE_PATH = os.path.join('historical_data', 'BTC-USD.csv')

# Define the lags to be used in the model
LAG_1 = 26
LAG_2 = 243
# ======================================================================

def create_model_and_plot(data_path, lag1, lag2):
    """
    Loads data, fits a linear regression model, and plots the results.

    Args:
        data_path (str): The file path to the CSV data.
        lag1 (int): The first lag to use in the model.
        lag2 (int): The second lag to use in the model.
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

    # Drop rows with NaN values
    data.dropna(inplace=True)

    # Add dates to the data DataFrame
    data['Date'] = df['Date'].iloc[data.index]

    # Define the dependent and independent variables
    X = data[[f'Yt-{lag1}', f'Yt-{lag2}']]
    y = data['Yt']

    # Fit the linear regression model with no intercept
    model = LinearRegression(fit_intercept=False)
    model.fit(X, y)

    # Get the predicted values
    y_pred = model.predict(X)

    # Calculate the R-squared value
    r_squared = r2_score(y, y_pred)

    # Get the coefficients
    coef_lag1 = model.coef_[0]
    coef_lag2 = model.coef_[1]

    # Select the last 1000 data points for plotting to ensure clarity
    plot_data = data.tail(1000).copy()
    plot_data['Yt_fitted'] = y_pred[-1000:]

    # Create a 4th degree polynomial trendline for the fitted model
    # Use the index as x values for polynomial fitting
    x_values = np.arange(len(plot_data)).reshape(-1, 1)
    y_values = plot_data['Yt_fitted'].values
    
    # Create and fit 4th degree polynomial model
    poly_features = PolynomialFeatures(degree=4)
    x_poly = poly_features.fit_transform(x_values)
    
    poly_model = LinearRegression()
    poly_model.fit(x_poly, y_values)
    
    # Generate trendline values
    x_trend = np.linspace(0, len(plot_data)-1, 1000).reshape(-1, 1)
    x_trend_poly = poly_features.transform(x_trend)
    y_trend = poly_model.predict(x_trend_poly)
    
    # Convert x positions to dates for plotting
    trend_dates = pd.date_range(
        start=plot_data['Date'].iloc[0],
        end=plot_data['Date'].iloc[-1],
        periods=1000
    )

    # Plot the graph
    plt.figure(figsize=(14, 8))

    # Plot the main series and the fitted line
    plt.plot(plot_data['Date'], plot_data['Yt'], label='Current Price ($Y_t$)', color='black', linewidth=2)
    plt.plot(plot_data['Date'], plot_data['Yt_fitted'], label='Fitted Model ($\hat{Y_t}$)', color='green', linestyle='-', linewidth=2)
    
    # Plot the 4th degree polynomial trendline
    plt.plot(trend_dates, y_trend, label='4th Degree Polynomial Trendline', color='red', linestyle='--', linewidth=3)

    # Add R-squared text to the plot with bold formatting
    text_x_pos = plt.gca().get_xlim()[0] + (plt.gca().get_xlim()[1] - plt.gca().get_xlim()[0]) * 0.05
    text_y_pos = plt.gca().get_ylim()[0] + (plt.gca().get_ylim()[1] - plt.gca().get_ylim()[0]) * 0.95
    plt.text(
        text_x_pos,
        text_y_pos,
        f'$\\mathbf{{R^2}}$ = {r_squared:.4f}',
        fontsize=14,
        ha='left',
        va='top',
        bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8)
    )

    # Add titles and labels with requested formatting
    plt.title(f'Bitcoin Price Series and Fitted Plastic Model with 4th Degree Polynomial Trendline\n', 
              fontsize=18, fontweight='bold', pad=5)
    plt.xlabel('Trading Date', fontsize=18, fontweight='bold')
    plt.ylabel('Daily Close Price', fontsize=18, fontweight='bold')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('Figure3_bitcoin_model.png')

    print("Plot saved successfully with R-squared value on the chart.")
    print(f"R-squared: {r_squared:.4f}")
    print(f"Model Coefficients: Lag {lag1} = {coef_lag1:.4f}, Lag {lag2} = {coef_lag2:.4f}")

# Execute the function
create_model_and_plot(DATA_FILE_PATH, LAG_1, LAG_2)