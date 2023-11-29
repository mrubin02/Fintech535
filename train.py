import pandas as pd 
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, roc_curve, roc_auc_score, RocCurveDisplay
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

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

X = merged[['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU', 'SPLV.K', 'XLI', 'XLP']]
scaler = StandardScaler()
scaler.fit_transform(X)

y = merged.iloc[:,:65]

X_train, X_valid, y_train, y_valid = train_test_split(X, y, shuffle = True)

"""model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_valid)
acc = accuracy_score(y_pred, y_valid)
print(acc)"""

for i in y_train:
    y = y_train[i].values.reshape(-1,1)
    model = LinearRegression()
    model.fit(X_train, y)
    y_pred = model.predict(X_valid)
    y_pred[y_pred < 0.1] = 0
    y_pred[y_pred >= 0.1] = 1
    try: 
        acc = accuracy_score(y_pred, y_valid[i])
        fpr, tpr, thresholds = roc_curve(y_valid[i], y_pred)
        auc = roc_auc_score(y_valid[i], y_pred)
        if auc>0.5:
            print(i + " auc score: " + str(auc))
        RocCurveDisplay.from_predictions(y_valid[i], y_pred)
    except: 
        print('guessed all zeroes')



    


