import pandas as pd 
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, roc_curve, roc_auc_score, RocCurveDisplay
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import sys

# read weights and set date to index
weights = pd.read_csv('optimized_portfolio_weights_daily.csv')
weights.columns.values[0] = 'date'
weights.set_index('date', inplace = True)

# set threshold to be included in portfolio 
threshold = .000001 

# mask weights
weights[weights<threshold] = 0
weights[weights>=threshold] = 1
weights.to_csv('weights_labels.csv')

# get features
features = pd.read_csv('feature_data.csv')
features.set_index('Date', inplace = True)
merged = pd.merge(left = weights, right = features, left_index = True,right_index = True)
merged.to_csv("features_and_labels.csv")

X = merged[['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU','SPLV.K','XLI', 'XLP', '.BCOMCLC', 'SLX', '.DRG', '.MIWO0CS00PUS', 'GE', "BA", ".BCOMKWC", "MUSA.K", ".BCOMCNC",".SOLLIT", ".BATTIDX1", "PEP.O_y", "TSLA.O", "MCD", "AAPL.O", "XME"]]
y = merged.iloc[:,:65]

# Shift y upwards by one row
y = y.shift(-1)

# Drop the last row from X and the first row from y
X = X.iloc[:-1, :]
y = y.iloc[:-1, :]

# Continue with scaling and model training
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Calculate the index to split the data on
split_index = int(len(X_scaled) * 0.8)

# Split the data without shuffling, ensuring that the model is trained on historical data only
X_train, X_valid = X_scaled[:split_index], X_scaled[split_index:]
y_train, y_valid = y[:split_index], y[split_index:]

"""model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_valid)
acc = accuracy_score(y_pred, y_valid)
print(acc)"""

def file_print(*args, **kwargs):
    with open('noFutureOutput.txt', 'a') as f:
        print(*args, **kwargs, file=f)

aucs = []
for i in y_train:
    y_pred = [] 
    for num, x in enumerate(y_train[i][490:]): 
        val = 490 + num 
        y = y_train[i][0:val].values.reshape(-1,1)
        X = X_train[0:val]
        model = LinearRegression()
        model.fit(X, y)
        y_pr = model.predict(X_valid)
        y_pr[y_pr < 0.1] = 0
        y_pr[y_pr >= 0.1] = 1
        y_pr = y_pr[-1][0]
        y_pred += [y_pr]
    try: 
        acc = accuracy_score(y_pred, y_train[i][490:])
        fpr, tpr, thresholds = roc_curve(y_train[i][490:], y_pred)
        auc = roc_auc_score(y_train[i][490:], y_pred)
        aucs += [auc]
        print(i + " auc score: " + str(auc))
        file_print(i + " auc score: " + str(auc))
        RocCurveDisplay.from_predictions(y_train[i][490:], y_pred)
    except: 
        print(i +' guessed all zeroes')
        file_print(i +' guessed all zeroes')

print(np.average(aucs))
file_print(np.average(aucs))