#!/usr/bin/env python3

import simpy
import numpy as np
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
TARGET_CHARGE = 75
# Threshold charge percentage for charging
THRESHOLD_CHARGE = 80
# Simulation days
SIM_DAYS = 1
# Total number of EVs present in the fleet
EVS = 10
# Rate of charging in kW per hour
CHARGER_RATE = {
    "level1": 10, 
    "level2": 25, 
    "level3": 50
}
# Delivery types with distance ranges in miles
DELIVERY_TYPES = {
    "short": (0, 25),
    "medium": (25, 50),
    "long": (50, 75)
}

class EV:
    ev_id = None
    miles = 0
    delivery_type = ""

    def __init__(self):
        self.battery_capacity = BATTERY_CAPACITY
        self.ev_id = uuid.uuid4()

# Class for charging stations
# Class for storing charging information


ev_1 = EV()
print(ev_1.battery_capacity)