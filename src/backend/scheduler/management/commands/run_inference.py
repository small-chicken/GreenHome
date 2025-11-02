from django.core.management.base import BaseCommand
from django.conf import settings
import os
import requests
import json
import pandas as pd
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta, timezone
import joblib  

from scheduler.models import CarbonPredictions

# helper funcs

def get_intensity_lags():
    """
    Get the CO2 intensity data and format
    """
    week_ago = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    url = f"https://api.carbonintensity.org.uk/intensity/{week_ago}/{now}"
    response = requests.get(url)
    response.raise_for_status()
    api_data = response.json()

    # flatten
    df = pd.json_normalize(api_data['data'])
    df = df[['from', 'intensity.actual']]
    df = df.rename(columns={'intensity.actual': 'intensity_actual'})

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
    df['intensity_t-48'] = df['intensity_actual'].shift(48)
    df['intensity_t-336'] = df['intensity_actual'].shift(336)
    df['avg_intensity_last_3_hours'] = df['intensity_actual'].shift(1).rolling(window=6).mean()
    df['avg_intensity_last_6_hours'] = df['intensity_actual'].shift(1).rolling(window=12).mean()
    return df.iloc[-1:].reset_index(drop=True)

def get_weather_lags():
    #Boilerplate api stuff
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"  # Use forecast to get 'past_days'
    params = {
        "latitude": 53.74, "longitude": -1.06,
        "past_days": 8,  
        "forecast_days": 1,
        "hourly": ["temperature_2m", "wind_speed_100m", "precipitation", "cloud_cover",
                   "direct_normal_irradiance_instant"],
        "timezone": "auto"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}

    hourly_data["temp_actual"] = hourly.Variables(0).ValuesAsNumpy()
    hourly_data["wind_actual"] = hourly.Variables(1).ValuesAsNumpy()
    hourly_data["precip_actual"] = hourly.Variables(2).ValuesAsNumpy()
    hourly_data["cloud_cover_actual"] = hourly.Variables(3).ValuesAsNumpy()
    hourly_data["irradiance_actual"] = hourly.Variables(4).ValuesAsNumpy()

    hourly_dataframe = pd.DataFrame(data=hourly_data).set_index('date')

    weather_30min_df = hourly_dataframe.resample('30T').interpolate(method='linear')
    weather_30min_df = weather_30min_df.bfill()  

    weather_lags_df = pd.DataFrame(index=weather_30min_df.index)

    for col in ['temp', 'wind', 'precip', 'cloud_cover', 'irradiance']:
        base_col = f"{col}_actual"
        weather_lags_df[base_col] = weather_30min_df[base_col]
        weather_lags_df[f"{col}_t-1"] = weather_30min_df[base_col].shift(1)
        weather_lags_df[f"{col}_t-2"] = weather_30min_df[base_col].shift(2)
        weather_lags_df[f"{col}_t-48"] = weather_30min_df[base_col].shift(48)
        weather_lags_df[f"{col}_t-336"] = weather_30min_df[base_col].shift(336)
        weather_lags_df[f"{col}_avg_last_3_hours"] = weather_30min_df[base_col].shift(1).rolling(window=6).mean()
        weather_lags_df[f"{col}_avg_last_6_hours"] = weather_30min_df[base_col].shift(1).rolling(window=12).mean()

    return weather_lags_df.iloc[-1:].reset_index(drop=True)

def get_live_generation_mix_elexon():
    """
    Fetches the latest instantaneous generation mix (in MW) from the
    Elexon data portal and maps it to the model's feature names.
    """
    base_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
    now_utc = datetime.now(timezone.utc)
    twelve_hours_ago_utc = now_utc - timedelta(hours=12)

    params = {
        'publishDateTimeFrom': twelve_hours_ago_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'publishDateTimeTo': now_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'format': 'json'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])

        if not data:
            print("No generation data found in the window.")
            return None

        latest_publish_time = max(item['publishTime'] for item in data)
        latest_records = [item for item in data if item['publishTime'] == latest_publish_time]

        raw_mix_mw = {}
        for item in latest_records:
            fuel_type = item.get('fuelType', 'unknown').upper()
            current_mw = item.get('generation')
            raw_mix_mw[fuel_type] = current_mw

        # Define your model's columns (SOLAR is removed)
        model_columns = ['WIND', 'GAS', 'NUCLEAR', 'COAL', 'HYDRO',
                         'IMPORTS', 'BIOMASS', 'STORAGE']

        mapped_mix = {col: 0.0 for col in model_columns}

        mapped_mix['WIND'] = raw_mix_mw.get('WIND', 0.0)
        mapped_mix['NUCLEAR'] = raw_mix_mw.get('NUCLEAR', 0.0)
        mapped_mix['COAL'] = raw_mix_mw.get('COAL', 0.0)
        mapped_mix['BIOMASS'] = raw_mix_mw.get('BIOMASS', 0.0)
        mapped_mix['GAS'] = raw_mix_mw.get('GAS', 0.0) + raw_mix_mw.get('OCGT', 0.0)
        mapped_mix['HYDRO'] = raw_mix_mw.get('NPSHYD', 0.0)
        mapped_mix['STORAGE'] = raw_mix_mw.get('PS', 0.0)

        interconnector_keys = ['INTELEC', 'INTEW', 'INTFR', 'INTGRNL', 'INTIFA2',
                               'INTIRL', 'INTNED', 'INTNEM', 'INTNSL', 'INTVKL']
        total_imports = 0.0
        for key in interconnector_keys:
            total_imports += raw_mix_mw.get(key, 0.0)
        mapped_mix['IMPORTS'] = total_imports

        df_live_gen = pd.DataFrame([mapped_mix], columns=model_columns)
        return df_live_gen

    except requests.RequestException as e:
        print(f"Error fetching Elexon generation data: {e}")
        return None

def get_live_weather_forecast():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 53.74, "longitude": -1.06,
        "hourly": "temperature_2m,wind_speed_100m,direct_normal_irradiance_instant",
        "forecast_days": 2, "timezone": "auto"
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temp_forecast"] = hourly.Variables(0).ValuesAsNumpy()
    hourly_data["wind_forecast"] = hourly.Variables(1).ValuesAsNumpy()
    hourly_data["dni_forecast"] = hourly.Variables(2).ValuesAsNumpy()

    df_forecast = pd.DataFrame(data=hourly_data).set_index('date')
    df_30min_forecast = df_forecast.resample('30T').interpolate(method='linear')
    live_forecast_vertical = df_30min_forecast.iloc[:48]  # Get exactly 48 steps

    temp_flat = live_forecast_vertical['temp_forecast'].values
    wind_flat = live_forecast_vertical['wind_forecast'].values
    dni_flat = live_forecast_vertical['dni_forecast'].values

    temp_cols = [f'temp_t+{i + 1}' for i in range(48)]
    wind_cols = [f'wind_t+{i + 1}' for i in range(48)]
    irradiance_cols = [f'irradiance_t+{i + 1}' for i in range(48)]

    live_forecast_data = {
        **dict(zip(temp_cols, temp_flat)),
        **dict(zip(wind_cols, wind_flat)),
        **dict(zip(irradiance_cols, dni_flat)),
    }

    return pd.DataFrame([live_forecast_data])

def build_live_inference_row():
    """
    Runs all API calls and stitches data together into the final
    1-row DataFrame for the model.
    """

    latest_co2_lags = get_intensity_lags()
    latest_weather_lags = get_weather_lags()

    live_gen_mix = get_live_generation_mix_elexon()

    live_forecast_pivoted = get_live_weather_forecast()

    if (latest_co2_lags is None or latest_weather_lags is None or
            live_gen_mix is None or live_forecast_pivoted is None):
        print("A critical API call failed. Aborting inference.")
        return None

    inference_row = pd.concat([
        latest_co2_lags,
        latest_weather_lags,
        live_gen_mix,
        live_forecast_pivoted
    ], axis=1)

    all_feature_cols = [
        'temp_actual', 'wind_actual', 'precip_actual', 'cloud_cover_actual', 'irradiance_actual',
        'temp_t-1', 'temp_t-2', 'temp_t-48', 'temp_t-336', 'temp_avg_last_3_hours', 'temp_avg_last_6_hours',
        'wind_t-1', 'wind_t-2', 'wind_t-48', 'wind_t-336', 'wind_avg_last_3_hours', 'wind_avg_last_6_hours',
        'precip_t-1', 'precip_t-2', 'precip_t-48', 'precip_t-336', 'precip_avg_last_3_hours', 'precip_avg_last_6_hours',
        'cloud_cover_t-1', 'cloud_cover_t-2', 'cloud_cover_t-48', 'cloud_cover_t-336', 'cloud_cover_avg_last_3_hours',
        'cloud_cover_avg_last_6_hours',
        'irradiance_t-1', 'irradiance_t-2', 'irradiance_t-48', 'irradiance_t-336', 'irradiance_avg_last_3_hours',
        'irradiance_avg_last_6_hours',
        'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_weekend',
        'intensity_t-1', 'intensity_t-48', 'intensity_t-336', 'avg_intensity_last_3_hours',
        'avg_intensity_last_6_hours',
        'temp_t+1', 'wind_t+1', 'irradiance_t+1', 'temp_t+2', 'wind_t+2', 'irradiance_t+2', 'temp_t+3', 'wind_t+3',
        'irradiance_t+3',
        'temp_t+4', 'wind_t+4', 'irradiance_t+4', 'temp_t+5', 'wind_t+5', 'irradiance_t+5', 'temp_t+6', 'wind_t+6',
        'irradiance_t+6',
        'temp_t+7', 'wind_t+7', 'irradiance_t+7', 'temp_t+8', 'wind_t+8', 'irradiance_t+8', 'temp_t+9', 'wind_t+9',
        'irradiance_t+9',
        'temp_t+10', 'wind_t+10', 'irradiance_t+10', 'temp_t+11', 'wind_t+11', 'irradiance_t+11', 'temp_t+12',
        'wind_t+12', 'irradiance_t+12',
        'temp_t+13', 'wind_t+13', 'irradiance_t+13', 'temp_t+14', 'wind_t+14', 'irradiance_t+14', 'temp_t+15',
        'wind_t+15', 'irradiance_t+15',
        'temp_t+16', 'wind_t+16', 'irradiance_t+16', 'temp_t+17', 'wind_t+17', 'irradiance_t+17', 'temp_t+18',
        'wind_t+18', 'irradiance_t+18',
        'temp_t+19', 'wind_t+19', 'irradiance_t+19', 'temp_t+20', 'wind_t+20', 'irradiance_t+20', 'temp_t+21',
        'wind_t+21', 'irradiance_t+21',
        'temp_t+22', 'wind_t+22', 'irradiance_t+22', 'temp_t+23', 'wind_t+23', 'irradiance_t+23', 'temp_t+24',
        'wind_t+24', 'irradiance_t+24',
        'temp_t+25', 'wind_t+25', 'irradiance_t+25', 'temp_t+26', 'wind_t+26', 'irradiance_t+26', 'temp_t+27',
        'wind_t+27', 'irradiance_t+27',
        'temp_t+28', 'wind_t+28', 'irradiance_t+28', 'temp_t+29', 'wind_t+29', 'irradiance_t+29', 'temp_t+30',
        'wind_t+30', 'irradiance_t+30',
        'temp_t+31', 'wind_t+31', 'irradiance_t+31', 'temp_t+32', 'wind_t+32', 'irradiance_t+32', 'temp_t+33',
        'wind_t+33', 'irradiance_t+33',
        'temp_t+34', 'wind_t+34', 'irradiance_t+34', 'temp_t+35', 'wind_t+35', 'irradiance_t+35', 'temp_t+36',
        'wind_t+36', 'irradiance_t+36',
        'temp_t+37', 'wind_t+37', 'irradiance_t+37', 'temp_t+38', 'wind_t+38', 'irradiance_t+38', 'temp_t+39',
        'wind_t+39', 'irradiance_t+39',
        'temp_t+40', 'wind_t+40', 'irradiance_t+40', 'temp_t+41', 'wind_t+41', 'irradiance_t+41', 'temp_t+42',
        'wind_t+42', 'irradiance_t+42',
        'temp_t+43', 'wind_t+43', 'irradiance_t+43', 'temp_t+44', 'wind_t+44', 'irradiance_t+44', 'temp_t+45',
        'wind_t+45', 'irradiance_t+45',
        'temp_t+46', 'wind_t+46', 'irradiance_t+46', 'temp_t+47', 'wind_t+47', 'irradiance_t+47', 'temp_t+48',
        'wind_t+48', 'irradiance_t+48',
        'WIND', 'GAS', 'NUCLEAR', 'COAL', 'HYDRO', 'IMPORTS', 'BIOMASS', 'STORAGE'
    ]

    final_inference_row = inference_row[all_feature_cols]

    return final_inference_row


class Command(BaseCommand):
    help = 'Fetch real time data, run inference with trained model, and save predictions to DB.'

    def handle(self, *args, **options):
        self.stdout.write("Starting new forecast run...")
        
        model_path = os.path.join(settings.BASE_DIR, 'models', 'CarbonIntensityPredictor.joblib')
        
        try:
            model = joblib.load(model_path)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR("Model file not found!"))
            return

        self.stdout.write("Model loaded successfully.")


        X_live = build_live_inference_row()
        if X_live is None:
            self.stderr.write(self.style.ERROR("Failed to build live inference row. Aborting."))
            return


        y_pred = model.predict(X_live)

        prediction_values = y_pred[0] 

        now = datetime.now(timezone.utc)
        next_half_hour = now.replace(second=0, microsecond=0)
        if now.minute < 30:
            next_half_hour = next_half_hour.replace(minute=30)
        else:
            next_half_hour = next_half_hour.replace(minute=0) + timedelta(hours=1)
            
        forecast_timestamps = pd.date_range(start=next_half_hour, periods=48, freq='30T')

        CarbonPredictions.objects.all().delete()
        self.stdout.write("Old predictions cleared.")

        predictions_to_create = []
        for i in range(48):
            predictions_to_create.append(
                CarbonPredictions(
                    timestamp=forecast_timestamps[i],
                    # This line will now work
                    carbon_intensity=prediction_values[i] 
                )
            )
        

        CarbonPredictions.objects.bulk_create(predictions_to_create)

        
        self.stdout.write(self.style.SUCCESS("Successfully saved new forecast."))