import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import joblib


try:
    df = pd.read_csv('../FinalTrainingSet.csv', index_col='from', parse_dates=True)
except FileNotFoundError:
    print('Error: FinalTrainingSet.csv not found.')

df.dropna(inplace=True)
df.drop(columns=["SOLAR"], inplace = True)

target_cols = [col for col in df.columns if col.startswith("target_")]

feature_cols = [col for col in df.columns if col not in target_cols and col != 'index']

X = df[feature_cols]
y = df[target_cols]

split = int(len(X) * 0.9)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

print(f"Training set size: {len(X_train)} rows")
print(f"Test set size:     {len(X_test)} rows")

xgb_model = xgb.XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth = 5,
    subsample = 0.8,
    colsample_bytree = 0.8,
    objective = 'reg:squarederror',
    random_state = 42,
    n_jobs=-1
)

multi_output_model = MultiOutputRegressor(xgb_model)

print("\nStarted Training...")
multi_output_model.fit(X_train, y_train)
print("Completed Training")


print("\nMaking predictions on the test set...")
y_pred = multi_output_model.predict(X_test)

actual_t_plus_2 = y_test['target_t+2']
actual_t_plus_48 = y_test['target_t+48']


pred_t_plus_2 = y_pred[:, 1]
pred_t_plus_48 = y_pred[:, 47]

mae_t_plus_2 = mean_absolute_error(actual_t_plus_2, pred_t_plus_2)
mae_t_plus_48 = mean_absolute_error(actual_t_plus_48, pred_t_plus_48)


print("\nFirst Prediction vis")

prediction_series = y_pred[0]
actual_series = y_test.iloc[0].values
time_steps = y_test.columns

plt.figure(figsize=(15, 6))
plt.plot(time_steps, actual_series, label='Actual CO₂ Intensity', marker='o')
plt.plot(time_steps, prediction_series, label='Predicted CO₂ Intensity', marker='x', linestyle='--')
plt.legend()
plt.title(f"24-Hour Forecast (Test Set Example)\n1-hr MAE: {mae_t_plus_2:.2f} | 24-hr MAE: {mae_t_plus_48:.2f}")
plt.ylabel('Carbon Intensity (gCO2/kWh)')
plt.xlabel('Time (t+n)')
plt.xticks(rotation=90)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# Save model to joblib

joblib.dump(multi_output_model, 'CarbonIntensityPredictoor.joblib')
