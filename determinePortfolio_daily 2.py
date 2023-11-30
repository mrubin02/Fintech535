import pandas as pd
import numpy as np
from scipy.optimize import minimize

# Load CSV data
df = pd.read_csv('dividend_data.csv')
df['Date'] = pd.to_datetime(df['Date'])

df = df.drop_duplicates(subset=['Date', 'Instrument'], keep='first')

# Pivot the table to have instruments as columns, dates as index, and closing prices as values
df_pivot = df.pivot(index='Date', columns='Instrument', values='close')

def get_annualized_performance(weights, mean_returns, cov_matrix):
    """Calculate annualized performance for a portfolio."""
    returns = np.sum(mean_returns * weights) * 252
    std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return std_dev, returns

def negative_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
    """Calculate the negative Sharpe ratio for a portfolio."""
    p_std_dev, p_return = get_annualized_performance(weights, mean_returns, cov_matrix)
    return -(p_return - risk_free_rate) / p_std_dev

risk_free_rate = 0.0463  # Change this to the current risk-free rate

# Dictionary to store daily weights
daily_weights = {}

for date in df_pivot[30:].index:

    # Calculate the start date of the lookback window (length of the current month)
    lookback_start_date = date - pd.DateOffset(30)

    # Select the data for the lookback window
    lookback_data = df_pivot.loc[lookback_start_date:date]
    
    # Calculate mean returns and covariance matrix
    mean_returns = lookback_data.pct_change(fill_method=None).mean()
    cov_matrix = lookback_data.pct_change(fill_method=None).cov()

    # Optimization
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
   
   # Updated constraint to ensure weights sum to 1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))
    result = minimize(negative_sharpe_ratio, num_assets * [1./num_assets], args=args, constraints=constraints, bounds=bounds)

    daily_weights[date] = result['x']

# Convert the daily_weights dictionary to a DataFrame
weights_df_daily = pd.DataFrame.from_dict(daily_weights, orient='index')
weights_df_daily.columns = df_pivot.columns  # Set the column names as the stock names

# Save the DataFrame to a CSV file
weights_df_daily.to_csv('optimized_portfolio_weights_daily.csv')
