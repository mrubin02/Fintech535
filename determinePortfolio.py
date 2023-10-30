import pandas as pd
import numpy as np
from scipy.optimize import minimize

# Load CSV data
df = pd.read_csv('dividend_data.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Pivot the table to have instruments as columns, dates as index and closing prices as values
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

risk_free_rate = 0.01  # Change this to current risk-free rate
monthly_weights = {}

for date in pd.date_range(df_pivot.index.min(), df_pivot.index.max(), freq='M'):
    # Filter data for the month
    monthly_data = df_pivot[df_pivot.index.month == date.month]
    
    # Calculate mean returns and covariance matrix
    mean_returns = monthly_data.pct_change(fill_method=None).mean()
    cov_matrix = monthly_data.pct_change(fill_method=None).cov()


    # Optimization
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))
    result = minimize(negative_sharpe_ratio, num_assets * [1./num_assets], args=args, constraints=constraints, bounds=bounds)

    monthly_weights[date] = result['x']

    # Convert the monthly_weights dictionary to a DataFrame
weights_df = pd.DataFrame.from_dict(monthly_weights, orient='index')
weights_df.columns = df_pivot.columns  # Set the column names as the stock names

# Save the DataFrame to a CSV file
weights_df.to_csv('optimized_portfolio_weights.csv')

