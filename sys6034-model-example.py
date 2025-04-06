import simpy
import numpy as np
import random

# Constants
WORKDAY_START = 7
WORKDAY_END = 21
BATTERY_CAPACITY = 100
EFFICIENCY = 0.2  # % used per mile
TARGET_CHARGE = 75
THRESHOLD_CHARGE = 80
SIM_DAYS = 1
EVS_PER_DAY = 10  # Total number of EVs generated each day
CHARGER_RATE = {"slow": 10, "medium": 25, "fast": 50}  # kW per hour

# Delivery types
DELIVERY_TYPES = {
    "short": (0, 25),
    "medium": (25, 50),
    "long": (50, 75)
}

class EV:
    def __init__(self, ev_id, delivery_type, miles, battery_pct):
        self.id = ev_id
        self.delivery_type = delivery_type
        self.miles = miles
        self.battery_pct = battery_pct
        self.final_battery_pct = battery_pct
        self.charged = False

class Charger:
    def __init__(self, env, level, rate, num_chargers):
        self.env = env
        self.level = level
        self.rate = rate
        self.resource = simpy.Resource(env, num_chargers)
        self.queue = []

    def queue_length(self):
        return len(self.resource.queue) + self.resource.count

    def charge(self, ev: EV):
        needed_pct = TARGET_CHARGE - ev.battery_pct
        charge_time = (needed_pct * BATTERY_CAPACITY / 100) / self.rate  # hours
        charge_until = self.env.now + charge_time

        # If charging crosses end of workday, stop early
        hour = self.env.now % 24
        if hour + charge_time > WORKDAY_END:
            time_left = WORKDAY_END - hour
            ev.final_battery_pct = ev.battery_pct + (self.rate * time_left / BATTERY_CAPACITY * 100)
            yield self.env.timeout(time_left)
        else:
            ev.final_battery_pct = TARGET_CHARGE
            yield self.env.timeout(charge_time)

def ev_lifecycle(env, ev: EV, chargers: list, log: list):
    # Workday check
    hour = env.now % 24
    if hour < WORKDAY_START or hour >= WORKDAY_END:
        yield env.timeout(WORKDAY_START - hour if hour < WORKDAY_START else 24 - hour + WORKDAY_START)

    # Battery drop after delivery
    ev.battery_pct -= ev.miles * EFFICIENCY
    ev.battery_pct = max(0, ev.battery_pct)

    if ev.battery_pct >= THRESHOLD_CHARGE:
        # Go to holding
        print(f"{env.now:.2f}: EV-{ev.id} goes to holding (Battery: {ev.battery_pct:.1f}%)")
    else:
        # Select charger with shortest queue
        best_charger = min(chargers, key=lambda c: c.queue_length())
        print(f"{env.now:.2f}: EV-{ev.id} queues at {best_charger.level} charger (Battery: {ev.battery_pct:.1f}%)")
        with best_charger.resource.request() as req:
            yield req
            yield env.process(best_charger.charge(ev))
            print(f"{env.now:.2f}: EV-{ev.id} done charging at {best_charger.level} (Battery: {ev.final_battery_pct:.1f}%)")

    log.append((ev.id, ev.delivery_type, ev.miles, ev.battery_pct, ev.final_battery_pct))

def ev_generator(env, chargers, log):
    ev_id = 0
    while True:
        for _ in range(EVS_PER_DAY):
            ev_id += 1
            dtype = random.choice(list(DELIVERY_TYPES.keys()))
            miles = np.random.uniform(*DELIVERY_TYPES[dtype])
            ev = EV(ev_id, dtype, miles, 100.0)
            env.process(ev_lifecycle(env, ev, chargers, log))
        yield env.timeout(24)  # Next day

# Run simulation
env = simpy.Environment()
chargers = [
    Charger(env, "slow", CHARGER_RATE["slow"], 1),
    Charger(env, "medium", CHARGER_RATE["medium"], 1),
    Charger(env, "fast", CHARGER_RATE["fast"], 1)
]

log = []
env.process(ev_generator(env, chargers, log))
env.run(until=SIM_DAYS * 24)

# Print summary
print("\nEV Summary:")
for entry in log:
    print(f"EV-{entry[0]} | {entry[1]} | {entry[2]:.1f} mi | Start: {entry[3]:.1f}% | End: {entry[4]:.1f}%")
