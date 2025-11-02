# In your_app/scheduler_utils.py

import json
from datetime import datetime, timedelta
import numpy as np  # <-- Added this import

def _datetime_to_slot_index(dt: datetime, forecast_start: datetime) -> int:
    """
    Converts an absolute datetime into a relative 30-minute slot index.
    Rounds to the nearest slot to handle user input that isn't exact.
    """
    delta = dt - forecast_start
    total_minutes = delta.total_seconds() / 60

    # --- CHANGED: Round to nearest slot instead of raising an error ---
    slot_index = int(round(total_minutes / 30.0))
    
    if slot_index < 0:
         print(f"Warning: Time {dt} is before forecast start {forecast_start}. Clamping to slot 0.")
         return 0
         
    return slot_index

def _slot_index_to_datetime(slot_index: int, forecast_start: datetime) -> datetime:
    # Converts a 30-minute slot index back to an absolute datetime.
    if slot_index < 0:
        raise ValueError("Slot index cannot be negative.")
        
    minutes_from_start = slot_index * 30
    return forecast_start + timedelta(minutes=minutes_from_start)

def _minutes_to_slots(minutes: int) -> int:
    """
    Converts a runtime in minutes to the number of 30-minute slots.
    Rounds UP to the nearest slot.
    """
    if minutes <= 0:
        raise ValueError("Runtime must be a positive number of minutes.")
    
    # --- CHANGED: Round up to ensure the full runtime is met ---
    slots = int(np.ceil(minutes / 30.0))
    if slots == 0:
        slots = 1 # Minimum 1 slot
    return slots

def scheduler(appliances: list[dict], carbon_forecast: list[float], forecast_start_time: datetime) -> dict:
    """
    Schedules appliances over a forecast window.
    (This is your function, pasted directly)
    """

    # We get the total number of slots from the forecast itself
    total_slots = len(carbon_forecast)
    if total_slots == 0:
        raise ValueError("Carbon forecast is empty.")
        
    optimal_schedule = {}

    for appliance in appliances:
        appliance_name = appliance['name']
        
        try:
            earliest_start_dt = datetime.fromisoformat(appliance['earliest_start'])
            latest_end_dt = datetime.fromisoformat(appliance['latest_end'])

            earliest_start_slot = _datetime_to_slot_index(earliest_start_dt, forecast_start_time)
            latest_end_slot_index = _datetime_to_slot_index(latest_end_dt, forecast_start_time)
            runtime_slots = _minutes_to_slots(appliance['runtime_min'])
            
            latest_start_slot = latest_end_slot_index - runtime_slots

            if latest_start_slot < earliest_start_slot:
                print(f"Warning: Appliance '{appliance_name}' is impossible to schedule.")
                optimal_schedule[appliance_name] = None
                continue
            
            # Ensure the latest possible run is within the forecast data
            if latest_start_slot + runtime_slots > total_slots:
                 print(f"Warning: Appliance '{appliance_name}' cannot be scheduled. "
                       f"Latest end time {latest_end_dt} is beyond the forecast window.")
                 optimal_schedule[appliance_name] = None
                 continue

            best_start_slot = -1
            min_total_cost = float('inf')

            # Efficiently find the best slot
            current_window_cost = sum(carbon_forecast[earliest_start_slot : earliest_start_slot + runtime_slots])
            min_total_cost = current_window_cost
            best_start_slot = earliest_start_slot

            for start_slot in range(earliest_start_slot + 1, latest_start_slot + 1):
                cost_to_drop = carbon_forecast[start_slot - 1]
                new_slot_index = start_slot + runtime_slots - 1
                cost_to_add = carbon_forecast[new_slot_index]

                current_window_cost = current_window_cost - cost_to_drop + cost_to_add

                if current_window_cost < min_total_cost:
                    min_total_cost = current_window_cost
                    best_start_slot = start_slot

            best_start_time_dt = _slot_index_to_datetime(best_start_slot, forecast_start_time)
            optimal_schedule[appliance_name] = best_start_time_dt.isoformat()

        except Exception as e:
            print(f"Error processing appliance '{appliance_name}': {e}")
            optimal_schedule[appliance_name] = None

    return optimal_schedule