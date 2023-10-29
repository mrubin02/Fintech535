import pandas as pd
import numpy as np
from scipy.optimize import minimize

# Assuming 'data' is a DataFrame where each column is a stock, and the index is date
# e.g. data = pd.read_csv('your_price_data.csv', index_col=0, parse_dates=True)

def get_optimal_weights(prices):
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for asset in range(num_assets))
    result = minimize(portfolio_volatility, num_assets*[1./num_assets,], args=args, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

def portfolio_volatility(weights, mean_returns, cov_matrix):
    returns = np.dot(weights, mean_returns)
    std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return -returns/std_dev  # we want to maximize the Sharpe ratio, equivalent to minimizing the negative Sharpe

portfolio_matrix = pd.DataFrame(index=data.columns)

for end_date in pd.date_range(data.index[59], data.index[-1], freq='M'):
    start_date = end_date - pd.DateOffset(months=59)
    sub_data = data[start_date:end_date]
    
    # Filter out stocks with negative or zero returns in the last month
    positive_return_stocks = sub_data.pct_change().tail(1).squeeze() > 0
    sub_data = sub_data.loc[:, positive_return_stocks]
    
    weights = get_optimal_weights(sub_data)
    
    # Map back to all stocks
    full_weights = pd.Series(data=0, index=data.columns)
    full_weights[positive_return_stocks.index] = weights
    
    selected = (full_weights > 0).astype(int)  # assuming stocks with positive weights are selected
    
    portfolio_matrix[end_date.strftime('%Y-%m')] = selected

print(portfolio_matrix)

portfolio_matrix.to_csv('portfolio_matrix.csv')
