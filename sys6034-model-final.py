#!/usr/bin/env python3

import simpy
import random
import uuid
from dataclasses import dataclass
from enum import Enum

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
# Total number of chargers present in the fleet
L1_CHARGERS = 7
L2_CHARGERS = 0
L3_CHARGERS = 0
# Rate of charging in kW per hour
class ChargerRate(Enum):
    LEVEL1 = 10 # Level 1 charger
    LEVEL2 = 25 # Level 2 charger
    LEVEL3 = 50 # Level 3 charger
# Delivery types with distance ranges in miles
class DeliveryType(Enum):
    SHORT = {
        "distance_min": 0, 
        "distance_max": 25,
        "lambda": 0.004295926,
        "mu": 0.007172583
        }
    MEDIUM = {
        "distance_min": 25, 
        "distance_max": 50,
        "lambda": 0.005029587,
        "mu": 0.007148450
        }
    LONG = {
        "distance_min": 50, 
        "distance_max": 75,
        "lambda": 0.004772020,
        "mu": 0.007432628
        }
    NONE = {
        "distance_min": 0, 
        "distance_max": 0,
        "lambda": 0.0,
        "mu": 0.0
        }
# Driving states
class DrivingState(Enum):
    DRIVING = "Driving"
    WAITING_TO_CHARGE = "WaitingToCharge"
    CHARGING = "Charging"
    PARKED = "Parked"

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
        self.delivery_type = DeliveryType.NONE
        # the current state of the EV
        self.state = DrivingState.PARKED
        # the current battery percentage of the EV
        self.battery_pct = 1.0

    def remove_battery_pct(self):
        # remove the battery percentage based on the miles driven
        self.battery_pct -= (self.miles * EFFICIENCY) / self.battery_capacity
        # if the battery percentage is less than 0, set it to 0
        if self.battery_pct < 0.0:
            self.battery_pct = 0.0

    def add_battery_pct(self, charge_added):
        # add the battery percentage based on the charge added
        self.battery_pct += (charge_added * 100) / self.battery_capacity
        # if the battery percentage is greater than 1, set it to 1
        if self.battery_pct > 1.0:
            self.battery_pct = 1.0

    def __repr__(self):
        return f"<EV {self.id} | {self.delivery_type.name} | Battery: {self.battery_pct:.2f} | State: {self.state.value}>"

# Class for charging stations
class Charger:
    def __init__(self, sim_env, rate):
        # unique ID for the charger
        self.id = uuid.uuid4()
        # the level of the charger (level1, level2, level3)
        self.rate = rate
        # the number of evs that are in the queue for this charger
        self.resource = simpy.Resource(sim_env, capacity=1)

# The warehouse class
class Warehouse:
    def __init__(self, env, short_deliveries, medium_deliveries, long_deliveries):
        # the number of short deliveries
        self.short_deliveries = short_deliveries
        # the number of medium deliveries
        self.medium_deliveries = medium_deliveries
        # the number of long deliveries
        self.long_deliveries = long_deliveries
        # the simpy environment
        self.env = env
        # the list of chargers
        self.chargers: list[Charger] = []
        # the list of evs
        self.evs: list[EV] = []
        # the current time in the simulation
        self.current_time = 0
    
    def assign_delivery_type(self, ev):
        # assign a delivery type to the ev
        available = []
        if self.short_deliveries > 0:
            available.append(DeliveryType.SHORT)
        if self.medium_deliveries > 0:
            available.append(DeliveryType.MEDIUM)
        if self.long_deliveries > 0:
            available.append(DeliveryType.LONG)

        if available:
            chosen = random.choice(available)
            ev.delivery_type = chosen
            if chosen == DeliveryType.SHORT:
                self.short_deliveries -= 1
            elif chosen == DeliveryType.MEDIUM:
                self.medium_deliveries -= 1
            else:
                self.long_deliveries -= 1
        else:
            ev.delivery_type = DeliveryType.NONE
    
    def set_miles(self, ev):
        if ev.delivery_type != DeliveryType.NONE:
            dist_range = ev.delivery_type.value
            ev.miles = random.uniform(dist_range["distance_min"], dist_range["distance_max"])
        else:
            print(f"[ERROR] No delivery type assigned to EV {ev.id}")
            print("All EVs in the warehouse:")
            for e in self.evs:
                print(f"EV ID: {e.id} | Delivery Type: {e.delivery_type}")
            exit()
    
    def unassign_delivery_type(self, ev):
        # unassign the delivery type from the ev
        if ev.delivery_type == DeliveryType.SHORT:
            ev.delivery_type = DeliveryType.NONE
            self.short_deliveries += 1
        elif ev.delivery_type == DeliveryType.MEDIUM:
            ev.delivery_type = DeliveryType.NONE
            self.medium_deliveries += 1
        elif ev.delivery_type == DeliveryType.LONG:
            ev.delivery_type = DeliveryType.NONE
            self.long_deliveries += 1
        else:
            print("No delivery type assigned to EV, please check you have the same number of deliveries as EVs")
            print("EV ID: ", ev.id)
            exit()

# Data Model for storing charging information
@dataclass
class ChargingData:
    # the unique ID for the EV
    ev_id: uuid.UUID
    # the current time in the simulation
    current_time: float
    # the time the EV started charging
    start_charge_time: float
    # the time the EV finished charging
    end_charge_time: float
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
    wait_time: float
    # the time spent charging
    charge_time: float
    # the EVs state
    state: DrivingState

def ev_process(env, ev: EV, warehouse: Warehouse, chargers: Charger, charging_logs: list[ChargingData]):
    # Step 1: Assign delivery and set miles
    warehouse.assign_delivery_type(ev)
    warehouse.set_miles(ev)

    # Step 2: Depart at Poisson-distributed interval
    departure_delay = random.expovariate(ev.delivery_type.value["lambda"])
    yield env.timeout(departure_delay)
    ev.state = DrivingState.DRIVING

    # Simulate delivery time (exponential service time)
    # TODO: fix this because mu probably is not the correct value
    delivery_time = random.expovariate(ev.delivery_type.value["mu"])
    yield env.timeout(delivery_time)

    # Step 3: Return to warehouse
    ev.remove_battery_pct()
    ev.state = DrivingState.WAITING_TO_CHARGE

    # Step 4: Decide if charging is needed
    if ev.battery_pct >= THRESHOLD_CHARGE:
        ev.state = DrivingState.PARKED
        return

    # Step 5: Choose charger with shortest queue
    available_chargers = sorted(chargers, key=lambda c: len(c.resource.queue))
    chosen_charger = available_chargers[0]

    queue_enter_time = env.now
    with chosen_charger.resource.request() as req:
        result = yield req | env.timeout(WORKDAY_END - env.now)

        if req not in result:
            # Left queue due to workday ending
            ev.state = DrivingState.PARKED
            return

        start_charge_time = env.now
        ev.state = DrivingState.CHARGING

        # Step 6: Charge until reaching 75% battery
        charge_needed_kwh = max(0, (TARGET_CHARGE - ev.battery_pct) * BATTERY_CAPACITY)
        charge_duration = charge_needed_kwh / chosen_charger.rate.value

        time_remaining = WORKDAY_END - env.now
        if charge_duration > time_remaining:
            # Not enough time to finish charging
            yield env.timeout(time_remaining)
            ev.add_battery_pct(chosen_charger.rate.value * time_remaining)
        else:
            yield env.timeout(charge_duration)
            ev.add_battery_pct(charge_needed_kwh)

        ev.state = DrivingState.PARKED
        end_charge_time = env.now

        # Step 7: Record data
        charging_logs.append(ChargingData(
            ev_id=ev.id,
            current_time=env.now,
            start_charge_time=start_charge_time,
            end_charge_time=end_charge_time,
            charge_added=charge_needed_kwh,
            charger_id=chosen_charger.id,
            delivery_type=ev.delivery_type.name,
            distance_driven=ev.miles,
            charged_to_target=(ev.battery_pct >= TARGET_CHARGE),
            final_battery_pct=ev.battery_pct * 100,
            charger_level=chosen_charger.rate.name,
            wait_time=start_charge_time - queue_enter_time,
            charge_time=end_charge_time - start_charge_time,
            state=ev.state
        ))

def main():
    DAYS = 180

    # Steps for modeling the simulation:
    # 1. Create a SimPy environment
    env = simpy.Environment()
    # 2. Create a list of chargers
    l1_chargers = [Charger(env, ChargerRate.LEVEL1) for _ in range(L1_CHARGERS)]
    l2_chargers = [Charger(env, ChargerRate.LEVEL2) for _ in range(L2_CHARGERS)]
    l3_chargers = [Charger(env, ChargerRate.LEVEL3) for _ in range(L3_CHARGERS)]
    # - Model as a shared queue (simpy.Resource) or individual queues (list of Resources)
    # - charger types (L1, L2, L3) with different service rates (mu)
    chargers = l1_chargers + l2_chargers + l3_chargers

    # 3. Create a list of EVs
    evs = [EV() for _ in range(EVS)]
    # - Assign unique ID to each EV
    # - Track EV state: 'Driving', 'WaitingToCharge', 'Charging', 'Parked', 'Done'

    # 4. Create a warehouse object
    warehouse = Warehouse(env, short_deliveries=5, medium_deliveries=3, long_deliveries=2)
    warehouse.evs = evs
    warehouse.chargers = chargers

    # Charging data collection
    charging_logs = []

    # Daily loop for each workday
    for day in range(DAYS):
        day_start = day * 24 + WORKDAY_START
        day_end = day * 24 + WORKDAY_END

        # Schedule EV processes each day
        env.process(ev_process(env, ev, warehouse, chargers, charging_logs))

        # Run SimPy from WORKDAY_START to WORKDAY_END for this day
        env.run(until=day_end)

    # Print summary
    print(f"Simulation completed for {DAYS} days.")
    print(f"Total charging logs: {len(charging_logs)}")
    for log in charging_logs:
        print(log)

if __name__ == "__main__":
    main()

# 4. Assign delivery types to EVs
# - Delivery types: Short(5), Medium(3), Long(2)
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
# def is_within_workday(env):
#     # Check if the current time is within the workday
#     if WORKDAY_START <= env.now < WORKDAY_END:
#         return True
#     else:
#         return False
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
# - Number of days taken to charge

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