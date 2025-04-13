# import simpy
# import random
# import json
# from datetime import datetime

# class Car(object):
#     def __init__(self, env, name, fast_bcs, slow_bcs, driving_time, charge_duration_fast, charge_duration_slow):
#         self.env = env
#         self.name = name
#         self.fast_bcs = fast_bcs
#         self.slow_bcs = slow_bcs
#         self.driving_time = driving_time
#         self.charge_duration_fast = charge_duration_fast
#         self.charge_duration_slow = charge_duration_slow
#         self.current_charge = 100  # Initial charge level in percentage
#         self.log = []  # List to store log entries
#         self.action = env.process(self.run())

#     def log_event(self, state, start_time=None, end_time=None):
#         """Log an event in JSON format."""
#         event = {
#             "timestamp": datetime.now().isoformat(),
#             "ev_name": self.name,
#             "charge_level": self.current_charge,
#             "state": state,
#             "start_charge_time": start_time,
#             "end_charge_time": end_time,
#             "simulation_time": self.env.now
#         }
#         self.log.append(event)
#         print(json.dumps(event, indent=4))  # Print the log entry for debugging

#     def run(self):
#         while True:
#             # Simulate driving to the BCS
#             self.log_event("driving")
#             yield self.env.timeout(self.driving_time)

#             # Decide whether to use a fast or slow charger
#             if random.choice(['fast', 'slow']) == 'fast':
#                 self.log_event("queueing", start_time=self.env.now)
#                 with self.fast_bcs.request() as req:
#                     yield req
#                     start_time = self.env.now
#                     self.log_event("charging", start_time=start_time)
#                     try:
#                         yield self.env.timeout(self.charge_duration_fast)
#                     except simpy.Interrupt:
#                         self.log_event("interrupted", start_time=start_time, end_time=self.env.now)
#                     end_time = self.env.now
#                     self.log_event("charging_complete", start_time=start_time, end_time=end_time)
#             else:
#                 self.log_event("queueing", start_time=self.env.now)
#                 with self.slow_bcs.request() as req:
#                     yield req
#                     start_time = self.env.now
#                     self.log_event("charging", start_time=start_time)
#                     try:
#                         yield self.env.timeout(self.charge_duration_slow)
#                     except simpy.Interrupt:
#                         self.log_event("interrupted", start_time=start_time, end_time=self.env.now)
#                     end_time = self.env.now
#                     self.log_event("charging_complete", start_time=start_time, end_time=end_time)

#             # Simulate driving after charging
#             trip_duration = 2
#             self.log_event("driving")
#             yield self.env.timeout(trip_duration)

# def driver(env, car):
#     yield env.timeout(5)
#     car.action.interrupt()

# # Simulation setup
# env = simpy.Environment()
# fast_bcs = simpy.Resource(env, capacity=1)  # Fast charging station with 1 spot
# slow_bcs = simpy.Resource(env, capacity=2)  # Slow charging station with 2 spots

# # Create multiple cars
# cars = []
# for i in range(10):  # Adjust the number of cars as needed
#     driving_time = random.expovariate(1.0 / 5)  # Poisson arrival rate with mean 5
#     charge_duration_fast = random.randint(2, 5)  # Random fast charge duration between 2 and 5
#     charge_duration_slow = random.randint(5, 10)  # Random slow charge duration between 5 and 10
#     car = Car(env, 'Car %d' % i, fast_bcs, slow_bcs, driving_time, charge_duration_fast, charge_duration_slow)
#     cars.append(car)

# env.run(until=50)  # Run the simulation for 50 time units

# # Save logs to a JSON file
# with open("ev_logs.json", "w") as log_file:
#     all_logs = [car.log for car in cars]
#     json.dump(all_logs, log_file, indent=4)

import simpy
import random

NUM_EVS = 10
SIM_TIME = 24000  # minutes
MU = 0.4423093 / 60  # service rate per minute

def ev_process(env, name, charger):
    # One trip per EV in this simple case
    # You can loop this if EVs do multiple trips

    # EV finishes delivery and returns
    delivery_time = random.uniform(30, 90)  # simulate delivery trip time
    yield env.timeout(delivery_time)
    print(f"[{env.now:.2f}] {name} returns to charge after delivery")

    # EV requests charger
    with charger.request() as req:
        queue_len = len(charger.queue)
        print(f"[{env.now:.2f}] {name} requests charger | Queue: {queue_len}")
        yield req
        print(f"[{env.now:.2f}] {name} starts charging")
        charging_time = random.expovariate(MU)
        yield env.timeout(charging_time)
        print(f"[{env.now:.2f}] {name} finishes charging")

# Set up environment
env = simpy.Environment()
charger = simpy.Resource(env, capacity=1)  # Single M/M/1 charger

# Launch all EVs into simulation
for i in range(1, NUM_EVS + 1):
    ev_name = f"EV-{i}"
    env.process(ev_process(env, ev_name, charger))

env.run(until=SIM_TIME)

