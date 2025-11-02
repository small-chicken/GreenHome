#%%
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone

import requests_cache

"""
This is just copied from a jupyter notebook so bad format
"""

def api_handler(start_date_str, end_date_str):


    base_url = "https://api.carbonintensity.org.uk/intensity"

    start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
    max_delta = timedelta(days=14)

    all_records = []
    current_start_dt = start_dt

    print(f"Starting data fetch from {start_dt} to {end_dt}...")

    while current_start_dt < end_dt:

        current_end_dt = min(current_start_dt + max_delta, end_dt)
        start_str = current_start_dt.isoformat().replace('+00:00', 'Z')
        end_str = current_end_dt.isoformat().replace('+00:00', 'Z')

        url = f"{base_url}/{start_str}/{end_str}"

        print(f"  Fetching chunk: {start_str} to {end_str}")

        try:
            response = requests.get(url)

            response.raise_for_status()

            data_chunk = response.json().get('data', [])

            if data_chunk:
                all_records.extend(data_chunk)

        except requests.exceptions.RequestException as e:
            print(f"  ERROR fetching data for chunk {start_str}: {e}")
            print("  Skipping this chunk and continuing...")
        current_start_dt = current_end_dt

    print(f"Fetch complete. Total records retrieved: {len(all_records)}")

    return {"data": all_records}


def create_full_forecast_training_data(api_data):
    print("processing data and engineering features...")
    df = pd.json_normalize(api_data['data'])

    df = df[['from', 'intensity.actual']]
    df = df.rename(columns={'intensity.actual': 'intensity_actual'})

    # Convert to Time-Series
    df['from'] = pd.to_datetime(df['from'])
    df = df.set_index('from').sort_index()

    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek

    df['hour_sin'] = np.sin(df['hour'] * (2 * np.pi / 24))
    df['hour_cos'] = np.cos(df['hour'] * (2 * np.pi / 24))
    df['day_of_week_sin'] = np.sin(df['day_of_week'] * (2 * np.pi / 7))
    df['day_of_week_cos'] = np.cos(df['day_of_week'] * (2 * np.pi / 7))

    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['intensity_t-1'] = df['intensity_actual'].shift(1)
    df['intensity_t-48'] = df['intensity_actual'].shift(48)  # 24 hours ago
    df['intensity_t-336'] = df['intensity_actual'].shift(336) # 1 week ago
    df['avg_intensity_last_3_hours'] = df['intensity_actual'].shift(1).rolling(window=6).mean()
    df['avg_intensity_last_6_hours'] = df['intensity_actual'].shift(1).rolling(window=12).mean()
    N_STEPS_AHEAD = 48

    for i in range(1, N_STEPS_AHEAD + 1):
        df[f'target_t+{i}'] = df['intensity_actual'].shift(-i)

    # Clean
    df_model = df.drop(columns=['hour', 'day_of_week', 'intensity_actual'])
    df_model = df_model.dropna()

    print(f"Processing complete. Training-ready table has {len(df_model)} rows.")

    return df_model



#%%

FALLBACK_DATA = {"data": [{"from":"2017-09-18T11:30Z","to":"2017-09-18T12:00Z","intensity":{"forecast":272,"actual":294,"index":"moderate"}},{"from":"2017-09-18T12:00Z","to":"2017-09-18T12:30Z","intensity":{"forecast":282,"actual":304,"index":"high"}},{"from":"2017-09-18T12:30Z","to":"2017-09-18T13:00Z","intensity":{"forecast":279,"actual":308,"index":"high"}},{"from":"2017-09-18T13:00Z","to":"2017-09-18T13:30Z","intensity":{"forecast":282,"actual":301,"index":"high"}},{"from":"2017-09-18T13:30Z","to":"2017-09-18T14:00Z","intensity":{"forecast":284,"actual":306,"index":"high"}},{"from":"2017-09-18T14:00Z","to":"2017-09-18T14:30Z","intensity":{"forecast":281,"actual":308,"index":"high"}},{"from":"2017-09-18T14:30Z","to":"2017-09-18T15:00Z","intensity":{"forecast":287,"actual":324,"index":"high"}}]} # (Truncated your long JSON)

start_date = "2025-01-01T00:00Z"
end_date = "2025-09-01T00:00Z"
api_data = None

try:

    api_data = api_handler(start_date, end_date)

    if not api_data or not api_data.get('data'):
        print("API fetch failed or returned no data. Using fallback data.")
        api_data = FALLBACK_DATA

except Exception as e:
    print(f"An error occurred during API fetch: {e}. Using fallback data.")
    api_data = FALLBACK_DATA

training_df = create_full_forecast_training_data(api_data)


#%% md
# # Historic Carbon Intensity data
#%%
training_df.head()
#%% md
# # Weather indicators
#%% md
# ### Historic weather features
# 
# OpenMeteo ERA5 Reanalysis
# 
# * Direct Normal Irradiance
# * Wind speed 100m
# * Precipitation
# * Temperature
# * Cloud_cover_total
#%%
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import numpy as np

cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 53.74,
    "longitude": -1.06,

    "start_date": "2025-01-01",
    "end_date": "2025-09-01",

    "hourly": ["temperature_2m", "wind_speed_100m", "precipitation", "cloud_cover", "direct_normal_irradiance_instant"],

    "models": "era5",
    "timezone": "auto"
}
responses = openmeteo.weather_api(url, params=params)

response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")

hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_wind_speed_100m = hourly.Variables(1).ValuesAsNumpy()
hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
hourly_cloud_cover = hourly.Variables(3).ValuesAsNumpy()
hourly_direct_normal_irradiance_instant = hourly.Variables(4).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
)}
hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["wind_speed_100m"] = hourly_wind_speed_100m
hourly_data["precipitation"] = hourly_precipitation
hourly_data["cloud_cover"] = hourly_cloud_cover
hourly_data["direct_normal_irradiance_instant"] = hourly_direct_normal_irradiance_instant

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_dataframe = hourly_dataframe.set_index('date')

print("\n--- Original Hourly Data ---")
hourly_dataframe.head()

#%%
hourly_dataframe.reset_index(inplace=True)
hourly_dataframe.rename(columns={'date': 'from'}, inplace=True)
hourly_dataframe['from'] = pd.to_datetime(hourly_dataframe['from'])

hourly_dataframe = hourly_dataframe.set_index('from')
hourly_dataframe.head()

hourly_df = hourly_dataframe.resample('30T').interpolate(method='linear')
hourly_df.head()

#%% md
# Merge historical datasets on from
#%%
merged_data = pd.DataFrame.merge(training_df, hourly_df, on = "from", how = 'left')
merged_data.head()
#%% md
# Reorder cols
#%%

hourly_cols = hourly_df.columns.tolist()
target_cols = [col for col in merged_data.columns if col not in hourly_cols]


new_order = hourly_cols + target_cols

merged_data = merged_data[new_order]
merged_data.head()

#%% md
# ### Add temperature historic features
#%%
merged_df = merged_data.copy()
merged_df["temp_t-1"]= merged_data['temperature_2m'].shift(1)
merged_df["temp_t-2"]= merged_data['temperature_2m'].shift(2)
merged_df["temp_t-48"] = merged_data['temperature_2m'].shift(48)
merged_df["temp_t-336"] = merged_data['temperature_2m'].shift(336)
merged_df["temp_avg_last_3_hours"] = merged_data['temperature_2m'].shift(1).rolling(window=6).mean()
merged_df["temp_avg_last_6_hours"] = merged_data['temperature_2m'].shift(1).rolling(window=12).mean()
merged_df.rename(columns={'temperature_2m': 'temp_actual'}, inplace=True)

merged_df.head()

#%% md
# ### Add wind speed historic features
#%%
merged_df.rename(columns={'wind_speed_100m': 'wind_actual'}, inplace=True)
merged_df["wind_t-1"] = merged_df["wind_actual"].shift(1)
merged_df["wind_t-2"] = merged_df["wind_actual"].shift(2)
merged_df["wind_t-48"] = merged_df["wind_actual"].shift(48)
merged_df["wind_t-336"] = merged_df["wind_actual"].shift(336)
merged_df["wind_avg_last_3_hours"] = merged_df["wind_actual"].shift(1).rolling(window=6).mean()
merged_df["wind_avg_last_6_hours"] = merged_df["wind_actual"].shift(1).rolling(window=12).mean()
#%% md
# ### Add precipitation Historic features
#%%
merged_df.rename(columns={'precipitation': 'precip_actual'}, inplace=True)
merged_df["precip_t-1"] = merged_df["precip_actual"].shift(1)
merged_df["precip_t-2"] = merged_df["precip_actual"].shift(2)
merged_df["precip_t-48"] = merged_df["precip_actual"].shift(48)
merged_df["precip_t-336"] = merged_df["precip_actual"].shift(336)
merged_df["precip_avg_last_3_hours"] = merged_df["precip_actual"].shift(1).rolling(window=6).mean()
merged_df["precip_avg_last_6_hours"] = merged_df["precip_actual"].shift(1).rolling(window=12).mean()
#%% md
# ### Add cloud cover historic features
#%%
merged_df.rename(columns = {"cloud_cover": "cloud_cover_actual"}, inplace = True)
merged_df["cloud_cover_t-1"] = merged_df["cloud_cover_actual"].shift(1)
merged_df["cloud_cover_t-2"] = merged_df["cloud_cover_actual"].shift(2)
merged_df["cloud_cover_t-48"] = merged_df["cloud_cover_actual"].shift(48)
merged_df["cloud_cover_t-336"] = merged_df["cloud_cover_actual"].shift(336)
merged_df["cloud_cover_avg_last_3_hours"] = merged_df["cloud_cover_actual"].shift(1).rolling(window=6).mean()
merged_df["cloud_cover_avg_last_6_hours"] = merged_df["cloud_cover_actual"].shift(1).rolling(window=12).mean()
#%% md
# ### Add irradiance historic features
#%%
merged_df.rename(columns = {"direct_normal_irradiance_instant": "irradiance_actual"}, inplace = True)
merged_df["irradiance_t-1"] = merged_df["irradiance_actual"].shift(1)
merged_df["irradiance_t-2"] = merged_df["irradiance_actual"].shift(2)
merged_df["irradiance_t-48"] = merged_df["irradiance_actual"].shift(48)
merged_df["irradiance_t-336"] = merged_df["irradiance_actual"].shift(336)
merged_df["irradiance_avg_last_3_hours"] = merged_df["irradiance_actual"].shift(1).rolling(window=6).mean()
merged_df["irradiance_avg_last_6_hours"] = merged_df["irradiance_actual"].shift(1).rolling(window=12).mean()

#%% md
# ### Reorder and Display
#%%
merged_df.dropna(inplace=True)
target_cols = ["temp_actual", "wind_actual", "precip_actual", "cloud_cover_actual", "irradiance_actual","temp_t-1","temp_t-2","temp_t-48","temp_t-336","temp_avg_last_3_hours","temp_avg_last_6_hours","wind_t-1","wind_t-2","wind_t-48","wind_t-336","wind_avg_last_3_hours","wind_avg_last_6_hours","precip_t-1","precip_t-2","precip_t-48","precip_t-336","precip_avg_last_3_hours","precip_avg_last_6_hours","cloud_cover_t-1","cloud_cover_t-2","cloud_cover_t-48","cloud_cover_t-336","cloud_cover_avg_last_3_hours","cloud_cover_avg_last_6_hours","irradiance_t-1","irradiance_t-2","irradiance_t-48","irradiance_t-336","irradiance_avg_last_3_hours","irradiance_avg_last_6_hours"]
new_order = target_cols + [col for col in merged_df.columns.tolist() if col not in target_cols]
merged_df = merged_df[new_order]
merged_df.iloc[0:20]
#%%

#%% md
# 
#%% md
# ### Past future weather forecast features
# 
# OpenMeteo Forecast API
# 
# DNI, temp, wind forecasts for 24 hrs ahead
#%%
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
params = {
	"latitude": 53.74,
	"longitude": -1.06,
	"start_date": "2025-01-01",
	"end_date": "2025-09-01",
	"hourly": ["temperature_2m", "wind_speed_180m", "direct_normal_irradiance_instant"],
}
responses = openmeteo.weather_api(url, params=params)

response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_wind_speed_180m = hourly.Variables(1).ValuesAsNumpy()
hourly_direct_normal_irradiance_instant = hourly.Variables(2).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["wind_speed_180m"] = hourly_wind_speed_180m
hourly_data["direct_normal_irradiance_instant"] = hourly_direct_normal_irradiance_instant

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_df =hourly_dataframe.copy()
#%%
hourly_df.reset_index(inplace=True)
hourly_df.rename(columns={'date': 'from'}, inplace=True)
hourly_df['from'] = pd.to_datetime(hourly_df['from'])
hourly_df = hourly_df.set_index('from')
hourly_df.head()
hourly_df = hourly_df.resample('30T').interpolate(method='linear')

hourly_df.drop(columns = ["index"], inplace = True)
hourly_df.head()

#%% md
# Create the future columns
#%%
new_columns = {}
for i in range(1, 49):
    new_columns[f'temp_t+{i}'] = hourly_df['temperature_2m'].shift(-i)
    new_columns[f'wind_t+{i}'] = hourly_df['wind_speed_180m'].shift(-i)
    new_columns[f'irradiance_t+{i}'] = hourly_df['direct_normal_irradiance_instant'].shift(-i)

hourly_df = pd.concat([hourly_df, pd.DataFrame(new_columns)], axis=1)

#%%
hourly_df.drop(columns = ["temperature_2m", "direct_normal_irradiance_instant","wind_speed_180m"], inplace = True)
#%%
hourly_df.head()
#%%
merged_df = merged_df.merge(hourly_df, on = "from", how = 'left')
#%%
merged_df
#%% md
# # Past Present Generation Mix Features
# 
# CSV for training, Elexon for prediction
#%% md
# ## Training CSV
#%%
gen_mix_df = pd.read_csv("data/generation_mix.csv")
#%%
gen_mix_df.columns
gen_mix_df.head()
gen_mix_df['DATETIME'] = pd.to_datetime(gen_mix_df['DATETIME'])
gen_mix_df = gen_mix_df.set_index('DATETIME')
target_cols = ["WIND","GAS","NUCLEAR","COAL","HYDRO","IMPORTS","BIOMASS","SOLAR","STORAGE"]
gen_mix_df = gen_mix_df[target_cols]
gen_mix_df.head()
#%%
gen_mix_df.reset_index(inplace=True)
gen_mix_df.rename(columns={'DATETIME': 'from'}, inplace=True)

merged_df.reset_index(inplace=True)

merged_df['from'] = merged_df['from'].dt.tz_localize(None)

merged_df = merged_df.merge(gen_mix_df, on = "from", how = 'left')

merged_df.set_index('from', inplace=True)

#%% md
# # Final Training Dataset
#%%
merged_df.head()
#%%
cols_to_drop = [f"{col}_x" for col in target_cols] + [f"{col}_y" for col in target_cols]
merged_df.drop(columns = cols_to_drop, inplace = True)

#%%
gen_mix_df.reset_index(inplace=True)
gen_mix_df.rename(columns={'DATETIME': 'from'}, inplace=True)
merged_df['from'] = merged_df['from'].dt.tz_localize(None)
merged_df = merged_df.merge(gen_mix_df, on = "from", how = 'left')
merged_df
merged_df.to_csv("TrainingSet.csv")
#%%
merged_df.head()
merged_df.to_csv("FinalTrainingSet.csv")
#%%
merged_df.shape