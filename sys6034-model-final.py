import simpy
import uuid
from enum import Enum
import random

# Total EVs
EVS = 21

# Battery capacity in kWh
BATTERY_CAPACITY = 135
EV_FULL_CHARGE_DISTANCE = 150  # Total distance on a full charge in miles
# Efficiency in kWh per mile
EFFICIENCY = BATTERY_CAPACITY / EV_FULL_CHARGE_DISTANCE

# Simulation time
SIM_DAYS = 5 # Total simulation days
SIM_TIME = SIM_DAYS * 24 * 60  # Total simulation time in minutes

# Working hours
WORKDAY_START = 7    # 7 AM
WORKDAY_END = 21     # 9 PM

# Get print outputs
VERBOSE = True

class ChargerAttributes:
    def __init__(self, service_rate, amount, servers):
        self.service_rate = service_rate
        self.amount = amount
        self.servers = servers

    def capacity(self):
        return self.amount * self.servers

class ChargerType(Enum):
    L1 = ChargerAttributes(service_rate=10, amount=0, servers=0)
    L2 = ChargerAttributes(service_rate=25, amount=0, servers=0)
    L3 = ChargerAttributes(service_rate=50, amount=1, servers=1)

    @property
    def rate(self):
        return self.value.service_rate

    @property
    def amount(self):
        return self.value.amount

    @property
    def capacity(self):
        return self.value.capacity()

class Delivery:
    def __init__(self, miles_min, miles_max, lambda_val):
        self.miles_max = miles_max
        self.miles_min = miles_min
        self.lambda_val = lambda_val
        self.miles = 0
    
    def get_miles(self):
        self.miles = random.randint(self.miles_min, self.miles_max)
        return self.miles
        

class DeliveryType(Enum):
    SHORT = Delivery(miles_min=0, miles_max=25, lambda_val=0.004295926)
    MEDIUM = Delivery(miles_min=25, miles_max=50, lambda_val=0.005029587)
    LONG = Delivery(miles_min=50, miles_max=75, lambda_val=0.004772020)
    NONE = Delivery(miles_min=0, miles_max=0, lambda_val=0)

# Maximum allowed delivery types
MAX_DELIVERY_TYPES = {
    DeliveryType.SHORT: 5,
    DeliveryType.MEDIUM: 3,
    DeliveryType.LONG: 2
}

# Available delivery types (shared across all EVs)
available_delivery_types = {
    DeliveryType.SHORT: MAX_DELIVERY_TYPES[DeliveryType.SHORT],
    DeliveryType.MEDIUM: MAX_DELIVERY_TYPES[DeliveryType.MEDIUM],
    DeliveryType.LONG: MAX_DELIVERY_TYPES[DeliveryType.LONG]
}

class EV:

    def __init__(self, env, uuid: uuid, chargers):
        self.env = env
        self.uuid = uuid
        self.chargers = chargers
        self.current_charge = BATTERY_CAPACITY
        self.max_charge = BATTERY_CAPACITY
        self.action = env.process(self.run())
        self.delivery_type = DeliveryType.NONE

    def run(self):
        while True:
            # check if it is within working hours
            if self.is_working_hours(): # if it is within working hours
                # Assign a delivery type
                self.delivery_type = self.assign_delivery_type()
                if self.delivery_type == DeliveryType.NONE:
                    if VERBOSE: print(f"{self.uuid}: No delivery types available. Waiting for reset.")
                    # TODO: Log
                    yield from self.wait_until_next_day()
                    continue
                yield self.env.timeout(random.randint(1,10)) # wait for 1 minute
                # get miles
                miles = self.delivery_type.value.get_miles()
                # remove charge from battery
                energy_used = miles * EFFICIENCY
                self.current_charge -= energy_used
                # arrive at charger in poisson distribution
                self.return_delivery_type()
                # queue at charger if below threshold
                # charge at charger until some percentage of battery, service rate
                # leave charger
                # wait until next day
            else:
                yield self.env.timeout(1) # wait for 1 minute
           

    def is_working_hours(self):
        current_hour = (self.env.now / 60) % 24 # convert minutes to hours, mod 24 hours and get current hour
        return WORKDAY_START <= current_hour < WORKDAY_END
    
    def wait_until_next_day(self):
        """Wait until the next workday starts."""
        current_hour = (self.env.now / 60) % 24
        wait = (24 - current_hour) + WORKDAY_START
        if VERBOSE: print(f"{self.uuid}: Waiting until next day at {wait} hours.")
        yield self.env.timeout(wait * 60)
    
    def assign_delivery_type(self):
        """Assign a delivery type based on availability."""
        for delivery_type, count in available_delivery_types.items():
            if count > 0:
                available_delivery_types[delivery_type] -= 1
                # TODO: Log
                if VERBOSE: print(f"{self.uuid}: Assigned {delivery_type.name} delivery type. Remaining: {available_delivery_types[delivery_type]}")
                return delivery_type
        return DeliveryType.NONE
    
    def return_delivery_type(self):
        """Return the delivery type to the pool."""
        if self.delivery_type != DeliveryType.NONE:
            available_delivery_types[self.delivery_type] += 1
            if VERBOSE: print(f"{self.uuid}: Returned {self.delivery_type.name} delivery type to the pool. Remaining: {available_delivery_types[self.delivery_type]}")
            # TODO: Log
            self.delivery_type = DeliveryType.NONE


def main():
    random.seed(2511)
    env = simpy.Environment()

    # Create chargers with a capacity of 1 for each level
    chargers = {}
    if ChargerType.L1.amount > 0:
        chargers[ChargerType.L1] = simpy.Resource(env, capacity=ChargerType.L1.capacity)
    if ChargerType.L2.amount > 0:
        chargers[ChargerType.L2] = simpy.Resource(env, capacity=ChargerType.L2.capacity)
    if ChargerType.L3.amount > 0:
        chargers[ChargerType.L3] = simpy.Resource(env, capacity=ChargerType.L3.capacity)

    # Create EVs
    for _ in range(EVS):
        ev_uuid = uuid.uuid4()
        if VERBOSE: print(f"Creating EV with UUID: {ev_uuid}")
        EV(env, ev_uuid, chargers)

    # Run the simulation
    env.run(until=SIM_TIME)

if __name__ == '__main__':
    main()