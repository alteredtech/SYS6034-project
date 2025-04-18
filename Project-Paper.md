---
title: EV Charging Fleet Strategies
author: 
- Michael Einreinhof
- Taichi Niu
---

# ELECTRIC VEHICLE CHARGING FLEET STRATEGY MODELS OF DIFFERENT DELIVERY STRATEGIES

# ABSTRACT
# INTRODUCTION

## Rise of EVs and Recharging Challenges
The global transition to electric vehicles (EVs) is reshaping transportation and energy systems, spurred by environmental goals and supported by policy, infrastructure, and battery advances. Yet, this shift introduces routing and charging challenges—EVs have limited range, slower refueling, and depend on an uneven charging infrastructure. These issues are especially acute for commercial fleets with tight delivery schedules, where charger availability and wait times directly impact operations.

## Problem Statement and Research Gap
Fleet routing for EVs must account for real-time State of Charge (SoC), delivery deadlines, and unpredictable charger access. Standard vehicle routing models fall short of capturing these dynamics, including queuing behavior and energy constraints. This research addresses that gap by integrating queueing theory and discrete-event simulation to study how recharging strategies influence charger demand and system performance.

## SoC-Aware Routing Models
Bac and Erdem (2021) introduced the EVRPTW-PR, incorporating partial charging, time windows, and heterogeneous fleets. Their model tracks SoC, recharge duration, and routing feasibility under real-world energy constraints. Jafari and Boyles (2017) approached the problem as a Markov Decision Process, optimizing single-EV decisions under stochastic, time-varying conditions. These works highlight the need for real-time SoC management and flexible charging decisions.

## Queueing Models at Chargers
Queueing models like M/M/1 and M/M/C are commonly used to simulate EV charging behavior. However, exponential service time assumptions often misrepresent real charging durations. Later models, such as Liu et al. (2021)'s M/D/C formulation, better capture real-world conditions by assuming deterministic charging times with stochastic arrivals, achieving improved accuracy in urban-scale simulations.

## Smart and Partial Charging
Uncontrolled charging risks grid instability and inefficiency. Smart charging, as categorized by Dahiwale et al. (2024), enables adaptive control using centralized or decentralized coordination. Reinforcement learning methods (e.g., Tuchnitz et al., 2021) have shown promise in reducing peak load and improving flexibility. Partial charging—emphasized by Bac and Erdem—offers operational benefits, reducing energy costs and improving schedule adherence.

## Algorithms for Charging-Aware Routing
Routing under SoC constraints has been approached through metaheuristics (e.g., VNS, ALNS), hybrid methods, and stochastic control. Bac and Erdem’s VNS/VND solution optimizes routes with partial recharge. Jafari and Boyles’ MDP-based routing adjusts to changing travel and queue conditions. Reinforcement learning models also show potential for routing integration, as shown by Tuchnitz et al. (2021).

## Discrete-Event Simulation with SimPy
SimPy is widely used for modeling EV operations due to its flexibility in handling asynchronous, time-driven events. Zhang and Varma (2024) developed a SimPy-based simulation to test ride-hailing EV strategies using real-world NYC data, demonstrating how EVs interact with chargers, trip requests, and dispatching under realistic conditions.

## Contribution of This Work
This study extends existing work by developing a SimPy-based simulation grounded in empirical data. Arrival and service rates are estimated using a cleaned Kaggle dataset in R, assuming Poisson arrivals and exponential charging durations. The simulation evaluates how different recharging strategies and charger configurations affect queue length, wait time, and system utilization. Post-simulation metrics are further analyzed using Erlang-C equations to support infrastructure planning.

# METHOD
## Data Preprocessing and Exploratory Analysis in RStudio
To support the design and parameterization of the simulation model, an initial dataset was obtained from Kaggle titled EV Charging Patterns. This dataset served as a proxy for electric vehicle (EV) charging behavior. All data processing and preliminary statistical analysis were conducted in RStudio (Version [your version]) using the tidyverse, fitdistrplus, and lubridate libraries.

Despite the dataset’s utility as a starting point, several inconsistencies necessitated extensive preprocessing to improve its reliability:

Temporal Corrections: All charging sessions originally reported start times rounded to the nearest hour, which is unlikely in real-world conditions. Additionally, the reported end times often did not align with the provided durations. Charging start times were recalculated by subtracting the charging duration from the end time.
State of Charge Corrections: Some entries indicated a decrease in the state of charge (SoC) during a session (i.e., end SoC lower than start SoC). These instances were corrected by inverting the values where appropriate. Charges exceeding 100% or beginning at or below 0% were excluded.
Charger Type Discrepancies: All charger levels (Level 1, Level 2, DC Fast) showed nearly identical average charging rates, contrary to real-world expectations. This raised concerns about the data's realism, prompting further evaluation of charging efficiency distributions.
To improve dataset focus and reduce noise from geographical variability, only records from Los Angeles were retained.

Feature Engineering

Several derived variables were computed to facilitate later simulation modeling:

Charging Efficiency: Measured in kilowatt-hours per hour (kWh/hr), computed as the energy delivered divided by charging time.
Arrival Times: Charging sessions were grouped by the hour of start time to estimate temporal patterns in user behavior.
Interarrival Times: Time between successive vehicle arrivals was calculated per user type to enable queueing model parameter estimation.
Categorical Encoding: User types and charger types were encoded as ordered factors to enable stratified analysis.
Verification, Validation, and Credibility Steps

This preprocessing stage supported three critical modeling assurances:

Verification: Code correctness and logical transformations were verified using summary statistics and visualizations (e.g., histograms, time series of arrivals).
Validation: The data’s structural alignment with real-world EV charging behavior was assessed through charging rate comparisons, temporal clustering, and interarrival pattern examination.
Credibility: The plausibility of derived parameters was evaluated by comparing charging efficiencies and usage patterns across charger levels. Density estimates and fitted distributions provided further support for model realism.
Estimation of Simulation Parameters

Key queueing parameters were extracted from the cleaned dataset:

Arrival Rate (λ): Mean number of charging events per hour was computed based on corrected start times.
Service Rate (μ): Mean charging durations were calculated and inverted to obtain service rates. Rates were computed both overall and stratified by charger type.
Utilization (ρ): System utilization was estimated as the ratio of λ to μ, providing a basis for evaluating congestion under M/M/1 queueing assumptions.
Interarrival times were further modeled using distribution fitting via the fitdistrplus package. Candidate distributions (exponential, lognormal, Weibull) were compared using AIC values, and best fits were visualized using faceted histograms and scaled density overlays.

## Discrete-Event Simulation in SimPy
To model the dynamics of EV fleet behavior at charging stations, a discrete-event simulation (DES) framework was implemented using the SimPy library in Python. The simulation captures EV arrival, queueing, and charging behavior under realistic time constraints, using parameter estimates derived from the preprocessed Kaggle dataset.

Simulation Overview

The model simulates a fixed fleet of 30 electric vehicles (EVs) over a period of 54 days, with each day comprising 24 hours. However, vehicles operate only during defined working hours: 7:00 AM to 9:00 PM (420 to 1260 minutes). Each EV alternates between delivery trips and charging, looping over consecutive workdays.

The primary components of the simulation include:

EV Process: Each EV performs a delivery (random duration between 6 to 10 hours), returns to request a charger, waits in queue if necessary, charges for a service-time drawn from an exponential distribution, and then waits until the next workday.
Charger Resource: Simulated as a simpy.Resource with limited capacity (e.g., 1 charger per simulation scenario), where contention for access is modeled explicitly.
Charger Attributes: Encapsulated in a dedicated class defining the average service rate (μ, in hours) and number of available chargers.
Event Logging: All EV behaviors are logged to structured JSON files, capturing event timestamps, simulation day/hour, queue lengths, and charging durations.
Model Parameters

Simulation parameters were drawn from the exploratory analysis performed in R:

Arrival Rate (λ): Set at 10.375 arrivals per hour, based on the hourly mean across all users.
Service Rates (μ): Estimated separately for each charger type using the inverse of the mean charging duration:
Level 1: 2.12 hours
Level 2: 2.28 hours
Level 3 (DC Fast): 2.39 hours
Simulation Time: 54 days × 24 hours × 60 minutes = 77,760 total simulation minutes.
Simulation Logic

Each EV executes a cyclical routine:

Delivery Period: Simulated via an exponential distribution truncated between 360 and 600 minutes (6–10 hours).
Charger Request: EVs return from delivery and attempt to acquire a charging resource. If the charger is unavailable, they wait in queue.
Charging Event: Charging duration is randomly drawn from an exponential distribution using the mean μ of the current charger type, constrained between 30 and 1440 minutes.
End-of-Day Transition: Once charging is complete, EVs wait until the next day’s work window resumes before initiating the next delivery.
Each simulation is executed for 20 independent runs per charger type, and log data is stored in the logs/ directory for later analysis. Verbose logging is optionally enabled to trace simulation state changes.

Temporal Handling

Helper functions (hour(), minute(), day()) are used to convert simulation time (in minutes) into human-readable format, which supports log consistency and later analysis. A wait_until_next_day() function ensures EVs do not initiate deliveries or charging outside of operational hours.

## Post-Simulation Analysis and Aggregation

To analyze and compare simulation output across multiple scenarios and replications, a post-processing pipeline was implemented using Python (Pandas, Seaborn, NumPy, SciPy, Matplotlib). The simulation logs generated from SimPy were stored in JSON format, with each file representing a single simulation run for a given charger type configuration.

Log Loading and Structuring

All simulation logs were loaded from the output directory using a custom load_logs() function, which extracted relevant event metadata including timestamps, queue lengths, and charger interactions. Each event’s extra information (e.g., return delays, charging times) was unpacked and merged into the main DataFrame for analysis. The source_file identifier was retained to track which simulation run each log entry originated from.

Scenario-Based Aggregation

Simulation runs were grouped by scenario (i.e., charger type), and data was averaged across all replications within each group. This enabled robust estimation of trends while smoothing individual run variability. Key analysis methods included:

Histogram Visualization: Return delays and charging times were visualized using combined histograms and KDE overlays across all runs per scenario.
Distribution Fitting: Kolmogorov–Smirnov (K-S) tests were used to fit candidate distributions (exponential, Weibull, lognormal) to each variable. The best-fitting distribution was reported per scenario using D-statistics and p-values.
Empirical vs Theoretical Comparison: Empirical return delays were compared to samples generated from a truncated exponential distribution (based on the λ value from real-world data) to assess modeling realism.
Heatmaps of Activity: Hourly heatmaps by day and hour were constructed to visualize charger request patterns across time, helping to identify usage peaks and congestion trends.
Performance Parameter Estimation

To support quantitative evaluation of system performance under M/M/1 assumptions, arrival and service rates were estimated per simulation run and then averaged across scenarios:

λ (Arrival Rate): Calculated from the mean return delay (in hours) as λ = 1 / mean_return_delay.
μ (Service Rate): Inferred from the mean charging duration (in hours) as μ = 1 / mean_charging_time.
ρ (Utilization): Computed as ρ = λ / μ, and averaged across runs.
All scenario-level summaries were compiled into a single CSV output for further inspection.

Erlang-C Queueing Evaluation

Using the averaged λ and μ values, theoretical queueing performance was analyzed for charger systems with 1 to 4 servers using the Erlang-C formula. Metrics calculated included:

Probability of waiting
Expected queue waiting time (E[Wq])
Total expected waiting time (E[W])
System utilization
These results were saved in structured JSON format for each scenario and used to support discussion on charger sizing and queue mitigation strategies.

# RESULTS AND DISCUSSION

gfhdjk

# CONCLUSION

fdsag

# CITATIONS

(1) An electric vehicle charging station access equilibrium model with M/D/C queueing
https://arxiv.org/abs/2102.05851

(2) A Simulation Framework for Ride-Hailing with Electric Vehicles
https://arxiv.org/abs/2411.19471

(3) A Comprehensive Review of Smart Charging Strategies for Electric Vehicles and Way Forward
https://ieeexplore.ieee.org/abstract/document/10457989

(4) Optimization of electric vehicle recharge schedule and routing problem with time windows and partial recharge: A comparative study for an urban logistics fleet
https://www.sciencedirect.com/science/article/abs/pii/S2210670721001736

(5) Development and Evaluation of a Smart Charging Strategy for an Electric Vehicle Fleet Based on Reinforcement Learning
https://www.sciencedirect.com/science/article/abs/pii/S0306261920317566

(6) Online Charging and Routing of Electric Vehicles in Stochastic Time-Varying Networks
https://journals.sagepub.com/doi/abs/10.3141/2667-07

# AI Usage

ChatGPT was used to proofread, rubber duck, and help structure this paper.