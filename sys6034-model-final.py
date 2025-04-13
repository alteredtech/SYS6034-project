import simpy
import uuid
import random
import time
import json  # Import JSON module for file writing

# Total EVs
EVS = 1

# Simulation time
SIM_DAYS = 365 # Total simulation days
SIM_TIME = SIM_DAYS * 24 * 60  # Total simulation time in minutes

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

def log_ev_event(ev_id, time, event, extra=None):
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
    
    def charging_time(self):
        return random.expovariate(self.service_rate * 60) # Convert to minutes

class Delivery:
    def __init__(self, miles_min, miles_max, lambda_val):
        self.miles_max = miles_max
        self.miles_min = miles_min
        self.lambda_val = lambda_val
        self.miles = 0
    
    def get_miles(self):
        self.miles = random.randint(self.miles_min, self.miles_max)
        return self.miles

class EV:

    def __init__(self, env, uuid: uuid, chargers, charger_type: ChargerAttributes):
        self.env = env
        self.uuid = uuid
        self.chargers = chargers
        self.charger_type = charger_type
        self.action = env.process(self.run())
        # self.delivery_type = Delivery(5, 75, 0.09638554)

    def run(self):
        while True:
            # check if it is within working hours
            # if self.is_working_hours(): # if it is within working hours
                # Print the current simulation day
            current_day = int(self.env.now / (24 * 60)) + 1
            if current_day == 1:
                yield self.env.timeout(WORKDAY_START) # wait until the first workday starts

            if VERBOSE: print(f"{self.uuid}: Current simulation day: {current_day}")
            log_ev_event(self.uuid, self.env.now, "current simulation day", {"day": current_day})
            # get miles
            # miles = self.delivery_type.value.get_miles()
            # arrive at charger in poisson distribution
            return_delay = self.get_delivery_time(minimum=360, maximum=600) # minimum 6 hour shift and maximum 10 hours
            if VERBOSE: print(f"{self.uuid}: Delivery time in {return_delay:.2f} minutes")
            log_ev_event(self.uuid, self.env.now, "Delivery", {"return_delay": return_delay})
            yield self.env.timeout(return_delay)

            # queue at charger if below threshold
            with self.chargers.request() as req:
                queue_len = len(self.chargers.queue)
                if VERBOSE: print(f"{self.uuid}: Requesting charger | Queue: {queue_len}")
                log_ev_event(self.uuid, self.env.now, "requesting charger", {"queue_length": queue_len})
                yield req

                if VERBOSE: print(f"{self.uuid}: Starts charging")
                log_ev_event(self.uuid, self.env.now, "starts charging")
                charging_time = random.expovariate(self.charger_type.charging_time())
                yield self.env.timeout(charging_time)

                if VERBOSE: print(f"{self.uuid}: Finished charging")
                log_ev_event(self.uuid, self.env.now, "finished charging")
            
            # I think what is happening is that EVs are waiting in the queue 
            # for the charger when a new day starts to it is skipping days
            yield from self.wait_until_next_day()

            # from the docs
            # env.process waits for the process to finish before continuing
            # env.timeout Events of this type occur (are processed) after a certain amount of (simulated) time has passed. 
            # They allow a process to sleep (or hold its state) for the given time.
            
           

    def is_working_hours(self):
        current_hour = (self.env.now / 60) % 24 # convert minutes to hours, mod 24 hours and get current hour
        return WORKDAY_START <= current_hour < WORKDAY_END
    
    def wait_until_next_day(self):
        """Wait until the next workday starts."""
        current_minute = self.env.now % 1440  # Convert simulation time to hours
        if VERBOSE: print(f"{self.uuid}: Current simulation time: {self.env.now} minutes, Current minute: {current_minute:.2f} hours")
        if current_minute < WORKDAY_START:
            # If it's before the workday starts, wait until WORKDAY_START
            wait = WORKDAY_START - current_minute
        else:
            # If it's after the workday ends, wait until the next WORKDAY_START
            wait = (1440 - current_minute) + WORKDAY_START
        if VERBOSE: print(f"{self.uuid}: Waiting until next day for {wait:.2f} minutes.")
        log_ev_event(self.uuid, self.env.now, "waiting until next day", {"wait_minute": wait})
        yield self.env.timeout(wait)

    def get_delivery_time(self, minimum=360, maximum=600):
        """
        Get the time it takes to deliver the package.
        Just to make sure the delivery or a persons shift time is not less than 6 hours.
        """
        # Simulate delivery time
        while True:
            delivery_time = random.expovariate(LAMBDA_ARRIVAL / 60) * 60
            if minimum <= delivery_time <= maximum:
                return delivery_time
    

def run_simulation(sim_id, charger_type: ChargerAttributes, ev_count, sim_time, verbose=False):
    global ev_logs
    ev_logs = []  # Reset logs for each simulation

    random.seed(2511 + sim_id)  # Ensure different seeds for different simulations
    env = simpy.Environment()

    # Create chargers
    chargers = simpy.Resource(env, capacity=charger_type.capacity())
    if verbose: print(f"[Sim {sim_id}] Created chargers with type: {charger_type}")

    # Create EVs
    for _ in range(ev_count):
        ev_uuid = uuid.uuid4()
        if verbose: print(f"[Sim {sim_id}] Creating EV with UUID: {ev_uuid}")
        EV(env, ev_uuid, chargers, charger_type)

    # Run the simulation
    env.run(until=sim_time)
    if verbose: print(f"[Sim {sim_id}] Simulation completed.")
    if verbose: print(f"[Sim {sim_id}] Simulation ended at time: {env.now}")

    # Dump logs to a JSON file
    start_time = time.time()
    
    output_file = f"simulation_{sim_id}_logs.json"
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
        # {"sim_id": 2, "charger_type": ChargerAttributes(L2,1), "ev_count": EVS, "sim_time": SIM_TIME},
        # {"sim_id": 3, "charger_type": ChargerAttributes(L3,1), "ev_count": EVS, "sim_time": SIM_TIME},
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