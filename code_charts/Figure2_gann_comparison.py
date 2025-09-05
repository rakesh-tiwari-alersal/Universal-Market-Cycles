import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_plot(df, low_points, title, filename, x_lim, y_lim=None):
    """
    Generates and saves a plot of Gann and Plastic equilibrium lines.
    
    Args:
        df (pd.DataFrame): The main DataFrame containing S&P 500 data.
        low_points (dict): Dictionary of low points to use for line origins.
        title (str): The title of the plot.
        filename (str): The name of the file to save the plot as.
        x_lim (tuple): The date range for the x-axis limits.
        y_lim (tuple, optional): The price range for the y-axis limits.
    """
    fig, ax1 = plt.subplots(figsize=(15, 8))
    
    # Filter data for the plotting window and plot it
    plot_df = df.loc[x_lim[0]:x_lim[1]]
    ax1.plot(plot_df.index, plot_df['close'], label='S&P 500 Close Price', color='black', linewidth=1)

    # Calculate and plot the equilibrium lines
    for label, low_date in low_points.items():
        low_price = df.loc[low_date, 'close']
        
        # Create a date range to extend the lines
        future_dates = pd.date_range(start=df.index.min(), end='2025-12-31', freq='B')
        start_date_idx = future_dates.get_loc(low_date)
        date_num = np.arange(len(future_dates)) - future_dates.get_loc(low_date)
        
        # Define the lines to plot with their ratios, colors, and styles
        lines_to_plot = {
            # Gann Lines - changed from dotted to dashed
            'Gann Equilibrium Line (1:1)': {'slope': 1.0, 'color': 'red', 'linestyle': '-', 'alpha': 0.75, 'linewidth': 1.5},
            'Gann (1:2)': {'slope': 0.5, 'color': 'red', 'linestyle': '--', 'alpha': 0.75, 'linewidth': 1.5},  # More faded
            
            # Plastic Lines
            'Plastic Equilibrium Line (1:1)': {'slope': 1.3247, 'color': 'blue', 'linestyle': '-', 'alpha': 1.0, 'linewidth': 1.5},
            'Plastic (1:2)': {'slope': 1.3247 / 2, 'color': 'blue', 'linestyle': '--', 'alpha': 1.0, 'linewidth': 1.5},  # More faded
        }

        for line_name, properties in lines_to_plot.items():
            line_values = properties['slope'] * date_num + low_price
            ax1.plot(
                future_dates,
                line_values,
                linestyle=properties['linestyle'],
                color=properties['color'],
                alpha=properties['alpha'],
                linewidth=properties['linewidth'],
                label=line_name
            )

    # Add title with padding to create space between title and plot
    ax1.set_title(title, fontdict={'weight': 'bold', 'size': 18}, pad=15)
    ax1.set_xlabel('Time → (Trading Days)', fontdict={'weight': 'bold', 'size': 18}, labelpad=10)
    ax1.set_ylabel('Price → (Daily Close)', fontdict={'weight': 'bold', 'size': 18}, labelpad=10)
    
    # Add legend
    ax1.legend(loc='upper left', fontsize=12)
    
    ax1.grid(True, alpha=0.5)
    
    # Set the x-axis limits to the specified window
    ax1.set_xlim(x_lim[0], x_lim[1])
    
    # Adjust the y-axis limits to be more readable
    if y_lim:
        ax1.set_ylim(y_lim[0], y_lim[1])
    else:
        ax1.autoscale_view()

    # Create a second y-axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('')

    # Explicitly synchronize the y-axis ticks and labels
    plt.draw()
    # Get the ticks from the primary axis after drawing
    ax2_ticks = ax1.get_yticks()
    # Set the ticks and labels for the secondary axis
    ax2.set_yticks(ax2_ticks)
    ax2.set_yticklabels([f'{t:,.0f}' for t in ax2_ticks])
    ax2.set_ylim(ax1.get_ylim())

    # Save the plot to a file
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved as '{filename}'")

# --- Main Script ---

# Load the data from historical_data folder
try:
    df_gspc = pd.read_csv('historical_data/GSPC.csv')
except FileNotFoundError:
    print("Error: historical_data/GSPC.csv not found. Please ensure the file is in the historical_data directory.")
    exit()

# Prepare the data
df_gspc['Date'] = pd.to_datetime(df_gspc['Date'])
df_gspc.set_index('Date', inplace=True)
df_gspc.sort_index(inplace=True)

# Find the 2008-2009 low point
low_points = {
    '2008-2009 low': df_gspc.loc['2008-01-01':'2009-12-31', 'close'].idxmin(),
}

# Generate the plot
generate_plot(
    df=df_gspc,
    low_points=low_points,
    title='Gann and Plastic Lines For S&P 500',
    filename='Figure2_gann_comparison.png',
    x_lim=(pd.to_datetime('2009-01-01'), pd.to_datetime('2025-12-31')),
    y_lim=(500, 7000)
)