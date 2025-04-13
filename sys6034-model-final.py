import simpy
import uuid
import random
import time
import os
import json  # Import JSON module for file writing

# Total EVs
EVS = 11

# Simulation time
SIM_DAYS = 365 # Total simulation days
SIM_TIME = SIM_DAYS * 24 * 60  # Total simulation time in minutes

# Use seed for random number generation
USE_SEED = True

# Working hours
WORKDAY_START = 420    # 7 AM
WORKDAY_END = 1260     # 9 PM

# Get print outputs
VERBOSE = True

# Rates
# Service rate for each charger type, mean duration in hours
L1 = 2.119910 
L2 = 2.283534
L3 = 2.393660
# Arrival rate
LAMBDA_ARRIVAL = 10.375 # Average arrival rate of EVs per hour

# Global list to store EV logs
ev_logs = []

def log_ev_event(ev_id, time, current_day, event, extra=None):
    """
    Log an EV event.
    
    :param ev_id: The unique ID of the EV.
    :param time: The current simulation time.
    :param event: The event type (e.g., "requesting charger", "charging", "finished charging").
    :param extra: Any additional information to log.
    """
    ev_logs.append({
        "ev_id": str(ev_id),  # Convert UUID to string for JSON serialization
        "time": time,
        "day": current_day,
        "sim_day": day(time),
        "sim_hour": hour(time),
        "sim_minute": minute(time),
        "event": event,
        "extra": extra
    })

class ChargerAttributes:
    def __init__(self, service_rate, servers):
        self.service_rate = service_rate
        self.servers = servers
    
    def rate(self):
        return self.service_rate
    
    def capacity(self):
        return self.servers
    
    def charging_time(self, min_charge_time=30, max_charge_time=1440):
        while True:
            charge_time = random.expovariate((1 / self.service_rate)) * 60
            if min_charge_time <= charge_time <= max_charge_time:
                return charge_time

class Delivery:
    def __init__(self, miles_min, miles_max, lambda_val):
        self.miles_max = miles_max
        self.miles_min = miles_min
        self.lambda_val = lambda_val
        self.miles = 0
    
    def get_miles(self):
        self.miles = random.randint(self.miles_min, self.miles_max)
        return self.miles

def ev(env, uuid: uuid, chargers, charger_type: ChargerAttributes):
    current_day = 1
    while current_day < SIM_DAYS:

        if current_day == 1:
            yield env.timeout(WORKDAY_START) # wait until the first workday starts

        if VERBOSE: print(f"{uuid}: Current simulation day: {current_day}")
        log_ev_event(uuid, env.now, current_day, "starting new simulation day")

        return_delay = get_delivery_time(minimum=360, maximum=600) # minimum 6 hour shift and maximum 10 hours
        if VERBOSE: print(f"{uuid}: Delivery time in {return_delay:.2f} minutes")
        log_ev_event(uuid, env.now, current_day, "Delivery", {"return_delay": return_delay})
        yield env.timeout(return_delay)

        # queue at charger if below threshold
        with chargers.request() as req:
            queue_len = len(chargers.queue)
            if VERBOSE: print(f"{uuid}: Requesting charger | Queue: {queue_len}")
            log_ev_event(uuid, env.now, current_day, "requesting charger", {"queue_length": queue_len})
            yield req

            if VERBOSE: print(f"{uuid}: Starts charging")
            log_ev_event(uuid, env.now, current_day, "starts charging")
            charging_time = charger_type.charging_time(min_charge_time=30, max_charge_time=1440)
            log_ev_event(uuid, env.now, current_day, "charging", {"charging_time": charging_time})
            yield env.timeout(charging_time)

            if VERBOSE: print(f"{uuid}: Finished charging")
            log_ev_event(uuid, env.now, current_day, "finished charging")
        
        yield from wait_until_next_day(env, uuid, current_day)  # Wait until the next workday starts
        current_day += 1

def wait_until_next_day(env, uuid, current_day):
    """Wait until the next workday starts."""
    current_minute = env.now % 1440  # Get the current minute of the day
    if VERBOSE: print(f"{uuid}: Current simulation time: {env.now} minutes, Current minute: {current_minute:.2f}")
    if current_minute < WORKDAY_START:
        # If it's before the workday starts, wait until WORKDAY_START
        wait = WORKDAY_START - current_minute
    else:
        # If it's after the workday ends, wait until the next WORKDAY_START
        wait = (1440 - current_minute) + WORKDAY_START
    if VERBOSE: print(f"{uuid}: Waiting until next day for {wait:.2f} minutes.")
    log_ev_event(uuid, env.now, current_day, "waiting until next day", {"wait_minute": wait})
    yield env.timeout(wait)

def get_delivery_time(minimum=360, maximum=600):
    """
    Get the time it takes to deliver the package.
    By default, it is set to 6 hours (360 minutes) to 10 hours (600 minutes).
    Just to make sure the delivery or a persons shift time is not less than 6 hours or longer than 10 hours.
    """
    # Simulate delivery time
    while True:
        delivery_time = random.expovariate((1 / LAMBDA_ARRIVAL) / 60) * 60
        if minimum <= delivery_time <= maximum:
            return delivery_time

def hour(sim_time):
    current_hour = int((sim_time / 60) % 24)  # Convert simulation time to hours
    return current_hour

def minute(sim_time):
    current_minute = (sim_time % 60)  # Get the current minute of the day
    return current_minute

def day(sim_time):
    current_day = int(sim_time / 1440) + 1  # Convert simulation time to days
    return current_day

def run_simulation(sim_id, charger_type: ChargerAttributes, ev_count, sim_time, verbose=False):
    global ev_logs
    ev_logs = []  # Reset logs for each simulation

    if USE_SEED:
        random.seed(2511 + sim_id)  # Ensure different seeds for different simulations
    env = simpy.Environment()

    # Create chargers
    chargers = simpy.Resource(env, capacity=charger_type.capacity())
    if verbose: print(f"[Sim {sim_id}] Created chargers with type: {charger_type}")

    # Create EVs
    for _ in range(ev_count):
        ev_uuid = uuid.uuid4()
        if verbose: print(f"[Sim {sim_id}] Creating EV with UUID: {ev_uuid}")
        env.process(ev(env, ev_uuid, chargers, charger_type))

    # Run the simulation
    env.run(until=None)
    if verbose: print(f"[Sim {sim_id}] Simulation completed.")
    if verbose: print(f"[Sim {sim_id}] Simulation ended at time: {env.now}")

    # Dump logs to a JSON file
    start_time = time.time()
    
    output_file = f"logs/simulation_{sim_id}_mu_{charger_type.service_rate}_cap_{charger_type.servers}_logs.json"
    os.makedirs("logs", exist_ok=True)  # Ensure the logs directory exists
    with open(output_file, "w") as f:
        json.dump(ev_logs, f)
    
    end_time = time.time()
    real_world_duration = end_time - start_time
    
    if verbose: 
        print(f"[Sim {sim_id}] Logs saved to {output_file}")
        print(f"[Sim {sim_id}] Real-world simulation duration: {real_world_duration:.2f} seconds")

def main():
    # Define simulation parameters
    simulations = [
        {"sim_id": 1, "charger_type": ChargerAttributes(L1,1), "ev_count": EVS, "sim_time": SIM_TIME},
        {"sim_id": 2, "charger_type": ChargerAttributes(L2,1), "ev_count": EVS, "sim_time": SIM_TIME},
        {"sim_id": 3, "charger_type": ChargerAttributes(L3,1), "ev_count": EVS, "sim_time": SIM_TIME},
    ]

    # Run simulations
    for sim in simulations:
        run_simulation(
            sim_id=sim["sim_id"],
            charger_type=sim["charger_type"],
            ev_count=sim["ev_count"],
            sim_time=sim["sim_time"],
            verbose=VERBOSE
        )

if __name__ == '__main__':
    main()