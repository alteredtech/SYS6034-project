#!/usr/bin/env python3

import simpy
import random
import uuid

# Constants
# Workday start and end times
WORKDAY_START = 7
WORKDAY_END = 21
# Battery capacity in kWh
BATTERY_CAPACITY = 135
# Total distance on a full charge in miles
FULL_CHARGE_DISTANCE = 150
# Efficiency in kWh used per mile
EFFICIENCY = BATTERY_CAPACITY / FULL_CHARGE_DISTANCE
# Target charge percentage
TARGET_CHARGE = 0.75
# Threshold charge percentage for charging
THRESHOLD_CHARGE = 0.80
# Simulation days
SIM_DAYS = 1
# Total number of EVs present in the fleet
EVS = 10
# Rate of charging in kW per hour
CHARGER_RATE = {
    "level1": 10, # Level 1 charger
    "level2": 25, # Level 2 charger
    "level3": 50  # Level 3 charger
}
# Delivery types with distance ranges in miles
DELIVERY_TYPES = {
    "short": {
        "distance_min": 0,
        "distance_max": 25,
        "lambda": 0.004295926,
        "mu": 0.007172583
    },
    "medium": {
        "distance_min": 25,
        "distance_max": 50,
        "lambda": 0.005029587,
        "mu": 0.007148450
    },
    "long": {
        "distance_min": 50,
        "distance_max": 75,
        "lambda": 0.004772020,
        "mu": 0.007432628
    }
}

# Class for electric vehicles
class EV:
    def __init__(self):
        # the battery capacity in kWh
        self.battery_capacity = BATTERY_CAPACITY
        # the unique ID for the EV
        self.id = uuid.uuid4()
        # the miles assigned to drive that day
        self.miles = 0
        # the delivery type assigned to the EV for the day
        self.delivery_type = None

# Class for charging stations
class Charger:
    def __init__(self, rate):
        # unique ID for the charger
        self.id = uuid.uuid4()
        # the level of the charger (level1, level2, level3)
        self.rate = rate
        # the number of evs that are in the queue for this charger
        self.queue: list[EV] = []

# Data Model for storing charging information
@dataclass
class ChargingData:
    # the unique ID for the EV
    ev_id: uuid.UUID
    # the current time in the simulation
    current_time: int
    # the time the EV started charging
    start_charge_time: int
    # the time the EV finished charging
    end_charge_time: int
    # the amount of charge added in kWh
    charge_added: float
    # the charging station used
    charger_id: uuid.UUID
    # the delivery type of the EV
    delivery_type: str
    # the distance driven by the EV
    distance_driven: float
    # was the EV able to charge to the target charge?
    charged_to_target: bool
    # the final battery percentage of the EV
    final_battery_pct: float
    # the charger level used
    charger_level: str
    # the time spent waiting in the queue
    wait_time: int
    # the time spent charging
    charge_time: int
    # time left


# Steps for modeling the simulation:
# 1. Create a SimPy environment
# 2. Create a list of chargers
# - Model as a shared queue (simpy.Resource) or individual queues (list of Resources)
# - charger types (L1, L2, L3) with different service rates (mu)

# 3. Create a list of EVs
# - Assign unique ID to each EV
# - Track EV state: 'Driving', 'WaitingToCharge', 'Charging', 'Parked', 'Done'

# 4. Assign delivery types to EVs
# - Delivery types: Short, Medium, Long
# - Sample mileage based on type
# - Add randomness to delivery time (normal or gamma noise)

# 5. Simulate the M/M/1 lifecycle of each EV

## 5.1. EVs leave the warehouse following a Poisson process (Exponential interarrival times)
# - Use something like random.expovariate(lambda) for departure timing

## 5.2. Each EV gets a delivery distance and an estimated return time
# - Return time = departure time + delivery duration

## 5.3. EV returns to the warehouse
# - Wait until return time before proceeding

## 5.4. Upon return, check battery %:
# - If battery >= 80%, park until the next workday
# - If battery < 80%, go to charger:
#     - Select charger with shortest queue or shared queue
#     - Record queue entry time

## 5.5. Charging behavior:
# - Charging time follows Exponential(mu) to simulate M/M/1
# - EV charges until target battery % (75%)
# - Track charger usage time
# - Monitor utilization (busy time vs total available time)

## 5.6. If end of workday occurs while in queue:
# - Leave the queue and go to parked state
# - Resume next day if needed (optional)

# 6. Log charging data for each EV:
# - EV ID
# - Delivery type and mileage
# - Departure and return times
# - Battery % on return
# - Queue wait time
# - Charging duration
# - Final battery %
# - Reached target? (Yes/No)
# - Number of days taken to charge (if multi-day charging is enabled)

# 7. Repeat steps 4–6 until the simulation ends
# - Simulate multiple workdays (7am–9pm)
# - Use simpy.Events to simulate active/inactive charger periods

# 8. Create a summary of results:
## 8.1. Interarrival times (compare to expected Poisson rate)
## 8.2. Total charging time per EV
## 8.3. Total queue wait time per EV
## 8.4. Charger utilization (busy time / workday duration)
## 8.5. Count of EVs that didn’t reach target charge
## 8.6. Count of EVs that parked without needing to charge
## 8.7. Max queue length during each day
## 8.8. Time spent in each EV state (Driving, WaitingToCharge, etc.)
## 8.9. Daily energy consumption (optional)
## 8.10. Peak charging demand periods (by hour or time window)


# From the documentation:
# env = simpy.Environment()
# bcs = simpy.Resource(env, capacity=2)

# def car(env, name, bcs, driving_time, charge_duration):
#     # Simulate driving to the BCS
#     yield env.timeout(driving_time)

#     # Request one of its charging spots
#     print('%s arriving at %d' % (name, env.now))
#     with bcs.request() as req:
#         yield req

#         # Charge the battery
#         print('%s starting to charge at %s' % (name, env.now))
#         yield env.timeout(charge_duration)
#         print('%s leaving the bcs at %s' % (name, env.now))

# for i in range(4):
#     env.process(car(env, 'Car %d' % i, bcs, i*2, 5))