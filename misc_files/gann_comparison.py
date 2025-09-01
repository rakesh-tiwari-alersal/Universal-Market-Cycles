import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    ax1.plot(plot_df.index, plot_df['close'], label='S&P 500 Close Price', color='black')

    # Calculate and plot the equilibrium lines
    for label, low_date in low_points.items():
        low_price = df.loc[low_date, 'close']
        
        # Set line styles and colors
        if '2008-2009 low' in label:
            gann_linestyle = '-'
            plastic_linestyle = '-'
        else: # Assumes the other label is '2018 low'
            gann_linestyle = '--'
            plastic_linestyle = '--'
        
        # Change Gann color to dark red as requested, Plastic remains blue
        gann_color = 'darkred'
        plastic_color = 'blue'

        # Create a date range to extend the lines
        future_dates = pd.date_range(start=df.index.min(), end='2025-12-31', freq='B')
        start_date_idx = df.index.get_loc(low_date)
        date_num = np.arange(len(future_dates)) - future_dates.get_loc(low_date)
        
        # Gann equilibrium line: y = x + offset
        gann_line = 1.0 * date_num + low_price
        
        # Plastic equilibrium line: y = 1.3247 * x + offset
        plastic_line = 1.3247 * date_num + low_price
        
        # Plot the lines with the determined styles and colors
        ax1.plot(future_dates, gann_line, linestyle=gann_linestyle, color=gann_color, alpha=0.7, label=f'Gann ({label})')
        ax1.plot(future_dates, plastic_line, linestyle=plastic_linestyle, color=plastic_color, alpha=0.7, label=f'Plastic ({label})')

    # Add labels and title to the primary axis
    ax1.set_title(title, fontweight='bold', fontsize=18, pad=20)
    ax1.set_xlabel('Time → (Days)', fontweight='bold', fontsize=18, labelpad=20)
    ax1.set_ylabel('Price → (S&P 500 Close)', fontweight='bold', fontsize=18, labelpad=20)
    ax1.legend()
    ax1.grid(True)
    
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
    ax2.set_ylim(ax1.get_ylim())

    # Explicitly synchronize the y-axis ticks and labels
    plt.draw()
    ax2.set_yticks(ax1.get_yticks())
    ax2.set_yticklabels([f'{t:,.0f}' for t in ax1.get_yticks()])

    # Save the plot to a file
    plt.savefig(filename)
    plt.close(fig)
    print(f"Plot saved as '{filename}'")

# Load the data once
try:
    df_gspc = pd.read_csv('GSPC.csv')
except FileNotFoundError:
    print("Error: GSPC.csv not found. Please ensure the file is in the same directory.")
    exit()

df_gspc['Date'] = pd.to_datetime(df_gspc['Date'])
df_gspc.set_index('Date', inplace=True)
df_gspc.sort_index(inplace=True)

# Generate the single chart with updated variable names for clarity
low_points = {
    '2008-2009 low': df_gspc.loc['2008-01-01':'2009-12-31', 'close'].idxmin(),
    '2018 low': df_gspc.loc['2018-01-01':'2018-12-31', 'close'].idxmin(),
}
generate_plot(
    df=df_gspc,
    low_points=low_points,
    title='Gann and Plastic Equilibrium Lines (2021-2025)',
    filename='gann_equilibrium_comparison.png', # File name changed here
    x_lim=(pd.to_datetime('2021-01-01'), pd.to_datetime('2025-12-31')),
    y_lim=(2000, 7000)
)