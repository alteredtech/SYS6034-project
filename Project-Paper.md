---
title: EV Charging Fleet Strategies
author: 
- Michael Einreinhof
- Taichi Niu
---

# ELECTRIC VEHICLE CHARGING FLEET STRATEGY MODELS OF DIFFERENT DELIVERY STRATEGIES

# ABSTRACT
# INTRODUCTION
* Opening Motivation
    * Briefly describe the rise of EVs and challenges of routing + recharging.
    * Highlight why recharging logistics and charging station congestion matter.
* Problem Statement / Research Context
    * Introduce the specific challenge: optimizing EV fleet routes under SoC and time constraints, including charging queues.
* Review of Prior Work (State of the Art)
    * Discuss prior studies on:
        * EV routing with SoC constraints (4,6)
Electric Vehicle Routing Problems (EVRPs) are significantly more complex than traditional vehicle routing problems due to limitations on driving range and the need to manage charging schedules. The inclusion of SoC constraints introduces challenges such as range anxiety, partial recharging strategies, and trade-offs between travel time and energy replenishment.

One foundational model that captures the complexity of EV routing with SoC constraints is the Electric Vehicle Routing Problem with Time Windows and Partial Recharge (EVRPTW-PR), developed by Bac and Erdem (2021). Their framework accounts for a heterogeneous fleet, multiple depots, and time windows, but more importantly, it integrates partial recharge options. The model explicitly tracks each vehicle’s battery SoC and recharging duration, ensuring that vehicles remain above minimum battery thresholds while considering recharging rates and station availability. It improves realism by allowing vehicles to visit multiple recharging stations and by dynamically adjusting SoC levels, depending on both distance and energy consumption rates. This comprehensive approach enables better distribution of charging loads, reduces stress on the electric grid, and minimizes operational delays due to energy limitations (4)​.

Complementary to this is the work by Jafari and Boyles (2017), which explores on-line charging and routing decisions in networks with stochastic, time-varying conditions. Their study models the behavior of a single EV operating in a real-time environment where travel and wait times are uncertain and dynamically revealed. The decision-making process is structured as a Markov Decision Process (MDP), where SoC is a discrete state variable. The model ensures that vehicles maintain a minimum acceptable charge level, modeling user risk-aversion and range anxiety explicitly. Upon reaching each node, the vehicle evaluates downstream travel times, queue lengths, and station prices to determine whether to charge or continue traveling. This formulation not only incorporates SoC in a dynamic decision context but also allows for flexible recharging decisions, such as interrupting a recharge session or bypassing stations altogether based on updated conditions (6)​.

Together, these works underscore the critical importance of integrating SoC management into EV routing. Bac and Erdem demonstrate optimization under deterministic, multi-vehicle conditions with partial recharging, while Jafari and Boyles introduce real-time stochastic adaptation for a single vehicle. Both approaches highlight the non-trivial nature of SoC constraints, where decisions are influenced by energy capacity, infrastructure, and evolving travel conditions.

        * Use of M/M/1 or queueing models at chargers (1)

Queueing theory plays a critical role in modeling and optimizing electric vehicle (EV) charging systems, especially in urban areas with constrained infrastructure. Numerous studies have applied classical queueing models—such as M/M/1, M/M/C, and M/G/1—to capture the dynamics of charger usage, waiting time, and service delays.

Among the earliest efforts, Jung et al. (2014) utilized an M/M/C queueing model in a simulation-based optimization approach for electric taxi charging stations. While this model helped capture system behavior under stochastic demand, its simplicity introduced limitations due to the exponential assumptions of both arrival and service times. The exponential service time distribution implied by M/M/1 or M/M/C models often leads to unrealistically long tails. For instance, modeling a 3-hour average charging time using an M/M/1 assumption can result in a nontrivial probability (e.g., over 18%) for charging durations exceeding 5 hours—exceeding realistic operational limits.

To address such issues, subsequent research explored more nuanced queue types. Biondi et al. (2016) introduced M/M/1/K models to account for limited charger capacity, while Yang et al. (2017) used M/M/C/K formulations in charger allocation problems. Keskin et al. (2019) applied M/G/1 queues, incorporating general service time distributions to better reflect real-world variability in charging durations. However, despite improvements in modeling accuracy, many of these studies focused on theoretical network structures or small-scale testbeds and did not incorporate real-world empirical data.

Liu et al. (2021) made a significant advancement by proposing an M/D/C queueing model, which assumes deterministic service times with stochastic arrivals. This approach addresses the limitations of M/M/1-type models in the context of EV charging, where service durations are often known and fixed (e.g., 30 minutes at a DC fast charger). The authors implemented their model within a large-scale equilibrium assignment framework applied to over 1,400 vehicles and 263 real-world charging stations across New York City. By incorporating M/D/C queueing dynamics and using approximations from Barceló et al. (1996), the study achieved a more accurate and realistic depiction of congestion and delay at EV chargers (Liu et al., 2021).

The literature reflects a growing consensus that while M/M/1 and its variants offer tractable solutions, their assumptions can misrepresent EV charging behavior, particularly in high-utilization urban environments. As such, there is a shift towards incorporating queueing models with more realistic service time distributions—such as M/D/C or M/G/1—for both planning and operational decision-making.

        * Smart/partial charging strategies (3,4,5)

With the rapid proliferation of electric vehicles, the need for intelligent and flexible charging strategies has become increasingly important. Uncontrolled EV charging—where vehicles begin charging immediately upon connection—can result in grid overloading, increased peak demand, and reduced system reliability. Smart charging strategies aim to mitigate these effects by leveraging communication, control, and optimization technologies to adapt charging behavior to both grid conditions and user preferences.

Smart charging is broadly defined as the coordinated control of EV charging loads to optimize various system objectives such as minimizing cost, reducing emissions, and ensuring grid stability. Dahiwale et al. (2024) offer a comprehensive taxonomy of smart charging strategies categorized by control topology (centralized, decentralized, hierarchical), optimization objectives (e.g., cost minimization, peak shaving), and pricing mechanisms. Their work emphasizes the interplay between stakeholders—distribution system operators, aggregators, and EV users—and the signal flows needed for real-time coordination​ (3).

One core advantage of smart charging is the ability to enable valley filling and load shifting, as highlighted in the reinforcement learning-based framework by Tuchnitz et al. (2021). Their study introduces a scalable charging coordination system that learns optimal policies through experience, achieving up to a 65% reduction in load variance compared to uncontrolled strategies. Unlike optimization-based models, their RL approach does not require prior knowledge of departure times or energy requirements, making it highly adaptable for real-world applications​ (5).

In addition to full charging, partial charging strategies have gained attention for their operational flexibility. Bac and Erdem (2021) demonstrate the effectiveness of partial recharge policies in logistics fleet routing. Their extended vehicle routing problem with time windows and partial recharge (EVRPTW-PR) allows heterogeneous EVs to recharge to varying levels, enhancing schedule feasibility and reducing the number of charging stops. The authors find that partial charging leads to better compliance with time constraints and lowers energy costs, particularly when recharge stations are limited or sparsely distributed​ (4).

Moreover, partial charging can help avoid grid congestion and extend battery lifespan by avoiding full-depth discharges. The ability to determine the optimal charge level dynamically based on route demands and station availability makes it especially suitable for urban logistics and high-utilization EV fleets.

In summary, both smart and partial charging strategies play pivotal roles in supporting the transition to electrified transportation. Smart charging enables grid-aware coordination, while partial charging introduces flexibility into time-sensitive EV operations. Together, these strategies represent a shift away from static, user-driven charging behavior toward adaptive, system-optimized models that benefit both the grid and the EV ecosystem.

        * SimPy or DES modeling tools (2)

Discrete-event simulation (DES) has become a crucial methodology in modeling complex systems where events occur at distinct points in time. In the context of electric vehicle (EV) fleet operations, DES enables researchers to simulate intricate dynamics such as trip requests, charging behavior, vehicle dispatching, and congestion effects in a computationally efficient manner. One of the most widely adopted tools for DES in Python is SimPy, a process-based simulation library that provides an intuitive way to manage asynchronous, time-driven interactions between entities.

In recent years, SimPy has gained prominence for modeling EV fleet behavior under various operational constraints. For example, Zhang and Varma (2024) developed an extensible and modular simulation framework using SimPy to evaluate fleet management strategies for ride-hailing electric vehicles. Their framework accurately represents non-Markovian system dynamics and high-dimensional state spaces by leveraging SimPy's ability to handle parallel processes through coroutine-based timeouts. This approach allows for realistic modeling of events such as EV pickups, drop-offs, charging interruptions, and queueing at charging stations, which would be challenging to manage using traditional analytical models​ (2).

SimPy’s object-oriented design enables modular construction of simulation components, such as EV agents and chargers, each with defined attributes and behaviors. The framework by Zhang and Varma illustrates this by encapsulating each EV as an object with properties like state-of-charge (SoC), location, and current task, and simulating their transitions through discrete processes. For instance, each time a vehicle completes a task, only the relevant states are updated asynchronously, which significantly reduces computational overhead and mirrors real-world behavior more closely​ (2).

Moreover, the flexibility of SimPy facilitates the integration of real-world datasets and algorithmic experimentation. In the cited simulation, customer trip requests were derived from NYC taxi data, and the system supported both Poisson-based arrivals and empirical datasets. The authors highlight how the simulation framework enables comparative evaluations of dispatching policies (e.g., power-of-d versus closest dispatch) and charging strategies (e.g., continuous vs. nighttime charging), making it a valuable tool for urban mobility planning​ (2).

Overall, the use of SimPy exemplifies the strengths of DES tools in simulating EV operations at scale, allowing for granular control over event logic while maintaining efficient runtimes. This aligns well with the increasing demand for scalable, realistic, and adaptable simulation environments to support data-driven decision-making in sustainable urban transportation systems.

        * Algorithms for charging-aware routing (4,5,6)

Routing electric vehicles (EVs) efficiently while accounting for their limited range and charging needs is a critical challenge in sustainable transportation planning. Various algorithms have been proposed to address this problem, particularly within the framework of electric vehicle routing problems with time windows (EVRPTW) and partial recharge (EVRPTW-PR).

Optimization-based approaches dominate the literature, employing classical heuristics and metaheuristics adapted to account for charging constraints. Bac and Erdem (2021) propose an EVRPTW-PR framework that incorporates realistic elements such as partial recharging, heterogeneous fleets, and multiple depots. Their solution leverages Variable Neighborhood Search (VNS) and Variable Neighborhood Descent (VND) algorithms with novel neighborhood operators designed to balance route feasibility, recharge scheduling, and compliance with delivery time windows​ (4).

Similarly, hybrid methods combining Tabu Search and Simulated Annealing have shown success in escaping local optima when optimizing routing under energy and time constraints. For example, Schneider et al. developed a hybrid VNS/TS algorithm, where recharging decisions are optimized in tandem with route construction​ (4). In another instance, Hiermann et al. introduced an Adaptive Large Neighborhood Search (ALNS) algorithm that dynamically adjusts its destroy-and-repair heuristics, providing flexibility in accommodating vehicle energy profiles and customer time windows.

From a stochastic and dynamic perspective, Jafari and Boyles (2017) present an online charging and routing algorithm based on finite-horizon Markov Decision Processes (MDPs). In their model, vehicles make real-time routing and charging decisions as new information about downstream travel times and charging station wait times becomes available. Their on-line strategy significantly outperforms offline static routing in networks characterized by uncertain travel conditions and limited charging infrastructure, especially as the network scale increases​ (6).

Furthermore, Reinforcement Learning (RL) techniques offer a data-driven and scalable alternative. Tuchnitz et al. (2021) develop a smart charging strategy using Deep Q-Networks (DQNs), showing that EV fleets can learn optimal charging behaviors without relying on exact forecasts of departure times or energy demands. Although this study primarily targets load balancing, its RL framework can be extended to jointly consider routing decisions by integrating charging-aware path selection within the state space of the learning agent​ (5).

Overall, these studies show that charging-aware routing algorithms must integrate both the vehicle’s battery dynamics and the network’s charging topology. Hybrid heuristics (e.g., VNS, ALNS), stochastic control (e.g., MDPs), and intelligent learning systems (e.g., RL) each provide viable paths for addressing the growing complexity of EV logistics in urban and regional networks.

    * Identify what they accomplished and what’s still missing (e.g., most assume fixed infrastructure or don’t explore number of chargers required).
* Your Contribution / Gap Addressed
    * Summarize how your work builds on this:
        * You extend a known model using simulation to answer infrastructure questions.
        * You explore how different recharging strategies affect charger needs and reliability.
# METHOD
# RESULTS AND DISCUSSION
# CONCLUSION
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