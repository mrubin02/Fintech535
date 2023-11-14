import pandas as pd 
import numpy as np 

weights = pd.read_csv('optimized_portfolio_weights_daily.csv')
weights.columns.values[0] = 'date'
weights.set_index('date', inplace = True)

weights[weights<.01] = 0
weights[weights>=.01] = 1

print(weights)

weights.to_csv('weights_labels.csv')
