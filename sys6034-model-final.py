import simpy
import uuid
import random
import time
import os
import json  # Import JSON module for file writing

# Total EVs
EVS = 30

# Simulation time
SIM_DAYS = 54 # Total simulation days
SIM_TIME = SIM_DAYS * 24 * 60  # Total simulation time in minutes

# Use seed for random number generation
USE_SEED = False

# Working hours
WORKDAY_START = 420    # 7 AM
WORKDAY_END = 1260     # 9 PM

# Get print outputs
VERBOSE = True

# Rates
# Service rate for each charger type, mean duration in hours (derived from the kaggle dataset)
L1 = 2.119910 
L2 = 2.283534
L3 = 2.393660
# Arrival rate
LAMBDA_ARRIVAL = 10.375 # Average arrival rate of EVs per hour (derived from the kaggle dataset)

# Global list to store EV logs
ev_logs = []

def log_ev_event(ev_id, time, current_day, event, extra=None):
    """
    Log an EV event.
    
    :param ev_id: The unique ID of the EV.
    :param time: The current simulation time.
    :param current_day: The current 'real' simulation day.
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
        """
        Initialize the ChargerAttributes class.

        :param service_rate: The average service rate (charging rate) of the charger.
        :param servers: The number of chargers available (capacity).
        """
        self.service_rate = service_rate  # Average service rate of the charger
        self.servers = servers  # Number of chargers available

    def rate(self):
        """
        Get the service rate of the charger.

        :return: The service rate.
        """
        return self.service_rate

    def capacity(self):
        """
        Get the capacity (number of chargers).

        :return: The number of chargers.
        """
        return self.servers

    def charging_time(self, min_charge_time=30, max_charge_time=1440):
        """
        Calculate the charging time for an EV based on the service rate.

        :param min_charge_time: Minimum charging time in minutes.
        :param max_charge_time: Maximum charging time in minutes.
        :return: The charging time in minutes.
        """
        while True:
            # Generate a random charging time using an exponential distribution
            charge_time = random.expovariate(1 / self.service_rate)
            # Convert the charging time to minutes
            charge_time = charge_time * 60
            # Ensure the charging time is within the specified range
            if min_charge_time <= charge_time <= max_charge_time:
                return charge_time

def ev(env, uuid: uuid, chargers, charger_type: ChargerAttributes):
    """
    Simulate the behavior of an EV in the system.

    :param env: SimPy environment.
    :param uuid: Unique identifier for the EV.
    :param chargers: SimPy resource representing the chargers.
    :param charger_type: ChargerAttributes object specifying charger properties.
    """
    current_day = 0  # Initialize the current simulation day
    while current_day < SIM_DAYS:  # Loop through each simulation day

        if current_day == 0:
            # On the first day, wait until the workday starts
            yield env.timeout(WORKDAY_START)

        if VERBOSE: print(f"{uuid}: Current simulation day: {current_day}")
        # Log the start of a new simulation day
        log_ev_event(uuid, env.now, current_day, "starting new simulation day")

        # Simulate the time taken for delivery (minimum 6 hours, maximum 10 hours)
        return_delay = get_delivery_time(minimum=360, maximum=600)
        if VERBOSE: print(f"{uuid}: Delivery time in {return_delay:.2f} minutes")
        # Log the delivery event
        log_ev_event(uuid, env.now, current_day, "Delivery", {"return_delay": return_delay})
        yield env.timeout(return_delay)  # Wait for the delivery time to elapse

        # Request access to a charger
        with chargers.request() as req:
            queue_len = len(chargers.queue)  # Get the current queue length
            if VERBOSE: print(f"{uuid}: Requesting charger | Queue: {queue_len}")
            # Log the charger request event
            log_ev_event(uuid, env.now, current_day, "requesting charger", {"queue_length": queue_len})
            yield req  # Wait until the charger becomes available

            if VERBOSE: print(f"{uuid}: Starts charging")
            # Log the start of the charging event
            log_ev_event(uuid, env.now, current_day, "starts charging")
            
            # Determine the charging time based on the charger type
            charging_time = charger_type.charging_time(min_charge_time=30, max_charge_time=1440)
            # Log the charging event with the calculated charging time
            log_ev_event(uuid, env.now, current_day, "charging", {"charging_time": charging_time})

            if VERBOSE: print(f"{uuid}: Charging for {charging_time:.2f} minutes")
            yield env.timeout(charging_time)  # Wait for the charging time to elapse

            if VERBOSE: print(f"{uuid}: Finished charging")
            # Log the completion of the charging event
            log_ev_event(uuid, env.now, current_day, "finished charging")
        
        # Wait until the next workday starts
        yield from wait_until_next_day(env, uuid, current_day)
        current_day += 1  # Increment the simulation day

def wait_until_next_day(env, uuid, current_day):
    """Wait until the next workday starts."""
    # Calculate the current minute of the day based on the simulation time
    current_minute = env.now % 1440  
    if VERBOSE: 
        # Print the current simulation time and minute for debugging
        print(f"{uuid}: Current simulation time: {env.now} minutes, Current minute: {current_minute:.2f}")
    
    if current_minute < WORKDAY_START:
        # If the current time is before the workday starts, calculate the wait time until WORKDAY_START
        wait = WORKDAY_START - current_minute
    else:
        # If the current time is after the workday ends, calculate the wait time until the next WORKDAY_START
        wait = (1440 - current_minute) + WORKDAY_START
    
    if VERBOSE: 
        # Print the calculated wait time for debugging
        print(f"{uuid}: Waiting until next day for {wait:.2f} minutes.")
    
    # Log the event of waiting until the next day with the calculated wait time
    log_ev_event(uuid, env.now, current_day, "waiting until next day", {"wait_minute": wait})
    
    # Pause the simulation for the calculated wait time
    yield env.timeout(wait)

def get_delivery_time(minimum=360, maximum=600):
    """
    Get the time it takes to deliver the package.
    By default, it is set to 6 hours (360 minutes) to 10 hours (600 minutes).
    Just to make sure the delivery or a persons shift time is not less than 6 hours or longer than 10 hours.
    """
    # Simulate delivery time
    while True:
        delivery_time = random.expovariate(1 / LAMBDA_ARRIVAL)
        # Convert to minutes
        delivery_time = delivery_time * 60
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

def run_simulation(sim_id, sim_runs, charger_type: ChargerAttributes, ev_count, sim_time, verbose=False):
    for i in range(sim_runs):
        if verbose: print(f"[Sim {sim_id}] Starting simulation run {i + 1}/{sim_runs}")
        
        # Reset the global EV logs for each simulation run
        global ev_logs
        ev_logs = []

        # Set a random seed for reproducibility if enabled
        if USE_SEED:
            random.seed(2511 + sim_id)  # Ensure different seeds for different simulations
        
        # Create a new SimPy environment for the simulation
        env = simpy.Environment()

        # Create a resource for chargers with the specified capacity
        chargers = simpy.Resource(env, capacity=charger_type.capacity())
        if verbose: print(f"[Sim {sim_id}] Created chargers with type: {charger_type}")

        # Create EV processes and add them to the simulation environment
        for _ in range(ev_count):
            ev_uuid = uuid.uuid4()  # Generate a unique identifier for each EV
            if verbose: print(f"[Sim {sim_id}] Creating EV with UUID: {ev_uuid}")
            env.process(ev(env, ev_uuid, chargers, charger_type))  # Add EV process to the environment

        # Run the simulation until the specified simulation time
        env.run(until=None)
        if verbose: print(f"[Sim {sim_id}] Simulation completed.")
        if verbose: print(f"[Sim {sim_id}] Simulation ended at time: {env.now}")

        # Save the simulation logs to a JSON file
        start_time = time.time()  # Record the start time for log saving
        
        # Define the output file path for the logs
        output_file = f"logs/simulation_{sim_id}_run_{i+1}_mu_{charger_type.service_rate}_cap_{charger_type.servers}_logs.json"
        os.makedirs("logs", exist_ok=True)  # Ensure the logs directory exists
        with open(output_file, "w") as f:
            json.dump(ev_logs, f)  # Write the logs to the JSON file
        
        end_time = time.time()  # Record the end time for log saving
        real_world_duration = end_time - start_time  # Calculate the duration of the log saving process
        
        # Print verbose output for log saving and simulation duration
        if verbose: 
            print(f"[Sim {sim_id}] Logs saved to {output_file}")
            print(f"[Sim {sim_id}] Real-world simulation duration: {real_world_duration:.2f} seconds")

def main():
    # Define simulation parameters
    simulations = [
        {"sim_id": 1, "sim_runs": 20, "charger_type": ChargerAttributes(L1,1), "ev_count": EVS, "sim_time": SIM_TIME},
        {"sim_id": 2, "sim_runs": 20, "charger_type": ChargerAttributes(L2,1), "ev_count": EVS, "sim_time": SIM_TIME},
        {"sim_id": 3, "sim_runs": 20, "charger_type": ChargerAttributes(L3,1), "ev_count": EVS, "sim_time": SIM_TIME},
    ]

    # Run simulations
    for sim in simulations:
        run_simulation(
            sim_id=sim["sim_id"],
            sim_runs=sim["sim_runs"],
            charger_type=sim["charger_type"],
            ev_count=sim["ev_count"],
            sim_time=sim["sim_time"],
            verbose=VERBOSE
        )

if __name__ == '__main__':
    main()