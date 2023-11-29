import pandas as pd 
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_curve, roc_auc_score, RocCurveDisplay, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# Your code for reading data and preprocessing...

X = merged[['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU', 'SPLV.K']]
y = merged.iloc[:,:65]

# Shift y upwards by one row
y = y.shift(-1)

# Drop the last row from X and the first row from y
X = X.iloc[:-1, :]
y = y.iloc[:-1, :]

# Continue with scaling and model training
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_valid, y_train, y_valid = train_test_split(X_scaled, y, shuffle = True)

# Your model training and evaluation code...
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



    


