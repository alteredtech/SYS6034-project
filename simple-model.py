import simpy
import random
from enum import Enum

RANDOM_SEED = 42
CHARGING_DURATION = 5  # Time it takes to charge an EV
SIM_TIME = 1000  # Simulation time in minutes

class ChargerAttributes:
    def __init__(self, rate, amount, servers):
        self.rate = rate
        self.amount = amount
        self.servers = servers

    def capacity(self):
        return self.amount * self.servers

class ChargerType(Enum):
    L1 = ChargerAttributes(rate=10, amount=0, servers=0)
    L2 = ChargerAttributes(rate=25, amount=0, servers=0)
    L3 = ChargerAttributes(rate=50, amount=1, servers=1)

    @property
    def rate(self):
        return self.value.rate

    @property
    def amount(self):
        return self.value.amount

    @property
    def capacity(self):
        return self.value.capacity()

EVS = 11  # Number of electric vehicles

BATTERY_CAPACITY = 135  # Battery capacity in kWh
FULL_CHARGE_DISTANCE = 150  # Total distance on a full charge in miles
EFFICIENCY = BATTERY_CAPACITY / FULL_CHARGE_DISTANCE  # Efficiency in kWh per mile
TARGET_CHARGE = 0.75  # Target charge percentage
THRESHOLD_CHARGE = 0.80  # Threshold charge percentage for charging

class ChargerLevel(Enum):
    L1 = 10  # Level 1 charger rate in kW
    L2 = 25  # Level 2 charger rate in kW
    L3 = 50  # Level 3 charger rate in kW

class EV:
    delivery_type_counts = {'short': 0, 'medium': 0, 'long': 0}  # Track assigned delivery types
    max_delivery_types = {'short': 5, 'medium': 3, 'long': 2}  # Max allowed per type in 24 hours

    def __init__(self, env, name, chargers):
        self.env = env
        self.name = name
        self.chargers = chargers
        self.current_charge = BATTERY_CAPACITY  # Initial charge level in kWh (full charge)
        self.max_charge = BATTERY_CAPACITY  # Maximum charge level in kWh
        self.delivery_type = self.assign_delivery_type()  # Assign initial delivery type
        self.action = env.process(self.run())

    @classmethod
    def reset_delivery_type_counts(cls):
        """Reset delivery type counts at the start of a new 24-hour period."""
        cls.delivery_type_counts = {'short': 0, 'medium': 0, 'long': 0}
        print("Delivery type counts have been reset.")

    def assign_delivery_type(self):
        """Assign a delivery type based on availability and probabilities."""
        available_types = [
            t for t, count in self.delivery_type_counts.items()
            if count < self.max_delivery_types[t]
        ]
        if not available_types:
            print(f"{self.name}: No delivery types available for assignment. Waiting for reset.")
            return None  # No delivery type assigned

        delivery_type = random.choices(
            available_types,
            weights=[0.5 if t == 'short' else 0.3 if t == 'medium' else 0.2 for t in available_types],
            k=1
        )[0]
        self.delivery_type_counts[delivery_type] += 1
        return delivery_type

    def get_delivery_range(self):
        """Get the range of miles for the current delivery type."""
        if self.delivery_type == 'short':
            return random.randint(5, 25)
        elif self.delivery_type == 'medium':
            return random.randint(25, 50)
        elif self.delivery_type == 'long':
            return random.randint(50, 75)
        else:
            return 0  # No delivery type assigned

    def run(self):
        while True:
            # Simulate a delivery
            if self.delivery_type is not None:
                delivery_range = self.get_delivery_range()
                energy_used = delivery_range * EFFICIENCY  # Energy used in kWh
                self.current_charge = max(0, self.current_charge - energy_used)
                #print(f'{self.name} completed a {self.delivery_type} delivery of {delivery_range} miles. '
                      #f'Energy used: {energy_used:.2f} kWh. Current charge: {self.current_charge:.2f} kWh.')

            # Check if charging is needed
            if self.current_charge / self.max_charge < THRESHOLD_CHARGE:
                # Request to charge at a random charger
                charger_level: ChargerType = random.choice(list(self.chargers.keys()))
                with self.chargers[charger_level].request() as req:
                    yield req
                    target_energy = TARGET_CHARGE * self.max_charge
                    energy_needed = max(0, target_energy - self.current_charge)
                    charging_rate = charger_level.rate  # Charger rate in kW
                    charging_duration = energy_needed / charging_rate  # Duration in hours
                    charging_duration_minutes = charging_duration * 60  # Convert to minutes
                    #print(f'{self.name} starts charging at {self.env.now} using {charger_level.name}. '
                          #f'Charging duration: {charging_duration_minutes:.2f} minutes.')
                    yield self.env.timeout(charging_duration_minutes)
                    self.current_charge = min(self.max_charge, self.current_charge + energy_needed)
                    #print(f'{self.name} finishes charging at {self.env.now}. Current charge: {self.current_charge:.2f} kWh.')

            # Simulate time before the next delivery
            yield self.env.timeout(random.randint(5, 15))

            # Assign a new delivery type at the start of a new 24-hour period
            if int(self.env.now) % (24) == 0:  # Reset every 24 hours
                EV.reset_delivery_type_counts()
            self.delivery_type = self.assign_delivery_type()
            if self.delivery_type:
                print(f'{self.name} is assigned a new delivery type: {self.delivery_type}.')

def main():
    random.seed(RANDOM_SEED)
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
    for i in range(EVS):
        EV(env, f'EV{i+1}', chargers)

    # Run the simulation
    env.run(until=SIM_TIME)

if __name__ == '__main__':
    main()