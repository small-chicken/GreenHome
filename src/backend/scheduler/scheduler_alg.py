import json
from datetime import datetime, timedelta

def _datetime_to_slot_index(dt: datetime, forecast_start: datetime) -> int:
    # Converts an absolute datetime into a relative 30-minute slot index based on the forecast's start time.

    # Calculate the time difference in minutes
    delta = dt - forecast_start
    total_minutes = delta.total_seconds() / 60

    # Check if the time is on a 30-minute boundary
    if total_minutes % 30 != 0:
        raise ValueError(f"Time {dt} is not on a 30-minute boundary relative to start {forecast_start}.")

    # Calculate the slot index
    slot_index = int(total_minutes // 30)
    
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
    # Converts a runtime into 30 minute slots (unchanged).
    if minutes <= 0 or minutes % 30 != 0:
        raise ValueError("Runtime must be a positive multiple of 30 minutes.")
    return minutes // 30

def scheduler(appliances: list[dict], carbon_forecast: list[float], forecast_start_time: datetime) -> dict:
    # Schedules appliances over a 48-hour (96-slot) window.
    #
    # Takes in:
    #   appliances: List of appliance dicts. Times MUST be ISO format strings.
    #     - 'name': str
    #     - 'runtime_min': int (multiple of 30)
    #     - 'earliest_start': str 
    #     - 'latest_end': str 
    #   carbon_forecast: A list of 96 float values for the 48-hour period.
    #   forecast_start_time: The absolute datetime corresponding to carbon_forecast[0].
    #
    # Returns:
    #   A dictionary mapping appliance names to their optimal start time
    #   as an ISO 8601 string. Returns 'None' for unfeasible jobs.

    if len(carbon_forecast) != 96:
        raise ValueError(f"Carbon forecast must contain exactly 96 values (for 48 hours). Got {len(carbon_forecast)}.")

    optimal_schedule = {}

    for appliance in appliances:
        appliance_name = appliance['name']
        
        try:
            # Convert ISO string times to datetime objects
            earliest_start_dt = datetime.fromisoformat(appliance['earliest_start'])
            latest_end_dt = datetime.fromisoformat(appliance['latest_end'])

            # Convert datetimes to slot indices relative to the forecast start
            earliest_start_slot = _datetime_to_slot_index(earliest_start_dt, forecast_start_time)
            latest_end_slot_index = _datetime_to_slot_index(latest_end_dt, forecast_start_time)
            
            # Get runtime in slots
            runtime_slots = _minutes_to_slots(appliance['runtime_min'])

            # Calculate the latest possible start slot
            latest_start_slot = latest_end_slot_index - runtime_slots

            # Check if job is possible
            if latest_start_slot < earliest_start_slot:
                print(f"Warning: Appliance '{appliance_name}' is impossible to schedule. "
                      f"Needs {appliance['runtime_min']} mins but window is too short.")
                optimal_schedule[appliance_name] = None
                continue
                
            # Ensure the latest possible run is within the forecast data
            if latest_start_slot + runtime_slots > len(carbon_forecast):
                 print(f"Warning: Appliance '{appliance_name}' cannot be scheduled. "
                       f"Latest end time {latest_end_dt} is beyond the 48h forecast window.")
                 optimal_schedule[appliance_name] = None
                 continue

            # Find the best start slot using a sliding window
            best_start_slot = -1
            min_total_cost = float('inf')

            # Calculate cost of initial window
            current_window_cost = 0.0
            for i in range(runtime_slots):
                slot_index = earliest_start_slot + i
                current_window_cost += carbon_forecast[slot_index]
            
            min_total_cost = current_window_cost
            best_start_slot = earliest_start_slot

            # Slide the window one slot at a time
            for start_slot in range(earliest_start_slot + 1, latest_start_slot + 1):
                cost_to_drop = carbon_forecast[start_slot - 1]
                
                new_slot_index = start_slot + runtime_slots - 1
                cost_to_add = carbon_forecast[new_slot_index]

                current_window_cost = current_window_cost - cost_to_drop + cost_to_add

                if current_window_cost < min_total_cost:
                    min_total_cost = current_window_cost
                    best_start_slot = start_slot

            # Convert best slot back to a full datetime object
            best_start_time_dt = _slot_index_to_datetime(best_start_slot, forecast_start_time)
            
            # Return as an ISO string
            optimal_schedule[appliance_name] = best_start_time_dt.isoformat()

        except Exception as e:
            print(f"Error processing appliance '{appliance_name}': {e}")
            optimal_schedule[appliance_name] = None

    return optimal_schedule

"""
### ----------------- ###
###  NEW TEST DATA    ###
### ----------------- ###

# 1. Define the absolute start time for our 48-hour forecast

FORECAST_START = datetime(2025, 11, 1, 0, 0) # Day 1, 00:00

# Helper function to create ISO strings from the start time
def T(days=0, hours=0, minutes=0):
    dt = FORECAST_START + timedelta(days=days, hours=hours, minutes=minutes)
    return dt.isoformat()

# 2. Update appliance list (removed "power_kW")
my_appliances = [
    {
        "name": "Washing Machine",
        "runtime_min": 120,       # 2 hours (4 slots)
        "earliest_start": T(hours=9), # Day 1, 09:00
        "latest_end": T(hours=17)     # Day 1, 17:00
    },
    {
        "name": "Dishwasher",
        "runtime_min": 90,         # 1.5 hours (3 slots)
        "earliest_start": T(hours=18), # Day 1, 18:00
        "latest_end": T(hours=23)      # Day 1, 23:00
    },
    {
        "name": "EV Charger",
        "runtime_min": 240,        # 4 hours (8 slots)
        "earliest_start": T(hours=0),  # Day 1, 00:00
        "latest_end": T(hours=6)       # Day 1, 06:00
    },
    {
        "name": "Impossible Job",
        "runtime_min": 60,         # 1 hour (2 slots)
        "earliest_start": T(hours=10), # Day 1, 10:00
        "latest_end": T(hours=10, minutes=30) # Day 1, 10:30 (Impossible)
    },
    {
        "name": "Cross-Day Job",
        "runtime_min": 180,        # 3 hours (6 slots)
        "earliest_start": T(days=0, hours=22), # Day 1, 22:00
        "latest_end": T(days=1, hours=8)       # Day 2, 08:00
    }
]

# 3. Define your 48-hour (96-slot) carbon forecast
peak_cost = 100
mid_cost = 50
low_cost = 20

day_pattern = (
    [low_cost] * 12 +       # 00:00 - 05:45 (Overnight low)
    [peak_cost] * 6 +      # 06:00 - 08:45 (Morning peak)
    [mid_cost] * 8 +       # 09:00 - 12:45 (Daytime)
    [low_cost] * 8 +       # 13:00 - 16:45 (Solar peak / Midday low)
    [peak_cost] * 10 +      # 17:00 - 21:45 (Evening peak)
    [mid_cost] * 4          # 22:00 - 23:45 (Dropping off)
)

carbon_forecast_data = day_pattern * 2

print(f"Carbon forecast has {len(carbon_forecast_data)} slots.")

# 4. Run the scheduler
schedule = scheduler(my_appliances, carbon_forecast_data, FORECAST_START)

# 5. Print the results
print("\n--- Optimal Schedule (48 Hours) ---")
print(json.dumps(schedule, indent=2))
"""