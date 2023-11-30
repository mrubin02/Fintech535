import pandas as pd 
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

# Read data
weights = pd.read_csv('optimized_portfolio_weights_daily.csv')
features = pd.read_csv('feature_data.csv')

# Adjust column names for merging
weights.columns.values[0] = 'date'
weights.set_index('date', inplace=True)
features.set_index('Date', inplace=True)

# Define the range of thresholds to test
thresholds = np.arange(0.01, 1.01, 0.01) # From 1% to 100%

best_auc = 0
best_threshold = 0

# Open a file to write the results
with open('threshold_evaluation_results.txt', 'w') as file:
    # Iterate over thresholds with a progress bar
    for threshold in tqdm(thresholds, desc="Evaluating Thresholds"):
        # Apply the inclusion threshold to the weights
        temp_weights = weights.copy()
        temp_weights[temp_weights < threshold] = 0
        temp_weights[temp_weights >= threshold] = 1

        # Merge the masked weights with features
        merged = pd.merge(left=temp_weights, right=features, left_index=True, right_index=True)

        X = merged[['XLV.PH', '.TRGSPI', '.TRGSPS', 'VNQ', 'SDY', 'XLU','SPLV.K','XLI', 'XLP', '.BCOMCLC', 'SLX', '.DRG', '.MIWO0CS00PUS', 'GE', "BA"]]
        y = merged.iloc[:,:65]

        # Shift y upwards by one row and adjust X, y accordingly
        y = y.shift(-1)
        X = X.iloc[:-1, :]
        y = y.iloc[:-1, :]

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split data
        X_train, X_valid, y_train, y_valid = train_test_split(X_scaled, y, shuffle=True)

        # Train models and evaluate performance
        aucs = []
        for i in y_train:
            y_train_target = y_train[i].values.reshape(-1,1)
            model = LinearRegression()
            model.fit(X_train, y_train_target)
            y_pred = model.predict(X_valid)
            y_pred_binary = np.where(y_pred < 0.1, 0, 1) # Using a fixed prediction threshold

            try:
                auc = roc_auc_score(y_valid[i], y_pred_binary)
                aucs.append(auc)
            except ValueError:
                continue

        average_auc = np.mean(aucs)
        file.write(f"Threshold: {threshold:.2f}, AUC: {average_auc:.4f}\n")

        # Update the best AUC and threshold if the current one is better
        if average_auc > best_auc:
            best_auc = average_auc
            best_threshold = threshold

    file.write(f"\nBest Inclusion Threshold: {best_threshold:.2f}, Best AUC: {best_auc:.4f}\n")

print("Evaluation complete. Results saved to threshold_evaluation_results.txt")
